---
id: quant-002
name_zh: 月初月末与周一效应样本外反证
name_en: Turn-of-month and Monday windows on BTC/ETH spot — fee-aware 2022-2024 tradable-price replay counter-evidence
bot: quant
date: 2026-10-20
market: crypto
pm_category: -
kind: supplement
improves: E-E2-turn-of-month
category: E
return_type: direction
instruments: BTC, ETH 现货
venues: Binance 现货
data: Binance 公开日线 + 1h K 线（data.binance.vision / data-api.binance.vision，免密钥；本条回放用 2022-01-01～2024-12-31）
test_2w: 运行 bots/quant/replay/quant-002/ 的 fetch_data.py、backtest.py、verify_sources.py，按“次日开盘成交、每边 0.30%”重跑；独立结果按 TOM 月窗口（35 个）和周一窗口（156–157 个）计；失败标准：8 个规则版本在 0.30%/边下 3 年连乘为负，或单窗口净收益 t 检验不显著为正（本条两者都成立）
status: 待核
confidence: 高
evidence: 回放
result: 负
slot: -
variants: 16
variants_ext: 0
window: 2022-01-01..2024-12-31
max_dd: 55.7%（日线，BTC 周一精确）
contribution: -7.5%
---

## 一句话

结论（负）：只在“月末最后 1 天 + 月初前 3 天”（TOM）或只在周一持有 BTC/ETH 现货，在 2022-01-01～2024-12-31 按可成交的次日开盘价、每边 0.30% 成本回放，8 个规则版本 × 2 种成交价 = 16 个结果全部亏钱；建议主项目把 E-E2-turn-of-month 的 BTC/ETH 现货版本降级或退回，本条只作为负证据按“补充采纳”（0.5 分）候选，不要按可交易策略收录。

## 钱从哪里来

- 原机制（E-E2-turn-of-month）的说法是月初月末资金流（发薪、定投、调仓）集中，造成固定日历窗口的超额收益。
- 本条不提出新收益来源，只补“这个现金流在 BTC/ETH 现货上扣成本后是否还在”的样本外证据；结论是 0.30%/边下不在。毛收益层面 BTC 周一（精确日历）名义上最接近正效应（+0.36%/窗口），但盈亏平衡每边成本约 0.18%，低于 GUIDE 的 0.30%，且同换手 placebo 的 p=0.145，不能算可交易优势。

## 规则

- TOM（精确日历）：每月最后 1 个日历日和次月第 1～3 日持有单币现货，其余时间现金；这 4 天在日界上连续，算 1 次进出。窗口首日 00:00 UTC 开盘买，最后持有日的次一日 00:00 UTC 开盘卖。
- 周一（精确日历）：只在周一（UTC）持有，周一 00:00 开盘进、周二 00:00 开盘出，其余时间现金。
- 原代码错位版本：私有研究原代码把窗口错后了一天，实际持有月初第 1～4 天或周二；本条同样报告，避免只挑好看的版本。
- 成交价（主口径）：信号出现后的下一根日线开盘价（GUIDE §9）。日历提前已知，无前视。敏感性口径：窗口首日 00:00–01:00 UTC 首小时 K 线的 VWAP（`quote_volume/volume`，真实成交的加权价），窗口结束后次日同一时段 VWAP 卖出。
- 单币最多 2,500 USDT（GUIDE 的单场所上限），其余现金；不加杠杆、不做空。若同时做 BTC 和 ETH，两者合计不超过 2,500 USDT（例如各 1,250），避免 5,000 USDT 全放在 Binance 一个场所。
- 成本：每边 0.30%，含手续费、价差、滑点；现货无资金费。

## 证据

### 证据 A：复用的已合并笔记（只作规则来源，不抄 2025–2026 数字）

- `bots/quant/notes/xqt-migration/README.md`、`reproduce.py`、`results.csv`（2026-10-20 运行）：冻结的 TOM/周一规则、`calendar_exact` 与 `orig_shift` 两种写法，以及旧的多折协议。旧笔记的窗口是 2020-12-31～2026-10-13；第 2 轮起加密只用 2022-2024 开发，所以本条只采用它的规则定义，不用它的旧数字，也不把其中 2025-2026 段抄进本条。旧 `results.csv` 的 8 个 M3 规则名与本次回放一致，逐笔数字由本次 `replay/quant-002/` 重算。
- `bots/quant/notes/q012-hist/`、`q006-hist/` 是地震计数和网球 Elo 条目，与本条无关，未复用。

### 证据 B：2022-2024 可成交价回放（新增，`bots/quant/replay/quant-002/`）

- 脚本：`fetch_data.py`（下载/缓存）、`backtest.py`（回放）、`verify_sources.py`（出处复核）；汇总：`SUMMARY.md`；明细：`results_variants.csv`、`trades.csv`、`placebo.csv`；stdout 副本在 `bots/quant/notes/scheduler/scratch/H-quant-002/round2_*.txt`。
- 数据：Binance 日线 + 1h K 线，2022-01-01～2024-12-31，免费免密钥；1d 1,096 行/币，1h 26,303 行/币。
- 成本与成交：主口径次日开盘价，0.30%/边；敏感性首小时 VWAP，0.30%/边。净收益 = `(1+毛收益)×(1−0.003)²−1`；日线净值按收盘盯市，含浮亏。

主口径（次日开盘，0.30%/边，2022-2024）：

| 版本（每边 0.30%，次日开盘） | 窗口数 | 3 年连乘 | 年化 | 最大回撤（日线） | 净均值/窗口 | 净 t | 净单边 p | 盈亏平衡每边成本 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BTC TOM（精确日历） | 35 | −44.51% | −17.84% | −51.75% | −1.60% | −2.46 | 0.990 | −0.50% |
| ETH TOM（精确日历） | 35 | −47.45% | −19.31% | −55.00% | −1.70% | −2.06 | 0.976 | −0.55% |
| BTC 周一（精确日历） | 157 | −38.54% | −14.99% | −55.72% | −0.24% | −0.81 | 0.791 | 0.18% |
| ETH 周一（精确日历） | 157 | −42.21% | −16.72% | −55.61% | −0.26% | −0.76 | 0.775 | 0.17% |
| BTC TOM（原代码，错后一天） | 36 | −12.50% | −4.36% | −27.04% | −0.25% | −0.31 | 0.619 | 0.18% |
| ETH TOM（原代码，错后一天） | 36 | −20.29% | −7.28% | −43.63% | −0.44% | −0.43 | 0.665 | 0.08% |
| BTC 周一（原代码，错后一天） | 156 | −56.02% | −23.97% | −62.37% | −0.49% | −2.26 | 0.988 | 0.06% |
| ETH 周一（原代码，错后一天） | 156 | −74.33% | −36.46% | −79.71% | −0.82% | −3.24 | 0.999 | −0.11% |

- 8 个版本在 0.30%/边、次日开盘下全部为负；换成首小时 VWAP 后仍然 8 个全负（−15.33% 到 −74.03%）。即 8 个规则版本 × 2 种可成交价 = 16 个结果全部为负，没有一个是正的。
- 8 个版本的净均值单边 t 检验 p=0.62–1.00，没有一个显著为正；按本条事先写死的失败标准，全部判“不值得继续”。
- 毛收益层面，BTC 周一（精确）均值 +0.36%/窗口，t=1.21，单边 p=0.114，是 8 个版本里名义上最接近正的；但盈亏平衡每边成本约 0.18%，低于 GUIDE 的 0.30%。同换手随机窗口 placebo（1,000 次，随机星期）中它的毛收益 +57.87% 排 p=0.145——不显著。其余版本的毛均值在 −1.11% 到 +0.35% 之间，没有一个显著为正。
- 逐年看，2024 单年 BTC 周一精确 +13.68%、ETH 周一精确 +29.51%，但同两个版本 2022、2023 均为负，3 年合计 −38.54%/−42.21%；不能拿单年正数翻案。完整逐年数字在 `SUMMARY.md` 和 `results_variants.csv`。
- 第 1 轮曾在 0.10%/边下看到少数正结果，但正结果会随“首小时 vs 末小时”成交时点换一组；本回放只按 GUIDE 的 0.30%/边，不再把 0.10% 当证据，也不引用含 2025 年段的旧数字。

### 证据 C：出处与数字复核（`verify_sources.py` / `_cache/verify_stdout.txt`）

- `https://data.binance.vision/?prefix=data/spot/monthly/klines/BTCUSDT/1d/` 与 ETH 同结构：HTTP 200。
- `https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/1d/BTCUSDT-1d-2024-12.zip`：HTTP 200，zip 成员 `BTCUSDT-1d-2024-12.csv`，31 行 × 12 列；ETH 月包 31 行 × 12 列。
- 完整日线/1h 查询 URL（带 `symbol`、`interval`、`startTime`、`endTime`）：HTTP 200，12 列；分页取完 2022-01-01～2024-12-31。
- `aggTrades` 2024-10-09 00:00–01:00 UTC：43,529 笔；首笔成交价 62,160.50 = 当日日线开盘价 62,160.50（差 0.000000 bp）；逐笔 VWAP 62,126.14842703 = 1h K 线首小时 VWAP 62,126.14842703（差 0.000000 bp）。证明开盘价/VWAP 来自真实成交，不是模型价。
- `known/KNOWN.md` 第 48 行存在 `| E-E2-turn-of-month | 月末月初持有 |`。
- 条目 front matter 的 `id: quant-002`、`date: 2026-10-20`、`status: 待核` 未改。

## 数据

- 日线/1h：`https://data-api.binance.vision/api/v3/klines?symbol=BTCUSDT&interval=1d&startTime=1640995200000&endTime=1735689599999&limit=1000`；`interval=1h` 同结构；`symbol=ETHUSDT` 同结构。免费免密钥，2022-01-01～2024-12-31。
- 月包样例：`https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/1d/BTCUSDT-1d-2024-12.zip`（ETHUSDT 同结构）。
- 逐笔：`https://data-api.binance.vision/api/v3/aggTrades?symbol=BTCUSDT&startTime=1728432000000&endTime=1728435599999&limit=1000`。该免密钥端点只回溯到 2024-10-08，所以逐笔复核用 2024-10-09；日线/1h 覆盖完整 2022-2024。
- 原始缓存放在 `bots/quant/replay/quant-002/_cache/`（已 `_cache/` gitignore，单文件 <1 MB 的 CSV；原始 1h 缓存约 3 MB，只在本地，不进仓库）。

## 两周内怎么检验

- 运行 `cd bots/quant/replay/quant-002 && python3 fetch_data.py && python3 backtest.py && python3 verify_sources.py`；首次下载约 7 分钟，回放约 8 秒，复核约 8 秒。
- 独立结果：TOM 35 个月窗口、周一 156–157 个周窗口，均超过 30；另有 1,000 次同换手 placebo。
- 失败标准（事先写死）：0.30%/边、可成交价下 8 个规则版本 3 年连乘为负，或单窗口净收益 t 检验不显著为正。本条的 8 个版本两项都成立，所以判“BTC/ETH 现货上的 TOM/周一不值得继续”。
- 诚实限制：2022-2024 是规则冻结后的时序样本，不是从未见过的盲样本；真正独立的样本只能从 2026-10 之后前向记录。本条不声称已经过了盲测。

## 成本与容量

- 每个 TOM 窗口进出各一次：0.30%/边 → 每月约 0.60%；周一每周进出一次 → 每月约 2.6%。成本是结果翻负的主因。
- 最好的毛收益版本 BTC 周一（精确）盈亏平衡每边成本约 0.18%；GUIDE 要求按 0.30%/边粗算，故仍为负。0.10%/边下可能为正，但那依赖成交时点，不能当成稳定优势。
- 容量：单币最多 2,500 USDT；5,000 USDT 总资金若同时做 BTC 和 ETH，每个币 1,250 USDT，合计仍不超过 Binance 单场所约 2,500 USDT 的上限。这类窗口每月/每周只进出一次，容量不是问题。
- 对 5,000 USDT 的年化贡献：主变体 BTC 周一精确年化 −14.99%，占用 2,500 USDT 单币袖套，`−14.99% × 2,500 ÷ 5,000 = −7.49%`，字段取 `-7.5%`。最差变体 ETH 周一错位为 `−36.46% × 2,500 ÷ 5,000 = −18.23%`。这是负贡献，正是本条要报告的结论。

## 风险

- 反证只覆盖 BTC/ETH 现货、2022-2024；其他币、期货、不同交易所日界未测。
- 2022-2024 不是盲样本；日历效应若只在特定年份出现，这里可能看不到，也可能被 2022 的熊市放大。
- 次年开盘成交在极端行情可能比 0.30%/边更差；本条没有额外加滑点，0.30%/边是 GUIDE 的粗算口径。
- 未计稳定币利息、交易所托管风险和资金费（现货无资金费）。
- `aggTrades` 免密钥端点历史较短，逐笔复核只能覆盖 2024-10-09 之后；日线/1h 的完整窗口不受影响。

## 改进了什么

不适用（kind: supplement）。相对第 1 轮版本，本条把主成交价从首小时 VWAP 改为次日开盘（GUIDE §9）、把开发窗口收到 2022-2024、并把 Binance 单场所敞口明确限制在 2,500 USDT；结论仍是负，且负得更干净：16/16 结果在 0.30%/边下为负。

## 门槛自查

1. 机制说得清：满足（作为补充）— 检验的是“月初月末资金流”这一已知说法，不另立新机制。
2. 有免费数据能检验：满足 — Binance 日线 + 1h K 线 + aggTrades，全部免密钥，2022-2024 完整。
3. 小资金能做：满足 — 现货、不加杠杆、单币 ≤2,500 USDT；同时做两币则各 1,250 USDT，合计不超过单场所上限。
4. 不重复：满足（作为补充）— known 的 E-E2-turn-of-month 先到；本条只补 2022-2024 的负证据，不另立策略。
5. 扣成本后粗算够用：不满足 — 本条结论正是 0.30%/边下 16/16 为负；不应按正策略收录，只按负证据补充采纳。
6. 两周内能检验：满足 — 35 个 TOM 窗口、156–157 个周一窗口，脚本几分钟内可重跑。
7. 出处可查：满足 — listing/zip/klines/aggTrades URL 全部 200 复核；aggTrades 首笔价与开盘价、VWAP 与 1h K 线完全一致；脚本、stdout、明细全部落盘。

## 出处

- bots/quant/replay/quant-002/fetch_data.py、backtest.py、verify_sources.py、SUMMARY.md、results_variants.csv、trades.csv、placebo.csv — 访问 2026-10-21 — 已读（本次运行）
- bots/quant/notes/scheduler/scratch/H-quant-002/round2_fetch_stdout.txt、round2_backtest_stdout.txt、round2_verify_stdout.txt — 访问 2026-10-21 — 已读（本次运行副本）
- bots/quant/notes/xqt-migration/README.md、reproduce.py、results.csv — 访问 2026-10-21 — 已读（本 bot 2026-10-20 运行；只复用规则定义，不抄 2025–2026 数字）
- https://data.binance.vision/?prefix=data/spot/monthly/klines/BTCUSDT/1d/ — 访问 2026-10-21 — 已读（HTTP 200，2,712 字节）
- https://data.binance.vision/?prefix=data/spot/monthly/klines/ETHUSDT/1d/ — 访问 2026-10-21 — 已读（HTTP 200，2,712 字节）
- https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/1d/BTCUSDT-1d-2024-12.zip — 访问 2026-10-21 — 已读（HTTP 200，31 行 × 12 列）
- https://data.binance.vision/data/spot/monthly/klines/ETHUSDT/1d/ETHUSDT-1d-2024-12.zip — 访问 2026-10-21 — 已读（HTTP 200，31 行 × 12 列）
- https://data-api.binance.vision/api/v3/klines?symbol=BTCUSDT&interval=1d&startTime=1640995200000&endTime=1735689599999&limit=1000 — 访问 2026-10-21 — 已读（HTTP 200，12 列；分页）
- https://data-api.binance.vision/api/v3/klines?symbol=BTCUSDT&interval=1h&startTime=1640995200000&endTime=1735689599999&limit=1000 — 访问 2026-10-21 — 已读（HTTP 200，12 列；分页）
- https://data-api.binance.vision/api/v3/aggTrades?symbol=BTCUSDT&startTime=1728432000000&endTime=1728435599999&limit=1000 — 访问 2026-10-21 — 已读（43,529 笔；首笔价=开盘价，VWAP=1h K 线）
- known/KNOWN.md 第 48 行 `| E-E2-turn-of-month | 月末月初持有 |` — 访问 2026-10-21 — 已读
- 使用者的私有仓库 x-quant-trials — 未访问（私有，不可核实） — 来源自报，未核实（不作为本条证据；`variants_ext` 记 0）
