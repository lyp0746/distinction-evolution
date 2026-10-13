# -*- coding: utf-8 -*-
"""
fisher_curvature.py — 方向“学习的几何”：Fisher 信息与能力涌现。

想法（C 级假说）：神经网络的“能力涌现”（记忆化、grokking）是否对应参数空间中
某个曲率量（Fisher 信息迹 / Hessian 顶特征值）的相变？

本脚本在模加法任务上训练 NumPy MLP，逐 epoch 记录：
  * train/test 精度；
  * Fisher 信息迹 F = E[||∇_θ log p(y|x)||²]（Gauss–Newton 曲率的迹的近似）；
  * Hessian 顶特征值的幂迭代估计 λ_max。

然后检测：F 或 λ_max 是否在精度跃迁处出现可辨识的转折（峰值/拐点）。

诚实声明：本实验是合成 MLP，不是公开 LLM；结论至多为“机制提示”。
输出：analysis/results/fisher_curvature.json
依赖：numpy。
"""
import argparse
import json
import os
import sys

import numpy as np

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(HERE, "analysis", "results")
SEED = 0


def modular_addition(p, train_frac=0.3, seed=SEED):
    rng = np.random.default_rng(seed)
    pairs = np.array([(a, b) for a in range(p) for b in range(p)])
    labels = (pairs[:, 0] + pairs[:, 1]) % p
    idx = rng.permutation(len(pairs))
    n_tr = int(len(pairs) * train_frac)
    X = np.zeros((len(pairs), 2 * p))
    X[np.arange(len(pairs)), pairs[:, 0]] = 1
    X[np.arange(len(pairs)), p + pairs[:, 1]] = 1
    return X[idx[:n_tr]], labels[idx[:n_tr]], X[idx[n_tr:]], labels[idx[n_tr:]]


class Net:
    def __init__(self, sizes, seed=SEED):
        rng = np.random.default_rng(seed)
        self.W = [rng.standard_normal((sizes[i], sizes[i + 1])) * np.sqrt(2.0 / sizes[i])
                  for i in range(len(sizes) - 1)]
        self.b = [np.zeros(sizes[i + 1]) for i in range(len(sizes) - 1)]
        self.cache = {}

    def forward(self, X):
        acts = [X]
        pre = []
        H = X
        for i in range(len(self.W) - 1):
            Z = H @ self.W[i] + self.b[i]
            pre.append(Z)
            H = np.maximum(Z, 0.0)
            acts.append(H)
        logits = H @ self.W[-1] + self.b[-1]
        self.cache = {"acts": acts, "pre": pre}
        return logits

    def loss_grad(self, X, y, wd):
        logits = self.forward(X)
        z = logits - logits.max(1, keepdims=True)
        ex = np.exp(z)
        prob = ex / ex.sum(1, keepdims=True)
        n = len(y)
        loss = -np.log(prob[np.arange(n), y] + 1e-12).mean()
        loss += 0.5 * wd * sum((W ** 2).sum() for W in self.W)
        d = prob.copy()
        d[np.arange(n), y] -= 1.0
        d /= n
        gW = [None] * len(self.W)
        gb = [None] * len(self.b)
        delta = d
        for i in range(len(self.W) - 1, -1, -1):
            gW[i] = self.cache["acts"][i].T @ delta + wd * self.W[i]
            gb[i] = delta.sum(0)
            if i > 0:
                delta = (delta @ self.W[i].T) * (self.cache["pre"][i - 1] > 0)
        return loss, gW, gb, prob


class Adam:
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
            self.mb[i] = self.b1 * self.mb[i] + (1 - self.b1) * gb[i]
            self.vb[i] = self.b2 * self.vb[i] + (1 - self.b2) * gb[i] ** 2
            mh = self.mW[i] / (1 - self.b1 ** self.t)
            vh = self.vW[i] / (1 - self.b2 ** self.t)
            net.W[i] -= self.lr * mh / (np.sqrt(vh) + self.eps)
            mh = self.mb[i] / (1 - self.b1 ** self.t)
            vh = self.vb[i] / (1 - self.b2 ** self.t)
            net.b[i] -= self.lr * mh / (np.sqrt(vh) + self.eps)


def fisher_trace(net, X, y):
    """Fisher 迹的 Monte-Carlo 估计：E[||∇_θ log p(y|x)||²]。"""
    logits = net.forward(X)
    z = logits - logits.max(1, keepdims=True)
    p = np.exp(z) / np.exp(z).sum(1, keepdims=True)
    n = len(y)
    # 逐样本梯度平方和
    total = 0.0
    for i in range(n):
        d = p[i].copy()
        d[y[i]] -= 1.0
        # 回传
        delta = d[None, :]
        for j in range(len(net.W) - 1, -1, -1):
            Hprev = net.cache["acts"][j][i:i + 1]
            gW = Hprev.T @ delta
            gb = delta.sum(0)
            total += float((gW ** 2).sum() + (gb ** 2).sum())
            if j > 0:
                delta = (delta @ net.W[j].T) * (net.cache["pre"][j - 1][i:i + 1] > 0)
    return total / n


def hessian_top(net, X, y, wd, iters=15, seed=SEED):
    """Hessian 顶特征值的幂迭代（用有限差分 Hessian-向量积）。"""
    rng = np.random.default_rng(seed)
    def flat_grad():
        _, gW, gb, _ = net.loss_grad(X, y, wd)
        return np.concatenate([g.ravel() for g in gW] + [g.ravel() for g in gb])
    v = rng.standard_normal(flat_grad().shape[0])
    v /= np.linalg.norm(v) + 1e-12
    eig = 0.0
    for _ in range(iters):
        base = flat_grad()
        # 保存参数
        saveW = [W.copy() for W in net.W]
        saveb = [b.copy() for b in net.b]
        eps = 1e-4
        k = 0
        for i in range(len(net.W)):
            nW = net.W[i].size
            net.W[i] = net.W[i] + eps * v[k:k + nW].reshape(net.W[i].shape)
            k += nW
        for i in range(len(net.b)):
            nb = net.b[i].size
            net.b[i] = net.b[i] + eps * v[k:k + nb].reshape(net.b[i].shape)
            k += nb
        gp = flat_grad()
        for i in range(len(net.W)):
            net.W[i] = saveW[i]
        for i in range(len(net.b)):
            net.b[i] = saveb[i]
        Hv = (gp - base) / eps
        eig = float(v @ Hv)
        nv = np.linalg.norm(Hv)
        if nv < 1e-12:
            break
        v = Hv / nv
    return eig


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--p", type=int, default=23)
    ap.add_argument("--epochs", type=int, default=3000)
    ap.add_argument("--every", type=int, default=50)
    args = ap.parse_args()

    Xtr, ytr, Xte, yte = modular_addition(args.p)
    net = Net([2 * args.p, 128, 128, args.p])
    opt = Adam(net, lr=1e-3)
    hist = []
    for ep in range(args.epochs):
        loss, gW, gb, prob = net.loss_grad(Xtr, ytr, 1e-3)
        opt.step(net, gW, gb)
        if ep % args.every == 0 or ep == args.epochs - 1:
            acc_tr = float((prob.argmax(1) == ytr).mean())
            logits = net.forward(Xte)
            acc_te = float((logits.argmax(1) == yte).mean())
            F = fisher_trace(net, Xtr, ytr)
            hist.append({"epoch": ep, "loss": float(loss), "train": acc_tr, "test": acc_te,
                         "fisher": F, "hess_top": hessian_top(net, Xtr, ytr, 1e-3)})
    os.makedirs(RES, exist_ok=True)

    # 能力跃迁：train 精度从 <0.5 到 >0.9 的 epoch
    jump = next((h["epoch"] for h in hist if h["train"] > 0.9), None)
    F = np.array([h["fisher"] for h in hist])
    H = np.array([h["hess_top"] for h in hist])
    eps = np.array([h["epoch"] for h in hist])
    # Fisher 峰值位置
    Fpeak = eps[int(np.argmax(F))]
    Hpeak = eps[int(np.argmax(H))]
    out = {
        "setup": {"task": f"modular_add p={args.p}", "hidden": 128, "epochs": args.epochs},
        "capability_jump_epoch": jump,
        "fisher_peak_epoch": Fpeak,
        "hess_top_peak_epoch": Hpeak,
        "fisher_at_jump": (float(F[eps == jump][0]) if jump is not None and (eps == jump).any() else None),
        "history": hist,
        "verdict": None,
    }
    if jump is not None:
        # 判定：峰值是否出现在跃迁附近（±2 个记录点）
        near = lambda p: abs(p - jump) <= 2 * args.every
        if near(Fpeak) or near(Hpeak):
            out["verdict"] = "支持（弱）：Fisher/Hessian 峰值出现在能力跃迁附近"
        else:
            out["verdict"] = "不支持：曲率峰值与能力跃迁不同步"
    else:
        out["verdict"] = "未观察到能力跃迁（train 精度未超过 0.9）"
    with open(os.path.join(RES, "fisher_curvature.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2, default=lambda o: float(o))

    print("=== 学习的几何：Fisher 曲率 vs 能力涌现 ===")
    print(f"  能力跃迁 epoch：{jump}")
    print(f"  Fisher 迹峰值 epoch：{Fpeak}；Hessian 顶特征值峰值 epoch：{Hpeak}")
    print(f"  末态：train={hist[-1]['train']:.3f} test={hist[-1]['test']:.3f} "
          f"Fisher={hist[-1]['fisher']:.3e} λmax={hist[-1]['hess_top']:.3e}")
    print(f"  判定：{out['verdict']}")
    print("[done]", os.path.join(RES, "fisher_curvature.json"))


if __name__ == "__main__":
    main()
