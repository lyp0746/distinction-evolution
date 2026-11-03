# -*- coding: utf-8 -*-
"""fix_pdf_links.py — 让目录（以及正文里的内部链接）真正能跳。

背景：Chrome 打印 PDF 时把 HTML 锚点写成**命名目标**，而每个目标的坐标是
``/XYZ 0 <页高> 0``——即页面**底部**。于是点击目录项时，阅读器确实跳了，
但落在页脚之外，看起来“没反应”。

做法：
1. 从 ``source/*.html`` 收集 ``id → 标题文本``；
2. 对每一页的每个链接，解析出目标页（命名目标也带页码）；
3. 在目标页上搜索该标题文本，取它的上沿作为落点的 y；找不到就落到页顶；
4. 用等宽矩形重写为 ``LINK_GOTO``（不带命名目标），旧链接删除。

用法：
    python scripts/fix_pdf_links.py output/book.pdf
    python scripts/fix_pdf_links.py output/book.pdf --dry   # 只报告，不写回
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE = os.path.join(HERE, "source")


def _strip(s):
    s = re.sub(r"<[^>]+>", "", s)
    s = s.replace("&nbsp;", " ").replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    return re.sub(r"[ \t\r\n]+", " ", s).strip()


def collect_heads():
    """id → 标题文本（去标签、压缩空白）。"""
    out = {}
    if not os.path.isdir(SOURCE):
        return out
    for fn in sorted(os.listdir(SOURCE)):
        if not fn.endswith(".html"):
            continue
        raw = open(os.path.join(SOURCE, fn), encoding="utf-8").read()
        for m in re.finditer(r"<h([1-4])([^>]*)>(.*?)</h\1>", raw, re.S):
            attrs, inner = m.group(2), m.group(3)
            mid = re.search(r'id="([^"]+)"', attrs)
            if not mid:
                continue
            text = _strip(inner)
            if text:
                out[mid.group(1)] = text
    return out


def rect_of(L):
    return L["from"]


def _find_y(page, text, cache):
    """在目标页上找标题，返回上沿 y；找不到返回 0（页顶）。"""
    if not text:
        return 0
    key = (page.number, text[:24])
    if key in cache:
        return cache[key]
    y = 0
    for probe in (text[:24], text[:14], text[:8]):
        probe = probe.strip()
        if len(probe) < 4:
            continue
        hits = page.search_for(probe)
        if hits:
            y = max(0.0, min(h.y0 for h in hits) - 6)
            break
    cache[key] = y
    return y


def fix(path, dry=False):
    try:
        import pymupdf
    except Exception:
        import fitz as pymupdf

    doc = pymupdf.open(path)
    heads = collect_heads()
    cache = {}
    total = named = goto = 0
    for page in doc:
        links = page.get_links()
        if not links:
            continue
        for L in links:
            kind = L.get("kind")
            if kind not in (pymupdf.LINK_GOTO, pymupdf.LINK_NAMED):
                continue
            tgt = L.get("page", -1)
            if tgt is None or tgt < 0 or tgt >= doc.page_count:
                continue
            total += 1
            name = L.get("nameddest") or ""
            text = heads.get(name, "")
            if not text:                            # 目录行本身就是标签
                try:
                    text = page.get_text("text", clip=rect_of(L)).strip().split("\n")[0].strip()
                except Exception:
                    text = ""
            y = _find_y(doc[tgt], text, cache)
            if kind == pymupdf.LINK_NAMED:
                named += 1
            else:
                goto += 1
            if dry:
                continue
            rect = L["from"]
            try:
                page.delete_link(L)
            except Exception:
                pass
            page.insert_link({"kind": pymupdf.LINK_GOTO, "from": rect,
                              "page": tgt, "to": pymupdf.Point(0, y), "zoom": 0})
    print(f"  [links] {total} 个内部链接（命名 {named} / 直接 {goto}）→ GOTO")
    if dry:
        doc.close()
        return total
    tmp = path + ".links"
    doc.save(tmp, garbage=3, deflate=True)
    doc.close()
    os.replace(tmp, path)
    # 复核
    d2 = pymupdf.open(path)
    bad = sum(1 for pg in d2 for L in pg.get_links()
              if L.get("kind") == pymupdf.LINK_NAMED)
    ys = set()
    for pg in d2:
        for L in pg.get_links():
            if L.get("kind") == pymupdf.LINK_GOTO:
                ys.add(round((L.get("to") or pymupdf.Point(0, 0)).y, 1))
    print(f"  [links] 复核：命名目标残留 {bad}；落点 y 取值 {len(ys)} 种（样例 {sorted(ys)[:4]}）")
    d2.close()
    return total


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        print(__doc__)
        sys.exit(1)
    fix(args[0], dry="--dry" in sys.argv)
