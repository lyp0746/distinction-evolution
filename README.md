# 区分的演化
### 从图论硬核到统一纲领：公理框架、可复现结果与限度宣言

> **The Evolution of Distinction** — From a Graph-Theoretic Hard Core to a Program for Unification: Axioms, Reproducible Results, and a Declaration of Limits

李毅芃　著　·　2026　·　CC BY 4.0

---

## 这本书在做什么

把"抽象统摄具体"写成可操作的方法（**压缩**），把它实现为一个形式框架（**演化区分系统**，EDS），在有限图上给出一个**完整、严格、可复现**的相变定理，并公开挂出一个**未解决的缺口**——分离曲率与 Gauss–Bonnet 定理之间的因子 **1/3**——作为可攻击的研究目标。

**一句话：** 它严格地解决了一个小问题，诚实地提出了一个大问题。

## 核心主张（分级）

| 层 | 内容 | 强度 | 位置 |
|---|---|---|---|
| 硬核 | 图上的两阶段相变定理，可证明、可计算、可复现 | **定理（A／甲）** | 第 12—15 章 |
| 统一语言 | 十余个领域可写成同一套"区分—观测—曲率—演化"语言 | 框架（B／乙） | 第 19—20 章 |
| 生成纲领 | 1/3 缺口、连续时间涌现、高维推广 | 纲领（C／丙） | 第 16—18、22 章 |

## 硬核长什么样

在有限连通图 `G` 上，区分强度按 `Ḋ = (−αI + βL)D` 演化（`L` 为拉普拉斯矩阵）。两个临界耦合为

```
β₁ = α / λₙ      （最高频/局部模式先解锁）
β₂ = α / λ₂      （Fiedler/全局模式后解锁）
```

Petersen 图：`(0.200, 0.500)`；环 `C₁₀`：`(0.250, 2.618)`；完全图无中间相。**所有数字可用随书脚本复算。**

## 快速开始

```bash
# 1) 复现第四部分数值（协议 V1）
python analysis/graph_phase_transition.py

# 2) 生成插图与封面
python analysis/make_figures.py && python analysis/make_cover.py

# 3) 构建全部版本：印刷 PDF / 电子阅读 PDF / EPUB / HTML / Markdown
bash scripts/build.sh

# 4) 质量门禁
bash scripts/validate.sh

# 5) 组装发布包
bash scripts/release.sh
```

依赖：Python（numpy、scipy、lxml、pypdf、bs4）、Chrome/Edge（PDF 打印）。

## 目录结构

```
distinction-evolution/
├── source/              # 唯一权威正文来源（HTML）
│   ├── book.json        # 书名/作者/日期/摘要（单一来源）
│   ├── parts.json       # 部分 → 章 → 节
│   ├── ch01.html … ch22.html
│   ├── front_*.html / back_*.html
│   └── appendix_*.html
├── analysis/            # 数值复现、插图、PCA、敏感性、校对、登记核销
├── assets/{css,svg}/    # 版式与矢量插图
├── docs/                # 方法论、数据来源、缺口、贡献指南、preregistration/
├── scripts/             # build / validate / release / per-artifact release
└── output/, release/    # 派生产物（gitignored）
```

## 可证伪性

本书最重要的部分之一是**可证伪登记簿**（附录 E 与 `docs/preregistration/`）：每一条可反驳命题都写明了证伪条件与核验日期，且账本**只追加、不修改**。欢迎按此纪律提交复现、缺口填补或反驳。

## 引用

```bibtex
@book{li2026distinction,
  title     = {区分的演化：演化区分系统——公理化、图上硬核与统一纲领},
  author    = {李毅芃},
  year      = {2026},
  publisher = {GitHub},
  note      = {CC BY 4.0},
  url       = {https://github.com/lyp0746/distinction-evolution}
}
```

## 许可

- 正文：**CC BY 4.0**
- 代码与脚本：**MIT**
