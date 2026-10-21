# 回放汇总：quant-003

十币广度闸门时序动量（Breadth-gated spot momentum）在真实可成交价格上的第 2 轮回放。数据窗口严格限定在 2022-01-01..2024-12-31；**没有下载、运行或报告 2021 年及以前、2025-01-01 以后的数据**。

## 如何复现

- 脚本：`bots/quant/replay/quant-003/replay_quant003.py`（Python 3，只用 stdlib + pandas/numpy；本机 pandas 3.0.6、numpy 2.5.4）。
- 运行：
  ```bash
  cd bots/quant/replay/quant-003
  python3 replay_quant003.py            # 首次运行会把 360 个月线 zip 下到 ./_cache/（已 .gitignore）
  python3 diagnose_replay.py            # 逐折对比、t 值、独立区段检查
  ```
  也可指定已有缓存：`python3 replay_quant003.py --cache <dir>`。只想先下数据可用 `python3 fetch_data.py`。
- 参数（全部）：
  - 币池：赛前冻结的 Binance 现货 USDT 前十，名单 `BTC, ETH, XRP, LTC, GRT, BCH, LINK, BNB, ADA, XLM`；名单和选取规则来自已合并笔记 `bots/quant/notes/r2prep-verification/quant-003.md` 的 PRESPEC_R003（按 2020-12 报价成交额排序），本次不重排、不重选。
  - 动量：`mom_t = close_t / close_{t-60} - 1`（B1 为 30 日）。
  - 广度：`B_t` = 池内 `mom_t > 0` 的币数；闸门 `B_t >= k` 时等权持有正动量币，否则全现金。主结果 k=6；k=1..10 全部报告，k=1 即无闸门对照。
  - 波动目标：被选币 60 日已实现波动（日收益标准差 × √365）加权平均，缩放 `min(0.30/avg_vol, 1)`，不加杠杆。
  - 调仓：每 5 个交易日一次；信号在 close(t) 计算，**在 open(t+1) 成交**。
  - 成本：每边 0.30%，按 `|Δweight|` 在成交时点计。
  - 收益计量：open-to-open，`r(t) = open(t+1)/open(t)-1`，权重在 open(t) 生效。
- 数据下载地址（公开、免密钥，访问 2026-10-21）：
  - 月线模板：`https://data.binance.vision/data/spot/monthly/klines/<SYM>/1d/<SYM>-1d-<YYYY-MM>.zip`
  - 实测 HTTP 200 的例子：`https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/1d/BTCUSDT-1d-2022-01.zip`（2,183 B）、`.../BTCUSDT-1d-2024-12.zip`（2,218 B）、`.../GRTUSDT-1d-2022-01.zip`（1,797 B）、`.../XLMUSDT-1d-2024-12.zip`（1,845 B）。
  - 目录/S3 清单：`https://data.binance.vision/?prefix=data/spot/monthly/klines/BTCUSDT/1d/`（HTTP 200）、`https://s3-ap-northeast-1.amazonaws.com/data.binance.vision?delimiter=/&prefix=data/spot/monthly/klines/BTCUSDT/1d/`（HTTP 200）。
- 数据本身起点：所选 10 个币在 2022-01-01 都已有日线（BTC 及多数币更早；本次只取 2022-01 起）。GRT 等币的 2022-01 文件均存在。
- 开发窗口：`2022-01-01..2024-12-31`；指标预热从窗口起点开始，2022 年头两个月因 60 日动量不足而空仓/低仓，不做窗口外预热。
- 切分依据：GUIDE 第 9 节，加密只在 2022-01-01..2024-12-31 开发；年度折 2022、2023、2024。
- 复现输出：`results_replay.csv`、`results_percoin.csv`、`equity_curve.csv`、`k6_weights.csv`、`replay.stdout.txt`；逐折/差值诊断用 `diagnose_replay.py`（输出 `diagnostics.stdout.txt`）；URL 核验见 `source_check.txt`。同样内容备份在 `bots/quant/notes/scheduler/scratch/P-quant-003/`。

## 成交和成本

- 成交价和时点：Binance 现货日线 **下一根 K 线开盘价**。close(t) 出信号，open(t+1) 成交；组合收益按 open-to-open 计算，无前视。不是用收盘价成交。
- 全部成本：每边 0.30%（手续费/价差/滑点粗算），按 `|Δweight|` 计，已在所有净收益里扣除。资金费不适用（现货、无杠杆）。
- 资金和容量：总资金 5,000 USDT；权重和 ≤1，不加杠杆。k=6 平均总敞口 0.19，约 950 USDT，单一场所 Binance 现货，远低于 2,500 USDT 上限。

## 汇总结果

- 独立结果数及计法：k=6 在 2022-2024 有效样本 1,036 天里有 **44 个“广度不足、转现金”区段**（风险关闭 556 天）。按 GUIDE 第 2 节按事件数计；同一轮下跌可能造成相邻区段不完全独立，44 是上限口径。
- 扣成本后净收益：**+61.82%**（2022-01-01..2024-12-30，1,095 个日收益），CAGR **+17.40%**。生成：`replay_quant003.py` → `results_replay.csv` 的 `GATE_k6` 行。
- 最大回撤：**−20.01%（日线，含浮亏）**。
- 对 5,000 USDT 的年化贡献：**17.40%**，即约 870 USDT/年。算法：策略权重已经是账户资金的比例（和 ≤1），净 CAGR 直接作用于 5,000 USDT 总资金；平均只占用约 950 USDT。
- result：**正**（净收益为正，独立结果 44 ≥ 30）。但这只是绝对收益；**相对 plain tsmom 的增量证据为负**，见下。
- 不可靠或失败原因：
  1. k=6 全期净收益 +61.82% 低于 B1 plain 30 日 tsmom 篮子 +88.73%，复合差 **−26.92 个百分点**；CAGR 17.40% vs 23.58%；Sharpe 0.92 vs 0.99。只有最大回撤更低（−20.01% vs −23.86%）。
  2. 三个年度折的 Sharpe 只在 **1/3** 折（2024）高于 B1；2022 −0.92 vs −0.33，2023 1.16 vs 1.99。原预登记要求 ≥4/6 折；在本窗口同构地看只有 1/3，远不达标。
  3. 日收益差 k6−B1 = −6.24%/年，年化波动 15.90%，t = −0.68（n=1,095），相关 0.762；差异不显著且点估计为负。
  4. k 网格里无闸门 k=1 的净收益最高（+64.05%），k=7 的 Sharpe 最高（0.97，事后看），k=6 不是任何指标的最优点；“多数闸门”没有稳定增量。
  5. 样本只有 3 个年度折、一个完整的牛熊周期（2022 熊、2023-2024 牛），独立区段 44 个但彼此相关，证据强度有限。
- 结论：**建议放弃（DROP）**。保留为反证可以，但不应当作可提交的独立优势；若主项目需要“广度闸门无效”的反例，可标待核作反证。

## 所有变体（所有市场都要写，看了不用的也算）

- variants（自己的）：**23**
- variants_ext（外部来源）：**-**（没有引用外部来源的策略结果；旧笔记是本仓库自己的前一轮研究，不是外部来源）

计数口径：k 网格 k=1..10 共 10 个；B1（30 日篮子）、B4（等权买入持有）、事后 30 日闸门各 1 个，共 13 个组合变体；再加 10 个逐币 plain 30 日 tsmom = 23。B2（60 日 plain 篮子）与 k=1 规则参数完全相同，只作对照行列出，不重复计数。

| 序号 | 自己 / 外部来源 | 规则与全部参数 | 窗口 | 结果和位置 |
|---|---|---|---|---|
| 1 | 自己 | GATE k=1，60d 动量，30% 波动目标，5 日调仓，0.30%/边 | 2022-01-01..2024-12-31 | 净 +64.05%，CAGR 17.94%，MDD −34.43%，Sharpe 0.79；`results_replay.csv` |
| 2 | 自己 | GATE k=2，其余同上 | 同上 | 净 +34.04%，CAGR 10.26%，MDD −35.40%，Sharpe 0.54；同上 |
| 3 | 自己 | GATE k=3，其余同上 | 同上 | 净 +43.68%，CAGR 12.84%，MDD −34.55%，Sharpe 0.66；同上 |
| 4 | 自己 | GATE k=4，其余同上 | 同上 | 净 +53.51%，CAGR 15.36%，MDD −24.06%，Sharpe 0.81；同上 |
| 5 | 自己 | GATE k=5，其余同上 | 同上 | 净 +60.36%，CAGR 17.05%，MDD −24.06%，Sharpe 0.89；同上 |
| 6 | 自己 | GATE k=6（主结果），其余同上 | 同上 | 净 +61.82%，CAGR 17.40%，MDD −20.01%，Sharpe 0.92；同上 |
| 7 | 自己 | GATE k=7，其余同上 | 同上 | 净 +57.96%，CAGR 16.46%，MDD −13.54%，Sharpe 0.97；同上 |
| 8 | 自己 | GATE k=8，其余同上 | 同上 | 净 +48.09%，CAGR 13.98%，MDD −12.07%，Sharpe 0.94；同上 |
| 9 | 自己 | GATE k=9，其余同上 | 同上 | 净 +32.99%，CAGR 9.97%，MDD −12.97%，Sharpe 0.76；同上 |
| 10 | 自己 | GATE k=10，其余同上 | 同上 | 净 +7.20%，CAGR 2.34%，MDD −24.10%，Sharpe 0.25；同上 |
| 11 | 自己 | B1：plain 30d tsmom 篮子，30% 波动目标，5 日调仓，0.30%/边 | 同上 | 净 +88.73%，CAGR 23.58%，MDD −23.86%，Sharpe 0.99；同上 |
| 12 | 自己 | B2：plain 60d tsmom 篮子（= GATE k=1） | 同上 | 净 +64.05%，CAGR 17.94%，MDD −34.43%，Sharpe 0.79；同上 |
| 13 | 自己 | B4：10 币等权买入持有，5 日调仓，无波动目标 | 同上 | 净 +38.20%，CAGR 11.39%，MDD −71.08%，Sharpe 0.49；同上 |
| 14 | 自己 | POSTHOC：30d 动量 + k=6 闸门（事后诊断，非预登记） | 同上 | 净 +39.83%，CAGR 11.82%，MDD −27.03%，Sharpe 0.67；同上 |
| 15 | 自己 | BTC 单币 plain 30d long/flat，无波动目标，5 日调仓 | 同上 | 净 +135.46%，CAGR 33.04%，MDD −51.13%，Sharpe 0.91；`results_percoin.csv` |
| 16 | 自己 | ETH 单币，同上 | 同上 | 净 +43.44%，CAGR 12.78%，MDD −37.14%，Sharpe 0.49；同上 |
| 17 | 自己 | XRP 单币，同上 | 同上 | 净 +129.39%，CAGR 31.88%，MDD −44.35%，Sharpe 0.76；同上 |
| 18 | 自己 | LTC 单币，同上 | 同上 | 净 −11.67%，CAGR −4.05%，MDD −52.10%，Sharpe 0.21；同上 |
| 19 | 自己 | GRT 单币，同上 | 同上 | 净 +82.48%，CAGR 22.20%，MDD −61.25%，Sharpe 0.62；同上 |
| 20 | 自己 | BCH 单币，同上 | 同上 | 净 −37.48%，CAGR −14.49%，MDD −71.84%，Sharpe 0.07；同上 |
| 21 | 自己 | LINK 单币，同上 | 同上 | 净 +22.07%，CAGR 6.87%，MDD −70.34%，Sharpe 0.42；同上 |
| 22 | 自己 | BNB 单币，同上 | 同上 | 净 +19.64%，CAGR 6.16%，MDD −43.43%，Sharpe 0.35；同上 |
| 23 | 自己 | ADA 单币，同上 | 同上 | 净 +99.28%，CAGR 25.84%，MDD −51.25%，Sharpe 0.68；同上 |
| 24 | 自己 | XLM 单币，同上 | 同上 | 净 +149.08%，CAGR 35.55%，MDD −54.32%，Sharpe 0.72；同上 |

（表格 24 行 = 13 个组合变体 + B2 重复对照 + 10 个单币；计数的 23 个不含重复的 B2。）

## 与旧证据的关系（复用已合并笔记）

- 旧的第 1 轮证据在 `bots/quant/notes/r2prep-verification/quant-003.md`：6 个年度折（2021–2026），close-to-close 收益，结论 ABANDON。该笔记里的币池名单（`universe_top10.csv`）和预登记判据被本次直接复用。
- 但旧笔记的窗口含 2021 和 2025–2026，且用 close-to-close 而非下一根开盘价，不满足第 2 轮加密回放口径，所以本次**重新跑**了 2022–2024 的 next-open 回放；旧记录里窗口外的数字不再作为本条目证据引用。
