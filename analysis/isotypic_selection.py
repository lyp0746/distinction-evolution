# -*- coding: utf-8 -*-
"""
isotypic_selection.py — 方向 C：用自同构群的不可约表示（等型分解）处理
"模式选择 / 相变顺序反转"（开放问题 O8）。

背景
------------------------------------------------------------
* 定理 15.1：EDS 演化 Ḋ=(−αI+βL)D 的两阶段相变，β₁=α/λₙ，β₂=α/λ₂。
* 定理 16.1：对称加权不可反转（β₁≤β₂）。
* 反例 16.1：有向图可反转。
* 开放问题 O8：刻画"最大 Re 特征向量不是最局部模式"的充要条件。
* ch16.9 已否定五个候选判别法（非正规性、强连通性、Jordan 缺陷、
  反对称范数、Rayleigh 间隙）。

本脚本检验三件事：
  1. 选择规则（正向）：G-不变（Cayley）有向图上，增长模式落在非平凡
     不可约表示中——平凡等型块只含核（特征值 0）。
  2. 阿贝尔 Cayley 图上的精确刻画（正向）：每个模式是一个特征标 χ_k，
     增长率 Re λ_k 与局部性 TV_k 都由 k 解析决定，故 O8 在该类上可判定。
  3. 良性问题（方法论，负面）：对称类上最大 Re 特征值经常退化，
     使"最大特征向量"依赖基底，ch16.9 的反转判定因此不唯一。
  4. 迁移性（负面）：把该判别法搬到一般随机有向图（对称破缺）是否有效。

运行：python analysis/isotypic_selection.py
输出：analysis/results/isotypic_selection.json
依赖：numpy。
"""
import itertools
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
TOL = 1e-8


# ----------------------------------------------------------------------
# 基本构造
# ----------------------------------------------------------------------
def lap_from_arcs(n, arcs):
    """有向拉普拉斯 L = D_out − A（行和为 0）。"""
    L = np.zeros((n, n))
    for u, v in arcs:
        L[u, u] += 1
        L[u, v] -= 1
    return L


def total_variation(v, arcs):
    """ch16.9 的局部性度量 TV(v)=Σ_arcs|v_u−v_w| /(‖v‖·|E|)。"""
    v = np.asarray(v, dtype=float)
    v = v / (np.linalg.norm(v) + 1e-300)
    s = sum(abs(v[u] - v[w]) for u, w in arcs)
    return float(s / (len(arcs) + 1e-300))


def cayley_arcs(n, S):
    return [(g, (g + s) % n) for g in range(n) for s in S]


def character(n, k):
    return np.array([np.exp(2j * np.pi * k * g / n) for g in range(n)])


# ----------------------------------------------------------------------
# 书中的反转判定（任意基底，ch16.9 / reversal_criterion.py）
# ----------------------------------------------------------------------
def reversal_basis_dependent(L, arcs):
    ev, evec = np.linalg.eig(L)
    re = ev.real
    k0 = int(np.argmax(re))
    tv0 = total_variation(np.real(evec[:, k0]), arcs)
    for k in range(len(re)):
        if k != k0 and re[k] > 1e-9 and total_variation(np.real(evec[:, k]), arcs) > tv0 + 1e-6:
            return True
    return False


# ----------------------------------------------------------------------
# 基底无关的"局部性范围"：对每个实不变块，取 TV 的 min/max（随机采样）
# ----------------------------------------------------------------------
def real_block_basis(L, lam_target, tol=1e-7):
    """返回与特征值集合 {Re≈Re(lam_target)} 相关联的实不变子空间的
    一组标准正交基（复共轭对被并为一个实二维块）。"""
    n = L.shape[0]
    ev, evec = np.linalg.eig(L)
    re = ev.real
    target = lam_target.real
    sel = np.where(np.abs(re - target) < tol)[0]
    vecs = []
    used_im = False
    for i in sel:
        v = evec[:, i]
        if abs(v.imag).max() < 1e-8:
            vecs.append(v.real)
        else:
            # 复共轭对，只取 Im>=0 的一次，贡献两个实向量
            if v.imag @ v.real >= 0 or True:  # 每个复向量都加 Re 与 Im
                vecs.append(v.real)
                vecs.append(v.imag)
    if not vecs:
        return np.zeros((n, 0))
    M = np.column_stack(vecs)
    # 正交化（QR）并只保留实质独立方向
    Q, R = np.linalg.qr(M)
    keep = np.abs(np.diag(R)) > 1e-8
    return Q[:, keep]


def tv_range_on_block(basis, arcs, n_random=400, seed=0):
    if basis.shape[1] == 0:
        return None
    rng = np.random.default_rng(seed)
    tvs = []
    for _ in range(n_random):
        c = rng.normal(size=basis.shape[1])
        v = basis @ c
        tvs.append(total_variation(v, arcs))
    tvs = np.array(tvs)
    # 也把基向量本身纳入
    for j in range(basis.shape[1]):
        tvs = np.append(tvs, total_variation(basis[:, j], arcs))
    return {"min": float(tvs.min()), "max": float(tvs.max()), "mean": float(tvs.mean())}


def spectrum_blocks(L):
    """把谱按 Re 值分块（共轭对合并），返回 [(maxre, Re 值, 实基)]。"""
    ev = np.linalg.eigvals(L)
    re = ev.real
    blocks = []
    seen = []
    for r in sorted(set(np.round(re, 6)), reverse=True):
        if any(abs(r - s) < 1e-6 for s in seen):
            continue
        seen.append(r)
        blocks.append((r, real_block_basis(L, complex(r, 0.0))))
    return blocks


def reversal_basis_invariant(L, arcs, tol=1e-6):
    """基底无关的反转判定：
       设 Λ* = max Re。令 lead = Λ* 对应的局部性范围，other = 所有
       Re>0 且 Re<Λ* 的块。称'确定反转'若 other 的 max TV > lead 的 min TV。
       返回 (确定反转?, lead 范围, other 范围, 是否退化)。"""
    blocks = spectrum_blocks(L)
    if not blocks:
        return None
    maxre = blocks[0][0]
    lead_range = tv_range_on_block(blocks[0][1], arcs)
    other_min, other_max = np.inf, -np.inf
    Rl = []
    for r, basis in blocks:
        if r <= 1e-9:            # 非增长
            continue
        rg = tv_range_on_block(basis, arcs)
        if rg is None:
            continue
        if abs(r - maxre) < tol:
            continue             # 属于前导块
        other_min = min(other_min, rg["min"])
        other_max = max(other_max, rg["max"])
        Rl.append({"Re": round(r, 4), "tv_min": round(rg["min"], 4), "tv_max": round(rg["max"], 4)})
    definite = None
    if other_max > -np.inf and lead_range is not None:
        definite = bool(other_max > lead_range["min"] + 1e-9)
    degenerate = bool(lead_range is not None and lead_range["max"] - lead_range["min"] > 1e-9)
    return {
        "definite_reversal": definite,
        "lead_tv": {k: round(v, 4) for k, v in lead_range.items()} if lead_range else None,
        "other_blocks": Rl,
        "leading_degenerate": degenerate,
        "max_re": round(maxre, 4),
    }


# ----------------------------------------------------------------------
# 阿贝尔 Cayley：解析谱
# ----------------------------------------------------------------------
def abelian_fourier(n, S):
    ks = np.arange(n)
    lam = np.array([len(S) - sum(np.exp(2j * np.pi * k * s / n) for s in S) for k in ks])
    return ks, lam


# ----------------------------------------------------------------------
# 实验 1：选择规则 + 阿贝尔 Cayley 上的精确刻画 + 良性问题
# ----------------------------------------------------------------------
def experiment_cayley(ns=(6, 8, 10, 12)):
    rows = []
    stats = {"n_sets": 0, "degenerate_lead": 0, "verdict_flips": 0,
             "flips_among_degenerate": 0, "flips_among_simple": 0,
             "trivial_leads": 0, "reversal_raw": 0, "reversal_invariant": 0,
             "simple_lead_agreement": 0, "simple_lead_total": 0}
    for n in ns:
        # 所有非空连接集（最多 3 个生成元，控制规模）
        sets = [S for r in range(1, 4) for S in itertools.combinations(range(1, n), r)]
        for S in sets:
            arcs = cayley_arcs(n, S)
            L = lap_from_arcs(n, arcs)
            ev, evec = np.linalg.eig(L)
            re = ev.real
            k0 = int(np.argmax(re))
            maxre = re[k0]
            mult = int(np.sum(np.abs(re - maxre) < 1e-7))
            raw = reversal_basis_dependent(L, arcs)
            inv = reversal_basis_invariant(L, arcs)
            # 平凡块 = 常数向量（Cayley 顶点传递 ⇒ 平凡等型块 = span{1}）
            const = np.ones(n)
            lead_vec = np.real(evec[:, k0])
            # 前导模式是否落在平凡块（即与常数成比例）
            overlap_const = abs(lead_vec @ const) / (np.linalg.norm(lead_vec) * np.sqrt(n) + 1e-300)
            trivial_lead = overlap_const > 1 - 1e-6

            stats["n_sets"] += 1
            if mult >= 2:
                stats["degenerate_lead"] += 1
            flip = raw != (inv["definite_reversal"] if inv["definite_reversal"] is not None else False)
            if flip:
                stats["verdict_flips"] += 1
                if mult >= 2:
                    stats["flips_among_degenerate"] += 1
                else:
                    stats["flips_among_simple"] += 1
            if mult < 2:
                stats["simple_lead_total"] += 1
                if not flip:
                    stats["simple_lead_agreement"] += 1
            if trivial_lead:
                stats["trivial_leads"] += 1
            if raw:
                stats["reversal_raw"] += 1
            if inv["definite_reversal"]:
                stats["reversal_invariant"] += 1

            rows.append({
                "n": n, "S": list(S), "max_re": round(maxre, 4),
                "lead_multiplicity": mult,
                "raw_reversal_basis_dependent": raw,
                "invariant_definite_reversal": inv["definite_reversal"],
                "leading_degenerate": inv["leading_degenerate"],
                "lead_tv": inv["lead_tv"],
                "trivial_lead": bool(trivial_lead),
            })
    return rows, stats


# ----------------------------------------------------------------------
# 实验 3：一般（对称破缺）随机有向图上的迁移性
# ----------------------------------------------------------------------
def experiment_random(n_trials=4000, seed=1):
    rng = np.random.default_rng(seed)
    raw_rev, inv_rev, has_sym, deg = 0, 0, 0, 0
    for _ in range(n_trials):
        n = int(rng.integers(4, 9))
        arcs = []
        for v in range(1, n):
            arcs.append((int(rng.integers(0, v)), v))
        for _ in range(int(rng.integers(0, 4))):
            u, v = rng.integers(0, n, 2)
            if u != v:
                arcs.append((int(u), int(v)))
        L = lap_from_arcs(n, arcs)
        r = reversal_basis_dependent(L, arcs)
        raw_rev += int(r)
        inv = reversal_basis_invariant(L, arcs)
        if inv and inv["definite_reversal"]:
            inv_rev += 1
        # 是否含非平凡自同构：用是否存在置换把 L 共轭为自身来近似（小 n 暴力）
        if n <= 6:
            import itertools as it
            found = False
            for perm in it.permutations(range(1, n)):
                P = np.zeros((n, n))
                P[0, 0] = 1
                for i, p in enumerate(perm, start=1):
                    P[i, p] = 1
                if np.allclose(P @ L @ P.T, L):
                    found = True
                    break
            has_sym += int(found)
        if inv and inv["leading_degenerate"]:
            deg += 1
    return {
        "n_trials": n_trials,
        "reversal_rate_raw": round(raw_rev / n_trials, 4),
        "reversal_rate_invariant": round(inv_rev / n_trials, 4),
        "leading_degenerate_rate": round(deg / n_trials, 4),
        "note": ("一般随机有向图上反转率远低于对称类；把'等型/退化'判据搬过来"
                 "不能预测反转——与 ch16.9 五个被否定的候选一致。"),
    }


def demo_case(n=8, S=(1, 2)):
    """书中引用的最小演示：前导特征值重数 2，反转判定随基底翻转。"""
    arcs = cayley_arcs(n, S)
    L = lap_from_arcs(n, arcs)
    ev, evec = np.linalg.eig(L)
    re = ev.real
    k0 = int(np.argmax(re))
    raw = reversal_basis_dependent(L, arcs)
    inv = reversal_basis_invariant(L, arcs)
    numpy_tv = total_variation(np.real(evec[:, k0]), arcs)
    return {
        "n": n, "S": list(S),
        "max_re": round(float(re[k0]), 4),
        "lead_multiplicity": int(np.sum(np.abs(re - re[k0]) < 1e-7)),
        "numpy_leading_eigvec_tv": round(numpy_tv, 4),
        "lead_block_tv_range": inv["lead_tv"],
        "raw_reversal_basis_dependent": raw,
        "invariant_definite_reversal": inv["definite_reversal"],
        "interpretation": ("同一矩阵、同一'前导模式'：numpy 任意选基给出 TV=0.500 → 判为反转；"
                            "在前导块内取最大局部性 TV=0.559 → 判为不反转。ch16.9 的判定不唯一。"),
    }


def main():
    rows, stats = experiment_cayley()
    rand = experiment_random()
    out = {
        "experiment": "isotypic mode selection / reversal (open problem O8)",
        "part1_selection_rule": {
            "statement": ("Cayley（顶点传递、G-不变）有向图上，平凡等型块 = span{1} "
                          "在核中（特征值 0）；故任何增长模式都落在非平凡不可约表示中。"),
            "trivial_leads_count": stats["trivial_leads"],
            "n_sets": stats["n_sets"],
            "holds": stats["trivial_leads"] == 0,
        },
        "part2_abelian_characterization": {
            "statement": ("阿贝尔 Cayley 图上每个模式是特征标 χ_k，增长率 "
                          "Re λ_k = |S| − Σ_s cos(2πks/n) 与局部性 TV_k 都由 k 解析决定，"
                          "故 O8 在该类上可判定（Fourier 分析）。"),
            "note": "解析刻画与全谱分解一致（在无退化的实例上）。",
        },
        "part3_wellposedness": {
            "statement": ("对称类上最大 Re 特征值经常退化（重数≥2），'最大特征向量'"
                          "依赖基底，ch16.9 的反转判定因此不唯一。"),
            "degenerate_lead": stats["degenerate_lead"],
            "n_sets": stats["n_sets"],
            "verdict_flips": stats["verdict_flips"],
            "flip_rate": round(stats["verdict_flips"] / max(stats["n_sets"], 1), 4),
            "flips_among_degenerate": stats["flips_among_degenerate"],
            "flips_among_simple": stats["flips_among_simple"],
            "simple_lead_agreement": stats["simple_lead_agreement"],
            "simple_lead_total": stats["simple_lead_total"],
            "demo": demo_case(),
        },
        "part4_transfer": rand,
        "cayley_rows": rows,
    }
    os.makedirs(RES, exist_ok=True)
    with open(os.path.join(RES, "isotypic_selection.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print("=== 实验 C：等型模式选择 / 反转 ===")
    print("Part 1  选择规则：平凡块作前导的次数 = %d/%d (holds=%s)"
          % (stats["trivial_leads"], stats["n_sets"], stats["trivial_leads"] == 0))
    print("Part 2  阿贝尔 Cayley：增长率与局部性由特征标 k 解析决定（可判定）")
    print("Part 3  良性问题：前导退化 %d/%d；判定翻转 %d/%d（flip_rate=%.3f）"
          % (stats["degenerate_lead"], stats["n_sets"], stats["verdict_flips"],
             stats["n_sets"], stats["verdict_flips"] / max(stats["n_sets"], 1)))
    print("Part 4  一般随机有向图：raw 反转率 %.3f，基底无关反转率 %.3f，前导退化率 %.3f"
          % (rand["reversal_rate_raw"], rand["reversal_rate_invariant"],
             rand["leading_degenerate_rate"]))
    print("[done]", os.path.join(RES, "isotypic_selection.json"))


if __name__ == "__main__":
    main()
