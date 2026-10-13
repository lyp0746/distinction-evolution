# -*- coding: utf-8 -*-
"""
axioms_graph.py — 六条公理在图论情形的精确状态（可核算）。

本脚本不做“为每条公理编一个定理”，而是逐条**核算**它在图上到底是不是平凡的、
可证的、还是不适用的。这是对“框架生成性”问题最诚实的回答。

核算结果（预期）：
  公理1（观测完备）：**平凡**。完整谱嵌入的行是正交矩阵的行，必互相正交 → 必单射。
                    不存在非平凡的“观测完备定理”（有限精度版本是另一个问题）。
  公理2（精度连续）：**平凡**。有限图上精度是离散的。
  公理3（曲率有界）：**有定理**。κ_info = Var(λ)/2（见 discrete_curvature.py）。
  公理4（演化适定）：**硬核**。两阶段相变定理（见 graph_phase_transition.py）。
  公理5（分离完备）：**有定理（本脚本新增）**。
      原子区分动作 = 谱投影 P_k。P_k 由谱唯一决定；
      但每个 P_k 内部分解为 rank-1 原子当且仅当该特征值单重（几何重数=1）。
      故：**原子分解唯一 ⟺ 谱是单谱（所有特征值互异）**。
      推论：K_n、K_{m,n}、Petersen、偶数环等退化谱图的原子分解不唯一。
  公理6（标准化）：图论不适用（无超有限）。

另附一个**生成性推论**（标准谱事实的应用）：
  笛卡尔积 G□H 的谱为 λ_i(G)+λ_j(H)，故相变结构可由因子图直接计算。
  这是“框架能从已知图生成新图的相变结构”的一个真实例子。

输出：analysis/results/axioms_graph.json
依赖：numpy。
"""
import json
import os
import sys

import numpy as np

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(HERE, "analysis", "results")
ALPHA = 1.0


def lap(n, edges):
    L = np.zeros((n, n))
    for (u, v) in edges:
        L[u, u] += 1
        L[v, v] += 1
        L[u, v] -= 1
        L[v, u] -= 1
    return L


def cycle(n):
    return [(i, (i + 1) % n) for i in range(n)]


def complete(n):
    return [(i, j) for i in range(n) for j in range(i + 1, n)]


def complete_bipartite(m):
    return [(i, m + j) for i in range(m) for j in range(m)]


def path(n):
    return [(i, i + 1) for i in range(n - 1)]


def petersen():
    return cycle(5) + [(5 + i, 5 + (i + 2) % 5) for i in range(5)] + [(i, 5 + i) for i in range(5)]


GRAPHS = {
    "Petersen": (10, petersen()),
    "C10": (10, cycle(10)),
    "C11": (11, cycle(11)),
    "K5": (5, complete(5)),
    "K4,4": (8, complete_bipartite(4)),
    "P8": (8, path(8)),
    "Star8": (8, [(0, i) for i in range(1, 8)]),
}


def multiplicity_profile(lam, tol=1e-7):
    """返回 (是否单谱, 重数分布)。"""
    uniq = []
    for x in np.sort(lam):
        if uniq and abs(x - uniq[-1][0]) < tol:
            uniq[-1][1] += 1
        else:
            uniq.append([x, 1])
    mults = [m for _, m in uniq]
    return (all(m == 1 for m in mults), [int(m) for m in mults])


def spectral_injectivity(n, edges):
    """完整谱嵌入是否单射？（预期：恒为真，因为行是正交矩阵的行）"""
    L = lap(n, edges)
    _, V = np.linalg.eigh(L)      # V 列为特征向量，V 正交
    # 行 i, j 的差范数：若为 0 则不单射
    mind = np.inf
    for i in range(n):
        for j in range(i + 1, n):
            mind = min(mind, float(np.linalg.norm(V[i] - V[j])))
    return {"min_row_distance": round(mind, 6), "injective": bool(mind > 1e-6)}


def phase(n, edges):
    lam = np.sort(np.linalg.eigvalsh(lap(n, edges)))
    l2, ln = float(lam[1]), float(lam[-1])
    return {"lambda_2": round(l2, 6), "lambda_n": round(ln, 6),
            "beta_1": round(ALPHA / ln, 6), "beta_2": round(ALPHA / l2, 6),
            "width": round(ALPHA * (1 / l2 - 1 / ln), 6)}


def cartesian_product(nA, eA, nB, eB):
    """G□H 的顶点为 (a,b)，边为 (a,b)-(a',b) 或 (a,b)-(a,b')。"""
    n = nA * nB
    idx = lambda a, b: a * nB + b
    edges = []
    for (u, v) in eA:
        for b in range(nB):
            edges.append((idx(u, b), idx(v, b)))
    for (u, v) in eB:
        for a in range(nA):
            edges.append((idx(a, u), idx(a, v)))
    return n, edges


def main():
    rows = {}
    profiles = {}
    inj = {}
    for name, (n, e) in GRAPHS.items():
        lam = np.sort(np.linalg.eigvalsh(lap(n, e)))
        simple, mults = multiplicity_profile(lam)
        profiles[name] = {"simple_spectrum": simple, "multiplicities": mults}
        inj[name] = spectral_injectivity(n, e)
        rows[name] = phase(n, e)

    # 生成性：Petersen □ K2 的相变结构（由因子谱预测并验证）
    nP, eP = GRAPHS["Petersen"]
    n, e = cartesian_product(nP, eP, 2, [(0, 1)])
    prod = phase(n, e)
    lamP = np.sort(np.linalg.eigvalsh(lap(nP, eP)))
    lamK2 = np.sort(np.linalg.eigvalsh(lap(2, [(0, 1)])))
    pred = np.sort(np.array([x + y for x in lamP for y in lamK2]))
    actual = np.sort(np.linalg.eigvalsh(lap(n, e)))
    prod_pred_ok = bool(np.allclose(pred, actual, atol=1e-9))

    out = {
        "axiom_status": {
            "axiom_1_observational_completeness": {
                "status": "平凡（trivial）",
                "reason": "完整谱嵌入的行是正交矩阵的行，必互相正交，故必单射；不存在非平凡定理。",
                "min_row_distance_all_positive": all(v["injective"] for v in inj.values()),
            },
            "axiom_2_precision_continuity": {
                "status": "平凡",
                "reason": "有限图上精度是离散的；连续版本需在 β 上讨论（见公理4）。",
            },
            "axiom_3_bounded_curvature": {
                "status": "有定理",
                "theorem": "κ_info(G) = Var(λ)/2（discrete_curvature.py）",
            },
            "axiom_4_wellposedness": {
                "status": "硬核",
                "theorem": "两阶段相变，β₁=α/λₙ、β₂=α/λ₂（graph_phase_transition.py）",
            },
            "axiom_5_separation_completeness": {
                "status": "有定理（本脚本）",
                "theorem": ("原子区分动作 = 谱投影 P_k；P_k 由谱唯一决定。"
                            "每个 P_k 可唯一分解为 rank-1 原子 ⟺ 该特征值单重。"
                            "故：原子分解唯一 ⟺ 谱为单谱（所有特征值互异）。"),
            },
            "axiom_6_standardization": {
                "status": "不适用",
                "reason": "有限图无超有限结构。",
            },
        },
        "spectrum_profiles": profiles,
        "spectral_injectivity": inj,
        "phase_structures": rows,
        "generative_corollary": {
            "name": "笛卡尔积 G□H 的相变结构",
            "predicted_from_factors": prod_pred_ok,
            "product_spectrum_matches": prod_pred_ok,
            "Petersen_square_K2": prod,
            "note": "λ(G□H)=λ_i(G)+λ_j(H)（标准谱事实）；相变结构由此可直接计算。",
        },
    }
    os.makedirs(RES, exist_ok=True)
    with open(os.path.join(RES, "axioms_graph.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print("=== 六条公理在图论情形 ===")
    for k, v in out["axiom_status"].items():
        print(f"  {k}: {v['status']}")
    print("\n=== 光谱多重度（公理5）===")
    for name, p in profiles.items():
        print(f"  {name:10s} simple={p['simple_spectrum']}  mults={p['multiplicities']}")
    print("\n=== 谱嵌入单射性（公理1，预期全 True）===")
    print("  all injective:", all(v["injective"] for v in inj.values()))
    print("\n=== 生成性推论：Petersen □ K2 ===")
    print("  谱由因子预测并通过验证:", prod_pred_ok)
    print("  相变结构:", prod)
    print("[done]", os.path.join(RES, "axioms_graph.json"))


if __name__ == "__main__":
    main()
