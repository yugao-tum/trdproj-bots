---
id: muse-909
name_zh: 体育市场：跟 Pinnacle 盘口比价
name_en: Line-shopping vs sharp books (Pinnacle) on Polymarket sports
bot: muse
date: 2026-10-20
market: polymarket
pm_category: sports
kind: new
improves: -
category: S
return_type: direction
instruments: 体育 moneyline / 让分盘 / 球员道具市场（NBA、NFL、足球）
venues: Polymarket（吃单）
data: Polymarket CLOB / Gamma API（免费免密钥）＋ Pinnacle 官网公开赔率页（免费、无需登录、人工前向记录；公开页只展示当前盘口）。The Odds API 需注册 key，免费层仅 500 credits/月，按红线不采用
test_2w: 用 Pinnacle 官网公开赔率页人工/半自动记录 2 周内 ≥30 场独立比赛（NBA/NFL/英超）的赛前快照；Pinnacle 去水位隐含概率与 Polymarket 中间价差 >4.5pp 记为信号，30–60 分钟后及开赛前再看 PM 中间价是否收敛；失败标准：扣吃单费和半个价差后期望 ≤0，或两周内完成不了 30 场有效快照
status: 草稿
confidence: 中
---

> 作者：Muse 直属 agent（muse-agent-1）｜ 试运行第 1 批

## 一句话

用 Pinnacle（sharp book 之王）的实时赔率算出隐含概率作为公允价，当 Polymarket 体育市场价格偏离超过阈值时吃单买入被低估的一边，持有到价格收敛或赛前平仓。这是单腿方向交易，不是跨博彩公司的无风险 surebet。

## 钱从哪里来

Pinnacle 接受职业投注者的大额下单，其赔率被迫收敛到真实概率，是全行业公认的定价锚；Polymarket 的体育盘口在伤病、 sharp money、盘口异动后经常慢 30–90 秒才跟上，这段滞后里的定价差就是钱。钱来自反应慢的散户对手盘，本质是跨场所价格发现速度差，会持续存在因为两边参与者结构不同。

与跨博彩公司 surebet 的区别：那条要求同一赛事两腿同时可成交且逆赔率和<1，锁定无风险利润（muse-905）；本条只买 Polymarket 一腿，不对冲，赚的是 PM 向 Pinnacle 收敛的方向性价差，可能看错或等不到收敛。若两腿都能成交且 sum(1/odds)<1，应归 surebet 条，不归本条。

## 规则

1. 数据源：Pinnacle 官网公开赔率页（`www.pinnacle.com`，无需登录；页面由 JS 渲染）取 moneyline decimal 赔率，先做去水位归一化再算隐含概率；Polymarket 侧用 CLOB 公共接口取中间价。
2. 信号：sharp_prob − pm_mid > 0.045（4.5 个百分点）时触发。
3. 下单：吃单买入被低估的一边，限价 pm_mid + 0.01，单笔约 40–50 美元（来源做法）。
4. 退出：价格收敛到与 Pinnacle 一致时卖出；或赛前 10 分钟自动撤单/平仓，不持仓过比赛开始。
5. 范围：NBA、NFL moneyline，足球及球员道具；只做盘口深度足够、买卖价差 ≤2¢ 的市场。
6. 结算：按联赛官方赛果结算（NBA/NFL 官网），UMA 争议只做不参与争议的市场。
7. 只做单腿方向交易，不对冲；若同一赛事两腿同时可成交且 sum(1/odds)<1，归 muse-905 的跨博彩公司套利，不归本条。

**市场模板与示例市场（2026-10-20 实查）**：模板是“某场 NBA/NFL/英超比赛的胜负（moneyline）”，同一场可能另有让分、大小分和道具盘，独立结果仍按场次计。示例：
- NBA：https://polymarket.com/event/nba-gsw-lal-2026-10-21 — Warriors vs. Lakers，2026-10-22 02:00 UTC 开赛；主胜负盘买一/卖一 0.34/0.35（价差 1¢），主市场流动性约 $8.7 万（2026-10-20 复核快照，会变；Gamma API）。
- NFL：https://polymarket.com/event/nfl-dal-phi-2026-10-27 — Cowboys vs. Eagles，2026-10-27 00:15 UTC 开赛；买一/卖一 0.66/0.67（价差 1¢），流动性约 $5.9 万（2026-10-20 复核快照，会变）。
- 英超：https://polymarket.com/event/epl-liv-ars-2026-11-01 — Liverpool vs. Arsenal，2026-11-01 16:30 UTC 开赛；主/平/客三档二元市场（slug 后缀 `-liv`/`-draw`/`-ars`），各档价差 1–3¢、每档流动性约 $4.4k（2026-10-20 复核快照，会变）。

月事件量：按 2026-10-20 Gamma API 抽样，NBA 7 天挂出 52 场主胜负盘（≈220 场/月）、NFL 一周 14 场（≈60 场/月）、英超两轮 20 场（≈40–55 场/月），三类合计约 320–335 场/月；这是早先抽样，本次未逐日重数，且不含球员道具和其他足球联赛。独立结果按场次计。

## 证据

- 来源自报、未核实：dev.to 作者称该策略是"最容易且最可靠的边缘"，edge 2–6%/笔，"PM 价格在扣费后还差 4–8% 就是近乎免费的钱"，顶级体育账号/bot 月交易量 $25M+ 在用此法（2026-03-01 发布，2026-06-11 更新）。
- sharpbetsclub 把 Pinnacle 的 no-vig 价称为 ground truth fair odds，并给出 EV = (Pinnacle Fair Probability × 场馆赔率) − 1；同页把 soft-to-sharp latency arbitrage（A）与 +EV/value betting（B）并列，本条对应 B 的单腿方向思路，A 对应 surebet 条（已读；机制说明，未独立核实）。
- 我方粗算（未实测）：阈值 4.5pp；体育吃单费率 0.05，p=0.5 时每份费用 0.05×0.5×0.5=1.25¢，占 50¢ 本金的 2.5%；再扣半个价差约 1–2%，净剩约 0–1pp——偏薄，实际盈利依赖抓到大于阈值的差（如 6–8% 的情形）。

## 数据

- Polymarket CLOB：盘口与价格历史，免费免密钥（`clob.polymarket.com`）；Gamma API 取市场、规则与结算结果。
- Pinnacle 官网公开赔率页：`www.pinnacle.com`，免费、无需登录；2026-10-20 实测具体场次页可打开（HTTP 200）并含该场的道具市场，moneyline/让分由页面数据接口同日确认；赔率由前端 JS 加载，公开页只展示当前盘口，未找到免密钥的历史赔率来源，只能人工/半自动前向记录。
- The Odds API：2026-10-20 定价页实测“Starter FREE 500 credits per month”，需订阅邮箱拿 API key；官方文档按 market×region 计费。按 GUIDE §10 红线不采用；dev.to 代码注释里的“500 calls/day”与官方定价页不符，以官方页为准。
- 结算源：NBA.com、NFL.com、Soccerway 等联赛官方赛果，免费。

## 两周内怎么检验

NBA（10 月下旬开赛）、NFL（赛季中）、英超常年有比赛，2 周内独立比赛场次 >100 场。检验方案（不依赖 The Odds API key）：每个比赛日挑 3–5 场主流比赛，在开赛前 30–60 分钟人工打开 Pinnacle 官网公开赔率页，记录 moneyline decimal 赔率并去水位；同时用 Polymarket CLOB 公共接口记录同一场的中间价。差值 >4.5pp 记为信号，30–60 分钟后及开赛前各再看一次 PM 中间价；按吃单费公式与半个价差扣成本后算每信号期望收益。

可行性边界：Pinnacle 官网免登录可看，但页面是 JS 渲染、只展示当前盘口，没有可用的历史赔率，只能前向记录；人工核对每天约 10–20 场（按人工可执行量假设），做不到 30–90 秒级轮询。因此本检验只能验证“赛前数十分钟内 PM 是否向 Pinnacle 收敛”这一粗粒度版本，不能验证原文的 30–90 秒抢跑窗口；若要 30 秒级信号，需要付费或需 key 的实时源（触红线）或未文档化的页面接口（不稳定），均不作为本条的检验前提。失败标准：≥30 个独立场次的有效快照下，扣成本后期望 ≤0；或两周内完成不了 30 场有效记录（数据采集不可行）。

## 成本与容量

- 成本：体育板块吃单费率 0.05，费用 = 份数 × 0.05 × p × (1−p)；另有半个买卖价差约 0.5–1.5¢。挂单不收费但本策略吃单为主。
- 容量：单笔 40–50 美元（来源做法）；5000 USDT 可分散到 20–50 个不相关场次（每场 40–50 美元，占用约 800–2500 USDT，其余留作缓冲）；单场所 2500 USDT 上限内。NBA/NFL/英超主胜负盘约 320–335 场/月（见上），吃单深度在主流盘通常够几百美元。
- 资金占用：单笔持有分钟到小时级，资金周转快。

## 风险

- Pinnacle 赔率本身含水位（sharpbetsclub 的示例为 2.56%），直接取倒数会系统性高估概率，需先做去水位处理（归一化），否则信号有偏。
- 盘口对应错：Pinnacle 官网赛事与 Polymarket 市场靠队名/开赛时间匹配，错配会吃到错误信号。
- 比赛开始前 PM 常暂停交易或价差拉大，退出不及会被迫持有到结算。
- 体育板块个别市场流动性差，吃单滑点吃掉边缘。
- 伤病消息的"首发"优势衰减快：越来越多 bot 做同样的事，30–90 秒窗口在变窄（来源自己也承认市场在变有效）。
- 检验数据靠人工前向记录，漏记、时间戳不准和样本选择会带来偏差；且只能做粗粒度收敛检验，无法验证 30–90 秒窗口。

## 改进了什么

不适用。

## 门槛自查

1. 机制说得清：满足。Pinnacle 作为 sharp 定价锚、PM 跟随滞后，付钱的是反应慢的对手盘。
2. 有免费数据能检验：不确定（对原 30–90 秒信号不满足）。PM CLOB/Gamma 免费免密钥；Pinnacle 官网公开页免费、无需登录，但公开页只展示当前盘口、未找到免密钥的历史赔率，只能人工/半自动前向记录，支撑不了 30 秒级轮询。The Odds API 免费层仅 500 credits/月且需注册 key，按红线不采用。
3. 小资金能做：满足。单笔 40–50 美元，5000 USDT 可分散多场。
4. 不重复：满足（与 surebet 条的边界已切开）。与 muse-905 的区别：那条是同一赛事两腿对冲、锁定 sum(1/odds)<1 的无风险价差（category A、return_type convergence），场所是博彩公司/交易所，Pinnacle 只是可选对冲腿；本条是 Polymarket 单腿、无对冲、以 Pinnacle no-vig 为公允价的方向性收敛交易（category S、return_type direction）。共同前提是“sharp 锚 + 慢场所”，但关键变量（单场所偏离幅度 vs 两腿逆赔率和）和损益结构（有方向风险 vs 无风险锁定）不同。若只找到 PM 一腿偏离，归本条；若两腿同时可成交且 sum(1/odds)<1，归 surebet。与 known/ 的 A-A3-poly-cross-market（跨市场定价差，泛指）不同关键变量：本条以 Pinnacle 外部赔率为唯一公允锚；与 dot-013（NBA 伤病消息时滞）不同：那条的关键变量是伤病新闻到达时间，本条是系统性的盘口比价（含 sharp money 与模型调盘，不限于伤病事件）。
5. 扣成本后粗算够用：不确定。来源自报净 2–6%/笔；我方按 4.5% 阈值粗算净剩约 0–1pp，偏薄，依赖抓到 6%+ 的大差。标为不确定，待检验。
6. 两周内能检验：不确定。2 周内 NBA/NFL/英超独立场次 >100，凑 30 场快照数量上可行；但人工/公开页只能做赛前 30–60 分钟和开赛前的粗粒度记录，验证不了原文的 30–90 秒滞后。只有把命题降级为“赛前 PM 是否向 Pinnacle 收敛”才可检验。
7. 出处可查：满足。dev.to 原文已读；sharpbetsclub 的 A/B 策略区分已读；费用公式见 GUIDE §8 与 martysmargin（摘要）；The Odds API 定价页已核对（500 credits/月、需注册 key）；示例市场和月事件量均于 2026-10-20 用 Polymarket 页面/Gamma API 核对。

## 出处

- https://dev.to/benjamin_martin_749c1d57f/polymarket-trading-bot-sports-market-df9 — 访问 2026-10-20 — 已读（策略 1 Line-Shopping vs Sharp Books：滞后 30–90 秒、阈值 4.5%、edge 2–6%/笔、NBA/NFL/足球；代码注释称 free tier 500 calls/day，与官方定价页不符）
- https://sharpbetsclub.substack.com/p/sharp-vs-soft-sportsbooks-the-microstructure — 访问 2026-10-20 — 已读（A. Soft-to-Sharp Latency Arbitrage：Pinnacle 领先、软庄滞后、sum(1/odds)<1；B. Positive Expected Value：Pinnacle no-vig 作为公允价、EV 公式；本条取 B 的单腿方向思路，A 归 surebet 条）
- https://www.martysmargin.com/ — 访问 2026-10-20 — 摘要（吃单费 = 系数 × p × (1−p)，体育系数 0.05；挂单不收费）
- https://the-odds-api.com/#get-access — 访问 2026-10-20 — 已读（Starter FREE 500 credits per month；订阅后邮件收 API key）
- https://the-odds-api.com/liveapi/guides/v4/ — 访问 2026-10-20 — 已读（Usage Quota Costs：1 per region per market）
- https://www.pinnacle.com/en/basketball/nba/portland-trail-blazers-vs-phoenix-suns/1637438612/ — 访问 2026-10-20 — 已读（无需登录；具体场次页可打开，道具市场可见，moneyline/让分由页面数据接口同日确认；未找到公开历史赔率）
- https://guest.api.arcadia.pinnacle.com/0.1/matchups/1637443985/markets/related/straight — 访问 2026-10-20 — 已读（未文档化 guest JSON；Lakers–Warriors 当前 moneyline −203/+176；接口可能变更，不作为检验前提）
- https://polymarket.com/event/nba-gsw-lal-2026-10-21 — 访问 2026-10-20 — 已读（Gamma API 同日核对 outcomes/prices/bestBid/bestAsk/liquidity/gameStart）
- https://polymarket.com/event/nfl-dal-phi-2026-10-27 — 访问 2026-10-20 — 已读（同上）
- https://polymarket.com/event/epl-liv-ars-2026-11-01 — 访问 2026-10-20 — 已读（同上；三个子市场 slug 后缀 -liv/-draw/-ars）
- https://gamma-api.polymarket.com/events?limit=100&active=true&closed=false&tag_slug=nba — 访问 2026-10-20 — 已读（分页抽样：7 天 52 场 NBA 主胜负盘；NFL/EPL 同法）
