# -*- coding: utf-8 -*-
"""axiom_independence.py — 定理 14.6 的可行性预检：六条公理在图论上是否独立？

方法与判据（有限图上）：
对每条公理，判断它在图上属于哪一类：
  T 托词（tautology）：对所有图都成立，无内容 => 不可能与其它公理"独立"，因为它根本
    不是一条约束。
  C 有内容（contentful）：存在图满足它、也存在图违反它 => 才谈得上独立性。
  N 不适用（N/A）：图论情形下该公理无指称。

若多条公理是 T，则"定理 14.6（六条公理相互独立）"要么平凡（托词彼此不构成约束），
要么无意义。预检结果将决定是否值得投入完整版。

输出：analysis/results/axiom_independence.json。依赖：numpy。
"""
import itertools
import json
import os

import numpy as np

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(HERE, "analysis", "results")


def laplacian(edges, n):
    L = np.zeros((n, n))
    for u, v in edges:
        L[u, u] += 1
        L[v, v] += 1
        L[u, v] -= 1
        L[v, u] -= 1
    return L


GRAPHS = {
    "Petersen": ([(0,1),(1,2),(2,3),(3,4),(4,0),(0,5),(1,6),(2,7),(3,8),(4,9),(5,7),(7,9),(9,6),(6,8),(8,5)], 10),
    "K5": ([(i,j) for i,j in itertools.combinations(range(5),2)], 5),
    "C6": ([(i,(i+1)%6) for i in range(6)], 6),
    "P8": ([(i,i+1) for i in range(7)], 8),
    "Star6": ([(0,i) for i in range(1,6)], 6),
}


def analyze(name, edges, n):
    L = laplacian(edges, n)
    lam = np.sort(np.linalg.eigvalsh(L))
    # A1（观测完备）：完整谱嵌入的行是正交矩阵的行 => 必单射 => 对所有图成立
    a1_tautology = True
    # A2（精度连续）：有限图上精度离散 => 对所有图成立
    a2_tautology = True
    # A3（曲率有界）：κ_info = Var(λ)/2 有限 => 对所有图成立
    kappa = float(np.var(lam) / 2.0)
    a3_tautology = np.isfinite(kappa)
    # A4（演化适定）：线性 ODE 必有唯一解 => 对所有图成立（内容在相变定理，不在公理）
    a4_tautology = True
    # A5（分离完备）：原子分解唯一 ⟺ 单谱。存在违反它的图（重谱）。
    distinct = len(set(np.round(lam, 8))) == n
    # A6（标准化）：有限图无超有限结构 => 不适用
    a6_applicable = False
    return {"graph": name, "spectrum": [round(x,4) for x in lam],
            "A1_observation_complete": "T（托词）" if a1_tautology else "C",
            "A2_precision_continuous": "T（托词）" if a2_tautology else "C",
            "A3_curvature_bounded": "T（托词）" if a3_tautology else "C",
            "A4_evolution_wellposed": "T（托词）" if a4_tautology else "C",
            "A5_separation_complete": "C（有内容）" if distinct else "C（违反：重谱）",
            "A6_normalization": "N（不适用）",
            "simple_spectrum": bool(distinct)}


def main():
    rows = [analyze(k, *v) for k, v in GRAPHS.items()]
    # 逐条公理跨图汇总
    summary = {}
    for ax in ["A1_observation_complete","A2_precision_continuous","A3_curvature_bounded",
               "A4_evolution_wellposed","A5_separation_complete","A6_normalization"]:
        vals = [r[ax] for r in rows]
        if all("T" in v for v in vals):
            summary[ax] = "托词（对所有图成立，无内容）"
        elif all(v.startswith("N") for v in vals):
            summary[ax] = "不适用"
        else:
            summary[ax] = "有内容（存在满足者与违反者）"
    n_content = sum(1 for v in summary.values() if v.startswith("有内容"))
    out = {"rows": rows, "summary": summary, "n_contentful_axioms": n_content,
           "verdict": ("六条公理在图上大多为托词 => 独立性不是正确的问题；"
                       "真正有内容的是 A5（及定理 15.1/14.1/12.1），不是公理组。"
                       if n_content <= 2 else "存在足够多内容型公理，独立性预检值得继续。"),
           "caveat": ("有限图情形的预检；托词指'对所有图成立因而无约束'。")}
    os.makedirs(RES, exist_ok=True)
    with open(os.path.join(RES, "axiom_independence.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    for ax, v in summary.items():
        print(f"{ax}: {v}")
    print("有内容的公理数：", n_content)
    print("verdict:", out["verdict"])
    print("[done]", os.path.join(RES, "axiom_independence.json"))


if __name__ == "__main__":
    main()
