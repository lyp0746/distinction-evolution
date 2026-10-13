# -*- coding: utf-8 -*-
"""
llm_activation_probe.py — 工程验证：层间激活与有效秩的相变探针。

背景（第 15 章、假说 A1/A2）
------------------------------------------------------------
本书第 15.5 节提出一个假说：在简化模型下，若某层的总激活 S 长期低于阈值
α/[β(1−1/k_eff)]，则其特征塌缩（有效秩不增长）；显著高于阈值则特征放大。
该假说标注为 C 级，且此前的唯一"证据"是玩具 ODE。本脚本把"可证伪"从承诺
变成事实：在一个**真实训练循环**上测量 S 与有效秩，并报告结果——包括失败。

两种运行模式
------------------------------------------------------------
1) --synthetic （默认，纯 NumPy，本机可跑）
   在模加法任务（grokking 的标准任务）上训练一个 MLP，带权重衰减。逐层记录
   总激活 S、有效秩 r，并检验：S 的变化趋势是否与 r 的变化趋势同号。
   这是对"激活—秩"机制的**无自由参数的定性检验**（不依赖 α、β 的可读性）。

2) --hf MODEL_ID （需要 torch + transformers + 可访问 HuggingFace）
   在给定模型的每个 Transformer 块上挂 forward hook，统计每层激活范数与
   有效秩。本机环境无 torch/transformers 且 HuggingFace 不可达，故此模式
   **未运行**；代码保留以便有条件的读者复现。脚本会明确打印"未运行"。

输出
------------------------------------------------------------
analysis/results/llm_activation_probe.json
assets/charts/llm_activation_probe.png

依赖：numpy（必需）；matplotlib（画图，可选）；torch/transformers（仅 --hf）。
"""
import argparse
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(HERE, "analysis", "results")
CHARTS = os.path.join(HERE, "assets", "charts")
SEED = 0


# ================================================================ 模加法数据
def modular_addition(p, train_frac=0.3, seed=SEED):
    rng = np.random.default_rng(seed)
    pairs = np.array([(a, b) for a in range(p) for b in range(p)])
    labels = (pairs[:, 0] + pairs[:, 1]) % p
    idx = rng.permutation(len(pairs))
    n_tr = int(len(pairs) * train_frac)
    tr, te = idx[:n_tr], idx[n_tr:]
    X = np.zeros((len(pairs), 2 * p))
    X[np.arange(len(pairs)), pairs[:, 0]] = 1
    X[np.arange(len(pairs)), p + pairs[:, 1]] = 1
    return X[tr], labels[tr], X[te], labels[te]


# ================================================================ MLP（NumPy）
class MLP:
    def __init__(self, sizes, seed=SEED):
        rng = np.random.default_rng(seed)
        self.W, self.b = [], []
        for i in range(len(sizes) - 1):
            # He 初始化
            self.W.append(rng.standard_normal((sizes[i], sizes[i + 1])) * np.sqrt(2.0 / sizes[i]))
            self.b.append(np.zeros(sizes[i + 1]))
        self.cache = {}

    def forward(self, X, keep=False):
        acts = [X]
        H = X
        pre = []
        for i in range(len(self.W) - 1):
            Z = H @ self.W[i] + self.b[i]
            pre.append(Z)
            H = np.maximum(Z, 0.0)          # ReLU
            acts.append(H)
        logits = H @ self.W[-1] + self.b[-1]
        self.cache = {"acts": acts, "pre": pre}
        return logits

    def loss_grad(self, X, y, weight_decay, p):
        logits = self.forward(X)
        # softmax cross-entropy
        z = logits - logits.max(axis=1, keepdims=True)
        ex = np.exp(z)
        prob = ex / ex.sum(axis=1, keepdims=True)
        n = len(y)
        loss = -np.log(prob[np.arange(n), y] + 1e-12).mean()
        loss += 0.5 * weight_decay * sum((W ** 2).sum() for W in self.W)
        dlogits = prob.copy()
        dlogits[np.arange(n), y] -= 1.0
        dlogits /= n
        gW = [None] * len(self.W)
        gb = [None] * len(self.b)
        delta = dlogits
        for i in range(len(self.W) - 1, -1, -1):
            Hprev = self.cache["acts"][i]
            gW[i] = Hprev.T @ delta + weight_decay * self.W[i]
            gb[i] = delta.sum(axis=0)
            if i > 0:
                dH = delta @ self.W[i].T
                delta = dH * (self.cache["pre"][i - 1] > 0)
        return loss, gW, gb, prob

    def step(self, gW, gb, lr):
        for i in range(len(self.W)):
            self.W[i] -= lr * gW[i]
            self.b[i] -= lr * gb[i]


class Adam:
    """NumPy 版 Adam（无 torch 依赖）。"""
    def __init__(self, net, lr=1e-3, b1=0.9, b2=0.999, eps=1e-8):
        self.lr, self.b1, self.b2, self.eps = lr, b1, b2, eps
        self.mW = [np.zeros_like(W) for W in net.W]
        self.vW = [np.zeros_like(W) for W in net.W]
        self.mb = [np.zeros_like(b) for b in net.b]
        self.vb = [np.zeros_like(b) for b in net.b]
        self.t = 0

    def step(self, net, gW, gb):
        self.t += 1
        for i in range(len(net.W)):
            self.mW[i] = self.b1 * self.mW[i] + (1 - self.b1) * gW[i]
            self.vW[i] = self.b2 * self.vW[i] + (1 - self.b2) * gW[i] ** 2
            mh = self.mW[i] / (1 - self.b1 ** self.t)
            vh = self.vW[i] / (1 - self.b2 ** self.t)
            net.W[i] -= self.lr * mh / (np.sqrt(vh) + self.eps)
            self.mb[i] = self.b1 * self.mb[i] + (1 - self.b1) * gb[i]
            self.vb[i] = self.b2 * self.vb[i] + (1 - self.b2) * gb[i] ** 2
            mh = self.mb[i] / (1 - self.b1 ** self.t)
            vh = self.vb[i] / (1 - self.b2 ** self.t)
            net.b[i] -= self.lr * mh / (np.sqrt(vh) + self.eps)


def eff_rank(H):
    """参与比：(Σσ)² / Σσ²，对中心化后的激活矩阵。"""
    Hc = H - H.mean(axis=0, keepdims=True)
    s = np.linalg.svd(Hc, compute_uv=False)
    s2 = s ** 2
    denom = (s2 ** 2).sum()
    if denom <= 1e-300:
        return 0.0
    return float((s2.sum() ** 2) / denom)


def run_synthetic(p=23, hidden=128, epochs=3000, lr=1e-3, weight_decay=1e-3,
                  train_frac=0.3, record_every=25):
    Xtr, ytr, Xte, yte = modular_addition(p, train_frac)
    net = MLP([2 * p, hidden, hidden, p])
    opt = Adam(net, lr=lr)
    hist = []
    for ep in range(epochs):
        loss, gW, gb, prob = net.loss_grad(Xtr, ytr, weight_decay, p)
        opt.step(net, gW, gb)
        if ep % record_every == 0 or ep == epochs - 1:
            # 记录每层（隐藏层）的总激活与有效秩（在训练集上）
            _ = net.forward(Xtr)
            row = {"epoch": ep, "loss": float(loss),
                   "train_acc": float((prob.argmax(1) == ytr).mean())}
            for li, H in enumerate(net.cache["acts"][1:], start=1):
                row[f"S{li}"] = float(np.abs(H).sum(axis=1).mean())
                row[f"r{li}"] = eff_rank(H)
            # 测试集精度
            logits = net.forward(Xte)
            row["test_acc"] = float((logits.argmax(1) == yte).mean())
            hist.append(row)
    return hist


def analyse(hist):
    """检验：ΔS 与 Δr 是否同号（逐层、逐记录点）。"""
    layers = sorted({k for row in hist for k in row if k.startswith("S")})
    out = {"sign_agreement": {}, "spearman": {}, "threshold_shape": {}, "n_pairs": {}}
    pairs = []
    for L in layers:
        rk = "r" + L[1:]
        dS, dr = [], []
        for i in range(1, len(hist)):
            dS.append(hist[i][L] - hist[i - 1][L])
            dr.append(hist[i][rk] - hist[i - 1][rk])
        dS, dr = np.array(dS), np.array(dr)
        if len(dS) < 3:
            continue
        agree = float(np.mean(np.sign(dS) == np.sign(dr)))
        # Spearman（秩相关），手算以避免 scipy 依赖
        def rank(a):
            order = a.argsort()
            r = np.empty_like(order, dtype=float)
            r[order] = np.arange(len(a))
            return r
        rs = np.corrcoef(rank(dS), rank(dr))[0, 1]
        out["sign_agreement"][L] = round(agree, 3)
        out["spearman"][L] = round(float(rs), 3)
        out["n_pairs"][L] = int(len(dS))
        for a, b in zip(dS, dr):
            pairs.append((hist[0][L] if False else None, a, b))
    # 阈值形状：按 S 的水平分箱，看平均 Δr
    allS, allDr = [], []
    for i in range(1, len(hist)):
        for L in layers:
            rk = "r" + L[1:]
            allS.append((hist[i][L] + hist[i - 1][L]) / 2)
            allDr.append(hist[i][rk] - hist[i - 1][rk])
    allS, allDr = np.array(allS), np.array(allDr)
    if len(allS) >= 10:
        qs = np.quantile(allS, [0, 1 / 3, 2 / 3, 1.0])
        bins = []
        for j in range(3):
            m = (allS >= qs[j]) & (allS < qs[j + 1] + (1e-9 if j == 2 else 0))
            if m.sum() > 0:
                bins.append({"S_range": [round(float(qs[j]), 4), round(float(qs[j + 1]), 4)],
                             "mean_delta_r": round(float(allDr[m].mean()), 5),
                             "n": int(m.sum())})
        out["threshold_shape"] = bins
    return out


# ================================================================ HF hook 模式
HF_PROBE = r'''
# 以下代码需要在装有 torch + transformers 且可访问 HuggingFace 的环境中运行：
#   python analysis/llm_activation_probe.py --hf gpt2
# 本机（书籍构建环境）无 torch/transformers 且 HuggingFace 不可达，故未运行。
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

def hf_probe(model_id, texts):
    tok = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForCausalLM.from_pretrained(model_id, output_hidden_states=True)
    model.eval()
    acts = {}
    def hook(name):
        def fn(module, inp, out):
            h = out[0] if isinstance(out, tuple) else out
            acts[name] = h.detach().float()
        return fn
    handles = [blk.register_forward_hook(hook(f"blk{i}"))
               for i, blk in enumerate(model.transformer.h if hasattr(model, "transformer")
                                        else model.model.layers)]
    stats = []
    with torch.no_grad():
        for t in texts:
            ids = tok(t, return_tensors="pt").input_ids
            model(ids)
            row = {}
            for name, h in acts.items():
                H = h.reshape(-1, h.shape[-1]).numpy()
                S = float(abs(H).sum(axis=1).mean())
                Hc = H - H.mean(axis=0, keepdims=True)
                s = np.linalg.svd(Hc, compute_uv=False) ** 2
                row[name] = {"S": S, "eff_rank": float((s.sum()**2)/((s**2).sum()+1e-30))}
            stats.append(row)
    for h in handles:
        h.remove()
    return stats
'''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hf", default="", help="HuggingFace 模型 id（需 torch/transformers/网络）")
    ap.add_argument("--out", default=os.path.join(RES, "llm_activation_probe.json"))
    args = ap.parse_args()

    if args.hf:
        print("=" * 64)
        print("[HF 模式] 需要 torch + transformers + HuggingFace 可访问。")
        try:
            import torch  # noqa
            import transformers  # noqa
            print("检测到 torch/transformers；请把 HF_PROBE 中的 hf_probe 接入流程。")
            print("（本脚本出于诚实性未在此环境伪造结果。）")
        except Exception as e:
            print("依赖缺失，未运行：", e)
        print("=" * 64)

    hist = run_synthetic()
    analysis = analyse(hist)
    os.makedirs(RES, exist_ok=True)

    # 汇总：末态与判据
    final = hist[-1]
    layers = sorted({k for k in final if k.startswith("S")}, key=lambda x: int(x[1:]))
    summary = {
        "mode": "synthetic (numpy MLP on modular addition; NOT a public LLM)",
        "params": {"task": "modular_add p=23", "hidden": 128, "epochs": len(hist) * 25,
                   "weight_decay": 1e-3, "optimizer": "Adam lr=1e-3", "train_frac": 0.3},
        "final": {"loss": final["loss"], "train_acc": final["train_acc"], "test_acc": final["test_acc"],
                  **{f"S{L}": final[L] for L in layers},
                  **{f"r{L}": final["r" + L[1:]] for L in layers}},
        "analysis": analysis,
        "law": "prediction: sign(dS) == sign(dr) if the activation-rank coupling holds",
        "verdict": None,
        "limitation": "本实验是合成 MLP，不是公开 LLM；HF 模式因环境限制未运行。",
    }
    ag = list(analysis["sign_agreement"].values())
    sp = list(analysis["spearman"].values())
    if ag:
        mean_ag = float(np.mean(ag))
        mean_sp = float(np.mean(sp))
        supported = [L for L, v in analysis["sign_agreement"].items()
                     if v >= 0.65 and analysis["spearman"][L] > 0.2]
        refuted = [L for L, v in analysis["sign_agreement"].items()
                   if v <= 0.45 or analysis["spearman"][L] < -0.2]
        if len(supported) == len(ag):
            verdict = "支持（弱）：所有层的激活变化与有效秩变化同号率显著高于随机"
        elif len(refuted) == len(ag):
            verdict = "反例：激活—秩耦合在本次训练中不成立"
        elif supported and refuted:
            verdict = ("混合：层 " + ",".join(supported) + " 支持耦合，层 "
                       + ",".join(refuted) + " 不支持；假说按层分裂")
        else:
            verdict = "不确定：同号率接近随机，假说未被检验支持"
        summary["verdict"] = verdict
        summary["layers_supported"] = supported
        summary["layers_refuted"] = refuted
        summary["mean_sign_agreement"] = round(mean_ag, 3)
        summary["mean_spearman"] = round(mean_sp, 3)

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump({"summary": summary, "history": hist}, f, ensure_ascii=False, indent=2)

    # 图（若 matplotlib 可用）
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        os.makedirs(CHARTS, exist_ok=True)
        xs = [h["epoch"] for h in hist]
        fig, ax = plt.subplots(1, 3, figsize=(10.5, 3.0), layout="constrained")
        for L in layers:
            ax[0].plot(xs, [h[L] for h in hist], label=f"layer {L}")
            ax[1].plot(xs, [h["r" + L[1:]] for h in hist], label=f"layer {L}")
        ax[0].set_title("total activation S"); ax[0].set_xlabel("epoch"); ax[0].legend(fontsize=7)
        ax[1].set_title("effective rank r"); ax[1].set_xlabel("epoch"); ax[1].legend(fontsize=7)
        ax[2].plot(xs, [h["train_acc"] for h in hist], label="train")
        ax[2].plot(xs, [h["test_acc"] for h in hist], label="test")
        ax[2].set_title("accuracy"); ax[2].set_xlabel("epoch"); ax[2].legend(fontsize=7)
        fig.savefig(os.path.join(CHARTS, "llm_activation_probe.png"), dpi=200)
        print("[fig]", os.path.join(CHARTS, "llm_activation_probe.png"))
    except Exception as e:
        print("[fig] 跳过：", e)

    print("=== 工程验证：LLM 激活探针（合成 MLP）===")
    print("末态 loss=%.4f  train=%.3f  test=%.3f" % (final["loss"], final["train_acc"], final["test_acc"]))
    for L in layers:
        print(f"  层 {L}: S={final[L]:.3f}  r={final['r'+L[1:]]:.3f}  "
              f"同号率={analysis['sign_agreement'].get(L)}  ρ={analysis['spearman'].get(L)}")
    print("阈值形状（按 S 分箱的平均 Δr）：", analysis.get("threshold_shape"))
    print("判定：", summary["verdict"])
    print("[done]", args.out)


if __name__ == "__main__":
    main()
