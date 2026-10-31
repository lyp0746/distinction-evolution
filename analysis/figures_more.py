# -*- coding: utf-8 -*-
import os, numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
OUT=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),"assets","svg")
plt.rcParams.update({"font.size":9,"axes.grid":True,"grid.alpha":.3,"figure.dpi":120,
 "savefig.bbox":"tight","font.sans-serif":["Microsoft YaHei","SimHei","DejaVu Sans"],"axes.unicode_minus":False})
C=dict(blue="#2b6cb0",red="#b3261e",green="#2f855a",orange="#b7791f",gray="#666")
def save(f,n): f.savefig(os.path.join(OUT,n),format="svg"); plt.close(f); print("wrote",n)

# 1 度数异质性与 R（散点）
import itertools
def lap(n,E):
    A=np.zeros((n,n))
    for u,v in E: A[u,v]=A[v,u]=1
    return np.diag(A.sum(1))-A
def Rof(e):
    nz=e[np.abs(e)>1e-9]; return e[-1]/nz[0] if len(nz)>1 else np.nan
pts=[]
try:
    import networkx as nx
    for n in (8,9,10):
        for G in nx.nonisomorphic_trees(n):
            e=np.linalg.eigvalsh(nx.laplacian_matrix(G).toarray().astype(float))
            deg=np.array(list(dict(G.degree()).values()))
            pts.append((int(deg.max()-deg.min()), Rof(np.sort(e)), n))
except Exception as ex:
    print("skip", ex)
if pts:
    pts=np.array(pts)
    fig,ax=plt.subplots(figsize=(5.4,3.0))
    for n,mk in ((8,"o"),(9,"s"),(10,"^")):
        m=pts[:,2]==n; ax.scatter(pts[m,0],pts[m,1],s=14,marker=mk,alpha=.7,label="n=%d"%n)
    ax.set_xlabel("度极差（度数异质性）"); ax.set_ylabel("R")
    ax.legend(fontsize=8); ax.set_title("图 18.4　树的度数异质性与 R（n≤10 全树）")
    save(fig,"fig-degree-vs-R.svg")

# 2 加权路的 R
def wpath(w):
    n=len(w)+1; L=np.zeros((n,n))
    for i,x in enumerate(w):
        L[i,i]+=x; L[i+1,i+1]+=x; L[i,i+1]-=x; L[i+1,i]-=x
    return L
ws=[1.0,2,5,10,20,50,100]
Rs=[]
for c in ws:
    w=np.ones(9); w[4]=c
    e=np.sort(np.linalg.eigvalsh(wpath(w))); Rs.append(Rof(e))
fig,ax=plt.subplots(figsize=(5.2,3.0))
ax.semilogx(ws,Rs,"o-",color=C["blue"])
ax.set_xlabel("中间边的权重倍数"); ax.set_ylabel("R")
ax.set_title("图 16.3　权重异质性提高则 R 下降（10 点路）")
save(fig,"fig-weighted-path.svg")

# 3 覆盖表分级柱状图
fig,ax=plt.subplots(figsize=(4.6,2.8))
ax.bar(["A","B","C"],[11,18,7],color=[C["green"],C["blue"],C["orange"]])
ax.set_ylabel("条数"); ax.set_title("图 21.2　三十六条覆盖的分级分布")
save(fig,"fig-coverage-grades.svg")

# 4 κ 与 R 的行为对比
ns=np.arange(4,61)
k=np.array([np.var(np.sort(2-2*np.cos(np.pi*np.arange(n)/n))) for n in ns])
R=np.array([(2*(2-2*np.cos(np.pi*(n-1)/n)))/(2-2*np.cos(np.pi/n)) for n in ns])
fig,ax=plt.subplots(figsize=(5.4,3.0))
ax.plot(ns,k,color=C["blue"],label="κ（路径图 P_n）")
ax.plot(ns,np.log10(R)*3,color=C["red"],ls="--",label="log₁₀R×3（同一族）")
ax.set_xlabel("n"); ax.set_ylabel("值"); ax.legend(fontsize=8)
ax.set_title("图 20.3　κ 有界、R 无界（同一族图）")
save(fig,"fig-kappa-vs-R.svg")
print("done")
