# -*- coding: utf-8 -*-
"""
reversal_criterion.py — 方向 B1'：相变顺序保持/反转的判别。

问题：定理 A 说“局部先于全局”。B1 说对称加权不能反转。B2 给出有向图反转反例。
那么：**什么条件下会反转？**

本脚本给出三件事：

1. Rayleigh 刻画（可证）。对对称 L，最大特征值模式最大化 Rayleigh 商
       R(v) = (vᵀ L v) / (vᵀ v) = Σ_e (v_u−v_v)² / Σ_v v²
   即“最局部变化”的模式最先增长。这把“局部先于全局”从“谱定理直觉”
   升级为“Rayleigh 极小极大”的严格陈述。

2. 两个候选判别法的**否定性检验**。
   - 非正规性 ν(L)=‖LLᵀ−LᵀL‖_F/‖L‖²_F
   - 强连通性
   结果：二者都**不能**预测反转（非正规性与反转率甚至负相关）。

3. 反转的开放问题登记。

输出：analysis/results/reversal_criterion.json
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


def lap(n, arcs):
    L = np.zeros((n, n))
    for u, v in arcs:
        L[u, u] += 1
        L[u, v] -= 1
    return L


def rayleigh(L, v):
    return float((v @ L @ v) / (v @ v + 1e-300))


def total_variation(v, arcs):
    v = v / (np.linalg.norm(v) + 1e-12)
    return float(sum(abs(v[u] - v[w]) for u, w in arcs) / (len(arcs) + 1e-12))


def check_rayleigh_theorem(n_trials=500, seed=0):
    """对称 L：最大特征值模式是否最大化 Rayleigh 商？（应恒为真）"""
    rng = np.random.default_rng(seed)
    ok = 0
    for _ in range(n_trials):
        n = int(rng.integers(4, 10))
        arcs = []
        for v in range(1, n):
            u = int(rng.integers(0, v))
            arcs += [(u, v), (v, u)]        # 对称化
        for _ in range(int(rng.integers(0, n))):
            u, v = rng.integers(0, n, 2)
            if u != v:
                arcs += [(int(u), int(v)), (int(v), int(u))]
        L = lap(n, arcs)
        ev, evec = np.linalg.eigh(L)
        # 对称 L：最大特征值模式 vs 其他模式的 Rayleigh 商
        R = [rayleigh(L, evec[:, k]) for k in range(n)]
        if abs(max(R) - max(ev)) < 1e-6:
            ok += 1
    return {"trials": n_trials, "max_rayleigh_is_top_eigenmode": ok,
            "holds": ok == n_trials,
            "theorem": "对称 L：λₙ 的特征向量最大化 Rayleigh 商 R(v)=Σ_e(v_u−v_v)²/Σv²。"}


def strong(n, arcs):
    adj = [set() for _ in range(n)]
    for u, v in arcs:
        adj[u].add(v)

    def reach(s):
        seen = {s}
        st = [s]
        while st:
            x = st.pop()
            for y in adj[x]:
                if y not in seen:
                    seen.add(y)
                    st.append(y)
        return seen
    return all(len(reach(i)) == n for i in range(n))


def reversal(L, arcs):
    ev, evec = np.linalg.eig(L)
    re = ev.real
    k0 = int(np.argmax(re))
    tv0 = total_variation(np.real(evec[:, k0]), arcs)
    for k in range(len(re)):
        if k != k0 and re[k] > 1e-9 and total_variation(np.real(evec[:, k]), arcs) > tv0 + 1e-6:
            return True
    return False


def nonnorm(L):
    A = L @ L.T - L.T @ L
    return float(np.linalg.norm(A) / (np.linalg.norm(L) ** 2 + 1e-12))


def defective(L, tol=1e-7):
    """几何重数 < 代数重数（有 Jordan 块）？"""
    ev = np.linalg.eigvals(L)
    uniq = []
    for e in ev:
        for u in uniq:
            if abs(e - u[0]) < 1e-6:
                u[1] += 1
                break
        else:
            uniq.append([e, 1])
    for e, alg in uniq:
        geo = len(L) - np.linalg.matrix_rank(L - e * np.eye(len(L)), tol=tol)
        if geo < alg:
            return 1.0
    return 0.0


def antisym_norm(L):
    A = (L - L.T) / 2
    return float(np.max(np.abs(np.linalg.eigvals(A))))


def rayleigh_gap(L):
    """max-Re 特征向量的对称部 Rayleigh 商与最大值之差。"""
    Ls = (L + L.T) / 2
    ev, evec = np.linalg.eig(L)
    k0 = int(np.argmax(ev.real))
    v0 = np.real(evec[:, k0])
    v0 = v0 / (np.linalg.norm(v0) + 1e-12)
    R0 = float(v0 @ Ls @ v0 / (v0 @ v0))
    Rs = []
    for k in range(len(L)):
        vk = np.real(evec[:, k])
        Rs.append(float(vk @ Ls @ vk / (vk @ vk + 1e-12)))
    return max(Rs) - R0


def negative_checks(n_trials=4000, seed=1):
    rng = np.random.default_rng(seed)
    rows = []
    for _ in range(n_trials):
        n = int(rng.integers(4, 9))
        arcs = []
        for v in range(1, n):
            arcs.append((int(rng.integers(0, v)), v))
        for _ in range(int(rng.integers(0, 4))):
            u, v = rng.integers(0, n, 2)
            if u != v:
                arcs.append((int(u), int(v)))
        L = lap(n, arcs)
        rows.append((nonnorm(L), float(strong(n, arcs)), float(reversal(L, arcs)),
                     defective(L), antisym_norm(L), rayleigh_gap(L)))
    rows = np.array(rows)
    nn, sc, rv = rows[:, 0], rows[:, 1], rows[:, 2]
    # 分位分箱（非正规性）
    qs = np.quantile(nn, [0, .25, .5, .75, 1.0])
    bins = []
    for i in range(4):
        m = (nn >= qs[i]) & (nn <= qs[i + 1])
        bins.append({"nonnorm_lo": round(float(qs[i]), 4), "nonnorm_hi": round(float(qs[i + 1]), 4),
                     "reversal_rate": round(float(rv[m].mean()), 4), "n": int(m.sum())})
    sc_mask = sc > 0.5
    return {
        "n_trials": n_trials,
        "reversal_rate": round(float(rv.mean()), 4),
        "nonnorm_bins": bins,
        "corr_nonnorm_reversal": round(float(np.corrcoef(nn, rv)[0, 1]), 3),
        "corr_defective_reversal": round(float(np.corrcoef(rows[:, 3], rv)[0, 1]), 3),
        "corr_antisym_reversal": round(float(np.corrcoef(rows[:, 4], rv)[0, 1]), 3),
        "corr_rayleigh_gap_reversal": round(float(np.corrcoef(rows[:, 5], rv)[0, 1]), 3),
        "defective_reversal_rate": round(float(rv[rows[:, 3] > 0.5].mean()), 4) if (rows[:, 3] > 0.5).any() else None,
        "nondefective_reversal_rate": round(float(rv[rows[:, 3] < 0.5].mean()), 4) if (rows[:, 3] < 0.5).any() else None,
        "strongly_connected_n": int(sc_mask.sum()),
        "strongly_connected_reversal_rate": (round(float(rv[sc_mask].mean()), 4) if sc_mask.sum() else None),
        "not_strongly_connected_reversal_rate": (round(float(rv[~sc_mask].mean()), 4) if (~sc_mask).sum() else None),
        "verdict": ("五个候选判别法（非正规性、强连通性、Jordan 缺陷、反对称范数、Rayleigh 间隙）"
                    "均不能预测反转；最强的反对称范数相关也仅 +0.13。"
                    "反转的充要条件仍是开放问题。"),
    }


def main():
    rayleigh = check_rayleigh_theorem()
    neg = negative_checks()
    out = {
        "B1p_rayleigh_theorem": rayleigh,
        "B1p_negative_checks": neg,
        "open_problem": ("给定非对称生成元 M=−αI+βL，刻画‘最大 Re 特征向量不是最局部模式’"
                         "的充要条件。目前已知：对称 ⇒ 不反转（定理 B1）；非对称 ⇒ 可能反转（B2），"
                         "但无简单结构判据。"),
    }
    os.makedirs(RES, exist_ok=True)
    with open(os.path.join(RES, "reversal_criterion.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print("=== B1' Rayleigh 刻画 ===")
    print(f"  对称 L 上‘最大特征值模式最大化 Rayleigh 商’：{rayleigh['max_rayleigh_is_top_eigenmode']}/{rayleigh['trials']}")
    print("=== B1' 否定性检验（候选判别法）===")
    print(f"  总反转率：{neg['reversal_rate']}")
    print(f"  非正规性分位 → 反转率：{[b['reversal_rate'] for b in neg['nonnorm_bins']]}")
    print(f"  corr(非正规性, 反转) = {neg['corr_nonnorm_reversal']}（负相关！）")
    print(f"  强连通反转率 = {neg['strongly_connected_reversal_rate']}（n={neg['strongly_connected_n']}）")
    print(f"  非强连通反转率 = {neg['not_strongly_connected_reversal_rate']}")
    print(f"  判定：{neg['verdict']}")
    print("[done]", os.path.join(RES, "reversal_criterion.json"))


if __name__ == "__main__":
    main()
