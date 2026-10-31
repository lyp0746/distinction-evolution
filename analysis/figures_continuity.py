# -*- coding: utf-8 -*-
"""连续性模量与 Lyapunov 谱两幅图。"""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "svg")
plt.rcParams.update({"font.size": 9, "axes.grid": True, "grid.alpha": .3, "figure.dpi": 120,
                     "savefig.bbox": "tight",
                     "font.sans-serif": ["Microsoft YaHei", "SimHei", "DejaVu Sans"],
                     "axes.unicode_minus": False})
C = dict(blue="#2b6cb0", red="#b3261e", green="#2f855a", orange="#b7791f", gray="#666")

def save(fig, name):
    fig.savefig(os.path.join(OUT, name), format="svg"); plt.close(fig); print("wrote", name)

# 图 9.2 连续性模量阶梯
d = np.logspace(-3, 0, 300)
fig, ax = plt.subplots(figsize=(5.4, 3.0))
ax.loglog(d, d, color=C["blue"], label=r"Lipschitz：$\omega(\delta)=L\delta$")
ax.loglog(d, np.sqrt(d), color=C["green"], label=r"Hölder 1/2：$\omega=\sqrt{\delta}$")
ax.loglog(d, 1 / np.log(1 / d), color=C["orange"], lw=1.6, label=r"一致连续（不可加界）：$\omega=1/\ln(1/\delta)$")
ax.loglog(d, (d > 0.15) * 0.5 + (d <= 0.15) * 0.5 * (d / 0.15), color=C["red"], ls="--",
          label=r"仅连续：$\delta$ 依赖 $x$")
ax.set_xlabel(r"区分尺度 $\delta$"); ax.set_ylabel(r"响应模量 $\omega(\delta)$")
ax.legend(fontsize=7, loc="lower right"); ax.set_title("图 9.2　按“区分尺度”排序的连续性层级")
save(fig, "fig-modulus-hierarchy.svg")

# 图 16.2 Lyapunov 谱即模式增长率
alpha = 1.0; beta = 0.55
lam = np.sort(np.array([0.0, 0.4, 1.0, 2.0, 3.4, 5.0]))
fig, ax = plt.subplots(figsize=(5.4, 3.0))
mu = beta * lam - alpha
ax.bar(np.arange(len(lam)), mu, color=[C["green"] if m < 0 else C["red"] for m in mu], width=.6)
ax.axhline(0, color=C["gray"], lw=.8)
ax.set_xticks(np.arange(len(lam))); ax.set_xticklabels([r"$\lambda_{%d}$" % (i + 1) for i in range(len(lam))])
ax.set_ylabel(r"Lyapunov 指数 $\mu_k=\beta\lambda_k-\alpha$")
beta1, beta2 = alpha / lam[-1], alpha / lam[1]
ax.set_title(r"图 16.2　相变＝Lyapunov 谱符号改变（$\beta=0.55$，$\beta_1=%.2f,\beta_2=%.2f$）" % (beta1, beta2),
             fontsize=9)
save(fig, "fig-lyapunov-spectrum.svg")
print("done")
