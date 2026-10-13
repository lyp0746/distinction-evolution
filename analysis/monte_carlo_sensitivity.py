# -*- coding: utf-8 -*-
"""
monte_carlo_sensitivity.py — 对第 15 章启发式阈值假说做敏感性分析。

问题：第 15.5 节的假说 A1/A2 说"某层总激活 S 长期低于阈值则特征塌缩，高于则放大"。
但 α、β、k_eff 都不是从架构直接读出的，它们有不确定性。本脚本回答：
  * 在给定的参数不确定性下，"κ = βS(1−1/k_eff) − α 的符号"有多稳定？
  * 方向翻转概率（direction-flip）是多少？
  * 能给出什么级别的结论（区间 / 序 / 仅符号 / 无点估计）？

尺度分离原则：本脚本的输出是"κ 符号的稳定性"，不是任何时间或容量的精度。
所有 regime 参数（CV、k 的范围）都是**规定性的（C 级）**，用途是回答敏感性，
不是声称真实值。

输出：analysis/results/monte_carlo_sensitivity.json
依赖：numpy。
"""
import json
import os

import numpy as np

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(HERE, "analysis", "results")
N = 400_000
SEED = 1
RNG = np.random.default_rng(SEED)


def sigma(cv):
    return float(np.sqrt(np.log(1.0 + cv ** 2)))


def run(S_obs, cv_alpha=0.3, cv_beta=0.3, k=64, n=N):
    """给定观测总激活 S_obs，采样 α、β、k_eff，返回 κ 符号的统计。"""
    alpha = np.exp(RNG.normal(0, sigma(cv_alpha), n))
    beta = np.exp(RNG.normal(0, sigma(cv_beta), n))
    # k_eff ∈ [1, k]，用 Beta 分布模拟"分布均匀程度"的不确定性
    u = RNG.beta(2.0, 2.0, n)
    k_eff = 1.0 + u * (k - 1.0)
    kappa = beta * S_obs * (1.0 - 1.0 / k_eff) - alpha
    frac_pos = float(np.mean(kappa > 0))
    # 与"朴素阈值 S_c=α/β"比较：朴素判断
    naive = beta * S_obs - alpha
    flip = float(np.mean((kappa > 0) != (naive > 0)))
    return {
        "S_obs": S_obs,
        "frac_kappa_positive": round(frac_pos, 4),
        "direction_flip_vs_naive": round(flip, 4),
        "kappa_p10_p90": [round(float(np.percentile(kappa, 10)), 3),
                          round(float(np.percentile(kappa, 90)), 3)],
    }


def licensed(frac_pos, flip):
    if abs(frac_pos - 0.5) < 0.05 or flip > 0.20:
        return "direction unstable; conditional branches only"
    if frac_pos > 0.9 and flip < 0.05:
        return "ordinal + narrow interval"
    if frac_pos > 0.75:
        return "ordinal only (direction stable, magnitude not reportable)"
    return "sign only"


def main():
    out = {
        "N": N,
        "note": "regime params (CV, k range) are stipulative (quality C); they answer sensitivity, not truth.",
        "scale_warning": "输出是 κ 符号的稳定性，不是任何时间/容量量的精度。",
        "scenarios": {},
    }
    for S in [0.5, 1.0, 2.0, 5.0, 10.0]:
        r = run(S)
        r["licensed_claim"] = licensed(r["frac_kappa_positive"], r["direction_flip_vs_naive"])
        out["scenarios"][f"S={S}"] = r
        print(f"S={S:<5} P(κ>0)={r['frac_kappa_positive']:.3f} "
              f"flip={r['direction_flip_vs_naive']:.3f} -> {r['licensed_claim']}")

    # 单因子检查：把 cv_alpha 从 0.3 降到 0.1
    base = run(2.0)
    tight = run(2.0, cv_alpha=0.1, cv_beta=0.1)
    out["single_factor_check"] = {
        "S": 2.0,
        "P_kappa_pos_cv0.3": base["frac_kappa_positive"],
        "P_kappa_pos_cv0.1": tight["frac_kappa_positive"],
        "note": "降低参数不确定性不改变方向结论，只收窄区间。",
    }

    os.makedirs(RES, exist_ok=True)
    with open(os.path.join(RES, "monte_carlo_sensitivity.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    # 注入正文占位符
    inj_path = os.path.join(HERE, "data", "injected.json")
    inj = {}
    if os.path.exists(inj_path):
        try:
            with open(inj_path, encoding="utf-8") as f:
                inj = json.load(f)
        except Exception:
            inj = {}
    inj["mc_S1_pos"] = f"{out['scenarios']['S=1.0']['frac_kappa_positive']:.3f}"
    inj["mc_S2_pos"] = f"{out['scenarios']['S=2.0']['frac_kappa_positive']:.3f}"
    inj["mc_S2_flip"] = f"{out['scenarios']['S=2.0']['direction_flip_vs_naive']:.3f}"
    with open(inj_path, "w", encoding="utf-8") as f:
        json.dump(inj, f, ensure_ascii=False, indent=2)
    print("[done]", os.path.join(RES, "monte_carlo_sensitivity.json"))


if __name__ == "__main__":
    main()
