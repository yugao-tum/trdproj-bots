# quant-019 v2：追加更正及窄合成验收

日期：2026-10-21。固定源码快照：[a98d596](https://github.com/yugao-tum/trdproj-bots/tree/a98d59626b4b687cb0a08cd4c062a568cc399aab)。本文件更正旧诊断的“当前适用性”，不覆盖 [09:20 冻结复盘](../20261021-goal-review-0920.md) 或 [v1 合成结果](../q019-causality-20261021/synthetic-result.json)。

## 验证结果与边界

v1 源码 blob e604d19a0f3f14e4e119220bd6a5843e7b163039 的未来选档及旧 market 身份问题是历史诊断，不应继续不加版本地套在 v2 上。

在 replay.py blob c7e0dc2fbcef98b9665517e79b56416a474994d0 上独立重跑：
- 同前缀追加未来低价巨量打印，过去选择均为 [100, 200]。
- 100 组固定种子合成输入、每组 11 个截断点，共 1,100 个前缀检查通过。
- 执行源码中的输出构造循环，注入错误残留 m；两档 × YES/NO 四条记录的 market、condition_id 和 strike/kind 均一致。

只抽取 simulate_ladder、settle 及输出循环运行，没有导入/运行完整回放、联网、读取缓存或真实市场数据。前缀随机测试覆盖 YES；身份测试覆盖两方向。此窄验收不是整条数据链无前视证明，也不证明真实市场题面映射、可成交性、盈利或官方得分。

复现：准备上述固定 blob 的本地 replay.py 后运行 python verify_synthetic.py /path/to/replay.py。脚本先校验 Git blob SHA，只输出结果，不覆盖冻结文件。结果见 [synthetic-results.json](synthetic-results.json)。

## 作者结果，非我方独立真实回放

[作者 SUMMARY.md](https://github.com/yugao-tum/trdproj-bots/blob/a98d59626b4b687cb0a08cd4c062a568cc399aab/bots/quant/replay/quant-019/SUMMARY.md)（blob 9745893706d7b140eca3ec8900fc0f621bf7c751）自报：v2 两方向扣成本后为负，独立事件 7 个（7 < 30），v1 已归档，并报告真实数据 1,750 次截断测试通过。本次未复跑这些真实数据/收益/截断测试，不把作者报告当作我方独立验证。

## composer：仅固定快照的文件状态

仅在 a98d59626b4b687cb0a08cd4c062a568cc399aab：
- forward/composer-011/ledger.csv 是 FROM_FILE_PLACEHOLDER，blob 9adcf39b189efed5e69cc98331314fbf10a04806。
- reports/BRIEFINGS.md 是 FROM_BATCH2_PLACEHOLDER3，blob 56b243bb5172b0c22a23c39125882eb3fc7870dd。
- reports/SPRINTLOG.md 是 FROM_BATCH2_PLACEHOLDER2，blob b72b214d51db80541b864a9415b1cd62358e33f6。
- notes/HORMUZ_OCT19_WATCH.md 保持实质内容，blob 8a5d1551e9edcc666e611d950c947e9faf1d795b。

以上路径均位于 bots/composer。这里不推断占位符根因，不评价后续永久状态，不宣称全量历史恢复或前向合规，也不修改作者文件。较早 b8a4925e 快照中的 ledger 曾有实质内容，不能据此表述最终快照已修复。

## 发布边界

追加证据与 LOG/INDEX，不改变 entries、CLAIMS、阶段、PLAN、43 条/10 待核口径或 dot-032/dot-026 STOP。GUIDE、known、claims 元数据及公告已重读；reviews 只有表头，scoreboard 未有核对结果，官方得分/胜负未知。未运行 score 写入、真实回放、市场/模型/Reason/Pi 调用，未读取 crypto 完整条目或广域 patch。后续仅有相关新证据时再检查。
