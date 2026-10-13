# -*- coding: utf-8 -*-
"""按重构后的阅读顺序生成 source/parts.json。

顺序 = 文件序号 = 章号：方法(ch01-03) → 样板(ch04-07) → 构造(ch08-11)
→ 硬核(ch12-15) → 边界与纲领(ch16-22)。
章标题取自各文件的 <h2 class="chapter">，小节取自 <h3>。
"""
import json
import os
import re

BOOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(BOOK, "source")

PARTS = [
    ("第一部分　问题与方法：统一值不值",
     "先把“统一”拆成可检验的强度与纪律，再把“抽象统摄具体”写成可执行的压缩操作。",
     range(1, 4)),
    ("第二部分　样板：方法在成熟领域上兑现",
     "四个读者熟悉的领域，四次“重建前后”对照；先相信方法，再允许作者谈自己的构造。",
     range(4, 8)),
    ("第三部分　现场构造：从区分到 EDS",
     "方法在“区分”上的现场输出；六条公理是从硬核定理反推出来的诠释，而非前提。",
     range(8, 12)),
    ("第四部分　硬核：一个可完全验证的情形",
     "有限图上的两阶段相变：全书唯一可证明、可计算、可复现的部分。",
     range(12, 16)),
    ("第五部分　边界与纲领",
     "框架撞上的第一堵墙（1/3）、领域编码的诚实边界，以及一份可接手的路线图。",
     range(16, 23)),
]


def chapter(n):
    fname = f"ch{n:02d}.html"
    with open(os.path.join(SRC, fname), encoding="utf-8") as f:
        txt = f.read()
    h2 = re.search(r'<h2 class="chapter">\s*第\s*(\d+)\s*章[　\s]*(.*?)</h2>', txt, re.S)
    no = h2.group(1) if h2 else str(n)
    title = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", h2.group(2))).strip() if h2 else ""
    sections = []
    for m in re.finditer(r"<h3[^>]*>(.*?)</h3>", txt, re.S):
        label = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", m.group(1))).strip()
        if re.match(r"\d+\.\d+", label) and "参考文献" not in label:
            sections.append(label.replace("　", " "))
    return {"no": no, "title": title, "file": fname, "written": True, "sections": sections}


def main():
    parts = []
    for ptitle, pdesc, rng in PARTS:
        parts.append({"part": ptitle, "desc": pdesc,
                      "chapters": [chapter(n) for n in rng]})
    out = os.path.join(SRC, "parts.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(parts, f, ensure_ascii=False, indent=2)
    total = sum(len(p["chapters"]) for p in parts)
    print(f"wrote {out}: {len(parts)} parts, {total} chapters")


if __name__ == "__main__":
    main()
