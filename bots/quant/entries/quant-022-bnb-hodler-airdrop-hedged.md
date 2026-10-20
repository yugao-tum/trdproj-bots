---
id: quant-022
name_zh: BNB空投+永续对冲：成本吃掉收益
name_en: Binance HODLer Airdrops on BNB, hedged with BNB-USDT perpetual short
bot: quant
date: 2026-10-20
market: crypto
pm_category: -
kind: new
improves: -
category: Y
return_type: rent
instruments: BNB（BNB-USDT 现货/Simple Earn ＋ BNBUSDT 永续空头）
venues: Binance（Simple Earn + USDⓈ-M 永续）
data: 币安 HODLer 公告（公开 bapi/cms 接口，免密钥）、data.binance.vision 的 BNBUSDT 永续资金费（2020-02 起）与现货 1d K 线（免密钥、无需登录）；Simple Earn 内 BNB 总量（计算收益分母）无公开来源
test_2w: 独立结果按「一次 HODLer 空投」计；12 个月只有 12 次、2026-07 起 3.7 个月零次，两周拿不到 30 个；失败标准=扣资金费与手续费后年化净收益≤0 或两周内没有新空投
status: 草稿
confidence: 中
---

整理说明：本条的重点是**否证**。机制、规则、空投规模与资金费都是我在 2026-10-20 现场抓取并自己算的（脚本与全部代码见文末 `notes/batch2-verification/quant-022.md`）；结论是「这一条很可能是负收益，因为对冲成本大于空投价值」。**没有做回测**，收益结论只有一层：把 12 次已发生空投的池面值与 12 个月资金费按同一分母做比较。

## 一句话

把 BNB 放进币安 Simple Earn 拿 HODLer 空投（随机历史快照、按平均持仓比例分配），同时用 BNBUSDT 永续空头对冲 BNB 价格；持有到下一次空投、或按年评估，扣资金费与手续费后的净收益若为正才做。

## 钱从哪里来

付钱给你的是**项目方**：新币上币要买「BNB 持有者的注意力」，把一部分代币（本样本 12 次里 640 万–2.4 亿枚）按 BNB 平均持仓比例白送给 Simple Earn 里的 BNB 持有者，币安不收上币费（OPG 公告原文 `Listing Fee: 0`）。这笔钱持续存在的原因是币安需要用「持有 BNB 的额外收益」维持 BNB 需求与 Simple Earn 规模，而项目方用代币而不是现金支付。

但**这条策略的第二条腿（永续空头）是纯支出**：空头要付资金费。我算的 12 个月 BNBUSDT 永续资金费合计是 **+1.9709%**（空头付出，见证据节），而按可比口径算出的空投年化只有 **0.23%–4.6%**（分母未知，见情景表）。所以「钱从哪里来」这一问在这一条上其实是反的：空投是别人给的，资金费是你付的，两者相减大概率是负的。这就是本条要如实写出的结论。

## 规则

**HODLer 空投规则（原文要点，以 2026-06-30 的 OPG 公告为例，已读全文）**

- 资格：把 BNB 申购到 **Simple Earn（活期和/或定期）和/或 On-Chain Yields**；公告原文另写「By subscribing BNB to Simple Earn, users are automatically eligible for HODLer Airdrops (as well as Launchpool and Megadrop rewards)」。
- 快照：`Snapshots of user balances and total pool balances will be taken multiple times at any point of time each hour to get users' hourly average balances`——即按**小时平均余额**，且**快照时点随机**；OPG 的计息窗口是 `2026-06-22 00:00 (UTC) 至 2026-06-24 23:59 (UTC)`，**在公告日（2026-06-30）之前**。我核了 18 个公告：窗口结束日到公告日的间隔 **3–21 天，中位 12 天**（清单见证据节）。**这决定了策略形态：窗口在公告前，事前不可能知道，所以必须长期连续持有，不能「窗口前买入、发完就卖」。**
- 分配：按平均持仓占比分配；**单人硬顶 4%**（原文 `BNB Holding Hard Cap: User's Average BNB Holding / Total Average BNB Holding * 100% ≤ 4%`），19 个抽查公告全部是 4%（`≤ 4%` 正则 19/19 命中）。
- 门槛：`any one of users' supported assets must be greater than 0.01 BNB`。
- 排除项：`BNB Simple Earn assets collateralizing against Binance Loans (Flexible Rate) are not entitled`；slisBNB / slisBNBx 在 Binance Wallet（Keyless）里可计入。
- 发放：公告后 `within 5 hours` 进现货账户。
- 收益公式（我的写法）：某用户拿到 `pool_i × min(h_i / S_i, 4%)`，`h_i` 是本人小时平均 BNB，`S_i` 是全体平均 BNB；折成「每 1 BNB 的年化」= `Σ_i (pool_i × p_i) / (S × P_BNB)`，其中 `p_i` 是发币日价格、`P_BNB` 是 BNB 价格。**`S` 币安不公布，这是本条最大的未知量（未查到）。**

**交易规则（提案，未验证）**

1. 现货腿：BNB 放 Simple Earn 活期，长期持有；不加杠杆、不借币。
2. 对冲腿：Binance USDⓈ-M `BNBUSDT` 永续空头，名义金额 = 现货 BNB 市值 × 1.0（不留敞口），全仓保证金另留 ≥30% buffer 防强平。
3. 资金费按 8 小时结算，逐次记账；**若连续 3 次结算资金费为负（空头收钱）则维持；若年化滚动资金费 > 3% 则平掉对冲腿、只留裸 BNB 并把这条线降级为「持有 BNB」**。
4. 再平衡：名义敞口偏离 >5% 时调回（调仓也是手续费，见成本节）。
5. 出场：没有「结算日」，只是评估点；不因为空投发完就平仓（因为下一次窗口在公告前）。
6. 明确不做：不为了空投去借 BNB、不用杠杆放大 BNB、不做新币本身的投机（收到即按市价卖出，`p_i` 就用发币日收盘价）。

## 证据

### 1）空投规模（我自己从公告 + K 线算的）

12 次空投 = 公告日在 2025-10-21 至 2026-10-20 之间的全部 HODLer 事件。池面值 = 公告里的 `HODLer Airdrops Token Rewards` × 发币日现货收盘价（data.binance.vision 1d K 线 `close`）。

| 公告日 | 代币 | 池数量（枚） | 计价日 | 收盘价 USDT | 池面值 USDT |
|---|---|---|---:|---:|---:|
| 2025-10-21 | TURTLE | 10,000,000 | 2025-10-22 | 0.1714 | 1,714,000 |
| 2025-11-03 | MMT | 7,500,000 | 2025-11-04 | 2.64 | 19,800,000 |
| 2025-11-06 | SAPIEN | 15,000,000 | 2025-11-06 | 0.3461 | 5,191,500 |
| 2025-11-11 | ALLO | 15,000,000 | 2025-11-11 | 0.4703 | 7,054,500 |
| 2025-11-27 | AT | 20,000,000 | 2025-11-27 | 0.22 | 4,400,000 |
| 2026-01-05 | BREV | 15,000,000 | 2026-01-06 | 0.3516 | 5,274,000 |
| 2026-03-11 | NIGHT | 240,000,000 | 2026-03-11 | 0.04819 | 11,565,600 |
| 2026-03-18 | ROBO | 100,000,000 | 2026-03-18 | 0.02672 | 2,672,000 |
| 2026-04-28 | CHIP | 25,000,000 | 2026-04-28 | 0.06894 | 1,723,500 |
| 2026-05-21 | AIGENSYN | 100,000,000 | 2026-05-21 | 0.03096 | 3,096,000 |
| 2026-05-29 | GENIUS | 10,000,000 | 2026-05-29 | 0.454 | 4,540,000 |
| 2026-06-30 | OPG | 6,400,000 | 2026-06-30 | 0.1309 | 837,760 |
| **合计** | | | | | **67,868,860** |

- MMT 那一行是**上币首日的尖峰**：2025-11-04 开 0.1、最高 4.4754、收 2.64，次日收 0.749。**剔除 MMT 后合计 48,068,860 USDT**——下面用这个保守值做盈亏平衡，避免用尖峰价把结论撑大。
- 这 12 次合计摊到 12 个月，是「整个 BNB 持有者群体」一年拿到的总空投面值（未扣卖出滑点）。单个用户拿的是其中 `h/S` 的比例。

### 2）分母 S 未知，收益只能给区间

`S`（Simple Earn + On-Chain Yields 里的 BNB 小时平均总量）币安不公布，**未查到**。所以只能用公式给出情景（`P_BNB = 730.2616 USDT`，CoinPaprika 2026-10-20T04:22:16Z）：

| 假设 S（BNB） | 每 1 BNB 年收入 USDT | 折成 BNB 市值年化 |
|---:|---:|---:|
| 2,000,000 | 33.93 | 4.65% |
| 5,000,000 | 13.57 | 1.86% |
| 10,000,000 | 6.79 | 0.93% |
| 20,000,000 | 3.39 | 0.46% |
| 40,000,000 | 1.70 | 0.23% |

（用合计 67,868,860 算；用保守的 48,068,860 时每行乘 0.708。）

- 要达到 GUIDE 的 8% 年化，需要 `S ≤ 48,068,860 / (0.08 × 730.2616) = 822,800 BNB`（用含 MMT 的 67.87M 则是 1,161,500 BNB）。**这条路要靠「币安 Simple Earn 里只有不到 100 万枚 BNB」才成立**；BNB 总供应是 131,512,046 枚（CoinPaprika，同一次抓取），即需要小于总供应的 0.8%。我认为这不现实，但**S 我核不到，这一步是我的推断，不是实测**。
- 成本侧用同一套算术求盈亏平衡：只算资金费（1.9709%/年）时 `S ≤ 48,068,860/(0.019709×730.2616) = 3,339,802 BNB`；再把 GUIDE 的每边 0.30% 交易成本算进去（建仓两条腿 0.6% + 平仓两条腿 0.6% = 1.2% 一次性，摊在 1 年上是 1.2%/年，合计 3.17%/年）时 `S ≤ 2,076,472 BNB`。

### 3）资金费（data.binance.vision，我自己算的）

`data/futures/um/monthly/fundingRate/BNBUSDT/` 下 2025-10 至 2026-09 共 12 个 zip（列名 `calc_time,funding_interval_hours,last_funding_rate`），合计 **1,095 行**（= 365×3）：

- 合计 `+0.019709`，即 **空头一年付出 1.9709% 名义本金**；均值 `0.18 bp/8h`，中位 `0`，正值占比 **39.54%**（空头付钱的时间只占四成，但总额仍是净支出）。
- 单次极值 `-3.5218 bp` 与 `+3.2423 bp`（每 8 小时）。`9.0e-08` 这类极小值大量出现（末行 `1790784000002,8,0.00008965`）。
- 说明：**这 12 个月恰好是资金费偏低的一段**；用均值外推未来是乐观假设。

### 4）Airdrop 频率（我数的）

币安公告列表接口 catalogId=48 拉 12 页共 **600 条公告**（2025-02-25 至 2026-10-14），其中标题含 `HODLer` 的 **56 条**，最早 2025-02-27（SHELL），**最晚 2026-06-30（OPG）**；2026-07 至 2026-10-14 之间 **0 条**。也就是说这个系列近 3.7 个月是停的，而 2025-09 一个月有 12 次（我按 `releaseDate` 数的）。频率高度不稳定，年化不能按「12 次/年」外推到明年。

### 5）Launchpool

公告原文只说「订阅 Simple Earn 的 BNB 自动同时具备 Launchpool、Megadrop 资格」，具体 Launchpool 的池子、期限与折算**本次未抓取，未查到**，所以本条不把 Launchpool 收益计入，也不声称它存在多少。

## 数据

- 币安公告（免密钥、免登录）：`https://www.binance.com/bapi/composite/v1/public/cms/article/list/query?type=1&pageNo=<n>&pageSize=50&catalogId=48`（列表，含 `releaseDate`）；正文 `https://www.binance.com/bapi/composite/v1/public/cms/article/detail/query?articleCode=<code>`（`body` 是富文本 JSON）。
- 注意：`https://www.binance.com/en/hodler-airdrop` 直接抓返回 **HTTP 202、0 字节**（Cloudflare 拦截），所以本条不用网页版，只用上面的公开 bapi 接口。`https://api.binance.com/api/v3/ticker/price?symbol=BNBUSDT` 返回 **451**，符合预期，本条不使用 api.binance.com。
- 资金费：`https://data.binance.vision/data/futures/um/monthly/fundingRate/BNBUSDT/BNBUSDT-fundingRate-<YYYY-MM>.zip`，2020-02 起有数据（bucket 列表已读）。
- 价格：`https://data.binance.vision/data/spot/monthly/klines/<SYM>USDT/1d/<SYM>USDT-1d-<YYYY-MM>.zip`；BNB 现价与总供应 `https://api.coinpaprika.com/v1/tickers/bnb-binance-coin`（免密钥）。
- 拿不到的：Simple Earn 的 BNB 总量 `S`（未查到，币安不公布）；历史「每人实际到账多少枚」也无公开来源，只能按公式反推。

## 两周内怎么检验

- **独立结果按「一次 HODLer 空投」计**（不是按代币、不按公告条数）：本样本 12 个月 12 次，且 2026-07 起 0 次。**两周内最多 1–2 个结果，不可能到 30 个**，所以这一条按 GUIDE 第 2 节第 6 条只能进待选区。
- 两周内**可以**做完的、不需要等待事件的检验（建议先做这个）：
  1. 用 data.binance.vision 的 BNBUSDT 资金费全历史（2020-02 起，免费）算**滚动 12 个月资金费**的分布与最坏值，看「空头成本」在新样本里是否还 < 2%/年；
  2. 用 56 条公告的 `pool × 发币日价格` 把样本从 12 次扩到 56 次，得到池面值的时间序列，检验「近 3.7 个月为 0」是偶发还是趋势；
  3. 若能找到任何公开的 `S` 代理（例如币安储备证明里的 BNB 数量、链上 Simple Earn 地址余额），就能把情景表压成一个数。
- **失败标准（写死）**：扣资金费 + 1.2% 一次性交易成本后，**年化净收益 ≤ 0**；或滚动 12 个月资金费升到 > 3%；或连续两个季度没有新的 HODLer 空投。

## 成本与容量

- **资金费**：12 个月实测 **+1.9709%**（空头付出，data.binance.vision，2025-10 至 2026-09）。
- **交易成本**：按 GUIDE 第 2 节「加密每边约 0.30%」粗算，建仓现货买 + 永续空 = 0.6%，平仓同样 0.6%，**一次性 1.2%**。另加再平衡（敞口偏离 >5% 才动）与永续保证金占用。
- **毛收入**：见情景表，`S ≥ 5,000,000 BNB` 时 < 1.86%/年。
- **容量**：单场所上限 2,500 USDT → 约 **3.42 BNB**（2,500 / 730.2616）。这笔钱一年拿到的空投在 `S = 10M` 时约 3.42 × 6.79 = **23 USDT**，而资金费支出约 2500 × 1.97% = **49 USDT**，交易成本 2500 × 1.2% = **30 USDT**。**净额是负的（约 −56 USDT/年，按 S=10M 情景）**。这就是本条最硬的结论。5,000 USDT 可以分两个场所放（现货一个、永续一个），但两条腿要能互相看见保证金，分开反而更难管。
- **一个月多少次机会**：本样本 12 次/12 个月，但 2026-07 起为 0；不能用平均值规划现金流。

## 风险

- **分母风险（最大）**：`S` 未查到。若 Simple Earn 里 BNB 极少，收益可能翻几倍；若极多，收益接近 0。整条策略的符号由这个不可观测的数决定。
- **资金费反转**：12 个月合计 +1.9709%，但单次最极端 `+3.2423 bp/8h`；若牛市里资金费持续高位（例如年化 10–20%），对冲腿会吃掉全部空投还有余。空头还有**强平风险**：BNB 单边上涨时永续浮亏，全仓下要留足 buffer，否则对冲腿先死。
- **空投停发**：2026-07 至 2026-10-14 一条都没有。持有成本（资金费 + 机会成本）照付。这是本条目前最可能的实际状态。
- **代币价格风险**：`p_i` 用发币日收盘价，实际到账后卖出会有滑点，且这类新币首日常常是「开 0.1、最高 4.48、收 2.64」（MMT 2025-11-04 的实测 K 线），**按收盘价估值会显著高估**：MMT 一项就占 12 次合计的 29%。
- **规则变动**：4% 硬顶、0.01 BNB 门槛、排除条款都在公告里逐次重申，但币安可单方面改（`Binance reserves the right to...`）；Simple Earn 活期额度也可能满。
- **平台/托管集中**：现货、Simple Earn、永续全在币安一个场所，2,500 USDT 上限内也是单点风险（交易所暴雷、提币暂停、账户风控）。这就是 GUIDE 的场所上限想防的事，本条没法通过分散解决，因为空投资格只认币安账内的 BNB。
- **口径风险**：`S` 用的是「全体平均 BNB」还是「全体平均合格 BNB」，公告没说清；4% 硬顶让大资金的实际边际收益低于线性公式。

## 改进了什么

不适用（`kind: new`）。

## 门槛自查

1. **机制说得清：满足** — 付钱方是项目方（用代币换 BNB 持有者注意力，`Listing Fee: 0`），规则与分配公式都有原文；同时写清了对冲腿是净支出。但**这条的净收益大概率为负**，机制清楚不等于能赚钱。
2. **有免费数据能检验：部分满足** — 公告（免密钥）与资金费/价格（data.binance.vision）都免费、2020-02 起；但**收益分母 `S` 无公开来源（未查到）**，所以「收益本身」的数据拿不到，只能拿到池面值与成本。按 GUIDE 第 2 节第 2 条「能拿到收益本身的数据」这一项**不满足**。
3. **小资金能做：满足** — 2,500 USDT/场所 → 3.42 BNB，不加杠杆、不借币；容量与机会数都写清了（12 次/12 个月，近 3.7 个月 0 次）。
4. **不重复：不确定** — 我查了 `known/KNOWN.md`（有 `Y-Y2-launchpool`「币安 Launchpool 质押挖新币」与 `Y-Y2-airdrop-farming`「空投与积分耕作」）、`bots/*/CLAIMS.md`（只有 quant 自己对本主题的认领 B19）与 `bots/*/entries/`（无 BNB/HODLer/Launchpool 条目）。与 `Y-Y2-launchpool` 的区别是：本条**不是**质押挖矿，而是「按历史快照追溯发放的持有奖励」＋**永续空头对冲腿**，且结论建立在对冲成本与空投价值的定量比较上；与 `Y-Y2-airdrop-farming` 的区别是收益不来自积分/交互，而来自可观测的公告池。是否算变体，请主审判断。
5. **扣成本后粗算够用：不满足** — 毛收入在合理 `S` 区间是 0.23%–1.86%/年，资金费已 1.9709%/年，再加 1.2% 一次性交易成本，**净额为负**；盈亏平衡需要 `S ≤ 2,076,472 BNB`（含交易成本）或 `≤ 3,339,802`（仅资金费），这在 BNB 总供应 131,512,046 枚的量级下不现实。**注意：`S` 未查到，这个判断依赖上表的算术，不是实测收益。**
6. **两周内能检验：不满足** — 独立结果按空投事件计，12 个月 12 次、近 3.7 个月 0 次，两周最多 1–2 个，拿不到 30 个。可替代的历史检验（56 条公告的池面值序列、2020 年起资金费分布）能在两周内做完，但那是成本/规模检验，不是收益检验。
7. **出处可查：满足** — 每个数字都有 URL + 访问日期 + 取数方式，脚本全文见 `notes/batch2-verification/quant-022.md`；`api.binance.com` 的 451 与币安网页的 202（0 字节）这两个失败也照写，没有把它们当数据源。

## 出处

- https://www.binance.com/bapi/composite/v1/public/cms/article/list/query?type=1&pageNo=1&pageSize=50&catalogId=48 — 访问 2026-10-20 — 已读（catalogName `New Cryptocurrency Listing`，`total` 2283；第 1–12 页共 600 条，日期 2025-02-25 至 2026-10-14）
- https://www.binance.com/bapi/composite/v1/public/cms/article/detail/query?articleCode=b026c9829d28459cb1f1a95000960a08 — 访问 2026-10-20 — 已读（OPG 公告全文：`6,400,000 OPG`、快照 `2026-06-22 00:00 (UTC) to 2026-06-24 23:59 (UTC)`、`≤ 4%`、`0.01 BNB`、`within 5 hours`、`Listing Fee: 0`）
- https://www.binance.com/bapi/composite/v1/public/cms/article/detail/query?articleCode=455eedc320bd43e28e2326f58d4aac2a — 访问 2026-10-20 — 已读（GENIUS 公告：`10,000,000 GENIUS`、快照 `2026-05-11 00:00 (UTC) to 2026-05-13 23:59 (UTC)`）
- 另 17 个 `article/detail/query?articleCode=...`（TURTLE/ZBT/YB/ENSO/EUL/WAL/MORPHO/2Z/AT/ALLO/SAPIEN/MMT/BREV/NIGHT/ROBO/CHIP/AIGENSYN）— 访问 2026-10-20 — 已读（全部 `≤ 4%`；池数量与快照窗口见上表与证据节）
- https://data.binance.vision/data/futures/um/monthly/fundingRate/BNBUSDT/BNBUSDT-fundingRate-2025-10.zip … `-2026-09.zip`（12 个）— 访问 2026-10-20 — 已读（列名 `calc_time,funding_interval_hours,last_funding_rate`，1,095 行，合计 +0.019709）
- https://s3-ap-northeast-1.amazonaws.com/data.binance.vision?prefix=data/futures/um/monthly/fundingRate/BNBUSDT/ — 访问 2026-10-20 — 已读（bucket 列表，最早 `BNBUSDT-fundingRate-2020-02.zip`）
- https://data.binance.vision/data/spot/monthly/klines/OPGUSDT/1d/OPGUSDT-1d-2026-06.zip — 访问 2026-10-20 — 已读（`2026-06-30` 收盘 `0.1309`；另 11 个代币同法取首日/发币日收盘）
- https://data.binance.vision/data/spot/monthly/klines/MMTUSDT/1d/MMTUSDT-1d-2025-11.zip — 访问 2026-10-20 — 已读（`2025-11-04` 开 `0.1`、高 `4.4754`、收 `2.64`、成交额 `931,122,562`）
- https://api.coinpaprika.com/v1/tickers/bnb-binance-coin — 访问 2026-10-20 — 已读（`price 730.2616340282318`、`total_supply 131512046`、`last_updated 2026-10-20T04:22:16Z`；`circulating_supply` 为 `null`）
- https://www.binance.com/en/hodler-airdrop — 访问 2026-10-20 — **失败**（HTTP 202，0 字节，Cloudflare 拦截；未作为数据源）
- https://api.binance.com/api/v3/ticker/price?symbol=BNBUSDT — 访问 2026-10-20 — **失败**（HTTP 451；改用 data.binance.vision 与 CoinPaprika）
- https://gamma-api.polymarket.com/public-search?q=binance&limit_per_type=5&events_status=all — 访问 2026-10-20 — 已读（只返回「WIF 是否上币安」这类旧上市市场，**未查到**「币安 HODLer 空投」模板；本条 `market: crypto`、`pm_category: -`，不是 Polymarket 策略）

---
