# -*- coding: utf-8 -*-
"""make_cover.py — 生成《区分的语法》满版封面 SVG（A4 比例 1000×1414）。

输出：assets/svg/cover.svg
封面须满版：配合 assets/css/book.css 中 .cover-page 的 210mm×297mm 与
@page :first { margin: 0 }，让底色铺满整页。
"""
import os

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(HERE, "assets", "svg", "cover.svg")


def build():
    W, H = 1000, 1414
    ink = "#e8e6df"
    dim = "#9aa0a6"
    layers = []
    # 区分动作 → 分离曲率：一族从中心发散/汇聚的曲线
    cx, cy = 500, 560
    for i in range(9):
        r = 90 + i * 42
        op = 0.30 - i * 0.028
        col = ["#3a6ea5", "#b8862f", "#009E73"][i % 3]
        layers.append(f'<ellipse cx="{cx}" cy="{cy}" rx="{r}" ry="{r*0.34:.0f}" '
                      f'fill="none" stroke="{col}" stroke-width="1.4" opacity="{max(op,0.05):.3f}"/>')
    # 两条临界线（β₁ / β₂）
    for i, (yy, col) in enumerate([(980, "#009E73"), (1060, "#c94f4f")]):
        layers.append(f'<line x1="80" y1="{yy}" x2="920" y2="{yy}" stroke="{col}" '
                      f'stroke-width="1.6" opacity="0.55" stroke-dasharray="8,6"/>')
    # 相变阶梯
    for i in range(7):
        y = 1120 + i * 26
        w = 700 - i * 90
        layers.append(f'<line x1="{500-w/2:.0f}" y1="{y}" x2="{500+w/2:.0f}" y2="{y}" '
                      f'stroke="{dim}" stroke-width="1" opacity="{0.42-0.05*i:.2f}"/>')

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">
<defs>
<linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">
<stop offset="0" stop-color="#0e1117"/><stop offset="0.55" stop-color="#151a23"/>
<stop offset="1" stop-color="#0b0e14"/>
</linearGradient>
</defs>
<rect x="0" y="0" width="{W}" height="{H}" fill="url(#bg)"/>
<rect x="0" y="0" width="{W}" height="8" fill="#b8862f" opacity="0.85"/>
{chr(10).join(layers)}
<style>
text{{font-family:'Microsoft YaHei','SimHei',Arial,sans-serif;}}
.ttl{{font-size:108px;font-weight:700;letter-spacing:12px;fill:{ink};}}
.sub{{font-size:29px;fill:{dim};letter-spacing:2px;}}
.eng{{font-size:21px;fill:{dim};letter-spacing:1px;}}
.au{{font-size:30px;fill:{ink};letter-spacing:2px;}}
.rule{{stroke:{dim};stroke-width:1;opacity:0.6;}}
</style>
<text x="80" y="176" class="eng">THE GRAMMAR OF DISTINCTION</text>
<text x="80" y="300" class="ttl">区分的语法</text>
<line x1="84" y1="344" x2="660" y2="344" class="rule"/>
<text x="84" y="396" class="sub">五个领域</text>
<text x="84" y="440" class="sub">同一个二次型</text>
<text x="80" y="1180" class="au">李毅芃　著</text>
<text x="80" y="1232" class="eng">Five Domains, One Quadratic Form</text>
<text x="80" y="1274" class="eng">语言规范 · 2026</text>
</svg>
'''
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(svg)
    print("wrote", OUT)


if __name__ == "__main__":
    build()
