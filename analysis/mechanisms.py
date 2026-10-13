# -*- coding: utf-8 -*-
"""mechanisms.py — 统一的四种机制：覆盖率统计（分类提案，等级 C／丙）

按用户提出的四类统一机制，对 27 个领域标注其出现情况：
  A 反对称闭算子型（X∘X=0，如外微分 d²=0、链复形）
  B 对偶／格型（Galois 连接、开闭集、对偶空间）
  C 不变性／转移型（转移原理、解析延拓、几乎处处、遍历不变）
  D 路径／同伦型（相等即路径、同伦、高阶结构）

诚实边界：机制归属是**作者判断（C／丙）**，不是测量；四机制是**一个分类提案**，
不声称穷尽，也不声称"第一性原理"。脚本只做覆盖率统计。

输出：analysis/results/mechanisms.json。
"""
import json
import os

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(HERE, "analysis", "results")

# (领域, 出现的机制集合)
D = [
    ("图论", ["A", "B"]),          # 图上余调 d²=0；偏序/二次型
    ("线性代数", ["B"]),           # 对偶空间
    ("表示论", ["B"]),             # 特征标对偶
    ("调和分析", ["B", "C"]),      # Pontryagin 对偶；不变性
    ("点集拓扑", ["B", "D"]),      # 开闭集对偶；基本群胚
    ("代数拓扑", ["A", "D"]),      # 链复形 d²=0；同伦
    ("测度论", ["B", "C"]),        # σ-代数对偶；几乎处处
    ("实分析", ["C"]),             # 极限/不变性
    ("泛函分析", ["B", "C"]),      # 对偶；转移
    ("复分析", ["A", "C"]),        # d-bar d²=0；解析延拓
    ("组合数学", ["B"]),           # 偏序/格
    ("数论", ["B", "C"]),          # 伽罗瓦对偶；局部—整体
    ("数理逻辑", ["B", "C"]),      # 布尔代数；紧致性/转移
    ("类型论", ["B", "D"]),        # 笛卡尔闭；相等即路径
    ("微分方程", ["C"]),           # 不变量/守恒
    ("动力系统", ["C", "D"]),      # 遍历不变；回复
    ("概率论", ["B", "C"]),        # 对偶；几乎处处
    ("信息论", ["C"]),             # 不变性
    ("算子代数", ["A", "B"]),      # 导子；Gelfand 对偶
    ("量子数学", ["B", "D"]),      # 对偶；高阶结构
    ("博弈论", ["B"]),             # 策略格
    ("优化", ["B"]),               # 线性规划对偶
    ("数值分析", ["C"]),           # 收敛/不变性
    ("微分几何", ["A", "B", "D"]), # 外微分；Hodge 对偶；特征类
    ("LLM 潜在空间", ["C"]),        # 表示不变性
    ("马尔可夫链", ["B", "C"]),    # 对偶；遍历性
    ("编码论", ["B"]),             # 对偶码
]

MECH = {"A": "反对称闭算子型", "B": "对偶／格型", "C": "不变性／转移型", "D": "路径／同伦型"}


def main():
    coverage = {m: 0 for m in MECH}
    only = {m: [] for m in MECH}
    multi = 0
    for name, ms in D:
        for m in ms:
            coverage[m] += 1
        if len(ms) > 1:
            multi += 1
        for m in MECH:
            if ms == [m]:
                only[m].append(name)
    total_marks = sum(len(ms) for _, ms in D)
    out = {
        "mechanisms": MECH,
        "coverage": coverage,
        "total_marks": total_marks,
        "domains": len(D),
        "multi_mechanism_domains": multi,
        "single_mechanism_only": {m: v for m, v in only.items()},
        "caveat": "机制归属为作者判断（C／丙）；四机制是分类提案，不声称穷尽或'第一性原理'。",
    }
    os.makedirs(RES, exist_ok=True)
    with open(os.path.join(RES, "mechanisms.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    for m, label in MECH.items():
        print(f"{m} {label}: 出现于 {coverage[m]}/27 领域")
    print(f"总标注数 {total_marks}；多机制领域 {multi}/{len(D)}")
    print("[done]", os.path.join(RES, "mechanisms.json"))


if __name__ == "__main__":
    main()
