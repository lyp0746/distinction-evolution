#!/usr/bin/env bash
# 一键复现全部数值实验（第四部分硬核 + 附录 I 工程验证）。
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
[ -f .env.build ] && . ./.env.build
PY="${PYTHON:-python}"

run() { echo "== $1 =="; "$PY" "$2"; echo; }

run "第四部分：图上的相变（协议 V1）"      analysis/graph_phase_transition.py
run "第四部分：编码矩阵 PCA"                analysis/pca_fields.py
run "第四部分：阈值假说敏感性"              analysis/monte_carlo_sensitivity.py
run "附录 I.1：LLM 激活探针（合成 MLP）"   analysis/llm_activation_probe.py
run "附录 I.2：轨形缺口（1/3）"            analysis/orbifold_gap.py
run "附录 I.3：编码结构保持"               analysis/encoding_preservation.py
run "附录 J：加权/有向相变（定理 B1 + 反例 B2）" analysis/weighted_directed_transition.py
run "附录 J：离散分离曲率（定理 C）"        analysis/discrete_curvature.py
run "附录 J：高维缺口（证伪 G4）"          analysis/higher_dim_gap.py
run "附录 J：顺序判据 B1'（Rayleigh + 否定）" analysis/reversal_criterion.py
run "第六部分：Fisher 曲率与能力涌现"      analysis/fisher_curvature.py
run "附录 J：公理在图论情形的精确状态"    analysis/axioms_graph.py

echo "全部实验完成。结果写入 analysis/results/ 与 assets/charts/。"
