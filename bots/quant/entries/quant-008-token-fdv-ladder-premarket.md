---
id: quant-008
name_zh: 代币上线FDV阶梯用外盘定价
name_en: Token-launch FDV ladder priced off pre-launch perps (Hyperliquid hyperps)
bot: quant
date: 2026-10-20
market: polymarket
pm_category: crypto
kind: new
improves: -
category: S
return_type: direction
instruments: 「某代币 FDV above $X one day after launch?」Yes/No 阶梯（同一事件 4–14 个档）
venues: Polymarket（Gamma/CLOB 只读）；Hyperliquid info（hyperp/perp markPx，只读）
data: Gamma events/markets（含 feeSchedule、clobTokenIds）、CLOB /book、CoinGecko 免费 coins 接口（total_supply、FDV）、Hyperliquid /info（metaAndAssetCtxs、spotMeta、perpDexs）；全部免费免密钥；Gamma 里该类事件最早 creationDate=2025-09-30
test_2w: 独立结果按事件数，不按档数；截至 2026-10-20 只抓到 6 个 closed 事件（其中 4 个已核分档），两周内最多再加约 2 个，凑不到 30；失败标准：外部价格隐含分档与最终结算分档相差 >1 档，或扣费后净收益 ≤0
status: 草稿
confidence: 低
---

## 一句话

在 Polymarket「<代币> FDV above $X one day after launch?」阶梯上，用外部可观测的盘前价格（Hyperliquid hyperp/perp 的 markPx × 总供应量）算出隐含 FDV 分档概率，只有当某档市场价与模型价相差超过「吃单费 + 半个价差 + 锁仓占用的年化门槛」时才买/卖该档 YES，持有到结算或价差收敛。

## 钱从哪里来

对手方（在长锁仓、低关注度的 FDV 阶梯上按直觉报价的散户）支付的价差。这类事件的资金要押到代币真正上线（示例事件 endDate 到 2027-01-01T05:00:00Z），中途没有现金流，专业报价者少，档与档之间会出现不自洽：本次抓到的 MetaMask 阶梯上 `> $1B` 的中间价 0.045 高于 `> $700M` 的 0.04，而「FDV>1B」是「FDV>700M」的子集，理论上必须 ≤。付款动机是「没人愿意为一年多后才结算的冷门档持续报价」；这一点是推断，未用成交数据验证它是否长期存在。

## 规则

结算规则原文（Gamma event description，逐字引用要点，按 slug 分别标注）：

- `papertrade`：「This market will resolve to "Yes" if the Fully Diluted Valuation of <token>'s token is greater than the specified value 1 day after launch.」；`metamask`/`zama`/`usdai`/`edgex` 作「... is greater than the value specified in the title 1 day after launch.」
- `papertrade`：「Only an official token launched by <token> after the creation of this market will qualify. Stablecoins, memecoins, LSTs and synthetic tokens will not count.」「The token must be actively and publicly tradable to be considered a launch.」；`metamask`/`zama`/`usdai`/`edgex` 只写「The token must be actively, publicly transferable and tradable to be considered a launch.」
- **FDV 定义**（`papertrade`/`zama`/`usdai`）：「The FDV will be determined using the total token supply multiplied by the token price.」
- **时点**：「"1 day after launch" is defined as 4:00 PM ET on the calendar day following launch.」
- **数据源**：「The resolution source for this market is the most liquid price source available.」——**没有点名 CoinGecko/CoinMarketCap**；市场级 `resolutionSource` 字段是 `https://x.com/papertrade_xyz` 这类项目方推特。
- **没上线怎么办**（`metamask`/`zama`/`usdai`/`edgex`）：「If <token> ... doesn't launch a token by December 31, 2026, 11:59 PM ET, this market will resolve to "No".」；`papertrade` 为 2027。

进场/出场/仓位（本版规则，未执行）：

1. 只做同一事件内**相邻档**（例如 700M 与 1B），不跨事件拼。
2. 外部定价腿：`FDV_ext = markPx × total_supply`。优先用 Hyperliquid `/info` 的 `markPx`（hyperp 或已转 vanilla 的 perp），总供应量用 CoinGecko `market_data.total_supply`；两个来源都必须能抓到，缺一个就不报价。
3. 只有当 `|p_market − p_model| > fee/share + 半个价差 + lockup 门槛` 才吃单；否则只在档位自洽性被破坏（子集价格 > 父集价格）时挂被动单。
4. 仓位：单档 ≤300 USDT，单事件 ≤600 USDT，同时在手的独立事件 ≤4 个，合计 ≤2,500 USDT；不加杠杆、不借钱、不跨场所对冲（HL 只做信号，不下单）。
5. 出场：结算，或当 `|p_market − p_model|` 收敛到成本的 1/3 以下。
6. 风险控制：同一事件的所有档合起来只算 1 个独立结果；总敞口按「最坏情况下全部 YES 归零」估算，单事件最大损失 = 该事件投入。

## 证据

以下全部是本次抓取到的原始字段，不是回测收益。

1. **外部价格 → FDV 这条腿能对上**：CoinGecko `coins/lighter`（`last_updated=2026-10-20T04:01:53.000Z`）返回 `total_supply=1000000000.0`、`current_price.usd=3.19`、`fully_diluted_valuation.usd=3192043356`。同一时点 Hyperliquid `metaAndAssetCtxs` 里 `LIT` 的 `markPx=3.1991`。我的算术：`3.1991 × 1,000,000,000 = $3,199,100,000`，与 CoinGecko FDV `$3,192,043,356` 相差 `3.1991/3.19204 − 1 = 0.22%`。说明「perp 价格 × 总供应量」和主流 FDV 口径基本一致。
2. **时点比口径更要紧**：`lighter-fdv-above-one-day-after-launch` 已结算，分档结果为 `> $2B` = Yes(1)、`> $3B` = No(0)，即上线次日 FDV 落在 (2B, 3B]。但上条 2026-10-20 的即时价格算出来是 3.20B——**同一个代币，晚 10 个月的价格会跨过档位**。因此外部价格只能用于「上线前后窗口」，不能拿今天的价格去给 2027 年才上线的档定价（本条把这个限制写进规则）。
3. **阶梯不自洽是真实存在但价差很小**：`metamask-fdv-above-one-day-after-launch` 2026-10-20 Gamma 快照中间价：`$100M`=0.045、`$300M`=0.04、`$500M`=0.041、`$700M`=0.04、`$1B`=0.045、`$2B`=0.0265、`$3B`=0.019、`$4B`=0.0185。`> $1B`(0.045) > `> $700M`(0.04)，违反单调性 0.5¢。同日 CLOB `/book` 实测：`> $100M` bestBid 0.04 / bestAsk 0.05；`> $700M` bestBid 0.034 / bestAsk 0.046；`> $1B` bestBid 0.04 / bestAsk 0.05。**可执行版本没有套利**：买 `>$100M` YES 付 0.05、卖 `>$1B` YES 收 0.04，净成本 0.01，而两腿中间价 0.045 − 0.045 = 0.000（真正 0.005 的错位是 `>$1B` 0.045 对 `>$700M` 0.04），再扣两条腿吃单费（见「成本与容量」约 0.006/份），价差被成本吃掉。这条证据是反面的，不能写成「有套利」。
4. **已结算事件的真实分档（本次唯一可用的校准样本，来源自报，未核实）**：`edgex` 落在 (600M, 700M]；`lighter` (2B, 3B]；`zama` (300M, 400M]；`usdai` (1B, 2B]。四者的 `umaResolutionStatus` 均为 `resolved`，`closed=true`、`outcomePrices` 为 1/0 终值。样本量 4，不足以估计任何分布参数，本条不写「胜率」或「平均收益」。
5. **没有回测**：`observed_net_return=null`，Sharpe 未知，最大回撤未知，`backtest_count=0`。上面 4 条只是规则与标定检查。

## 数据

- Gamma：`https://gamma-api.polymarket.com/public-search?q=FDV%20above%20one%20day%20after%20launch&limit_per_type=50`（首次抓取返回 `pagination={"hasMore": true, "totalResults": 149}`，本次只取到前 50 条，其中 46 条是这个模板；**所以 46 是下界，不是全集**）；单事件：`https://gamma-api.polymarket.com/events?slug=<slug>`。免费免密钥，含 `description`（规则原文）、`outcomePrices`、`clobTokenIds`、`feeSchedule`、`endDate`、`volume`、`liquidity`。
- CLOB：`https://clob.polymarket.com/book?token_id=<id>`，免费免密钥，只有当前盘口；**历史 L2 没有免费来源**，只能从现在往前记录。
- CoinGecko：`https://api.coingecko.com/api/v3/coins/<id>?localization=false&tickers=false&market_data=true&community_data=false&developer_data=false`，本次 HTTP 200、无密钥可用；给 `total_supply`、`fully_diluted_valuation`、`last_updated`。
- Hyperliquid：`https://api.hyperliquid.xyz/info`，keyless，用 POST body 指定类型（`{"type":"metaAndAssetCtxs"}`、`{"type":"spotMeta"}`、`{"type":"perpDexs"}`、`{"type":"meta","dex":"<hip3>"}`）。返回 `markPx`、`dayNtlVlm`、HIP-3 dex 资产表；**不返回「是否 hyperp」的标志位**（本次对 234 个主盘 perp 逐条打印字段，只有 `name/szDecimals/maxLeverage/marginTableId`），要判断是否 hyperp 只能靠「该币有没有现货」这类间接线索，本条不下结论。
- 覆盖缺口（重要）：把 46 个事件代币名和 HL 主盘 234 个 perp 名、214 个 HIP-3 资产名做全匹配，**命中 0 个主盘、1 个 HIP-3（`hyna:LIGHTER`），而 Lighter 事件已经结算**。也就是说 2026-10-20 这一刻，没有任何「未结算 FDV 事件 ↔ HL 盘前价格」的活跃配对。策略因此是机会型的：只在「代币将上线 + HL/HIP-3 出现盘前 perp + Polymarket 挂出 FDV 阶梯」三件事同时成立时才有报价对象。

## 两周内怎么检验

- 独立结果按**事件**数：一个事件的所有档（4–14 个）算 1 个结果，同一代币在不同月份重复挂的也算 1 个。
- 可用历史：本次在 50 条搜索结果里只找到 6 个 `closed=true` 的事件（`onefootball-club`、`fuse-energy`（volume 0）、`edgex`、`zama`、`usdai`、`lighter`），其中 4 个已核对分档。**两周内不可能得到 30 个独立结果**，所以这条不能当「两周可检验」的主策略，只能作为前向记录 + 事件到来时的一次性机会。
- 前向记录（计划）：每天对每个开放事件存一次 Gamma 全档 `outcomePrices` + CLOB 买卖价 + 外部价格（CG/HL），记录「模型分档 vs 市场分档」的偏离（单位：档）。
- 失败标准（先写死）：(a) 已结算事件里，外部价格隐含分档与真实分档相差 >1 档的比例 ≥50%；或 (b) 所有触发报价的交易扣费后合计净收益 ≤0。任一成立即判定不成立。
- 复现检查（现在就能做，只需公开数据）：对 `lighter`，取 2025-12-29 前后 LIT 的价格 × CG `total_supply=1e9`，看是否落在 (2B, 3B]；本轮**没有做**，因为需要上线当日的历史价格，尚未抓到对应来源，写「未查到」。

## 成本与容量

- 费用（Gamma 实测字段，非 GUIDE 表）：示例市场 `feeSchedule={"exponent":1,"rate":0.07,"takerOnly":true,"rebateRate":0.2}`，同时 `makerBaseFee=1000`、`takerBaseFee=1000`、`feesEnabled=true`、`feeType="crypto_fees_v2"`。按 GUIDE 第 8 节公式：`fee(每份) = rate × p × (1−p)`。
  - p=0.045：`0.07×0.045×0.955 = 0.00301` USDC/份；占投入 `0.00301/0.045 = 6.69%`（= `0.07×0.955`）。
  - p=0.60：`0.07×0.60×0.40 = 0.0168` USDC/份；占投入 `2.80%`。
  - **低档（几美分）的费率占投入极高**，这是本条最大的成本障碍；`takerOnly=true` 意味着挂单成交不收这笔费（返佣 `rebateRate=0.2`），所以规则要求优先挂单。
- 价差：MetaMask 三档实测 bestBid/bestAsk = 0.04/0.05、0.034/0.046、0.04/0.05，半价差 0.5–0.6¢；在 p=0.045 上，半价差占投入 `0.005/0.045 = 11.1%`。所以 p=0.04 这一带「0.5¢ 的中间价错位」远小于「费 6.7% + 半价差 11.1%」，不可交易。
- 锁仓：`endDate=2027-01-01T05:00:00Z`，从 2026-10-20 算 73 天。若一笔毛边际 3%，年化 `3% × 365/73 = 15.0%`（算术）；若是 2028 年结算的事件（`papertrade` endDate `2028-01-01T05:00:00Z`），同样 3% 摊到 438 天只有 `3% × 365/438 = 2.5%/年`，低于门槛。
- 容量：开放事件的实际流动性差异极大——`papertrade...` 事件 `liquidity=184039.1655`、`volume=282854.88727`；`allox-fdv-above-one-day-after-launch` `volume=7492.984083`。按单档 ≤300 USDT、单事件 ≤600、4 个事件并行，总占用 ≤2,400 USDT，落在 2,500 上限内；但薄事件（volume 数千美元）实际可成交深度**未测**，不能假设 300 USDT 一定吃得下。
- 机会频率（算术）：本次拿到的 46 个事件，creationDate 从 2025-09-30 到 2026-10-06，跨度 371 天，`46 / 371 × 30.44 = 3.77` 个/月。**但其中真正带外部盘前价格的同时段可能为 0**（见数据一节的全匹配结果），所以可交易频率远低于 3.77/月，具体值未查到。

## 风险

- **结算源模糊**：规则只写「the most liquid price source available」，没指定 CoinGecko 还是 CoinMarketCap，也没写取哪一个时区的哪一根价、按哪个总供应量（是否含未解锁、是否含销毁）。同一 FDV 在不同源可差几个百分点，足以跨档。
- **时点漂移**：`4:00 PM ET on the calendar day following launch` 是一个精确时刻；盘前 perp 在那一刻的 markPx 可能大幅偏离，且 HL 的 mark 本身有「3× 8 小时 EMA 上限」「外盘中位数 1.5×」「4× 一月均价」等熔断（HL 文档原文），极端行情下 mark 会被夹住，不能当真实可交易价。
- **hyperp 身份无法自动判定**：`/info` 不返回 hyperp 标志；把 vanilla perp 当成盘前价格、或用上线后价格给上线前事件定价，会系统性高估或低估（Lighter 例子里 10 个月后差了一整个档）。
- **不可成交**：低档 `p≈0.04` 的费率占投入 6.7%、半价差 11.1%，任何 <18% 的错位都吃掉；本次实测的错位只有 0.5¢/0.045≈11%。
- **长锁仓 + 事件取消**：`fuse-energy` 事件已 `closed=true` 但 volume=0；没上线则按规则全部结算 No，买方归零。资金占用最长到 2028-01-01。
- **样本极小**：可校准的已结算事件只有 4 个，任何「胜率/期望」结论都不成立；本条没有回测。
- **平台/规则变更**：`feeSchedule` 是逐市场字段（`rate` 已经是 0.07、`exponent` 1），平台调费率或改 `rebateRate` 会直接改写成本；未核历史费率。

## 改进了什么

不适用（`kind: new`）。

## 门槛自查

1. 机制说得清：满足 — 一句话：用外部可观测价格给长锁仓 FDV 阶梯定价，赚散户报价不自洽的价差；付款方与「为什么持续」只有推断（冷门长周期档没人愿意持续报价），未用成交数据证明。
2. 有免费数据能检验：不确定 — Gamma/CLOB/CoinGecko/Hyperliquid 全部免费免密钥且本次都抓到了；但历史 L2 无免费来源，已结算事件只有 6 个（核对分档 4 个），够规则核对，不够统计。
3. 小资金能做：满足 — 单档 300 USDT、单事件 600、总 2,400 USDT 即可参与（示例档位价格 0.019–0.045），2,500 上限能放下；未验证薄市场的真实可成交深度。
4. 不重复：不确定 — 本条与 dot-032（流动性奖励）收益来源不同；但「Polymarket 阶梯自洽性/逻辑约束」在 `A` 类里可能已有条目，本次未查全库，须主审确认。
5. 扣成本后粗算够用：不满足 — 实测可执行错位 0.5¢（占投入 11%），而吃单费 6.7% + 半价差 11.1%；当前观察到的最好机会不覆盖成本，只能等更大错位或改挂单。
6. 两周内能检验：不满足 — 独立结果按事件计只有 6 个历史事件、两周最多再加约 2 个，达不到 30；只能进待选区做前向记录。
7. 出处可查：满足（部分）— 每个数字都有 URL + 抓取时间 + 原文片段（见下）；「上线当日 LIT 价格」这一项未查到，已如实标注为复现待办。

## 出处

- https://gamma-api.polymarket.com/public-search?q=FDV%20above%20one%20day%20after%20launch&limit_per_type=50 — 访问 2026-10-20 — 已读（`pagination.totalResults=149`、`hasMore=true`；前 50 条中 46 条为该模板）
- https://gamma-api.polymarket.com/events?slug=metamask-fdv-above-one-day-after-launch — 访问 2026-10-20 — 已读（8 档中间价、`feeSchedule`、`endDate=2027-01-01T05:00:00Z`、规则原文）
- https://gamma-api.polymarket.com/events?slug=papertrade-fdv-above-one-day-after-launch — 访问 2026-10-20 — 已读（`liquidity=184039.1655`、`volume=282854.88727`、`endDate=2028-01-01T05:00:00Z`、规则原文同模板）
- https://gamma-api.polymarket.com/events?slug=lighter-fdv-above-one-day-after-launch — 访问 2026-10-20 — 已读（`>$2B`=1、`>$3B`=0，`resolved`）
- https://gamma-api.polymarket.com/events?slug=zama-fdv-above-one-day-after-launch — 访问 2026-10-20 — 已读（`>$300M`=1、`>$400M`=0）
- https://gamma-api.polymarket.com/events?slug=usdai-fdv-above-one-day-after-launch — 访问 2026-10-20 — 已读（`>$1B`=1、`>$2B`=0）
- https://gamma-api.polymarket.com/events?slug=edgex-fdv-above-one-day-after-launch — 访问 2026-10-20 — 已读（`>$600M`=1、`>$700M`=0）
- https://clob.polymarket.com/book?token_id=<metamask 各档 YES token> — 访问 2026-10-20 — 已读（bestBid/bestAsk 见「证据」第 3 条）
- https://api.coingecko.com/api/v3/coins/lighter?localization=false&tickers=false&market_data=true&community_data=false&developer_data=false — 访问 2026-10-20T04:01:53Z — 已读（`total_supply=1e9`、`current_price.usd=3.19`、`fdv=3192043356`）
- https://api.hyperliquid.xyz/info — 访问 2026-10-20 — 已读（`metaAndAssetCtxs`：`LIT.markPx=3.1991`；`spotMeta` 无 LIT 代币；`perpDexs` 10 个 HIP-3 dex）
- https://hyperliquid.gitbook.io/hyperliquid-docs/trading/hyperps — 访问 2026-10-20 — 已读（hyperp 定义、oracle = 8 小时 EMA、mark 上限 3×/1.5×、oracle ≤4× 一月均价、上线后转 vanilla）

---
