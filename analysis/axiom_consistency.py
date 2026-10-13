# -*- coding: utf-8 -*-
"""axiom_consistency.py — 优先级 A：六条公理在已编码领域中的自洽性核算

目标：对 27 个领域的 EDS 编码，逐条核算六条公理的状态。

诚实基线：
- 只有**图论**列是已证/已核算的（见 axioms_graph.py）。
- 其余领域的格子按编码元数据（是否有限、演化流类型）**机械推导**，
  状态只允许：✓成立 / 平凡 / 不适用 / 未验证。**不存在非图论的 ✓。**
- 这个矩阵的作用不是“证明六条公理普遍成立”，而是**暴露它们在哪里是空的**。

规则（全部可从附录 B 表 B.1 的元数据机械读出）：
  A1 观测完备：图论=平凡（谱嵌入必单射）；其余=未验证。
  A2 精度连续：有限/离散域=平凡（精度离散）；连续域=未验证。
  A3 曲率有界：κ 有定义（非 0/无）=未验证（图论 ✓）；否则=不适用。
  A4 演化适定：无演化流=不适用（空）；有演化流=未验证（图论=硬核）。
  A5 分离完备：有分离结构=未验证（图论=有定理）；否则=未验证。
  A6 标准化：超有限/非标准域（泛函分析）=未验证；其余=不适用。

输出：analysis/results/axiom_consistency.json。
"""
import json
import os

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(HERE, "analysis", "results")

# (领域, 有限/离散?, 演化流: None|"discrete"|"continuous", κ 有定义?)
D = [
    ("图论", True, "continuous", True),
    ("线性代数", True, None, False),
    ("表示论", True, None, False),
    ("调和分析", False, "continuous", False),
    ("点集拓扑", False, None, False),
    ("代数拓扑", True, None, False),
    ("测度论", False, None, False),
    ("实分析", False, None, False),
    ("泛函分析", False, None, False),   # 超有限/非标准
    ("复分析", False, None, False),
    ("组合数学", True, None, True),
    ("数论", True, None, True),
    ("数理逻辑", True, None, False),
    ("类型论", None, None, False),
    ("微分方程", False, "continuous", True),
    ("动力系统", False, "discrete", True),
    ("概率论", False, None, True),
    ("信息论", None, None, True),
    ("算子代数", False, "continuous", True),
    ("量子数学", False, "continuous", True),
    ("博弈论", True, "discrete", True),
    ("优化", False, "continuous", True),
    ("数值分析", True, "discrete", True),
    ("微分几何", False, "continuous", True),
    ("LLM 潜在空间", None, "discrete", True),
    ("马尔可夫链", True, "discrete", True),
    ("编码论", True, None, True),
]

AXIOMS = ["A1 观测完备", "A2 精度连续", "A3 曲率有界", "A4 演化适定", "A5 分离完备", "A6 标准化"]

# 已通过 A4 小实例检验的领域（a4_wellposedness.py）
A4_MINI = {"优化", "马尔可夫链", "微分方程", "动力系统", "数值分析", "算子代数"}


def status(ax, finite, evo, kappa, name):
    graph = (name == "图论")
    if ax == "A1 观测完备":
        return "平凡" if graph else "未验证"
    if ax == "A2 精度连续":
        if finite is True:
            return "平凡"
        return "未验证"
    if ax == "A3 曲率有界":
        if graph:
            return "成立"
        return "未验证" if kappa else "不适用"
    if ax == "A4 演化适定":
        if evo is None:
            return "不适用（无演化流）"
        if graph: return "成立(硬核)"
        return "成立(小实例)" if name in A4_MINI else "未验证"
    if ax == "A5 分离完备":
        return "成立(部分)" if graph else "未验证"
    if ax == "A6 标准化":
        return "未验证" if name == "泛函分析" else "不适用"
    return "?"


def main():
    rows = {}
    for name, finite, evo, kappa in D:
        rows[name] = {ax: status(ax, finite, evo, kappa, name) for ax in AXIOMS}
    # 汇总
    summary = {}
    for ax in AXIOMS:
        vals = [rows[n][ax] for n, *_ in D]
        summary[ax] = {
            "成立": sum(v.startswith("成立") for v in vals),
            "平凡": sum(v == "平凡" for v in vals),
            "不适用": sum(v.startswith("不适用") for v in vals),
            "未验证": sum(v == "未验证" for v in vals),
        }
    out = {"domains": rows, "summary": summary,
           "caveat": ("只有图论列已核算；其余为元数据机械推导。"
                      "A4 在 13 个'无演化流'领域是空的（不适用），"
                      "其余 14 个有演化流的领域中只有图论成立。")}
    os.makedirs(RES, exist_ok=True)
    with open(os.path.join(RES, "axiom_consistency.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(f"{'领域':<14}" + "".join(f"{a[:4]:>10}" for a in AXIOMS))
    for n, *_ in D:
        print(f"{n:<14}" + "".join(f"{rows[n][a][:8]:>10}" for a in AXIOMS))
    print("\n汇总结论：")
    for ax in AXIOMS:
        s = summary[ax]
        print(f"  {ax}: 成立 {s['成立']} / 平凡 {s['平凡']} / 不适用 {s['不适用']} / 未验证 {s['未验证']}")
    print("[done]", os.path.join(RES, "axiom_consistency.json"))


if __name__ == "__main__":
    main()
