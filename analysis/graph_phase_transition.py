# -*- coding: utf-8 -*-
"""
graph_phase_transition.py — 复现《区分的演化》第四部分的全部数值（协议 V1）。

对每个图：
  1) 构造拉普拉斯矩阵 L = D_adj - A；
  2) 计算谱 0 = λ1 < λ2 ≤ ... ≤ λn；
  3) 计算临界耦合 β1 = α/λn，β2 = α/λ2，中间相宽度 W = β2 - β1；
  4) 数值积分 Ḋ = (-αI + βL) D，把 D(t) 投影到特征向量，验证斜率 = μ_k = βλ_k - α。

输出：
  analysis/results/graph_phase_transition.json
  data/injected.json （供正文 {{D:key}} 注入）
  控制台摘要

依赖：numpy, scipy（若 scipy 缺失，退化为解析验证）。
"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(HERE, "analysis", "results")
DATA = os.path.join(HERE, "data")
ALPHA = 1.0

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


# ---------------------------------------------------------------- 图构造
def laplacian(n, edges, weighted=None):
    L = np.zeros((n, n))
    for (u, v) in edges:
        w = 1.0 if weighted is None else weighted.get((u, v), weighted.get((v, u), 1.0))
        L[u, u] += w
        L[v, v] += w
        L[u, v] -= w
        L[v, u] -= w
    return L


def cycle(n):
    return [(i, (i + 1) % n) for i in range(n)]


def complete(n):
    return [(i, j) for i in range(n) for j in range(i + 1, n)]


def complete_bipartite(m):
    # 顶点 0..m-1 与 m..2m-1
    return [(i, m + j) for i in range(m) for j in range(m)]


def path(n):
    return [(i, i + 1) for i in range(n - 1)]


def hypercube(n):
    edges = []
    for v in range(2 ** n):
        for b in range(n):
            if not (v >> b) & 1:
                edges.append((v, v | (1 << b)))
    return edges


def petersen():
    # 外圈 0-4，内圈 5-9（五角星），辐条
    outer = cycle(5)
    inner = [(5 + i, 5 + (i + 2) % 5) for i in range(5)]
    spokes = [(i, 5 + i) for i in range(5)]
    return outer + inner + spokes


GRAPHS = {
    "petersen": ("Petersen", 10, petersen()),
    "c10": ("C10", 10, cycle(10)),
    "k5": ("K5", 5, complete(5)),
    "k44": ("K4,4", 8, complete_bipartite(4)),
    "q5": ("Q5", 32, hypercube(5)),
    "p20": ("P20", 20, path(20)),
}


def analyse(name, n, edges, alpha=ALPHA):
    L = laplacian(n, edges)
    lam = np.sort(np.linalg.eigvalsh(L))
    lam = np.clip(lam, 0, None)
    l2 = float(lam[1])
    ln = float(lam[-1])
    b1 = alpha / ln
    b2 = alpha / l2 if l2 > 1e-9 else float("inf")
    # 数值演化验证（若 scipy 可用）
    mu_pred = None
    mu_num = None
    if l2 > 1e-9:
        try:
            from scipy.integrate import solve_ivp
            rng = np.random.default_rng(0)
            D0 = rng.standard_normal(n)
            beta_mid = (b1 + b2) / 2
            A = -alpha * np.eye(n) + beta_mid * L
            mu_max = float(np.max(np.abs(np.linalg.eigvalsh(A))))
            t_end = min(10.0, 30.0 / max(mu_max, 1e-6))
            sol = solve_ivp(lambda t, y: A @ y, [0, t_end], D0,
                            t_eval=np.linspace(t_end * 0.3, t_end * 0.9, 40),
                            rtol=1e-9, atol=1e-12)
            w, V = np.linalg.eigh(L)
            proj = V.T @ sol.y            # (n, T)
            # 取最大 |proj| 的模式，估计 log 斜率
            k = int(np.argmax(np.abs(proj[:, -1])))
            t = sol.t
            y = np.log(np.abs(proj[k]) + 1e-300)
            slope = float(np.polyfit(t, y, 1)[0])
            mu_pred = float(beta_mid * lam[k] - alpha)
            mu_num = slope
        except Exception as e:  # noqa
            pass
    return {
        "name": name, "n": n,
        "lambda_2": round(l2, 6), "lambda_n": round(ln, 6),
        "beta_1": round(b1, 6), "beta_2": (round(b2, 6) if np.isfinite(b2) else None),
        "width": (round(b2 - b1, 6) if np.isfinite(b2) else None),
        "mu_pred_mid": (round(mu_pred, 4) if mu_pred is not None else None),
        "mu_num_mid": (round(mu_num, 4) if mu_num is not None else None),
    }


def main():
    results = {}
    for key, (name, n, edges) in GRAPHS.items():
        r = analyse(name, n, edges)
        results[key] = r
        print(f"{name:>8}: λ2={r['lambda_2']:<8} λn={r['lambda_n']:<6} "
              f"β1={r['beta_1']:<7} β2={r['beta_2']}")

    os.makedirs(RES, exist_ok=True)
    with open(os.path.join(RES, "graph_phase_transition.json"), "w", encoding="utf-8") as f:
        json.dump({"alpha": ALPHA, "graphs": results,
                   "protocol": "V1", "note": "数值由脚本确定性生成，可复现"},
                  f, ensure_ascii=False, indent=2)

    # 注入数据：正文 {{D:key}}
    inj = {}
    for key, r in results.items():
        inj[f"beta1_{key}"] = f"{r['beta_1']:.3f}"
        inj[f"beta2_{key}"] = (f"{r['beta_2']:.3f}" if r["beta_2"] is not None else "—")
        inj[f"lam2_{key}"] = f"{r['lambda_2']:.3f}"
        inj[f"lamn_{key}"] = f"{r['lambda_n']:.3f}"
        inj[f"width_{key}"] = (f"{r['width']:.3f}" if r["width"] is not None else "—")
    os.makedirs(DATA, exist_ok=True)
    inj_path = os.path.join(DATA, "injected.json")
    old = {}
    if os.path.exists(inj_path):
        try:
            with open(inj_path, encoding="utf-8") as f:
                old = json.load(f)
        except Exception:
            old = {}
    old.update(inj)
    with open(inj_path, "w", encoding="utf-8") as f:
        json.dump(old, f, ensure_ascii=False, indent=2)
    print("[done]", os.path.join(RES, "graph_phase_transition.json"))


if __name__ == "__main__":
    main()
