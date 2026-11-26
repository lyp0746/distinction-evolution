# -*- coding: utf-8 -*-
"""
build_book.py — 把 source/ 下的书稿组装为自包含 HTML，并调用无头浏览器打印 PDF。

设计要点
--------
* 目录可跳转：正文各级标题自动生成锚点，目录（含小节级 l3）全部为内部链接。
* 电子书标准：打印时启用 Chrome 的 ``--generate-pdf-document-outline``，
  由 ``h1``（部分）/``h2``（章）/``h3``（节）自动生成**分级 PDF 书签**；
  ``build_epub.py`` 另外生成带 nav/ncx 的 EPUB 3。
* 第一版版式：A4 单栏、衬线正文（Times + SimSun）、无衬线标题、
  10.5pt / 1.5 倍行距、35mm 侧边距（见 assets/css/paper.css）。
* 双版本：默认印刷版；``--ereader`` 叠加 ereader.css 生成电子阅读版。

用法
----
    python build_book.py                 # -> output/book.html
    python build_book.py --pdf           # -> output/book.html + output/book.pdf
    python build_book.py --ereader --pdf # -> output/book-ereader.html + output/book-ereader.pdf
"""
import base64
import datetime
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCE = os.path.join(HERE, "source")
CSS_DIR = os.path.join(HERE, "assets", "css")
OUTPUT = os.path.join(HERE, "output")
DATA_DIR = os.path.join(HERE, "data")

FRONT = [("总纲　现实中不存在无限", "front_finitude.html", "finitude"),
         ("先读这一页　五个可复算的事实", "front_hardcore.html", "hardcore"),
         ("前言　为什么把“统一”降级为“可检验的操作”", "front_preface.html", "preface"),
         ("十分钟读懂本书", "front_quickstart.html", "quickstart"),
         ("阅读合约　本书向你承诺什么，又不承诺什么", "front_theorymap.html", "theorymap"),
         ("术语、记号与断言分级速查", "front_terms.html", "terms")]
BACK = [
        ("结语　一份开放的邀请", "back_epilogue.html", "apxe"),
        ("本系列（九本书）", "back_popular_guide.html", "apxp"),
        ("参考文献", "back_references.html", "apxr"),
        ("术语表", "back_glossary.html", "apxg"),
        ("附录 A　形式化与证明", "appendix_a.html", "apxA"),
        ("附录 B　数据与案例", "appendix_b.html", "apxB"),
        ("附录 C　工具与清单", "appendix_d.html", "apxC"),
        ("附录 D　可证伪登记簿（append-only）", "appendix_e.html", "apxD"),
        ("附录 E　定理与命题索引", "appendix_f.html", "apxE"),
        ("附录 F　术语中英对照", "appendix_f2.html", "apxF"),
]

def load_json(p, default=None):
    if not os.path.exists(p):
        return default
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def _data_uri(path):
    """把 PNG/SVG 编码为 data URI，保持 <img> 标签合法且矢量清晰。"""
    ext = path.lower().rsplit(".", 1)[-1]
    mime = {"png": "image/png", "svg": "image/svg+xml"}.get(ext, "application/octet-stream")
    with open(path, "rb") as f:
        return f"data:{mime};base64," + base64.b64encode(f.read()).decode()


def inline_images(html):
    """把 <img src="....png|svg"> 替换为内嵌的 base64 data URI。

    注意：只能替换 src 属性，绝不能把整段 SVG 插进 <img> 内部
    （那会产生 `<img ... <svg ...>` 这种非法标签，导致图裂与标签外泄）。
    """
    def rep(m):
        tag, src = m.group(0), m.group(1)
        p = os.path.join(HERE, src)
        if not os.path.exists(p):
            print("  [warn] missing figure:", src)
            return tag
        return tag.replace(f'src="{src}"', f'src="{_data_uri(p)}"')
    return re.sub(r'<img\b[^>]*?src="([^"]+\.(?:png|svg))"[^>]*>', rep, html)


def annotate_headings(html):
    """给编号小节标题加锚点：h3（2.3）-> sec2-3，h4（2.3.1）-> sec2-3-1。"""
    def rep_h3(m):
        attrs, inner = m.group(1), m.group(2)
        txt = re.sub(r"<[^>]+>", "", inner)
        mm = re.match(r"\s*(\d+)\.(\d+)", txt)
        if mm and "id=" not in attrs:
            return f'<h3 id="sec{mm.group(1)}-{mm.group(2)}"{attrs}>{inner}</h3>'
        return m.group(0)

    def rep_h4(m):
        attrs, inner = m.group(1), m.group(2)
        txt = re.sub(r"<[^>]+>", "", inner)
        mm = re.match(r"\s*(\d+)\.(\d+)\.(\d+)", txt)
        if mm and "id=" not in attrs:
            sid = f"sec{mm.group(1)}-{mm.group(2)}-{mm.group(3)}"
            return f'<h4 id="{sid}"{attrs}>{inner}</h4>'
        return m.group(0)

    html = re.sub(r"<h3([^>]*)>(.*?)</h3>", rep_h3, html, flags=re.S)
    html = re.sub(r"<h4([^>]*)>(.*?)</h4>", rep_h4, html, flags=re.S)
    return html


def numbered_subsections(fname):
    """自某章源文件提取编号为 X.Y.Z 的子小节，用于目录第四级。"""
    p = os.path.join(SOURCE, fname)
    if not os.path.exists(p):
        return []
    with open(p, encoding="utf-8") as f:
        txt = f.read()
    out = []
    for m in re.finditer(r"<h4[^>]*>(.*?)</h4>", txt, flags=re.S):
        label = re.sub(r"<[^>]+>", "", m.group(1))
        label = re.sub(r"\s+", " ", label).strip()
        mm = re.match(r"(\d+\.\d+\.\d+)", label)
        if mm:
            out.append((mm.group(1), label))
    return out


def inject_placeholders(html):
    """把正文中的 {{D:key}} 占位符替换为 data/injected.json 中的真实值。"""
    data = load_json(os.path.join(DATA_DIR, "injected.json"), {}) or {}
    missing = []

    def rep(m):
        key = m.group(1).strip()
        v = data.get(key)
        if v is None or v == "":
            missing.append(key)
            return f'<span class="todo-data">〔待填 {key}〕</span>'
        return str(v)

    out = re.sub(r"\{\{D:([^}]+)\}\}", rep, html)
    if missing:
        uniq = sorted(set(missing))
        print(f"  [data] {len(uniq)} 个占位符待填：{', '.join(uniq[:8])}{' …' if len(uniq) > 8 else ''}")
    return out


# ----------------------------------------------------------------- 结构部件
def build_cover():
    p = os.path.join(HERE, "assets", "svg", "cover.svg")
    if not os.path.exists(p):
        return ""
    with open(p, encoding="utf-8") as f:
        svg = f.read()
    return f'<div class="cover-page">{svg}</div>'


def _attr(s):
    """安全地放入 HTML 属性的文本。"""
    return (s or "").replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;")


# --- abstract page (injected) ---
def build_title_page(book):
    """扉页。刻意不用 h1/h2，避免污染 PDF 书签层级。"""
    today = book.get("date") or datetime.date.today().isoformat()
    ab = book.get("abstract", "")
    ab_html = (f'<div class="abstract"><span class="abt">内容提要</span>　{ab}'
               + (f'<div class="kw"><b>关键词：</b>{book["keywords"]}</div>' if book.get("keywords") else "")
               + "</div>") if ab else ""
    return f"""<div class="title-page">
<div class="book-title">{book.get('title','')}</div>
<div class="book-subtitle">{book.get('subtitle','')}</div>
<div class="author">{book.get('author','')}</div>
<div class="aff">{book.get('email','')}　·　学术专著　·　{today}</div>
</div>
"""


def build_abstract_page(book):
    """内容提要与关键词独立成页（扉页只留书名，避免溢出产生空白页）。"""
    ab = book.get("abstract", "")
    if not ab:
        return ""
    kw = (f'<div class="kw"><b>关键词：</b>{book["keywords"]}</div>'
          if book.get("keywords") else "")
    return f'<div class="abstract-page"><div class="abstract"><span class="abt">内容提要</span>　{ab}{kw}</div></div>'



# --- folio support (injected) ---
_PM_PATH = os.path.join(OUTPUT, ".pagemap.json")
_CN_NUM = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6,
           "七": 7, "八": 8, "九": 9, "十": 10}


def load_pagemap():
    return load_json(_PM_PATH, {}) or {}


def _toc_key(text):
    t = re.sub(r"<[^>]+>", "", text or "").strip()
    m = re.search(r"第\s*(\d+)\s*章", t)
    if m:
        return "ch:" + m.group(1)
    m = re.match(r"^(\d+\.\d+\.\d+)", t)
    if m:
        return "sec:" + m.group(1)
    m = re.match(r"^(\d+\.\d+[a-z]?)", t)
    if m:
        return "sec:" + m.group(1)
    m = re.search(r"第\s*([一二三四五六七八九十]+)\s*部分", t)
    if m:
        return "part:" + str(_CN_NUM.get(m.group(1), 0))
    return "txt:" + re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]", "", t)[:10]


def _with_folios(html, pagemap):
    """给目录行右侧补页码。pagemap: {key: page}"""
    if not pagemap:
        return html

    def rep(m):
        head, inner = m.group(1), m.group(2)
        page = pagemap.get(_toc_key(inner))
        if not page:
            page = pagemap.get("pfx:" + re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]", "", re.sub("<[^>]+>", "", inner))[:8])
        if not page:
            return m.group(0)
        return f'{head}{inner}<span class="folio">{page}</span></div>'

    return re.sub(r'(<div class="l[1-4][^"]*">)(.*?)</div>', rep, html, flags=re.S)


def read_toc_map(pdf_path):
    """从 PDF 书签读出 {key: 页码}。页码为物理页（封面=1）。"""
    try:
        import pymupdf
    except Exception:
        try:
            import fitz as pymupdf
        except Exception:
            return {}
    out, seen = {}, {}
    try:
        doc = pymupdf.open(pdf_path)
        toc = doc.get_toc(simple=True)
        for _lvl, title, _page in toc:
            k = _toc_key(title)
            seen[k] = seen.get(k, 0) + 1
        for _lvl, title, page in toc:
            k = _toc_key(title)
            if page and seen.get(k) == 1:
                out[k] = page
                out["pfx:" + re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]", "", re.sub("<[^>]+>", "", title))[:8]] = page
        doc.close()
    except Exception as e:
        print("  [folio] 读取书签失败：", e)
    return out


def stamp_folios(pdf_path):
    """页脚页码 + 页眉章名（章名由 PDF 书签推出；封面、扉页、部分页不盖章）。"""
    try:
        import pymupdf
    except Exception:
        try:
            import fitz as pymupdf
        except Exception:
            print("  [folio] 无 PyMuPDF，跳过页码")
            return
    try:
        doc = pymupdf.open(pdf_path)
        n = len(doc)
        # 书签 → (起始页, 层级, 标题)；用于页眉
        toc = []
        try:
            toc = [(p, lvl, t) for lvl, t, p in doc.get_toc()]
        except Exception:
            toc = []
        chapters = [(p, t) for p, lvl, t in toc if re.search(r"第\s*\d+\s*章", t or "")]
        first_ch = min([p for p, _ in chapters], default=2)
        for i in range(1, n):                      # 第 1 页是封面，不盖
            page = doc[i]
            w, h = page.rect.width, page.rect.height
            cx = w / 2.0
            y = h - 26
            page.draw_line(pymupdf.Point(cx - 16, y - 11),
                           pymupdf.Point(cx + 16, y - 11),
                           color=(0.72, 0.72, 0.72), width=0.4)
            page.insert_text((cx - 3.2 * len(str(i + 1)), y), str(i + 1),
                             fontsize=8.5, fontname="helv",
                             color=(0.32, 0.32, 0.32))
            # 页眉：只在正文章内盖（扉页、部分页、目录不盖）
            if chapters and (i + 1) >= first_ch:
                cur = None
                for p, lvl, t in toc:
                    if p > i + 1:
                        break
                    if re.search(r"第\s*\d+\s*章", t or ""):
                        cur = t
                # 扉页、部分页、章前扉页不盖页眉：一是书签正好压在本页且不是章，
                # 二是本页正文太短（扉页只有章题、题记与结构，通常 < 260 字）
                here = [(lvl, t) for p, lvl, t in toc if p == i + 1]
                fp_here = any(lvl == 1 and not re.search(r"第\s*\d+\s*章", t or "") for lvl, t in here)
                short = len(page.get_text("text").strip()) < 260
                # 章首页：本页有超大字号且带“章”字（章标题已在正文中），页眉重复，不盖
                big_title = False
                try:
                    for blk in page.get_text("dict")["blocks"]:
                        for line in blk.get("lines", []):
                            for sp in line.get("spans", []):
                                if sp.get("size", 0) > 16 and "章" in (sp.get("text") or ""):
                                    big_title = True
                except Exception:
                    pass
                if cur and not fp_here and not short and not big_title:
                    ttl = re.sub(r"\s+", " ", cur).strip()[:34]
                    page.insert_text((w - 85 - 7.4 * len(ttl), 40), ttl,
                                     fontsize=7.6, fontname="china-s",
                                     color=(0.45, 0.45, 0.45))
                    page.draw_line(pymupdf.Point(85, 47), pymupdf.Point(w - 85, 47),
                                   color=(0.85, 0.85, 0.85), width=0.35)
        doc.saveIncr()
        doc.close()
        print(f"  [folio] 已给 {n - 1} 页盖页码（章内页另盖页眉）")
    except Exception as e:
        print("  [folio] 盖章失败：", e)

def build_toc(parts, pagemap=None):
    """带分级（部分／章／节）内部链接的目录。"""
    rows = ['<div class="toc-title">目　录</div>', '<div class="toc">']
    # 前置部分：按 FRONT 顺序列出
    for title, fname, anchor in FRONT:
        if os.path.exists(os.path.join(SOURCE, fname)):
            rows.append(f'<div class="l2"><a href="#{anchor}">{title}</a></div>')
    for part in parts:
        rows.append(f'<div class="l1">{part["part"]}</div>')
        for ch in part.get("chapters", []):
            anchor = f'ch{ch["no"]}'
            if ch.get("written") and ch.get("file"):
                rows.append(f'<div class="l2 done"><a href="#{anchor}">第{ch["no"]}章　{ch["title"]}</a></div>')
            else:
                rows.append(f'<div class="l2 todo">第{ch["no"]}章　{ch["title"]}（待写）</div>')
            subs = numbered_subsections(ch["file"]) if ch.get("file") else []
            used = set()
            for sec in ch.get("sections", []):
                mm = re.match(r"\s*(\d+)\.(\d+)", sec)
                if mm:
                    sid = f'sec{mm.group(1)}-{mm.group(2)}'
                    rows.append(f'<div class="l3"><a href="#{sid}">{sec}</a></div>')
                    prefix = f"{mm.group(1)}.{mm.group(2)}."
                    for num, label in subs:
                        if num.startswith(prefix) and num not in used:
                            used.add(num)
                            rows.append(f'<div class="l4"><a href="#sec{num.replace(".", "-")}">'
                                        f'{label}</a></div>')
                else:
                    rows.append(f'<div class="l3">{sec}</div>')
            for num, label in subs:
                if num not in used:
                    rows.append(f'<div class="l4"><a href="#sec{num.replace(".", "-")}">{label}</a></div>')
    rows.append('<div class="l1">结语与附录</div>')
    for title, fname, anchor in BACK:
        if os.path.exists(os.path.join(SOURCE, fname)):
            rows.append(f'<div class="l2"><a href="#{anchor}">{title}</a></div>')
    rows.append("</div>")
    rows.append('<div class="pb"></div>')
    return _with_folios("\n".join(rows), pagemap)


def build_copyright(book=None):
    p = os.path.join(SOURCE, "front_copyright.html")
    if not os.path.exists(p):
        return ""
    with open(p, encoding="utf-8") as f:
        html = f.read()
    # 版次日期取自单一来源 book.json（真实完成日期）
    date = (book or {}).get("date", "")
    html = html.replace("{{BOOK_DATE}}", date)
    return f'<div class="copyright-page">{html}</div>'



def _part_para(text):
    """部分导语/小结正文：按空行拆段，逐段包 <p>。"""
    text = (text or "").strip()
    if not text:
        return ""
    out = []
    for seg in re.split(r"\n\s*\n", text):
        seg = " ".join(seg.split())
        if seg:
            out.append(f"<p>{seg}</p>")
    return "\n".join(out)


def build_part_page(part, idx=1, total=1):
    """部分扉页：满版插图 + 序号 + 导语（spec v2 §1）。

    图形在 assets/svg/part-NN.svg（暗色渐变、金线母题），文字在 HTML 里（可选中、可检索）。
    """
    title = __import__("re").sub(r"^第[一二三四五六七八九十]+部分[　 ]*", "", part["part"])
    intro = part.get("intro") or part.get("desc") or ""
    return (f'<div class="part-page">'
            f'<div class="part-body">'
            f'<div class="part-big">{idx:02d}</div>'
            f'<div class="part-kicker">PART {idx:02d} / {total:02d}</div>'
            f'<h1 class="part-title">{title}</h1>'
            f'</div></div>'
            f'<div class="part-intro-page">'
            f'<div class="part-intro">{_part_para(intro)}</div>'
            f'</div>')




def build_chapter_opener(ch):
    """章前扉页：章号、题记（取自本章开篇场景）、本章结构。"""
    f = os.path.join(SOURCE, ch.get("file", ""))
    if not os.path.exists(f):
        return ""
    raw = open(f, encoding="utf-8").read()
    import re as _re
    m = _re.search(r'<p class="lead"[^>]*>(.*?)</p>', raw, _re.S)
    quote = ""
    if m:
        t = _re.sub(r"<[^>]+>", "", m.group(1)).strip()
        # 取带 <b> 的那一句；没有就取开头
        b = _re.search(r"<b>(.*?)</b>", m.group(1), _re.S)
        if b:
            quote = _re.sub(r"<[^>]+>", "", b.group(1)).strip().strip('“”" ')
            if quote.endswith(("：", ":")):
                rest = t.split(quote, 1)[-1].strip()
                if rest:
                    quote = rest
        else:
            quote = t.split("。")[0] + "。"
    if len(quote) > 90:
        quote = quote[:88] + "……"
    secs = [x for x in ch.get("sections", []) if not x.startswith(str(ch.get("no")) + "　") or True]
    secs = [x for x in secs if "本章文献" not in x and "参考文献" not in x]
    items = "".join(f"<li>{x}</li>" for x in secs)
    return (f'<div class="chapter-opener">'
            f'<div class="co-kicker">CHAPTER {int(ch["no"]):02d}</div>'
            f'<div class="co-num">{ch["no"]}</div>'
            f'<div class="co-title">{ch["title"]}</div>'
            f'<div class="co-quote">“{quote}”</div>'
            f'<div class="co-map"><span>本章结构</span><ul>{items}</ul></div>'
            f'</div>')

def build_part_summary(part):
    """部分小结：最硬的一条、它依赖的假设、下一部分为什么从这里开始。"""
    sm = part.get("summary") or ""
    if not sm.strip():
        return ""
    return (f'<div class="part-summary"><span class="bt">本部分小结</span>'
            f'{_part_para(sm)}</div>')


# --- index support (injected) ---
_IX_PATH = os.path.join(OUTPUT, ".indexmap.json")


def load_terms():
    """从各书的术语装置取词条（能复用就复用，不另建词表）。

    三种形态都认：
      1) 表头首列为“术语／中文”的表（capacity、entropy、知识、mind-forks、诠释、涌现）；
      2) 定义块 <div class="define"><span class="bt">术语</span>（选择的代价）；
      3) 上面都没有时，退回 front_terms.html 的表。
    """
    cands = ["back_glossary.html", "appendix_d.html", "appendix_a.html", "appendix_b.html", "front_terms.html"]
    terms, seen = [], set()

    def push(t):
        t = re.sub(r"<[^>]+>", "", t)
        t = re.sub(r"\s+", " ", t).strip(" 　·、—（）()")
        if len(t) < 2 or len(t) > 24 or t in seen or t.startswith("["):
            return
        if re.fullmatch(r"[\W_]+", t):
            return
        seen.add(t)
        terms.append(t)

    for fn in cands:
        f = os.path.join(SOURCE, fn)
        if not os.path.exists(f):
            continue
        raw = open(f, encoding="utf-8").read()
        for tbl in re.findall(r"<table\b.*?</table>", raw, re.S):
            rows = re.findall(r"<tr[^>]*>(.*?)</tr>", tbl, re.S)
            if not rows:
                continue
            head = re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", rows[0], re.S)
            if not head:
                continue
            h0 = re.sub(r"<[^>]+>", "", head[0])
            if any(k in h0 for k in ("术语", "中文", "词", "概念", "项", "条目", "名称")):
                for r in rows[1:]:
                    cells = re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", r, re.S)
                    if cells:
                        push(cells[0])
                if terms:
                    return terms
        for m in re.finditer(r'<div class="define"><span class="bt">(.*?)</span>', raw, re.S):
            push(m.group(1))
        if terms:
            return terms
    return terms


def compute_indexmap(pdf_path, max_hits=6):
    """在已生成的 PDF 里检索术语，记录页码（跳过正文之前的页）。"""
    try:
        import pymupdf
    except Exception:
        try:
            import fitz as pymupdf
        except Exception:
            return {}
    terms = load_terms()
    if not terms:
        return {}
    doc = pymupdf.open(pdf_path)
    first = 2
    try:
        for lvl, t, p in doc.get_toc():
            if re.search(r"第\s*\d+\s*章", t or ""):
                first = p
                break
    except Exception:
        pass
    last = len(doc) + 1
    out = {}
    for t in terms:
        pages = []
        for i in range(first - 1, max(first, last - 1)):
            try:
                if doc[i].search_for(t):
                    pages.append(i + 1)
            except Exception:
                continue
            if len(pages) >= max_hits:
                break
        if pages:
            out[t] = pages
    doc.close()
    return out


def build_index(indexmap):
    if not indexmap:
        return ""
    items = []
    for t in sorted(indexmap, key=lambda x: (x[0].lower(), x)):
        shown = "、".join(str(p) for p in indexmap[t])
        items.append(f'<p class="ix"><b>{t}</b>　{shown}</p>')
    return ('<div id="index" style="break-before:page;">'
            '<h1 class="part-title">索引</h1>'
            '<p class="lead">词条取自术语表（附录 G），页码为印刷版页码；每条最多列六处，'
            '不列全书出现次数。</p>'
            '<div style="column-count:2;column-gap:8mm;font-size:0.86em;line-height:1.5;">'
            + "".join(items) + '</div></div>')


def build(book, parts, ereader=False, pagemap=None, indexmap=None):
    blocks = [build_cover(), build_title_page(book), build_copyright(book),
              build_abstract_page(book), build_toc(parts, pagemap)]
    for title, fname, anchor in FRONT:
        f = os.path.join(SOURCE, fname)
        if os.path.exists(f):
            with open(f, encoding="utf-8") as fh:
                blocks.append(f'<div id="{anchor}">{fh.read()}</div>')
    written = []
    for pi, part in enumerate(parts, 1):
        if not any(c.get("written") and c.get("file") for c in part.get("chapters", [])):
            continue
        blocks.append(build_part_page(part, pi, len(parts)))
        for ch in part.get("chapters", []):
            if ch.get("written") and ch.get("file"):
                f = os.path.join(SOURCE, ch["file"])
                if os.path.exists(f):
                    with open(f, encoding="utf-8") as fh:
                        body = fh.read()
                    blocks.append(build_chapter_opener(ch))
                    blocks.append(f'<div id="ch{ch["no"]}">{body}</div>')
                    written.append(ch["no"])
        blocks.append(build_part_summary(part))
    if any(os.path.exists(os.path.join(SOURCE, f)) for _, f, _ in BACK):
        blocks.append('<h1 class="part-title">结语与附录</h1>')
    _seen_back = set()
    for title, fname, anchor in BACK:
        f = os.path.join(SOURCE, fname)
        if os.path.exists(f) and fname not in _seen_back:
            _seen_back.add(fname)
            with open(f, encoding="utf-8") as fh:
                blocks.append(f'<div id="{anchor}">{fh.read()}</div>')

    if not ereader and indexmap:
        blocks.append(build_index(indexmap))
    body = "\n".join(blocks)
    body = annotate_headings(inline_images(body))
    body = inject_placeholders(body)

    with open(os.path.join(CSS_DIR, "paper.css"), encoding="utf-8") as f:
        css = f.read()
    with open(os.path.join(CSS_DIR, "book.css"), encoding="utf-8") as f:
        book_css = re.sub(r'@import url\("paper.css"\);\s*', "", f.read())
    css += "\n" + book_css
    if ereader:
        with open(os.path.join(CSS_DIR, "ereader.css"), encoding="utf-8") as f:
            css += "\n" + f.read()
    # 删除 CSS 注释：开发者注释可能含版次字样，不得进入读者可见的 HTML/PDF/EPUB
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)

    html = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="author" content="{_attr(book.get('author',''))}">
<meta name="description" content="{_attr(book.get('abstract','')[:300])}">
<meta name="keywords" content="{_attr(book.get('keywords',''))}">
<meta name="license" content="{_attr(book.get('license',''))}">
<meta name="date" content="{_attr(book.get('date',''))}">
<title>{book.get('title','')}</title>
<style>
{css}
</style></head>
<body>
{body}
</body></html>
"""
    os.makedirs(OUTPUT, exist_ok=True)
    out = os.path.join(OUTPUT, "book-ereader.html" if ereader else "book.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"wrote {out} ({len(html)} bytes); chapters written: {written}")
    return out


def _to_winpath(p):
    if len(p) > 1 and p[1] == ":":        # 已是 Windows 路径
        return p.replace("/", "\\")
    if p.startswith("/mnt/") and len(p) > 6 and p[6] == "/":
        drive = p[5].upper()
        return drive + ":" + p[6:].replace("/", "\\")
    return p


CHROME_CANDS_WIN = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]
CHROME_CANDS_NIX = [
    "/mnt/c/Program Files/Google/Chrome/Application/chrome.exe",
    "/mnt/c/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",
    "/usr/bin/google-chrome", "/usr/bin/chromium", "/usr/bin/chromium-browser",
]


def dedupe_pdf_outline(path):
    """修复 Chrome ``--generate-pdf-document-outline`` 的已知瑕疵：
    当书签标题紧跟在其它分页元素之后时，Chrome 会把标题文本重复一遍
    （“第1章…第1章…”）。此处对完全自重复的 /Title 做一次折半。
    """
    try:
        import pypdf
        from pypdf.generic import NameObject, TextStringObject
    except Exception as e:  # pypdf 可选
        print("  [outline] 未安装 pypdf，跳过书签去重：", e)
        return
    try:
        writer = pypdf.PdfWriter(clone_from=path)
        fixed = [0]

        def fix(node):
            cur = node
            while cur is not None:
                obj = cur.get_object() if hasattr(cur, "get_object") else cur
                t = obj.get("/Title")
                if t is not None:
                    s = str(t)
                    L = len(s)
                    if L % 2 == 0 and s[: L // 2] == s[L // 2:]:
                        obj[NameObject("/Title")] = TextStringObject(s[: L // 2])
                        fixed[0] += 1
                    else:
                        # Chrome 还会产生“首份被截断 + 次份完整”的重复：
                        # 形如“…与制度第 4 章…与制度失效”。取第二个章前缀之后的完整份。
                        import re as _re
                        m = _re.search(r"第\s*\d+\s*章\s*", s)
                        if m:
                            second = s.find(m.group(0), m.end())
                            if second > 0:
                                tail = s[second:]
                                if len(tail) >= len(m.group(0)) + 1:
                                    obj[NameObject("/Title")] = TextStringObject(tail)
                                    fixed[0] += 1
                f = obj.get("/First")
                if f is not None:
                    fix(f)
                cur = obj.get("/Next")

        ol = writer._root_object.get("/Outlines")
        if ol is not None:
            ol = ol.get_object() if hasattr(ol, "get_object") else ol
            first = ol.get("/First")
            if first is not None:
                fix(first)
        if fixed[0]:
            with open(path, "wb") as fh:
                writer.write(fh)
            print(f"  [outline] 已修正 {fixed[0]} 个重复书签标题")
    except Exception as e:
        print("  [outline] 去重失败（不影响正文）：", e)


def print_pdf(html_path):
    """用无头 Chrome/Edge 把 HTML 打印为 PDF（含分级书签）。"""
    import subprocess
    cands = CHROME_CANDS_WIN if os.name == "nt" else CHROME_CANDS_NIX
    browser = next((c for c in cands if os.path.exists(c)), None)
    if not browser:
        print("未找到 Chrome/Edge；请手动用浏览器打印：", html_path)
        return
    out_pdf = os.path.join(OUTPUT, os.path.basename(html_path).replace(".html", ".pdf"))
    if os.name == "nt":
        uri = "file:///" + html_path.replace("\\", "/")
        out_arg = out_pdf
    elif browser.startswith("/mnt/"):
        uri = "file:///" + _to_winpath(html_path).replace("\\", "/")
        out_arg = _to_winpath(out_pdf)
    else:
        uri = "file://" + html_path
        out_arg = out_pdf
    subprocess.run([browser, "--headless=new", "--disable-gpu", "--no-sandbox",
                    "--no-pdf-header-footer", "--generate-pdf-document-outline",
                    f"--print-to-pdf={out_arg}", uri],
                   check=False)
    print("[pdf]", out_pdf, "(含分级书签)")
    dedupe_pdf_outline(out_pdf)
    set_pdf_metadata(out_pdf)


def set_pdf_metadata(pdf_path):
    """写入 PDF 元数据（标题/作者/主题/关键词），保留分级书签。"""
    try:
        from pypdf import PdfReader, PdfWriter
    except Exception:
        print("  [meta] pypdf 不可用，跳过 PDF 元数据")
        return
    book = load_json(os.path.join(SOURCE, "book.json"), {})
    title = book.get("title", "")
    subtitle = book.get("subtitle", "")
    full_title = f"{title}：{subtitle}" if subtitle else title
    with open(pdf_path, "rb") as fh:
        reader = PdfReader(fh)
        writer = PdfWriter()
        writer.clone_document_from_reader(reader)
        writer.add_metadata({
            "/Title": full_title,
            "/Author": book.get("author", ""),
            "/Subject": "；".join(book.get("subjects", [])) or "脆弱性诊断",
            "/Keywords": book.get("keywords", ""),
            "/Creator": "distinction-evolution (HTML→PDF)",
            "/Producer": "distinction-evolution build_book.py",
        })
    tmp = pdf_path + ".meta"
    with open(tmp, "wb") as fh:
        writer.write(fh)
    os.replace(tmp, pdf_path)
    print("  [meta] 已写入 PDF 元数据（书名/作者/主题/关键词）")


if __name__ == "__main__":
    ereader = "--ereader" in sys.argv
    book = load_json(os.path.join(SOURCE, "book.json"), {})
    parts = load_json(os.path.join(SOURCE, "parts.json"), [])
    pm = {} if ereader else load_pagemap()
    out = build(book, parts, ereader=ereader, pagemap=pm)
    if "--pdf" in sys.argv:
        print_pdf(out)
        if not ereader:
            pdf = os.path.join(OUTPUT, "book.pdf")
            newpm = read_toc_map(pdf)
            if newpm and newpm != pm:
                with open(_PM_PATH, "w", encoding="utf-8") as fh:
                    json.dump(newpm, fh, ensure_ascii=False, indent=0)
                print(f"  [folio] 目录页码：{len(newpm)} 项，重建一遍")
                out = build(book, parts, ereader=ereader, pagemap=newpm)
                print_pdf(out)
            stamp_folios(pdf)
            # 索引：先检索术语页码，再重建一次（索引追加在书末，不影响前面的页码）
            try:
                ix = compute_indexmap(pdf)
                print(f"  [index] 词条 {len(ix)} 条")
                if ix:
                    with open(_IX_PATH, "w", encoding="utf-8") as fh:
                        json.dump(ix, fh, ensure_ascii=False, indent=0)
                    out = build(book, parts, ereader=ereader,
                                pagemap=newpm if newpm else pm, indexmap=ix)
                    print_pdf(out)
                    stamp_folios(pdf)
            except Exception as _ix_e:
                print("  [index] 跳过：", _ix_e)
    # 目录必须能跳：Chrome 把锚点写成“页面底部”的命名目标，这里改写成 GOTO
    try:
        import importlib.util
        _fp = os.path.join(HERE, "scripts", "fix_pdf_links.py")
        if os.path.exists(_fp):
            _spec = importlib.util.spec_from_file_location("fix_pdf_links", _fp)
            _mod = importlib.util.module_from_spec(_spec)
            _spec.loader.exec_module(_mod)
            _mod.fix(os.path.join(OUTPUT, "book-ereader.pdf" if ereader else "book.pdf"))
    except Exception as _e:
        print("  [links] 修复失败：", _e)
