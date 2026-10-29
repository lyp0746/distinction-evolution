# -*- coding: utf-8 -*-
"""
build_epub.py — 由 source/ 生成符合 EPUB 3 标准的电子书。

特点
----
* EPUB 3（含 EPUB 2 兼容的 NCX 回退），可被 Kindle / Apple Books / 多看等读取。
* **分级目录**：部分（part）→ 章（chapter）→ 节（section，带锚点），
  在阅读器的目录面板中可逐级跳转。
* 版式沿用第一版字体体系（宋体正文 / 黑体标题），但去掉固定页宽以适应重排。
* 图片以外部 SVG/PNG 打包，保持矢量清晰。

用法
----
    python build_epub.py            # -> output/book.epub
"""
import datetime
import os
import re
import uuid
import zipfile

from lxml import etree, html as lhtml

from build_book import (HERE, SOURCE, CSS_DIR, OUTPUT, FRONT, BACK,
                        annotate_headings, load_json)

EPUB = os.path.join(OUTPUT, "book.epub")
OEBPS = "OEBPS"
UID = "urn:uuid:" + str(uuid.uuid5(uuid.NAMESPACE_URL, "entropy-spiral-book"))


# --------------------------------------------------------------- 工具
def frag_to_xhtml(fragment, title="", body_id=""):
    """把 HTML 片段转成 XHTML 正文（闭合空标签、规范实体）。"""
    fragment = re.sub(r'src="assets/(?:svg|charts)/([^"]+)"', r'src="../images/\1"', fragment)
    div = lhtml.fragment_fromstring(fragment, create_parent="div")
    xml = etree.tostring(div, method="xml", encoding="unicode")
    inner = re.sub(r"^<div[^>]*>", "", xml, count=1)
    inner = re.sub(r"</div>$", "", inner, count=1)
    body_id = f' id="{body_id}"' if body_id else ""
    return (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<!DOCTYPE html>\n'
        '<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="zh-CN" lang="zh-CN">\n'
        f'<head><meta charset="utf-8"/><title>{title}</title>'
        '<link rel="stylesheet" type="text/css" href="../css/book.css"/></head>\n'
        f'<body{body_id}><section>\n{inner}\n</section></body>\n</html>\n'
    )


def epub_css():
    """由印刷样式裁剪出可重排的 EPUB 样式。"""
    css = ""
    for name in ("paper.css", "book.css"):
        with open(os.path.join(CSS_DIR, name), encoding="utf-8") as f:
            t = f.read()
        t = re.sub(r"@import url\([^)]*\);\s*", "", t)
        t = re.sub(r"@page[^{]*\{[^}]*\}", "", t)
        css += t + "\n"
    # 不向 EPUB 写入开发者注释（可能含版次字样）
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    css += "\n/* 重排覆盖 */\nbody{max-width:none;margin:0;padding:0 4%;}\n"
    return css


def collect_images(fragment):
    out = {}
    for m in re.finditer(r'src="assets/(svg|charts)/([^"]+)"', fragment):
        out[m.group(2)] = os.path.join(HERE, "assets", m.group(1), m.group(2))
    return out


# --------------------------------------------------------------- 主体
def build():
    book = load_json(os.path.join(SOURCE, "book.json"), {})
    parts = load_json(os.path.join(SOURCE, "parts.json"), [])

    # 1) 逐文件生成 XHTML
    docs = []                       # (id, href, title, fragment, images)
    images = {}

    def add(fid, fname, title, body_id, is_chapter):
        f = os.path.join(SOURCE, fname)
        if not os.path.exists(f):
            return
        with open(f, encoding="utf-8") as fh:
            frag = fh.read()
        frag = annotate_headings(frag)
        images.update(collect_images(frag))
        href = f"text/{os.path.splitext(fname)[0]}.xhtml"
        docs.append({"id": fid, "href": href, "title": title,
                     "frag": frag, "body_id": body_id, "chapter": is_chapter})

    add("copyright", "front_copyright.html", "版权与数据来源", "copyright", False)
    for title, fname, anchor in FRONT:
        add(anchor, fname, title, anchor, False)
    for part in parts:
        for ch in part.get("chapters", []):
            if ch.get("written") and ch.get("file"):
                add(f"ch{ch['no']}", ch["file"], f"第{ch['no']}章　{ch['title']}",
                    f"ch{ch['no']}", True)
    for title, fname, anchor in BACK:
        add(anchor, fname, title, anchor, False)

    # 2) 封面
    cover_img = None
    cover_src = os.path.join(HERE, "assets", "svg", "cover.svg")
    if os.path.exists(cover_src):
        images["cover.svg"] = cover_src
        cover_img = "cover.svg"
        cover_xhtml = (
            '<?xml version="1.0" encoding="utf-8"?>\n<!DOCTYPE html>\n'
            '<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="zh-CN">\n'
            '<head><meta charset="utf-8"/><title>封面</title>'
            '<style>html,body{margin:0;padding:0;text-align:center}'
            'img{max-width:100%;max-height:100%}</style></head>\n'
            '<body><section><img src="../images/cover.svg" alt="封面"/></section></body></html>\n')

    os.makedirs(OUTPUT, exist_ok=True)
    with zipfile.ZipFile(EPUB, "w") as z:
        # mimetype 必须第一个且不压缩
        zi = zipfile.ZipInfo("mimetype")
        zi.compress_type = zipfile.ZIP_STORED
        z.writestr(zi, "application/epub+zip")

        z.writestr("META-INF/container.xml",
                   '<?xml version="1.0" encoding="utf-8"?>\n'
                   '<container version="1.0" '
                   'xmlns="urn:oasis:names:tc:opendocument:xmlns:container">\n'
                   f'<rootfiles><rootfile full-path="{OEBPS}/content.opf" '
                   'media-type="application/oebps-package+xml"/></rootfiles></container>\n')

        if cover_img:
            z.writestr(f"{OEBPS}/text/cover.xhtml", cover_xhtml)

        for d in docs:
            z.writestr(f"{OEBPS}/{d['href']}",
                       frag_to_xhtml(d["frag"], d["title"], d["body_id"]))

        z.writestr(f"{OEBPS}/css/book.css", epub_css())

        for name, path in images.items():
            with open(path, "rb") as fh:
                z.writestr(f"{OEBPS}/images/{name}", fh.read())

        z.writestr(f"{OEBPS}/nav.xhtml", build_nav(book, parts, docs, cover_img))
        z.writestr(f"{OEBPS}/toc.ncx", build_ncx(book, parts, docs))
        z.writestr(f"{OEBPS}/content.opf", build_opf(book, parts, docs, images, cover_img))

    print(f"wrote {EPUB}")
    return EPUB


def nav_items(parts, docs):
    """返回嵌套目录项：部分 -> 章 -> 节 -> 子节（4 级）。"""
    docmap = {d["id"]: d for d in docs}
    items = []
    for title, fname, anchor in FRONT:
        if anchor in docmap:
            items.append({"title": title,
                          "href": docmap[anchor]["href"], "children": []})
    for part in parts:
        children = []
        for ch in part.get("chapters", []):
            if not (ch.get("written") and ch.get("file")):
                continue
            cid = f"ch{ch['no']}"
            d = docmap.get(cid)
            href = d["href"] if d else ""
            frag = d["frag"] if d else ""
            subs = []
            for m in re.finditer(r'<h4[^>]*>(.*?)</h4>', frag, flags=re.S):
                label = re.sub(r"<[^>]+>", "", m.group(1)).strip()
                mm = re.match(r"(\d+\.\d+\.\d+)", label)
                if mm:
                    subs.append((mm.group(1), label))
            secs = []
            for sec in ch.get("sections", []):
                mm = re.match(r"\s*(\d+)\.(\d+)", sec)
                if not mm:
                    continue
                sid = f"sec{mm.group(1)}-{mm.group(2)}"
                sub_children = [
                    {"title": label, "href": f"{href}#sec{num.replace('.', '-')}"}
                    for num, label in subs if num.startswith(f"{mm.group(1)}.{mm.group(2)}.")
                ]
                secs.append({"title": sec, "href": f"{href}#{sid}",
                             "children": sub_children})
            children.append({"title": f"第{ch['no']}章　{ch['title']}", "href": href,
                             "children": secs})
        items.append({"title": part["part"], "href": children[0]["href"] if children else "",
                      "children": children})
    back = []
    for title, fname, anchor in BACK:
        if anchor in docmap:
            back.append({"title": title, "href": docmap[anchor]["href"], "children": []})
    if back:
        items.append({"title": "结语与附录", "href": back[0]["href"], "children": back})
    return items


def render_nav_ol(items_indent, items):
    pad = "  " * items_indent
    out = [f"{pad}<ol>"]
    for it in items:
        out.append(f'{pad}  <li><a href="{it["href"]}">{esc(it["title"])}</a>')
        if it.get("children"):
            out.append(render_nav_ol(items_indent + 2, it["children"]))
        out.append(f"{pad}  </li>")
    out.append(f"{pad}</ol>")
    return "\n".join(out)


def esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def build_nav(book, parts, docs, cover_img):
    items = nav_items(parts, docs)
    if cover_img:
        items = [{"title": "封面", "href": "text/cover.xhtml", "children": []}] + items
    return (
        '<?xml version="1.0" encoding="utf-8"?>\n<!DOCTYPE html>\n'
        '<html xmlns="http://www.w3.org/1999/xhtml" '
        'xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="zh-CN">\n'
        '<head><meta charset="utf-8"/><title>目录</title>'
        '<link rel="stylesheet" type="text/css" href="css/book.css"/></head>\n'
        '<body><nav epub:type="toc" id="toc"><h1>目录</h1>\n'
        + render_nav_ol(0, items) + "\n</nav></body></html>\n"
    )


def build_ncx(book, parts, docs):
    items = nav_items(parts, docs)
    counter = [0]

    def navpoints(nodes, depth, indent):
        pad = "  " * indent
        out = []
        for it in nodes:
            counter[0] += 1
            out.append(f'{pad}<navPoint id="np{counter[0]}" playOrder="{counter[0]}">')
            out.append(f'{pad}  <navLabel><text>{esc(it["title"])}</text></navLabel>')
            out.append(f'{pad}  <content src="{it["href"]}"/>')
            if it.get("children"):
                out.append("\n".join(navpoints(it["children"], depth + 1, indent + 1)))
            out.append(f"{pad}</navPoint>")
        return out

    return (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1" xml:lang="zh-CN">\n'
        f'<head><meta name="dtb:uid" content="{UID}"/>'
        '<meta name="dtb:depth" content="3"/>'
        '<meta name="dtb:totalPageCount" content="0"/>'
        '<meta name="dtb:maxPageNumber" content="0"/></head>\n'
        f'<docTitle><text>{esc(book.get("title",""))}</text></docTitle>\n'
        '<navMap>\n' + "\n".join(navpoints(items, 1, 1)) + "\n</navMap>\n</ncx>\n"
    )


def build_opf(book, parts, docs, images, cover_img):
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    manifest = [
        '<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>',
        '<item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>',
        '<item id="css" href="css/book.css" media-type="text/css"/>',
    ]
    if cover_img:
        manifest.append('<item id="cover-image" href="images/cover.svg" '
                        'media-type="image/svg+xml" properties="cover-image"/>')
        manifest.append('<item id="cover" href="text/cover.xhtml" '
                        'media-type="application/xhtml+xml"/>')
    for name in sorted(images):
        if name == "cover.svg":
            continue
        mt = "image/svg+xml" if name.endswith(".svg") else "image/png"
        manifest.append(f'<item id="img-{name}" href="images/{name}" media-type="{mt}"/>')
    for d in docs:
        manifest.append(f'<item id="{d["id"]}" href="{d["href"]}" '
                        'media-type="application/xhtml+xml"/>')
    spine = []
    if cover_img:
        spine.append('<itemref idref="cover"/>')
    for d in docs:
        spine.append(f'<itemref idref="{d["id"]}"/>')

    desc = esc(book.get("abstract", "")[:200])
    kw = book.get("keywords", "")
    subjects = book.get("subjects", [])
    subj_xml = ""
    if kw:
        subj_xml += f'  <dc:subject>{esc(kw)}</dc:subject>\n'
    for s in subjects:
        subj_xml += f'  <dc:subject>{esc(s)}</dc:subject>\n'
    return (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<package xmlns="http://www.idpf.org/2007/opf" version="3.0" '
        'unique-identifier="bookid" xml:lang="zh-CN">\n'
        '<metadata xmlns:dc="http://purl.org/dc/elements/1.1/">\n'
        f'  <dc:identifier id="bookid">{UID}</dc:identifier>\n'
        f'  <dc:title>{esc(book.get("title",""))}</dc:title>\n'
        f'  <dc:creator>{esc(book.get("author",""))}</dc:creator>\n'
        '  <dc:language>zh-CN</dc:language>\n'
        f'  <dc:date>{esc(book.get("date",""))}</dc:date>\n'
        f'  <dc:description>{desc}</dc:description>\n'
        + subj_xml
        + f'  <dc:rights>{esc(book.get("license",""))}</dc:rights>\n'
        + f'  <meta property="dcterms:license">{esc(book.get("license_url",""))}</meta>\n'
        + f'  <meta property="dcterms:modified">{now}</meta>\n'
        '</metadata>\n<manifest>\n  ' + "\n  ".join(manifest) +
        '\n</manifest>\n<spine toc="ncx">\n  ' + "\n  ".join(spine) +
        "\n</spine>\n</package>\n"
    )


if __name__ == "__main__":
    build()
