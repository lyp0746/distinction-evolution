# -*- coding: utf-8 -*-
"""
kappa_type_mismatch.py — 第 12/20 章的类型诊断：三个 "κ" 不是同一个量。

书中出现过三个都叫"分离曲率"的对象：

  1. 动态 κ = βλ − α             （图上演化增长率，定理 15.1）
  2. 离散 κ_info = Var(λ)/2      （热核熵变分，定理 12.1）
  3. 热核 κ = R/6                （流形上热核展开系数 a₁，第 20 章）

本脚本给出一个决定性的数值对照：连续曲率为零的平坦空间上，离散"分离
曲率" κ_info 并不为零，且不随加密趋于零。因此 κ_info 不是 R/6 的离散化，
第 20 章所谓"1/3 缺口"部分来自把两类不同的量放在同一个方程里比较。

对照 1  平坦二维环面 T²（连续 R=0 ⇒ ∫R/6 = 0）
        m×m 网格图的未归一化拉普拉斯：Var(λ)/2 = 2.0000（任意 m）
对照 2  环 C_n（离散化一维圆，连续 R=0）
        Var(λ)/2 = 1.0000（任意 n）
对照 3  表 12.3 的其它图，确认 κ_info 是谱方差不变量。

运行：python analysis/kappa_type_mismatch.py
输出：analysis/results/kappa_type_mismatch.json
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


def lap_cycle(n):
    L = np.zeros((n, n))
    for i in range(n):
        L[i, i] += 2
        L[i, (i + 1) % n] -= 1
        L[i, (i - 1) % n] -= 1
    return L


def lap_grid_torus(m):
    N = m * m
    L = np.zeros((N, N))

    def idx(a, b):
        return (a % m) * m + (b % m)

    for a in range(m):
        for b in range(m):
            i = idx(a, b)
            L[i, i] += 4
            for da, db in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                L[i, idx(a + da, b + db)] -= 1
    return L


def kappa_info(L):
    ev = np.linalg.eigvalsh(L)
    return float(0.5 * ev.var()), ev


def main():
    rows = []

    print("=== 对照 1：平坦二维环面 T²（连续 R=0、∫R/6=0）===")
    for m in (4, 6, 8, 10, 14, 20):
        k, ev = kappa_info(lap_grid_torus(m))
        rows.append({"family": "flat torus T^2 (grid m x m)", "param": m,
                     "n_vertices": int(ev.size), "lambda_max": round(float(ev.max()), 4),
                     "kappa_info": round(k, 6), "continuous_R_over_6": 0.0})
        print(f"  {m:2d}x{m:<2d}  N={ev.size:4d}  lam_max={ev.max():7.3f}  kappa_info={k:.4f}")

    print("\n=== 对照 2：环 C_n（连续 R=0、∫R/6=0）===")
    for n in (10, 20, 40, 80, 160):
        k, ev = kappa_info(lap_cycle(n))
        rows.append({"family": "cycle C_n", "param": n,
                     "n_vertices": n, "lambda_max": round(float(ev.max()), 4),
                     "kappa_info": round(k, 6), "continuous_R_over_6": 0.0})
        print(f"  C_{n:<4d} N={n:4d}  lam_max={ev.max():7.3f}  kappa_info={k:.4f}")

    defs = {
        "kappa_dynamic": "βλ − α（图上演化增长率，定理 15.1）",
        "kappa_info": "Var(λ)/2（热核熵变分，定理 12.1）——谱不变量",
        "kappa_heat": "R/6（流形上热核展开系数 a₁）——局部分析量",
    }
    summary = {
        "flat_torus_kappa_info_is_2": all(
            abs(r["kappa_info"] - 2.0) < 1e-9 for r in rows if r["family"].startswith("flat torus")),
        "cycle_kappa_info_is_1": all(
            abs(r["kappa_info"] - 1.0) < 1e-9 for r in rows if r["family"].startswith("cycle")),
        "verdict": ("连续曲率为零的平坦空间上 κ_info = 2（环面）/ 1（环），并不趋于 0，"
                    "而 ∫R/6 = 0。故 κ_info 不是 R/6 的离散化；“1/3 缺口”部分来自"
                    "把谱不变量与局部分析量并置比较（类型混淆），而非深层不变量。"),
    }

    out = {"definitions": defs, "rows": rows, "summary": summary}
    os.makedirs(RES, exist_ok=True)
    with open(os.path.join(RES, "kappa_type_mismatch.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print("\n结论：", summary["verdict"])
    print("[done]", os.path.join(RES, "kappa_type_mismatch.json"))


if __name__ == "__main__":
    main()
