# -*- coding: utf-8 -*-
"""把原 ch24（区分与计算）与 ch25（区分与学习）合并为附录 K。

这两章有出处、有可复算内容，降格为"登记但未展开的猜想"附录；
原 ch23（扭量/全息）与 ch26（量子引力）无出处，删除。
"""
import os
import re

BOOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(BOOK, "source")


def read(fn):
    with open(os.path.join(SRC, fn), encoding="utf-8") as f:
        return f.read()


def transform(txt, sec_map, obj_maps):
    # 去掉章标题
    txt = re.sub(r'<h2 class="chapter">.*?</h2>\s*', "", txt, count=1, flags=re.S)
    # h3 小节号：24.1 -> K.1
    txt = re.sub(r'<h3>(\d+)\.(\d+)([　\s][^<]*)</h3>',
                 lambda m: f'<h3>{sec_map[f"{m.group(1)}.{m.group(2)}"]}{m.group(3)}</h3>', txt)
    # 编号对象
    for label, mp in obj_maps.items():
        txt = re.sub(rf'{label} (\d+\.\d+)',
                     lambda m, label=label, mp=mp: f'{label} {mp[m.group(1)]}', txt)
    # 章号引用：24/25 -> 本附录；旧第 5 章（统一冲动）-> 新第 1 章
    txt = txt.replace("第 24 章", "本附录").replace("第 25 章", "本附录")
    txt = txt.replace("第 5 章", "第 1 章")
    # 登记表编号 24.N -> K-N（避免与节号 K.N 冲突）
    txt = re.sub(r'>\s*24\.(\d+)\s*<', lambda m: f'>K-{m.group(1)}<', txt)
    # 裸节引用 第 X.Y 节 -> K.n
    txt = re.sub(r'第 (\d+)\.(\d+) 节',
                 lambda m: sec_map.get(f'{m.group(1)}.{m.group(2)}', m.group(0)), txt)
    # 其余裸 24.N / 25.N -> K.n
    txt = re.sub(r'24\.(\d+)', lambda m: sec24.get(f'24.{m.group(1)}', m.group(0)), txt)
    txt = re.sub(r'25\.(\d+)', lambda m: sec25.get(f'25.{m.group(1)}', m.group(0)), txt)
    # 修复原稿遗留的重复加粗
    txt = txt.replace("<b>复杂度是关于分辨能力的。<b>EDS", "<b>复杂度是关于分辨能力的。</b>EDS")
    return txt.strip()


def split_refs(txt):
    m = re.search(r'<h3>本章参考文献</h3>\s*<div class="refs">(.*?)</div>', txt, re.S)
    if not m:
        return txt, ""
    return (txt[:m.start()] + txt[m.end():]).strip(), m.group(1).strip()


ch24 = read("ch24.html")
ch25 = read("ch25.html")

sec24 = {"24.1": "K.1", "24.2": "K.2", "24.3": "K.3", "24.4": "K.4", "24.5": "K.5"}
obj24 = {"定义": {"24.1": "K.1"}, "猜想": {"24.1": "K.1", "24.2": "K.2"}, "表": {"24.1": "K.1"}}
sec25 = {"25.1": "K.6", "25.2": "K.7", "25.3": "K.8", "25.4": "K.9", "25.5": "K.10"}
obj25 = {"假说": {"25.1": "K.1"}, "结论": {"25.1": "K.1"}, "表": {"25.1": "K.2", "25.2": "K.3"}}

b24, r24 = split_refs(transform(ch24, sec24, obj24))
b25, r25 = split_refs(transform(ch25, sec25, obj25))

# 附录语境：章→附录；两个"本章小结"重命名为方向小结
b24 = b24.replace("本章", "本附录").replace("<h3>K.5　本附录小结</h3>", "<h3>K.5　计算方向小结</h3>")
b25 = b25.replace("本章", "本附录").replace("<h3>K.10　本附录小结</h3>", "<h3>K.10　学习方向小结</h3>")

lead = ('<p class="lead">本附录登记两组<b>有出处、可操作、但尚未展开</b>的 C 级猜想：'
        '计算的区分复杂度（K.1–K.5）与学习的曲率—涌现（K.6–K.10）。'
        '它们来自正文纲领之外的联想，之所以保留，是因为各自带有<b>可复算的对象、明确的证伪条件，'
        '以及一段真实运行过的代码或一个被明确拒绝的口号</b>。把它们放进附录而不是正文，'
        '是为了不让"联想"冒充"论证"——正文的硬核（第四部分）与边界（第五部分）不依赖本附录的任何命题。</p>')

html = f'''<h1 class="chapter">附录 K　登记但未展开的猜想：计算与学习</h1>

{lead}

{b24}

{b25}

<h3>本附录参考文献</h3>
<div class="refs">
{r24}
{r25}
</div>
'''

with open(os.path.join(SRC, "appendix_k_conjectures.html"), "w", encoding="utf-8") as f:
    f.write(html)
print("wrote appendix_k_conjectures.html", len(html), "bytes")
