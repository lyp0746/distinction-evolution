# -*- coding: utf-8 -*-
"""reverse_engineer.py — 反向工程：定理 15.1 强迫了六元组的哪些项？

定理 15.1(有限图相变)：设 G 为连通有限图，拉普拉斯谱 0=lam1<lam2<=…<=lamn，
演化 D'=(-alphaI+betaL)D 的临界耦合为 beta1=alpha/lamn、beta2=alpha/lam2。

本脚本逐项检查：若从六元组 (X, D, O, ~, k, Phi) 中移除某一项，定理 15.1 是否
仍能被陈述/证明。判据是"该项是否出现在定理的陈述或证明里"，不是"它是否有用"。

诚实边界：这是**概念核查**(作者判断，B／乙)，不是机器证明；但它把"六元组是不是
被定理强迫的"从印象变成一张可反驳的表。输出 analysis/results/reverse_engineer.json。
"""
import json
import os

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(HERE, "analysis", "results")

# (项, 是否被定理 15.1 使用, 在何处出现, 移除后的后果)
ROWS = [
    ("X　对象集", True, "L 定义在顶点集 X 上", "移除后无载体，L 与 D 都无从定义"),
    ("D　区分动作族", True, "L(邻接/边)即区分结构；谱由 D 决定", "移除后没有谱，定理无法陈述"),
    ("O　观测泛函", True, "状态向量 D 即观测；ODE 描述 D 的演化", "移除后没有可谈论的'区分强度'"),
    ("~　不可区分关系", False, "定理纯谱，未出现任何等价关系", "移除后定理陈述与证明均不变 ⇒ 非必要"),
    ("k　分离曲率", False, "k=Var(lam)/2 是定理 12.1 的导出量，不是 15.1 的输入", "移除后定理不变；k 是下游导出"),
    ("Phi　演化流", True, "D'=(-alphaI+betaL)D 及其解 e^{tM} 即 Phi", "移除后没有动力学，临界耦合无从谈起"),
]


def main():
    needed = [r[0] for r in ROWS if r[1]]
    not_needed = [r[0] for r in ROWS if not r[1]]
    out = {
        "theorem": "定理 15.1(有限图两阶段相变)",
        "rows": [{"item": r[0], "needed": r[1], "where": r[2], "removed": r[3]} for r in ROWS],
        "minimal_set": needed,
        "not_forced": not_needed,
        "conclusion": ("定理 15.1 只强迫 X、D、O、Phi 四项；"
                       "~ 未被使用，k 是下游导出(定理 12.1)。"
                       "因此在图上，六元组不是最小结构：它是四项 + 一个导出量 + 一个未用项。"),
        "caveat": "概念核查(B／乙)，非机器证明；判据是'是否出现在定理的陈述/证明中'。",
    }
    os.makedirs(RES, exist_ok=True)
    with open(os.path.join(RES, "reverse_engineer.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    for r in ROWS:
        print(f"[{'必要' if r[1] else '非必要'}] {r[0]}：{r[2]}")
    print("定理 15.1 的最小结构：", "、".join(needed))
    print("未被强迫：", "、".join(not_needed))
    print("[done]", os.path.join(RES, "reverse_engineer.json"))


if __name__ == "__main__":
    main()
