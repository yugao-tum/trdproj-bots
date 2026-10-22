---
id: muse-912
name_zh: 结算窗口时滞折价买入（多场所）
name_en: Resolution-Lag Discount Buying (Multi-Venue)
bot: muse
date: 2026-10-20
market: polymarket
pm_category: cross
kind: supplement
improves: dot-004
category: E
return_type: convergence
instruments: 结果已可知的待结算市场获胜方份额/合约（Polymarket YES 份额 + Kalshi Yes 合约）
venues: Polymarket（主）; Kalshi（变体）
data: Polymarket Gamma API（市场规则原文、结算状态，免费免密钥）；结算源公开数据（气象站/比分源）；CLOB data-api 成交（免费，每市场最近约 2 万笔）；Kalshi 公开 API trade-api/v2（markets/trades/orderbook，免密钥）
test_2w: Polymarket 侧：用 Gamma API 扫描近 2 周已结算市场，筛选权威源公布结果早于正式结算的事件，记录可知时刻获胜方**最后成交价**（历史 ask 无公开来源，GUIDE §8），或做前向记录；计算持有至 $1 的净收益。Kalshi 侧：用公开 trades 接口拉过去 4 周已结算日频市场（T0 结果可知时点，T1 结算时点），取 (T0,T1) 区间获胜方吃单成交价相对 $1.00 的折价分布；约 20 个交易日 ≥30 个独立结果（按事件数计）。失败标准：中位数净收益 ≤0，或争议/异常结算率 >10%（PM）；Kalshi 平均折价 <0.5¢ 或扣费后期望为负
status: 待核
confidence: 高
---

> 作者：Muse（2026-10-20 合并：muse-912 + muse-own-predmarket-kalshi-settle-lag；两条同机制，验证复盘判定合并）

## 一句话
在官方结算源已公布结果、但正式结算尚未完成的窗口内（Polymarket/UMA 约 2 小时挑战期、Kalshi 约 3 小时结算窗口），以低于 $1 的折价买入获胜方份额/合约，持有至 $1 结算。

## 钱从哪里来
付钱的是不愿承担结算风险、急于离场的持有者——他们宁愿折价卖出，也不愿把资金锁在结算流程里；以及回避持仓过结算的做市商。这笔钱持续存在的原因是结构性的：
- Polymarket：UMA 乐观预言机要求"提案 + 2 小时挑战期"，每个市场都有这个窗口，而大多数参与者不愿为锁仓和争议风险定价。
- Kalshi：官方口径"大多数市场在结果确定后几小时内结算，通常约三小时"（Alphascope 2026-10-06 核查 Kalshi 官方 FAQ）；CFTC 备案规则写明结算日不晚于到期日次日——等待窗口是制度性的。结果确定后，一部分持有者宁愿以 97–99¢ 卖出获胜合约立刻释放资金，也不愿等约 3 小时拿满 $1.00。

## 规则
只做规则文本完备的市场：结算源、单位、精度、口径四要素齐全，缺一则放弃（fail-closed）。
触发条件（需同时满足）：① 规则指定的权威源已公布结果且出处可追溯；② 获胜方 YES 的 ask ≤ $0.97（PM）；③ 官方源口径与规则文本完全一致。
吃单买入（时滞窗口内挂单常无对手方）。
仓位：PM 单个市场 ≤ $500，总资金 $5000 内多市场分散；Kalshi 单市场 ≤ $800（约 820 张）。
持有至 $1 赎回/结算；若进入争议（PM 为 UMA DVM 投票、Kalshi 为 Market Outcome Review），按 4–6 天锁仓处理，不加仓。
不做规则模糊的市场：措辞有歧义、结算源不唯一，直接放弃。
Kalshi 跳过：结算条款含"官方可能修正数据"且修正窗口未过的市场；组合市场（combo，结算更慢）。

结算机制（据已读来源）：UMA 乐观预言机——提案人提交结果并缴纳保证金（新市场默认 $500 USDC.e，官方文档另有 $750 口径，以链上实时参数为准），2 小时（7200 秒）挑战期内无人争议即结算；首次争议重置并开启新一轮提案，第二轮再被争议则进入 UMA DVM 持币人投票（24 小时承诺期 + 24 小时揭示期），全程约 4–6 天。

## 变体：Kalshi 结算滞后
同一机制、不同场所：Kalshi 日频市场（股指收盘、每日最高温等）+ 月度经济数据市场（CPI、非农）。只做结算条款清晰、指定数据源为公开官方源（BLS、交易所收盘价）的市场。
- 触发：结果已可从官方源独立确认（如 BLS 8:30 公布、美东 16:00 股指收盘），且市场状态仍为未结算（公开 API 查 market status）。
- 建仓：吃单买入获胜方 Yes 合约，买入价 ≤ 98¢；单市场 ≤ $800。
- 持有至 $1.00/张结算；若 12 小时仍未结算，按官方建议检查 rules 是否有更晚的确定窗口，有则继续持有，否则按市价退出。
- 注意：mariokarras 建模指南写的"确定通常需 1 到 12 小时以上"是**组合（combo）市场口径**，不是一般日频市场的日口径，本条不采用；一般窗口以官方"约三小时"为准。
- Settlement Date ≤ Expiration+1（CFTC 备案）：Kalshi 规则文件原文 "The Settlement Date of the Contract shall be no later than the day after the Expiration Date, unless the Market Outcome is under review pursuant to Rule 7.1."（见出处 CFTC 备案 PDF）。
- 费用：Kalshi 吃单费 = 合约数 × 0.07 × 价格 × (1−价格)；97¢ 买入约 0.2¢/张，按 venue 向上取整到 1¢ 取保守值。粗算（假设折价 3¢，待实测）：毛利 3¢ − 吃单费 1¢ − 半价差约 0.5¢ = 净约 1.5¢/张；$800/事件净利约 $12.4。若实测平均折价只有 1¢：净约 −0.5¢/张，策略不成立——这正是检验要回答的。

## 证据
- BroCode Research《Resolution risk is the mispriced variable》（实盘研究机构，2026）：明确描述该交易——"在真实结果与正式结算之间的窗口内，获胜份额仍可能以 $0.93–$0.98 交易"；"权威源已公布结果时，以低于 $1 买入可获得短期回报"。该机构称其天气交易系统仅在"权威源报告结果且出处可追溯、规则匹配"时才允许此交易。（来源自报其系统逻辑，未核实其收益数字）
- 同文风险提示：$0.95 全损一次需约 19 笔 5 美分盈利弥补；Zelenskyy 西装市场（2 亿美元成交）曾按字面规则逆直觉结算。（来源自报案例）
- startpolymarket.com：未争议路径约 2 小时完成；争议后 UMA 投票需 48–96 小时。（摘要）
- Kalshi 折价幅度**暂无公开实测数据**（未查到），本条目不做断言。机制存在性的公开证据：Alphascope（2026-10-06 核查 Kalshi 官方 Market FAQs）：大多数市场在结果确定后几小时内结算，通常约三小时；收盘、确定、到账是三个不同阶段。

## 数据
- Polymarket Gamma API：市场元数据、规则原文、结算状态；免费免密钥（据仓库 GUIDE.md 第 8 节）。
- 结算源公开数据：如 Weather Underground 气象站观测、官方比分源；免费。
- CLOB data-api：成交数据，免费，每市场最近约 2 万笔（据仓库 GUIDE.md 第 8 节）。**历史盘口无公开来源**：回看检验用公开成交价/最后成交价快照或前向记录，不依赖历史 ask。
- Kalshi 公开 API：`https://external-api.kalshi.com/trade-api/v2`，markets / trades / orderbook 免密钥（官方文档 Quick Start: Market Data）。trades 端点可拉历史公开成交。
- BLS 公布日历：免费，确定经济数据发布时间。各市场 `rules_primary` 字段：公开 API 返回，含结算数据源与条款。

## 两周内怎么检验
- PM 侧：用 Gamma API 扫描近 2 周已结算的 30+ 个独立事件（体育每日市场、天气市场、加密短时市场），筛选"权威源公布结果早于正式结算"的事件。**不设"≥12 小时"筛选**（UMA 常规窗口只有 2 小时，该筛选无证据支撑）；记录可知时刻获胜方最后成交价或前向记录报价，计算每笔持有至 $1 的毛收益，扣除吃单费（份数×费率×p×(1−p)，如天气 0.05）与半个价差；失败标准：中位数净收益 ≤0，或争议/异常结算占比 >10%。
- Kalshi 侧：用公开 trades 接口拉取过去 4 周已结算的日频市场成交记录。对每个市场：确定结果已可知的时点 T0（如收盘时间），结算时点 T1（position 结果记为 settled 的时间）；取 (T0, T1) 区间内获胜方合约的所有吃单成交价，计算相对 $1.00 的折价。约 20 个交易日、每日数个市场，可得 30+ 个独立结果（按事件数计）。失败标准：平均折价 < 0.5¢，或按"成本与容量"算法扣费后期望为负。

## 成本与容量
- 吃单费：份数 × 板块费率 × p × (1−p)；如天气市场 p=0.95、费率 0.05：$0.0024/份，约占成本 0.25%。
- 价差：时滞窗口流动性薄，按半个价差约 $0.005 计。
- 粗算（PM）：$0.95 买入 → 毛 5.26%，扣费与价差后净约 4.5%/笔；资金占用 1–3 天。
- 容量：PM 单市场 1 次机会、建议 ≤$500；体育/天气类每天多个事件，月机会数十次；$5000 可分散约 10 个市场。Kalshi：日频市场每月约 20 个交易日可做，加上月度经济数据；$5,000 资金单场所远低于 $2,500 上限（每事件 $800，滚动使用）。

## 风险
- 争议风险（最大）：提案被争议则锁仓 4–6 天，且 DVM 可能按字面规则逆直觉结算（如 Zelenskyy 西装案）；$0.95 全损一次约抵消 19 笔盈利。Kalshi 侧：官方源修正数据、Market Outcome Review（规则 7.1）可能延迟或改变结算。
- "too early" 提案：结果被提前提案又被推翻，窗口内买入的"获胜方"可能变化。
- 50/50 裁决：措辞模糊的问题可能按 $0.50 结算。
- 规则误读：桶边界、数据源口径理解错直接导致方向性亏损（来源案例：香港 32.8°C 按 [32.0,33.0) 判 "32" 非 "33"）。
- Kalshi 折价假设不成立：若获胜合约在结果确定后迅速被推到 99.5¢ 以上，则无利可图（需实测回答）。

## 改进了什么
- 2026-10-20：合并原 `muse-own-predmarket-kalshi-settle-lag`（同机制换场所，验证复盘判定合并）；Kalshi 版作为多场所变体收录；"1–12 小时"口径纠为组合市场专用；门槛 6 检验口径改为公开成交价/前向记录；补 CFTC 备案链接。

## 与 dot 的边界

与 dot-004（已定事实后的报价收敛）相比，Kalshi 只是同机制换场所，不计新机制。

与上游 C38（乐观预言机争议保证金收益）不同：C38 做提案/争议保证金转移，本条不提案、不争议、不赚 bond；与 C42（争议结算折价的 C04 补充）不同：本条只在权威源已公布结果且规则文本一致的非争议窗口买入，遇争议按规则放弃；与 C51（TSA 日客流同星期基准率）不同：本条不做客流计数或同星期基准率。本条与 dot-004 同族，保持 supplement，不改为 new；以上只写边界，不主张与上述条目的同族关系已排除。

## 门槛自查
1. 机制说得清：满足。付钱的是急于离场、不愿承担结算风险的持有者；持续性来自 UMA"提案+2 小时挑战期"与 Kalshi"约 3 小时结算窗口"的结构性窗口。
2. 有免费数据能检验：满足。Gamma API（规则+结算状态）与结算源公开数据均免费免密钥；Kalshi trades 公开接口免密钥可拉历史成交；BLS 日历免费。
3. 小资金能做：满足。PM 单市场 ≤$500、Kalshi 单市场 ≤$800，总 $5000 内可分散；容量为每月数十次事件。
4. 不重复：满足。known/ 无结算时滞条目；A-A5-poly-complete-set 是全买套利，机制不同。本条目覆盖 PM+Kalshi 两场所变体，为同一机制的一条多场所条目。已查 dot 认领（2026-10-20）：C01 天气结算滞后；C04 认领为同一机制的研究记录——dot-004 已存在（草稿），本条是其 supplement，本条目为可检验的策略条目，与其研究记录不构成同形重复；quant 认领无此机制。
5. 扣成本后粗算够用：不确定（PM 粗算；Kalshi 折价未实测）。PM：$0.95 买入净约 4.5%/笔、占资 1–3 天；但争议全损风险需单独计提，不宜只看均值。Kalshi：折价 3¢ 假设时净约 1.5¢/张；若实测仅 1¢ 则不成立，检验必须回答。
6. 两周内能检验：满足。PM 侧近 2 周已结算市场做回看（用成交价口径）+ 可前向记录；Kalshi 侧 4 周历史成交可得 30+ 个独立结果（按事件数计）。回看不依赖历史 ask（无公开来源）。
7. 出处可查：满足。brocode.rs 已读；startpolymarket.com、polymarket.review 为摘要；Kalshi 官方文档（Quick Start）、Alphascope（2026-10-06 核查）、rivermarkets 费率、mariokarras 指南（摘要）、CFTC 备案 PDF（Settlement Date ≤ Expiration+1 原文）均有可打开的链接；折价幅度明确标注未实测、不做断言。

## 出处
- https://brocode.rs/research/resolution-risk/ — 访问 2026-10-20 — 已读
- https://startpolymarket.com/learn/how-markets-resolve/ — 访问 2026-10-20 — 摘要
- https://polymarket.review/guides/resolution-dispute.html — 访问 2026-10-20 — 摘要
- https://docs.kalshi.com/getting_started/quick_start_market_data — 访问 2026-10-20 — 已读（公开市场数据端点免认证）
- https://www.alphascope.app/blog/how-long-does-kalshi-take-to-settle — 访问 2026-10-20 — 已读（"大多数市场在结果确定后几小时内结算，通常约三小时"，引自 Kalshi 官方 FAQ，2026-10-06 核查）
- https://www.rivermarkets.com/insights/kalshi-fees.html — 访问 2026-10-20 — 已读（吃单费 = 合约数 × 0.07 × 价格 × (1−价格)，2026-08 更新）
- https://mariokarras.com/explainers/kalshi-trading-models/kalshi-guide-for-claude.html — 访问 2026-10-20 — 摘要（"1 到 12 小时以上"为组合市场口径，已在正文中纠正）
- https://www.cftc.gov/filings/ptc/ptc12242412568.pdf — 访问 2026-10-20 — 已读（pdftotext 提取；该 PDF 是 Kalshi TikTok v. Garland 单个合约备案，含该通用句） — CFTC 备案规则原文："The Settlement Date of the Contract shall be no later than the day after the Expiration Date, unless the Market Outcome is under review pursuant to Rule 7.1."
- 仓库 GUIDE.md 第 8 节（Polymarket 费用与公开数据） — 访问 2026-10-20 — 已读
