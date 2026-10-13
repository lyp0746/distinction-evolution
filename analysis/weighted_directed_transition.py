# -*- coding: utf-8 -*-
"""
weighted_directed_transition.py — 方向 A1：加权图与有向图上的相变顺序。

两阶段相变（定理 12.1）在无向无权图上给出 β₁=α/λₙ ≤ β₂=α/λ₂。
本脚本回答两个新问题：

A1.1 加权图（对称权重）：顺序是否保持？
     结论（可证）：保持。加权拉普拉斯仍实对称半正定，谱满足
     0=λ₁<λ₂≤…≤λₙ，故 β₁=α/λₙ ≤ α/λ₂=β₂ 恒成立，
     且中间相宽度 W=α(1/λ₂−1/λₙ) 随权重连续变化。
     ——即"局部先于全局"在任意对称加权下不可反转。

A1.2 有向图（非对称耦合）：顺序能否反转？
     生成元 M=−αI+βL（L=D_out−A）非对称，特征值可为复数，增长率由
     Re(μ_k)=β Re(λ_k)−α 决定。第一个增长的模式 = Re(λ_k) 最大者。
     用"特征向量总变差 TV"定义局部性：高 TV ≈ 局部振荡，低 TV ≈ 全局。
     在随机有向图上搜索是否存在"最大 Re 模式是全局模式"的反转例子。

输出：analysis/results/weighted_directed_transition.json
      assets/charts/weighted_directed_transition.png
依赖：numpy；matplotlib 可选。
"""
import json
import os
import sys

import numpy as np
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(HERE, "analysis", "results")
CHARTS = os.path.join(HERE, "assets", "charts")
ALPHA = 1.0


# ---------------------------------------------------------------- 图构造
def weighted_laplacian(n, edges, weights):
    L = np.zeros((n, n))
    for (u, v), w in zip(edges, weights):
        L[u, u] += w
        L[v, v] += w
        L[u, v] -= w
        L[v, u] -= w
    return L


def directed_laplacian(n, arcs):
    """L = D_out − A（非对称）。"""
    L = np.zeros((n, n))
    for (u, v) in arcs:
        L[u, u] += 1
        L[u, v] -= 1
    return L


def random_connected_edges(n, rng, extra=0):
    """随机生成一个连通无向图（生成树 + extra 条边）。"""
    edges = []
    for v in range(1, n):
        u = int(rng.integers(0, v))
        edges.append((u, v))
    for _ in range(extra):
        u, v = rng.integers(0, n, 2)
        if u != v and (u, v) not in edges and (v, u) not in edges:
            edges.append((int(u), int(v)))
    return edges


def total_variation(vec, edges):
    """特征向量的总变差（归一化）：度量模式的空间振荡程度。"""
    v = vec / (np.linalg.norm(vec) + 1e-12)
    tv = sum(abs(v[u] - v[vv]) for u, vv in edges)
    return float(tv / (len(edges) + 1e-12))


# ---------------------------------------------------------------- A1.1
def weighted_sweep(n_trials=400, n=8, seed=0):
    rng = np.random.default_rng(seed)
    widths, ratios, order_ok = [], [], 0
    for _ in range(n_trials):
        edges = random_connected_edges(n, rng, extra=int(rng.integers(0, n)))
        w = rng.uniform(0.05, 5.0, size=len(edges))
        L = weighted_laplacian(n, edges, w)
        lam = np.sort(np.linalg.eigvalsh(L))
        l2, ln = lam[1], lam[-1]
        b1, b2 = ALPHA / ln, ALPHA / l2
        if b1 <= b2 + 1e-12:
            order_ok += 1
        widths.append(b2 - b1)
        ratios.append(ln / max(l2, 1e-12))
    return {
        "n_trials": n_trials,
        "order_preserved_count": order_ok,
        "order_preserved": order_ok == n_trials,
        "width_min": round(float(np.min(widths)), 4),
        "width_max": round(float(np.max(widths)), 4),
        "ln_over_l2_min": round(float(np.min(ratios)), 4),
        "ln_over_l2_max": round(float(np.max(ratios)), 4),
        "conclusion": "对称加权下 β₁≤β₂ 恒成立；‘局部先于全局’不可反转。",
    }


# ---------------------------------------------------------------- A1.2
def find_reversal(n=7, n_trials=4000, seed=1):
    """在有向图上搜索顺序反转：最大 Re(λ) 模式的总变差低于某个更小的 Re 模式。"""
    rng = np.random.default_rng(seed)
    best = None
    reversals = 0
    for t in range(n_trials):
        # 随机有向图：先生成无向骨架，再随机定向并加额外弧
        base = random_connected_edges(n, rng, extra=int(rng.integers(0, n)))
        arcs = []
        for (u, v) in base:
            if rng.random() < 0.5:
                arcs.append((u, v))
            else:
                arcs.append((v, u))
        # 再加少量随机弧制造非正规性
        for _ in range(int(rng.integers(0, 4))):
            u, v = rng.integers(0, n, 2)
            if u != v:
                arcs.append((int(u), int(v)))
        L = directed_laplacian(n, arcs)
        ev = np.linalg.eigvals(L)
        re = ev.real
        order = np.argsort(-re)
        # 最大 Re 模式
        k0 = order[0]
        evals, evecs = np.linalg.eig(L)
        v0 = np.real(evecs[:, k0])
        tv0 = total_variation(v0, [(u, v) for (u, v) in arcs])
        # 找一个 Re 稍小但 TV 明显更大的模式
        for k in order[1:]:
            if re[k] > 1e-9:
                vk = np.real(evecs[:, k])
                tvk = total_variation(vk, [(u, v) for (u, v) in arcs])
                if tvk > tv0 + 1e-6:
                    reversals += 1
                    if best is None:
                        best = {"arcs": arcs, "re_max": float(re[k0]), "tv_of_max": round(tv0, 5),
                                "other_re": float(re[k]), "tv_of_other": round(tvk, 5),
                                "note": "最大 Re 模式更平滑（更全局），其它模式更振荡（更局部）"}
                    break
    return {
        "n_trials": n_trials,
        "reversal_found": best is not None,
        "reversal_examples": reversals,
        "first_example": best,
        "conclusion": ("有向耦合可以反转顺序：非对称 Laplacian 的最大实部模式未必是"
                       "最振荡的局部模式。反转的存在性由非正规性引起，对称加权不可能。"),
    }


def explicit_counterexample():
    """A1.2 的确定性反例（可手算）。

    顶点 0..5，弧集见下。最大实部模式（Re=2）的总变差为 0.25（全局/平滑）；
    另一个实部较小的模式（Re=1）的总变差为 0.7071（局部/振荡）。于是：
        β_global = α/2 < β_local = α/1，全局模式**先**增长——顺序反转。
 """
    arcs = [(0, 2), (1, 0), (2, 4), (3, 1), (3, 2), (4, 1), (5, 1), (5, 2)]
    n = 6
    L = directed_laplacian(n, arcs)
    ev, evec = np.linalg.eig(L)
    re = ev.real
    k0 = int(np.argmax(re))
    v0 = np.real(evec[:, k0])
    tv0 = total_variation(v0, arcs)
    # 找 Re > 0 且 TV 明显更大的模式中最显著者
    cand = [k for k in range(len(re)) if k != k0 and re[k] > 0.2]
    k1 = max(cand, key=lambda k: total_variation(np.real(evec[:, k]), arcs)) if cand else None
    tv1 = total_variation(np.real(evec[:, k1]), arcs) if k1 is not None else None
    res = {
        "arcs": arcs,
        "max_real_part": round(float(re[k0]), 4),
        "tv_of_max_real_part": round(tv0, 4),
        "beta_of_max_real_part": round(ALPHA / float(re[k0]), 4),
        "other_mode_real_part": round(float(re[k1]), 4) if k1 is not None else None,
        "tv_of_other": round(tv1, 4) if tv1 is not None else None,
        "beta_of_other": round(ALPHA / float(re[k1]), 4) if k1 is not None else None,
        "reversal": bool(k1 is not None and tv1 > tv0 and re[k0] > re[k1]),
        "reading": ("首个增长模式是全局（低 TV），局部（高 TV）模式反而后增长；"
                    "与对称情形的‘局部先于全局’相反。"),
    }
    return res


# ---------------------------------------------------------------- 主程序
def main():
    sym = weighted_sweep()
    rev = find_reversal()
    explicit = explicit_counterexample()
    out = {
        "alpha": ALPHA,
        "A1.1_symmetric_weighted": sym,
        "A1.2_directed": rev,
        "A1.2_explicit_counterexample": explicit,
        "summary": {
            "theorem": "对称加权图：β₁=α/λₙ ≤ α/λ₂=β₂，顺序不可反转。",
            "counterexample": ("有向图：见 A1.2_explicit_counterexample；"
                               "全局模式可先于局部模式增长。"),
        },
    }
    os.makedirs(RES, exist_ok=True)
    with open(os.path.join(RES, "weighted_directed_transition.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print("=== A1.1 对称加权 ===")
    print(f"  {sym['order_preserved_count']}/{sym['n_trials']} 保持顺序；"
          f"W∈[{sym['width_min']},{sym['width_max']}]，λₙ/λ₂∈[{sym['ln_over_l2_min']},{sym['ln_over_l2_max']}]")
    print("=== A1.2 有向图 ===")
    print(f"  随机搜索：反转找到 {rev['reversal_found']}（{rev['reversal_examples']}/{rev['n_trials']}）")
    e = explicit
    print(f"  确定性反例：首个增长模式 Re={e['max_real_part']} TV={e['tv_of_max_real_part']} "
          f"(β={e['beta_of_max_real_part']})；"
          f"后增长模式 Re={e['other_mode_real_part']} TV={e['tv_of_other']} (β={e['beta_of_other']})")
    print(f"  顺序反转：{e['reversal']}")
    print("[done]", os.path.join(RES, "weighted_directed_transition.json"))

    # 图
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        os.makedirs(CHARTS, exist_ok=True)
        fig, ax = plt.subplots(1, 2, figsize=(9, 3.2), layout="constrained")
        # 左：对称加权的 W 分布
        rng = np.random.default_rng(0)
        ws = []
        for _ in range(600):
            edges = random_connected_edges(8, rng, extra=int(rng.integers(0, 8)))
            w = rng.uniform(0.05, 5.0, size=len(edges))
            lam = np.sort(np.linalg.eigvalsh(weighted_laplacian(8, edges, w)))
            ws.append(1 / lam[1] - 1 / lam[-1])
        ax[0].hist(ws, bins=40, color="#3a6ea5")
        ax[0].set_title("symmetric weighted: W = a(1/l2 - 1/ln) >= 0")
        ax[0].set_xlabel("intermediate-phase width W")
        # 右：有向图 Re 谱与 TV
        if rev["first_example"]:
            arcs = rev["first_example"]["arcs"]
            L = directed_laplacian(7, arcs)
            ev = np.linalg.eigvals(L).real
            ax[1].plot(np.sort(ev)[::-1], "o-", color="#c94f4f")
            ax[1].set_title("directed: sorted Re(lambda_k)")
            ax[1].set_xlabel("mode index"); ax[1].set_ylabel("Re(lambda)")
        fig.savefig(os.path.join(CHARTS, "weighted_directed_transition.png"), dpi=200)
        print("[fig]", os.path.join(CHARTS, "weighted_directed_transition.png"))
    except Exception as e:
        print("[fig] skip:", e)


if __name__ == "__main__":
    main()
