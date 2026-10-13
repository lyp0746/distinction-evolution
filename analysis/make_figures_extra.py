# -*- coding: utf-8 -*-
"""补充插图：候选核心图、分层可信度图、阅读合约图。

风格沿用 make_figures.py 的 house palette，输出到 assets/svg/。
"""
import os

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(HERE, "assets", "svg")

BLUE, RED, GOLD, GREEN, GREY = "#3a6ea5", "#c94f4f", "#b8862f", "#009E73", "#666"
INK = "#1a1a1a"
FONT = "'Microsoft YaHei','SimHei',Arial,sans-serif"
SERIF = "'Times New Roman',Georgia,serif"


def wrap(w, h, body, bg="#ffffff"):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}">'
            f'<rect width="{w}" height="{h}" fill="{bg}"/>'
            f'<style>text{{font-family:{FONT};fill:{INK};}}'
            f'.s{{font-family:{SERIF};}}</style>'
            f'{body}</svg>')


def box(x, y, w, h, label, sub="", color=BLUE, fc="#ffffff"):
    body = (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" '
            f'fill="{fc}" stroke="{color}" stroke-width="2"/>'
            f'<text x="{x + w/2}" y="{y + h/2 - (6 if sub else -6)}" text-anchor="middle" '
            f'font-size="22" font-weight="600" fill="{color}">{label}</text>')
    if sub:
        body += (f'<text x="{x + w/2}" y="{y + h/2 + 22}" text-anchor="middle" '
                 f'font-size="15" fill="{GREY}">{sub}</text>')
    return body


def fig_candidate_core():
    W, H = 1000, 560
    b = []
    b.append(f'<text x="40" y="46" font-size="24" font-weight="700">区分演化候选：四个要素与一个硬核</text>')
    cx, cy = 500, 250
    b.append(f'<circle cx="{cx}" cy="{cy}" r="78" fill="#eef3f8" stroke="{BLUE}" stroke-width="2.5"/>')
    b.append(f'<text x="{cx}" y="{cy-4}" text-anchor="middle" font-size="20" font-weight="700" fill="{BLUE}">区分演化</text>')
    b.append(f'<text x="{cx}" y="{cy+22}" text-anchor="middle" font-size="16" fill="{GREY}">候选（B—C）</text>')
    items = [
        (110, 110, "基本对象", "区分动作 𝒟", BLUE),
        (660, 110, "核心不变量", "分离曲率 κ", GOLD),
        (110, 300, "演化规则", "演化流 Φ", GREEN),
        (660, 300, "三值分类", "κ 的符号", RED),
    ]
    for x, y, lab, sub, col in items:
        b.append(box(x, y, 230, 80, lab, sub, col))
        b.append(f'<line x1="{x+115}" y1="{y+40}" x2="{cx}" y2="{cy}" stroke="{col}" stroke-width="1.4" stroke-dasharray="5 4" opacity="0.6"/>')
    b.append(f'<rect x="250" y="450" width="500" height="72" rx="10" fill="#f4fbf7" stroke="{GREEN}" stroke-width="2"/>')
    b.append(f'<text x="500" y="480" text-anchor="middle" font-size="18" font-weight="700" fill="{GREEN}">硬核：有限图上的两阶段相变（唯一完全兑现，A）</text>')
    b.append(f'<text x="500" y="506" text-anchor="middle" font-size="15" fill="{GREY}">连续情形撞上 1/3 缺口（未解决）</text>')
    return wrap(W, H, "\n".join(b))


def fig_trust_layers():
    W, H = 1000, 520
    b = []
    b.append('<text x="40" y="46" font-size="24" font-weight="700">分层可信度与依赖关系</text>')
    layers = [
        (80, "硬核层 A", "有限图定理（谱定理 + ODE）", GREEN, "复现 / 漏洞 / 反例"),
        (215, "框架层 B", "六元组 + 六公理 + 曲率分类", BLUE, "公理矛盾 / 公理失效"),
        (350, "候选统一层 C", "连续 · 同伦 · 1/3 缺口 · 四场互补", GOLD, "O12/O13/G7 被证伪"),
    ]
    for y, name, sub, col, how in layers:
        b.append(box(70, y, 560, 100, name, sub, col))
        b.append(f'<text x="660" y="{y+42}" font-size="16" fill="{GREY}">证伪方式：</text>')
        b.append(f'<text x="660" y="{y+68}" font-size="16" fill="{INK}">{how}</text>')
    # 依赖箭头：B -> C
    b.append(f'<line x1="350" y1="315" x2="350" y2="350" stroke="{RED}" stroke-width="3" marker-end="url(#ar)"/>')
    b.append(f'<text x="360" y="340" font-size="15" fill="{RED}">仅此一条依赖（B → C）</text>')
    b.append(f'<text x="70" y="480" font-size="15" fill="{GREY}">A 与 B 相互独立；A 与 C 相互独立。攻击 B 层（公理自洽）是推翻整个框架最经济的路径。</text>')
    b = '<defs><marker id="ar" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto"><path d="M0,0 L8,3 L0,6 z" fill="%s"/></marker></defs>' % RED + "\n".join(b)
    return wrap(W, H, b)


def fig_reading_contract():
    W, H = 1000, 520
    b = []
    b.append('<text x="40" y="46" font-size="24" font-weight="700">阅读合约：期望 → 章节 → 严格度</text>')
    rows = [
        ("一个可复算的定理", "第五部分（15—18）", "A", GREEN),
        ("框架如何工作", "第四部分（11—14）", "B", BLUE),
        ("现代统一中的位置", "第二部分（4—6）", "B—C", GOLD),
        ("样板：抽象如何压缩", "第三部分（7—10）", "B", BLUE),
        ("扩展到其他领域", "第六部分（19—25）", "C", GREY),
        ("统一候选的陈述", "第七部分（26—27）", "B—C", RED),
    ]
    y = 90
    b.append(f'<text x="90" y="{y-14}" font-size="16" font-weight="700" fill="{INK}">你的期望</text>')
    b.append(f'<text x="420" y="{y-14}" font-size="16" font-weight="700" fill="{INK}">读这些章</text>')
    b.append(f'<text x="760" y="{y-14}" font-size="16" font-weight="700" fill="{INK}">严格度</text>')
    for i, (exp, sec, grade, col) in enumerate(rows):
        yy = y + i * 62
        b.append(f'<rect x="70" y="{yy}" width="300" height="46" rx="8" fill="#f7f9fc" stroke="{col}" stroke-width="1.5"/>')
        b.append(f'<text x="86" y="{yy+29}" font-size="17">{exp}</text>')
        b.append(f'<text x="420" y="{yy+29}" font-size="17" fill="{GREY}">{sec}</text>')
        b.append(f'<text x="770" y="{yy+29}" font-size="20" font-weight="700" fill="{col}">{grade}</text>')
    b.append(f'<text x="70" y="500" font-size="15" fill="{GREY}">严格度 A=可机器复算；B=有论证；C=方向性。只有第五部分承诺 A。</text>')
    return wrap(W, H, "\n".join(b))


def main():
    figs = {
        "fig24-candidate-core.svg": fig_candidate_core(),
        "fig25-trust-layers.svg": fig_trust_layers(),
        "fig00-reading-contract.svg": fig_reading_contract(),
    }
    for name, svg in figs.items():
        with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
            f.write(svg)
        print("wrote", name)


if __name__ == "__main__":
    main()
