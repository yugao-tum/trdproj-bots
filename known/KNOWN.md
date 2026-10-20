# 主项目已有的机制（只有名称）

用户 10-19 同意放进来，只放名称，不放结果和规则。用途：查重。交新策略前先在这里搜一遍；和这里的机制相同、只换币或参数的，算变体，最多按补充计分（GUIDE 第 3、6 节）。想把其中某一条做得更好的，交 `kind: improvement`，`improves` 写这里的编号。

共 135 条，由操作员从主项目的策略总表导出（2026-10-20）。

| 编号 | 名称 |
|---|---|
| A-A1-funding-carry | 现货多＋永续空收资金费 |
| A-A2-basis | 现货多＋季度合约空（基差） |
| A-A2-spot-perp-spread | 现货永续瞬时价差 |
| A-A3-cex-dex | 中心化所与 DEX 搬砖套利 |
| A-A3-cross-venue | 跨所同币价差（币安/HL） |
| A-A3-cross-venue-funding | 跨所资金费差 |
| A-A3-kimchi | 韩国所泡菜溢价回归 |
| A-A3-poly-cross-market | 预测市场跨市场定价差 |
| A-A4-lst-hedge | 质押币多＋永续空 |
| A-A5-lst-discount | 质押币折价赎回 |
| A-A5-onchain-mev | 链上 MEV 与清算机器人 |
| A-A5-poly-complete-set | 预测市场全买套利 |
| A-A5-triangle | 三角汇率套利 |
| B-B1-hold | 买入持有（对照） |
| C-C1-hl-copytrade | 跟单 Hyperliquid 高手 |
| C-C1-whale-net | 大户净持仓变化作方向信号 |
| C-C3-hl-vaults | Hyperliquid 用户金库委托 |
| E-E1-delist-short | 下架公告后做空 |
| E-E1-depeg-buy | 稳定币脱锚抄底 |
| E-E1-index-etf-event | 指数纳入与 ETF 获批事件 |
| E-E1-listing-chase | 上新公告后立即追涨 |
| E-E1-listing-short | 做空新上市币 |
| E-E1-macro-window | FOMC/CPI 宏观事件窗口 |
| E-E1-monitor-tag-short | 币安监控标签公告后做空 |
| E-E1-newperp-funding | 新永续首周资金费（现货对冲） |
| E-E1-unlock-short | 代币大额解锁前做空 |
| E-E1-upbit-pump-short | Upbit 上新冲高后做空 |
| E-E2-cme-gap | CME 周末缺口回补 |
| E-E2-funding-settle | 资金费结算前后短线 |
| E-E2-holiday | 美国假日窗口（新高过滤） |
| E-E2-max-pain | 期权到期最大痛点钉住 |
| E-E2-time-of-day | 固定 UTC 时段持有 |
| E-E2-turn-of-month | 月末月初持有 |
| E-E2-weekend | 周末动量 |
| E-E3-btc-leadlag | BTC 领涨山寨补涨 |
| F-F1-bab | 押注低贝塔（市场中性） |
| F-F1-dbeta | 下行贝塔因子 |
| F-F1-lowvol | 低波动币多头 |
| F-F2-illiq | 非流动性因子（Amihud） |
| F-F3-csf | 截面资金费因子 |
| F-F3-oi-lev | 持仓量增速因子 |
| F-F3-perp-share | 永续成交占比（做空拥挤） |
| F-F3-smart | 大户散户多空分歧 |
| F-F4-skew | 偏度因子（彩票币） |
| F-F5-multifactor | 动量价值套息多因子 |
| M-M1-bollmaker | 布林带双边挂单 |
| M-M1-grid | 网格挂单 |
| M-M1-orderbook-mm | 盘口双边挂单做市 |
| M-M2-amm-lp | DEX 集中流动性做市 |
| M-M3-hlp-vault | 存入 HLP 做市金库 |
| M-M3-jlp-hedge | JLP 多＋永续空（对冲） |
| M-M4-poly-rewards | 预测市场挂单领奖励 |
| R-R1-bbmr | 布林下轨买入（回中轨） |
| R-R1-capitulation | 急跌放量反弹（强平冲击） |
| R-R1-dca | 分批加仓摊低成本（DCA） |
| R-R1-failed-breakout | 假突破反向 |
| R-R1-mvrv | MVRV 估值低位买入高位退出 |
| R-R1-nday-low | 10 日新低反弹 |
| R-R1-nfi | 多信号超跌买入（NFI X8） |
| R-R1-oversold | 多币小时超跌反弹 |
| R-R1-rsi2 | 短周期 RSI 超跌买入（趋势内） |
| R-R1-scalp-dip | 分钟级超跌抄底（社区脚本） |
| R-R1-squeeze | 5 分钟动量谷底反转 |
| R-R1-sweep | 流动性扫单反转 |
| R-R1-vwap | VWAP 极端偏离回归 |
| R-R1-wick-maker | 插针低处挂限价单接货 |
| R-R2-xsrev | 截面反转（买跌最多的币） |
| R-R3-ou | 因子残差回归（OU） |
| R-R3-pairs | 配对比值回归 |
| R-R4-fear-greed | 恐惧贪婪指数反向 |
| R-R4-funding-extreme | 资金费极端反向 |
| R-R4-ls-ratio | 全账户多空比极端反向 |
| R-R4-oi-ts | 单币持仓量骤变反向 |
| R-R4-rel-funding | 相对资金费反向（对 BTC） |
| R-R4-trap | 下跌中多头拥挤做空 |
| S-S1-depth-imbalance | 盘口深度失衡跟随 |
| S-S1-ml-lit | 机器学习与情绪预测（文献） |
| S-S1-orderflow | 订单流信号预测 |
| S-S2-er-switch | 效率比切换（趋势/回归） |
| S-S2-hmm-regime | HMM 状态识别切换仓位 |
| S-S2-vr-switch | 方差比切换（趋势/回归） |
| S-S3-attention | Wikipedia 关注度变化择时 |
| S-S3-etf-flow | 现货 ETF 资金流方向 |
| S-S3-exchange-netflow | 交易所净流量择时 |
| S-S3-stablecoin-supply | 稳定币供应增长时持有 |
| T-T1-attack-breakout | 5 分钟区间突破 |
| T-T1-donchian | 单周期唐奇安通道突破 |
| T-T1-donchian-e | 多周期通道突破集成（波动目标） |
| T-T1-hawkes | 小时波动扩张（Hawkes） |
| T-T1-keltner | 15 分钟肯特纳上穿 |
| T-T1-nday-high | 创 10 日新高持有 |
| T-T1-range-breakout | 开盘区间突破 |
| T-T1-regime-filter | 小时突破放量（状态过滤） |
| T-T1-turtle | 多币突破加仓（BTC 开关） |
| T-T1-vcb-mcld | 主流币放量突破（波动聚集开关） |
| T-T1-volume-burst | 1 分钟放量追涨 |
| T-T2-alt-bleed | 多 BTC 空山寨（山寨走弱） |
| T-T2-cmf | 资金流量指标趋势 |
| T-T2-cross-asset | 黄金股指永续趋势（跨资产） |
| T-T2-dual-ma | 双均线金叉（趋势过滤） |
| T-T2-ema-cross | 价格上穿长期均线 |
| T-T2-hash-ribbons | BTC 算力均线回升买入 |
| T-T2-ichimoku | 一目均衡云趋势 |
| T-T2-intraday-mom | 日内前段动量决定末段持有 |
| T-T2-macd | 小时 MACD 金叉（带趋势） |
| T-T2-romero-ema | 1 分钟均线多头排列 |
| T-T2-rptrend | 趋势风险平价（均线过滤） |
| T-T2-smugplug | 3 分钟顺势动量 |
| T-T2-supertrend | 3 分钟超级趋势 |
| T-T2-tsmom | 时序动量（N 日涨则持有） |
| T-T2-vm | 主流币正动量等权（波动管理） |
| T-T3-rotation | 强弱币轮动（ETH/BTC 等） |
| T-T3-xsmom | 截面动量（买最强的币） |
| V-V1-btc-put-spread | BTC 每周卖看跌价差 |
| V-V1-covered-call | 持仓期卖虚值看涨（备兑） |
| V-V1-straddle-dhedge | Delta 对冲卖跨式（做空波动率） |
| V-V2-poly-longshot | 预测市场押热门（冷门偏差） |
| V-V3-iv-timed-spread | 隐含波动率择时卖看跌价差 |
| X-X1-btc-stable-rebal | BTC/稳定币偏离再平衡 |
| X-X1-combo1-k3 | 突破七成＋卖看跌三成（K3） |
| X-X1-combo3 | 趋势子策略合成三号 |
| X-X1-cplus | C+ 三腿合成（CB＋NFI） |
| X-X1-factory-combo | 工厂一号趋势组合 |
| X-X1-nohs1-carry | 突破＋空仓期资金费套利 |
| X-X1-nohs1-ens | BTC/ETH 四趋势等权合成 |
| X-X2-combo2-vt15 | 五个趋势子策略合成（15% 波动目标） |
| X-X2-pos-vtd | 持仓合成＋日波动目标 |
| X-X3-cb | 双机器人：通道突破＋超跌反弹 |
| Y-Y1-pendle-pt | 折价买 Pendle PT 持有到期 |
| Y-Y1-stable-lending | 稳定币借贷利息 |
| Y-Y2-airdrop-farming | 空投与积分耕作 |
| Y-Y2-launchpool | 币安 Launchpool 质押挖新币 |
| Y-Y2-lst-hold | 持有流动质押币 |
| Y-Y2-susde-hold | 持有收益型稳定币（sUSDe） |
| Y-Y3-idle-cash | 空仓资金借出吃利息 |
