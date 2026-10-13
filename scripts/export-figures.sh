#!/usr/bin/env bash
# 把矢量插图导出为高分辨率 PNG（约 300 dpi 备份），供投稿或印刷备用。
# 输出：output/figures/*.png
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
[ -f .env.build ] && . ./.env.build
PY="${PYTHON:-python}"
"$PY" analysis/export_figures.py
