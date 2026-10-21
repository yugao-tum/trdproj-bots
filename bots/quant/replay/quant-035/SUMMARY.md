# 回放汇总：quant-035

## 如何复现

- 脚本：`bots/quant/replay/quant-035/replay.py`（Python 3.10+，`requests`；其余为标准库）。
- 运行：在仓库根目录执行 `python3 bots/quant/replay/quant-035/replay.py`。脚本会把 Binance 月度 ZIP 和 Hyperliquid JSON 原始下载缓存在 `bots/quant/replay/quant-035/_cache/`（已被 `bots/quant/.gitignore` 的 `_cache/` 忽略，不进仓库），然后生成 `results.json`、`trades.csv`、`equity.csv`、`variants.csv`。
- 参数：主规则 = 14 天滚动平均资金费 > 0 开仓、< 0 平仓；Binance 四币各 300 USDT 名义、每个 sleeve 预算 600 USDT；HYPE 1,200 USDT 名义、预算 2,450 USDT；成本 0.30%/腿/边；成交为决策后下一根 K 线开盘（Binance 1h；HYPE 历史 4h，见下）。
- 数据下载地址和访问日期（均为 2026-10-21，公开、免密钥）：
  - 现货 1h：`https://data.binance.vision/data/spot/monthly/klines/<SYM>/1h/<SYM>-1h-<YYYY-MM>.zip`
  - USDⓈ-M 永续 1h：`https://data.binance.vision/data/futures/um/monthly/klines/<SYM>/1h/<SYM>-1h-<YYYY-MM>.zip`
  - USDⓈ-M mark 1h：`https://data.binance.vision/data/futures/um/monthly/markPriceKlines/<SYM>/1h/<SYM>-1h-<YYYY-MM>.zip`
  - USDⓈ-M 资金费：`https://data.binance.vision/data/futures/um/monthly/fundingRate/<SYM>/<SYM>-fundingRate-<YYYY-MM>.zip`
  - Hyperliquid：`POST https://api.hyperliquid.xyz/info`，`candleSnapshot`（`HYPE`、`@107`，4h）和 `fundingHistory`（`HYPE`，1h）
  - `<SYM>` = SOLUSDT/XRPUSDT/ADAUSDT/AVAXUSDT；`<YYYY-MM>` = 2022-01..2024-12。
- 数据本身起点：Binance 2022-01-01；HYPE 2024-12-05（Hyperliquid 上首个可用资金费/K 线日，晚于上市日，仍在 2024-12-31 前）。
- 开发窗口：`2022-01-01..2024-12-31`。HYPE 只有 2024-12-05..2024-12-31；没有下载、运行或报告 2025-01-01 以后的数据，也没有使用 2021 年及以前的数据。
- 切分依据：加密遵守 GUIDE 第 9 节，整段 2022–2024 为开发窗口；HYPE 短历史不另做 70% 切分，因为其数据起点在开发窗口内部，且只作为单币短样本变体报告。

## 成交和成本

- **成交价和时点**：每个资金费时间戳 `t` 做决策；在 `t` 之后下一根 K 线开盘成交。Binance 1h 开盘价；HYPE 回放用 4h 开盘价（Hyperliquid 公开 API 的 2024 年 1h 历史被裁剪，4h 仍可取；前向记录按规则用 1h）。不使用未来价格；信号只用 `t` 及以前的资金费。
- **全部成本**：每腿每边 0.30%（现货和永续开、平各一次，完整往返 = 名义的 1.2%）+ 实际资金费收付。资金费现金 = `q × mark_price(t) × funding_rate(t)`，空头正费率收正、负费率付负；Binance mark 用 `markPriceKlines` 在 `t` 所在小时的 1h 开盘价，HYPE 用永续 4h 开盘价。未另加滑点；0.30%/腿/边已包含手续费和价差粗算。
- **资金和容量**：总资本 5,000 USDT；Binance 四个 sleeve 合计预算 2,400 USDT（每个 600），Hyperliquid HYPE sleeve 预算 2,450 USDT；总占用最大 4,809.11 USDT，单场所最大 2,409.11 USDT，均在 2,500 以内。每个 sleeve 的 `q` 用 `min(target/spot, budget/((spot+perp)×1.003))` 限制，1x、不借币、不做空现货。
- **容量**：单笔名义 300 USDT（Binance）或 1,200 USDT（HYPE），远低于这些合约的日常盘口深度；策略不依赖高频成交。

## 汇总结果

- **独立结果数及计法**：主组合 55 个 entry-to-exit episode（SOL 11、XRP 13、ADA 14、AVAX 16、HYPE 1）；按“同一小时同向新开仓合并”保守计，唯一开仓时间戳 51 个、唯一开仓日 48 个。51 ≥ 30，满足 `result: 正` 的独立结果要求。资金费结算行不重复计为独立结果；对冲两腿算 1 个。
- **扣成本后净收益**：**+521.11 USDT**（5,000 USDT 账户，2022-01-01..2024-12-31，3.0007 年）。其中资金费 +735.88、费用 -221.88、价格/基差 +7.11；累计净收益 10.42%，年化贡献 **3.47%**。
- **最大回撤**：**1.95%**（日线，5,000 账户权益，含浮亏；峰值 5,550.70，谷值 5,521.11，2023-01-15）。策略占用资金的平均值 1,794.08 USDT，最大 4,809.11 USDT；1,096 天中有 988 天至少一个 sleeve 在场。
- **对 5,000 USDT 的年化贡献**：`521.11 / 5,000 / 3.0007 = 3.47%`。等价地，占用资金年化约 `521.11 / 3.0007 / 1,794.08 = 9.68%` × 平均占用 1,794.08 / 5,000 ≈ 3.47%。这是组合腿口径，未达到 GUIDE 第 9 节单独策略 8% 的线，但超过 3% 的组合腿线。
- **result**：**正**（扣全部成本后净收益为正，独立结果 ≥30）。
- **方向性**：日频收益对四币等权现货篮子的 beta = **-0.00028**，接近 0；两腿同币等量，持仓期间净方向敞口为 0（仅基差/保证金/费用残余）。
- **分年净损益**（同一 5,000 账户，按日线权益年末值差）：2022 **-89.43**、2023 **+97.00**、2024 **+513.54**。结果集中在 2024；2022 为负。这一点不掩饰，见“不可靠或失败原因”。
- **分币 sleeve**：

| sleeve | 净损益 USDT | 年化贡献 | 日线最大回撤 | episodes | 费用 USDT | 最大占用 USDT |
|---|---:|---:|---:|---:|---:|---:|
| SOL 300 | 198.69 | 1.32% | 0.39% | 11 | 46.06 | 600.00 |
| XRP 300 | 54.55 | 0.36% | 0.66% | 13 | 51.61 | 600.00 |
| ADA 300 | 94.53 | 0.63% | 0.61% | 14 | 51.21 | 600.00 |
| AVAX 300 | 147.36 | 0.98% | 0.57% | 16 | 59.40 | 600.00 |
| HYPE 1,200 | 25.98 | 0.17% | 0.11% | 1 | 13.60 | 2,409.11 |
| **合计** | **521.11** | **3.47%** | **1.95%** | **55** | **221.88** | **4,809.11** |

- **交易统计**：55 笔 episode，19 笔盈利、36 笔亏损；中位持有 14.67 天，平均 58.95 天；单笔净损益最小 -2.13、最大 +217.48 USDT。
- **不可靠或失败原因**：
  - 2022 年净 -89.43，说明负资金费/熊市阶段 14 天均值闸门仍会滞后，不能保证每年正。
  - 2024 年贡献 513.54（其中 HYPE +25.98），结果对 2024 年 alts 资金费环境依赖较大；不能外推到所有年份。
  - HYPE 只有 2024-12-05..2024-12-31、1 个 episode，单独看不显著；它只作为短历史补充，不支撑主结论。
  - 回放 HYPE 用 4h 成交粒度，前向用 1h，二者不完全同口径。
  - 资金费 mark 用 1h/4h 开盘价近似，不是交易所精确结算 mark；误差方向不定但量级小。
  - 未模拟强平、保证金档位变化、交易所对手方和 USDT 脱锚；1x 全抵押只保证结构上限，不保证路径上不需要补保证金。

## 所有变体（所有市场都要写，看了不用的也算）

- **variants（自己的）**：**94**。下表是 `variants.csv` 的全部行；`main_basket` 是主结果，其余是参数、币种、场所和阈值敏感性，包含看了不用的探索性变体。所有变体都用同一 2022–2024 窗口；没有 2025+ 数据。
- **variants_ext（外部来源）**：**0**。composer-003 和 dot-019 只用于机制对照；它们的样本含 2025 以后，具体结果见原文，本条不抄入。没有把外部绩效数字并入本表。
- 主规则取 14 天（两个资金费周）；同篮子 7/21/28 天分别 +361.15/+451.53/+493.32（年化 2.41%/3.01%/3.29%），都为正，说明主结果不是单点刀尖。30-event z>0.5 在 SOL 上 378 个 episode、净 -5,271.08；always-on 在四币上均大幅为负；这是本条相对 composer-003 的核心反证。

| # | 变体 | 家族 | 币/组合 | 场所 | 回看(天) | 入场阈值 | 净损益 USDT | 年化贡献 | 日线最大回撤 | episodes |
|---:|---|---|---|---|---:|---:|---:|---:|---:|---:|
| 1 | main_basket | main | SOL,XRP,ADA,AVAX,HYPE | Binance+Hyperliquid | 14 | 0.0 | 521.11 | 3.47% | 1.95% | 55 |
| 2 | coin_SOLUSDT_7d | per_coin | SOLUSDT | Binance | 7 | 0.0 | 450.45 | 3.00% | 3.95% | 24 |
| 3 | coin_SOLUSDT_14d | per_coin | SOLUSDT | Binance | 14 | 0.0 | 797.33 | 5.31% | 1.57% | 11 |
| 4 | coin_SOLUSDT_21d | per_coin | SOLUSDT | Binance | 21 | 0.0 | 652.79 | 4.35% | 0.97% | 9 |
| 5 | coin_SOLUSDT_28d | per_coin | SOLUSDT | Binance | 28 | 0.0 | 663.95 | 4.43% | 0.65% | 6 |
| 6 | coin_SOLUSDT_42d | per_coin | SOLUSDT | Binance | 42 | 0.0 | 469.72 | 3.13% | 0.75% | 6 |
| 7 | coin_SOLUSDT_14d_5bp | per_coin | SOLUSDT | Binance | 14 | 5e-05 | 643.67 | 4.29% | 1.29% | 9 |
| 8 | coin_SOLUSDT_21d_5bp | per_coin | SOLUSDT | Binance | 21 | 5e-05 | 610.35 | 4.07% | 0.74% | 6 |
| 9 | coin_SOLUSDT_21d_10bp | per_coin | SOLUSDT | Binance | 21 | 0.0001 | 458.05 | 3.05% | 0.46% | 2 |
| 10 | coin_SOLUSDT_always | per_coin | SOLUSDT | Binance | 0 | 0.0 | -3720.43 | -24.80% | 74.41% | 298 |
| 11 | coin_XRPUSDT_7d | per_coin | XRPUSDT | Binance | 7 | 0.0 | 63.10 | 0.42% | 4.57% | 22 |
| 12 | coin_XRPUSDT_14d | per_coin | XRPUSDT | Binance | 14 | 0.0 | 218.85 | 1.46% | 2.65% | 13 |
| 13 | coin_XRPUSDT_21d | per_coin | XRPUSDT | Binance | 21 | 0.0 | 274.22 | 1.83% | 1.35% | 8 |
| 14 | coin_XRPUSDT_28d | per_coin | XRPUSDT | Binance | 28 | 0.0 | 332.16 | 2.21% | 1.11% | 6 |
| 15 | coin_XRPUSDT_42d | per_coin | XRPUSDT | Binance | 42 | 0.0 | 395.99 | 2.64% | 0.74% | 3 |
| 16 | coin_XRPUSDT_14d_5bp | per_coin | XRPUSDT | Binance | 14 | 5e-05 | 320.65 | 2.14% | 0.62% | 4 |
| 17 | coin_XRPUSDT_21d_5bp | per_coin | XRPUSDT | Binance | 21 | 5e-05 | 329.29 | 2.19% | 0.64% | 4 |
| 18 | coin_XRPUSDT_21d_10bp | per_coin | XRPUSDT | Binance | 21 | 0.0001 | 198.02 | 1.32% | 0.46% | 1 |
| 19 | coin_XRPUSDT_always | per_coin | XRPUSDT | Binance | 0 | 0.0 | -4431.78 | -29.54% | 88.63% | 335 |
| 20 | coin_ADAUSDT_7d | per_coin | ADAUSDT | Binance | 7 | 0.0 | 210.12 | 1.40% | 3.51% | 22 |
| 21 | coin_ADAUSDT_14d | per_coin | ADAUSDT | Binance | 14 | 0.0 | 379.21 | 2.53% | 2.44% | 14 |
| 22 | coin_ADAUSDT_21d | per_coin | ADAUSDT | Binance | 21 | 0.0 | 354.13 | 2.36% | 2.79% | 15 |
| 23 | coin_ADAUSDT_28d | per_coin | ADAUSDT | Binance | 28 | 0.0 | 433.23 | 2.89% | 1.20% | 9 |
| 24 | coin_ADAUSDT_42d | per_coin | ADAUSDT | Binance | 42 | 0.0 | 424.35 | 2.83% | 1.23% | 8 |
| 25 | coin_ADAUSDT_14d_5bp | per_coin | ADAUSDT | Binance | 14 | 5e-05 | 428.67 | 2.86% | 1.19% | 8 |
| 26 | coin_ADAUSDT_21d_5bp | per_coin | ADAUSDT | Binance | 21 | 5e-05 | 418.52 | 2.79% | 1.09% | 7 |
| 27 | coin_ADAUSDT_21d_10bp | per_coin | ADAUSDT | Binance | 21 | 0.0001 | 309.30 | 2.06% | 0.31% | 2 |
| 28 | coin_ADAUSDT_always | per_coin | ADAUSDT | Binance | 0 | 0.0 | -3512.59 | -23.41% | 70.48% | 283 |
| 29 | coin_AVAXUSDT_7d | per_coin | AVAXUSDT | Binance | 7 | 0.0 | 378.98 | 2.53% | 3.75% | 27 |
| 30 | coin_AVAXUSDT_14d | per_coin | AVAXUSDT | Binance | 14 | 0.0 | 591.17 | 3.94% | 2.30% | 16 |
| 31 | coin_AVAXUSDT_21d | per_coin | AVAXUSDT | Binance | 21 | 0.0 | 550.49 | 3.67% | 1.97% | 15 |
| 32 | coin_AVAXUSDT_28d | per_coin | AVAXUSDT | Binance | 28 | 0.0 | 549.66 | 3.66% | 1.33% | 12 |
| 33 | coin_AVAXUSDT_42d | per_coin | AVAXUSDT | Binance | 42 | 0.0 | 664.18 | 4.43% | 0.88% | 7 |
| 34 | coin_AVAXUSDT_14d_5bp | per_coin | AVAXUSDT | Binance | 14 | 5e-05 | 637.27 | 4.25% | 0.89% | 8 |
| 35 | coin_AVAXUSDT_21d_5bp | per_coin | AVAXUSDT | Binance | 21 | 5e-05 | 637.80 | 4.25% | 0.99% | 7 |
| 36 | coin_AVAXUSDT_21d_10bp | per_coin | AVAXUSDT | Binance | 21 | 0.0001 | 485.28 | 3.23% | 0.45% | 3 |
| 37 | coin_AVAXUSDT_always | per_coin | AVAXUSDT | Binance | 0 | 0.0 | -3568.69 | -23.79% | 71.35% | 300 |
| 38 | coin_HYPE_7d | per_coin | HYPE | Hyperliquid | 7 | 0.0 | 86.27 | 0.57% | 0.15% | 1 |
| 39 | coin_HYPE_14d | per_coin | HYPE | Hyperliquid | 14 | 0.0 | 25.98 | 0.17% | 0.11% | 1 |
| 40 | coin_HYPE_21d | per_coin | HYPE | Hyperliquid | 21 | 0.0 | -4.92 | -0.03% | 0.14% | 1 |
| 41 | coin_HYPE_28d | per_coin | HYPE | Hyperliquid | 28 | 0.0 | 0.00 | 0.00% | 0.00% | 0 |
| 42 | coin_HYPE_42d | per_coin | HYPE | Hyperliquid | 42 | 0.0 | 0.00 | 0.00% | 0.00% | 0 |
| 43 | coin_HYPE_14d_5bp | per_coin | HYPE | Hyperliquid | 14 | 5e-05 | 25.98 | 0.17% | 0.11% | 1 |
| 44 | coin_HYPE_21d_5bp | per_coin | HYPE | Hyperliquid | 21 | 5e-05 | -4.92 | -0.03% | 0.14% | 1 |
| 45 | coin_HYPE_21d_10bp | per_coin | HYPE | Hyperliquid | 21 | 0.0001 | -4.92 | -0.03% | 0.14% | 1 |
| 46 | coin_HYPE_always | per_coin | HYPE | Hyperliquid | 0 | 0.0 | 88.95 | 0.59% | 0.92% | 3 |
| 47 | basket_7d | basket | SOL,XRP,ADA,AVAX,HYPE | Binance+Hyperliquid | 7 | 0.0 | 361.15 | 2.41% | 3.75% | 96 |
| 48 | basket_21d | basket | SOL,XRP,ADA,AVAX,HYPE | Binance+Hyperliquid | 21 | 0.0 | 451.53 | 3.01% | 1.57% | 48 |
| 49 | basket_28d | basket | SOL,XRP,ADA,AVAX,HYPE | Binance+Hyperliquid | 28 | 0.0 | 493.32 | 3.29% | 0.86% | 33 |
| 50 | one_slot_14d | one_slot | SOL,XRP,ADA,AVAX | Binance | 14 | 0.0 | 202.66 | 1.35% | 2.63% | 16 |
| 51 | one_slot_21d | one_slot | SOL,XRP,ADA,AVAX | Binance | 21 | 0.0 | 253.44 | 1.69% | 1.29% | 12 |
| 52 | one_slot_42d | one_slot | SOL,XRP,ADA,AVAX | Binance | 42 | 0.0 | 318.77 | 2.12% | 1.12% | 8 |
| 53 | one_slot_63d | one_slot | SOL,XRP,ADA,AVAX | Binance | 63 | 0.0 | 403.10 | 2.69% | 0.84% | 5 |
| 54 | one_slot_189d | one_slot | SOL,XRP,ADA,AVAX | Binance | 189 | 0.0 | 439.19 | 2.93% | 1.35% | 5 |
| 55 | HYPE_1d | hype_extra | HYPE | Hyperliquid | 1 | 0.0 | 157.18 | 1.05% | 0.18% | 1 |
| 56 | HYPE_2d | hype_extra | HYPE | Hyperliquid | 2 | 0.0 | 133.63 | 0.89% | 0.27% | 1 |
| 57 | HYPE_3d | hype_extra | HYPE | Hyperliquid | 3 | 0.0 | 132.12 | 0.88% | 0.12% | 1 |
| 58 | HYPE_5d | hype_extra | HYPE | Hyperliquid | 5 | 0.0 | 115.79 | 0.77% | 0.14% | 1 |
| 59 | HYPE_7d | hype_extra | HYPE | Hyperliquid | 7 | 0.0 | 86.27 | 0.57% | 0.15% | 1 |
| 60 | HYPE_21d | hype_extra | HYPE | Hyperliquid | 21 | 0.0 | -4.92 | -0.03% | 0.14% | 1 |
| 61 | HYPE_28d | hype_extra | HYPE | Hyperliquid | 28 | 0.0 | 0.00 | 0.00% | 0.00% | 0 |
| 62 | HYPE_42d | hype_extra | HYPE | Hyperliquid | 42 | 0.0 | 0.00 | 0.00% | 0.00% | 0 |
| 63 | HYPE_N42_0 | hype_events | HYPE | Hyperliquid | 1.75 | 0.0 | 136.45 | 0.91% | 0.11% | 1 |
| 64 | HYPE_N42_5bp | hype_events | HYPE | Hyperliquid | 1.75 | 5e-05 | 136.45 | 0.91% | 0.11% | 1 |
| 65 | HYPE_N63_0 | hype_events | HYPE | Hyperliquid | 2.625 | 0.0 | 124.30 | 0.83% | 0.19% | 1 |
| 66 | HYPE_N63_5bp | hype_events | HYPE | Hyperliquid | 2.625 | 5e-05 | 124.30 | 0.83% | 0.19% | 1 |
| 67 | HYPE_N84_0 | hype_events | HYPE | Hyperliquid | 3.5 | 0.0 | 129.08 | 0.86% | 0.12% | 1 |
| 68 | HYPE_N84_5bp | hype_events | HYPE | Hyperliquid | 3.5 | 5e-05 | 129.08 | 0.86% | 0.12% | 1 |
| 69 | HYPE_N168_0 | hype_events | HYPE | Hyperliquid | 7.0 | 0.0 | 86.27 | 0.57% | 0.15% | 1 |
| 70 | HYPE_N168_5bp | hype_events | HYPE | Hyperliquid | 7.0 | 5e-05 | 86.27 | 0.57% | 0.15% | 1 |
| 71 | HYPE_N336_0 | hype_events | HYPE | Hyperliquid | 14.0 | 0.0 | 25.98 | 0.17% | 0.11% | 1 |
| 72 | HYPE_N336_5bp | hype_events | HYPE | Hyperliquid | 14.0 | 5e-05 | 25.98 | 0.17% | 0.11% | 1 |
| 73 | HYPE_N504_0 | hype_events | HYPE | Hyperliquid | 21.0 | 0.0 | -4.92 | -0.03% | 0.14% | 1 |
| 74 | HYPE_N504_5bp | hype_events | HYPE | Hyperliquid | 21.0 | 5e-05 | -4.92 | -0.03% | 0.14% | 1 |
| 75 | SOL_z30_0.5 | zscore | SOLUSDT | Binance | 0 | 0.0 | -5271.08 | -35.13% | 105.42% | 378 |
| 76 | SOL_z30_1.0 | zscore | SOLUSDT | Binance | 0 | 0.0 | -2981.04 | -19.87% | 59.62% | 213 |
| 77 | SOL_14d_basis | basis | SOLUSDT | Binance | 14 | 0.0 | -1269.11 | -8.46% | 25.38% | 104 |
| 78 | SOL_63d_0 | sol_extra | SOLUSDT | Binance | 63 | 0.0 | 512.07 | 3.41% | 0.61% | 5 |
| 79 | SOL_63d_5bp | sol_extra | SOLUSDT | Binance | 63 | 5e-05 | 414.81 | 2.76% | 0.45% | 3 |
| 80 | SOL_63d_10bp | sol_extra | SOLUSDT | Binance | 63 | 0.0001 | 390.38 | 2.60% | 0.42% | 1 |
| 81 | SOL_189d_0 | sol_extra | SOLUSDT | Binance | 189 | 0.0 | 1234.23 | 8.23% | 1.09% | 2 |
| 82 | SOL_189d_5bp | sol_extra | SOLUSDT | Binance | 189 | 5e-05 | 245.52 | 1.64% | 0.29% | 1 |
| 83 | coin_XRPUSDT_63d_0 | per_coin_long | XRPUSDT | Binance | 63 | 0.0 | 390.58 | 2.60% | 0.71% | 2 |
| 84 | coin_XRPUSDT_63d_5bp | per_coin_long | XRPUSDT | Binance | 63 | 5e-05 | 415.89 | 2.77% | 0.77% | 2 |
| 85 | coin_XRPUSDT_189d_0 | per_coin_long | XRPUSDT | Binance | 189 | 0.0 | 397.43 | 2.65% | 0.79% | 2 |
| 86 | coin_XRPUSDT_189d_5bp | per_coin_long | XRPUSDT | Binance | 189 | 5e-05 | 192.00 | 1.28% | 0.40% | 1 |
| 87 | coin_ADAUSDT_63d_0 | per_coin_long | ADAUSDT | Binance | 63 | 0.0 | 375.17 | 2.50% | 1.20% | 5 |
| 88 | coin_ADAUSDT_63d_5bp | per_coin_long | ADAUSDT | Binance | 63 | 5e-05 | 319.87 | 2.13% | 0.28% | 1 |
| 89 | coin_ADAUSDT_189d_0 | per_coin_long | ADAUSDT | Binance | 189 | 0.0 | 465.50 | 3.10% | 0.73% | 3 |
| 90 | coin_ADAUSDT_189d_5bp | per_coin_long | ADAUSDT | Binance | 189 | 5e-05 | 302.15 | 2.01% | 0.28% | 1 |
| 91 | coin_AVAXUSDT_63d_0 | per_coin_long | AVAXUSDT | Binance | 63 | 0.0 | 594.94 | 3.97% | 0.75% | 5 |
| 92 | coin_AVAXUSDT_63d_5bp | per_coin_long | AVAXUSDT | Binance | 63 | 5e-05 | 434.17 | 2.89% | 0.57% | 3 |
| 93 | coin_AVAXUSDT_189d_0 | per_coin_long | AVAXUSDT | Binance | 189 | 0.0 | 394.63 | 2.63% | 0.49% | 1 |
| 94 | coin_AVAXUSDT_189d_5bp | per_coin_long | AVAXUSDT | Binance | 189 | 5e-05 | 461.48 | 3.08% | 0.58% | 1 |

## 数据与脚本产物

- `replay/quant-035/replay.py` — 可运行脚本（下载、回放、变体、输出）。
- `replay/quant-035/results.json` — 主结果、五个 sleeve、全部变体指标。
- `replay/quant-035/trades.csv` — 主组合 55 笔 episode 明细（入场/出场两腿价格、数量、资金费、费用、净损益）。
- `replay/quant-035/equity.csv` — 日线权益、累计损益、占用资金。
- `replay/quant-035/variants.csv` — 94 个变体的参数和结果。
- `replay/quant-035/_cache/` — 原始下载缓存，已被 `.gitignore` 忽略，不进仓库。
