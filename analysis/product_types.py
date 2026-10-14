# -*- coding: utf-8 -*-
"""
product_types.py — 第 20.2.2 节：笛卡尔积下的"类型匹配"核算。

背景（对话中提出、本脚本核实）
------------------------------------------------------------
一个流行的说法是：EDS 的内部结构是"加法性"的，拓扑不变量是"乘法性"的，
1/3 缺口是这种"加法内部性 vs 乘法外部性"的必然结果。

本脚本把可计算的部分全部算出来，得到三条结论：

  G10  Δ0 热核迹在笛卡尔积下**乘法性**成立（Kronecker 和 + 指数律）：
         Tr(e^{-tΔ0(G□H)}) = Tr(e^{-tΔ0(G)})·Tr(e^{-tΔ0(H)})
  G11  Δ1（边拉普拉斯）热核迹**不**满足乘法性（交叉项 B_G⊗B_H^T ≠ 0）。
  G12  超迹 X(t)=Tr(e^{-tΔ0})-Tr(e^{-tΔ1}) **不**满足乘法性。
  G13  χ(G□H) = χ(G)·χ(H) − |E_G|·|E_H|（精确公式）。
  G14  谱测度满足卷积：μ_{G□H} = μ_G * μ_H。

**关键诊断（与对话的不同处）**：G13 的亏项 |E_G|·|E_H| 恰是**产品复形的 2-胞腔数**。
补上 2-胞腔后 V−E+F = χ(G)·χ(H) 精确成立。因此所谓"类型不匹配"的准确表述是：
**图是 1-维复形，没有 2-胞腔；两个 1-复形之积是 2-维的，而 χ 只在完整产品复形上乘法。**
EDS 定义在 1-骨架上，看不见 2-胞腔——这与第 5 章"缺少粘合/高阶结构"是同一件事。

**并且**：这一分析**不解释** 1/3 缺口（那是固定二维曲面上"密度归一化 vs 欧拉密度"
的另一个轴）。G10—G14 是**标准事实**，不是本书的新定理；它们的价值是把一个漂亮的
口号（"加法 vs 乘法"）钉成可复算的语句，并指出它不是缺口的根源。

运行：python analysis/product_types.py
输出：analysis/results/product_types.json
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


def build(n, edges):
    A = np.zeros((n, n))
    for u, v in edges:
        A[u, v] = A[v, u] = 1
    return A


def lap(A):
    return np.diag(A.sum(1)) - A


def incidence(A):
    n = len(A)
    E = [(i, j) for i in range(n) for j in range(i + 1, n) if A[i, j]]
    B = np.zeros((len(E), n))
    for k, (i, j) in enumerate(E):
        B[k, i] = 1
        B[k, j] = -1
    return B


def edge_lap(A):
    B = incidence(A)
    return B @ B.T


def tr_exp(L, t):
    return float(np.sum(np.exp(-t * np.linalg.eigvalsh(L))))


def chi_graph(A):
    return len(A) - int(A.sum() // 2)


def cartesian(A, B):
    n1, n2 = len(A), len(B)
    C = np.zeros((n1 * n2, n1 * n2))
    for i1 in range(n1):
        for i2 in range(n2):
            u = i1 * n2 + i2
            for j2 in range(n2):
                if B[i2, j2]:
                    C[u, i1 * n2 + j2] = 1
            for j1 in range(n1):
                if A[i1, j1]:
                    C[u, j1 * n2 + i2] = 1
    return C


def supertrace(A, t):
    return tr_exp(lap(A), t) - tr_exp(edge_lap(A), t)


GRAPHS = {
    "K3": build(3, [(0, 1), (1, 2), (0, 2)]),
    "P2": build(2, [(0, 1)]),
    "P3": build(3, [(0, 1), (1, 2)]),
    "C4": build(4, [(0, 1), (1, 2), (2, 3), (3, 0)]),
    "K4": build(4, [(i, j) for i in range(4) for j in range(i + 1, 4)]),
    "C5": build(5, [(i, (i + 1) % 5) for i in range(5)]),
}


def main():
    pairs = list(itertools.combinations(GRAPHS, 2))
    out = {"tests": {}, "pairs": len(pairs)}

    # G10 / G11 / G12
    rows = []
    for t in (0.1, 1.0, 3.0):
        ok0 = ok1 = ok2 = 0
        for a, b in pairs:
            G, H = GRAPHS[a], GRAPHS[b]
            GH = cartesian(G, H)
            if abs(tr_exp(lap(GH), t) - tr_exp(lap(G), t) * tr_exp(lap(H), t)) < 1e-8:
                ok0 += 1
            if abs(tr_exp(edge_lap(GH), t) - tr_exp(edge_lap(G), t) * tr_exp(edge_lap(H), t)) < 1e-8:
                ok1 += 1
            if abs(supertrace(GH, t) - supertrace(G, t) * supertrace(H, t)) < 1e-8:
                ok2 += 1
        rows.append({"t": t, "G10_d0_trace_multiplicative": f"{ok0}/{len(pairs)}",
                     "G11_d1_trace_multiplicative": f"{ok1}/{len(pairs)}",
                     "G12_supertrace_multiplicative": f"{ok2}/{len(pairs)}"})
    out["tests"]["G10_G11_G12"] = rows

    # G13 + 2-cell deficit
    g13_ok = True
    deficit_ok = True
    detail = []
    for a, b in pairs:
        G, H = GRAPHS[a], GRAPHS[b]
        GH = cartesian(G, H)
        lhs = chi_graph(GH)
        rhs = chi_graph(G) * chi_graph(H) - int(G.sum() // 2) * int(H.sum() // 2)
        if lhs != rhs:
            g13_ok = False
        V = len(GH); E = int(GH.sum() // 2); F = int(G.sum() // 2) * int(H.sum() // 2)
        if V - E + F != chi_graph(G) * chi_graph(H):
            deficit_ok = False
        detail.append({"pair": f"{a}x{b}", "V": V, "E": E, "F_2cells": F,
                       "V-E+F": V - E + F, "chi_G_chi_H": chi_graph(G) * chi_graph(H),
                       "chi_1skeleton": lhs})
    out["tests"]["G13"] = {"holds": g13_ok,
                           "statement": "chi(G□H) = chi(G)chi(H) - |EG||EH|"}
    out["tests"]["2cell_deficit"] = {
        "holds": deficit_ok,
        "statement": "亏项 |EG||EH| = 产品复形的 2-胞腔数 F；V-E+F = chi(G)chi(H)",
        "detail": detail}

    # G14 spectral measure convolution
    g14_ok = True
    for a, b in pairs:
        G, H = GRAPHS[a], GRAPHS[b]
        GH = cartesian(G, H)
        s1 = np.linalg.eigvalsh(lap(G)); s2 = np.linalg.eigvalsh(lap(H))
        sums = np.sort(np.array([x + y for x in s1 for y in s2]))
        if not np.allclose(sums, np.sort(np.linalg.eigvalsh(lap(GH)))):
            g14_ok = False
    out["tests"]["G14"] = {"holds": g14_ok,
                           "statement": "spec Δ0(G□H) = {λ_i + μ_j} ⇒ μ_{G□H} = μ_G * μ_H"}

    out["diagnosis"] = {
        "type_matched_object": "谱测度 μ_G / 热核迹 Tr(e^{-tΔ0})（Kronecker 和 ⇒ 乘法性/卷积）",
        "not_multiplicative": "χ 在 1-骨架上：χ(G□H)=χ(G)χ(H)-|EG||EH|；亏项 = 产品复形的 2-胞腔数",
        "accurate_statement": ("所谓“加法 vs 乘法”的准确表述是维度问题：图是 1-维复形，"
                               "两个 1-复形之积是 2-维的，χ 只在完整产品复形上乘法；"
                               "EDS 定义在 1-骨架上，看不见 2-胞腔（同第 5 章“缺少粘合”）。"),
        "does_not_explain": ("这一分析不解释 1/3 缺口——后者是固定二维曲面上“密度归一化 vs "
                             "欧拉密度”的另一个轴。G10-G14 是标准事实，不是新定理。"),
    }

    os.makedirs(RES, exist_ok=True)
    with open(os.path.join(RES, "product_types.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print("=== 乘积行为核算（15 对图）===")
    for r in out["tests"]["G10_G11_G12"]:
        print(f"  t={r['t']}: G10 Δ0 乘法 {r['G10_d0_trace_multiplicative']}；"
              f"G11 Δ1 乘法 {r['G11_d1_trace_multiplicative']}；"
              f"G12 超迹乘法 {r['G12_supertrace_multiplicative']}")
    print(f"  G13 χ(G□H)=χ(G)χ(H)-|EG||EH|: {g13_ok}")
    print(f"  2-胞腔亏项 V-E+F=χ(G)χ(H): {deficit_ok}")
    print(f"  G14 谱测度卷积 μ_{{G□H}}=μ_G*μ_H: {g14_ok}")
    print("诊断：", out["diagnosis"]["accurate_statement"])
    print("       ", out["diagnosis"]["does_not_explain"])
    print("[done]", os.path.join(RES, "product_types.json"))


if __name__ == "__main__":
    main()
