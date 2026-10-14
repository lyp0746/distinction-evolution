# -*- coding: utf-8 -*-
"""
dirac_mckean_singer.py — 第 20.2.3 节：图上的 de Rham/Dirac 算子与 McKean–Singer。

主张（对话中提出）：用狄拉克算子 D=[[0,B^T],[B,0]] 取代拉普拉斯算子，
超迹 Tr_s(e^{-tD^2}) 的短时展开给出欧拉类而非 R/6，于是 1/3 缺口消失。

本脚本核实其**第一步**（也是它最脆弱的一步）：

  D^2 = diag(B^T B, B B^T) = diag(Δ0, Δ1)
  X(t) := Tr(e^{-tΔ0}) - Tr(e^{-tΔ1})

而 B^T B 与 B B^T 只在核上不同（非零谱完全一致）。因此由 McKean–Singer：

  X(t) = dim ker Δ0 - dim ker Δ1 = b0 - b1 = χ(G)

**对一切 t 精确成立**——超迹没有发散、没有短时渐近、更没有 1/3。
所以"改用狄拉克算子使 1/3 消失"是同义反复：超迹里本来就没有 1/3。
1/3 出现在**标量**拉普拉斯（非超迹）的热核常数项 a1=R/6 中。

附注：图上给出 χ 的是 de Rham 算子（B 的度数 ±1 部分），不是旋量 Dirac 算子；
后者的指标是 Â-亏格，是另一个不变量。

运行：python analysis/dirac_mckean_singer.py
输出：analysis/results/dirac_mckean_singer.json
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


def build(n, edges):
    A = np.zeros((n, n))
    for u, v in edges:
        A[u, v] = A[v, u] = 1
    return A


def incidence(A):
    n = len(A)
    E = [(i, j) for i in range(n) for j in range(i + 1, n) if A[i, j]]
    B = np.zeros((len(E), n))
    for k, (i, j) in enumerate(E):
        B[k, i] = 1
        B[k, j] = -1
    return B


def tr_exp(M, t):
    return float(np.sum(np.exp(-t * np.linalg.eigvalsh(M))))


GRAPHS = {
    "K3": build(3, [(0, 1), (1, 2), (0, 2)]),
    "C4": build(4, [(0, 1), (1, 2), (2, 3), (3, 0)]),
    "K4": build(4, [(i, j) for i in range(4) for j in range(i + 1, 4)]),
    "P3": build(3, [(0, 1), (1, 2)]),
    "C5": build(5, [(i, (i + 1) % 5) for i in range(5)]),
    "Petersen": build(10, [(i, (i + 1) % 5) for i in range(5)]
                      + [(5 + i, 5 + (i + 2) % 5) for i in range(5)]
                      + [(i, 5 + i) for i in range(5)]),
}


def main():
    ts = [0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0, 20.0, 100.0]
    rows = []
    mckean_singer_ok = True
    isospectral_ok = True
    scalar_varies_ok = True
    for name, A in GRAPHS.items():
        B = incidence(A)
        L0 = B.T @ B           # Δ0 = B^T B
        L1 = B @ B.T           # Δ1 = B B^T
        e0 = np.linalg.eigvalsh(L0)
        e1 = np.linalg.eigvalsh(L1)
        nz0 = np.sort(e0[e0 > 1e-9])
        nz1 = np.sort(e1[e1 > 1e-9])
        iso = bool(nz0.size == nz1.size and (nz0.size == 0 or np.allclose(nz0, nz1)))
        chi = len(A) - int(A.sum() // 2)
        X = [tr_exp(L0, t) - tr_exp(L1, t) for t in ts]
        scalar = [tr_exp(L0, t) for t in ts]
        const = all(abs(x - chi) < 1e-8 for x in X)
        varies = (max(scalar) - min(scalar)) > 1e-3
        isospectral_ok &= iso
        mckean_singer_ok &= const
        scalar_varies_ok &= varies
        rows.append({
            "graph": name, "chi": chi,
            "isospectral_off_kernel": iso,
            "X_t_const_equal_chi": const,
            "X_t_values": [round(x, 8) for x in X],
            "scalar_trace_varies": varies,
            "t_grid": ts,
        })

    out = {
        "statement": ("X(t)=Tr(e^{-tΔ0})-Tr(e^{-tΔ1}) 恒等于 χ(G)（McKean–Singer），"
                      "对一切 t 精确成立；无短时发散，无 1/3。"),
        "checks": {
            "isospectral_off_kernel": isospectral_ok,
            "X_t_const_equal_chi": mckean_singer_ok,
            "scalar_trace_varies": scalar_varies_ok,
        },
        "verdict": ("'改用 Dirac 算子使 1/3 消失' 属同义反复——超迹中本无 1/3。"
                    "1/3 在标量拉普拉斯热核常数项 a1=R/6 中，与超迹是不同对象。"
                    "图上的算子是 de Rham 算子（给出 χ），不是旋量 Dirac 算子（给出 Â-亏格）。"),
        "rows": rows,
    }
    os.makedirs(RES, exist_ok=True)
    with open(os.path.join(RES, "dirac_mckean_singer.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print("=== McKean–Singer：超迹恒等于 χ ===")
    for r in rows:
        print(f"  {r['graph']:8s} χ={r['chi']:3d}  非零谱一致={r['isospectral_off_kernel']}  "
              f"X(t)≡χ={r['X_t_const_equal_chi']}  X(t)={r['X_t_values'][:4]}...")
    print("三项检查：", out["checks"])
    print("结论：", out["verdict"])
    print("[done]", os.path.join(RES, "dirac_mckean_singer.json"))


if __name__ == "__main__":
    main()
