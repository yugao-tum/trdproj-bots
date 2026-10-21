# 主项目已有的机制（编号、名称和状态）

用户 10-19 同意放进来，10-21 同意加上状态。只放编号、名称和状态，不放结果、数字和规则。用途：查重和选题。交新策略前先在这里搜一遍；和这里的机制相同、只换币或参数的，算变体，最多按补充计分（GUIDE 第 3、6 节）。想把其中某一条做得更好的，交 `kind: improvement`，`improves` 写这里的编号。

状态的意思：
- 运行中：主项目登记为运行中（影子前向或模拟盘），不是实盘。
- 研究中：主项目正在检验。
- 暂缓：主项目暂时放下了，欢迎交改进。
- 已淘汰：主项目的检验没过。可以回头再看，但要交 `kind: improvement`，写清这次改了什么、为什么可能不一样；换个名字原样再交，算重复。
- 想法：主项目还没有检验过。

共 135 条，由操作员从主项目的策略总表导出（2026-10-21）。

| 编号 | 名称 | 状态 |
|---|---|---|
| A-A1-funding-carry | 现货多＋永续空收资金费 | 研究中 |
| A-A2-basis | 现货多＋季度合约空（基差） | 研究中 |
| A-A2-spot-perp-spread | 现货永续瞬时价差 | 已淘汰 |
| A-A3-cex-dex | 中心化所与 DEX 搬砖套利 | 暂缓 |
| A-A3-cross-venue | 跨所同币价差（币安/HL） | 研究中 |
| A-A3-cross-venue-funding | 跨所资金费差 | 已淘汰 |
| A-A3-kimchi | 韩国所泡菜溢价回归 | 暂缓 |
| A-A3-poly-cross-market | 预测市场跨市场定价差 | 已淘汰 |
| A-A4-lst-hedge | 质押币多＋永续空 | 研究中 |
| A-A5-lst-discount | 质押币折价赎回 | 暂缓 |
| A-A5-onchain-mev | 链上 MEV 与清算机器人 | 暂缓 |
| A-A5-poly-complete-set | 预测市场全买套利 | 研究中 |
| A-A5-triangle | 三角汇率套利 | 想法 |
| B-B1-hold | 买入持有（对照） | 研究中 |
| C-C1-hl-copytrade | 跟单 Hyperliquid 高手 | 暂缓 |
| C-C1-whale-net | 大户净持仓变化作方向信号 | 想法 |
| C-C3-hl-vaults | Hyperliquid 用户金库委托 | 想法 |
| E-E1-delist-short | 下架公告后做空 | 已淘汰 |
| E-E1-depeg-buy | 稳定币脱锚抄底 | 想法 |
| E-E1-index-etf-event | 指数纳入与 ETF 获批事件 | 想法 |
| E-E1-listing-chase | 上新公告后立即追涨 | 想法 |
| E-E1-listing-short | 做空新上市币 | 已淘汰 |
| E-E1-macro-window | FOMC/CPI 宏观事件窗口 | 想法 |
| E-E1-monitor-tag-short | 币安监控标签公告后做空 | 想法 |
| E-E1-newperp-funding | 新永续首周资金费（现货对冲） | 想法 |
| E-E1-unlock-short | 代币大额解锁前做空 | 想法 |
| E-E1-upbit-pump-short | Upbit 上新冲高后做空 | 想法 |
| E-E2-cme-gap | CME 周末缺口回补 | 已淘汰 |
| E-E2-funding-settle | 资金费结算前后短线 | 想法 |
| E-E2-holiday | 美国假日窗口（新高过滤） | 想法 |
| E-E2-max-pain | 期权到期最大痛点钉住 | 已淘汰 |
| E-E2-time-of-day | 固定 UTC 时段持有 | 想法 |
| E-E2-turn-of-month | 月末月初持有 | 想法 |
| E-E2-weekend | 周末动量 | 已淘汰 |
| E-E3-btc-leadlag | BTC 领涨山寨补涨 | 已淘汰 |
| F-F1-bab | 押注低贝塔（市场中性） | 已淘汰 |
| F-F1-dbeta | 下行贝塔因子 | 已淘汰 |
| F-F1-lowvol | 低波动币多头 | 已淘汰 |
| F-F2-illiq | 非流动性因子（Amihud） | 已淘汰 |
| F-F3-csf | 截面资金费因子 | 已淘汰 |
| F-F3-oi-lev | 持仓量增速因子 | 已淘汰 |
| F-F3-perp-share | 永续成交占比（做空拥挤） | 已淘汰 |
| F-F3-smart | 大户散户多空分歧 | 已淘汰 |
| F-F4-skew | 偏度因子（彩票币） | 已淘汰 |
| F-F5-multifactor | 动量价值套息多因子 | 想法 |
| M-M1-bollmaker | 布林带双边挂单 | 已淘汰 |
| M-M1-grid | 网格挂单 | 已淘汰 |
| M-M1-orderbook-mm | 盘口双边挂单做市 | 暂缓 |
| M-M2-amm-lp | DEX 集中流动性做市 | 研究中 |
| M-M3-hlp-vault | 存入 HLP 做市金库 | 已淘汰 |
| M-M3-jlp-hedge | JLP 多＋永续空（对冲） | 想法 |
| M-M4-poly-rewards | 预测市场挂单领奖励 | 暂缓 |
| R-R1-bbmr | 布林下轨买入（回中轨） | 已淘汰 |
| R-R1-capitulation | 急跌放量反弹（强平冲击） | 已淘汰 |
| R-R1-dca | 分批加仓摊低成本（DCA） | 想法 |
| R-R1-failed-breakout | 假突破反向 | 已淘汰 |
| R-R1-mvrv | MVRV 估值低位买入高位退出 | 想法 |
| R-R1-nday-low | 10 日新低反弹 | 已淘汰 |
| R-R1-nfi | 多信号超跌买入（NFI X8） | 已淘汰 |
| R-R1-oversold | 多币小时超跌反弹 | 运行中 |
| R-R1-rsi2 | 短周期 RSI 超跌买入（趋势内） | 已淘汰 |
| R-R1-scalp-dip | 分钟级超跌抄底（社区脚本） | 已淘汰 |
| R-R1-squeeze | 5 分钟动量谷底反转 | 已淘汰 |
| R-R1-sweep | 流动性扫单反转 | 已淘汰 |
| R-R1-vwap | VWAP 极端偏离回归 | 已淘汰 |
| R-R1-wick-maker | 插针低处挂限价单接货 | 想法 |
| R-R2-xsrev | 截面反转（买跌最多的币） | 已淘汰 |
| R-R3-ou | 因子残差回归（OU） | 已淘汰 |
| R-R3-pairs | 配对比值回归 | 已淘汰 |
| R-R4-fear-greed | 恐惧贪婪指数反向 | 暂缓 |
| R-R4-funding-extreme | 资金费极端反向 | 已淘汰 |
| R-R4-ls-ratio | 全账户多空比极端反向 | 想法 |
| R-R4-oi-ts | 单币持仓量骤变反向 | 想法 |
| R-R4-rel-funding | 相对资金费反向（对 BTC） | 已淘汰 |
| R-R4-trap | 下跌中多头拥挤做空 | 已淘汰 |
| S-S1-depth-imbalance | 盘口深度失衡跟随 | 想法 |
| S-S1-ml-lit | 机器学习与情绪预测（文献） | 已淘汰 |
| S-S1-orderflow | 订单流信号预测 | 已淘汰 |
| S-S2-er-switch | 效率比切换（趋势/回归） | 已淘汰 |
| S-S2-hmm-regime | HMM 状态识别切换仓位 | 暂缓 |
| S-S2-vr-switch | 方差比切换（趋势/回归） | 已淘汰 |
| S-S3-attention | Wikipedia 关注度变化择时 | 想法 |
| S-S3-etf-flow | 现货 ETF 资金流方向 | 想法 |
| S-S3-exchange-netflow | 交易所净流量择时 | 想法 |
| S-S3-stablecoin-supply | 稳定币供应增长时持有 | 想法 |
| T-T1-attack-breakout | 5 分钟区间突破 | 已淘汰 |
| T-T1-donchian | 单周期唐奇安通道突破 | 已淘汰 |
| T-T1-donchian-e | 多周期通道突破集成（波动目标） | 运行中 |
| T-T1-hawkes | 小时波动扩张（Hawkes） | 已淘汰 |
| T-T1-keltner | 15 分钟肯特纳上穿 | 已淘汰 |
| T-T1-nday-high | 创 10 日新高持有 | 已淘汰 |
| T-T1-range-breakout | 开盘区间突破 | 已淘汰 |
| T-T1-regime-filter | 小时突破放量（状态过滤） | 已淘汰 |
| T-T1-turtle | 多币突破加仓（BTC 开关） | 运行中 |
| T-T1-vcb-mcld | 主流币放量突破（波动聚集开关） | 运行中 |
| T-T1-volume-burst | 1 分钟放量追涨 | 已淘汰 |
| T-T2-alt-bleed | 多 BTC 空山寨（山寨走弱） | 已淘汰 |
| T-T2-cmf | 资金流量指标趋势 | 已淘汰 |
| T-T2-cross-asset | 黄金股指永续趋势（跨资产） | 想法 |
| T-T2-dual-ma | 双均线金叉（趋势过滤） | 已淘汰 |
| T-T2-ema-cross | 价格上穿长期均线 | 已淘汰 |
| T-T2-hash-ribbons | BTC 算力均线回升买入 | 想法 |
| T-T2-ichimoku | 一目均衡云趋势 | 已淘汰 |
| T-T2-intraday-mom | 日内前段动量决定末段持有 | 想法 |
| T-T2-macd | 小时 MACD 金叉（带趋势） | 已淘汰 |
| T-T2-romero-ema | 1 分钟均线多头排列 | 已淘汰 |
| T-T2-rptrend | 趋势风险平价（均线过滤） | 已淘汰 |
| T-T2-smugplug | 3 分钟顺势动量 | 已淘汰 |
| T-T2-supertrend | 3 分钟超级趋势 | 已淘汰 |
| T-T2-tsmom | 时序动量（N 日涨则持有） | 已淘汰 |
| T-T2-vm | 主流币正动量等权（波动管理） | 运行中 |
| T-T3-rotation | 强弱币轮动（ETH/BTC 等） | 已淘汰 |
| T-T3-xsmom | 截面动量（买最强的币） | 已淘汰 |
| V-V1-btc-put-spread | BTC 每周卖看跌价差 | 研究中 |
| V-V1-covered-call | 持仓期卖虚值看涨（备兑） | 想法 |
| V-V1-straddle-dhedge | Delta 对冲卖跨式（做空波动率） | 想法 |
| V-V2-poly-longshot | 预测市场押热门（冷门偏差） | 研究中 |
| V-V3-iv-timed-spread | 隐含波动率择时卖看跌价差 | 想法 |
| X-X1-btc-stable-rebal | BTC/稳定币偏离再平衡 | 想法 |
| X-X1-combo1-k3 | 突破七成＋卖看跌三成（K3） | 研究中 |
| X-X1-combo3 | 趋势子策略合成三号 | 已淘汰 |
| X-X1-cplus | C+ 三腿合成（CB＋NFI） | 已淘汰 |
| X-X1-factory-combo | 工厂一号趋势组合 | 已淘汰 |
| X-X1-nohs1-carry | 突破＋空仓期资金费套利 | 已淘汰 |
| X-X1-nohs1-ens | BTC/ETH 四趋势等权合成 | 已淘汰 |
| X-X2-combo2-vt15 | 五个趋势子策略合成（15% 波动目标） | 运行中 |
| X-X2-pos-vtd | 持仓合成＋日波动目标 | 已淘汰 |
| X-X3-cb | 双机器人：通道突破＋超跌反弹 | 运行中 |
| Y-Y1-pendle-pt | 折价买 Pendle PT 持有到期 | 想法 |
| Y-Y1-stable-lending | 稳定币借贷利息 | 已淘汰 |
| Y-Y2-airdrop-farming | 空投与积分耕作 | 想法 |
| Y-Y2-launchpool | 币安 Launchpool 质押挖新币 | 已淘汰 |
| Y-Y2-lst-hold | 持有流动质押币 | 已淘汰 |
| Y-Y2-susde-hold | 持有收益型稳定币（sUSDe） | 想法 |
| Y-Y3-idle-cash | 空仓资金借出吃利息 | 研究中 |
