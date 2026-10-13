# -*- coding: utf-8 -*-
"""一次性重构脚本：把章号规范化为"正文阅读顺序 = 物理文件序号 = 章号"。

背景：原稿中 chNN.html 与"第 M 章"错位（如 ch12.html 是"第 1 章"）。
重构后正文顺序为 方法→样板→构造→硬核→边界，即文件 ch01..ch22 的自然顺序，
故令 new(M) 使 chNN.html 恰为"第 NN 章"。

同时重写所有跨引用：第 N 章 / 第 N.M 节 / 第 N.M.Z 节 / 定义·定理·图·表·式 N.M，
以及 h2/h3/h4 标题的章号前缀。范围引用（第 a—b 章）按端点映射。

不处理的文件：front_whatsnew.html（将删除）、ch23–ch26.html（将裁撤/降格）。
"""
import os
import re

BOOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(BOOK, "source")

# old displayed chapter number -> new displayed chapter number
OLD2NEW = {
    1: 12, 2: 13, 3: 14, 4: 15,
    5: 1, 6: 2, 7: 3,
    8: 8, 9: 9, 10: 10, 11: 11,
    12: 4, 13: 5, 14: 6, 15: 7,
    16: 16, 17: 17, 18: 18, 19: 19, 20: 20, 21: 21, 22: 22,
}

SKIP = {"front_whatsnew.html", "ch23.html", "ch24.html", "ch25.html", "ch26.html"}


def m(n):
    return OLD2NEW.get(int(n), int(n))


def repl(text):
    stats = {"range": 0, "chapter": 0, "section": 0, "object": 0, "h3": 0, "h4": 0}

    # 1) 范围：第 a—b 章
    def r_range(mo):
        stats["range"] += 1
        return f'第 {m(mo.group(1))}{mo.group(2)}{m(mo.group(3))} 章'
    text = re.sub(r'第\s*(\d+)\s*([—–\-])\s*(\d+)\s*章', r_range, text)

    # 2) 单章：第 N 章
    def r_chapter(mo):
        stats["chapter"] += 1
        return f'第 {m(mo.group(1))} 章'
    text = re.sub(r'第\s*(\d+)\s*章', r_chapter, text)

    # 3) 小节：第 N.M 节 / 第 N.M.Z 节
    def r_section(mo):
        stats["section"] += 1
        return f'第 {m(mo.group(1))}.{mo.group(2)} 节'
    text = re.sub(r'第\s*(\d+)\.(\d+(?:\.\d+)?)\s*节', r_section, text)

    # 4) 编号对象：定义/定理/图/表/式 N.M（允许前置"（"）
    def r_object(mo):
        stats["object"] += 1
        return f'{mo.group(1)}{mo.group(2)}{m(mo.group(3))}.{mo.group(4)}'
    text = re.sub(
        r'(定义|定理|命题|推论|引理|猜想|假说|结论|图|表|式|公式|附注|假设|算法)'
        r'([\s（(]*)'
        r'(\d+)\.(\d+(?:\.\d+)?)',
        r_object,
        text,
    )

    # 5) h3 标题前缀 N.M
    def r_h3(mo):
        stats["h3"] += 1
        return f'{mo.group(1)}{m(mo.group(2))}.{mo.group(3)}'
    text = re.sub(r'(<h3[^>]*>)\s*(\d+)\.(\d+)', r_h3, text)

    # 6) h4 标题前缀 N.M.Z
    def r_h4(mo):
        stats["h4"] += 1
        return f'{mo.group(1)}{m(mo.group(2))}.{mo.group(3)}.{mo.group(4)}'
    text = re.sub(r'(<h4[^>]*>)\s*(\d+)\.(\d+)\.(\d+)', r_h4, text)

    # 注意：h2 的“第 N 章”已由规则 2 处理，切勿再次映射（会双重置换）。
    return text


def main():
    changed = []
    for fn in sorted(os.listdir(SRC)):
        if not (fn.endswith(".html")):
            continue
        if fn in SKIP:
            continue
        # 只处理 ch/ front_/ back_/ appendix_（front_copyright 也含日期占位，无章号）
        with open(os.path.join(SRC, fn), encoding="utf-8") as f:
            txt = f.read()
        new = repl(txt)
        if new != txt:
            with open(os.path.join(SRC, fn), "w", encoding="utf-8") as f:
                f.write(new)
            changed.append(fn)
    print(f"rewrote {len(changed)} files")
    for fn in changed:
        print("  ", fn)


if __name__ == "__main__":
    main()
