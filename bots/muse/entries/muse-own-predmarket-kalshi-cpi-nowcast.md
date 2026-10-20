> 作者：Muse 直属 agent（muse-agent-3）｜ 试运行第 1 批

---
id: muse-own-predmarket-kalshi-cpi-nowcast
name_zh: Kalshi CPI 阶梯今值定价偏差
name_en: Kalshi CPI Ladder Nowcast Pricing
bot: muse
date: 2026-10-20
market: prediction_other
pm_category: -
kind: new
improves: -
category: S
return_type: direction
instruments: Kalshi CPI / CPIYOY / PCECORE 月度阶梯市场（0.1 个百分点一档）
venues: Kalshi
data: Kalshi 公开 API（免密钥，trade-api/v2：markets/orderbook/trades/candlesticks）；克利夫兰联储通胀 nowcast（每个工作日约美东 10:00 更新，免费）；BLS 公开数据（结算）；nowcast 历史图表文件（2013-08 起，免费）
test_2w: 取 2013-08 至 2026-08 共 156 个有实际值的月份，对每月用发布前最后一次 nowcast 加历史误差分布算出各桶公允概率，与 BLS 实际值对比做校准检验；失败标准：公允概率系统性偏离实际命中率超 10 个百分点。同时即日起用 Kalshi 公开 API 前向记录阶梯价格，积累价格偏离案例
status: 草稿
confidence: 中
---

## 一句话

在 Kalshi 的 CPI（及 PCE/非农等）月度阶梯市场上，用克利夫兰联储每日 nowcast 加历史误差分布算出各价格桶的公允概率，价格偏离公允超过阈值时反向交易（卖出偏贵的桶 / 买入偏便宜的桶）。

## 钱从哪里来

付钱的是被新闻标题和混淆概念驱动的散户资金流，以及更新缓慢的被动报价。2026 年 9 月 CPI 阶梯是一个实证例子：The Traders Spread 记录到 3.7% 桶被定价 41.5¢，而按 156 个月 nowcast 误差分布算出的公允值只有 21.8%——买方把美联储主席提到的 PCE 全年 3.7% 误当成当月 CPI 桶来定价。这类由概念混淆和注意力偏差造成的定价错误会持续出现，因为每个月都有新的数据发布和新的新闻叙事。

## 规则

1. 每日（美东约 10:00 nowcast 更新后）拉取 Kalshi CPI/CPIYOY/PCECORE 当月阶梯各桶买卖价，取中间价为市场概率。
2. 取当日克利夫兰联储 nowcast 点估计，结合历史 nowcast 误差的经验分布（156 个月样本），算出每个 0.1pp 桶的公允概率。
3. 当某桶 |市场价 − 公允价| ≥ 15¢ 时建仓：市场价高于公允则卖出该桶 Yes（或买入 No），反之买入。单桶仓位不超过 $500。
4. 持有至 BLS 公布后结算；若 nowcast 点估计移入该桶区间（如 nowcast 从 3.60 升至 3.65 进入 3.7 桶），立即平仓。
5. 只做吃单价差 ≤ 2¢、桶流动性（liquidity 字段）≥ $2,000 的桶。

## 证据

The Traders Spread（2026-10-11 发布，来源自报，未核实）：2026 年 9 月 CPI 阶梯，3.7% 桶 Yes 价 41.5¢（bid 41¢/ask 42¢，成交量约 $23,860），按 156 个月 nowcast 误差分布算出的公允值为 21.8%，价差约 20¢；3.6% 桶 39.0¢ 对公允 40.4%，基本吻合。**事后披露**：9 月 CPI 实际打印 3.7%（Nowflation 评分记录），3.7% 桶命中——单次结果落在公允分布的 21.8% 一侧，不否定概率优势，但说明误差分布有肥尾，仓位必须按此控制。该文未扣成本。

克利夫兰联储官方称其 nowcast 在历史上多数情况下优于 Blue Chip 共识和 SPF 中位数（来源自报，未核实；clevelandfed.org 问答页）。

## 数据

- Kalshi 公开 API：`https://external-api.kalshi.com/trade-api/v2`，markets / orderbook / trades / candlesticks 端点免密钥（官方文档 Quick Start: Market Data，2026-05-05 更新）。我方 2026-10-20 实测：`CPI`、`CPIYOY`、`PCECORE`、`FEDDECISION` 系列存在，月度频率。
- 克利夫兰联储 nowcast：https://www.clevelandfed.org/indicators-and-data/inflation-nowcasting ，每个工作日更新，免费；历史图表文件可回溯至 2013-08。
- BLS：CPI 发布时间表与历史数据，免费。

## 两周内怎么检验

1. 下载 nowcast 历史文件（156 个月）与 BLS 实际值，复算每月的桶公允概率，检验校准性：把公允概率分桶（如 0-10%、10-20%…），看实际命中率是否落在公允区间内。失败标准：系统性偏离超 10 个百分点。
2. 即日起每日记录 Kalshi CPI 阶梯价格（公开 API），统计 |市场价−公允价| ≥ 15¢ 的事件频率。失败标准：两周内零次触发（说明机会频率不足）。

独立结果按事件数：每月 CPI 公布为 1 个结果；156 个月历史 = 156 个独立结果。

## 成本与容量

- Kalshi 吃单费 = 合约数 × 0.07 × 价格 × (1−价格)。以 3.7% 桶为例：在 41.5¢ 卖出 Yes，吃单费约 0.07×0.415×0.585 ≈ 1.7¢/张；价差 1¢，半个价差 0.5¢。
- 粗算（用文献案例数字，来源自报）：卖出 3.7% 桶 Yes @41.5¢，公允 21.8¢，期望毛利 19.7¢/张；扣吃单费 1.7¢、半价差 0.5¢，净期望约 17.5¢/张。单桶 $500 仓位（约 1200 张）期望净利约 $210/事件。资金占用约 2 周。
- 容量：CPI/PCE/非农/Fed 四个系列，每月约 4-6 个事件；$5,000 资金可覆盖（单场所 <$2,500，跨事件分散）。

## 风险

- 模型风险：nowcast 误差分布有肥尾（如 2026-06 曾出现 0.39pp 的单月误差），公允概率本身不准；单次事件可能亏损。
- 结算口径风险：合约按 BLS 未季调 CPI-U 取一位小数结算，nowcast 的季调月环比口径不能直接相加，必须用同比口径（文献已指出此坑）。
- 流动性风险：偏远桶流动性可能不足 $2,000，大单冲击价差。
- 平台风险：Kalshi 为 CFTC 监管交易所，规则以官方为准；费率可能调整。

## 改进了什么

不适用。

## 门槛自查
1. 机制说得清：满足。付钱的是被新闻叙事和概念混淆驱动的散户资金流，赚的是外部模型定价与市场定价之差；有 2026-09 实证案例。
2. 有免费数据能检验：满足。Kalshi API 免密钥、nowcast 免费每日更新、BLS 免费；156 个月历史独立结果。
3. 小资金能做：满足。单桶 $500，$5,000 覆盖多事件；不加杠杆。
4. 不重复：满足。known/ 中无此机制（A-A3-poly-cross-market 是跨市场价差，机制不同；V-V2-poly-longshot 是冷门偏差下注，机制不同）。
5. 扣成本后粗算够用：满足（基于文献案例数字，来源自报）。期望净利约 17.5¢/张，单事件期望约 $210，资金占用两周。
6. 两周内能检验：满足。156 个历史独立结果一次算完做校准检验；价格偏离频率往前记录。
7. 出处可查：满足。见出处节；第三方分析的数字已标来源自报。

## 出处
- https://docs.kalshi.com/getting_started/quick_start_market_data — 访问 2026-10-20 — 已读（公开市场数据端点免认证）
- https://www.clevelandfed.org/indicators-and-data/inflation-nowcasting — 访问 2026-10-20 — 已读（每日 nowcast、四种通胀指标、历史准确性自述）
- https://thetradersspread.com/prediction-markets/september-cpi-odds-3-7-bucket-above-fair — 访问 2026-10-20 — 已读（2026-09 CPI 阶梯 3.7% 桶 41.5¢ vs 公允 21.8%、156 个月误差分布方法；其价格数字为来源自报）
- https://nowflation.com/cpi/september-2026 — 访问 2026-10-20 — 摘要（9 月 CPI 实际打印 3.7%、Kalshi 市场隐含均值 3.65%）
- https://api.elections.kalshi.com/trade-api/v2/series — 访问 2026-10-20 — 已读（实测确认 CPI/CPIYOY/PCECORE/FEDDECISION 系列存在）
