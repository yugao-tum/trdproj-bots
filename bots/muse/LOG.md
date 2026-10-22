# LOG — muse 工作日志

- 2026-10-19：建目录，首次提交 README.md / INDEX.md / CLAIMS.md / LOG.md。参加第 1 轮（2026-10-19 至 2026-10-25）。

## 2026-10-20 01:28 UTC

- 做了什么：按 GUIDE/ENTRY 完成第 1 轮 deepseek worker 的两条研究并交稿。muse-800 为 Polymarket `btc-updown-5m` 的完整集铸造做市（new，PM/crypto，M/service）；muse-801 为 Base 上 Aerodrome Slipstream USDC-USDT 稳定币 LP（supplement，improves M-M2-amm-lp）。已更新 CLAIMS（先认领后完成）、INDEX、LOG。
- 查重：读 known/KNOWN.md（135 条）、bots/dot/CLAIMS 与 40+ 条 dot entries、muse-agent-1~5 的 notes。muse-800 与 M-M1-orderbook-mm、M-M4-poly-rewards、A-A5-poly-complete-set、dot-032（Q-score）、dot-006（负风险完整集）关键变量不同；muse-801 与 M-M2-amm-lp 同机制，按 supplement 交，不冒充新策略。
- muse-800 证据：GitHub `0xbrutusdev/polymarket-5min-crypto-trading-bot`（README/config/strategy/backtest 已读，未执行）；data-api 公开账户 `spork30` 的 89 天 PnL（economic 21,402.56、market 11,639.39、maker_rebate 9,849.15 且 9/12 后字段冻结、volume_usdc 3.18M）；最近 5,500 条 activity（约 24h 内 4,451 TRADE、289 SPLIT@750、286 MERGE、1 MAKER_REBATE $71.1599）。Oct 5–12 tape：2,012 窗，market PnL +$292.98 ≈ $0.146/窗（不含返佣），作者自报 42 bps 返佣。官方费用/返佣/5m 规则已读：crypto feeRate 0.07、maker 返 20%、按日、最低 $1；5m TWAP 奖励已于 2026-08 结束，本条不依赖它。
- muse-801 证据：DefiLlama 459 天（2025-07-10 至 2026-10-20）base APY 均值 11.78%、中位 7.00%、65 个 7 日窗口中位 8.49%、当前 19.40%；TVL $1.076M、24h 量 $6.55M；GeckoTerminal 池 `0xa41bc0...fcd1` 名称 `USDT / USDC 0.01%`。费率口径有冲突：DefiLlama `poolMeta=CL1 - 0.0008%` vs GeckoTerminal 0.01%；按 APY 反推 1 bp 才自洽，Base RPC `eth_call` 本次超时，未取得链上 `fee()`，已在条目中披露。Hyperion USDT-USDC 有 470 天/中位 15.8% 的记录，但末段 144 天 APY/TVL 完全不变、volume 字段为空，疑似停更，未采用。
- 风险/边界：没有交易、没有钱包/密钥/账户、没有运行第三方代码；没有独立完整回测（两条均 backtest_count=0），账户 PnL 是 venue API 事后值，不是审计。muse-800 的收益高度依赖 20% maker rebate（账户 tape 的价差 edge 大部分被逆向选择吃掉）；muse-801 的全期日度中位仅 7.0%、50% 区间折扣情景中位约 4.2%，所以只作 supplement，门槛 5 标“边际”。
- 本轮计数：提交 2 篇待核（1 new + 1 supplement）；没有声称七门槛全通过；muse-800 自评 7 项满足（有返佣/成交率条件），muse-801 自评 5 边际、其余满足/有缺口。原始数据、账户 JSON、chart JSON 留在本地 `/tmp/opencode/muse/` 与 `/tmp/opencode/`，未入仓库。
- 下一轮（如继续）：优先用 Base RPC 复核 Aerodrome 池 `fee()`/tickSpacing 并尝试取得 tick 级深度；用公开 data-api 对 `btc-updown-5m` 做 30 个 UTC 日的 taker-print 回放（不执行第三方代码，自写只读脚本）；再找一条真正新的加密做市/返佣机制，优先低门槛 maker rebate 或稳定币 LP 的改进维度。

## 2026-10-20 01:40 UTC（补）

- 补记候选筛选：新增 `notes/20261020-crypto-mm-screen.md`，记录本轮 22 条加密做市/流动性候选及淘汰理由（Hyperion 数据停更、Hyperliquid/Backpack 正费、Kalshi 激励将结束、Kraken/dYdX 高量门槛、ApeX 负费过小、EURC 非稳定对、Orca/Uniswap/Curve/Velodrome 费收不足、dot-006/032 重复等），满足“每轮至少 10 条候选线索”。
- Base RPC 复核再次失败：`mainnet.base.org`、`base-rpc.publicnode.com`、`base.llamarpc.com`、`1rpc.io/base`、`base.drpc.org` 的 `eth_call` 均 15s 超时（2026-10-20 01:30 UTC），muse-801 的 1 bp 费率仍只能靠 GeckoTerminal 池名与 APY 反推，条目中的披露保留。
- 条目 frontmatter 已改为文件首行 `---`（作者行移到 frontmatter 之后），并校验 muse-800/801 的 17 个字段齐全、id 与文件名一致、11 个二级标题、7 条门槛编号齐全、单文件 <1 MB。

## 2026-10-20 02:20 UTC（muse-802）

- 做了什么：新增 muse-802（supplement，improves M-M2-amm-lp），主题为 Base/Aerodrome Slipstream EURC-USDC 低波动 FX LP，2,500 USDC、1% 宽（±0.5%）区间。已先更新 CLAIMS（进行中→已完成待核），再更新 INDEX/LOG 和 `notes/20261020-crypto-mm-screen.md`（新增 12 条复核/淘汰，累计 34 条）。
- muse-802 证据：DefiLlama 459 天（2025-07-10 至 2026-10-20）base APY 均值 23.02%、中位 21.90%，57 个完整 7 日窗口中位 22.57%、p25 18.12%；TVL 中位 $2.23M；EUR/USD 1 年 vol 5.45%、最大回撤 -6.66%。Base RPC 链上读取：`fee()=70`（0.007%）、`tickSpacing()=50`、token0=EURC、token1=USDC、`slot0` tick 1151、`liquidity()=144,494,561,524,372`；池内 858,176.87 EURC + 570,822.29 USDC ≈ $1.533M，与 DefiLlama/GeckoTerminal 一致。
- 关键校正：DefiLlama 当前 `apyBase=40.04%`（总 APY 45.45%）与链上费收不一致。用块 52,793,447→52,836,647 的 `feeGrowthGlobal0/1X128` 增量 × 平均 L 实测，约 24h 费收 142.52 EURC + 154.29 USDC ≈ $314.17；除以 24h 量 $5.16M 得隐含费率 0.609 bp，支持链上 0.7 bp（GeckoTerminal 池名 0.05% 是标签错误）。按该 24h 费收年化，全池费收对总 TVL 仅约 7.5%；40% 不能当成 2,500 美元仓位的收益。
- muse-802 收益模型：按当前 L，0.5% 宽（±0.25%）份额约 0.65%、毛 APY≈29.8%；1% 宽（±0.5%）份额约 0.326%、毛 APY≈14.9%；2% 宽（±1%）份额约 0.163%、毛 APY≈7.5%。采用 1% 宽；扣 IL/再平衡粗算 10–12%，作为与加密趋势低相关的腿 >3%；门槛 5 标“边际”，不硬称 40%。EUR/USD 移动 0.5%/1%/1.5% 时 1% 宽仓位的 IL 约 -0.125%/-0.375%/-0.62%。
- 本轮淘汰/复核：Polymarket Perps 流动性奖励（7d 量 $473.7M，1% maker 份额≈$338k/day，$2,500 需 135x/日，GUIDE 禁止杠杆，扣费后边际/为负）；Holding Rewards（官方无页面）；GRVT（基础返佣 0.1 bp，进阶受 2.5–10% 份额门槛，API/文档不可达）；edgeX（文档 000，无返佣率）；Aevo pre-launch（API 无 pre-launch 类型，标准 perps 正 maker 费）；GMX（2.37–16.49%，多数低或含 token 暴露）；CoW/Bunni（无池数据）；Reya/Ostium（无 LP 池）；HLP 改进（`apr≈3.49%`，低于 8%）；Polymarket US/QCX（美国 KYC，不采用）。
- 风险/边界：没有交易、没有钱包/密钥/账户、没有运行第三方代码；muse-802 没有 tick 级分布/逐仓位 PnL，收益是当前 L/费收的静态估计，不是历史已实现；DefiLlama 的 APY 口径未公开，已用链上费收交叉校验但仍有块窗口/流动性均值误差。GeckoTerminal 的 0.05% 与链上 0.007% 冲突已在条目中披露并解释。
- 本轮计数：累计 3 篇待核（muse-800 new、muse-801 supplement、muse-802 supplement）；muse-802 自评 1–4、6–7 满足，5 边际（1% 宽 14.9% 毛 / 扣成本 10–12% 单独 >8%；2% 宽 7.5% 单独 <8%，作为腿 >3%）。
- 下一轮（如继续）：用 Base RPC 复核 muse-801 的 USDC-USDT 池 `fee()`/`tickSpacing()`（本轮 RPC 已恢复，之前超时）；对 muse-802 做 14 天纸面/实盘费收记录（不交易，仅只读跟踪），重点看 1% 宽区间的出界频率和实际费份额；再找一条真正新的低门槛 maker rebate 或非 CLMM 的流动性机制。

## 2026-10-20 02:45 UTC（muse-801 链上复核后撤回）

- 做了什么：Base RPC 恢复后，用与 muse-802 相同的方法复核 muse-801 的 USDC-USDT 池 `0xa41bc0affba7fd420d186b84899d7ab2ac57fcd1`，发现原稿的费率假设错误，已把 muse-801 从“待核”改为“草稿/已撤回”，并同步更新 CLAIMS、INDEX、screen note（新增 #35）。
- 链上事实：`fee()=8` → 0.0008%（0.08 bp），不是 1 bp；`tickSpacing()=1`；token0=USDC、token1=USDT、`slot0` tick 14（价格约 1.0014149）；`liquidity()=4,574,606,316,213,892`（24h 前 2,937,063,005,834,841）。
- 费收实测：块 52,793,628→52,836,828 的 `feeGrowthGlobal0/1X128` 增量 × 平均 L ≈ 31.66 USDC + 31.64 USDT ≈ **$63.35/day**；除以 24h 量约 $6.55M，隐含费率 0.0966 bp，支持 0.08 bp。DefiLlama `poolMeta=CL1 - 0.0008%` 与链上一致；GeckoTerminal 池名 `USDT / USDC 0.01%` 是标签错误。
- 收益校正：全池费收对 TVL $1.076M 约 **2.15%/年**，不是 19.4%；DefiLlama 19.4% 是 active-liquidity/其他口径。按当前 L，2,500 美元仓位：1 tick（0.01%）宽毛 APY≈9.99%，但 0.005% 移动就出界；5 ticks（0.05%）宽≈2.02%；10 ticks（0.10%）≈1.01%；50 ticks（0.50%）≈0.20%。5 ticks 宽是相对可管理的宽度，但远低于 8%，**门槛 5 不通过**。
- 对 muse-802 的影响：muse-802 已用链上费收校准（EURC/USDC：fee 0.007%、24h 费收 $314、TVL $1.533M、总 TVL 费收约 7.5%；1% 宽仓位毛 APY≈14.9%），与 muse-801 的方法一致，不因本次撤回而改变；但 muse-802 的门槛 5 仍标“边际”，需 14 天实测确认。
- 本轮计数：可提交条目从 3 篇降为 **2 篇**（muse-800 new、muse-802 supplement）；muse-801 作为草稿/反面记录保留，不进入提交清单。
- 方法教训（已写入 screen note）：CLMM 的池级 APY 不能直接当仓位收益；必须用 `feeGrowthGlobal × 自己的 L / 活跃 L` 校准，并用链上 `fee()` 与 `feeGrowth/volume` 双校验；GeckoTerminal 的池名费率标签可能错，DefiLlama 的 `poolMeta` 更接近链上，但仍要读合约。

## 2026-10-20（w02 政治板块筛选：无条目）

- 做了什么：新增 `notes/20261020-politics-screen.md`，记录本轮政治板块的检验与淘汰；muse-100~106 中 100~105 标暂缓，106（Trump 背书初选折价）在 look-ahead 修正后也标暂缓。没有新增/修改 entry。
- Trump 背书：Ballotpedia 2026 表 350 条总背书 / 315 条初选 / 自报 96% 初选成功率；2024 96%、2022 93%、2020 97%、2018 95%。Polymarket 2026 初选市场 127 个，匹配 48 个，初筛 31 个单一背书非 runoff 市场，28 胜 3 负，T-7 均价 0.671、+21.7c/份（1c 价差 + 0.04 fee），t=2.92。
- 关键修正：31 个中 8 个是 Ballotpedia 标 `General` 的大选背书，Truth Social 源帖日期在初选之后（Steve Toth 2026-07-13 vs TX-02 2026-03-03；Casey Askar/Dan Green/Scott Singer/Mike Beltran 2026-09-01 vs FL 2026-08-18；Marsha Blackburn 2026-08-07 vs TN 2026-08-06；Larry Rhoden 2026-08-27 vs SD 2026-06-02；Andy Biggs 行标 General 保守排除），属于 look-ahead，必须剔除。
- 修正后：先剔 8 个 General 背书，剩 23 个（20 胜 3 负；输例 Lindell、Degenfelder、Ogles），T-7 均价 0.751、+10.3c/份，t=1.35；再剔 2 个源帖晚于事件日的（Jerry Carl 2026-06-22 vs AL-01 2026-05-19；Mike Collins 2026-06-15 vs GA Senate 2026-05-19，T-1 价取的是 5/18 首轮前），**有效 21 个（18 胜 3 负）**，T-7 均价 0.793、+5.0c/份，t=0.68；T-1 均价 0.822、+2.1c/份，t=0.37。未达 30 个独立结果，扣成本后不显著；早期 28 个“全胜”还用了 `res>=0.99` 只留赢家，100% 胜率是构造出来的。**不写条目。**
- 民调 vs 市场：Silver Bulletin 2026 民调均值 CSV（7360 行，2026-08-19 至 2026-10-19；22 Senate + 26 Governor）与 Polymarket 75 个 2026 Senate/Governor winner 事件匹配 45 个；竞争性选区市场价与 `Φ(margin/8)` 偏差多在 ±5c，大偏差集中在安全州/排名选择/党派倾斜。7 日变化回归（4388 个重叠观测、39 选区）系数 −0.139、cluster t=−6.19，但按选区聚合 t=0.67，极端 5% 分位下一期仅 +2.2c/−1.3c，扣 2c 成本不成立。**不写。**
- 其他：支持率阶梯卖中间 +3.3c t=0.66（半年不稳定）；Up/Down 趋势 +6.2c t=0.83（26H2 −26.6c）；2026 初选动量 14d +4.7c 但 12d/T−2 为负、8 月驱动；538 官网关停、GitHub 只有 2024-09-12 快照，无州级日度个人民调。
- 风险/边界：所有数字来自实际打开的页面/CSV/API；没有交易、没有钱包/密钥/账户；没有把未复核的实时价格写成条目证据。下一步若要继续，先补 2024/2022 初选有效样本到 ≥30，再重跑；否则政治板块本轮无提交。

## 2026-10-20 04:10 UTC（muse-903 + muse-902 撤回）

- 做了什么：完成 muse-903（improvement，improves dot-005），主题为 Polymarket 与 Kalshi 同一 2026 州级候选人的跨场 maker 价差。已先更新 CLAIMS（进行中→已完成待核）、INDEX、LOG；muse-902 因证据不足撤回。
- 核心改动：`dot-005` 用“跨场等价命题精确互补集”，本版改为“同一候选人的跨场相对价值价差”（Kalshi YES + PM NO）。令 K=Kalshi 判该候选人赢、P=PM 判其赢，支付 = 1+(K−P)：两边一致付 1；Kalshi 赢/PM 输付 2；PM 赢/Kalshi 输付 0。危险方向是后者，不是对称的“共识合约”；不要求结果集穷尽。执行上硬约束 maker-only：同一批 117 个配对里 taker 中位数 −1.52c、仅 6 个为正；maker 毛边中位数 1.00c、20 个 ≥2c、最高 4.00c。
- 实时证据（2026-10-20 04:00 UTC）：Kalshi trade-api v2 + PM Gamma/CLOB，65 场、117 个同名同党配对。示例：NV Governor Ford K 0.55/0.56（bid size 15,098）+ PM NO 0.41（size 10,001）= 0.96，毛边 4.00c；GA Governor Bottoms K bid 0.49 + PM NO bid 0.47 = 0.96，4.00c（Kalshi size 100；PM NO bid size 1,187）；SC Senate Andrews 0.16 + 0.82 = 0.98，2.00c（size 78,469/8,526）；OH Governor Acton 0.70 + 0.27 = 0.97，3.00c（size 497/20,725）。
- 规则对齐：Kalshi `GOVPARTY`/`SENATEPARTY` 的 Payout 以“宣誓就任/提交证书”的政党为准，4/8 媒体源可加速；PM 以 AP+Fox+NBC 三家 call 的 election winner 为准，否则官方 certification。正常流程一致，尾部（赢家未就职且替代者属另一党、参议院拒收证书）可能分歧；危险方向是 PM 判赢/Kalshi 判输（付 0），反方向付 2；这是唯一归零风险，也是价差存在的原因，条目中列为最大风险。
- 费用：Kalshi Elections series `/series` 返回 `fee_type=quadratic`（非 `quadratic_with_maker_fees`），maker 0；taker `ceil(0.07×C×p×(1−p))`。PM Politics `feeSchedule rate=0.04, takerOnly=true, rebateRate=0.25`，maker 0。Kalshi 3.50% APY 对现金和未平仓头寸计息（12am ET 净值、按月），作为 carry 小项。
- 检验计划：2026-10-20 至 2026-11-03 每天扫 60+ 场，join/improve 两种报价，公开成交 tape 判定 fill，单边成交后 taker 对冲记账；主结果 ≥30 个配对；失败阈值：费后净边 <1c、单边对冲中位亏损 >毛边、双边成交率 <20%、任一对规则分歧。
- muse-902 撤回证据：Kalshi Volume Incentive Program 已于 2026-10-13 结束（cryptotimes.io 引 Rule 3.13(f)：3¢–97¢ 合格区间、每张上限 0.5¢）；Kalshi 的 Market Maker/Liquidity Provider 计划要求签 Market Maker Agreement，按反向拍卖分配，$5k 散户不可及。原认领的“LP 挂单奖励 supplement dot-032”不再成立。
- 风险/边界：没有交易、没有钱包/密钥/账户；117 个配对是单一时点快照，不是历史回测；maker fill、queue、legging、markout 都未实测；规则分歧概率未量化；117 个配对共享选举夜风险，不能当 117 次独立下注。条目自评门槛 5 为“边际”，其余满足/前向满足。

## 2026-10-20（政治板块追加复核：ACDC/校准/FLB，无条目）

- 做了什么：新增 `notes/20261020-politics-followup-acdc-calibration-flb.md`，复核三条新线索并更新 INDEX；没有新增/修改 entry，没有新增 CLAIMS。
- ACDC 小额冲击：343 个成交量 $2k–$60k 的 2026 众议院选区市场，data-api 逐笔按交易哈希聚合，单笔 $100–$999 且 YES 跳 ≥10c、前后价 0.10–0.90、间隔 ≤2h 的事件只有 6 个。fade 后 +1h 均值 +6.16c/中位 +4.12c/67% 胜，扣 1c 价差后 -1.42%；+24h 均值 +0.72c/中位 -3.84c/33% 胜，扣费 -18% 到 -22%；+4d 仅 4 个样本。24h/4d 回归不成立；ACDC 的 94% 覆盖大量总成交 <$1k 的市场（76%），在可承载 $500 的市场里合格率仅 6/343，脆弱性 ≠ 可交易容量。
- 校准论文：Nam Anh Le, arXiv:2602.19520，292M trades/327k contracts，政治平均斜率 1.31（Polymarket）/1.64（Kalshi），通用 >1 月斜率 1.32；但二手综述称作者贝叶斯模型显示约一半斜率变化是噪声、样本外 R² 71.5%。用 874 个政治市场买热门方，T-7 的 0.70–0.85 多为负，0.60–0.65 的 +47% 主要来自俄罗斯/特朗普会面/新闻类 stale quote；不能直接成策略。
- FLB 逐笔：68 个 T-7 YES 0.03–0.10 市场，用 T-7 至 T-2 第一笔真实 NO 买盘成交价入场、持有到结算；55 个有成交，5 次亏损，均值 -4.74%、中位 +3.25%、胜率 91%。0.90–0.97 的 NO 子样本 N=28、1 次亏损、+1.82%，但 0.95+ 为 -3.29%，且是事后选带；上一轮日线口径的 +3.91% 不可复现。quantLab 的 KILLED 仍是强反证。
- 关键教训：CLOB `prices-history` 是最后成交/中间价，不是可执行盘口；薄市场的最后成交可能是几小时前的 1 股单。预测市场回测必须用 data-api 逐笔成交价或前向盘口；负偏策略看均值不看胜率。
- 下一步：2026-10-20 至 2026-11-03 前向记录 33 Senate + 435 House 的 CLOB 盘口，筛 YES 0.90–0.97 的竞争性选区，按真实 ask 纸面买 NO，目标 ≥30 个独立选区，预先写死失败线；ACDC 方向只做 ≥$2k 市场并记录 1h/24h/4d 可执行买卖价。数据源可考虑 GitHub `Jon-Becker/prediction-market-analysis`（36GB 逐笔，二手介绍，未下载）。在这些数据出来前不新增 muse-107。
- 风险/边界：没有交易、没有钱包/密钥/账户；所有数字来自实际打开的页面/API/逐笔；`/tmp/opencode/` 下的缓存和脚本不提交。

## 2026-10-20 第 1 轮首批提交（10 待核 + 14 草稿）

- 做了什么：候选池 28 条经全量验证（24 条逐条核源：15 通过 / 8 存疑 / 1 不通过，见 notes/verify-batch-a.md、verify-batch-b.md），按"零硬伤优先、待核名额留 5 个给后半程"的原则精选：10 条以待核提交、14 条以草稿提交占认领，4 条不提交。
- 待核 10 条：muse-700、muse-701、muse-800、muse-900、muse-901、muse-own-polymarket-fed-futures-fomc、muse-own2-rules-dispute-window、muse-own2-tail-sports-midband、muse-own2-whale-cluster-detect、muse-own2-whale-smart-score（提交前已补录来源自带的负面证据：166 个达标钱包全跟 120 天 −1.9%）。
- 不提交 4 条：muse-own-crypto-skew-harvest（验证不通过：期权腿方向与现金流公式自相矛盾，机制已被 muse-701 取代）、muse-802（流动性薄、证据仅静态估计）、muse-own-alt-clv-value（是评估指标非独立策略）、muse-801（链上费收复核不达标，维持撤回）。
- 草稿 14 条的后续：修引用规格与门槛标注（pinnacle、news-sentiment、lp-rewards）、同机制合并（resolution-lag 与 kalshi-settle-lag）、补核验（903、live-surprise-fade），计划 2026-10-23 前分批转待核，待核总数不超过 15。
- 风险/边界：没有交易、没有钱包/密钥/账户；验证中发现的问题均已如实记录，未修饰后提交。

## 2026-10-21 格式修复推送包：新旧文件名对照

- 依据：`repo-docs/guidance-1021/NOTICES.md` 第 4 条（2026-10-25 23:59 UTC 前改格式）。本段只追加，不改上方任何历史行；改名不改先后，首次推送时间仍按旧文件在仓库的记录计算。
- 范围：仓库当前 `bots/muse/entries` 24 条。下表 17 条为“改名+格式”：`id` 改为 `muse-三位编号`，文件名同步改为 `muse-三位数-英文短名.md`。
- 17 条改名对照：

| 旧文件名 | 新文件名 | 新 id |
|---|---|---|
| `muse-own-alt-surebet.md` | `muse-905-alt-surebet.md` | `muse-905` |
| `muse-own-crypto-as-quoting.md` | `muse-906-crypto-as-quoting.md` | `muse-906` |
| `muse-own-polymarket-fed-futures-fomc.md` | `muse-908-polymarket-fed-futures-fomc.md` | `muse-908` |
| `muse-own-polymarket-pinnacle-line-shopping.md` | `muse-909-polymarket-pinnacle-line-shopping.md` | `muse-909` |
| `muse-own-predmarket-kalshi-cpi-nowcast.md` | `muse-910-predmarket-kalshi-cpi-nowcast.md` | `muse-910` |
| `muse-own-xmkt-news-sentiment.md` | `muse-911-xmkt-news-sentiment.md` | `muse-911` |
| `muse-own-xmkt-resolution-lag.md` | `muse-912-xmkt-resolution-lag.md` | `muse-912` |
| `muse-own2-live-goal-lag.md` | `muse-913-live-goal-lag.md` | `muse-913` |
| `muse-own2-live-surprise-fade.md` | `muse-914-live-surprise-fade.md` | `muse-914` |
| `muse-own2-lp-rebate-farm.md` | `muse-915-lp-rebate-farm.md` | `muse-915` |
| `muse-own2-lp-rewards-inventory.md` | `muse-916-lp-rewards-inventory.md` | `muse-916` |
| `muse-own2-rules-dispute-window.md` | `muse-917-rules-dispute-window.md` | `muse-917` |
| `muse-own2-rules-wording-ambiguity.md` | `muse-918-rules-wording-ambiguity.md` | `muse-918` |
| `muse-own2-tail-sports-midband.md` | `muse-919-tail-sports-midband.md` | `muse-919` |
| `muse-own2-tail-weather-expiry-favfade.md` | `muse-920-tail-weather-expiry-favfade.md` | `muse-920` |
| `muse-own2-whale-cluster-detect.md` | `muse-921-whale-cluster-detect.md` | `muse-921` |
| `muse-own2-whale-smart-score.md` | `muse-922-whale-smart-score.md` | `muse-922` |

- 仅改格式、不改名的 5 条（作者行从 `---` 之前移到 frontmatter 之后；903 另修 `pm_category`）：

| 文件名（新旧同名） | 动作 |
|---|---|
| `muse-700-defined-risk-iron-fly.md` | 仅格式：作者行后移 |
| `muse-701-skew-harvest-sign-correction.md` | 仅格式：作者行后移；`improves` 同步为 `muse-907` |
| `muse-900-polymarket-cross-event-logical-arb.md` | 仅格式：作者行后移 |
| `muse-901-negrisk-no-basket-conversion-supplement.md` | 仅格式：作者行后移 |
| `muse-903-pm-kalshi-same-candidate-maker-spread.md` | 仅格式：`pm_category: cross` → `-`，`market` 仍 `prediction_other` |

- 删除 1 条：`muse-own-predmarket-kalshi-settle-lag.md` → 删除（内容已并入 `muse-912-xmkt-resolution-lag.md`；CLAIMS 保留“已合并”历史行）。
- 未改 1 条：`muse-800-polymarket-5m-complete-set-mm.md`（首行已是 `---`，id/文件名合规）。
- 计数：按推送动作计 17 改名+格式 + 5 仅格式（含 903 的 `pm_category` 修正）= 22；另 1 条删除（settle-lag）、1 条不动（800）。操作员按“编号/文件名 + 作者行”字面口径的 22 含 settle-lag、不含 903；本清单把 settle-lag 改为删除、903 计入格式修正，净数同为 22，差额原因见 `notes/push-approval-final-20261021.md`。
- 本对照只记录文件名/id 映射；staging 当前内容相对仓库旧版是否有额外更新，见 `notes/push-approval-final-20261021.md` 0.1 的 `*` 标记（本段不据此改任何条目）。
- 未推送的 staging-only 草稿不在本对照的仓库改名范围内：`muse-own-alt-clv-value` → `muse-904-alt-clv-value`、`muse-own-crypto-skew-harvest` → `muse-907-crypto-skew-harvest`、`muse-own3-nba-live-ml-spread-arb` → `muse-923-nba-live-ml-spread-arb`、`muse-own3-new-listing-quote-vacuum` → `muse-924-new-listing-quote-vacuum`。这 4 条从未推送；801/802/927 也无旧名。其中 `muse-907` 已被 `muse-701` 更正，保留作原条目/反证，本次不推送、不归档删除。是否推送另批决定。

## 2026-10-22 第一批 4 条转待核（912/916/913/903）

- 做了什么：muse-912、muse-916、muse-913、muse-903 由草稿转待核；同步 INDEX（4 行状态）与 CLAIMS（4 行状态）。
- 前置闭合：P-91 边界文本已落盘（912 补段；916/913/903 新增「撞车与边界」节）；913 DOI 出处行改为「摘要（Crossref 元数据）；出版社排版版无法核验」；正式 claims-scan --strict 四条 exit 0、selfcheck FAIL 0（2026-10-22 实跑）。
- 签核与拍板（Muse，2026-10-22 用户授权自行决定）：913 采集时分无真实日志、条目诚实标注「待补」，予以豁免保留待补转待核，不得冒充补录；903 权重按 frontmatter 严格口径记 1.0（market: prediction_other），不改 market。签核记录见 staging notes/transfer-signoff-muse-20261022.md。
- 转待核后待核总数 14；第 5 席无合格递补，不硬凑。
