#!/usr/bin/env bash
# 质量门禁：术语/编号/交叉引用校对 + EPUB 结构校验
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
[ -f .env.build ] && . ./.env.build
PY="${PYTHON:-python}"

echo "== 全书校对 =="
"$PY" analysis/audit.py

echo "== EPUB 结构校验 =="
"$PY" - <<'PY'
import sys, zipfile
from lxml import etree
try:
    z = zipfile.ZipFile('output/book.epub')
except FileNotFoundError:
    print('未找到 output/book.epub，先运行 scripts/build.sh'); sys.exit(0)
assert z.read('mimetype') == b'application/epub+zip', 'mimetype 错误'
bad = []
for n in z.namelist():
    if n.endswith(('.xhtml', '.opf', '.ncx', '.xml')):
        try:
            etree.fromstring(z.read(n))
        except Exception as e:
            bad.append((n, str(e)))
print('XML 解析错误：', bad or '无')
print('条目数：', len(z.namelist()))
PY
echo "校验完成。"
