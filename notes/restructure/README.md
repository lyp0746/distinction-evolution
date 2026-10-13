# 重构脚本（一次性，仅供存档）

这三个脚本执行了从"硬核先行 26 章"到"质疑→方法→样板→构造→兑现→边界 22 章"的重构。

**警告：不可再次运行。** 它们假定 `source/` 处于重构前的旧章号状态；对已重构的
`source/` 再跑一遍会二次置换（章号是一个 11-循环置换），破坏正文。

- `restructure_renumber.py` — 把"正文顺序 = 文件序号 = 章号"规范化，并重写全部跨引用。
- `restructure_parts.py` — 按新顺序重生成 `source/parts.json`。
- `restructure_appendix_k.py` — 把原 ch24（计算）与 ch25（学习）合并为附录 K。

重构后的改动已记录在 `versions/CHANGELOG.md`（内部，不进发布包）。
