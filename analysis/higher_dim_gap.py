# -*- coding: utf-8 -*-
"""
higher_dim_gap.py — 方向 B2：1/3 缺口在高维是否有一个良定义的一般化？

第 17 章猜测高维缺口因子为 f(n)=1/(2n+1)（开放问题 G4）。本脚本用**标准球面**
检验这个猜测，结果是一个**负面但精确**的结论：

在单位球面 S^{2n} 上：
    Vol(S^{2n}) = 2 π^{(2n+1)/2} / Γ((2n+1)/2)
    R = 2n(2n-1)                     （标量曲率）
    ∫ R/6 dV  (分离曲率积分，若取 κ=R/6)
    χ_naive := (1/(2π)) ∫ R/6 dV
    χ(S^{2n}) = 2
    ratio(n) := χ_naive / χ(S^{2n})

对 n=1（二维）：ratio = 1/3（与第 17 章一致）。
对 n≥2：ratio 依赖 n 且含 π，例如 n=2 为 2π/3，n=3 为 4π²/3。

结论：**用标量曲率定义的"分离曲率"在高维没有理由与欧拉示性数按一个普适常数
相关；f(n)=1/(2n+1) 不是一个良定义的猜想。** 正确的推广必须使用陈–高斯–博内
的欧拉形式（曲率张量的 Pfaffian），而不是标量曲率。

输出：analysis/results/higher_dim_gap.json
依赖：numpy（scipy 可选，用于 Γ；缺失时用 math.lgamma）。
"""
import json
import math
import os
import sys

import numpy as np

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(HERE, "analysis", "results")


def vol_sphere(d):
    """单位 S^d 的体积。"""
    return 2.0 * math.pi ** ((d + 1) / 2.0) / math.gamma((d + 1) / 2.0)


def scalar_curvature_round(d):
    """单位 S^d 的标量曲率。"""
    return d * (d - 1)


def analyse():
    rows = []
    for n in range(1, 7):
        d = 2 * n
        V = vol_sphere(d)
        R = scalar_curvature_round(d)
        int_kappa = R * V / 6.0                 # ∫ (R/6) dV
        chi_naive = int_kappa / (2 * math.pi)   # 若定义 χ(D) = ∫κ/(2π)
        chi = 2.0                               # χ(S^{2n}) = 2
        ratio = chi_naive / chi
        f_conjectured = 1.0 / (2 * n + 1)       # 第 17 章猜想
        rows.append({
            "n": n, "dim": d,
            "vol": V, "scalar_curvature": R,
            "int_kappa": int_kappa,
            "chi_naive": chi_naive,
            "chi": chi,
            "ratio": ratio,
            "conjectured_1_over_2n_plus_1": f_conjectured,
            "matches_conjecture": abs(ratio - f_conjectured) < 1e-9,
        })
    return rows


def main():
    rows = analyse()
    n_match = sum(1 for r in rows if r["matches_conjecture"])
    out = {
        "setup": "unit round sphere S^{2n}, kappa = R/6, chi_naive = int(kappa)/(2 pi)",
        "rows": rows,
        "summary": {
            "n_cases": len(rows),
            "n_matches_conjecture": n_match,
            "verdict": ("f(n)=1/(2n+1) 只在 n=1 成立；高维 ratio 含 π 且随 n 变化。"
                        "因此该猜想不是良定义的一般化；正确的推广须用欧拉形式而非标量曲率。"),
        },
    }
    os.makedirs(RES, exist_ok=True)
    with open(os.path.join(RES, "higher_dim_gap.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(f"{'n':>2} {'dim':>4} {'R':>6} {'Vol':>12} {'chi_naive':>12} {'ratio':>10} {'1/(2n+1)':>10} match")
    for r in rows:
        print(f"{r['n']:>2} {r['dim']:>4} {r['scalar_curvature']:>6} {r['vol']:>12.4f} "
              f"{r['chi_naive']:>12.4f} {r['ratio']:>10.4f} "
              f"{r['conjectured_1_over_2n_plus_1']:>10.4f} {'YES' if r['matches_conjecture'] else 'NO '}")
    print(f"\n{out['summary']['verdict']}")
    print("[done]", os.path.join(RES, "higher_dim_gap.json"))


if __name__ == "__main__":
    main()
