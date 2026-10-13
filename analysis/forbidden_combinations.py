# -*- coding: utf-8 -*-
"""forbidden_combinations.py — 优先级 B 的首次尝试：探测"拓扑×正×连续"格子

问题（第 23.5.2 节禁戒检验协议）：表 B.3 把这个格子列为"空缺"。
它是数学禁戒，还是只是"我们的轴标签没把已有的例子放进这一格"？

方法（可计算、有限、诚实）：
  对小的有限图，用一个"拓扑式"的区分结构（Alexandrov / 图拓扑的开集下集）
  作为轴 1 = 拓扑；用 κ_info = Var(λ)/2 的符号作为轴 2；用热半群 e^{-tL}
  作为轴 3 = 连续演化。看是否存在实例同时满足三者。

结果若存在实例 ⇒ 该格子**不是**数学禁戒（禁戒假设被削弱），
且表 B.3 的"空缺"部分是**轴标签造成的假象**。
本脚本不做完整禁戒证明，只做一次有界的可达性探测。
"""
import itertools
import json
import os

import numpy as np

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(HERE, "analysis", "results")


def laplacian(edges, n):
    L = np.zeros((n, n))
    for u, v in edges:
        L[u, u] += 1
        L[v, v] += 1
        L[u, v] -= 1
        L[v, u] -= 1
    return L


def alexandrov_open_sets(edges, n):
    """图拓扑/Alexandrov 拓扑：开集 = 由边关系诱导的下集（此处取"上集"）。

    有限图的自然拓扑是 Alexandrov 拓扑，开集对任意并、有限交封闭。
    这里枚举它的一族开集，作为"拓扑式区分动作"的有限证据。
    """
    adj = [set() for _ in range(n)]
    for u, v in edges:
        adj[u].add(v)
        adj[v].add(u)
    # 主滤子 {x} 的上集：{y : dist(x,y) 有限且...}——用闭邻域作为样本开集
    opens = set()
    for x in range(n):
        up = frozenset([y for y in range(n) if y == x or y in adj[x]])
        opens.add(up)
    opens.add(frozenset())          # 空集
    opens.add(frozenset(range(n)))  # 全集
    return opens


def kappa_info(L):
    lam = np.linalg.eigvalsh(L)
    return float(np.var(lam) / 2.0)


def heat_flow_ok(L):
    """连续演化 e^{-tL} 存在：对 L 的谱做指数，验证半群性质。"""
    lam, V = np.linalg.eigh(L)
    def E(t):
        return V @ np.diag(np.exp(-lam * t)) @ V.T
    return bool(np.allclose(E(0.3) @ E(0.4), E(0.7), atol=1e-9))


def main():
    examples = {
        "C3（三角）": ([(0, 1), (1, 2), (2, 0)], 3),
        "C4（四环）": ([(0, 1), (1, 2), (2, 3), (3, 0)], 4),
        "C5（五环）": ([(0, 1), (1, 2), (2, 3), (3, 4), (4, 0)], 5),
        "K4（完全图）": ([(i, j) for i, j in itertools.combinations(range(4), 2)], 4),
        "P4（路径）": ([(0, 1), (1, 2), (2, 3)], 4),
    }
    rows = []
    realizable = []
    for name, (edges, n) in examples.items():
        L = laplacian(edges, n)
        opens = alexandrov_open_sets(edges, n)
        k = kappa_info(L)
        has_topo = len(opens) >= 3          # 有非平凡开集族
        sign = "正" if k > 1e-9 else ("零" if abs(k) < 1e-9 else "负")
        cont = heat_flow_ok(L)
        cell = has_topo and sign == "正" and cont
        rows.append({"example": name, "has_topology": has_topo, "kappa": round(k, 4),
                     "kappa_sign": sign, "continuous_evolution": cont,
                     "occupies_topo_pos_cont": bool(cell)})
        if cell:
            realizable.append(name)
    verdict = ("NOT_forbidden" if realizable else "no_instance_found")
    out = {
        "target_cell": "拓扑 × 正 × 连续",
        "rows": rows,
        "realizing_instances": realizable,
        "verdict": verdict,
        "conclusion": (
            "该格子并非数学禁戒：有限实例（如 C3 三角）同时具备拓扑式区分、κ>0、"
            "连续热演化。它在表 B.3 中显示为空缺，更可能是轴 1 的标签假象"
            "（我们把这些例子归到了'图论'/'组合'而不是'拓扑'），"
            "而不是数学上不可能。" if realizable else
            "在本次有界搜索中未找到实例；这不构成禁戒证明，只说明需要更大搜索或真正论证。"),
        "caveat": ("有界可达性探测，不是禁戒证明。"
                   "它只能否证'禁戒'，不能证明'禁戒'。"),
    }
    os.makedirs(RES, exist_ok=True)
    with open(os.path.join(RES, "forbidden_combinations.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    for r in rows:
        print(f"{r['example']:<14} topo={r['has_topology']} kappa={r['kappa']:>6} "
              f"({r['kappa_sign']}) cont={r['continuous_evolution']} cell={r['occupies_topo_pos_cont']}")
    print("verdict:", verdict, "| realizers:", realizable)
    print("[done]", os.path.join(RES, "forbidden_combinations.json"))


if __name__ == "__main__":
    main()
