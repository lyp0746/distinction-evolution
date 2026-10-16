# -*- coding: utf-8 -*-
"""symplectic_probe.py — 第 14.6.1 节：辛推广（图上阻尼波动方程）的临界阻尼谱。

对每个图 G，拉普拉斯 L 的特征值 λ_k 决定阻尼波动方程
    q̈ + γ q̇ + L q = 0
中模式 k 的行为：γ < 2√λ_k 欠阻尼振荡，γ = 2√λ_k 临界阻尼，γ > 2√λ_k 过阻尼。
本脚本输出每个图的 γ_k = 2√λ_k（k 从低频到高频），并数值核验
伴随矩阵 [[0,1],[−λ,−γ]] 的特征值在 γ=2√λ 两侧由复变实。

协议 V1：确定性、仅用 numpy。
"""
import numpy as np

EDGES = {
    "P3":      [(0, 1), (1, 2)],
    "C4":      [(0, 1), (1, 2), (2, 3), (3, 0)],
    "C5":      [(0, 1), (1, 2), (2, 3), (3, 4), (4, 0)],
    "K4":      [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)],
    "Petersen": [(0, 1), (1, 2), (2, 3), (3, 4), (4, 0),
                 (5, 7), (7, 9), (9, 6), (6, 8), (8, 5),
                 (0, 5), (1, 6), (2, 7), (3, 8), (4, 9)],
    "Q3":      [(0, 1), (0, 2), (0, 4), (1, 3), (1, 5), (2, 3),
                (2, 6), (3, 7), (4, 5), (4, 6), (5, 7), (6, 7)],
}


def laplacian(n, edges):
    L = np.zeros((n, n))
    for u, v in edges:
        L[u, u] += 1
        L[v, v] += 1
        L[u, v] -= 1
        L[v, u] -= 1
    return L


def companion_eigs(lam, gamma):
    """阻尼振子 ẍ+γẋ+λx=0 的伴随矩阵 [[0,1],[−λ,−γ]] 的特征值。"""
    M = np.array([[0.0, 1.0], [-lam, -gamma]])
    return np.linalg.eigvals(M)


def check(lam, gamma):
    e = companion_eigs(lam, gamma)
    return float(np.max(np.abs(e.imag)))


def main():
    print("=== 辛推广：图上阻尼波动方程的临界阻尼谱（协议 V1）===")
    for name, edges in EDGES.items():
        n = max(max(e) for e in edges) + 1
        L = laplacian(n, edges)
        lam = np.sort(np.linalg.eigvalsh(L))
        lam = lam[lam > 1e-9]              # 去掉零模（整体平移）
        gammas = 2.0 * np.sqrt(lam)
        print(f"\n{name}: n={n}, λ={np.round(lam, 4)}")
        print(f"  临界阻尼 γ_k = 2√λ_k = {np.round(gammas, 4)}")
        # 数值核验：临界值下方仍振荡，上方已过阻尼
        ok = True
        for l, g in zip(lam, gammas):
            below = check(l, g * (1 - 1e-3))   # 略低于临界：有虚部（振荡）
            at = check(l, g)                    # 临界：虚部≈0
            above = check(l, g * (1 + 1e-3))   # 略高于临界：无虚部（过阻尼）
            if not (below > 1e-4 and at < 1e-4 and above < 1e-6):
                ok = False
        print(f"  γ<γ_k 振荡 / γ=γ_k 临界 / γ>γ_k 过阻尼：{'PASS' if ok else 'FAIL'}")
    print("\n结论：γ_k=2√λ_k，随 γ 增大模式由低频到高频依次过阻尼。"
          "这是可计算、可复现的结果（A／甲）；但它只是「换形式」，不是新理论。")


if __name__ == "__main__":
    main()
