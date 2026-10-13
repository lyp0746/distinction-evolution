# 数据与来源说明

本文件说明书中数值与引用的来源与可复现性。

## 一、数值结果（第四部分）

第 12—15 章的全部数字由 `analysis/graph_phase_transition.py` 从公开定义（图拉普拉斯矩阵的谱）确定性计算，不依赖任何外部数据。复现命令：

```bash
python analysis/graph_phase_transition.py
```

输出：

- `analysis/results/graph_phase_transition.json`：各图的谱、临界耦合、数值验证斜率。
- `data/injected.json`：注入正文的数值。

关键结果（α=1）：Petersen (0.200, 0.500)、C₁₀ (0.250, 2.618)、K₅ (0.200, 0.200)、K₄,₄ (0.125, 0.250)、Q₅ (0.100, 0.500)、P₂₀ (0.252, 40.612)。

## 二、统计结果

- `analysis/pca_fields.py` 输出 `analysis/results/pca_fields.json`：编码矩阵特征值、N_eff、PC1 载荷、平行分析。
- `analysis/monte_carlo_sensitivity.py` 输出 `analysis/results/monte_carlo_sensitivity.json`：κ 符号的敏感性。所有 regime 参数为规定性（C 级）。

## 三、文献来源

参考文献见正文附录 C。凡引用的数学事实均标注等级（A/B/C）。标准教科书结论（谱定理、Gauss–Bonnet、热核展开）列为 A 或 B；探索性文献列为 C。

## 四、数据可得性

本书不包含受保护、非公开或尚未观测的数据。经验数据缺口（如 LLM 激活）在附录 F 中登记，并给出获取路径，但本书未获取它们。作者不伪造这些数据。

## 五、许可

正文 CC BY 4.0；脚本与构建工具 MIT。
