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

FRONT = [("先读这一页　三个可复算的定理", "front_hardcore.html", "hardcore"),
         ("两个框架：五种代数（骨架）与四种机制（兑现方式）", "front_two_frameworks.html", "twoframeworks"),
         ("前言　为什么把“统一”降级为“可检验的操作”", "front_preface.html", "preface"),
         ("十分钟读懂本书", "front_quickstart.html", "quickstart"),
         ("阅读合约　本书向你承诺什么，又不承诺什么", "front_theorymap.html", "theorymap"),
         ("术语、记号与断言分级速查", "front_terms.html", "terms")]
BACK = [("结语　一份开放的邀请", "back_epilogue.html", "epilogue"),
        ("附录 A　数学补充：谱、线性方程与相变", "appendix_a_math.html", "apxA"),
        ("附录 B　领域编码总表", "appendix_b_map.html", "apxB"),
        ("附录 C　参考文献", "appendix_c_references.html", "apxC"),
        ("附录 D　术语表", "appendix_d_glossary.html", "apxD"),
        ("附录 E　可证伪登记簿", "appendix_e_preregistration.html", "apxE"),
        ("附录 F　证据与数据缺口清单", "appendix_f_datagaps.html", "apxF"),
        ("附录 G　研究纲领与工具包", "appendix_g_toolkit.html", "apxG"),
        ("附录 H　形式化路线图：从 sorry 到编译", "appendix_h_formalization.html", "apxH"),
        ("附录 I　工程验证记录：可运行的实验与失败", "appendix_i_engineering.html", "apxI"),
        ("附录 J　硬核扩展：加权、有向与离散曲率（含证明）", "appendix_j_hardcore.html", "apxJ"),
        ("附录 K　登记但未展开的猜想：计算与学习", "appendix_k_conjectures.html", "apxK"),
        ("附录 L　与其他基础框架的比较", "appendix_l_comparison.html", "apxL")]


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
{ab_html}
</div>
<div class="pb"></div>
"""


def build_toc(parts):
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
    return "\n".join(rows)


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


def build(book, parts, ereader=False):
    blocks = [build_cover(), build_title_page(book), build_copyright(book), build_toc(parts)]
    for title, fname, anchor in FRONT:
        f = os.path.join(SOURCE, fname)
        if os.path.exists(f):
            with open(f, encoding="utf-8") as fh:
                blocks.append(f'<div id="{anchor}">{fh.read()}</div>')
    written = []
    for part in parts:
        n_before = len(blocks)
        for ch in part.get("chapters", []):
            if ch.get("written") and ch.get("file"):
                f = os.path.join(SOURCE, ch["file"])
                if os.path.exists(f):
                    if len(blocks) == n_before:  # 部分扉页只加一次
                        blocks.append(f'<h1 class="part-title">{part["part"]}</h1>')
                    with open(f, encoding="utf-8") as fh:
                        body = fh.read()
                    blocks.append(f'<div id="ch{ch["no"]}">{body}</div>')
                    written.append(ch["no"])
    if any(os.path.exists(os.path.join(SOURCE, f)) for _, f, _ in BACK):
        blocks.append('<h1 class="part-title">结语与附录</h1>')
    for title, fname, anchor in BACK:
        f = os.path.join(SOURCE, fname)
        if os.path.exists(f):
            with open(f, encoding="utf-8") as fh:
                blocks.append(f'<div id="{anchor}">{fh.read()}</div>')

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
    out = build(book, parts, ereader=ereader)
    if "--pdf" in sys.argv:
        print_pdf(out)
