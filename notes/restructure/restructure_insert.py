# -*- coding: utf-8 -*-
"""插入重构：在现行 1—3 章之后插入新的"第二部分　统一的地平线"（新 4—6 章），
把原第 4—22 章整体后移为 7—25 章。

章号映射：n -> n+3（n>=4）；1—3 不变。文件同步改名 chNN -> ch(NN+3)。
一次运行生效；再次运行会二次位移，切勿重跑。
"""
import os
import re
import subprocess

BOOK = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(BOOK, "source")
GIT = "/mnt/d/Git/cmd/git.exe"


def newn(n):
    n = int(n)
    return n + 3 if n >= 4 else n


def repl(text):
    # h3/h4 前缀
    text = re.sub(r'(<h3[^>]*>)\s*(\d+)\.(\d+)',
                  lambda m: f'{m.group(1)}{newn(m.group(2))}.{m.group(3)}', text)
    text = re.sub(r'(<h4[^>]*>)\s*(\d+)\.(\d+)\.(\d+)',
                  lambda m: f'{m.group(1)}{newn(m.group(2))}.{m.group(3)}.{m.group(4)}', text)
    # 范围
    text = re.sub(r'第\s*(\d+)\s*([—–\-])\s*(\d+)\s*章',
                  lambda m: f'第 {newn(m.group(1))}{m.group(2)}{newn(m.group(3))} 章', text)
    # 单章
    text = re.sub(r'第\s*(\d+)\s*章', lambda m: f'第 {newn(m.group(1))} 章', text)
    # 小节
    text = re.sub(r'第\s*(\d+)\.(\d+(?:\.\d+)?)\s*节',
                  lambda m: f'第 {newn(m.group(1))}.{m.group(2)} 节', text)
    # 编号对象（含警告/例）
    text = re.sub(
        r'(定义|定理|命题|推论|引理|猜想|假说|结论|图|表|式|公式|附注|假设|算法|警告|例)'
        r'([\s（(]*)(\d+)\.(\d+(?:\.\d+)?)',
        lambda m: f'{m.group(1)}{m.group(2)}{newn(m.group(3))}.{m.group(4)}', text)
    return text


def main():
    # 1) 内容重编号
    changed = []
    for fn in sorted(os.listdir(SRC)):
        if not fn.endswith(".html"):
            continue
        p = os.path.join(SRC, fn)
        t = open(p, encoding="utf-8").read()
        nt = repl(t)
        if nt != t:
            open(p, "w", encoding="utf-8").write(nt)
            changed.append(fn)
    print("renumbered files:", len(changed))

    # 2) 文件改名（降序，避免碰撞）：ch22->ch25 ... ch04->ch07
    for n in range(22, 3, -1):
        src = os.path.join(SRC, f"ch{n:02d}.html")
        dst = os.path.join(SRC, f"ch{n+3:02d}.html")
        if os.path.exists(src):
            subprocess.run([GIT, "mv", "-f", src, dst], check=False)
    print("renamed ch04..ch22 -> ch07..ch25")


if __name__ == "__main__":
    main()
