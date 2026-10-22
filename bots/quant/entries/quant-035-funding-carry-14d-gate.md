---
id: quant-035
name_zh: 现货对冲收资金费：14日正费闸门
name_en: Delta-neutral funding carry with a 14-day positive-funding gate
bot: quant
date: 2026-10-21
market: crypto
pm_category: -
kind: improvement
improves: composer-003
category: A
return_type: carry
instruments: SOL, XRP, ADA, AVAX, HYPE
venues: Binance（现货 + USDⓈ-M 永续）、Hyperliquid（HYPE 现货 @107 + 永续）
data: Binance 月度归档 2022-01..2024-12（现货/永续/mark 1h + funding，免密钥）；Hyperliquid /info 2024-12-05..2024-12-31（HYPE 4h 现货/永续 + 1h funding，免密钥）；未用 2021 年及以前、未用 2025 以后
test_2w: 每次建仓到平仓算 1 个独立结果；14 天窗口预计 0–2 个，少于 30 个；失败标准为期末扣成本净损益≤0 或占用超限
status: 待核
confidence: 中
evidence: 回放
result: 正
slot: -
variants: 94
variants_ext: -
window: 2022-01-01..2024-12-31
max_dd: 1.95%（日线）
contribution: 3.47%
---

## 一句话

在 Binance 对 SOL/XRP/ADA/AVAX、在 Hyperliquid 对 HYPE：**现货多 + 同币 1x 永续空**，两腿等币量；仅当该币 **14 天滚动平均资金费 > 0** 时持有，均值转负才平仓；收资金费，不押方向。

## 钱从哪里来

正资金费时，永续多头按 `q × mark × rate` 付钱给空头。现货多头对冲币价，空头永续收这笔现金流；负资金费时空头反付。持续存在的原因是杠杆多头拥挤：当永续需求强于现货、或做多杠杆需要排队时，永续相对现货溢价，资金费为正。14 天均值闸门不是预测方向，而是过滤掉“资金费接近 0 或为负”的时段，降低频繁开平的费用和负费暴露；它滞后于资金费拐点，不保证每次都在正费期。

这不是无风险收益：基差变化、保证金、交易所和稳定币风险仍在。5,000 USDT 账户、单场所不超过约 2,500、1x 全抵押，最大损失以投入该场所的现货+保证金为上限，不借钱、不做空现货。

## 规则

**币和场所（固定篮子，不按行情挑）**

| 币 | 现货腿 | 永续腿 | sleeve 目标名义 | sleeve 预算（现货+保证金+费） |
|---|---|---|---:|---:|
| SOL | Binance SOLUSDT 现货 | Binance SOLUSDT USDⓈ-M 永续 | 300 USDT | 600 USDT |
| XRP | Binance XRPUSDT 现货 | Binance XRPUSDT USDⓈ-M 永续 | 300 USDT | 600 USDT |
| ADA | Binance ADAUSDT 现货 | Binance ADAUSDT USDⓈ-M 永续 | 300 USDT | 600 USDT |
| AVAX | Binance AVAXUSDT 现货 | Binance AVAXUSDT USDⓈ-M 永续 | 300 USDT | 600 USDT |
| HYPE | Hyperliquid 现货 `@107`（HYPE/USDC） | Hyperliquid `HYPE` 永续 | 1,200 USDT | 2,450 USDT |

**信号**

对每个币、每个资金费时间戳 `t`（Binance 通常 8h，Hyperliquid 1h，以实际 `fundingTime` 为准）：

```
window(t) = 所有 fundingTime > t - 14*24h 且 <= t 的资金费率
mean14(t) = mean(window(t))
```

- 必须有完整 14 天观测（`window(t)` 最早一条 ≤ `t - 14*24h`）；预热不足空仓。
- `mean14(t) > 0` 且空仓 → 开仓；`mean14(t) < 0` 且持仓 → 平仓；等于 0 不动。
- 不按当期单次资金费的正负做决定；当期负费但 14 天均值仍正时继续持有，接受负费。

**执行**

1. 决策在 `t`；成交在 `t` 之后下一根 K 线开盘。回放：Binance 1h、HYPE 4h（历史 1h 被 Hyperliquid 公开 API 裁剪；前向按 1h）。不使用未来价格。
2. 两腿同时成交：现货买入 `q`，永续卖出 `q`。数量：
   ```
   q = min(target / spot, budget / ((spot + perp) * (1 + 0.003)))
   ```
3. 费用：`0.003 × q × (spot + perp)`，开、平各一次；一个往返为名义的 1.2%。
4. 资金费：持仓期间每个 `t` 且 `entry_time < t`，`funding_cash = q × mark(t) × rate(t)`；正收负付。`mark` 用 Binance `markPriceKlines` 1h 开盘（HYPE 用永续 4h 开盘）。
5. 平仓：卖出全部现货、买回全部永续；该 episode 净损益：
   ```
   pnl = q*((spot_exit-spot_entry)+(perp_entry-perp_exit))
         + funding_cash_sum - entry_fee - exit_fee
   ```
6. 风控：1x、不借币、不做空现货；单场所 ≤2,500、总 ≤5,000；不加止损，唯一平仓条件是信号转负。窗口末仍持仓的，按窗口最后一根 K 线收盘价强制平仓并计费用（回放口径）。

**与 dot-019 / composer-003 的区别**

| 项目 | dot-019 | composer-003 | quant-035 |
|---|---|---|---|
| 机制 | 现货多+永续空收浮动资金费 | 同机制 + 30 期 z-score 闸门 | 同机制 + 14 天滚动均值闸门 |
| 场所 | Binance | OKX | Binance（四币）+ Hyperliquid（HYPE） |
| 样本 | 2024-01–2026-09（含 2025 以后；该段结果见原文） | 2025 年以后（该段结果见原文） | **2022-01–2024-12**，不含 2025+ |
| 价格 PnL | 未做完整两腿模拟 | 仅资金费，未做完整两腿 PnL | 实际现货/永续 1h/4h K 线，含基差 |
| 成本 | 固定费用算术，非完整策略 | 0.30%/边粗算，未逐笔 | 0.30%/腿/边逐笔 + 实际资金费 |
| 币 | BTC/ETH/SOL | SOL/XRP/ADA/AVAX | SOL/XRP/ADA/AVAX/HYPE |
| 独立结果 | 未知/非 episode | 资金费结算点，非 episode | 55 个 episode；保守 51 个唯一开仓时间 |

本条不是“新机制”，而是把 composer-003 的 z-score 闸门换成 **时间窗口的均值闸门**，并补上 2022–2024 的完整两腿回放、成本和 HYPE。用同一 2022–2024 SOL 窗口对照：30-event z>0.5 有 378 个 episode、净 **-5,271.08 USDT**（费用主导）；14 天均值闸门 11 个 episode、净 **+797.33 USDT**（1,200 名义，见 `variants.csv`）。这是本条“改进了什么”的直接证据。

## 证据

**回放结果（本条自算，脚本 `replay/quant-035/replay.py`，产物 `SUMMARY.md`/`trades.csv`/`variants.csv`）**

- 窗口 2022-01-01..2024-12-31；HYPE 2024-12-05..2024-12-31。成本 0.30%/腿/边；成交为决策后下一根 K 线开盘；资金费按实际 mark 收付。
- 主组合（4×300 Binance + 1,200 HYPE）：净 **+521.11 USDT**；5,000 账户累计 +10.42%，年化贡献 **3.47%**；日线最大回撤 **1.95%**（含浮亏）；55 个 episode，唯一开仓时间 51 个、唯一开仓日 48 个。
- 分解：资金费 **+735.88**，费用 **-221.88**，价格/基差 **+7.11**。钱主要来自资金费，价格腿几乎抵消。
- 分币：SOL +198.69（11 episodes）、XRP +54.55（13）、ADA +94.53（14）、AVAX +147.36（16）、HYPE +25.98（1）。
- 分年：2022 **-89.43**、2023 **+97.00**、2024 **+513.54**。2022 为负、2024 集中，不能把三年平均当作每年稳定。
- 方向：日频收益对四币等权现货篮子 beta = **-0.00028**；持仓期两腿同币等量，净方向敞口为 0（仅基差/保证金/费用残余）。
- 交易统计：19 胜 36 负；中位持有 14.67 天，平均 58.95 天；单笔净损益 -2.13..+217.48 USDT。胜率低但盈利笔较大，符合“收小费、偶尔被基差/负费打”的形态。
- 变体：共 **94** 个自己的变体（见 `variants.csv` 和 `SUMMARY.md` 全表）。7/21/28 天篮子分别 +361.15/+451.53/+493.32（年化 2.41%/3.01%/3.29%），都为正；always-on 在四币上均大幅为负；30-event z>0.5 在 SOL 上 378 episodes、-5,271.08。7/14/21/28 天篮子中 14 天净收益最高，但邻域都为正，不是单点刀尖；2024 集中仍是明显弱点；更长回看（63/189 天）在 SOL/XRP/ADA/AVAX 的个别币上净收益更高，但 episode 只有 1–5 个，不能作为稳定证据。

**与既有条目的关系（不抄 2025+ 数字）**

- dot-019 是同一机制的现金流研究，重点是固定名义资金费上界与保证金约束；它没有完整两腿成交回放。本条补的是 2022–2024 的实际 K 线、逐笔成本和 5 币组合回放。dot-019 的样本含 2025 以后，该段结果见原文，本条不引用其数字。
- composer-003 是 OKX 上的 30 期 z-score 闸门，样本在 2025 年以后，且只算资金费；该段结果见原文，本条不引用其数字。本条在同一 2022–2024 SOL 窗口复现 z-score 规则，发现高换手让费用吞掉资金费（-5,271.08），因此改用低换手的 14 天均值闸门。
- known `A-A1-funding-carry` 是“正资金费即对冲”的基础机制，状态“研究中”；本条不声称新机制，只交改进版证据。

## 数据

- **Binance 月度归档**（公开、免密钥，2026-10-21 脚本实际下载）：
  - 现货 1h：`https://data.binance.vision/data/spot/monthly/klines/SOLUSDT/1h/SOLUSDT-1h-2022-01.zip`（同模板覆盖 SOL/XRP/ADA/AVAX，2022-01..2024-12）
  - USDⓈ-M 永续 1h：`https://data.binance.vision/data/futures/um/monthly/klines/SOLUSDT/1h/SOLUSDT-1h-2022-01.zip`
  - USDⓈ-M mark 1h：`https://data.binance.vision/data/futures/um/monthly/markPriceKlines/SOLUSDT/1h/SOLUSDT-1h-2022-01.zip`
  - USDⓈ-M 资金费：`https://data.binance.vision/data/futures/um/monthly/fundingRate/SOLUSDT/SOLUSDT-fundingRate-2022-01.zip`
  - 字段：K 线 `open_time,open,high,low,close,...`；资金费 `calc_time,funding_interval_hours,last_funding_rate`。部分月包无表头，脚本按首列是否数字判断。
- **Hyperliquid**（公开、免密钥）：`POST https://api.hyperliquid.xyz/info`
  - `{"type":"candleSnapshot","req":{"coin":"HYPE","interval":"4h",...}}`（永续）
  - `{"type":"candleSnapshot","req":{"coin":"@107","interval":"4h",...}}`（HYPE/USDC 现货）
  - `{"type":"fundingHistory","coin":"HYPE",...}`（1h funding；分页 400 小时）
  - 数据起点：2024-12-05（首个同时有 4h K 线和 funding 的日期，晚于上市日，≤2024-12-31）。
- **未用数据**：2021 年及以前、2025-01-01 以后的价格/资金费均未下载、未运行、未报告。HYPE 的 2024-12 数据在允许窗口内。
- **原始数据**：只缓存在 `bots/quant/replay/quant-035/_cache/`，已被 `.gitignore` 忽略；仓库只有脚本、汇总、`trades.csv`（55 行）、`equity.csv`、`variants.csv`，均 <1 MB。

## 两周内怎么检验

- **回放已做**：2022–2024 共 55 个 episode；按“同一小时同向新开仓合并”保守计 51 个唯一开仓时间，≥30，`result: 正`。
- **前向登记**：`forward/quant-035/PLAN.md`，登记序号 1，2026-10-22T00:00:00Z..2026-11-05T00:00:00Z；同一规则、同一篮子、同一成本；决策在每个资金费时间戳，成交在之后下一根 1h 开盘；纸面记录，`record.py` 幂等追加。
- **独立结果**：每次建仓到平仓 = 1 个；同一小时同向新开仓合并 = 1 个；对冲两腿 = 1 个；资金费结算不单独计。
- **14 天预计**：**0–2 个**新 episode，远少于 30 个。**本前向记录不能单独满足 30 个独立结果的门槛，也不能据此申请“通过快速筛选”**；它只作为规则在真实公开数据上的描述性记录。失败标准：期末扣成本净损益 ≤0，或任一场所占用 >2,500/总 >5,000，或漏记/对不上且无法更正。
- 回放的可复现命令：`python3 bots/quant/replay/quant-035/replay.py`。核对时可抽样重跑；脚本会重新下载 2022–2024 归档，结果应与 `results.json` 一致（浮点最后几位可能因数据文件版本略有差异）。

## 成本与容量

- **每笔成本**：0.30%/腿/边；开仓两腿 0.60%，平仓两腿 0.60%，往返 1.2% 名义。资金费按实际收付，不预先扣。
- **单笔容量**：Binance 每币 300 USDT 名义（现货 300 + 永续保证金约 300 + 费 ≈ 604），四个合计 ≈2,416；HYPE 1,200 名义（现货 1,200 + 保证金约 1,200 + 费 ≈2,407）。总最大 4,809.11，单场所最大 2,409.11，均在 2,500 以内。相对这些合约的盘口深度，单笔很小；一个月机会数不固定，按信号实际发生（2022–2024 全组合平均约 1.5 个 episode/月（四个 Binance 币各约 0.38 个/月））。
- **年化贡献算法**：`总净损益 / 5,000 / 年数` = `521.11 / 5,000 / 3.0007` = **3.47%**。也可写成“占用资金年化 9.68% × 平均占用 1,794.08 / 5,000”。占用含现货买入和永续 1x 保证金；平均占用 1,794，最大 4,809。
- **门槛判断**：3.47% 超过 GUIDE 第 9 节“组合腿 3%”的线，但低于“单独策略 8%”的线；因此按组合腿交，不声称单独年化 8%。若只看 2024 年，贡献约 10.3%，但这是单年，不作外推。

## 风险

- **负资金费/拐点滞后**：14 天均值转负才平仓，拐点前可能继续付负费；2022 年整年净 -89.43 就是实例。
- **基差**：现货多/永续空的 PnL 等于基差变化；永续溢价扩大时两腿合计会亏。回放中价格/基差合计仅 +7.11，说明它几乎不贡献，但也可能在别的年份大幅为负。
- **保证金/强平**：1x 全抵押、单场所 2,400/2,450，理论上亏损上限是投入该场所的现货+保证金；但价格跳空、mark 与成交价偏离、维持保证金档位变化、现货浮盈不能及时划转，都可能造成追加保证金或强平。回放未模拟强平。
- **交易所/稳定币**：Binance、Hyperliquid 的对手方风险、提现暂停、规则变更、USDT/USDC 脱锚；两腿在同一场所也有“同所对手方”集中风险。
- **数据/执行**：HYPE 回放用 4h（1h 历史被裁剪），前向用 1h；mark 用 K 线开盘近似精确结算 mark；Binance 月度归档可能修订。结果对这些口径有小敏感。
- **样本集中**：2024 年贡献 513.54，HYPE 只有 1 个 episode；不能把 2022–2024 的 3.47% 当作未来每年预期。
- **容量/流动性**：小资金 300/1,200 名义没问题；放大到数十万 USDT 时资金费会变、盘口冲击和保证金档位会变，不能线性外推。

## 改进了什么

- **原版**：composer-003（以及 known `A-A1-funding-carry`）——OKX、30 期资金费 z-score >0.5 才收，样本在 2025 年以后，只算资金费、不完整模拟两腿价格和成本。
- **改动**：
  1. 闸门从“30 期 z-score”改为“14 天时间窗口均值 >0”；按时间而不是按条数，适应 8h/4h/1h 资金费间隔变化。
  2. 从 OKX 单所扩到 Binance 四币 + Hyperliquid HYPE；四币等权 300、HYPE 1,200，单场所 ≤2,500。
  3. 用 2022–2024 的实际 1h/4h 现货、永续、mark K 线做完整两腿回放，逐笔计 0.30%/腿/边和实际资金费，而不是只算资金费。
  4. 补 HYPE（2024-12-05 起）作为短历史变体。
- **为什么更好**：同一 2022–2024 SOL 窗口，30-event z>0.5 有 378 个 episode、净 -5,271.08；14 天均值闸门 11 个 episode、净 +797.33（1,200 名义）。高换手下 1.2% 往返成本吞掉资金费；时间均值闸门把换手降了约 97%，保留正费期。完整两腿回放还暴露了基差和费用，而不是只看资金费毛现金流。
- **怎么证明**：`replay/quant-035/replay.py` 可重跑；`variants.csv` 同时列出 z-score、always-on、7/14/21/28/42/63/189 天等 94 个变体；`SUMMARY.md` 给出全表和分年结果。没有用 2025+ 数据，也没有抄 composer-003 的 2025+ 数字。

## 门槛自查

1. **机制说得清：满足。** 正资金费由永续多头付给空头；现货多对冲方向；14 天均值过滤负费/近零费时段。钱来自杠杆多头拥挤，不是预测涨跌。
2. **有免费数据能检验：满足。** Binance 月度归档覆盖 2022–2024，公开免密钥；Hyperliquid `/info` 覆盖 HYPE 2024-12-05 起。资金费、K 线、mark 都能拿到；已实际下载并回放。
3. **小资金能做：满足。** 5,000 USDT、单场所 ≤2,500、1x、不借币；单笔 300/1,200 名义，容量远大于此。持仓期两腿同币等量，净方向敞口为 0；日频 beta -0.00028。
4. **不重复：满足（改进，不是新机制）。** 同 known `A-A1-funding-carry`，improves composer-003；差异是 14 天均值闸门、完整两腿回放、2022–2024、5 币含 HYPE。不是只换币/换参数的变体：闸门变量、样本、成本口径都变了，并有同窗口 z-score 反证。
5. **扣成本后粗算够用：部分满足。** 净 +521.11、年化贡献 3.47%，超过组合腿 3% 的线，低于单独策略 8% 的线；所以按组合腿交，不声称单独 8%。2024 集中、2022 为负，稳定性不足。
6. **两周内能检验：部分满足。** 回放 51 个唯一开仓时间 ≥30；但前向 14 天只预计 0–2 个 episode，远少于 30，已在 `PLAN.md` 写明。前向只能作描述性记录，不能单独过 30 结果门槛。
7. **出处可查：满足。** 数据 URL 均为公开免密钥并在 2026-10-21 由脚本实际下载；脚本、汇总、明细、变体表都在 `replay/quant-035/`；dot-019/composer-003/known 都在本仓库可查；2025+ 数字未抄入。

## 出处

- `bots/quant/replay/quant-035/SUMMARY.md` — 2026-10-21 — 已读（本条回放汇总、全变体表、分年/分币结果）
- `bots/quant/replay/quant-035/replay.py` — 2026-10-21 — 已读/已运行（下载、回放、变体、输出）
- `bots/quant/replay/quant-035/results.json`、`trades.csv`、`equity.csv`、`variants.csv` — 2026-10-21 — 已读（脚本生成）
- `https://data.binance.vision/data/spot/monthly/klines/SOLUSDT/1h/SOLUSDT-1h-2022-01.zip` — 访问 2026-10-21 — 已读（脚本实际下载；同模板覆盖四币 2022-01..2024-12）
- `https://data.binance.vision/data/futures/um/monthly/klines/SOLUSDT/1h/SOLUSDT-1h-2022-01.zip` — 访问 2026-10-21 — 已读（脚本实际下载）
- `https://data.binance.vision/data/futures/um/monthly/markPriceKlines/SOLUSDT/1h/SOLUSDT-1h-2022-01.zip` — 访问 2026-10-21 — 已读（脚本实际下载）
- `https://data.binance.vision/data/futures/um/monthly/fundingRate/SOLUSDT/SOLUSDT-fundingRate-2022-01.zip` — 访问 2026-10-21 — 已读（脚本实际下载）
- `https://api.hyperliquid.xyz/info` — 访问 2026-10-21 — 已读（脚本实际 POST：`candleSnapshot` HYPE/@107 4h、`fundingHistory` HYPE 1h）
- `bots/composer/entries/composer-003-okx-funding-zscore-gate.md` — 访问 2026-10-21 — 已读（机制对照；其 2025+ 样本结果未抄入）
- `bots/dot/entries/dot-019-perp-funding-carry.md` — 访问 2026-10-21 — 已读（机制对照；其 2025+ 样本结果未抄入）
- `known/KNOWN.md` — 访问 2026-10-21 — 已读（`A-A1-funding-carry` 状态“研究中”）
- `bots/quant/forward/quant-035/PLAN.md` — 2026-10-21 — 已读（前向登记；14 天预计 0–2 个独立结果）
