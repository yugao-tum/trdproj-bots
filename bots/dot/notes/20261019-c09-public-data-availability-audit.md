# C09：公开历史数据确有文件，但仍未取得可执行收益样本

访问与核验：2026-10-19 UTC。本轮为数据可用性审计，新增机制 0、策略回测 0、自测净收益 null。

## 核验结果

1. [aidaman 原始仓库](https://github.com/aidaman01/prediction-markets/tree/dc6b596eea2cd307f1c9c8d4e6fcd1869a02c7a2)：已将提交 dc6b596… 与树 a20d34b… 的目录逐项对齐；公开累计损益 CSV 确有 2,092 行，1×、2× 成本各 1,046 行，但只有 costs/bet/cum_pnl 三列。另有 30,666 个市场 ID；两者没有事件映射、入场盘口或费用明细。未截断目录不含原始 data/，.gitignore 明示排除该目录。故不能独立重建其 832 个事件或检验可执行性。来源 +0.17¢ 已扣其基础成本，本轮没有重复扣费或复算收益。

2. [Marketlens 七组免费样本](https://github.com/marketlenstrade/polymarket-historical-data/tree/6eb9b8efda545eddafb2a8f75acb4bcbca6db019)：已将提交 6eb9b8… 与树 f0b1fad… 的目录逐项对齐。完整读取全部 2,278 条 markets.csv 记录，七个文件字节均匹配 Git blob 哈希。按事先固定、以所附 close_time 为条件的代理筛选 data_start≤close_time−168h≤data_end，合格行数为 0；最大的 close_time−data_start 是 Apple 的 165.804h，不能称为采集窗口持续时长。close_time 尚非已核验的事前计划结束时间，因此 0 行只适用于该元数据代理，不能推出真实事前 T−7d 一定没有数据；事前日程版本缺口仍在。不能为了得到回报而把 T−7d 改成开盘。571 个事件标签也不代表独立事件数。此外，Counter-Strike 的 29 行 winning_outcome 字段明确写成双边 0.5/0.5 兑付，不能强行编码为 0/1 胜负；这只是已核对的文件字段，不等于本轮独立核实最终兑付。

3. [Dinesh 订单簿数据](https://github.com/DineshKumar8399/polymarket-orderbook-dataset)：已实际下载并核对 SHA-256 的 labels.parquet 为 743,684 字节，首日报价分区为 804,193 字节。独立读取文件 footer 后，标签表声明 187,094 行、仅 slug/y/source；报价表声明 783,350 行，只有时间、slug、类别、bid/ask/mid/spread、volume24hr、segment。未解码任何记录页。这些字段缺少互补侧 token/盘口、深度、历史费用、成交证据、计划结束时间和最终结算证据。作者还披露标签截尾、推断标签偏差和观察名单选择偏差；不能因 source=api 就认定最终结算已核实。

4. [Pancake 历史数据](https://github.com/usepancake/polymarket-history/tree/356b59b01ae74cc558ae75d8dcf4b7971be5a509)：实际下载 65,897 字节的 2024-11 结算文件，SHA-256 匹配清单；footer 声明 258 行及结算证据相关字段，但未逐行验证。README 明确不提供 quotes/book_l2，trades 为合成末价观察，不能当作实际成交或买入 ask。

## 裁决

已证实“存在可下载文件”，尚未证实“本规则有 ≥30 个独立、结算和执行均可核验的历史事件”。C09 维持不确定、不晋级；既未证盈利，也未否定机制。买入对象仍是任意低价侧 L 的互补侧，实际 NO ask 不能写成 1−YES ask；ask 已包含的价差不再重复扣除。

本轮只运行自行编写的目录/时间覆盖/文件元数据检查，没有运行下载的策略代码、计算 P&L、开设账户或使用密钥。X 定向查询仅找到相关索引线索，原帖访问 403 后停止，未作为已读原文或收益证据。上述数据文件不随本说明再分发。

