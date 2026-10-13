# -*- coding: utf-8 -*-
"""axis_rethink.py — 表 B.3 三轴设计的反思：空缺有多少是"标签假象"？

背景（第 23.5.2 节 B 探测）：格子"拓扑×正×连续"并非禁戒，只是轴 1 标签假象。
本脚本量化这个问题：把轴 1（区分代数）从"单值分类"改为"多值分类"
（一个领域可同时承认多种区分代数），看 45 个格子里空缺数如何变化。

诚实边界：轴 1 的多值归属是**作者判断（C／丙）**，不是测量。
脚本的作用是**敏感性分析**——说明空缺对分类方式的敏感程度，不是给出真值。

输出：analysis/results/axis_rethink.json。
"""
import itertools
import json
import os

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(HERE, "analysis", "results")

A1 = ["线性", "拓扑", "度量", "序", "逻辑"]
A2 = ["负", "零", "正"]          # κ 符号（"依…"记为全部）
A3 = ["无", "离散", "连续"]       # 演化流

# (领域, 单值轴1（现行）, 多值轴1（修正）, κ 符号, 演化流)
D = [
    ("图论", "序", ["序", "线性", "拓扑"], ["负", "零", "正"], "连续"),
    ("线性代数", "线性", ["线性"], ["零"], "无"),
    ("表示论", "线性", ["线性"], ["零"], "无"),
    ("调和分析", "线性", ["线性", "拓扑"], ["零"], "连续"),
    ("点集拓扑", "拓扑", ["拓扑", "序"], ["负"], "无"),
    ("代数拓扑", "拓扑", ["拓扑", "线性"], ["负"], "无"),
    ("测度论", "度量", ["度量", "拓扑"], ["正"], "无"),
    ("实分析", "度量", ["度量", "拓扑"], ["正"], "无"),
    ("泛函分析", "线性", ["线性", "度量", "拓扑"], ["正"], "无"),
    ("复分析", "度量", ["度量", "拓扑", "线性"], ["零"], "无"),
    ("组合数学", "序", ["序", "逻辑"], ["正"], "无"),
    ("数论", "序", ["序", "逻辑", "线性"], ["正"], "无"),
    ("数理逻辑", "逻辑", ["逻辑", "序"], ["零"], "无"),
    ("类型论", "逻辑", ["逻辑", "拓扑", "线性"], ["负"], "无"),
    ("微分方程", "度量", ["度量", "线性", "拓扑"], ["负", "零", "正"], "连续"),
    ("动力系统", "度量", ["度量", "序", "拓扑"], ["负", "零", "正"], "离散"),
    ("概率论", "度量", ["度量", "序"], ["负", "零", "正"], "无"),
    ("信息论", "度量", ["度量", "逻辑"], ["负"], "无"),
    ("算子代数", "线性", ["线性", "拓扑"], ["负", "零", "正"], "连续"),
    ("量子数学", "线性", ["线性", "度量"], ["正"], "连续"),
    ("博弈论", "序", ["序", "逻辑"], ["负", "零", "正"], "离散"),
    ("优化", "度量", ["度量", "线性"], ["负", "零", "正"], "连续"),
    ("数值分析", "线性", ["线性", "度量"], ["正"], "离散"),
    ("微分几何", "度量", ["度量", "拓扑", "线性"], ["负", "零", "正"], "连续"),
    ("LLM 潜在空间", "度量", ["度量", "线性"], ["正"], "离散"),
    ("马尔可夫链", "序", ["序", "度量"], ["负", "零", "正"], "离散"),
    ("编码论", "逻辑", ["逻辑", "序"], ["正"], "无"),
]


def occupied(multi):
    cells = set()
    for name, single, revised, ksig, evo in D:
        a1s = revised if multi else [single]
        for a1, a2, a3 in itertools.product(a1s, ksig, [evo]):
            cells.add((a1, a2, a3))
    return cells


def main():
    total = len(A1) * len(A2) * len(A3)          # 45
    occ_single = occupied(False)
    occ_multi = occupied(True)
    out = {
        "total_cells": total,
        "occupied_single_axis1": len(occ_single),
        "occupied_multi_axis1": len(occ_multi),
        "empty_single": total - len(occ_single),
        "empty_multi": total - len(occ_multi),
        "newly_filled": sorted(f"{a}/{b}/{c}" for a, b, c in (occ_multi - occ_single)),
        "caveat": "轴1多值归属为作者判断（C／丙）；这是敏感性分析，不是真值。",
    }
    os.makedirs(RES, exist_ok=True)
    with open(os.path.join(RES, "axis_rethink.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"总格子 {total}")
    print(f"单值轴1：占据 {len(occ_single)}，空缺 {total - len(occ_single)}")
    print(f"多值轴1：占据 {len(occ_multi)}，空缺 {total - len(occ_multi)}")
    print("新增填充：", out["newly_filled"])
    print("[done]", os.path.join(RES, "axis_rethink.json"))


if __name__ == "__main__":
    main()
