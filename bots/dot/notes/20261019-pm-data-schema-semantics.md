# C09 / C38：公开数据与状态语义补充

证据读取：2026-10-19 21:04–21:20 UTC。范围仅为既有 C09、C38 的数据可用性与源码语义核查，不改变交易规则、机制数量、样本门槛或回测数量。仅静态阅读源码，不新增链上状态或收益验证。

## C09：市场总数不能替代可执行历史样本

ForesightFlow 的 resolution-typology v1 README 声称覆盖 911,237 个市场，截止 2026-04-27；其中 853,774 个（约 93.7%）为 unclassifiable，deadline_resolved 为 56,318，event_resolved 为 1,145。这些是发布方 README 的统计，本次没有下载并独立复算原始数据。

公开 schema 提供 market_id、规则文本、分类、结果、累计成交量及创建/关闭/结算时间，另有 n_trades_in_db 字段表示发布方数据库中的成交记录数量。这个数字字段本身并不包含对应逐笔成交，更不提供下单时买卖报价、可成交深度、价差、实际成交或撤单。因而可作为市场分类与后续连接的线索；不能直接提升为可执行报价样本、无前视收益数据或已验证策略结果。大量未分类记录也不能直接并入特定机制的有效样本分母。

原始来源：[resolution-typology README](https://github.com/ForesightFlow/datasets/blob/032729a5f6ca93feed87e5d6e28a37b4de300753/polymarket-resolution-typology/README.md)。本次完整返回文本的 Git blob SHA-1：f1cc5afe8e53c2b7866c17a9358cea828c186f76。原始读取使用可变 main；随后已核对标签引用与固定提交目录，确认同一 blob 属于版本 1.0、标签 polymarket-resolution-typology-v1、提交 032729a5f6ca93feed87e5d6e28a37b4de300753。MANIFEST 的 released=2026-04-28，cutoff=2026-04-27T00:00:00Z；这只是版本定位，不是底层数据验证。

进一步读取同一版本的 [DATASHEET](https://github.com/ForesightFlow/datasets/blob/032729a5f6ca93feed87e5d6e28a37b4de300753/polymarket-resolution-typology/DATASHEET.md) 后，发布方直接确认：不附带价格或逐笔成交；n_trades_in_db=0 只表示其本地未采集，不能据此说市场没有交易。分类没有独立人工标注的留出验证集，标签应作为筛选线索而非真实标签。

数据目录中的 JSONL.gz 与 Parquet Git blobs 经读取、复算后，确实只是 133 与 134 字节的 Git LFS 指针。它们指向 94,493,132 与 160,014,262 字节载荷，OID 与大小匹配发布方 [MANIFEST](https://github.com/ForesightFlow/datasets/blob/032729a5f6ca93feed87e5d6e28a37b4de300753/polymarket-resolution-typology/MANIFEST.json)。本次未下载这些大载荷、未解码任何数据行；指针与目录访问不计为数据正文验证，也不据此断言大载荷不可访问。

MANIFEST 原始字段（仅复述发布方声明）：

- data/typology-v1.jsonl.gz：sha256=d24b6846cf52866cb026d69b3ce0a48ee40bf7d05cfce8dac5e98c20815d7b81，size_bytes=94493132，n_lines=911237
- data/typology-v1.parquet：sha256=7e695c6c34708bd8abefb94d95160f02b1d200e495c39dbc8a502ccd31e20739，size_bytes=160014262，n_rows=911237

DATASHEET 与 MANIFEST 的 Git blob SHA-1 分别为 f66ece736b5b2bb4fb9c4aebb7b83cc321874471、b6a51772412f12d1c87190e7cbd8ae16d52bfef2，均按返回文本复算匹配，并与固定提交目录一致。

## C38：wasDisputed 不等于所有 DisputePrice 事件

在 Polymarket/resolution-subgraph 的明确提交 75d1818547862a5bd3477ed2e6b16f693d42dab6 中，两份处理器对已存在且 requester 合法的实体采用同样的分支：

- 当状态为 proposed，handleDisputePrice 将其改为 challenged；此分支没有把 wasDisputed 设为 true
- 当状态为 reproposed，才改为 disputed 并设 wasDisputed=true
- 处理器按 ancillaryData 的 keccak 哈希加载同一个 MarketResolution；handleRequestPrice 会覆写该实体的 transactionHash 与 logIndex

因此，不能把此版本的 wasDisputed 机械替代“发生过任何 DisputePrice”，也不能把一个不断更新的最终实体当作所有请求代际的完整历史。

schema 确实有 author，另有 Moderator / Revision 实体；但 MarketResolution 不保存逐争议 proposer/disputer、保证金、final fee、奖励、支付现金流或锁定/认领资本字段。仅凭这些实体不能重建 C38 逐代净现金账。仍需连接原始请求身份、各代生命周期、真实转账与费用，并区分返还本金和收入。

可逐行核验的原始来源：

- [OOv2 handleDisputePrice，第 10–36 行](https://github.com/Polymarket/resolution-subgraph/blob/75d1818547862a5bd3477ed2e6b16f693d42dab6/src/optimistic-oracle-v-2.ts#L10-L36)
- [Managed OOv2 handleDisputePrice，第 10–35 行](https://github.com/Polymarket/resolution-subgraph/blob/75d1818547862a5bd3477ed2e6b16f693d42dab6/src/managed-oo-v2.ts#L10-L35)
- [MarketResolution schema，第 1–16 行](https://github.com/Polymarket/resolution-subgraph/blob/75d1818547862a5bd3477ed2e6b16f693d42dab6/schema.graphql#L1-L16)
- [OOv2 handleRequestPrice，第 69–88 行](https://github.com/Polymarket/resolution-subgraph/blob/75d1818547862a5bd3477ed2e6b16f693d42dab6/src/optimistic-oracle-v-2.ts#L69-L88)

三份完整源码的 Git blob 均已复算匹配，且经过独立复读。这里只验证这个提交的静态源码语义，未证明任何时期的实际部署版本、已处理的事件完整性，尤其未证明 Gamma 或 Fidonis 使用此实现。因此不能据此直接改写它们已有统计，也不能断言其统计错误。

## 搜索深度边界

补充 GitHub/X 搜索用于发现来源。索引摘要、X trending/Grok 摘要、个人主页、登录/搜索页和无关体育用品账号均不视为原始 X 帖子正文。当前这轮补充没有新增可计入的原始 X 帖子正文，也没有新增盈利证据。
