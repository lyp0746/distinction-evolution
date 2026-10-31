# -*- coding: utf-8 -*-
"""生成重写版所需的 12 幅插图（SVG，确定性，无随机）。"""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyArrowPatch

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "svg")
plt.rcParams.update({"font.size": 9, "axes.grid": True, "grid.alpha": .3,
                     "figure.dpi": 120, "savefig.bbox": "tight",
                     "font.sans-serif": ["Microsoft YaHei", "SimHei", "DejaVu Sans"],
                     "axes.unicode_minus": False})
C = dict(blue="#2b6cb0", red="#b3261e", green="#2f855a", gray="#666", orange="#b7791f")

def lap(n, E):
    A = np.zeros((n, n))
    for u, v in E: A[u, v] = A[v, u] = 1
    return np.diag(A.sum(1)) - A

def grid_g(n):
    idx = lambda i, j: i * n + j
    E = [(idx(i, j), idx(i + 1, j)) for i in range(n - 1) for j in range(n)]
    E += [(idx(i, j), idx(i, j + 1)) for i in range(n) for j in range(n - 1)]
    return n * n, E

def torus_g(n):
    idx = lambda i, j: (i % n) * n + (j % n)
    E = [(idx(i, j), idx(i + 1, j)) for i in range(n) for j in range(n)]
    E += [(idx(i, j), idx(i, j + 1)) for i in range(n) for j in range(n)]
    return n * n, E

def spec(L):
    return np.sort(np.linalg.eigvalsh(L))

def save(fig, name):
    p = os.path.join(OUT, name)
    fig.savefig(p, format="svg")
    plt.close(fig)
    print("wrote", name)

# 1 R 的缩放（闭式，避免大矩阵对角化）
ns = [8, 10, 12, 16, 20, 25, 32, 40, 50, 64, 80]
grid_l2 = lambda n: 2 - 2 * np.cos(np.pi / n)
grid_ln = lambda n: 2 * (2 - 2 * np.cos(np.pi * (n - 1) / n))
torus_l2 = lambda n: 2 - 2 * np.cos(2 * np.pi / n)
Rg = [grid_ln(n) / grid_l2(n) for n in ns]
Rt = [8.0 / torus_l2(n) for n in ns]
fig, ax = plt.subplots(figsize=(5.6, 3.4))
ax.loglog(ns, Rg, "o-", color=C["blue"], label="网格 P_n□P_n（闭式）")
ax.loglog(ns, Rt, "s-", color=C["green"], label="环面 C_n□C_n（闭式）")
ax.loglog(ns, [8 / np.pi ** 2 * n * n for n in ns], "--", color=C["blue"], alpha=.6, label=r"$(8/\pi^2)n^2$")
ax.loglog(ns, [2 / np.pi ** 2 * n * n for n in ns], "--", color=C["green"], alpha=.6, label=r"$(2/\pi^2)n^2$")
ax.set_xlabel("n（每边结点数）"); ax.set_ylabel(r"$R=\lambda_n/\lambda_2$")
ax.legend(fontsize=7, loc="upper left"); ax.set_title("图 19.1　谱各向异性随分辨率二次增长")
save(fig, "fig-r-scaling.svg")

# 2 λ2/h² 收敛
ns2 = [10, 20, 40, 80, 160, 320]
vals = [grid_l2(n) * n * n for n in ns2]
fig, ax = plt.subplots(figsize=(5.2, 3.0))
ax.semilogx(ns2, vals, "o-", color=C["blue"])
ax.axhline(np.pi ** 2, ls="--", color=C["red"], label=r"$\pi^2=9.8696$")
ax.set_xlabel("n"); ax.set_ylabel(r"$\lambda_2/h^2$"); ax.legend(fontsize=8)
ax.set_title("图 19.2　缩放后的 λ₂ 收敛到 π²")
save(fig, "fig-lam2-convergence.svg")

# 3 四类图的谱线
fig, axes = plt.subplots(2, 2, figsize=(6.4, 4.2))
sets = [("完全图 K_12", lap(12, [(i, j) for i in range(12) for j in range(i + 1, 12)])),
        ("环 C_20", lap(20, [(i, (i + 1) % 20) for i in range(20)])),
        ("网格 10×10", lap(*grid_g(10))),
        ("Petersen", lap(10, [(i, (i + 1) % 5) for i in range(5)] +
                         [(5 + i, 5 + (i + 2) % 5) for i in range(5)] + [(i, 5 + i) for i in range(5)]))]
for ax, (t, L) in zip(axes.ravel(), sets):
    e = spec(L); ax.plot(e, np.arange(len(e)), "o", ms=3, color=C["blue"])
    ax.set_title(t, fontsize=8); ax.set_xlabel(r"$\lambda$")
fig.suptitle("图 18.1　四类图的拉普拉斯谱", fontsize=10)
fig.tight_layout()
save(fig, "fig-spectra-four.svg")

# 4 Weyl 计数
n = 40; L = lap(*grid_g(n)); e = spec(L); h = 1.0 / n
Lams = np.array([40, 60, 80, 120, 160, 240, 320, 480, 640, 960, 1280, 1920, 2560])
cnt = [int(np.sum(e <= h * h * x)) for x in Lams]
lat = [sum(1 for a in range(0, 60) for b in range(0, 60) if np.pi ** 2 * (a * a + b * b) <= x) for x in Lams]
fig, ax = plt.subplots(figsize=(5.6, 3.2))
ax.loglog(Lams, np.maximum(cnt, 1), "o-", color=C["blue"], label="网格计数（80×80）")
ax.loglog(Lams, np.maximum(lat, 1), "s--", color=C["green"], label="格点精确计数")
ax.loglog(Lams, Lams / 4.0, ":", color=C["red"], label=r"Weyl 主项 $\Lambda/4$")
ax.set_xlabel(r"$\Lambda$"); ax.set_ylabel(r"$N(\Lambda)$"); ax.legend(fontsize=7)
ax.set_title("图 20.1　解锁计数的三层对照")
save(fig, "fig-weyl-count.svg")

# 5 同谱反例
G1 = [(0, 2), (1, 2), (1, 3), (1, 4), (2, 5), (3, 5), (4, 5)]
G2 = [(0, 2), (0, 5), (1, 3), (1, 4), (2, 3), (3, 4), (3, 5)]
pos = {0: (0, 1), 1: (1, 0.2), 2: (1, 1.6), 3: (2, 0.4), 4: (2, 1.4), 5: (3, 1)}
fig, axes = plt.subplots(1, 2, figsize=(6.4, 2.6))
for ax, E, t in zip(axes, (G1, G2), ("G₁：度序列 3,3,3,2,2,1", "G₂：度序列 4,2,2,2,2,2")):
    for u, v in E: ax.plot([pos[u][0], pos[v][0]], [pos[u][1], pos[v][1]], "-", color=C["gray"], lw=1.4)
    for k, (x, y) in pos.items():
        ax.plot(x, y, "o", ms=12, color=C["blue"]); ax.text(x, y, str(k), color="white", ha="center", va="center", fontsize=7)
    ax.set_title(t, fontsize=8); ax.axis("off")
fig.suptitle("图 18.2　两个 6 顶点图，拉普拉斯谱相同", fontsize=10)
fig.tight_layout()
save(fig, "fig-cospectral-pair.svg")

# 6 两阶段相变示意
alpha = 1.0; l2, ln = 0.4, 5.0
beta = np.linspace(0, 3, 500)
unlocked = np.array([np.sum(beta_i * np.array([ln, 2.0, 1.0, l2]) > alpha) for beta_i in beta])
fig, ax = plt.subplots(figsize=(5.4, 3.0))
ax.step(beta, unlocked, where="post", color=C["blue"], lw=2)
ax.axvspan(alpha / ln, alpha / l2, color=C["orange"], alpha=.15, label="中间相")
ax.axvline(alpha / ln, color=C["green"], ls="--", label=r"$\beta_1=\alpha/\lambda_n$")
ax.axvline(alpha / l2, color=C["red"], ls="--", label=r"$\beta_2=\alpha/\lambda_2$")
ax.set_xlabel("耦合强度 β"); ax.set_ylabel("已解锁模式数"); ax.legend(fontsize=7)
ax.set_title("图 17.2　两阶段相变：中间相是阶跃之间的平台")
save(fig, "fig-two-stage-steps.svg")

# 7 中间相窗口
beta = np.linspace(0.2, 2.4, 300)
fig, ax = plt.subplots(figsize=(5.4, 3.0))
for lam, lab, col in ((5.0, r"$\lambda_n=5$（高频）", C["blue"]), (2.0, r"$\lambda=2$", C["green"]), (0.4, r"$\lambda_2=0.4$（低频）", C["red"])):
    ax.plot(beta, beta * lam - 1.0, label=lab, color=col)
ax.axhline(0, color=C["gray"], lw=.8)
ax.fill_between(beta, -1.2, 1.2, where=(beta > 1 / 5.0) & (beta < 1 / 0.4), color=C["orange"], alpha=.12)
ax.set_ylim(-1.2, 1.2); ax.set_xlabel(r"$\beta$"); ax.set_ylabel("增长率 μ=βλ−α"); ax.legend(fontsize=7)
ax.set_title("图 17.3　中间相里高频已增长、低频仍衰减")
save(fig, "fig-intermediate-window.svg")

# 8 Cheeger/AB 夹逼
d = np.arange(3, 61)
lo = 2 * d / (d - 2 * np.sqrt(d - 1))
fig, ax = plt.subplots(figsize=(5.4, 3.0))
ax.plot(d, lo, color=C["blue"], label=r"下界 $2d/(d-2\sqrt{d-1})$")
ax.plot(d, 2 * d / 0.1 * np.ones_like(d), color=C["green"], ls="--", lw=.8, label=r"上界 $2d/\gamma$（取 $\gamma=0.1$）")
ax.fill_between(d, lo, 2 * d / 0.1, color=C["blue"], alpha=.08)
ax.set_yscale("log"); ax.set_xlabel("度 d"); ax.set_ylabel("R")
ax.legend(fontsize=7); ax.set_title("图 18.3　正则族的 R 被两面夹住（下界趋于 2）")
save(fig, "fig-cheeger-band.svg")

# 9 热核
t = np.logspace(-2.5, 0, 200)
n = 40; L = lap(*grid_g(n)); e = spec(L) / (n * n)
Tr = np.array([np.sum(np.exp(-ti * e)) for ti in t])
fig, ax = plt.subplots(figsize=(5.4, 3.0))
ax.loglog(t, Tr, color=C["blue"], label=r"$\mathrm{Tr}\,e^{t\Delta}$（网格 40×40，按 $h^2$ 缩放）")
ax.loglog(t, 1 / (4 * np.pi * t), "--", color=C["red"], label=r"$(4\pi t)^{-1}\cdot$面积")
ax.set_xlabel("t"); ax.set_ylabel("热核迹"); ax.legend(fontsize=7)
ax.set_title("图 20.2　热核迹的短时渐近给出体积项")
save(fig, "fig-heat-kernel.svg")

# 10 自旋网络示意
fig, ax = plt.subplots(figsize=(5.0, 3.0))
pts = {0: (0, 0.5), 1: (0.9, 1.2), 2: (0.9, -0.2), 3: (1.8, 0.5)}
edges = [(0, 1, "1/2"), (0, 2, "1"), (1, 3, "1/2"), (2, 3, "3/2"), (1, 2, "1")]
for u, v, j in edges:
    ax.plot([pts[u][0], pts[v][0]], [pts[u][1], pts[v][1]], "-", color=C["gray"], lw=2)
    mx, my = (pts[u][0] + pts[v][0]) / 2, (pts[u][1] + pts[v][1]) / 2
    ax.text(mx, my + .08, "j=" + j, fontsize=8, color=C["blue"], ha="center")
for k, (x, y) in pts.items():
    ax.plot(x, y, "o", ms=10, color=C["blue"])
ax.fill([0.55, 0.55, 1.15, 1.15], [-0.5, 1.5, 1.5, -0.5], color=C["orange"], alpha=.12)
ax.text(0.58, 1.55, "面 S：只有被切开的边贡献面积", fontsize=7, color=C["orange"])
ax.set_xlim(-.3, 2.3); ax.set_ylim(-.7, 1.8); ax.axis("off")
ax.set_title("图 14.1　自旋网络：面积＝被区分出来的边")
save(fig, "fig-spin-network.svg")

# 11 失败矩阵
M = np.zeros((5, 6))
for i, j in [(0, 2), (1, 0), (1, 4), (1, 5), (2, 1), (2, 2), (2, 5), (3, 3), (3, 5),
             (4, 0), (4, 1), (4, 2), (4, 3), (4, 4), (4, 5)]:
    M[i, j] = 1
fig, ax = plt.subplots(figsize=(5.6, 2.8))
ax.imshow(M, cmap="Blues", vmin=0, vmax=1.4)
ax.set_xticks(range(6)); ax.set_xticklabels(["换词", "过度统一", "分级失效", "路径依赖", "不可通约", "空域"], fontsize=8)
ax.set_yticks(range(5)); ax.set_yticklabels(["一 纪律", "二 语言", "三 形式", "四 硬核", "五 覆盖"], fontsize=8)
for i in range(5):
    for j in range(6):
        if M[i, j]: ax.text(j, i, "●", ha="center", va="center", color="white", fontsize=9)
ax.set_title("图 23.1　六种失败与五个部分的高危矩阵"); ax.grid(False)
save(fig, "fig-failure-matrix.svg")

# 12 哈希链
fig, ax = plt.subplots(figsize=(5.8, 2.2))
labels = ["R1", "R2", "R3", "R4", "R5"]
for i, lab in enumerate(labels):
    ax.add_patch(Rectangle((i * 1.1, .3), .85, .5, facecolor="#e6effa", edgecolor=C["blue"]))
    ax.text(i * 1.1 + .42, .55, lab + "  h=" + "h" + str(i + 1), ha="center", va="center", fontsize=8)
    if i < len(labels) - 1:
        ax.add_patch(FancyArrowPatch((i * 1.1 + .86, .55), ((i + 1) * 1.1, .55),
                                     arrowstyle="->", color=C["gray"]))
ax.text(0, .1, "改任一条 → 其后所有哈希失效（append-only 可验证）", fontsize=8, color=C["red"])
ax.set_xlim(-.1, 5.7); ax.set_ylim(0, 1); ax.axis("off")
ax.set_title("图 24.1　登记簿的哈希链")
save(fig, "fig-hash-chain.svg")
print("done")
