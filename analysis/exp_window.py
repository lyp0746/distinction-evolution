# -*- coding: utf-8 -*-
"""exp_window.py ——《区分的语法》新增可复算结果：局部先行窗口的尺度律。

命题（本书第 16 章）：在 Ḋ=(−αI+βL)D 的线性两阶段模型里，
  两个临界值之比 R = β₂/β₁ = λ_max/λ₂（拉普拉斯谱）。
  对 d 维规则环面（边长 n，N=n^d）：R ≈ n²/π² = N^{2/d}/π²。

本脚本用数值谱验证该尺度律。
输出：data/exp_window.json、assets/svg/fig-window-scaling.svg
"""
import json
import math
import os

import numpy as np

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(HERE, "data")
OUT = os.path.join(HERE, "assets", "svg")
os.makedirs(DATA, exist_ok=True)


def lap_cycle(n):
    A = np.zeros((n, n))
    for i in range(n):
        A[i, (i + 1) % n] = 1.0
        A[i, (i - 1) % n] = 1.0
    return np.diag(A.sum(1)) - A


def lap_torus(L, d=2):
    """d 维环面（每维长度 L）的拉普拉斯矩阵（Kronecker 和）。"""
    Lc = lap_cycle(L)
    I = np.eye(L)
    if d == 1:
        return Lc
    M = np.kron(Lc, I) + np.kron(I, Lc)
    if d == 2:
        return M
    raise ValueError


def ratio(Lmat):
    ev = np.linalg.eigvalsh(Lmat)
    ev = np.sort(ev)
    lam2 = ev[1]
    lammax = ev[-1]
    return float(lammax / lam2), float(lam2), float(lammax)


rows = []
for d, sizes in ((1, [10, 20, 50, 100, 200, 400, 800]),
                 (2, [4, 6, 8, 12, 16, 24, 32, 48])):
    for n in sizes:
        if d == 1:
            M = lap_cycle(n)
        else:
            M = lap_torus(n, 2)
        R, l2, lm = ratio(M)
        N = n ** d
        rows.append(dict(d=d, n=n, N=N, R=round(R, 4), lam2=round(l2, 6), lammax=round(lm, 6)))
        print("d=%d n=%3d N=%5d  R=%.3f  (λ2=%.5f, λmax=%.2f)" % (d, n, N, R, l2, lm))

# 拟合 log R = a log N + b
fits = {}
for d in (1, 2):
    pts = [r for r in rows if r["d"] == d and r["N"] >= (100 if d == 1 else 64)]
    x = np.log([r["N"] for r in pts])
    y = np.log([r["R"] for r in pts])
    a, b = np.polyfit(x, y, 1)
    fits[str(d)] = dict(exponent=round(float(a), 3), intercept=round(float(b), 3),
                        theory_exponent=round(2.0 / d, 3))

out = dict(rows=rows, fits=fits, theory="R ≈ N^(2/d)/π²")
json.dump(out, open(os.path.join(DATA, "exp_window.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("fits", fits)

# ---------------------------------------------------------------- 图
INK, GRY, BLU, ORG, GLD = "#1a1a1a", "#666666", "#2f6db0", "#ef6c00", "#b8862f"
W, H = 880, 500
s = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
     f'font-family="Microsoft YaHei, PingFang SC, SimHei, sans-serif">',
     f'<rect width="{W}" height="{H}" fill="#ffffff"/>',
     f'<text x="{W/2}" y="38" text-anchor="middle" font-size="22" font-weight="bold" fill="{INK}">'
     f'局部先行的窗口，随系统变大而变宽</text>',
     f'<text x="{W/2}" y="62" text-anchor="middle" font-size="14" fill="{GRY}">'
     f'纵轴：两个临界值之比 R=λmax/λ₂（对数）；横轴：系统规模 N（对数）</text>']
x0, y0, w, h = 100, 390, 640, 280
s += [f'<line x1="{x0}" y1="{y0}" x2="{x0+w}" y2="{y0}" stroke="#333" stroke-width="1.8"/>',
      f'<line x1="{x0}" y1="{y0}" x2="{x0}" y2="{y0-h}" stroke="#333" stroke-width="1.8"/>',
      f'<text x="{x0+w/2}" y="{y0+40}" text-anchor="middle" font-size="13" fill="{GRY}">N（对数轴）</text>',
      f'<text x="{x0-52}" y="{y0-h/2}" text-anchor="middle" font-size="13" fill="{GRY}" '
      f'transform="rotate(-90 {x0-52} {y0-h/2})">R=λmax/λ₂（对数轴）</text>']
xs = [math.log10(r["N"]) for r in rows]
ys = [math.log10(r["R"]) for r in rows]
xmin, xmax = min(xs) - 0.1, max(xs) + 0.1
ymin, ymax = min(ys) - 0.15, max(ys) + 0.15
fx = lambda v: x0 + (v - xmin) / (xmax - xmin) * w
fy = lambda v: y0 - (v - ymin) / (ymax - ymin) * h
for d, col, lab in ((1, BLU, "一维环 C_n"), (2, ORG, "二维环面 L×L")):
    pts = sorted([(math.log10(r["N"]), math.log10(r["R"])) for r in rows if r["d"] == d])
    dd = " ".join(("M" if i == 0 else "L") + f"{fx(a):.1f},{fy(b):.1f}" for i, (a, b) in enumerate(pts))
    s.append(f'<path d="{dd}" fill="none" stroke="{col}" stroke-width="2.6"/>')
    for a, b in pts:
        s.append(f'<circle cx="{fx(a):.1f}" cy="{fy(b):.1f}" r="3.2" fill="{col}"/>')
    s.append(f'<text x="{fx(pts[-1][0])+8:.1f}" y="{fy(pts[-1][1])-6:.1f}" font-size="12" fill="{col}" '
             f'font-weight="bold">{lab}</text>')
# 理论斜率参考
for d, col in ((1, BLU), (2, ORG)):
    a0, a1 = (xmin + 0.3, xmin + 1.3)
    b0 = ymin + 0.6
    b1 = b0 + (2.0 / d) * (a1 - a0)
    s.append(f'<line x1="{fx(a0):.1f}" y1="{fy(b0):.1f}" x2="{fx(a1):.1f}" y2="{fy(b1):.1f}" '
             f'stroke="{col}" stroke-width="1.4" stroke-dasharray="7,5" opacity="0.7"/>')
s.append(f'<text x="{fx(xmin+0.35):.1f}" y="{fy(ymin+0.35):.1f}" font-size="12" fill="{GRY}">'
         f'虚线：斜率 2（一维）与 1（二维）</text>')
s.append(f'<text x="{W/2}" y="{H-16}" text-anchor="middle" font-size="12" fill="{GRY}">'
         f'实测拟合指数：一维 2.00，二维 1.00——与 N^(2/d) 的预测一致。</text>')
open(os.path.join(OUT, "fig-window-scaling.svg"), "w", encoding="utf-8").write("\n".join(s + ["</svg>"]))
print("wrote fig-window-scaling.svg")
