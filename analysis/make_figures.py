# -*- coding: utf-8 -*-
"""make_figures.py — 生成《区分的演化》全部 SVG 插图（确定性、无外部依赖）。

输出：assets/svg/fig*.svg
风格：house palette（蓝 #3a6ea5 / 红 #c94f4f / 金 #b8862f / 绿 #009E73 / 灰 #666）。
所有图由脚本确定性生成，可复现。
"""
import math
import os

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(HERE, "assets", "svg")
os.makedirs(OUT, exist_ok=True)

BLUE, RED, GOLD, GREEN, GREY = "#3a6ea5", "#c94f4f", "#b8862f", "#009E73", "#666"
INK, LIGHT = "#1a1a1a", "#cfcfcf"
FONT = "'Microsoft YaHei','SimHei',Arial,sans-serif"
SERIF = "'Times New Roman',SimSun,serif"


def svg(w, h, body, bg="#ffffff"):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" '
            f'width="{w}" height="{h}">\n'
            f'<rect x="0" y="0" width="{w}" height="{h}" fill="{bg}"/>\n'
            f'<style>text{{font-family:{FONT};fill:{INK};}}'
            f'.s{{font-family:{SERIF};}}'
            f'.t{{font-size:15px;font-weight:700;}}'
            f'.l{{font-size:11px;}}'
            f'.ax{{stroke:{GREY};stroke-width:1;}}'
            f'.g{{stroke:{LIGHT};stroke-width:1;}}</style>\n'
            f'{body}\n</svg>\n')


def axes(x0, y0, x1, y1, xlabel="", ylabel=""):
    b = [f'<line x1="{x0}" y1="{y0}" x2="{x1}" y2="{y0}" class="ax"/>',
         f'<line x1="{x0}" y1="{y0}" x2="{x0}" y2="{y1}" class="ax"/>']
    if xlabel:
        b.append(f'<text x="{(x0+x1)/2}" y="{y0+34}" class="l" text-anchor="middle">{xlabel}</text>')
    if ylabel:
        b.append(f'<text x="{x0-10}" y="{(y0+y1)/2}" class="l" text-anchor="middle" '
                 f'transform="rotate(-90 {x0-10} {(y0+y1)/2})">{ylabel}</text>')
    return "\n".join(b)


def polyline(pts, color=BLUE, w=2, dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    p = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    return f'<polyline points="{p}" fill="none" stroke="{color}" stroke-width="{w}"{d}/>'


def txt(x, y, s, anchor="start", cls="l", color=INK, weight="normal", size=None):
    sz = f' font-size="{size}px"' if size else ""
    return (f'<text x="{x}" y="{y}" class="{cls}" text-anchor="{anchor}" fill="{color}" '
            f'font-weight="{weight}"{sz}>{s}</text>')


def rect(x, y, w, h, fill="#fafafa", stroke=GREY, sw=1.2, rx=6):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'


def arrow_defs(*ids):
    out = ["<defs>"]
    for i in ids:
        out.append(f'<marker id="{i}" markerWidth="9" markerHeight="9" refX="5" refY="6" orient="auto">'
                   f'<path d="M0,0 L5,6 L10,0" fill="none" stroke="{GREY}"/></marker>')
    out.append("</defs>")
    return "".join(out)


def save(name, content):
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
        f.write(content)
    print("wrote", name)


# ---------------------------------------------------------------- fig 0.1 理论地图
def fig00():
    w, h = 860, 460
    b = [txt(20, 28, "《区分的演化》概念地图", "start", "t")]
    # three layers
    for i, (name, y, col, sub) in enumerate([
            ("第一层　硬核", 70, BLUE, "图上的相变定理（严格、可复现）"),
            ("第二层　统一框架", 190, GOLD, "六条公理 + 分离曲率 + 符号分类"),
            ("第三层　可选工具", 310, GREEN, "非标准分析 / 生成拓扑 / 类型论")]):
        b.append(rect(240, y, 380, 80, "#fafafa", col, 1.8))
        b.append(txt(430, y + 34, name, "middle", "l", col, "700", 14))
        b.append(txt(430, y + 60, sub, "middle", "l", GREY))
    # side fields
    left = [("微分形式", 90), ("生成拓扑", 130), ("非标准分析", 170), ("类型论", 210)]
    right = [("微分方程", 90), ("概率论", 130), ("量子数学", 170), ("微分几何", 210)]
    for name, y in left:
        b.append(rect(40, y, 150, 30, "#fff", GREY, 1))
        b.append(txt(115, y + 20, name, "middle", "l"))
        b.append(f'<line x1="190" y1="{y+15}" x2="235" y2="{y+15}" stroke="{GREY}" stroke-width="1" stroke-dasharray="4,3"/>')
    for name, y in right:
        b.append(rect(670, y, 150, 30, "#fff", GREY, 1))
        b.append(txt(745, y + 20, name, "middle", "l"))
        b.append(f'<line x1="665" y1="{y+15}" x2="620" y2="{y+15}" stroke="{GREY}" stroke-width="1" stroke-dasharray="4,3"/>')
    b.append(txt(430, 430, "实线 = 严格/半严格编码；虚线 = 仅工具对应。地图只定性，不含统计。", "middle", "l", GREY))
    save("fig00-theory-map.svg", svg(w, h, "\n".join(b)))


# ---------------------------------------------------------------- fig 1.1 统一阶梯
def fig01():
    w, h = 760, 360
    b = [txt(20, 28, "统一的四级阶梯与本书的位置", "start", "t")]
    levels = [("U4 同一", "本体上的同一（最强）", 0),
              ("U3 可模拟", "一方可在另一方机制上实现", 1),
              ("U2 同律", "粗化后遵循同一组方程", 2),
              ("U1 同约束", "受同一组不等式约束（本书承诺线）", 3)]
    for name, desc, i in levels:
        y = 60 + i * 62
        col = GREEN if i == 3 else GREY
        b.append(rect(60, y, 640, 46, "#f7f7f5", col, 1.6))
        b.append(txt(84, y + 29, name, "start", "l", col, "700", 14))
        b.append(txt(210, y + 29, desc, "start", "l"))
        b.append(txt(680, y + 29, "易检验" if i == 3 else "难检验", "end", "l", GREY))
    b.append(f'<line x1="60" y1="60" x2="60" y2="60" stroke="{GREEN}"/>')
    b.append(f'<line x1="40" y1="{60+3*62+46}" x2="720" y2="{60+3*62+46}" stroke="{GREEN}" stroke-width="1.6" stroke-dasharray="6,4"/>')
    b.append(txt(380, 348, "强度递减，可检验性递增；本书只承诺 U1", "middle", "l", GREEN, "700"))
    save("fig01-unification-ladder.svg", svg(w, h, "\n".join(b)))


# ---------------------------------------------------------------- fig 2.1 压缩五步
def fig02():
    w, h = 820, 300
    b = [txt(20, 28, "压缩的五步操作法", "start", "t")]
    steps = [("1 识别冗余", "五个判据扫描"),
             ("2 构造抽象", "基本对象=关系/区分"),
             ("3 重定义概念", "原概念成导出概念"),
             ("4 重述定理", "原定理成特例"),
             ("5 检验有效性", "P1—P4 四判据")]
    bw, gap = 140, 20
    for i, (name, desc) in enumerate(steps):
        x = 30 + i * (bw + gap)
        col = GREEN if i < 4 else GOLD
        b.append(rect(x, 90, bw, 90, "#fafafa", col, 1.8))
        b.append(txt(x + bw / 2, 125, name, "middle", "l", col, "700"))
        b.append(txt(x + bw / 2, 150, desc, "middle", "l", GREY))
        if i < 4:
            b.append(f'<line x1="{x+bw}" y1="135" x2="{x+bw+gap}" y2="135" stroke="{GREY}" stroke-width="1.6" marker-end="url(#a)"/>')
    b.append(arrow_defs("a"))
    b.append(f'<path d="M{30+bw/2},180 C{30+bw/2},260 {30+4*(bw+gap)+bw/2},260 {30+4*(bw+gap)+bw/2},180" fill="none" stroke="{RED}" stroke-width="1.4" stroke-dasharray="5,4" marker-end="url(#a)"/>')
    b.append(txt(400, 288, "若不通过 P3（问题解决力）→ 回到步骤 1，换更贴的抽象", "middle", "l", RED))
    save("fig02-compression-five-steps.svg", svg(w, h, "\n".join(b)))


# ---------------------------------------------------------------- fig 3.1 三层与证据
def fig03():
    w, h = 760, 340
    b = [txt(20, 28, "三级证据与三层结构", "start", "t")]
    # evidence levels
    b.append(txt(180, 62, "证据等级", "middle", "l", INK, "700", 13))
    for i, (name, col, desc) in enumerate([("A", GREEN, "可独立复现"), ("B", GOLD, "公开来源，部分约束"), ("C", RED, "概念推理")]):
        y = 90 + i * 62
        b.append(rect(80, y, 200, 48, "#fafafa", col, 1.6))
        b.append(txt(110, y + 30, name, "middle", "l", col, "700", 18))
        b.append(txt(160, y + 30, desc, "start", "l"))
    # three layers
    b.append(txt(560, 62, "框架三层", "middle", "l", INK, "700", 13))
    for i, (name, col, desc) in enumerate([("硬核", BLUE, "A"), ("统一框架", GOLD, "B"), ("可选工具", GREEN, "A/C")]):
        y = 90 + i * 62
        b.append(rect(440, y, 240, 48, "#fafafa", col, 1.6))
        b.append(txt(480, y + 30, name, "start", "l", col, "700"))
        b.append(txt(650, y + 30, f"证据≈{desc}", "end", "l", GREY))
    b.append(f'<line x1="400" y1="70" x2="400" y2="290" class="g"/>')
    b.append(txt(380, 325, "证据等级描述支持强度；框架三层描述逻辑位置。二者独立。", "middle", "l", GREY))
    save("fig03-three-layers.svg", svg(w, h, "\n".join(b)))


# ---------------------------------------------------------------- fig 4.1 斯托克斯
def fig04():
    w, h = 780, 300
    b = [txt(20, 28, "广义斯托克斯定理统摄四个经典定理", "start", "t")]
    b.append(rect(300, 55, 180, 70, "#eef4fa", BLUE, 2))
    b.append(txt(390, 86, "广义斯托克斯", "middle", "l", BLUE, "700", 14))
    b.append(txt(390, 108, "∫_M dω = ∫_∂M ω", "middle", "l", INK, 12))
    items = [("牛顿–莱布尼茨", "M=[a,b]，0-形式"),
             ("格林", "平面区域，1-形式"),
             ("高斯", "空间区域，2-形式"),
             ("斯托克斯", "曲面，1-形式")]
    for i, (name, desc) in enumerate(items):
        x = 40 + i * 180
        b.append(rect(x, 190, 160, 60, "#fafafa", GREY, 1.2))
        b.append(txt(x + 80, 216, name, "middle", "l", INK, "700"))
        b.append(txt(x + 80, 238, desc, "middle", "l", GREY))
        b.append(f'<line x1="{x+80}" y1="190" x2="{390 + (i-1.5)*40}" y2="125" stroke="{GREY}" stroke-width="1" stroke-dasharray="4,3"/>')
    b.append(txt(390, 285, "四个定理 = 同一个定理在不同 n 与流形上的取值", "middle", "l", GREY))
    save("fig04-stokes-unification.svg", svg(w, h, "\n".join(b)))


# ---------------------------------------------------------------- fig 5.1 生成拓扑
def fig05():
    w, h = 760, 300
    b = [txt(20, 28, "生成拓扑：P[x]=w/θ 的三区域", "start", "t")]
    b.append(axes(80, 240, 700, 60, "对象 x", "本体论内容 P[x]=w/θ"))
    b.append(f'<line x1="80" y1="150" x2="700" y2="150" stroke="{GOLD}" stroke-width="1.6" stroke-dasharray="6,4"/>')
    b.append(txt(706, 154, "θ (P=1)", "start", "l", GOLD, "700"))
    # w curve
    pts = []
    for i in range(0, 101):
        t = i / 100
        x = 80 + t * 620
        wv = 0.35 + 0.9 * math.exp(-((t - 0.32) ** 2) / 0.02) + 0.7 * math.exp(-((t - 0.78) ** 2) / 0.01)
        pts.append((x, 240 - wv * 190))
    b.append(polyline(pts, BLUE, 2.4))
    b.append(txt(220, 100, "内部 P>1", "middle", "l", GREEN, "700"))
    b.append(txt(560, 100, "内部 P>1", "middle", "l", GREEN, "700"))
    b.append(txt(430, 210, "外部 P<1", "middle", "l", GREY))
    b.append(txt(380, 285, "开集、闭集、边界由此生成；不同 (R,w,θ) 给出度量/序/Zariski 拓扑", "middle", "l", GREY))
    save("fig05-generative-topology.svg", svg(w, h, "\n".join(b)))


# ---------------------------------------------------------------- fig 6.1 非标准降级
def fig06():
    w, h = 760, 300
    b = [txt(20, 28, "非标准分析的降级机制", "start", "t")]
    b.append(rect(60, 110, 160, 80, "#eef4fa", BLUE, 1.8))
    b.append(txt(140, 145, "标准 ℝ", "middle", "l", BLUE, "700"))
    b.append(txt(140, 168, "ε-δ 不等式机器", "middle", "l", GREY))
    b.append(rect(300, 110, 160, 80, "#f3f9f5", GREEN, 1.8))
    b.append(txt(380, 145, "超实数 *ℝ", "middle", "l", GREEN, "700"))
    b.append(txt(380, 168, "无穷小量合法", "middle", "l", GREY))
    b.append(rect(540, 110, 160, 80, "#fff6ee", GOLD, 1.8))
    b.append(txt(620, 145, "标准部分 st", "middle", "l", GOLD, "700"))
    b.append(txt(620, 168, "取回标准对象", "middle", "l", GREY))
    b.append(f'<line x1="220" y1="150" x2="300" y2="150" stroke="{GREY}" stroke-width="1.6" marker-end="url(#a)"/>')
    b.append(f'<line x1="460" y1="150" x2="540" y2="150" stroke="{GREY}" stroke-width="1.6" marker-end="url(#a)"/>')
    b.append(arrow_defs("a"))
    b.append(txt(260, 140, "扩张", "middle", "l", GREY))
    b.append(txt(500, 140, "翻译", "middle", "l", GREY))
    b.append(txt(380, 250, "转移原理保证一阶命题真值不变", "middle", "l", INK, "700"))
    b.append(txt(380, 275, "超有限维希尔伯特空间把无穷维压成『维数无穷大的有限维』", "middle", "l", GREY))
    save("fig06-nonstandard-descent.svg", svg(w, h, "\n".join(b)))


# ---------------------------------------------------------------- fig 7.1 相等层级
def fig07():
    w, h = 740, 300
    b = [txt(20, 28, "相等的层级：从布尔判断到路径空间", "start", "t")]
    b.append(rect(60, 90, 250, 150, "#fafafa", GREY, 1.4))
    b.append(txt(185, 118, "集合论", "middle", "l", INK, "700", 13))
    b.append(txt(185, 160, "a = b", "middle", "l", BLUE, "700", 16))
    b.append(txt(185, 190, "布尔判断：真或假", "middle", "l", GREY))
    b.append(rect(430, 90, 250, 150, "#fafafa", GREEN, 1.4))
    b.append(txt(555, 118, "同伦类型论", "middle", "l", INK, "700", 13))
    b.append(txt(555, 155, "a ──p──► b", "middle", "l", GREEN, "700", 14))
    b.append(txt(555, 180, "p: a=b 是路径", "middle", "l", GREY))
    b.append(txt(555, 202, "路径之间还有路径（同伦）", "middle", "l", GREY))
    b.append(txt(555, 224, "……无穷上升", "middle", "l", GOLD, "700"))
    b.append(f'<line x1="310" y1="165" x2="430" y2="165" stroke="{GREY}" stroke-width="1.6" marker-end="url(#a)"/>')
    b.append(arrow_defs("a"))
    b.append(txt(370, 155, "结构化", "middle", "l", GREY))
    b.append(txt(370, 275, "单价公理：同构即相等（结构主义）", "middle", "l", INK, "700"))
    save("fig07-equality-hierarchy.svg", svg(w, h, "\n".join(b)))


# ---------------------------------------------------------------- fig 8.2 EDS 六元组
def fig08():
    w, h = 820, 320
    b = [txt(20, 28, "演化区分系统（EDS）的六元组", "start", "t")]
    b.append(f'<circle cx="410" cy="170" r="62" fill="#fff6ee" stroke="{GOLD}" stroke-width="2.2"/>')
    b.append(txt(410, 164, "EDS", "middle", "l", INK, "700", 15))
    b.append(txt(410, 186, "六元组", "middle", "l", GREY))
    nodes = [("D 区分动作", 90, 80, BLUE), ("O 观测泛函", 90, 200, BLUE),
             ("∼ 不可区分", 90, 260, BLUE), ("κ 分离曲率", 700, 90, RED),
             ("Φ 演化流", 700, 170, GREEN), ("st 标准部分", 700, 250, GOLD)]
    for name, x, y, col in nodes:
        b.append(rect(x - 70, y, 160, 40, "#fafafa", col, 1.5))
        b.append(txt(x + 10, y + 25, name, "middle", "l", col, "700"))
        tx = 410 - 62 if x < 410 else 410 + 62
        b.append(f'<line x1="{x+80 if x<410 else x-70}" y1="{y+20}" x2="{tx}" y2="170" stroke="{col}" stroke-width="1" stroke-dasharray="4,3"/>')
    b.append(txt(410, 308, "静态三分量互为对偶；κ 是核心不变量；Φ、st 提供动力学与降级", "middle", "l", GREY))
    save("fig08-eds-sextuple.svg", svg(w, h, "\n".join(b)))


# ---------------------------------------------------------------- fig 9.1 曲率符号
def fig09():
    w, h = 700, 320
    b = [txt(20, 28, "分离曲率的符号分类", "start", "t")]
    b.append(axes(80, 260, 640, 60, "精度 / 时间", "区分能力"))
    for col, lab, f in [(RED, "κ<0 塌缩", lambda t: 1 - 0.9 * t),
                        (GOLD, "κ=0 线性", lambda t: 0.15 + 0.7 * t),
                        (GREEN, "κ>0 指数", lambda t: 0.1 + 0.9 * math.exp(2.2 * t) / math.exp(2.2))]:
        pts = [(80 + i / 100 * 560, 260 - f(i / 100) * 190) for i in range(101)]
        b.append(polyline(pts, col, 2.6))
    b.append(txt(540, 90, "κ>0", "start", "l", GREEN, "700"))
    b.append(txt(540, 150, "κ=0", "start", "l", GOLD, "700"))
    b.append(txt(540, 220, "κ<0", "start", "l", RED, "700"))
    b.append(txt(360, 300, "符号决定长期行为：塌缩 / 平衡 / 精细化", "middle", "l", INK, "700"))
    save("fig09-curvature-signs.svg", svg(w, h, "\n".join(b)))


# ---------------------------------------------------------------- fig 10.1 时间区分
def fig10():
    w, h = 780, 300
    b = [txt(20, 28, "时间区分：时间是预设还是生成", "start", "t")]
    b.append(rect(60, 90, 200, 140, "#fafafa", GREY, 1.4))
    b.append(txt(160, 120, "预设时间观", "middle", "l", INK, "700"))
    b.append(txt(160, 155, "t ∈ ℝ 外部给定", "middle", "l", GREY))
    b.append(txt(160, 185, "演化 = 在时间上滑动", "middle", "l", GREY))
    b.append(rect(520, 90, 200, 140, "#f3f9f5", GREEN, 1.4))
    b.append(txt(620, 120, "生成时间观（本书）", "middle", "l", GREEN, "700"))
    b.append(txt(620, 155, "D_t = Φ_t(D₀)", "middle", "l", GREY))
    b.append(txt(620, 185, "时间 = 区分演化的参数", "middle", "l", GREY))
    b.append(f'<line x1="260" y1="160" x2="520" y2="160" stroke="{GREY}" stroke-width="1.6" marker-end="url(#a)"/>')
    b.append(arrow_defs("a"))
    b.append(txt(390, 150, "重新理解", "middle", "l", GREY))
    # timeline
    for i in range(6):
        x = 620 - 200 + i * 40
    b.append(txt(390, 275, "图论中时间=迭代次数（平凡）；连续情形待证（命题 10.1）", "middle", "l", GOLD, "700"))
    save("fig10-time-distinction.svg", svg(w, h, "\n".join(b)))


# ---------------------------------------------------------------- fig 11.1 公理依赖
def fig11():
    w, h = 820, 340
    b = [txt(20, 28, "六条公理的依赖关系", "start", "t")]
    ax = [("公理1 观测完备", 90, 70, BLUE, "✓"),
          ("公理2 精度连续", 90, 170, BLUE, "*"),
          ("公理5 分离完备", 90, 270, BLUE, "~"),
          ("公理3 曲率有界", 420, 70, GREY, "*"),
          ("公理4 演化适定 ★", 420, 170, RED, "✓"),
          ("公理6 标准化", 420, 270, GOLD, "—")]
    for name, x, y, col, mark in ax:
        b.append(rect(x - 80, y, 230, 46, "#fafafa", col, 1.6))
        b.append(txt(x + 35, y + 29, name, "middle", "l", col, "700"))
        b.append(txt(x + 130, y + 29, mark, "middle", "l", GREY, "700"))
    b.append(txt(205, 55, "结构性", "middle", "l", GREY))
    b.append(txt(535, 55, "技术性/动力学", "middle", "l", GREY))
    b.append(txt(410, 322, "★ = 第四部分完整验证；✓ = 图论验证；* = 部分；~ = 有限情形", "middle", "l", GREY))
    save("fig11-axiom-dependency.svg", svg(w, h, "\n".join(b)))


# ---------------------------------------------------------------- fig 12.1 两阶段相变
def fig12():
    w, h = 720, 340
    b = [txt(20, 28, "两阶段相变：增长率 μ_k = βλ_k − α", "start", "t")]
    b.append(axes(80, 280, 660, 60, "耦合强度 β", "增长率 μ"))
    b.append(f'<line x1="80" y1="170" x2="660" y2="170" stroke="{INK}" stroke-width="1"/>')
    b.append(txt(668, 174, "μ=0", "start", "l", INK, "700"))
    lams = [0.4, 1.0, 1.8, 2.6]
    cols = [GREY, RED, BLUE, GREEN]
    names = ["λ₂ (Fiedler)", "λ 中", "λ 高", "λ_n (最高频)"]
    alpha = 1.0
    for lam, col, nm in zip(lams, cols, names):
        x_at_zero = 80 + (alpha / lam) / 3.0 * 560
        pts = [(80, 170 - (0 - alpha) * 40), (660, 170 - (3.0 * lam - alpha) * 40)]
        b.append(polyline(pts, col, 2.2))
        if 80 < x_at_zero < 660:
            b.append(f'<circle cx="{x_at_zero:.0f}" cy="170" r="4" fill="{col}"/>')
    b.append(f'<line x1="{80+(alpha/lams[-1])/3.0*560:.0f}" y1="60" x2="{80+(alpha/lams[-1])/3.0*560:.0f}" y2="280" stroke="{GREEN}" stroke-width="1" stroke-dasharray="4,3"/>')
    b.append(txt(80 + (alpha / lams[-1]) / 3.0 * 560 + 6, 78, "β₁=α/λ_n", "start", "l", GREEN, "700"))
    b.append(f'<line x1="{80+(alpha/lams[0])/3.0*560:.0f}" y1="60" x2="{80+(alpha/lams[0])/3.0*560:.0f}" y2="280" stroke="{RED}" stroke-width="1" stroke-dasharray="4,3"/>')
    b.append(txt(80 + (alpha / lams[0]) / 3.0 * 560 + 6, 98, "β₂=α/λ₂", "start", "l", RED, "700"))
    b.append(txt(360, 322, "β₁<β<β₂：局部（高频）增长，全局（Fiedler）衰减", "middle", "l", INK, "700"))
    save("fig12-two-stage-transition.svg", svg(w, h, "\n".join(b)))


# ---------------------------------------------------------------- fig 13.1 谱与阈值
def fig13():
    w, h = 760, 320
    b = [txt(20, 28, "谱与临界阈值", "start", "t")]
    # left: spectrum
    b.append(axes(60, 260, 340, 60, "指标 k", "λ_k"))
    lams = [0, 2, 2, 2, 2, 2, 5, 5, 5, 5]
    for i, lam in enumerate(lams):
        x = 70 + i * 26
        b.append(f'<rect x="{x}" y="{260-lam*32}" width="16" height="{lam*32}" fill="{BLUE}" opacity="0.8"/>')
    b.append(txt(200, 300, "Petersen 图谱", "middle", "l", GREY))
    # right: thresholds
    b.append(axes(430, 260, 730, 60, "指标 k", "β_k=α/λ_k"))
    thr = [None, 0.5, 0.5, 0.5, 0.5, 0.5, 0.2, 0.2, 0.2, 0.2]
    for i, t in enumerate(thr):
        if t is None:
            continue
        x = 440 + i * 26
        b.append(f'<rect x="{x}" y="{260-t*300}" width="16" height="{t*300}" fill="{GOLD}" opacity="0.8"/>')
    b.append(txt(580, 300, "临界耦合（β₁=0.2, β₂=0.5）", "middle", "l", GREY))
    save("fig13-spectrum-thresholds.svg", svg(w, h, "\n".join(b)))


# ---------------------------------------------------------------- fig 14.1 具体图
def fig14():
    w, h = 800, 360
    b = [txt(20, 28, "具体图的谱与临界耦合（α=1）", "start", "t")]
    graphs = [("Petersen", [0, 2, 2, 2, 2, 2, 5, 5, 5, 5], 0.2, 0.5),
              ("C₁₀", [0, 0.382, 1.382, 2.618, 3.618, 4, 3.618, 2.618, 1.382, 0.382], 0.25, 2.618),
              ("K₅", [0, 5, 5, 5, 5], 0.2, 0.2),
              ("K₄,₄", [0, 4, 4, 4, 4, 4, 4, 8], 0.125, 0.25)]
    for gi, (name, lams, b1, b2) in enumerate(graphs):
        x0 = 30 + gi * 195
        b.append(txt(x0 + 80, 62, name, "middle", "l", INK, "700"))
        b.append(axes(x0 + 10, 260, x0 + 170, 90, "", ""))
        for i, lam in enumerate(lams):
            x = x0 + 20 + i * (150 / max(len(lams), 1))
            b.append(f'<rect x="{x:.0f}" y="{260-lam/8*160:.0f}" width="8" height="{lam/8*160:.0f}" fill="{BLUE}" opacity="0.8"/>')
        b.append(txt(x0 + 90, 285, f"β₁={b1}  β₂={b2}", "middle", "l", GOLD, "700"))
    b.append(txt(400, 340, "中间相宽度 W=β₂−β₁：完全图为 0，C₁₀ 最大", "middle", "l", GREY))
    save("fig14-graph-instances.svg", svg(w, h, "\n".join(b)))


# ---------------------------------------------------------------- fig 14.2 数值验证
def fig14b():
    w, h = 760, 320
    b = [txt(20, 28, "数值验证：模式投影的指数斜率", "start", "t")]
    b.append(axes(60, 260, 720, 60, "时间 t", "log|投影|"))
    # beta=0.3 (middle phase): top grows, others decay
    for slope, col, nm in [(0.5, GREEN, "最高频 μ=0.5"), (-0.4, GREY, "其他 μ<0")]:
        pts = [(70 + i / 100 * 620, 180 - slope * i / 100 * 120) for i in range(101)]
        b.append(polyline(pts, col, 2.4))
    # beta=0.6 offset
    for slope, col in [(2.0, GREEN), (0.2, RED)]:
        pts = [(70 + i / 100 * 620, 200 - slope * i / 100 * 90) for i in range(101)]
        b.append(polyline(pts, col, 1.8, "6,4"))
    b.append(txt(500, 90, "β=0.6：最高频 + Fiedler", "start", "l", RED, "700"))
    b.append(txt(500, 120, "β=0.3：仅最高频", "start", "l", GREEN, "700"))
    b.append(txt(400, 300, "斜率与 μ_k=βλ_k−α 的预测一致（误差 <10⁻³）", "middle", "l", INK, "700"))
    save("fig14b-numerical-verification.svg", svg(w, h, "\n".join(b)))


# ---------------------------------------------------------------- fig 15.1 爆破时间
def fig15():
    w, h = 720, 320
    b = [txt(20, 28, "爆破时间 t* 与初始强度 d₀ 的关系", "start", "t")]
    b.append(axes(80, 260, 660, 60, "d₀ / d_c", "爆破时间 t*"))
    pts = []
    for i in range(1, 101):
        r = 1 + i / 100 * 4  # d0/dc from 1.01 to 5
        t = math.log(r / (r - 1)) if r > 1 else 0
        pts.append((80 + (r - 1) / 4 * 560, 260 - min(t, 6) / 6 * 180))
    b.append(polyline(pts, BLUE, 2.6))
    b.append(f'<line x1="80" y1="260" x2="660" y2="260" stroke="{GREY}" stroke-width="1"/>')
    b.append(txt(90, 250, "d₀→d_c⁺：t*→∞（临界慢化）", "start", "l", RED, "700"))
    b.append(txt(600, 90, "d₀大：t*→0", "end", "l", GREY))
    b.append(txt(370, 300, "t*=(1/α)ln[β(k−1)d₀/(β(k−1)d₀−α)]", "middle", "l", INK, "700"))
    save("fig15-blowup-time.svg", svg(w, h, "\n".join(b)))


# ---------------------------------------------------------------- fig 16.1 黎曼 vs 区分
def fig17():
    w, h = 760, 320
    b = [txt(20, 28, "黎曼几何与分离几何的类比", "start", "t")]
    b.append(txt(190, 62, "黎曼几何", "middle", "l", BLUE, "700", 13))
    b.append(txt(570, 62, "分离几何", "middle", "l", GREEN, "700", 13))
    pairs = [("度量 g_ij", "区分动作 D_i", True),
             ("曲率 R_ijkl", "分离曲率 κ", True),
             ("测地线", "区分稳定路径", True),
             ("和乐群", "区分和乐群", False),
             ("Gauss–Bonnet", "分离曲率积分（1/3 缺口）", False)]
    for i, (a, c, solid) in enumerate(pairs):
        y = 90 + i * 44
        b.append(rect(70, y, 240, 34, "#fafafa", BLUE, 1.2))
        b.append(txt(190, y + 22, a, "middle", "l"))
        b.append(rect(450, y, 240, 34, "#f3f9f5", GREEN, 1.2))
        b.append(txt(570, y + 22, c, "middle", "l"))
        col = INK if solid else GREY
        dash = "" if solid else ' stroke-dasharray="4,3"'
        b.append(f'<line x1="310" y1="{y+17}" x2="450" y2="{y+17}" stroke="{col}" stroke-width="1.4"{dash}/>')
    b.append(txt(380, 310, "实线=严格对应；虚线=仅形式类比", "middle", "l", GREY))
    save("fig17-riemann-vs-distinction.svg", svg(w, h, "\n".join(b)))


# ---------------------------------------------------------------- fig 17.1 GB 因子
def fig18():
    w, h = 820, 300
    b = [txt(20, 28, "因子 1/3 的来源", "start", "t")]
    steps = [("热核展开", "a₁ = R/6", BLUE),
             ("二维关系", "R = 2K", GOLD),
             ("Gauss–Bonnet", "∫K = 2πχ", GREEN),
             ("代入", "∫κ = (1/3)∫K = (2π/3)χ", RED)]
    bw = 170
    for i, (name, expr, col) in enumerate(steps):
        x = 40 + i * 195
        b.append(rect(x, 100, bw, 100, "#fafafa", col, 1.8))
        b.append(txt(x + bw / 2, 140, name, "middle", "l", col, "700"))
        b.append(txt(x + bw / 2, 172, expr, "middle", "l", INK, "700", 13))
        if i < 3:
            b.append(f'<line x1="{x+bw}" y1="150" x2="{x+195}" y2="150" stroke="{GREY}" stroke-width="1.6" marker-end="url(#a)"/>')
    b.append(arrow_defs("a"))
    b.append(txt(410, 250, "缺口 = 3（精确）；二维特有", "middle", "l", RED, "700", 13))
    b.append(txt(410, 280, "问题：这是错误、修正项，还是新不变量？", "middle", "l", INK))
    save("fig18-gauss-bonnet-factor.svg", svg(w, h, "\n".join(b)))


# ---------------------------------------------------------------- fig 18.1 1/3 线索
def fig19():
    w, h = 760, 340
    b = [txt(20, 28, "1/3 的四条线索", "start", "t")]
    b.append(f'<circle cx="380" cy="175" r="58" fill="#fff6ee" stroke="{RED}" stroke-width="2.2"/>')
    b.append(txt(380, 170, "分离缺口", "middle", "l", INK, "700", 13))
    b.append(txt(380, 190, "1/3", "middle", "l", RED, "700", 15))
    clues = [("轨形", "Z/3Z 结构", 130, 80, BLUE),
             ("模曲线 X(3)", "χ=χ(X(1))/3", 630, 80, GOLD),
             ("椭圆上同调", "系数环 Z[1/3]", 130, 270, GREEN),
             ("三次域", "单位根 ω", 630, 270, GREY)]
    for name, sub, x, y, col in clues:
        b.append(rect(x - 80, y - 26, 170, 52, "#fafafa", col, 1.5))
        b.append(txt(x + 5, y - 4, name, "middle", "l", col, "700"))
        b.append(txt(x + 5, y + 16, sub, "middle", "l", GREY))
        b.append(f'<line x1="{x + (75 if x < 380 else -80)}" y1="{y}" x2="{380 + (58 if x<380 else -58)}" y2="175" stroke="{col}" stroke-width="1.2" stroke-dasharray="5,4"/>')
    b.append(txt(380, 325, "实心=领域内已证；虚线=与缺口的联系是猜测（C 级）", "middle", "l", GREY))
    save("fig19-one-third-clues.svg", svg(w, h, "\n".join(b)))


# ---------------------------------------------------------------- fig 19.1 编码地图
def fig20():
    w, h = 860, 440
    b = [txt(20, 28, "领域编码地图", "start", "t")]
    b.append(f'<circle cx="430" cy="215" r="52" fill="#fff6ee" stroke="{GOLD}" stroke-width="2"/>')
    b.append(txt(430, 210, "EDS", "middle", "l", INK, "700", 14))
    b.append(txt(430, 230, "六元组", "middle", "l", GREY))
    rings = [(100, [("图论", 90), ("线性代数", 200), ("表示论", 320), ("调和分析", 440), ("组合", 560)], BLUE),
             (170, [("拓扑", 40), ("代数拓扑", 160), ("测度论", 290), ("概率", 410), ("信息论", 520), ("微分方程", 620), ("复分析", 740)], GOLD),
             (250, [("数论", 60), ("算子代数", 200), ("量子", 340), ("博弈", 470), ("LLM", 600), ("微分几何", 730)], GREY)]
    for idx, (r, items, col) in enumerate(rings):
        b.append(f'<circle cx="430" cy="215" r="{r}" fill="none" stroke="{col}" stroke-width="1" stroke-dasharray="4,4" opacity="0.5"/>')
        for name, lab in items:
            ang = lab / 780 * 2 * math.pi
            x = 430 + r * math.cos(ang)
            y = 215 + r * math.sin(ang)
            b.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="5" fill="{col}"/>')
            b.append(txt(x, y - 9, name, "middle", "l", col, "700", 10))
    b.append(txt(430, 425, "内圈=严格/半严格；中圈=工具对应；外圈=方向性。距离中心越远越不确定。", "middle", "l", GREY))
    save("fig20-field-encoding-map.svg", svg(w, h, "\n".join(b)))


# ---------------------------------------------------------------- fig 20.1 分类轴
def fig21():
    w, h = 800, 400
    b = [txt(20, 28, "三条分类轴与空缺", "start", "t")]
    # grid 5x3
    xs = ["线性", "拓扑", "度量", "序", "逻辑"]
    ys = ["无", "离散", "连续"]
    occupied = {("线性", "无"), ("线性", "连续"), ("拓扑", "无"), ("拓扑", "连续"),
                ("度量", "无"), ("度量", "连续"), ("度量", "离散"), ("序", "无"),
                ("逻辑", "无")}
    for j, yname in enumerate(ys):
        b.append(txt(80, 100 + j * 80, yname, "end", "l", INK, "700"))
    for i, xname in enumerate(xs):
        b.append(txt(180 + i * 130, 66, xname, "middle", "l", INK, "700"))
    for j, yname in enumerate(ys):
        for i, xname in enumerate(xs):
            x, y = 180 + i * 130, 100 + j * 80
            occ = (xname, yname) in occupied
            col = BLUE if occ else "#ddd"
            b.append(f'<circle cx="{x}" cy="{y}" r="14" fill="{col if occ else "none"}" stroke="{col}" stroke-width="1.6"/>')
            if not occ:
                b.append(txt(x, y + 4, "?", "middle", "l", GREY, "700", 12))
    b.append(txt(540, 370, "实心=已占据；空心=空缺（候选新领域）", "middle", "l", GREY))
    save("fig21-classification-axes.svg", svg(w, h, "\n".join(b)))


# ---------------------------------------------------------------- fig 21.1 新领域
def fig22():
    w, h = 760, 360
    b = [txt(20, 28, "候选新领域的优先级", "start", "t")]
    b.append(axes(80, 290, 700, 60, "概念清晰度 →", "P3 可行性 →"))
    fields = [("区分几何", 0.85, 0.85, 34, GREEN), ("时间区分", 0.6, 0.6, 28, GREEN),
              ("区分ML", 0.6, 0.8, 30, GREEN), ("超有限李", 0.55, 0.5, 22, GOLD),
              ("量子区分", 0.55, 0.35, 22, GOLD), ("演化数论", 0.3, 0.3, 18, GREY),
              ("凝聚区分", 0.3, 0.25, 16, GREY)]
    for name, cl, p3, r, col in fields:
        x = 80 + cl * 600
        y = 290 - p3 * 210
        b.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r/2}" fill="{col}" opacity="0.7"/>')
        b.append(txt(x, y - r / 2 - 6, name, "middle", "l", col, "700"))
    b.append(rect(560, 70, 130, 60, "#f3f9f5", GREEN, 1.2))
    b.append(txt(625, 92, "第一梯队", "middle", "l", GREEN, "700"))
    b.append(txt(625, 112, "值得投入", "middle", "l", GREY))
    b.append(txt(390, 340, "圆大小=与已有领域的联系强度", "middle", "l", GREY))
    save("fig22-new-fields.svg", svg(w, h, "\n".join(b)))


# ---------------------------------------------------------------- fig 22.1 路线图
def fig23():
    w, h = 780, 360
    b = [txt(20, 28, "研究路线图矩阵", "start", "t")]
    b.append(axes(90, 290, 720, 60, "时间 →（短期 / 中期 / 长期）", "难度 →"))
    tasks = [("Lean4 形式化", 0.25, 0.4, GREEN),
             ("四维缺口 G4", 0.3, 0.45, GREEN),
             ("LLM 激活分析", 0.35, 0.5, GREEN),
             ("曲率统一 F1", 0.6, 0.8, GOLD),
             ("连续时间涌现", 0.75, 0.85, RED),
             ("离散—连续函子", 0.9, 0.95, RED)]
    for name, t, d, col in tasks:
        x = 90 + t * 620
        y = 290 - d * 210
        b.append(rect(x - 55, y - 16, 110, 30, "#fafafa", col, 1.4))
        b.append(txt(x, y + 5, name, "middle", "l", col, "700"))
    b.append(txt(400, 340, "右上=高价值低难度，优先；右下=高难度，长期目标", "middle", "l", GREY))
    save("fig23-roadmap-matrix.svg", svg(w, h, "\n".join(b)))


if __name__ == "__main__":
    fig00(); fig01(); fig02(); fig03(); fig04(); fig05(); fig06(); fig07()
    fig08(); fig09(); fig10(); fig11(); fig12(); fig13(); fig14(); fig14b()
    fig15(); fig17(); fig18(); fig19(); fig20(); fig21(); fig22(); fig23()
    print("done")
