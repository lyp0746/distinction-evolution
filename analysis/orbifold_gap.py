# -*- coding: utf-8 -*-
"""
orbifold_gap.py — 第 17 章的数值对比：χ(D)=χ(M)/3 何时成立、何时失败。

明确定义（避免歧义）
------------------------------------------------------------
考虑一个二维轨形 B（拓扑商空间底流形 M，奇异点阶数 α_i）：

    χ_geom = χ(M) = 2 - 2g                         （底流形欧拉示性数）
    χ_orb  = χ_geom - Σ_i (1 - 1/α_i)              （Satake 轨形欧拉示性数）

轨形 Gauss–Bonnet：∫_B K dA = 2π χ_orb。

本书取分离曲率 κ = R/6 = K/3（二维）。于是

    ∫_B κ dA = (1/3) ∫_B K dA = (2π/3) χ_orb.

若定义区分欧拉示性数 χ(D) := (1/2π)∫_B κ dA，则

    χ(D) = χ_orb / 3.                              （由 Gauss–Bonnet 定义）

而本书第 17 章用的是朴素猜想 χ(D) = χ_geom/3。二者一致**当且仅当 χ_orb = χ_geom**，
即在**无奇异点**（自由作用／光滑流形）时。带锥点的轨形给出反例。

输出：analysis/results/orbifold_gap.json 与控制台表。
依赖：仅标准库（numpy 可选）。
"""
import json
import os

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(HERE, "analysis", "results")


def chi_geom(g):
    return 2 - 2 * g


def chi_orb(g, cone_orders):
    return chi_geom(g) - sum(1.0 - 1.0 / a for a in cone_orders)


def catalog():
    rows = []

    def add(name, g, orders, note):
        cg = chi_geom(g)
        co = chi_orb(g, orders)
        chi_D = co / 3.0                 # Gauss–Bonnet 定义
        naive = cg / 3.0                 # 本书朴素猜想
        rows.append({
            "name": name,
            "genus_underlying": g,
            "cone_orders": orders,
            "chi_geom": cg,
            "chi_orb": round(co, 6),
            "chi_D_gauss_bonnet": round(chi_D, 6),
            "chi_geom_over_3": round(naive, 6),
            "matches": abs(chi_D - naive) < 1e-9,
            "no_singular_points": len(orders) == 0,
            "note": note,
        })

    # 自由作用（无奇异点）：χ_orb = χ_geom，猜想成立
    add("smooth surface genus 0 (no action)", 0, [], "无奇异点：χ_orb=χ_geom=2，χ(D)=2/3 自洽")
    add("smooth surface genus 2", 2, [], "无奇异点：χ_orb=χ_geom=-2，自洽")
    add("free Z/3Z quotient (genus-2 bottom)", 2, [],
        "自由 Z/3Z 作用的商：底流形 genus 2，无锥点，自洽")
    add("free Z/3Z quotient (genus-1 bottom)", 1, [],
        "自由 Z/3Z 作用的商：环面，χ=0，自洽")
    # 带奇异点：一般失败
    add("S^2/(Z/3Z), two fixed pts", 0, [3, 3],
        "底流形 S^2，两个 3 阶锥点；χ_orb=2/3，χ(D)=2/9 ≠ 2/3 → 反例")
    add("S^2 with three 3-cones", 0, [3, 3, 3],
        "底流形 S^2，三个 3 阶锥点；χ_orb=0，χ(D)=0 ≠ 2/3 → 反例（第 17.5 节）")
    add("S^2 with one 3-cone", 0, [3],
        "底流形 S^2，一个 3 阶锥点；χ_orb=4/3，χ(D)=4/9 ≠ 2/3 → 反例")
    add("T^2 with three 3-cones", 1, [3, 3, 3],
        "底流形环面，三个 3 阶锥点；χ_orb=-2，χ(D)=-2/3 ≠ 0 → 反例")
    add("genus-2 bottom with one 3-cone", 2, [3],
        "底流形 genus 2，一个锥点；χ_orb=-8/3，χ(D)=-8/9 ≠ -2/3 → 反例")
    return rows


def free_action_genus():
    """一个 Z/3Z 自由作用存在的充要条件：3 | χ(covering)=2-2g_covering。"""
    out = []
    for g in range(0, 19):
        chi = 2 - 2 * g
        if chi % 3 == 0:
            g_bottom = (2 - chi // 3) // 2  # χ_bottom = chi/3 = 2-2g_bottom
            out.append({"g_covering": g, "chi_covering": chi,
                        "chi_bottom": chi // 3, "g_bottom": g_bottom})
    return out


def main():
    rows = catalog()
    n = len(rows)
    match = [r for r in rows if r["matches"]]
    fail = [r for r in rows if not r["matches"]]
    out = {
        "definitions": {
            "chi_geom": "2 - 2g  (underlying surface)",
            "chi_orb": "chi_geom - sum_i (1 - 1/alpha_i)  (Satake)",
            "chi_D": "chi_orb / 3   (integration of kappa = K/3 via orbifold Gauss-Bonnet)",
            "naive_conjecture": "chi_D = chi_geom / 3",
        },
        "catalog": rows,
        "free_action_genus": free_action_genus(),
        "summary": {
            "n_cases": n,
            "n_matches": len(match),
            "n_refuted": len(fail),
            "verdict": ("χ(D)=χ(M)/3 当且仅当轨形无奇异点（χ_orb=χ_geom）；"
                        "任何带锥点的轨形都是反例。这精确刻画了第 17.5 节的球面矛盾。"),
        },
    }
    os.makedirs(RES, exist_ok=True)
    with open(os.path.join(RES, "orbifold_gap.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(f"{'name':36s} {'chi_geom':>8} {'chi_orb':>8} {'chi(D)':>8} {'chi/3':>8}  match")
    for r in rows:
        print(f"{r['name']:36s} {r['chi_geom']:>8} {r['chi_orb']:>8} "
              f"{r['chi_D_gauss_bonnet']:>8} {r['chi_geom_over_3']:>8}  "
              f"{'YES' if r['matches'] else 'NO '}")
    print(f"\n{out['summary']['n_matches']}/{n} 匹配；{out['summary']['n_refuted']} 个反例。")
    print("存在自由 Z/3Z 作用的覆盖亏格：", [c["g_covering"] for c in out["free_action_genus"]])
    print("[done]", os.path.join(RES, "orbifold_gap.json"))


if __name__ == "__main__":
    main()
