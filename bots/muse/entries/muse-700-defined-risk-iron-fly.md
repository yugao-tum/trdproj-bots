> 作者：Muse 直属 agent（muse-agent-2）｜ 试运行第 1 批

---
id: muse-700
name_zh: 月到期铁鹰：有界短波动率
name_en: Defined-Risk Monthly Iron Fly on Deribit USDC Options
bot: muse
date: 2026-10-20
market: crypto
pm_category: -
kind: improvement
improves: V-V1-straddle-dhedge
category: V
return_type: vol_harvest
instruments: BTC, ETH, SOL（Deribit USDC 线性期权）
venues: Deribit
data: Deribit 公共 API（api.deribit.com，免密钥）：USDC 线性期权链与盘口、DVOL（BTC/ETH，657 天，2025-01-01 至 2026-10-19）、已到期期权的 chart 数据（实测 2026-10-20 可取 20OCT26 合约）；12 个月完整逐笔盘口历史未取得，回测用已到期合约成交价 + 当前价差 haircut
test_2w: 用已到期月度期权重建 2025-11 至 2026-10 的 30 个“标的×月到期”结果（BTC/ETH/SOL 各约 10 个），每个算 1 个独立结果；另在 30OCT26 做一次前向试点。失败标准：30 个结果扣估算价差/费用后合计 P&L < 0，或胜率 < 50%，或单次亏损超过按报价算的最大亏损
status: 待核
confidence: 中
---

## 一句话

每月在 Deribit 用 USDC 线性期权卖出一组 7–14 天到期的 ATM 跨式、同时买入 10Δ 双翼（铁鹰），赚“隐含波动率高于随后实现波动率”的波动率风险溢价；最大亏损在建仓时锁死，持有到期或收回 50% 权利金。

## 钱从哪里来

付钱的是**买期权的人**：现货持有者买保险、方向交易者买凸性、做市商在跳空和挤兑中索要风险补偿。BTC/ETH 期权市场长期存在正的风险溢价：

- FMA 论文（Deribit BTC 期权，2025 年会议稿）摘要明确写：“The BTC volatility risk premium ... is, on average, positive and persistent.” 同文还记录压力期定价核非单调、短到期翼部 IV 明显高于 ATM，说明尾部保险并不便宜，但卖方仍拿到平均溢价。
- 本项目自算 2025-01-01 至 2026-10-19、627 个日观测：用 DVOL 对随后 30 天实现波动（Coinbase 日线），BTC 的 IV−RV 均值 **+4.09** 个波动率点、中位 **+7.61**、为正 **67.6%**；ETH 均值 **−0.13**、中位 **+5.14**、为正 **57.7%**。BTC 的溢价最稳，ETH 均值被尾部事件吃掉。
- `giovannibrusco/btc-vrp-strategy` 自报：2021-06 至 2024-09，DVOL 高于 30 天实现波动 **74%** 的交易日，平均 **+6.2** 个点；但作者 2026-10 审计后承认样本内 Sharpe 仅 **0.83（p=0.12）**、9 笔样本外 Sharpe 2.16、最大回撤 −5.3%，**edge 不大且统计上不显著**。这是来源自报，未核实。
- `tfrmma/options-volatility-trading-strats` 的 README 强调：加密期权前月合约常见 **20–50bps** 宽，回测必须按 bid/ask 成交；VRP 会压缩、倒挂、在宏观事件周围失控，所以要用 z-score 和 vega 目标，而不是机械地每天卖。

为什么用铁鹰而不是裸跨式：卖方赚的是溢价，但裸跨式在跳空时亏损无上限；买入 10Δ 双翼把最大亏损变成已知数，代价是少收一部分权利金。对 5,000 USDT 的账户，这个交换是必要的。

## 规则

- **标的与场所**：Deribit USDC 线性期权，BTC、ETH、SOL。USDC 线性合约的 contract size 分别为 1 BTC、1 ETH、10 SOL，最小下单量 0.01 BTC、0.1 ETH、10 SOL，可以用 0.05 BTC / 1 ETH / 10 SOL（1 张）这样的小颗粒度建仓；反向期权 BTC 最小 0.1 BTC，单笔保证金就会顶到 2,500 上限，故不作为主结构。
- **进场时间**：每个月到期日（当月最后一个周五 08:00 UTC）前的 **7–14 天**，在 08:00 UTC 建仓；每月每个标的只做一次。若当天没有 7–14 天到期的月度序列，跳过该标的。
- **结构**：
  - 卖出 1 单位 ATM 跨式：取最接近指数的行权价 K，卖 1 张 K 看涨 + 1 张 K 看跌。
  - 买入 1 张 10Δ 看跌（行权价 K_put < K）+ 1 张 10Δ 看涨（K_call > K），同到期日。
  - 10Δ 用建仓时该合约的 mark IV 代入 Black-Scholes 求 delta，取绝对值最接近 0.10 的已挂牌行权价；缺 10Δ 时取最近的更虚一档。
  - 只按**可成交价**算：卖出腿用 bid，买入腿用 ask；净权利金 C > 0，且 C / 最大亏损 ≥ 0.5 才建仓。
- **仓位**：BTC 0.05 张（即 0.05 BTC 名义）、ETH 1 张、SOL 1 张（10 SOL）；三标的合计初始保证金约 2,251 USDT（按 0.15×指数×2 条短腿粗算），低于单场所 2,500 上限；单次最大亏损约 463 USDT，占 5,000 本金的 9.3%。
- **Delta 对冲**：建仓时组合 delta 约 0；当 |组合 delta| > 0.15 时，用 Deribit 永续/季度合约对冲回 ±0.05 内，最多调 2 次；用 Whalley-Wilmott 带宽，不按固定时钟调仓（`tfrmma` README 的 execution 规则）。
- **出场**：权利金收回 50%（即买回铁鹰的成本 ≤ 0.5C）即平仓；否则持有到期。DTE ≤ 3 时不再新开，已有仓位持有到期。不设止损——双翼就是止损。
- **过滤**：只做两个风险闸门：(a) 建仓日 DVOL 高于过去 1 年 90 分位则跳过（避免在波动率尖峰卖 vol）；(b) 任一腿无双边报价、或 ATM 跨式的 bid/ask 中点价差 > 10% 则跳过。**不做** IV 方向择时：`giovannibrusco` 测试了 5 个 regime 过滤器，和交易 PnL 的相关性都 < 0.25，作者已放弃。
- **结算**：Deribit 欧式现金结算；USDC 线性期权以 USDC 结算，到期内在价值按到期指数价计算；USDC 线性月度期权交割费 0.015%（上限为期权价值的 12.5%）；反向日到期期权交割费 0%，本策略不用日到期。

## 证据

- **机制**：FMA 论文摘要（已读）给出 BTC VRP 平均为正且持续；同文记录短到期翼部 IV 85–91% vs ATM 64–70%，说明翼部贵，但 ATM 跨式仍是溢价的主要来源。本条买翼、卖 ATM，等于用一部分溢价买尾部保护。
- **本项目自算**（627 天，DVOL vs 随后 30 天 RV）：BTC 均值 +4.09、中位 +7.61、正 67.6%；ETH 均值 −0.13、中位 +5.14、正 57.7%。方法：DVOL 日收盘减随后 30 个自然日 Coinbase 日线收盘对数的年化标准差；未扣成本；这是**自算**，不是来源数字。
- **来源自报，未核实**：`giovannibrusco` 的 74%/+6.2 点、样本内 Sharpe 0.83（p=0.12）、样本外 2.16（9 笔）、最大回撤 −5.3%；作者明确写 edge “modest and not statistically significant”，并记录 3 倍多仓位在样本内最大回撤 −49.7%（仓位一起崩），所以本条把三标的合计最大亏损压到本金的 9.3%。
- **成本证据**：`tfrmma` README 明确“every fill at bid/ask, never mid”“crypto options routinely trade 20-50bps wide even on BTC/ETH front-month”。本条所有报价示例都用 bid/ask。
- **当前可成交报价**（2026-10-20 01:30 UTC，Deribit USDC 线性，30OCT26，7–14 天窗口；指数 BTC 81,455、ETH 2,391、SOL 104.3）：
  - BTC：卖 81,000C bid 2,180 + 卖 81,000P bid 1,580 = 3,760；买 75,000P ask 305 + 买 88,000C ask 230 = 535；净收 **3,225 USDC/1 BTC**；最大亏损在 88,000 翼：7,000 − 3,225 = **3,775 USDC**（在 75,000 翼为 6,000 − 3,225 = 2,775）；0.05 BTC 单位净收 **161**、最大亏损 **189**。
  - ETH：卖 2,400C bid 74 + 卖 2,400P bid 80 = 154；买 2,100P ask 12.4 + 买 2,700C ask 8.6 = 21；净收 **133 USDC/1 ETH**；最大亏损 300 − 133 = **167**。
  - SOL：卖 104C bid 4.0 + 卖 104P bid 3.6 = 7.6；买 91P ask 0.7 + 买 121C ask 0.6 = 1.3；净收 **6.3 USDC/SOL**（1 张 10 SOL = 63）；最大亏损在 121 翼：17 × 10 − 63 = **107**（在 91 翼为 13 × 10 − 63 = 67）。
  - 三标的合计：净收约 **357**、最大亏损约 **463**、初始保证金约 **2,251**；实际费率+价差成本约 **4.5%**（BTC 4.5%、ETH 3.5%、SOL 6.7%）。
- **为什么不是 1DTE**：同为反向 BTC，21OCT26 1DTE 铁鹰净收 0.0126 BTC（约 1,024）、最大亏损 1,505；按 4 腿 0.03% + 价差，成本约 **19.1%** 的净权利金（价差 98 + 手续费 97.7）。反向 10DTE 约 **5.7%**（价差 86 + 手续费 97.7），USDC 线性 10DTE 约 **4.5%**（价差 47.5 + 手续费 97.7）；1DTE 的价差/权利金比例太高，所以选 7–14DTE，不选日到期。

## 数据

- `https://www.deribit.com/api/v2/public/get_instruments?currency=USDC&kind=option&expired=false`：USDC 线性期权链（BTC_USDC、ETH_USDC、SOL_USDC 等）。
- `https://www.deribit.com/api/v2/public/get_book_summary_by_currency?currency=USDC&kind=option`：当前 mark IV、bid/ask、标记价。
- `https://www.deribit.com/api/v2/public/get_order_book?instrument_name=...`：单合约盘口。
- `https://www.deribit.com/api/v2/public/get_index_price?index_name=btc_usdc`（eth_usdc、sol_usdc）：指数。
- `https://www.deribit.com/api/v2/public/get_volatility_index_data?currency=BTC&start_timestamp=...`：DVOL 日线，657 天（2025-01-01 至 2026-10-19）；ETH 同；SOL 无 DVOL。
- `https://www.deribit.com/api/v2/public/get_tradingview_chart_data?instrument_name=BTC-20OCT26-81000-C&start_timestamp=...&end_timestamp=...&resolution=60`：已到期期权的小时成交价；实测 2026-10-20 可返回 20OCT26 合约的 ticks/close。
- 全部免费、免密钥。限制：chart 数据是最后成交价，不是历史 bid/ask；回测用当前价差 haircut（BTC 1.5%、ETH 1.3%、SOL 4.8% 的权利金比例）近似，不能当成真实可成交价。12 个月完整盘口历史没有免费来源。

## 两周内怎么检验

1. **历史重建（主要）**：对 2025-11 至 2026-10 的每个月度到期，取 BTC/ETH/SOL 三个标的，在到期前 7–14 天的 08:00 UTC 建仓；用已到期合约的 chart close 作为成交价，卖腿减半个当前价差、买腿加半个当前价差；按 0.03%/腿手续费、月度交割费 0.015% 计；到期用指数结算价算内在价值。每个“标的×月到期”算 1 个独立结果，目标 **30 个**（BTC/ETH/SOL 各约 10 个）。
2. **前向试点**：2026-10-20 至 2026-10-30 的 30OCT26 窗口，按上面报价实际挂单一次，记录真实成交价、滑点、保证金、到期 P&L；这是 3 个额外结果，不替代历史 30 个。
3. **失败标准**：30 个结果扣估算成本后合计 P&L < 0；或胜率 < 50%；或任一笔实际亏损超过按建仓报价算的最大亏损（说明执行/保证金假设错）；或三标的同月同时触发最大亏损（相关性风险）。
4. **独立性说明**：BTC/ETH/SOL 同月会受同一波市场冲击影响，严格说不是 30 个完全独立事件；条目把“同月三标的”视为 3 个结果，但在报告里同时按“月份”聚合成 10 个 cluster，避免把相关性当分散化。

## 成本与容量

- **手续费**：Deribit 期权 0.03%/腿（按标的的名义，单腿上限为期权价值的 12.5%）；USDC 线性月度期权交割费 0.015%（上限 12.5% 期权价值）；反向日到期 0% 交割费，本策略不用日到期。按 4 腿、0.05 BTC/1 ETH/10 SOL 计，三标的合计约 **9 USDC/月**。
- **价差**：按当前盘口，BTC 约 47.5/3,225 = 1.5%、ETH 约 1.7/133 = 1.3%、SOL 约 3/63 = 4.8% 的权利金；三标的加权约 **4.5%**。
- **保证金**：BTC 0.05 约 1,222、ETH 1 约 717、SOL 10 约 312，合计约 **2,251 USDT**；单场所 < 2,500，5,000 本金可放下，且最大亏损 463（9.3% 本金）。
- **容量**：每月 1 次、3 个标的，月毛权利金约 357 USDC；一年 12 次，毛权利金约 4,284 USDC。**这不是净利**：按 VRP 均值 4 个点、成本 4.5% 粗算，净边际约 5–10% 的权利金（约 18–36 USDC/月），年化约 8–17% 的 2,500 保证金；按规则要求的 0.30%/边压力成本（约 45 USDC/月），净边际接近 0。结论：实际费率下勉强过 8%，压力成本下不够，这是本条最大的不确定性。
- **容量上限**：SOL 的 10Δ 翼部盘口只有 0.1–0.2 的深度，单笔 10 SOL 可以，放大到 100 SOL 就会吃掉价差；BTC/ETH 可以放到 0.1 BTC/3 ETH，但会顶到 2,500 保证金上限。本条只做 1 组，不扩仓。

## 风险

- **VRP 转负**：2026-10-20 当前 1DTE BTC IV 约 31、ETH 约 47，而近期实现波动更高；此时卖 vol 会亏。条目的 DVOL 90 分位闸门只能挡尖峰，挡不住“IV 低于 RV”的慢性负溢价。`giovannibrusco` 的 edge 本来就不显著（p=0.12），这是策略风险，不是执行风险。
- **跳空/双翼穿透**：最大亏损 463 是“同时穿透两翼”的上限；单翼被穿透时亏损介于 0 和 463 之间。一次最大亏损 ≈ 1.3 个月的权利金，连续两次会显著回撤。
- **相关性**：BTC/ETH/SOL 在暴跌中同向，三标的一起触发最大亏损的概率不能用“独立”估计；`giovannibrusco` 的 3 倍多仓位样本内最大回撤 −49.7% 就是教训。
- **翼部流动性**：SOL 的 10Δ 翼部最薄，实际成交可能比报价差 0.1–0.2；回测的价差 haircut 可能偏低。
- **保证金/交易所**：USDC 线性期权的保证金、交割费和 USDC/USDT 兑换按 Deribit 规则；交易所集中托管、规则变更、指数插针都可能让“最大亏损”失效。不借钱、不加杠杆。
- **模型风险**：10Δ 用 Black-Scholes + mark IV 近似，和 Deribit 的组合 delta 可能有偏差；建仓后用实际组合 delta 校正。

## 改进了什么

- **原版**：`V-V1-straddle-dhedge`（Delta 对冲卖跨式）赚同样的 VRP，但裸卖跨式的尾部亏损无上限；对 5,000 USDT 账户，一次跳空就可能穿仓。
- **改动**：
  1. 买入 10Δ 双翼，把最大亏损锁死在本金的 9.3%（463/5,000）；代价是净权利金从裸跨式的约 3,760 降到 3,225（BTC 例），约 14% 的溢价让渡给保险。
  2. 用 USDC 线性期权把最小颗粒度从 0.1 BTC 降到 0.01 BTC，使 0.05 BTC 单位可行；反向期权的最小 0.1 BTC 会让单笔保证金顶到 2,500 上限。
  3. 选择 7–14DTE 而不是 1DTE：反向 1DTE 的实际成本约 19.1% 权利金，反向 10DTE 约 5.7%、USDC 线性 10DTE 约 4.5%，同样的 VRP 下净边际高得多。
  4. 保留 delta 对冲，但改用 Whalley-Wilmott 带宽、最多 2 次；`giovannibrusco` 的日频对冲在 BTC 上成本高（对冲腿平均每笔亏损），带宽能省一部分。
  5. 用 50% 权利金捕获出场（源策略已验证 21/30 个参数组合为正），而不是持有到到期吃满 theta；降低尾部暴露时间。
- **为什么更好**：不是承诺更高收益，而是在同样的 VRP 暴露下把破产风险从“无上限”变成“已知 9.3% 本金”，并降低单位权利金的交易成本；对竞赛的 5,000 USDT/2,500 单场所约束更合适。
- **怎么证明**：30 个月度到期重建，比较“铁鹰” vs “同标的裸跨式 + 同样 delta 对冲”的净 P&L、最大回撤、成本占比；若铁鹰在净 P&L 不低于裸跨式 80% 的前提下最大回撤显著更低，改进成立。

## 门槛自查

1. 机制说得清：**满足**。付钱的是买保险/买凸性的人；VRP 平均为正且有学术与自算证据；翼部是保险费，不是收益来源。
2. 有免费数据能检验：**满足**。Deribit 公共 API 免密钥；DVOL 657 天；已到期期权 chart 数据可重建 30 个月度到期；限制是只有成交价、没有历史盘口，已用价差 haircut 处理。
3. 小资金能做：**满足**。0.05 BTC/1 ETH/10 SOL，保证金约 2,251，最大亏损 463，低于 2,500 单场所和 5,000 总本金；亏损有上限。
4. 不重复：**满足（改进）**。`improves: V-V1-straddle-dhedge`；与 `V-V3-iv-timed-spread`（卖看跌价差、IV 择时）、`dot-030`（同到期偏斜溢价）、`dot-031`（跨到期期限结构）、`V-V2-poly-longshot`（预测市场）关键变量不同。
5. 扣成本后粗算够用：**不确定**。实际费率+价差 4.5%，按 VRP 均值粗算年化 8–17%，刚过线；按 0.30%/边压力成本净边际接近 0。没有把“毛权利金”当净利。
6. 两周内能检验：**满足**。用历史已到期合约重建 30 个“标的×月到期”结果，两周内可完成；前向试点 3 个结果。失败标准明确。
7. 出处可查：**满足**。每个数字有链接、访问日期、阅读程度；自算数字标明方法与“自算”。

## 出处

- https://www.fmaconferences.org/Vancouver/Segarra.pdf — 访问 2026-10-20 — 已读（摘要；正文第 746–749 行：短到期翼部 call IV 约 85%、put 约 91%，ATM 64–70%；VRP 平均为正且持续）
- https://github.com/giovannibrusco/btc-vrp-strategy — 访问 2026-10-20 — 已读 README（74% 交易日、+6.2 点、2021-06 至 2024-09；IS Sharpe 0.83、p=0.12；OOS 2.16/9 笔；最大回撤 −5.3%；regime filters 与 stop loss 被否；3 倍仓位 −49.7%；来源自报，未核实）
- https://github.com/tfrmma/options-volatility-trading-strats — 访问 2026-10-20 — 已读 README（bid/ask 成交、前月 20–50bps 宽、VRP z-score、Whalley-Wilmott 带宽；无收益结果）
- https://support.deribit.com/hc/en-us/articles/25944746248989-Fees — 访问 2026-10-20 — 摘要（直接抓取 403，经搜索缓存读取：期权 0.03%/腿；交割费 0.015%，上限 12.5% 期权价值；日到期期权交割 0%）
- https://support.deribit.com/hc/en-us/articles/31424939096093-Inverse-Options — 访问 2026-10-20 — 摘要（反向 BTC 1 BTC/最小 0.1、ETH 1 ETH/最小 1；每日 08:00 UTC 到期、币本位现金结算；USDC 线性合约规格由 API 的 contract_size/min_trade_amount 字段核对）
- https://support.deribit.com/hc/en-us/articles/25944688876957-Contract-Introduction-Policy — 访问 2026-10-20 — 摘要（BTC/ETH 每日 08:00 UTC 到期，日到期每天新挂；月度最后一个周五到期）
- https://www.deribit.com/api/v2/public/get_volatility_index_data?currency=BTC&start_timestamp=1735689600000&end_timestamp=1792454400000&resolution=1D — 访问 2026-10-20 — 已调用（BTC DVOL 657 天；ETH 同）
- https://www.deribit.com/api/v2/public/get_tradingview_chart_data?instrument_name=BTC-20OCT26-81000-C&start_timestamp=1792022400000&end_timestamp=1792454400000&resolution=60 — 访问 2026-10-20 — 已调用（已到期期权小时成交价可读）
- https://www.deribit.com/api/v2/public/get_order_book?instrument_name=BTC_USDC-30OCT26-81000-C — 访问 2026-10-20 — 已调用（30OCT26 铁鹰四腿报价；同一时刻 ETH_USDC/SOL_USDC 同法）
- 自算 DVOL−RV 统计与 30OCT26 报价表 — 2026-10-20 — 自算（数据源为上面两个 API；脚本在临时目录，未提交）
