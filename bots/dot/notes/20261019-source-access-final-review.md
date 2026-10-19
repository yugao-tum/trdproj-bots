# 公开来源补查：读到了什么，仍缺什么

统计截至 2026-10-19 22:15 UTC；此后收尾查询单独保留，不回填本页统计。以下仅补充既有研究，新增机制、回测及盈利验证均为 0。

## 实际 GitHub / X 检索

21:04–22:15 UTC 分批执行了 19 次公开搜索调用，保存 24 个不同查询字符串：9 个针对 GitHub，15 个针对 X。其中 11 次调用返回空结果。混合批量响应不能逐条归属命中，因此不把查询数等同于有效来源数。

GitHub 另有 13 次文件或元数据读取：6 份实质文档/源码返回完整文件文本，并复算匹配 Git blob；7 份为目录、标签、manifest 或 Git LFS 指针。后者只证明版本或载荷声明，不计正文或已解码数据。该组读取没有失败响应。

X 没有新增可核验原帖正文。返回内容主要为空结果、Grok/trending 摘要及非帖子页面；定向查询也会返回无关内容。搜索摘要和代码搜索片段只用于发现，没有冒充全文。空结果不证明相关内容不存在，也不证明平台全站搜索完整。

## 来源账本的计数边界

历史 304 个来源记录组保留原口径，其中含既有 API 分类，未按本轮规则全部重审；不与新口径硬加成一个正文总数。

本轮对已保存证据及新增读取，核验出 75 个新增版本化文档/代码正文组：39 组文件文本匹配 Git blob 或树记录，17 组返回全部工具提取网页行，7 组返回文件文本但没有外部 blob 匹配，1 组为完整保存的 OpenAPI 文档，11 组仅有选定正文段落。

折叠 GitHub 文件版本后为 59 个 URL 家族；再归并同一 Binance 文章的地区版本后为 58 个文件/文章家族。这些不是独立事件、样本或盈利证据。52 个新增组有保存的 20:02:02 UTC 后请求或读取时间依据，23 个没有该精确时段支持，不能全部称作此后抓取。

X 保留历史 11 个原帖正文/部分正文 URL，新增为 0。原有搜索统计不被本轮查询字符串直接改写；API/RPC 返回、下载数据、LFS 指针和失败探针均另列，不加入新正文组。

## 两个实质发现

- [ForesightFlow DATASHEET](https://github.com/ForesightFlow/datasets/blob/032729a5f6ca93feed87e5d6e28a37b4de300753/polymarket-resolution-typology/DATASHEET.md) 明示没有附带价格或逐笔成交，零成交计数仅代表本地未采集，也没有独立标注留出集。两份 LFS 载荷本轮未下载、未解码，声明行数不能当作已验证交易样本
- [Polymarket 固定提交处理器](https://github.com/Polymarket/resolution-subgraph/blob/75d1818547862a5bd3477ed2e6b16f693d42dab6/src/optimistic-oracle-v-2.ts#L10-L36) 的首次 proposed→challenged 分支不设置 wasDisputed=true；[当前实体 schema](https://github.com/Polymarket/resolution-subgraph/blob/75d1818547862a5bd3477ed2e6b16f693d42dab6/schema.graphql#L1-L16) 也不能替代逐代现金账。这只说明该提交的源码语义，未证明部署版本或 Gamma/Fidonis 使用此实现

以上是访问与数据限制核查，不是新增收益结果。本轮来源检查未登录、付费或执行外部源码。
