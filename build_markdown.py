# -*- coding: utf-8 -*-
"""
build_markdown.py — 把 source/ 下的 HTML 书稿导出为 Markdown。

设计要点
--------
* 与 build_book.py / build_epub.py 共用同一份源文件与顺序（FRONT + parts.json + BACK），
  因此 Markdown 版不会与 PDF/EPUB 版“漂移”。
* 复用注入逻辑（{{D:key}} → data/injected.json）与版次日期（{{BOOK_DATE}}）。
* 自定义块转换为可读的 Markdown：
    - 定义 / 警告 / 案例 / 情景 / 说明 → 引用块（> **标签**）
    - 表格 → GFM 表格（含表题）
    - 公式 → 引用行（含编号）
    - 图 → ![alt](assets/...)，并复制图片到输出目录，保持自包含
* 输出：
    output/markdown/book.md        合并全书（部分 → 章 → 节）
    output/markdown/00_*.md …      逐文件（开篇/前言/理论地图/…/ch01…/附录）
    output/markdown/assets/…       被引用的图片

用法
----
    python build_markdown.py
"""
import os
import re
import shutil

from bs4 import BeautifulSoup, NavigableString, Tag

from build_book import (HERE, SOURCE, OUTPUT, FRONT, BACK,
                        load_json, inject_placeholders)

MD_DIR = os.path.join(OUTPUT, "markdown")
ASSETS_DIR = os.path.join(MD_DIR, "assets")

CALLOUT_LABEL = {"define": "定义", "warning": "警告", "case": "案例",
                 "scenario": "情景", "note": "说明"}
CALLOUT_ICON = {"warning": "⚠️ ", "note": "📝 "}


# ------------------------------------------------------------------ 内联转换
def inline(node) -> str:
    """把内联标签转换为 Markdown（保留 sub/sup 为 HTML）。"""
    if isinstance(node, NavigableString):
        return str(node)
    if not isinstance(node, Tag):
        return ""
    name = node.name.lower()
    if name == "br":
        return "  \n"
    if name == "img":
        return f'![{node.get("alt", "")}]({node.get("src", "")})'
    inner = "".join(inline(c) for c in node.children)
    if name in ("b", "strong"):
        return f"**{inner.strip()}**" if inner.strip() else inner
    if name in ("i", "em"):
        return f"*{inner.strip()}*" if inner.strip() else inner
    if name == "code":
        return f"`{inner}`"
    if name == "a":
        href = node.get("href", "")
        return f"[{inner}]({href})" if href else inner
    if name in ("sub", "sup"):
        return f"<{name}>{inner}</{name}>"
    return inner


def inline_nodes(nodes) -> str:
    return "".join(inline(n) for n in nodes)


_INLINE_TAGS = {"b", "strong", "i", "em", "code", "a", "sub", "sup", "span", "br"}


def is_inline(el) -> bool:
    if isinstance(el, NavigableString):
        return True
    if isinstance(el, Tag):
        return el.name.lower() in _INLINE_TAGS
    return False


def _one_line(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def cell_md(node) -> str:
    return _one_line(inline(node)).replace("|", "\\|")


# ------------------------------------------------------------------ 表格
def table_md(tbl: Tag) -> str:
    out = []
    cap = tbl.find("caption")
    if cap:
        capt = _one_line(inline(cap))
        if not (capt.startswith("**") and capt.endswith("**")):
            capt = "**" + capt + "**"
        out.append(capt)
        out.append("")
    header, body = None, []
    for tr in tbl.find_all("tr"):
        ths = tr.find_all("th", recursive=False)
        tds = tr.find_all("td", recursive=False)
        if ths:
            cells = [cell_md(c) for c in ths]
            if header is None:
                header = cells
            else:
                body.append(cells)
        elif tds:
            body.append([cell_md(c) for c in tds])
    ncol = max([len(header) if header else 0] + [len(r) for r in body] + [1])
    if header is None:
        header = [""] * ncol
    header = header + [""] * (ncol - len(header))
    out.append("| " + " | ".join(header) + " |")
    out.append("|" + "---|" * ncol)
    for r in body:
        r = r + [""] * (ncol - len(r))
        out.append("| " + " | ".join(r) + " |")
    return "\n".join(out)


# ------------------------------------------------------------------ 列表项
def render_li(li: Tag, chap_level: int) -> str:
    parts = []
    for child in li.children:
        if isinstance(child, Tag) and child.name in ("p", "ul", "ol", "div", "table"):
            parts.append(block(child, chap_level))
        else:
            parts.append(inline(child))
    txt = "".join(parts).strip()
    lines = txt.splitlines()
    return ("\n  ").join(lines) if len(lines) > 1 else txt


# ------------------------------------------------------------------ 引用块
def callout(el: Tag, chap_level: int, cls: set) -> str:
    if "case" in cls:
        label_el = el.find(class_="ct")
    else:
        label_el = el.find("span", class_="bt")
    label = _one_line(inline(label_el)) if label_el else ""
    if label_el:
        label_el.extract()
    if not label:
        key = next((k for k in CALLOUT_LABEL if k in cls), "")
        label = CALLOUT_LABEL.get(key, "")
        label = CALLOUT_ICON.get(key, "") + label
    inner = block(el, chap_level)
    lines = []
    if label:
        lines.append("> **" + label + "**")
    if inner:
        if lines:
            lines.append(">")
        lines += ["> " + ln for ln in inner.splitlines()]
    return "\n".join(lines)


# ------------------------------------------------------------------ 块级
def block(container, chap_level: int = 1) -> str:
    out = []
    buf = []  # 连续的“内联级”节点，如定义/警告块内未包裹的文本与 <b>/<span>

    def flush():
        if buf:
            txt = _one_line(inline_nodes(buf))
            if txt:
                out.append(txt)
            buf.clear()

    for el in container.children:
        if is_inline(el):
            buf.append(el)
            continue
        flush()
        if not isinstance(el, Tag):
            continue
        name = el.name.lower()
        cls = set(el.get("class") or [])

        if name in ("h1", "h2", "h3", "h4", "h5", "h6"):
            lvl = {"h1": chap_level - 1, "h2": chap_level, "h3": chap_level + 1,
                   "h4": chap_level + 2, "h5": chap_level + 3, "h6": chap_level + 4}[name]
            out.append("#" * max(1, lvl) + " " + _one_line(inline(el)))
        elif name == "p":
            txt = inline(el).strip()
            if txt:
                out.append(txt)
        elif name in ("ul", "ol"):
            items = []
            for i, li in enumerate(el.find_all("li", recursive=False), 1):
                prefix = "- " if name == "ul" else f"{i}. "
                items.append(prefix + render_li(li, chap_level))
            out.append("\n".join(items))
        elif name == "blockquote":
            inner = block(el, chap_level)
            out.append("\n".join("> " + ln for ln in inner.splitlines()))
        elif name == "table":
            out.append(table_md(el))
        elif name == "img":
            out.append(f'![{el.get("alt", "")}]({el.get("src", "")})')
        elif name == "hr":
            out.append("---")
        elif name == "div":
            if "eq" in cls:
                body = el.find(class_="body")
                num = el.find(class_="num")
                line = _one_line(inline(body)) if body else ""
                if num:
                    line += "　　" + _one_line(inline(num))
                out.append("> " + line)
            elif "cap" in cls:
                # 图注：标签本身已含 <b>，不再额外包斜体，避免 ***…*** 畸形强调
                out.append(_one_line(inline(el)))
            elif cls & set(CALLOUT_LABEL):
                out.append(callout(el, chap_level, cls))
            elif "datasrc" in cls:
                out.append("> " + _one_line(inline(el)))
            else:  # refs 及未知容器
                inner = block(el, chap_level)
                if inner:
                    out.append(inner)
        else:
            inner = block(el, chap_level)
            if inner:
                out.append(inner)
    flush()
    return "\n\n".join(x for x in out if x and x.strip())


def html_to_md(html: str, chap_level: int = 1) -> str:
    soup = BeautifulSoup(html, "html.parser")
    md = block(soup, chap_level)
    md = re.sub(r"\n{3,}", "\n\n", md)
    return md.strip() + "\n"


# ------------------------------------------------------------------ 图片复制
def collect_assets(html: str) -> set:
    return set(re.findall(r'src="(assets/[^"]+)"', html))


def copy_assets(srcs: set):
    for s in sorted(srcs):
        src = os.path.join(HERE, s)
        dst = os.path.join(MD_DIR, s)
        if os.path.exists(src):
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)


# ------------------------------------------------------------------ 组装
def build_title_md(book: dict) -> str:
    lines = [f"# {book.get('title','')}", ""]
    if book.get("subtitle"):
        lines += [f"## {book['subtitle']}", ""]
    lines += [f"**作者：**{book.get('author','')}　·　{book.get('date','')}",
              f"**许可：**{book.get('license','')}", ""]
    if book.get("abstract"):
        lines += ["> **内容提要**", ">",
                  "\n".join("> " + ln for ln in _wrap(book["abstract"]).splitlines()), ""]
    if book.get("keywords"):
        lines += [f"**关键词：**{book['keywords']}", ""]
    return "\n".join(lines)


def _wrap(text: str, width: int = 1000) -> str:
    return text


def load_section(fname: str, chap_level: int) -> str:
    p = os.path.join(SOURCE, fname)
    if not os.path.exists(p):
        return ""
    with open(p, encoding="utf-8") as f:
        html = f.read()
    html = html.replace("{{BOOK_DATE}}", load_json(os.path.join(SOURCE, "book.json"), {}).get("date", ""))
    html = inject_placeholders(html)
    collect_assets(html)
    return html_to_md(html, chap_level)


def main():
    book = load_json(os.path.join(SOURCE, "book.json"), {})
    parts = load_json(os.path.join(SOURCE, "parts.json"), [])
    os.makedirs(MD_DIR, exist_ok=True)

    # 1) 逐文件导出
    files = []          # (slug, title, md)
    all_assets = set()

    def add(fname, title, anchor, chap_level):
        nonlocal all_assets
        p = os.path.join(SOURCE, fname)
        if not os.path.exists(p):
            return
        with open(p, encoding="utf-8") as f:
            html = f.read()
        html = html.replace("{{BOOK_DATE}}", book.get("date", ""))
        html = inject_placeholders(html)
        all_assets |= collect_assets(html)
        md = html_to_md(html, chap_level)
        files.append((anchor, title, md, fname))

    # 版权页
    for _, fname, anchor in [("版权", "front_copyright.html", "copyright")]:
        add(fname, "版权与数据来源", anchor, 1)
    for title, fname, anchor in FRONT:
        add(fname, title, anchor, 1)
    for part in parts:
        for ch in part.get("chapters", []):
            if ch.get("written") and ch.get("file"):
                add(ch["file"], f"第{ch['no']}章　{ch['title']}", f"ch{ch['no']}", 1)
    for title, fname, anchor in BACK:
        add(fname, title, anchor, 1)

    # 2) 写逐文件
    index = ["# 目录（分文件）", ""]
    used = set()
    for i, (anchor, title, md, fname) in enumerate(files):
        slug = f"{i:02d}_{anchor}"
        path = os.path.join(MD_DIR, slug + ".md")
        with open(path, "w", encoding="utf-8") as f:
            f.write(md)
        index.append(f"- [{title}]({slug}.md)")
        used.add(slug)
    with open(os.path.join(MD_DIR, "README.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(index) + "\n")

    # 3) 合并全书（部分 = #，章 = ##，节 = ###）
    combined = [build_title_md(book), "\n---\n"]
    # 前置（按 FRONT 顺序，含版权、开篇、前言、十分钟、理论地图、术语、执行摘要）
    front_order = ["copyright"] + [a for _, _, a in FRONT]
    for anchor, title, md, fname in files:
        if anchor in front_order:
            combined.append(md.strip() + "\n\n---\n")
    for part in parts:
        combined.append(f"# {part['part']}\n")
        for ch in part.get("chapters", []):
            if not (ch.get("written") and ch.get("file")):
                continue
            with open(os.path.join(SOURCE, ch["file"]), encoding="utf-8") as f:
                html = inject_placeholders(f.read())
            all_assets |= collect_assets(html)
            combined.append(html_to_md(html, chap_level=2).strip() + "\n\n---\n")
    combined.append("# 结语与附录\n")
    for title, fname, anchor in BACK:
        p = os.path.join(SOURCE, fname)
        if os.path.exists(p):
            with open(p, encoding="utf-8") as f:
                html = inject_placeholders(f.read())
            all_assets |= collect_assets(html)
            combined.append(html_to_md(html, chap_level=2).strip() + "\n\n---\n")
    with open(os.path.join(MD_DIR, "book.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(combined).replace("\n\n\n\n", "\n\n\n"))

    # 4) 复制图片
    copy_assets(all_assets)

    total = sum(os.path.getsize(os.path.join(MD_DIR, x))
                for x in os.listdir(MD_DIR) if x.endswith(".md"))
    print(f"wrote {os.path.join(MD_DIR, 'book.md')}")
    print(f"wrote {len(files) + 1} markdown files ({total} bytes), {len(all_assets)} assets copied")


if __name__ == "__main__":
    main()
