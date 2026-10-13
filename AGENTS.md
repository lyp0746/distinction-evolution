# AGENTS.md — 本仓库工作约定与工具链（记忆）

> pi 会把本文件作为目录级上下文/记忆自动加载。改动后新会话生效。

## 工具链（本机实测，2026-10）

- **Git**：`D:\Git\cmd\git.exe`（不在 WSL 的 PATH 里，请用绝对路径 `/mnt/d/Git/cmd/git.exe`）
  - remote：`https://github.com/lyp0746/distinction-evolution.git`，默认分支 `main`
  - 凭据已缓存，可直接 `push`；脚本里加 `GIT_TERMINAL_PROMPT=0` 防卡住
- **Python（构建/分析）**：`/mnt/d/0_Code/Iris Series/.venv/Scripts/python.exe`
  - 已装：numpy scipy pandas matplotlib bs4 lxml pypdf requests（**无** weasyprint / markdown）
  - `.env.build` 的 `PYTHON` 已指向该解释器
  - 注意：WSL 的 `export VAR=...` **不会**传入 Windows Python（interop）；需要 token 时在 Python 里自己调 git credential fill
- **PDF 生成**：`build_book.py --pdf` 调**无头 Chrome**（`C:\Program Files\Google\Chrome\Application\chrome.exe`）打印，**不是** weasyprint

## 常用命令

```bash
PY="/mnt/d/0_Code/Iris Series/.venv/Scripts/python.exe"
GIT="/mnt/d/Git/cmd/git.exe"

"$PY" analysis/make_figures.py       # 生成 assets/svg/fig*.svg
"$PY" analysis/make_figures_extra.py # 补充插图：候选核心、分层可信度、阅读合约、验证状态、四场判定
"$PY" analysis/make_cover.py         # 生成 assets/svg/cover.svg
"$PY" analysis/graph_phase_transition.py  # 第四部分数值（协议 V1）
"$PY" analysis/pca_fields.py         # 编码矩阵 PCA
"$PY" analysis/monte_carlo_sensitivity.py # 阈值假说敏感性
"$PY" analysis/llm_activation_probe.py # 附录 I.1 激活探针（合成 MLP）
"$PY" analysis/orbifold_gap.py       # 附录 I.2 轨形缺口
"$PY" analysis/encoding_preservation.py # 附录 I.3 / 表 B.5 编码保结构（15 个对象）
"$PY" analysis/independent_features.py  # O17 独立特征复核（削弱猜想 D2）
"$PY" analysis/axiom_consistency.py    # 第 14.6.1 六公理在 27 领域的自洽核算
"$PY" analysis/weighted_directed_transition.py # 附录 J 加权/有向相变
"$PY" analysis/discrete_curvature.py # 附录 J 离散分离曲率
"$PY" analysis/higher_dim_gap.py     # 附录 J 高维缺口（证伪 G4）
bash scripts/verify-experiments.sh   # 一键复现全部数值实验
"$PY" analysis/audit.py              # 校对 → 刷新 校对清单.md
bash scripts/build.sh                # audit→印刷PDF→电子阅读PDF→EPUB→Markdown
bash scripts/validate.sh             # 校对 + EPUB 结构校验
bash scripts/release.sh              # 组装 release/
"$PY" scripts/create_github_release_per_artifact.py --list
"$PY" scripts/create_github_release_per_artifact.py --date 2026-10-13   # 一个产物一个 tag
```

## 仓库约定

- **`source/*.html` 是唯一权威正文来源**；`output/`、`release/` 是派生产物（见 `.gitignore`）。
- 图表：脚本输出 `assets/svg/*.svg`；正文用相对路径 `assets/svg/...` 引用。
- 改正文后顺序：`analysis/make_figures.py`（如改图）→ `analysis/audit.py` → `bash scripts/build.sh`。
- 结论标注：证据等级 A/B/C 与概念等级 甲/乙/丙 双重标注；全书数字必须带等级。
- **一个产物一个 tag**：`scripts/create_github_release_per_artifact.py` 为每个产物各建一个 tag/release，每个 release 只承载一个资产。
- **可证伪登记簿**（`source/appendix_e_preregistration.html` 与 `docs/preregistration/`）为 **append-only**：只追加，绝不改写旧行。
- **正文与元数据不含版本号**；日期使用真实完成日期（`source/book.json` 单一来源）。

## 写作风格（重要）

见 skill `academic-book-pipeline` 的 `references/voice.md`。要点：

- **张力，不宿命**：约束是交易的条件，不是判决。禁止把“必然／不可避免／无法消除／注定／死路”当作结论。
- **分级在装置，不在每句**：证据/概念等级放表格与附录；正文一句一个精确限定即可。
- **反例进正文**（例如球面矛盾、朴素阈值被证伪）；**地图只定性**。
- 每个硬约束章必须带反向力量：这条限制**使什么成为可能**。

## 版本脉络

见 `versions/CHANGELOG.md`（首版）。
