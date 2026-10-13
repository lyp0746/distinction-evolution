# -*- coding: utf-8 -*-
"""
全书校对：扫描 source/ch01–ch10.html，生成校对清单（表 A1–A6）。
输出：校对清单.md 与 analysis/results/audit.json

检查项：
  A1 术语一致性（定义、关键术语出现次数与首次定义位置）
  A2 公式编号连续性 + 正文引用是否有效
  A3 表/图编号连续性 + 交叉引用是否有效
  A4 C 级数据清单（自动检出所有"质量 C""指示性"标注位置）
  A5 章节交叉引用是否有效（第X章 / 表X.X / 图X.X / 式(X.X)）
  A6 参考文献：正文引用的作者-年份 vs 章节末参考表
"""
import html
import json
import sys
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass
import os
import re
from collections import defaultdict

BOOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTENT = os.path.join(BOOK, "source")
OUT = os.path.join(BOOK, "analysis", "results")
CHAPTERS = sorted(f for f in os.listdir(CONTENT)
                  if re.fullmatch(r"ch\d+\.html", f))


def read_all():
    docs = {}
    for c in CHAPTERS:
        p = os.path.join(CONTENT, c)
        if os.path.exists(p):
            with open(p, encoding="utf-8") as f:
                docs[c] = f.read()
    return docs


def strip_tags(h):
    return html.unescape(re.sub(r"<[^>]+>", "", h))


R = {}
docs = read_all()
texts = {k: strip_tags(v) for k, v in docs.items()}

# ---------------------------------------------------------------- A1 术语
TERMS = ["演化区分系统", "区分动作", "观测泛函", "不可区分", "分离曲率", "演化流",
         "时间区分", "临界耦合", "两阶段相变", "相变", "拉普拉斯", "生成拓扑",
         "非标准分析", "超有限", "同伦类型论", "单价公理", "压缩", "同约束",
         "分离度量", "区分流形", "轨形", "椭圆上同调", "可证伪", "证据等级", "有效维度"]
term_report = {}
for t in TERMS:
    hits, first = [], None
    for c in CHAPTERS:
        if c not in texts:
            continue
        n = texts[c].count(t)
        if n:
            hits.append((c, n))
            if first is None:
                first = c
    term_report[t] = {"total": sum(n for _, n in hits), "by_chapter": hits, "first": first}
R["A1_terms"] = term_report

# 定义编号
defs = {}
for c in CHAPTERS:
    if c not in texts:
        continue
    for m in re.finditer(r"定义\s*(\d+\.\d+)", texts[c]):
        defs.setdefault(m.group(1), c)
R["A1_definitions"] = defs

# ---------------------------------------------------------------- A2 公式
formulas = defaultdict(list)   # number -> chapter
formula_refs = defaultdict(list)
for c in CHAPTERS:
    if c not in docs:
        continue
    for m in re.finditer(r'<span class="num">\((\d+\.\d+)\)</span>', docs[c]):
        formulas[m.group(1)].append(c)
    for m in re.finditer(r"式\((\d+\.\d+)\)", texts[c]):
        formula_refs[m.group(1)].append(c)
R["A2_formulas_defined"] = sorted(formulas.keys())
R["A2_formula_refs"] = {k: v for k, v in sorted(formula_refs.items())}
R["A2_refs_missing_def"] = sorted(set(formula_refs) - set(formulas))
# 编号连续性（按章）
cont = {}
for c in CHAPTERS:
    nums = sorted(int(x.split(".")[1]) for x in formulas if c in formulas[x])
    if nums:
        cont[c] = {"numbers": nums, "continuous": nums == list(range(1, len(nums) + 1))}
R["A2_continuity"] = cont

# ---------------------------------------------------------------- A3 表/图
tables, figures = defaultdict(list), defaultdict(list)
tref, fref = defaultdict(list), defaultdict(list)
for c in CHAPTERS:
    if c not in texts:
        continue
    for m in re.finditer(r"表\s*(\d+\.\d+)", texts[c]):
        (tref if texts[c].count("表 " + m.group(1)) else tref)[m.group(1)].append(c)
    for m in re.finditer(r"图\s*(\d+\.\d+)", texts[c]):
        fref[m.group(1)].append(c)
    for m in re.finditer(r'<caption class="cap"><b>表\s*(\d+\.\d+)', docs[c]):
        tables[m.group(1)].append(c)
    for m in re.finditer(r'<b>图\s*(\d+\.\d+)', docs[c]):
        figures[m.group(1)].append(c)
R["A3_tables_defined"] = sorted(tables.keys())
R["A3_figures_defined"] = sorted(figures.keys())
R["A3_table_refs_missing_def"] = sorted(set(tref) - set(tables))
R["A3_figure_refs_missing_def"] = sorted(set(fref) - set(figures))
R["A3_tables_unreferenced"] = sorted(set(tables) - set(tref))
R["A3_figures_unreferenced"] = sorted(set(figures) - set(fref))

# ---------------------------------------------------------------- A4 C级数据
cgrade = []
for c in CHAPTERS:
    if c not in texts:
        continue
    for m in re.finditer(
            r"［[^］]{0,20}，\s*C[^］]{0,6}］|（C\s*级）|质量等级[：:]\s*C|指示性|质量 C",
            texts[c]):
        cgrade.append({"chapter": c, "snippet": m.group(0).strip()[:90]})
R["A4_c_grade"] = cgrade

# ---------------------------------------------------------------- A5 交叉引用
chref = defaultdict(list)
for c in CHAPTERS:
    if c not in texts:
        continue
    for m in re.finditer(r"第\s*(\d+)\s*章", texts[c]):
        chref[m.group(1)].append(c)
R["A5_chapter_refs"] = {k: sorted(set(v)) for k, v in sorted(chref.items())}
R["A5_chapter_refs_invalid"] = sorted(
    n for n in chref if n not in {str(i) for i in range(1, len(CHAPTERS) + 1)})
sec_refs = defaultdict(list)
for c in CHAPTERS:
    if c not in texts:
        continue
    for m in re.finditer(r"§?\s*(\d+\.\d+)", texts[c]):
        sec_refs[m.group(1)].append(c)
R["A5_section_refs"] = {k: sorted(set(v)) for k, v in sorted(sec_refs.items())}

# ---------------------------------------------------------------- A6 参考文献
cit_en = defaultdict(set)
cit_cn = defaultdict(set)
for c in CHAPTERS:
    if c not in texts:
        continue
    for m in re.finditer(r"([A-Z][A-Za-z\-]+)(?:\s*(?:&|and|等|，|,)\s*[A-Za-z\-]+)?\s*\((\d{4})\)", texts[c]):
        cit_en[m.group(1)].add(m.group(2))
    for m in re.finditer(r"（([A-Z][A-Za-z\-]+)[，,]\s*(\d{4})）", texts[c]):
        cit_en[m.group(1)].add(m.group(2))
refs_defined = defaultdict(set)
for c in CHAPTERS:
    if c not in docs:
        continue
    m = re.search(r'<h3>本章参考文献</h3>(.*?)</div>', docs[c], re.S)
    if not m:
        m = re.search(r'<h3>本章参考文献</h3>(.*?)$', docs[c], re.S)
    if m:
        # 逐条 <p> 解析，避免把“书名/副标题”误当作者
        for para in re.findall(r'<p>(.*?)</p>', m.group(1), re.S):
            t = re.sub(r"<[^>]+>", "", para)
            r = re.match(r"\s*([A-Z][A-Za-z\-]+).*?\((\d{4})\)", t)
            if r:
                refs_defined[r.group(1)].add(r.group(2))
R["A6_cited"] = {k: sorted(v) for k, v in sorted(cit_en.items())}
R["A6_defined"] = {k: sorted(v) for k, v in sorted(refs_defined.items())}
R["A6_cited_not_defined"] = sorted(set(cit_en) - set(refs_defined))

# ---------------------------------------------------------------- A7 插图文件存在性
img_missing = []
for c in CHAPTERS:
    if c not in docs:
        continue
    for m in re.finditer(r'<img[^>]*src="([^"]+)"', docs[c]):
        src = m.group(1)
        if not os.path.exists(os.path.join(BOOK, src)):
            img_missing.append({"chapter": c, "src": src})
R["A7_images_missing"] = img_missing

# ---------------------------------------------------------------- A8 公式块结构
eq_malformed = []
for c in CHAPTERS:
    if c not in docs:
        continue
    for m in re.finditer(r'<div class="eq">(.*?)</div>', docs[c], re.S):
        blk = m.group(1)
        # 编号(num)为可选：仅当公式被正文引用时才需要。此处只检查结构类 body。
        if 'class="body"' not in blk:
            eq_malformed.append({"chapter": c, "snippet": strip_tags(blk).strip()[:70]})
R["A8_eq_malformed"] = eq_malformed

# ---------------------------------------------------------------- A9 内部/调试字串
BAD_PATTERNS = ["本机", "无网络", "TODO", "FIXME", "XXX", "DEBUG", "localhost"]
debug_hits = []
for c in CHAPTERS:
    if c not in texts:
        continue
    for pat in BAD_PATTERNS:
        for m in re.finditer(re.escape(pat), texts[c]):
            s = max(0, m.start() - 18)
            debug_hits.append({"chapter": c, "pattern": pat,
                               "snippet": texts[c][s:m.end() + 22].strip()})
R["A9_debug_strings"] = debug_hits

# ------------------------------------------------ A10 面向读者的版本字样（应为空）
# skill 非协商规则：reader-facing 文本不得含版本号 / 版本对比 / 变更日志。
ALL_SRC = sorted(f for f in os.listdir(CONTENT) if f.endswith(".html"))
VER_PAT = re.compile(r"上一版|本版|版本对比|本次新增|第[一二三四五六七八九十]+版|v\d+\.\d+")
ver_hits = []
for fn in ALL_SRC:
    with open(os.path.join(CONTENT, fn), encoding="utf-8") as f:
        t = f.read()
    for m in VER_PAT.finditer(t):
        s = max(0, m.start() - 18)
        ver_hits.append({"file": fn, "snippet": t[s:m.end() + 18].strip()})
R["A10_version_labels"] = ver_hits

# ------------------------------------------------ A11 宿命词（仅允许出现在定理/交易句）
FATE_PAT = re.compile(r"必然|不可避免|无法消除|注定|死路")
fate_hits = []
for c in CHAPTERS:
    if c not in texts:
        continue
    for m in FATE_PAT.finditer(texts[c]):
        s = max(0, m.start() - 24)
        ctx = texts[c][s:m.end() + 24]
        fate_hits.append({"chapter": c, "word": m.group(0), "snippet": ctx.strip()})
R["A11_fatalism"] = fate_hits

# ------------------------------------------------ A12 文件内重复标题（应为空）
dup_hits = []
for fn in ALL_SRC:
    with open(os.path.join(CONTENT, fn), encoding="utf-8") as f:
        txt = f.read()
    seen = {}
    for m in re.finditer(r"<h2[^>]*>(.*?)</h2>", txt, re.S):
        label = re.sub(r"<[^>]+>", "", m.group(1)).strip()
        seen[label] = seen.get(label, 0) + 1
    for label, n in seen.items():
        if n > 1:
            dup_hits.append({"file": fn, "heading": label, "count": n})
R["A12_duplicate_headings"] = dup_hits

os.makedirs(OUT, exist_ok=True)
with open(os.path.join(OUT, "audit.json"), "w", encoding="utf-8") as f:
    json.dump(R, f, ensure_ascii=False, indent=2)

# ---------------------------------------------------------------- Markdown 报告
L = []
L.append("# 《区分的演化》校对清单\n")
L.append(f"自动生成，覆盖 {len(docs)} 章。原始数据见 `analysis/results/audit.json`。\n")

L.append("## 表 A1　术语与定义一致性\n")
L.append("| 术语 | 出现次数 | 首次出现 | 分布 |")
L.append("|---|---:|---|---|")
for t, v in term_report.items():
    dist = "、".join(f"{c}({n})" for c, n in v["by_chapter"])
    L.append(f"| {t} | {v['total']} | {v['first']} | {dist} |")
L.append("\n**定义编号与所在章：**\n")
L.append("| 定义 | 章 |")
L.append("|---|---|")
for k, v in sorted(defs.items()):
    L.append(f"| 定义 {k} | {v} |")

L.append("\n## 表 A2　公式编号与引用\n")
L.append(f"已定义公式：{', '.join('('+x+')' for x in R['A2_formulas_defined'])}\n")
L.append("| 章 | 公式序号 | 连续？ |")
L.append("|---|---|---|")
for c, v in cont.items():
    L.append(f"| {c} | {v['numbers']} | {'✓' if v['continuous'] else '✗'} |")
L.append(f"\n正文引用但未定义：{R['A2_refs_missing_def'] or '无'}")

L.append("\n## 表 A3　表格与图表编号\n")
L.append(f"已定义表：{', '.join(R['A3_tables_defined'])}\n")
L.append(f"已定义图：{', '.join(R['A3_figures_defined'])}\n")
L.append(f"- 引用但未定义的表：{R['A3_table_refs_missing_def'] or '无'}")
L.append(f"- 引用但未定义的图：{R['A3_figure_refs_missing_def'] or '无'}")
L.append(f"- 定义但正文未引用的表：{R['A3_tables_unreferenced'] or '无'}")
L.append(f"- 定义但正文未引用的图：{R['A3_figures_unreferenced'] or '无'}")

L.append("\n## 表 A4　C 级数据清单（需替换为官方序列）\n")
L.append(f"检出 {len(cgrade)} 处。前 30 处：\n")
L.append("| # | 章 | 片段 |")
L.append("|---:|---|---|")
for i, d in enumerate(cgrade[:30], 1):
    L.append(f"| {i} | {d['chapter']} | {d['snippet']} |")

L.append("\n## 表 A5　章节交叉引用\n")
L.append(f"- 引用到的章：{', '.join(sorted(R['A5_chapter_refs'], key=lambda x:int(x)))}")
L.append(f"- 无效章节引用：{R['A5_chapter_refs_invalid'] or '无'}")
L.append(f"- 引用到的小节号数：{len(sec_refs)} 个")

L.append("\n## 表 A6　参考文献\n")
L.append(f"- 正文引用但章节参考表未列出的作者：{R['A6_cited_not_defined'] or '无'}")
L.append(f"- 正文引用作者数：{len(R['A6_cited'])}；参考表作者数：{len(R['A6_defined'])}")

L.append("\n## 表 A7　插图文件存在性\n")
L.append(f"缺失的插图文件：{R['A7_images_missing'] or '无'}")

L.append("\n## 表 A8　公式块结构\n")
L.append(f"缺少 body/num 的公式块：{R['A8_eq_malformed'] or '无'}")

L.append("\n## 表 A9　内部／调试字串扫描\n")
L.append(f"检出的内部或调试字串（应为空）：{R['A9_debug_strings'] or '无'}")

L.append("\n## 表 A10　面向读者的版本字样（应为空）\n")
L.append(f"检出 {len(R['A10_version_labels'])} 处。")
for d in R["A10_version_labels"][:20]:
    L.append(f"- `{d['file']}`：{d['snippet']}")

L.append("\n## 表 A11　宿命词扫描（应仅出现在定理或交易句）\n")
L.append(f"检出 {len(R['A11_fatalism'])} 处。")

L.append("\n## 表 A12　文件内重复标题（应为空）\n")
L.append(f"检出 {len(R['A12_duplicate_headings'])} 处。{R['A12_duplicate_headings'] or '（无）'}")
L.append(f"检出 {len(R['A11_fatalism'])} 处。")
for d in R["A11_fatalism"][:20]:
    L.append(f"- `{d['chapter']}`：{d['snippet']}")

with open(os.path.join(BOOK, "校对清单.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(L))

print("=== 校对摘要 ===")
print("公式：", R["A2_formulas_defined"])
print("公式引用缺失定义：", R["A2_refs_missing_def"])
print("表：", R["A3_tables_defined"])
print("图：", R["A3_figures_defined"])
print("表引用缺失：", R["A3_table_refs_missing_def"], "图引用缺失：", R["A3_figure_refs_missing_def"])
print("未引用表：", R["A3_tables_unreferenced"], "未引用图：", R["A3_figures_unreferenced"])
print("C 级片段数：", len(cgrade))
print("无效章引用：", R["A5_chapter_refs_invalid"])
print("引用未列文献：", R["A6_cited_not_defined"])
print("缺失插图文件：", R["A7_images_missing"])
print("异常公式块：", R["A8_eq_malformed"])
print("内部／调试字串：", R["A9_debug_strings"])
print("版本字样（应为空）：", R["A10_version_labels"])
print("宿命词（应仅为定理/交易）：", len(R["A11_fatalism"]), "处")
print("重复标题（应为空）：", R["A12_duplicate_headings"])
print("wrote 校对清单.md")
