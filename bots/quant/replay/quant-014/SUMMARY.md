# 回放汇总：quant-014

对应条目：`bots/quant/entries/quant-014-pm-spx-lognormal-calibration.md`。
本回放是**可成交价**（data-api 逐笔成交）历史回测，不是 CLOB `prices-history` 中间价回测。完整采集脚本沿用已合并的 `bots/quant/notes/q014-hist/q014_hist.py`（2026-10-21 v2），本目录保存其冻结副本 `replay.py` 与逐腿明细 `events.csv`；离线复算脚本 `summarize.py` 不需要网络。

## 如何复现
- 采集 + 回测（需要网络）：
  ```bash
  cd bots/quant/replay/quant-014
  python3 replay.py          # 首次会抓 Gamma/data-api/FRED；原始响应写入本地 _cache/（不入库）
  ```
  依赖：Python 3.11+、`requests`、`zoneinfo`（stdlib）。
- 离线复算（只用本目录冻结明细，不需要网络）：
  ```bash
  cd bots/quant/replay/quant-014
  python3 summarize.py       # 逐位复现主结果、fee=0、OOS、Brier、贡献
  ```
- 出处复核（需要网络，只读公开接口）：
  ```bash
  python3 verify_sources.py  # 2026-10-21 运行：OK=40 FAIL=0；stdout 见 notes/scheduler/scratch/H-quant-014/verify_sources_stdout.txt
  ```
- 参数（冻结，未按结果调参）：
  - 模型：零漂移对数正态；`sigma` = 决策日前 20 个交易日对数收益的年化标准差（`stdev * sqrt(252)`）；`T = 剩余交易日 / 252`；`P(S_T>K)=Phi((ln(S/K)-sigma^2*T/2)/(sigma*sqrt(T)))`；日频 Up/Down 直接取 `P(up)=0.5000`（entry 原文）。
  - 报价：决策时点前 6 小时窗口内**最后一笔 data-api 成交**为 `p_yes`；`ask=p_yes+0.01`、`bid=p_yes-0.01`（1¢ tick，entry 的半价差假设）。`No`/`Down` 成交按 `1-price` 映射。
  - 阈值：`2*(fee+half_spread)`；`fee=0.04*p*(1-p)`；`half_spread=0.01`。买 YES 当 `p_model-ask >= threshold`；买 NO 当 `bid-p_model >= threshold`；持有到 `outcomePrices`。
  - 仓位：每条触发腿 1 份用于统计；贡献换算按 entry 的 100 份/腿上限。
  - 独立结果：一个 event（同一交易日/同一结算源）算 1 个；日频 event 1 条腿，阶梯 event 多档。
  - 多重检验：`summarize.py` 的 `variants=5` 全部列出；日频 FADE 的 95% CI 用 ISO 周 cluster bootstrap（10,000 次，seed 20261020）。
- 数据下载地址和访问日期（均为免费、免密钥公开 GET）：
  - Gamma 规则/结算/盘口：`https://gamma-api.polymarket.com/events?series_id=10383`、`series_id=10603`、`series_id=10856`、`?slug=...`、`https://gamma-api.polymarket.com/public-search?...` — 访问 2026-10-20（采集）/ 2026-10-21（复核）。
  - 可成交价：`https://data-api.polymarket.com/trades?market=<conditionId>&limit=500&offset=N` — 访问 2026-10-20，共 303 个 market / 243,699 笔成交。
  - SPX 日线：`https://fred.stlouisfed.org/graph/fredgraph.csv?id=SP500` — 访问 2026-10-20。复核用 `https://query1.finance.yahoo.com/v8/finance/chart/%5ESPX?range=6y&interval=1d`，截到 2021-10-20..2026-10-19，1,254 根，σ 与 entry 逐位一致。
  - CLOB 仅用于复核“已关闭市场大多没有价格历史”：`https://clob.polymarket.com/prices-history?market=<YES token>&interval=max&fidelity=60` — 访问 2026-10-20 / 2026-10-21；100 个已关闭日频 event 中 22 个非空（2026-09-21..2026-10-20），不是成交价来源。
- 数据本身起点：Gamma 事件 2025-10-15；FRED 模型输入 2016-10-20（只作 sigma 预热，首个计价日 2025-10-15）。
- 开发窗口：`2025-10-15..2026-06-30`；OOS：`2026-07-01..2026-10-19`。完整 `window:` 字段写 `2025-10-15..2026-10-19`。
- 切分依据：Polymarket 无 2022–2024 加密窗口限制；按事件日期先 70% / 后 30% 做时间切分，后 30% 不参与规则选择，只用于 OOS 复核。

## 成交和成本
- 成交价和时点：决策时点之前 6 小时窗口内**最后一笔真实成交**（data-api），不使用更早价格，不以后见价格成交；`ask/bid` 在成交价上加减 1¢。无盘口深度数据，因此“100 份能否在 ask 上成交”仍**未量化**；这是回放的主要乐观假设。
- 全部成本：吃单费 `0.04*p*(1-p)`/份 + 半个买卖价差 1¢/份；未计 maker 返佣、结算滞后资金成本。2026-10-21 复核发现这些 SPX finance 市场当前 `feeType=zero_fees`、`rate=0`（2026-10-20 快照为 0.04）；回放仍按 0.04 计，**成本取高、结果偏保守**，另给 fee=0 敏感性。
- 资金和容量：每条腿 100 份，单 event ≤300 USDT、同时 ≤3 个 event；日频约 21 event/月，阶梯 1–2 event/月。成交额几千到十几万美元/event（Gamma 自报），但宽价差使实际可放金额远小于该数。

## 汇总结果
- 独立结果数及计法：**259 个 event**（252 日频 + 2 weekly above + 3 monthly above + 2 monthly close），303 条腿；229 个 event 至少触发一条腿，240 条腿触发。日频 FADE 子集 **194 个 event / 54 个 ISO 周**。
- 扣成本后净收益（`python3 summarize.py` 输出，抄自 `summarize_stdout.txt`）：
  - 全部触发腿：均值 **−0.00743/份**，中位数 **−0.14482**，命中率 0.258，总净 **−1.783** 份，每 $1 投入 **−0.0287**。
  - 日频 FADE 子集：毛 **+0.02267/份**，扣费 **+0.00650/份**，中位数 **−0.14482**，总净 **+1.261**；ISO 周 bootstrap 95% CI **[-0.04872,+0.06235]**，跨 0。
  - 日频 FOLLOW（entry 原测试方向）：毛 **−0.02267**，扣费 **−0.03835**，总净 **−7.440**。
  - 阶梯：monthly above **−0.06948/份**（9 条腿），monthly close **−0.13662/份**（7 条腿），两个方向都负。
  - OOS（2026-07-01..2026-10-19）：全部触发腿 **−0.03452/份**（72 条腿，总净 −2.486）；日频 FADE **−0.02703**，FOLLOW **−0.00451**，两者都负。
  - 校准：日频 252 event，模型 Brier **0.25000**，常数 0.53 **0.24923**，市场 p6 **0.17783**；OOS 模型 0.25000、常数 0.53 0.25327、市场 0.14319。模型（0.5）不比常数 0.53 好，远不如市场报价。
- 最大回撤：不适用（Polymarket 事件型、无按日盯市的账户权益曲线；`max_dd: -`）。若按逐 event 已实现损益序列看，样本内累计净值为 −1.783 份、无正收益段。
- 对 5,000 USDT 的年化贡献：按 100 份/触发腿、样本约一年，`−1.783 × 100 ÷ 5,000 = −3.57%`；fee=0 时 `−0.216 × 100 ÷ 5,000 = −0.43%`。两种口径都 ≤0，且容量只有几百 USDT。
- result：**负**（GUIDE 第 7 节：扣全部成本后为负，独立结果 ≥30）。
- 不可靠或失败原因：
  1. 数据只有 2025-10-15..2026-10-19 约一年、一个上涨为主的波动率 regime；252 个日频 event 高度相关，不能外推到别的年份。
  2. data-api 每个 market 最多约 2 万笔；更早的 SPX 日频市场取不到逐笔成交，故无法做 2022–2024 或更长的样本。
  3. 没有历史盘口深度；`ask=trade+1¢` 是近似，100 份的成交概率与逆向选择未量化。
  4. 阶梯只有 7 个已结算 event，且决策固定在结算前 6 小时/前一日，`T≈1/252`；**没有复现 entry 对“到期前约 72 天远端阶梯”的原始主张**，所以阶梯结论只覆盖临近到期。
  5. 结算源是 WSJ（日频）/Yahoo `^GSPC`（月度）/Pyth（NVDA），模型输入是 FRED SP500；随机 5 个结算日交叉核对 5/5 一致，但档界附近仍可能有几分钱差异。
  6. 未计 maker rebate、结算滞后资金占用；2026-10-21 复核发现当前吃单费率为 0，回放按 0.04 计偏保守。

## 所有变体（所有市场都要写，看了不用的也算）
- variants（自己的）：**5**
- variants_ext（外部来源）：**-**

| 序号 | 自己 / 外部来源 | 规则与全部参数 | 窗口 | 结果和位置 |
|---|---|---|---|---|
| 1 | 自己 | 主规则：close−6h 决策；`sigma=20d`；`fee=0.04`；`half_spread=0.01`；阈值 `2*(fee+half_spread)`；全部 SPX 收盘 event | 2025-10-15..2026-10-19 | 全部触发腿均值 −0.00743/份，总净 −1.783；`summarize.py` PRIMARY 段 |
| 2 | 自己 | 同 1，成本敏感性 `fee=0`（2026-10-21 实际费率） | 2025-10-15..2026-10-19 | 均值 −0.00090/份，总净 −0.216；仍为负；`summarize.py` fee 0 行 |
| 3 | 自己 | 时点敏感性：前一个美股收盘决策；其余参数同 1 | 2025-10-15..2026-10-19 | 86 条触发腿均值 +0.06948/份；日频 83 event 均值 +0.07425，95% CI [-0.02342,+0.17149]，不显著；`notes/q014-hist/run_output.txt` SENSITIVITY 段 |
| 4 | 自己 | 日频子集 `|p6−0.5|≥0.10`，FADE（模型 0.5 反向做），fee=0.04 | 2025-10-15..2026-10-19 | 194 条腿均值 +0.00650/份，中位数 −0.14482，CI 跨 0；`summarize.py` FADE 行 |
| 5 | 自己 | 日频子集同 4，FOLLOW（entry 原文“按 p6 那一侧吃单”），fee=0.04 | 2025-10-15..2026-10-19 | 194 条腿均值 −0.03835/份，总净 −7.440；`summarize.py` FOLLOW 行 |

补充（不另计变体，同一套参数的时间子段）：OOS `2026-07-01..2026-10-19` 全部触发腿均值 −0.03452/份；见 `summarize.py` OUT-OF-SAMPLE 段。外部来源没有做过同族回测，`variants_ext=-`。
