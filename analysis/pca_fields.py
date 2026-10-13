# -*- coding: utf-8 -*-
"""
pca_fields.py — 对第 19—20 章的领域编码矩阵做 PCA / 因子分析。

回答一个审稿人式的问题：『你说 25 个领域被同一框架统一，但它们在框架里的编码
是不是高度共线，以至于"统一"只是给同一列贴了很多标签？』

做法：把每个领域的编码表示为一个二值/有序特征向量
  （区分动作代数类型、曲率符号、演化流类型、严格度），
做 PCA，报告：
  * 特征值、方差解释比、累积；
  * 有效维度 N_eff = K^2 / Σλ^2；
  * PC1 载荷（哪些特征主导第一主成分）；
  * 平行分析（随机对照）。

若 N_eff 接近 K，说明编码确实张成多维空间（统一不是同义反复）；
若 N_eff 接近 1，说明所有领域其实只在一个维度上变化（"统一"可疑）。

输出：analysis/results/pca_fields.json
依赖：numpy。
"""
import json
import os

import numpy as np

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(HERE, "analysis", "results")

# 特征：[线性, 拓扑, 度量, 序, 逻辑, κ负, κ零, κ正, 无演化, 离散, 连续]
# 1 = 该特征存在/主导；数值取自表 B.1/B.2 的编码。
DATA = {
    #            线性 拓扑 度量 序 逻辑  κ-  κ0  κ+  无 离散 连续
    "图论":       [0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 1],
    "线性代数":   [1, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0],
    "表示论":     [1, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0],
    "调和分析":   [1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1],
    "点集拓扑":   [0, 1, 0, 0, 0, 1, 0, 0, 1, 0, 0],
    "代数拓扑":   [0, 1, 0, 0, 0, 1, 0, 0, 1, 0, 0],
    "测度论":     [0, 0, 1, 0, 0, 0, 0, 1, 1, 0, 0],
    "实分析":     [0, 0, 1, 0, 0, 0, 0, 1, 1, 0, 0],
    "泛函分析":   [1, 0, 1, 0, 0, 0, 0, 1, 1, 0, 0],
    "复分析":     [0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0],
    "组合数学":   [0, 0, 0, 1, 0, 0, 0, 1, 1, 0, 0],
    "数论":       [0, 0, 0, 1, 0, 0, 0, 1, 1, 0, 0],
    "数理逻辑":   [0, 0, 0, 0, 1, 0, 1, 0, 1, 0, 0],
    "类型论":     [0, 0, 0, 0, 1, 1, 0, 0, 1, 0, 0],
    "微分方程":   [0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 1],
    "动力系统":   [0, 0, 1, 0, 0, 0, 0, 1, 0, 1, 0],
    "概率论":     [0, 0, 1, 0, 0, 0, 1, 0, 0, 1, 0],
    "信息论":     [0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0],
    "算子代数":   [1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1],
    "量子数学":   [1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1],
    "博弈论":     [0, 0, 0, 1, 0, 0, 0, 1, 0, 1, 0],
    "优化":       [0, 0, 0, 1, 0, 1, 0, 0, 1, 0, 0],
    "数值分析":   [0, 0, 1, 0, 0, 0, 1, 0, 0, 1, 0],
    "微分几何":   [0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 1],
    "LLM潜在空间": [1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1],
}
FEATURES = ["线性", "拓扑", "度量", "序", "逻辑", "κ负", "κ零", "κ正",
            "无演化", "离散", "连续"]

PARALLEL_ITERS = 2000
SEED = 0


def pca(mat):
    C = np.corrcoef(mat)
    ev, evec = np.linalg.eigh(C)
    order = np.argsort(ev)[::-1]
    ev, evec = ev[order], evec[:, order]
    for j in range(evec.shape[1]):
        if evec[0, j] < 0:
            evec[:, j] *= -1
    var = ev / ev.sum()
    load = evec * np.sqrt(np.clip(ev, 0, None))
    neff = float(ev.sum() ** 2 / np.sum(ev ** 2))
    return ev, var, load, neff


def parallel(mat, n_iter=PARALLEL_ITERS, seed=SEED):
    rng = np.random.default_rng(seed)
    K, T = mat.shape
    sims = np.empty((n_iter, K))
    for i in range(n_iter):
        sims[i] = np.sort(np.linalg.eigh(np.corrcoef(rng.standard_normal((K, T))))[0])[::-1]
    return np.percentile(sims, 95, axis=0)


def main():
    names = list(DATA)
    M = np.array([DATA[n] for n in names], dtype=float).T  # features x fields
    ev, var, load, neff = pca(M)
    pa95 = parallel(M)
    out = {
        "n_fields": len(names), "n_features": len(FEATURES),
        "features": FEATURES, "fields": names,
        "eigenvalues": [round(float(x), 4) for x in ev],
        "variance_explained": [round(float(x), 4) for x in var],
        "cumulative": [round(float(x), 4) for x in np.cumsum(var)],
        "effective_dimensionality": round(neff, 3),
        "pc1_share": round(float(var[0]), 3),
        "loadings_pc1": {f: round(float(l), 3) for f, l in zip(FEATURES, load[:, 0])},
        "parallel_95pct": [round(float(x), 3) for x in pa95],
        "components_retained_parallel": int(np.sum(ev > pa95)),
        "kaiser_gt1": int(np.sum(ev > 1.0)),
        "note": "若 N_eff→1，说明领域编码高度共线（统一可疑）；若 N_eff 接近 K，说明编码张成多维空间。",
    }
    os.makedirs(RES, exist_ok=True)
    with open(os.path.join(RES, "pca_fields.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    # 注入正文占位符 {{D:pca_*}}
    inj_path = os.path.join(HERE, "data", "injected.json")
    inj = {}
    if os.path.exists(inj_path):
        try:
            with open(inj_path, encoding="utf-8") as f:
                inj = json.load(f)
        except Exception:
            inj = {}
    inj.update({
        "pca_neff": f"{neff:.2f}",
        "pca_k": str(len(FEATURES)),
        "pca_pc1": f"{var[0]:.3f}",
        "pca_retained": str(out["components_retained_parallel"]),
    })
    os.makedirs(os.path.join(HERE, "data"), exist_ok=True)
    with open(inj_path, "w", encoding="utf-8") as f:
        json.dump(inj, f, ensure_ascii=False, indent=2)

    print(f"字段数 K={len(FEATURES)}，领域数={len(names)}")
    print(f"有效维度 N_eff = {neff:.2f}（K={len(FEATURES)}）")
    print(f"PC1 方差解释 = {var[0]:.3f}")
    print("PC1 载荷前五：", sorted(out["loadings_pc1"].items(), key=lambda kv: -abs(kv[1]))[:5])
    print("平行分析保留成分数 =", out["components_retained_parallel"],
          "；Kaiser(λ>1) =", out["kaiser_gt1"])
    print("[done]", os.path.join(RES, "pca_fields.json"))


if __name__ == "__main__":
    main()
