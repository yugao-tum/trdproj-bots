> 作者：Muse 直属 agent（muse-agent-1）｜ 试运行第 1 批

---
id: muse-own-polymarket-pinnacle-line-shopping
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
data: Polymarket CLOB（免费免密钥）＋ The Odds API（免费层 500 次/天，需注册拿 key）或 Pinnacle 官网公开赔率
test_2w: 记录每次 Pinnacle 隐含概率与 Polymarket 中间价差 >4.5% 的信号，跟踪 30 分钟内 PM 价格是否向 Pinnacle 收敛；2 周内 ≥30 场独立比赛；失败标准：扣吃单费和半个价差后期望为负
status: 草稿
confidence: 中
---

## 一句话

用 Pinnacle（sharp book 之王）的实时赔率算出隐含概率作为公允价，当 Polymarket 体育市场价格偏离超过阈值时吃单买入被低估的一边，持有到价格收敛或赛前平仓。

## 钱从哪里来

Pinnacle 接受职业投注者的大额下单，其赔率被迫收敛到真实概率，是全行业公认的定价锚；Polymarket 的体育盘口在伤病、 sharp money、盘口异动后经常慢 30–90 秒才跟上，这段滞后里的定价差就是钱。钱来自反应慢的散户对手盘，本质是跨场所价格发现速度差，会持续存在因为两边参与者结构不同。

## 规则

1. 数据源：The Odds API 取 Pinnacle 的 decimal 赔率（`bookmakers=pinnacle, markets=h2h, oddsFormat=decimal`），隐含概率 = 1 / decimal 赔率；Polymarket 侧用 CLOB 取中间价。
2. 信号：sharp_prob − pm_mid > 0.045（4.5 个百分点）时触发。
3. 下单：吃单买入被低估的一边，限价 pm_mid + 0.01，单笔约 40–50 美元（来源做法）。
4. 退出：价格收敛到与 Pinnacle 一致时卖出；或赛前 10 分钟自动撤单/平仓，不持仓过比赛开始。
5. 范围：NBA、NFL moneyline，足球及球员道具；只做盘口深度足够、买卖价差 ≤2¢ 的市场。
6. 结算：按联赛官方赛果结算（NBA/NFL 官网），UMA 争议只做不参与争议的市场。

## 证据

- 来源自报、未核实：dev.to 作者称该策略是"最容易且最可靠的边缘"，edge 2–6%/笔，"PM 价格在扣费后还差 4–8% 就是近乎免费的钱"，顶级体育账号/bot 月交易量 $25M+ 在用此法（2026-03-01 发布，2026-06-11 更新）。
- 来源自报、未核实：Medium 上自称 Polymarket whale 的对冲基金拆解称"体育博彩共识从 55% 变到 62% 而 Polymarket 还停在 54% 时，这 8% 的差可以交易"。
- 我方粗算（未实测）：阈值 4.5pp；体育吃单费率 0.05，p=0.5 时每份费用 0.05×0.5×0.5=1.25¢，占 50¢ 本金的 2.5%；再扣半个价差约 1–2%，净剩约 0–1pp——偏薄，实际盈利依赖抓到大于阈值的差（如 6–8% 的情形）。

## 数据

- Polymarket CLOB：盘口与价格历史，免费免密钥（`clob.polymarket.com`）。
- The Odds API：Pinnacle 实时赔率，免费层 500 次/天（需注册，对应 2026 年 30 秒轮询约可用 16 小时/天；按需可放宽轮询）。
- Pinnacle 官网公开赔率页面：免费免密钥，可人工核对。
- 结算源：NBA.com、NFL.com、Soccerway 等联赛官方赛果，免费。

## 两周内怎么检验

NBA（10 月下旬开赛）、NFL（赛季中）、足球常年有比赛，2 周内独立比赛场次 >100 场。检验：用程序记录每次触发信号（差值 >4.5%）时的 Pinnacle 隐含概率、PM 中间价、吃单价；跟踪信号后 30 分钟 PM 价格变动方向与幅度；按吃单费公式与半个价差扣成本后算每信号期望收益。失败标准：≥30 个信号样本下，扣成本后期望 ≤0，或信号出现频率 <1 次/天（机会不足）。

## 成本与容量

- 成本：体育板块吃单费率 0.05，费用 = 份数 × 0.05 × p × (1−p)；另有半个买卖价差约 0.5–1.5¢。挂单不收费但本策略吃单为主。
- 容量：单笔 40–50 美元（来源做法）；5000 USDT 可同时跑 20–50 个不相关场次；单场所 2500 USDT 上限内。NBA/NFL/足球每月数百场机会，吃单深度在主流盘通常够几百美元。
- 资金占用：单笔持有分钟到小时级，资金周转快。

## 风险

- Pinnacle 赔率本身含水位（margin约 2–4%），直接取倒数会系统性高估概率，需先做去水位处理（归一化），否则信号有偏。
- 盘口对应错：The Odds API 的 event 与 Polymarket 市场靠队名匹配，错配会吃到错误信号。
- 比赛开始前 PM 常暂停交易或价差拉大，退出不及会被迫持有到结算。
- 体育板块个别市场流动性差，吃单滑点吃掉边缘。
- 伤病消息的"首发"优势衰减快：越来越多 bot 做同样的事，30–90 秒窗口在变窄（来源自己也承认市场在变有效）。

## 改进了什么

不适用。

## 门槛自查

1. 机制说得清：满足。Pinnacle 作为 sharp 定价锚、PM 跟随滞后，付钱的是反应慢的对手盘。
2. 有免费数据能检验：满足。PM CLOB 免费免密钥；The Odds API 免费层需注册（500 次/天），Pinnacle 官网可免密钥人工核对。
3. 小资金能做：满足。单笔 40–50 美元，5000 USDT 可分散多场。
4. 不重复：满足。与 known/ 的 A-A3-poly-cross-market（跨市场定价差，泛指）不同关键变量：本条以 Pinnacle 外部赔率为唯一公允锚；与 dot-013（NBA 伤病消息时滞）不同：那条的关键变量是伤病新闻到达时间，本条是系统性的盘口比价（含 sharp money 与模型调盘，不限于伤病事件）。
5. 扣成本后粗算够用：不确定。来源自报净 2–6%/笔；我方按 4.5% 阈值粗算净剩约 0–1pp，偏薄，依赖抓到 6%+ 的大差。标为不确定，待检验。
6. 两周内能检验：满足。2 周内独立比赛 >30 场，检验方案上文已给。
7. 出处可查：满足。dev.to 原文已读；费用公式见 GUIDE §8 与 martysmargin（摘要）。

## 出处

- https://dev.to/benjamin_martin_749c1d57f/polymarket-trading-bot-sports-market-df9 — 访问 2026-10-20 — 已读（策略 1 Line-Shopping vs Sharp Books：滞后 30–90 秒、阈值 4.5%、edge 2–6%/笔、NBA/NFL/足球）
- https://medium.com/@davidvincent2010/inside-a-prediction-market-hedge-fund-complete-breakdown-067f9f056f14 — 访问 2026-10-20 — 摘要（体育博彩共识 55%→62% 而 PM 停在 54% 时 8% 差可交易）
- https://www.martysmargin.com/ — 访问 2026-10-20 — 摘要（吃单费 = 系数 × p × (1−p)，体育系数 0.05；挂单不收费）
