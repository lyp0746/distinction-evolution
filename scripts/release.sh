#!/usr/bin/env bash
# 组装"可发布"交付包：仅含读者可见内容。
# 明确排除：xlsx / csv / json / py / ipynb / requirements.txt。
#
# 可用环境变量：
#   BASE=my-book   发布文件的基础名（默认 book）
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
[ -f .env.build ] && . ./.env.build
PY="${PYTHON:-python}"
BASE="${BASE:-distinction-evolution}"

echo "== 先构建最新产物 =="
if [ -f scripts/build.sh ]; then bash scripts/build.sh >/dev/null; else
  "$PY" build_book.py --pdf >/dev/null
  "$PY" build_book.py --ereader --pdf >/dev/null
  "$PY" build_epub.py >/dev/null
  "$PY" build_markdown.py >/dev/null
fi

REL="$ROOT/release"
# Windows 预览/索引有时会短暂锁住刚生成的 PDF；重试删除，失败则原地覆盖。
for _ in 1 2 3; do rm -rf "$REL" 2>/dev/null || true; [ ! -d "$REL" ] && break; sleep 2; done
mkdir -p "$REL"

copy() { if [ -f "$1" ]; then cp "$1" "$2"; echo "  + $(basename "$2")"; fi; }

copy output/book.pdf          "$REL/$BASE-print.pdf"
copy output/book-ereader.pdf  "$REL/$BASE-ereader.pdf"
copy output/book.epub         "$REL/$BASE.epub"
copy output/book.html         "$REL/$BASE.html"
copy output/book-ereader.html "$REL/$BASE-ereader.html"
copy output/markdown/book.md  "$REL/$BASE.md"
# 逐文件 Markdown（含被引用的图片，保持自包含）
if [ -d output/markdown ]; then
  mkdir -p "$REL/$BASE-markdown"
  cp -r output/markdown/. "$REL/$BASE-markdown/"
  echo "  + $BASE-markdown/（分文件 Markdown + assets）"
  # 额外打包一个 zip，便于一次性下载（GitHub Release 不能上传目录）
  "$PY" - "release/$BASE-markdown.zip" "output/markdown" <<'PY'
import os, sys, zipfile
out, src = sys.argv[1], sys.argv[2]
with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
    for root, _, files in os.walk(src):
        for f in files:
            p = os.path.join(root, f)
            z.write(p, os.path.relpath(p, src))
print('  + %s（Markdown 打包）' % os.path.basename(out))
PY
fi
copy assets/svg/cover.svg     "$REL/cover.svg"
copy docs/READERS.md          "$REL/README.md"
copy docs/RELEASE-NOTES.md    "$REL/修订说明.md"
copy docs/DATA-GAPS.md        "$REL/数据缺口清单.md"
copy docs/OPEN-CONTRIBUTION.md "$REL/欢迎补充数据.md"

cat > "$REL/MANIFEST.txt" <<EOF
$BASE — 发布包清单
==================
$BASE-print.pdf    印刷/正式版 PDF（A4，宋体+Times，四级书签）
$BASE-ereader.pdf  电子阅读版 PDF
$BASE.epub         EPUB 3（nav + NCX 四级目录）
$BASE.html         网页版（自包含）
$BASE.md           合并全书 Markdown（GFM 表格与引用块）
$BASE-markdown/    分文件 Markdown（含 assets/ 图片）
$BASE-markdown.zip 分文件 Markdown 打包（便于一次性下载）
cover.svg          封面矢量图
README.md          读者说明
修订说明.md        版次与主要变化
数据缺口清单.md    数据可得性登记与获取路径
欢迎补充数据.md    开放贡献指南

明确不包含（非发布内容）：
  *.xlsx / *.csv / *.json    原始数据与中间结果
  *.py / analysis/           分析脚本与工程
  requirements.txt           依赖清单
  source/ assets/ scripts/   源文件与构建工具
EOF

# 守门：发布包中不得出现非发布内容
BAD=$(find "$REL" -type f \( -name '*.xlsx' -o -name '*.csv' -o -name '*.json' \
      -o -name '*.py' -o -name '*.ipynb' -o -name 'requirements.txt' \) || true)
if [ -n "$BAD" ]; then
  echo "ERROR: 发布包中检测到非发布内容，已中止："; echo "$BAD"; exit 1
fi

echo "== 发布包已生成：release/ =="
ls -lh "$REL"
