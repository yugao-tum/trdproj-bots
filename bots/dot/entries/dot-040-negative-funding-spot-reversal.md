---
id: dot-040
name_zh: 负资金费背离后的现货反转
name_en: Negative-funding spot reversal proxy
bot: dot
date: 2026-10-19
market: crypto
pm_category: -
kind: supplement
improves: R-R4-funding-extreme
category: R
return_type: direction
instruments: BTCUSDT现货主检验；ETHUSDT、SOLUSDT现货敏感性
venues: Binance公开历史数据；现货执行仅为模拟假设
data: 已核官方现货日线2023-01-01至2026-09-30及8小时资金费2024-01-01至2026-09-30，免费免密钥；历史L2、OI、CVD和真实滑点未齐
test_2w: 已完成固定spot-proxy-v1的3币×2成本历史模拟；BTC仅19持仓段且独立性未证，须按共同负费冲击聚类；年化未达8%或3%组合门槛，不晋级
status: 待核
confidence: 中
---

## 一句话

前一完整UTC日三次资金费全负、价格却未贴近20日最低收盘时，下一日开盘模拟买入现货，在资金费转非负或满7日时退出；这是自拟现货代理规则，不收资金费，也不能证明逼空发生。

## 钱从哪里来

假说是负费与价格韧性反映偏空需求或仓位拥挤，随后回补和价格修正使现货上涨。CryptoCred原帖同时强调OI、CVD及清算背景的限制[S1]。付款持续性未证；与dot-019合同资金费carry、dot-023单纯价格RSI不同，本条必要变量是资金费与价格的背离。

## 规则

- 固定规则spot-proxy-v1于2026-10-19 18:49 UTC冻结，18:58首次运行，未搜索参数。BTC为主检验，ETH/SOL是预设敏感性，各自独立模拟5000 USDT，不是同时投入15000或三种机制。
- 空仓时，仅用前UTC日00/08/16三笔已完成资金费：全部<0，且前收盘≥截至前日最近20日最低收盘×1.01，今日开盘模拟买入。不得使用今日资金费。
- 有仓时，前日08/16两笔资金费均≥0，或到入场日+7天开盘，任一条件满足即退出；退出当天不重入。最终日先按规则交易，再收盘强平。没有日内止损。
- 总本金5000，场内1250、闲置3750；买入名义=min(1100，交易前场内净值×90%)，费用从场内扣。只持现货，不借款、不做空、不持永续。
- 2024-01-02至2026-09-30模拟；2025-01-01起标为OOS并继承跨界持仓和现金。这是事后固定规则分段，并非真正未见未来的前向交易。

## 证据

- 来源仅提供负费/价格背离的教育性机制观点，没有本规则收益证据[S1]。
- 本研究既有历史模拟，全期1003日；每边成本0.30%/0.60%下：BTC净额134.3565/3.4933 USDT，CAGR 0.9696%/0.0254%；ETH净额−62.4416/−191.0404，CAGR −0.4563%/−1.4077%；SOL净额−242.9332/−491.4851，CAGR −1.7962%/−3.6954%。全部6情景保留，未择优。
- 净额贡献以固定5000为分母，CAGR按各段起始净值及实际日历天数算。BTC基准/压力最大收盘回撤3.9206%/4.7940%；删去最佳日历月后的净额35.6325/−80.6644 USDT，只是归因诊断，不是另一可交易策略。
- 既有13个自编单测及独立逐日账本重建通过，6情景6018日行一致；这是机械核验，不是6018个独立结果。BTC/ETH/SOL分别19/21/51持仓段，不能直接相加。详见已公开的研究摘要[S4]。
- 固定变体实际回测已有1项、6情景；本次整理新增回测0。完整拥挤/逼空机制收益未知，未验证费用、滑点不填0。
- 补充来源Forced-or-frantic v3的OI分类需等事件起点后2小时，不能预测同窗位移；其起点强度控制与全窗总清算量控制结论不同，后者置信区间跨0，均属来源自报、未复现。原始文件缺失且重建注明requester-pays，不能据此验证本资金费现货代理[S5]。

## 数据

Binance月度现货klines及USD-M fundingRate归档免密钥，已下载并逐档核SHA；现货三币共4107行，资金费共9036行[S2、S3]。现货2025年起时间戳单位变化已在输入校验中处理。日线开/收盘成交是假设，不能替代当时盘口、延迟和容量。

输入指纹：spot_daily SHA-256 a008fbd0514f4d01bd477fc008de9fb24b8dfae5e83ebda2ced8bbf2e89bcf0a；funding SHA-256 310508098d4b9a30a33823368a80e8fe7c034c05f8cb37513d7de3b101a449a8；既有汇总SHA-256 42dddf26dab48d5837dfe698040a8a2c7e0d6a6336201527814d558a36e866a2。

## 两周内怎么检验

已有历史初验完成，下一步只核固定规则的独立事件、真实执行和机制代理，不因低收益改阈值挑赢家。相邻负费阶段、同期多币共同冲击须聚类；BTC主检验19段不足30，SOL的51段也不是独立性证明。前向采集尚未启动。

失败标准：5000总资本口径年化<8%，且没有≥3%与低趋势相关性的组合证据，则盈利门槛不通过；当前已触发。若独立有效簇<30、真实成交或资金路径不能复核，也不能晋级。这只否定固定简化规则的本次筛选，不否定全部拥挤反转机制。

## 成本与容量

每次模拟买卖腿按实际成交名义0.30%，压力0.60%；现货无资金费收付。BTC全期费用125.2726/243.9993 USDT。历史L2、额外滑点和开盘成交概率未知，不能将其写成0或断言真实成本已覆盖。

6情景未观察到开/收盘或日高上界超过2500的场内市值；严格动态2500是本研究诊断口径。1100是预算名义而非已测成交容量。真实每月可执行机会数未知；不能用持仓段除月份冒充独立机会频率。

## 风险

负费可能是合理避险而非待回补空头；缺OI/CVD无法辨别。价格持续下跌、日内跳空、开盘不可按假设成交、交易所及USDT风险均可亏损。没有日内止损，收盘回撤不代表最大盘中亏损；三币敏感性共享市场冲击。

## 改进了什么

本条改按 `kind: supplement`，`improves: R-R4-funding-extreme` 归类。分类依据是 [known 中的 R-R4-funding-extreme](https://github.com/yugao-tum/trdproj-bots/blob/bc5dd79aa7da5e07cdd3ed2d22a158ab620222fb/known/KNOWN.md#L79)（2026-10-20 UTC 核对，仅含名称，不含既有规则或绩效）。极端负资金费反向，价位过滤和现货表达为变体。

本条提供的研究补充：整理负资金费反向的冻结现货代理模拟、成本压力和资金诊断；原收益门槛未通过，持仓段独立性未证，现货表达不产生新机制。

补充材料相对既有实现的新增性与采纳价值交由评审判断；本次申请补充核对，尚未采纳，不主张新机制、已证改进或盈利，提交状态为待核。

## 2026-10-20 补充送审说明

- **送审目的与增量**：向 `R-R4-funding-extreme` 提交负费/价格背离的冻结现货代理筛查，检验机制观点落到可计算规则后的收益幅度，而非把现货当资金费收入。BTC主检验0.30%/0.60%每边全期净额134.3565/3.4933 USDT，CAGR 0.9696%/0.0254%；ETH/SOL两档均负。BTC压力档减去最佳月份贡献后为−80.6644 USDT，仅为归因诊断。负面价值是显示这项简化代理的微弱正值对费用和少数月份敏感，不能由“负费”直接推成可盈利挤空。
- **可复现的内容**：[公开复现包](../notes/reproduction/README.md)中的C40规则、资金费网格校验、模拟器及输出摘要，结合指定现货/funding输入可重建全部6情景、6,018日账行及逐腿费用；[机制摘要](../notes/20261019-c40-spot-proxy.md)与[稳健性诊断](../notes/20261019-frozen-rule-robustness.md)保留全部不利结果。6018行是账本规模，既有机械复现不增加独立交易或回测机制。
- **边界与分别送审理由**：现货不领取资金费，OI/CVD和真实L2缺失，不能证明拥挤、因果或可执行滑点；BTC仅19个持仓段，跨币共同冲击未完成聚类。与[dot-023](dot-023-sol-rsi14-oversold.md)的价格RSI信号不同，故分别呈交给不同known补充对象；共享资产时期和代码框架不构成独立重复验证，失败也不否定所有资金费反转。
- **请评审核对**：这项明确区分资金费信号、现货价差收益和成本敏感性的代理反证，是否具有关键补充价值。3%/8%盈利要求未过、独立样本未足，不请求收录或改进资格，也不推断known私有实现的表现。

## 门槛自查

1. 机制说得清：满足定义；负费/价格背离的付款假说清楚，拥挤与因果未证
2. 有免费数据能检验：满足简化规则历史输入要求；真实可成交收益和OI/CVD仍不足
3. 小资金能做：不确定；模拟预算及市值诊断通过，真实深度/滑点未验证
4. 不重复：同机制补充，非新策略——对应 `R-R4-funding-extreme`；补充材料的新增性与采纳价值仍待核，不据 dot 内部区别主张全局新颖性。
5. 扣成本后粗算够用：不满足；BTC不足3%，其余币亏损
6. 两周内能检验：不满足现有独立样本要求；主检验19段，不能靠多币/日行凑30
7. 出处可查：满足当前描述；观点、官方输入和本研究模拟分开列示，收益不外推

## 出处

- [S1] https://x.com/CryptoCred/status/1694339656853188768 — 访问2026-10-19 UTC — 已读（负资金费与价格背离、OI/CVD/清算限制；后续重开失败不计新阅读）
- [S2] https://github.com/binance/binance-public-data — 访问2026-10-19 UTC — 已读（README的Data Information、CHECKSUM及时间戳说明）；https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/1d/BTCUSDT-1d-2023-01.zip — 同日已读并校验，官方月档示例
- [S3] https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Get-Funding-Rate-History — 访问2026-10-19 UTC — 已读（fundingRate、fundingTime字段）；https://data.binance.vision/data/futures/um/monthly/fundingRate/BTCUSDT/BTCUSDT-fundingRate-2025-01.zip — 同日已读并校验，实际输入路线为官方月档
- [S4] https://github.com/yugao-tum/trdproj-bots/blob/main/bots/dot/notes/20261019-c40-spot-proxy.md — 访问2026-10-19 UTC — 已读（本研究公开摘要；冻结规则、6情景、机械核验与指纹，不是第三方来源自报）
- [S5] https://github.com/edwinyeeshunwan/forced-or-frantic/blob/main/CORRECTIONS.md ；https://github.com/edwinyeeshunwan/forced-or-frantic/blob/main/reanalysis/protocol/CORRECTION_PROTOCOL.md#L7-L25 ；https://github.com/edwinyeeshunwan/forced-or-frantic/blob/main/reanalysis/outputs/results/primary_effects.json ；https://github.com/edwinyeeshunwan/forced-or-frantic/blob/main/reanalysis/outputs/results/sensitivity_grid.csv ；https://github.com/edwinyeeshunwan/forced-or-frantic/blob/main/data/README.md — 访问2026-10-19 UTC — 已读（v3更正、分类时点、primary/S5a控制口径及原始数据可得性；作者输出未复现）
