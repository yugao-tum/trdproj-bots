# 回放汇总：quant-018

条目：`bots/quant/entries/quant-018-strait-transit-count-base-rate.md`
机制：Polymarket「本周 Bab el-Mandeb 海峡通行次数落在哪一档」周度 negRisk 阶梯，用 IMF PortWatch 近 12 个完整周的经验分布当公允值，在外侧档买 NO，持有到 UMA 结算。

回放只做 **Bab el-Mandeb**；条目明确不做 Hormuz（Hormuz 档宽 5 对周 sd 44，基准率无信息量），因此 Hormuz 不是本回放的变体，只是被排除的对象。

## 如何复现

- 脚本：`bots/quant/replay/quant-018/replay.py`（Python 3.13，`pandas`；无网络依赖，读同目录冻结输入）
- 运行：
  ```bash
  python3 bots/quant/replay/quant-018/replay.py
  ```
  输出逐字保存在 `stdout.txt`，逐份成交在 `trades.csv`。
- 输入如何生成：`bots/quant/replay/quant-018/build_inputs.py`（stdout `build_inputs_stdout.txt`；scratch 留有同一脚本 `build_replay_inputs.py` 作证据链）
  - `inputs/buckets_bab.csv`（sha1 `205f1facfdc5a120cbaae3f163166052736ca6e5`）：12 个草稿期 Bab 事件，由合并笔记 `bots/quant/notes/q018-paired/buckets.csv`（sha1 `962b0b2434581fdf75a6ea8210836a6931baa6e3`）原样投影，未改数。
  - `inputs/oos_bab_oct12.csv`（sha1 `420531cd824165f85252917b0a6a5232c0a266c3`）：1 个 post-draft OOS 事件（week of 2026-10-12），数值由 `bots/quant/notes/scheduler/scratch/H-quant-018/tradable_backtest.py` 于 2026-10-21 现场取 Gamma/data-api/PortWatch 得到。
- 数据下载地址（公开、免密钥，访问日期 2026-10-21）：
  - Gamma 事件与规则、`outcomePrices`、`feesEnabled`：`https://gamma-api.polymarket.com/events?slug=<event-slug>`
  - 逐笔成交（入场价唯一来源）：`https://data-api.polymarket.com/trades?market=<conditionId>&limit=500&offset=<n>`
  - 结算源日度计数：`https://services9.arcgis.com/weJ1QsnbMYJlCHdG/arcgis/rest/services/Daily_Chokepoints_Data/FeatureServer/0/query?where=portname = 'Bab el-Mandeb Strait'&outFields=date,n_total&returnGeometry=false&f=json&resultOffset=0&resultRecordCount=1000&orderByFields=date ASC`
  - 同族事件清单：`https://gamma-api.polymarket.com/public-search?q=how%20many%20ships%20transit`
- 数据本身起点：PortWatch 2019-01-01；本回放实际使用的事件窗口 **2026-07-20..2026-10-18**（POLYMARKET，不受加密 2022–2024 窗口限制）。
- 开发窗口：**2026-07-20..2026-10-18**。其中 2026-07-20..2026-10-05 的 12 个事件是草稿期历史；2026-10-12 是条目快照之后才结算的唯一 post-draft OOS，单独列出，不混入主结果。
- 切分依据：Polymarket 无强制窗口；这里按“草稿快照 2026-10-20 之前已结算”与“之后才结算”切成开发段和 1 个 OOS，未按结果调参。

## 成交和成本

- 决策时点 `T` = 事件周周一 00:00 UTC。
- 模型：严格早于 `T` 的最近 12 个完整 Mon–Sun PortWatch 周，按当期档位计频数，Laplace `p_i=(k_i+1)/(12+n)`。
- 入场价：`[T−24h, T]` 内 data-api 的**最后一笔真实成交**，YES 成交取 `p`、NO 成交取 `1−p`；同一秒多笔时取该秒**最高 YES 价**（对 NO 买方最差）；窗口内无成交则该档不成交。没有使用 CLOB `prices-history` 当成交价。
- 触发：`p_yes ≥ p_model + half_spread + 0.01`；基础 `half_spread=0.01`，压力 `0.05`，压力下**重新判定触发**。
- 全部成本：吃单价 `1−p_yes+half_spread`；手续费按 Gamma `feesEnabled/feeSchedule`，13 个事件全部 `feesEnabled=false`，费率 **0**（地缘板块 GUIDE §8 也是 0）。没有另加滑点，买卖价差已由 `half_spread` 承担。
- 资金和容量：每档 1 份回放；条目实盘上限为每档 100 份、单 event 200 USDT、本条专线 1,000 USDT、单场所不超过 2,500 USDT。不加杠杆，NO 买单最大亏损是本金。

## 汇总结果

- 独立结果数及计法：按 **weekly event** 计，不按档、不按市场。基础口径有触发成交的独立事件 **10 个**（草稿期 9 + OOS 1），**小于 GUIDE §2 要求的 30**。13 个事件共 21 个成交份额；另有 22 个档位在 `[T−24h,T]` 内无成交，不计入。
- 扣成本后净收益（`replay.py` 原样）：
  - 全样本 base 1¢：21 份 / 10 事件，总净 **+0.7116 USDT**，投入 15.2884 USDT，每美元 **+0.0465**；份额中位 **+0.2400/份**；但事件中位仅 **+0.0850**，事件 5 胜 5 负。
  - 草稿期 12 事件 base 1¢：18 份 / 9 事件，总净 **+0.1216 USDT**，每美元 **+0.0094**；事件中位 **−0.1800**，事件 4 胜 5 负。
  - 5¢ 压力：全样本 18 份 / 10 事件，总净 **+0.2416 USDT**，每美元 **+0.0176**；草稿期 15 份 / 9 事件，总净 **−0.2284 USDT**，每美元 **−0.0203**。
  - 事件聚类 bootstrap（10,000 次，种子 20261021）：全样本每份均值 95% 区间 **[-0.158, +0.188]**，每美元 **[-0.216, +0.261]**，都跨 0。
- 最大回撤：本回放是 1 份/档的份额曲线，事件序列最大回撤 **−1.4600 USDT**（按 200 USDT/event 上限折 **−0.73%**）。Polymarket 条目的 `max_dd` 字段按 GUIDE §7 填 `-`；这不是账户级回撤。
- 对 5,000 USDT 的年化贡献：草稿期每美元 **+0.0094** × 200 USDT/event × 每年约 **39** 次触发（Bab 每周 1 个 event、9/12 有触发）÷ 5,000 = **1.5%**。这是粗算；bootstrap 区间跨 0，不能当保证。
- result：**不显著**（独立事件 10 < 30；且全样本区间跨 0、草稿期事件中位为负）。
- 不可靠或失败原因：
  1. 有触发成交的独立事件只有 **10 个 < 30**；同点全档有价事件 24/43 < 30。门 6 不满足。
  2. 份额中位 +0.24 是份额口径，事件层中位只有 +0.085（草稿期 −0.18），不能读成“稳定盈利”。
  3. data-api 只给已成交打印，不给当时订单簿深度；1¢/5¢ 价差是预先假设，薄市场可能更差。
  4. PortWatch 是当前修订版，不是 `T` 时点的 vintage；2026-03 至 05 有 7 周与结算不一致。
  5. 唯一 post-draft OOS（2026-10-12）为 +0.5900（3 份），只有 1 个事件，不能当显著性证据。

## 所有变体（所有市场都要写，看了不用的也算）

- variants（自己的）：**2**
- variants_ext（外部来源）：**-**（未引用外部来源的变体数；dot-051 只作周起点价 Brier 的交叉核对，不算变体）

| 序号 | 自己 / 外部来源 | 规则与全部参数 | 窗口 | 结果和位置 |
|---|---|---|---|---|
| V1 | 自己 | Bab NO；12 周 Laplace；`[T−24h,T]` 最后一笔成交；触发 `p_yes ≥ p_model+0.01+0.01`；`half_spread=0.01`；费 0；1 份/档 | 2026-07-20..2026-10-18 | 21 份/10 事件，总净 +0.7116，每美元 +0.0465；草稿期 9 事件每美元 +0.0094；`trades.csv` case=`base_1c` |
| V2 | 自己 | 同 V1，但 `half_spread=0.05` 并**重新判定触发**；费 0；1 份/档 | 2026-07-20..2026-10-18 | 18 份/10 事件，总净 +0.2416；草稿期每美元 −0.0203；`trades.csv` case=`stress_5c` |

未作为交易变体、但看过的诊断（不计入 `variants`）：

- Hormuz 同规则：条目明确排除（档宽 5 vs 周环比中位 13），只在 `notes/q018-price-test`、`notes/q018-paired` 里作 Brier 对照，未交易。
- 市场首价 vs 周起点价 Brier：0.7436（起点价，34 事件）优于模型 0.7747，差 −0.0310（t=−0.473，p=0.6365），见 `notes/scheduler/scratch/H-quant-018/brier_start_check_stdout.txt`；这是校准检查，不是交易变体。
- 草稿期按 2026-09-01 事后切两段：前段 −0.0184、后段 +0.1400，非预注册，只有描述意义。
