# -*- coding: utf-8 -*-
"""independent_features.py — O17 概念性复核：独立特征的 PCA

目的：检验“六元组维数上界”（猜想 D2）。用一组**与 EDS 六元组无关**的特征
重新刻画同一批领域，做 PCA，看有效维度是否仍接近 6。

重要声明（必须先读）：
本脚本的特征值**不是**测量数据，而是作者依据公开常识（教科书结构、MSC 分类、
Mathlib 覆盖、公开问题数量级）给出的**主观估计（C／丙）**。因此本脚本是
“概念性复核”（conceptual replication），**不是独立测量**。

- 若结果仍≈6：只能说“与 D2 相容”，**不能**说 D2 被证明——估计偏差与设计偏差
  仍可能存在。
- 若结果远离 6：说明 6.14 更可能是六元组设计诱导的循环后果，D2 应降级。

真正的 O17 需要书目计量数据（nLab/Wikipedia/MSC 条目计数、Mathlib 覆盖率、
zbMATH 公开问题计数等）。本书环境不具备这些数据，故登记为数据缺口（附录 F）。

输出：analysis/results/independent_features.json。
依赖：numpy。
"""
import json
import os

import numpy as np

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(HERE, "analysis", "results")

# 特征（每一个都与 EDS 六元组无关）
FEATURES = [
    "prereq_depth",       # F1 前置深度（1—5）
    "cored_defs",         # F2 核心定义数量级（1—5）
    "age_decades",        # F3 现代形式至今的十年数（1—5）
    "comp_verifiable",    # F4 主要结论可计算机验证的比例（0—1）
    "cross_links",        # F5 与其他领域的深层联系数（1—5）
    "open_problems",      # F6 活跃公开问题数量级（1—5）
    "formal_coverage",    # F7 形式化（Mathlib 等）覆盖率（0—1）
    "method_diversity",   # F8 本质不同的证明方法数（1—5）
]

# 作者估计（C／丙）。顺序与 FEATURES 一致。
# 这些数字是“量级判断”，不是精确测量；任何读者可自行替换后重跑。
EST = {
    "图论":        [1, 2, 3, 0.8, 4, 2, 0.5, 3],
    "线性代数":    [2, 3, 4, 0.9, 5, 1, 0.9, 3],
    "表示论":      [4, 4, 4, 0.4, 4, 3, 0.4, 4],
    "调和分析":    [4, 4, 4, 0.5, 4, 3, 0.3, 4],
    "点集拓扑":    [3, 4, 4, 0.5, 4, 2, 0.4, 3],
    "代数拓扑":    [4, 4, 4, 0.4, 5, 4, 0.3, 5],
    "测度论":      [4, 3, 4, 0.6, 4, 2, 0.5, 3],
    "实分析":      [4, 3, 4, 0.6, 4, 2, 0.4, 3],
    "泛函分析":    [5, 4, 4, 0.4, 4, 3, 0.3, 4],
    "复分析":      [4, 4, 4, 0.4, 4, 3, 0.2, 4],
    "组合数学":    [2, 3, 3, 0.7, 4, 5, 0.4, 5],
    "数论":        [5, 4, 5, 0.3, 5, 5, 0.2, 5],
    "数理逻辑":    [3, 3, 4, 0.8, 3, 2, 0.7, 3],
    "类型论":      [3, 3, 2, 0.9, 3, 2, 0.9, 3],
    "微分方程":    [4, 3, 4, 0.5, 4, 4, 0.2, 4],
    "动力系统":    [3, 3, 3, 0.6, 4, 4, 0.2, 4],
    "概率论":      [4, 4, 4, 0.7, 4, 3, 0.4, 4],
    "信息论":      [2, 2, 3, 0.8, 4, 2, 0.3, 2],
    "算子代数":    [5, 4, 4, 0.3, 4, 3, 0.2, 4],
    "量子数学":    [5, 4, 3, 0.3, 4, 4, 0.2, 4],
    "博弈论":      [2, 2, 3, 0.6, 4, 3, 0.2, 3],
    "优化":        [2, 3, 3, 0.9, 4, 2, 0.4, 3],
    "数值分析":    [2, 3, 3, 0.9, 3, 2, 0.3, 3],
    "微分几何":    [5, 4, 5, 0.3, 5, 4, 0.2, 4],
    "LLM 潜在空间": [3, 2, 1, 0.7, 4, 5, 0.1, 3],
    "马尔可夫链":  [3, 2, 4, 0.8, 4, 2, 0.4, 3],
    "编码论":      [3, 3, 4, 0.8, 4, 3, 0.3, 3],
}


def effective_dim(X):
    """相关矩阵的有效维度 N_eff = K^2 / sum(lambda^2)。"""
    Xc = X - X.mean(0)
    sd = Xc.std(0)
    sd[sd == 0] = 1
    Z = Xc / sd
    C = np.corrcoef(Z, rowvar=False)
    lam = np.linalg.eigvalsh(C)
    lam = lam[lam > 1e-12]
    return float(lam.size ** 2 / np.sum(lam ** 2)), np.sort(lam)[::-1]


def main():
    domains = list(EST.keys())
    X = np.array([EST[d] for d in domains], dtype=float)
    neff, lam = effective_dim(X)
    # 平行分析（随机矩阵 95 分位）
    rng = np.random.default_rng(0)
    K = len(FEATURES)
    rand = []
    for _ in range(2000):
        R = rng.standard_normal(X.shape)
        rand.append(effective_dim(R)[0])
    p95 = float(np.percentile(rand, 95))
    out = {
        "n_domains": len(domains),
        "n_features": K,
        "features": FEATURES,
        "effective_dim": round(neff, 4),
        "eigenvalues": [round(float(x), 4) for x in lam],
        "parallel_p95": round(p95, 4),
        "note": ("作者估计（C／丙）上的概念性复核，非独立测量。"
                 "若结果≈6，仅与猜想 D2 相容，不构成证明；"
                 "真实验证需书目计量数据（数据缺口，见附录 F）。"),
        "verdict": ("consistent_with_D2" if abs(neff - 6) <= 1.0 else
                    "inconsistent_with_D2"),
    }
    os.makedirs(RES, exist_ok=True)
    with open(os.path.join(RES, "independent_features.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"domains={len(domains)} features={K}")
    print(f"N_eff (independent features) = {neff:.3f}")
    print(f"eigenvalues = {out['eigenvalues']}")
    print(f"parallel p95 = {p95:.3f}")
    print(f"verdict = {out['verdict']}")
    print("[done]", os.path.join(RES, "independent_features.json"))


if __name__ == "__main__":
    main()
