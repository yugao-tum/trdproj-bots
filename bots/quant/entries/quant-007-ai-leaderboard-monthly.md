---
id: quant-007
name_zh: 月度AI榜首市场：按榜单排名定价
name_en: Polymarket "Best AI Company" monthly (arena.ai Text Arena rank)
bot: quant
date: 2026-10-20
market: polymarket
pm_category: tech
kind: new
improves: -
category: S
return_type: direction
instruments: negRisk 多臂月度组「某公司是否在月末检查时为 arena.ai Text Arena (Overall) 第 1 名」（每公司一臂 Yes/No）
venues: Polymarket
data: Gamma events/markets 与 CLOB book 免费免密钥（本轮已取）；结算源 arena.ai 页面 curl 返回 403，历史快照仅 Wayback CDX 索引可取、内容两次抓取失败，故榜单历史值本轮未取得
test_2w: 独立结果按 event 计（一月一 event、一 event 只一个结算快照，禁按臂计数）；历史自 2024-12 起仅 22 个已结算 event，两周内只新增 1 个（2026-10-31 12:00 ET），故凑不到 30 个，只能记 forward；失败标准：净 PnL 中位 ≤0
status: 待核
confidence: 中
---

整理说明：本稿只由本轮实际抓取的 Gamma/CLOB 响应与规则原文写成。**核心输入（榜单当前 Rank/分数/置信区间）本轮没有取到**：`arena.ai` 与其 `/api/` 路径对 curl 返回 403，`web.archive.org` 对该页的内容抓取两次返回 HTTP 000（只有 CDX 索引成功）。因此下文所有"榜单状态"一律标 未查到，不写任何模型分数、名次或差距。

## 一句话

在 Polymarket 每月一次的「哪家公司拥有最好的 AI 模型」negRisk 组里，用结算源（arena.ai Text Arena Overall，style control 关）当下公开的第一名与第二名分差，去比市场的吃单价：当"当前第一名所属公司"的买价低于榜单黏性所隐含的概率时买它，当追赶者买价明显高于一个月内翻盘所需时卖它；持有到月末检查时点，或提前在价差收敛时平掉。**本轮没有取到榜单数据，所以这条目前只是可检验的定价框架，不是已验证的边。**

## 钱从哪里来

付款方是把"谁最强"当叙事出价的对手方，而结算只看**某一瞬间**的榜单列。规则原文（见下）规定结算取 2026-10-31 12:00 PM ET 那一刻的 Rank 列，不是月度平均、也不是"曾经第一"。榜单前列在几周内通常变化有限，而市场叙事（新模型发布、发布传闻）会把近月的臂推得比"到那一刻仍第一"的实际概率更高或更低，价差就是这个偏差。这条钱的持续性依赖两点，**都未核实**：(a) 榜首在 2–6 周窗口内的黏性显著高于市场定价；(b) 榜单页本身公开可读，信息差不该存在，所以偏差只能来自纪律/注意力而非信息。若 (a) 不成立，本条无收益。与 dot-032（做市奖励）不同，付款方不是平台预算，是对手方。

## 规则

以下为 2026 年 10 月这一版的规则原文要点（Gamma `events?slug=which-company-has-the-best-ai-model-end-of-october`，event id `841230`）：

- 结算时点：`when the table under the "Leaderboard" tab is checked on October 31, 2026, 12:00 PM ET`（`endDate` 字段 `2026-10-31T16:00:00Z`；`startDate` `2026-08-13T00:02:19Z`）。
- 结算数据源原文：`Results from the "Rank" column under the "Text Arena | Overall" Leaderboard tab at https://arena.ai/leaderboard/text/overall-no-style-control with style control off (Adjustments: None) and filtered for "Models"`。**style control = 关（Adjustments: None）**，这是关键口径：开 style control 的榜单排名不同。
- 主键是 **Rank 列**，不是分数：`Models will be ordered primarily by their leaderboard rank at the market's check time`。
- 平手规则（两级）：先按 `Arena score, including any underlying, unrounded, granular values`，仍平则按公司名字母序，原文举例 `"Google" would be ranked ahead of "SpaceXAI"`。推论（我的算术/推断，非原文）：字母序把 Anthropic 排在 Google、Meta、OpenAI 之前，所以"分数完全相同"时 Anthropic 占优；但原文先用未取整的 granular 分数，精确同分极罕见，此项多数时候不影响结算。
- 排除项：`Models marked "AutoEval" ... will not be considered, regardless of whether they display a rank or score`。→ 读榜时必须剔除 AutoEval 行，否则会把一个不计入的模型当第一名。
- 缺数据规则：源在检查时不可用则**保持开放**，等恢复后按第一次可得检查结算；永久不可用则结算为 `"Other"`（2025 年那版写的是"按另一个结算源"，措辞不同，见下）。

**规则随时间改过（本条的重要风险，也是可定价的口径差）**：
- 2024-12 那期 `top-ai-model-on-december-31`（`endDate` `2024-12-31T12:00:00Z`）的 description 全文只有 101 字符：`This is a negrisk market group over which will be the top AI model on December 31, 2024, 12:00 PM ET.` —— **没有写结算源，也没写 style control 或平手规则**。
- 2025-09 那期 `which-company-has-best-ai-model-end-of-september`（`endDate` `2025-09-30T00:00:00Z`）用的是 `the highest arena score based off the Chatbot Arena LLM Leaderboard (https://lmarena.ai/)`，`style control off`，平手直接按公司名字母序。
- 2026-09/10/11 那几期改成 `arena.ai` + **Rank 列优先**。
→ 含义：跨期回测不能把 2024–2025 的"最高 Arena Score"结果直接当今天的"Rank 列第一"用；用分数差建模时必须对上当期规则。

**市场结构与臂**：`negRisk=true`、`enableOrderBook=true`、`restricted=true`；2026-10 这期 **32 个市场（臂）**：21 个具名公司（Anthropic、Meta、Google、Alibaba、Moonshot、OpenAI、Baidu、Z.ai、Xiaomi、SpaceXAI、DeepSeek、Amazon、ByteDance、Nvidia、Thinky、MiniMax、Mistral、Meituan、Tencent、StepFun、Microsoft）+ 10 个占位臂 `Company A–I,K` + `Other`。**占位臂与 Other 在 2026-10-20 快照里 `bid=0 / ask=1 / spread=1`、volume=0**，即不是可交易价格，"0.5"只是默认值。2026-11 那期 35 臂，占位到 `Company M`。

**进场/出场/仓位（本版，写死）**：
- 只在检查时点前 7–21 天进场；只买具名臂的 Yes（不裸卖、不做空占位臂）。
- 信号：设榜单 Top1 公司为 L、Top2 公司为 C。若 L 的 ask ≤ 0.85 且（我给出的）P̂(L 到检查时仍第一) − (ask_L + 费 + 半价差) ≥ +2pp，则买 L；若 C 的 ask ≥ P̂(C 翻盘) + 费 + 半价差 + 2pp，则买 C 的 No（等价于押 L）。P̂ 的计算方式必须先固定（例如"以分差/名次差为主的单调映射 + 历史翻盘基率"），**本轮没有榜单数据，P̂ 未校准，不写具体公式参数**。
- 单臂 ≤ 500 份，整组占用 ≤ 1,500 USDT（单场所 ≤ 2,500 USDT、总资金 5,000 USDT）。
- 出场：检查时点后按结算价退出（0 或 1），或在距检查 ≤3 天时若价格已收敛到 (ask+0.01) 以上则提前平掉。
- 风控：一次只做一臂（不做"买一篮子"当无风险），因为占位臂/Other 没有可成交报价，named 臂合计 0.9955 < 1 **不构成套利**（GUIDE 第 8 节"多选项没列全时，各项价格之和小于 1 是正常的"）。

## 证据

**本轮已核（Gamma/CLOB 原始字段，非来源自报）**，快照时间以 `updatedAt=2026-10-20T04:00:58Z` 为准，抓取时间 2026-10-20：

| 项 | 2026-10 期（检查 10-31 12:00 ET） | 2026-11 期（`endDate` 2026-12-01T04:59Z） |
|---|---|---|
| 事件 slug | `which-company-has-the-best-ai-model-end-of-october` | `which-company-has-the-best-ai-model-end-of-november` |
| 臂数 | 32 | 35 |
| event volume | 2,956,232.94 | 341,608.79 |
| event liquidity | 1,513,204.41 | 未取 |
| Google | last 0.736，bid 0.742 / ask 0.743，tick 0.001 | bid 0.50 / ask 0.53，spread 0.03 |
| Anthropic | bid 0.23 / ask 0.24，tick 0.01 | bid 0.39 / ask 0.43，spread 0.04 |
| OpenAI | bid 0.006 / ask 0.008 | bid 0.035 / ask 0.047 |
| 具名臂 Yes 合计 | 0.9955（21 臂） | 未算（含占位 8.012 无意义） |

- 10 月这期具名臂合计 0.9955（我的算术：把 21 个具名臂 `outcomePrices[0]` 相加），全部 32 臂相加得 6.4955，因为 11 个 `Company *`/`Other` 臂停在默认 0.5。
- CLOB 盘口（`clob.polymarket.com/book?token_id=...`，2026-10-20）：Google Yes 最优 bid `0.742×196`、最优 ask `0.743×128.15`，前 10 档 bid 约 1,240.10 USD、ask 约 2,387.70 USD；Anthropic Yes 最优 bid `0.23×570.38`、ask `0.24×186.59`，前 10 档 bid 约 1,220.70 USD、ask 约 7,448.40 USD。
- 费用字段（Gamma 逐市场）：`feeSchedule = {exponent: 1, rate: 0.04, takerOnly: true, rebateRate: 0.25}`，与 GUIDE 第 8 节 tech 类 0.04 一致；`orderMinSize=5`（份）。
- **未取得（不写成结论）**：榜单当前 Rank、Top1/Top2 的 Arena 分数与置信区间、AutoEval 名单、历史任何一天的榜单快照内容。→ `arena.ai/leaderboard/text/overall-no-style-control`、`arena.ai/leaderboard/text/overall`、`arena.ai/api/leaderboard/text`、`lmarena.ai/leaderboard/text` 均返回 **HTTP 403**；`web.archive.org/cdx/...` 索引返回 200 并列出 2026-01-30 起的 `arena.ai/leaderboard/text/overall-no-style-control` 200 快照，但取内容两次 **HTTP 000**（失败）。
- **没有任何回测**：`observed_net_return = null`，Sharpe 未知，翻盘基率未知，`backtest_count = 0`（仅表示未做，不代表收益为 0）。过去已结算的 22 期为 0/1 结算价，能证明"事件确实按月结算"，不能证明本策略赚钱。

## 数据

- `https://gamma-api.polymarket.com/events?slug=<slug>`：规则原文、`endDate`、`negRisk`、32/35 个臂、`outcomePrices`、`bestBid/bestAsk/spread`、`feeSchedule`、`orderPriceMinTickSize`、`orderMinSize`。免费免密钥。
- `https://gamma-api.polymarket.com/series/10030` 与 `https://gamma-api.polymarket.com/events?series_id=10030&limit=60&closed=true|false`：`recurrence: monthly`、`createdAt 2025-02-01T00:23:50Z`，已结算 22 个 event、在开 3 个（2026-10、2026-11、年度 `end-of-2026`）。免费免密钥。
- `https://clob.polymarket.com/book?token_id=<id>`：现价盘口与 10 档深度。免费免密钥；**历史 L2 不公开**，只能从今天起自行记录。
- 结算源：`https://arena.ai/leaderboard/text/overall-no-style-control`（规则指定的那一页）。本轮 403，**无法程序化取数**；`web.archive.org/cdx/...` 只能给快照时间戳清单。
- 结算结果核对：Gamma 已结算 event 的 `outcomePrices`（0/1）。

**同类数量与起始时间（本轮已核）**：series `10030`（`best-ai-company`，`Best AI Company`）最早 event `top-ai-model-on-december-31`（`endDate 2024-12-31`），至 2026-09 逐月连续，**已结算 22 个月度 event**（2024-12、2025-01…2025-12、2026-01…2026-09），加在开的 2026-10、2026-11 与年度 2026 = 25 个。即 **约每月 1 个同类 event**，规模从 5 臂（2024-12）增长到 32 臂（2026-10）/35 臂（2026-11）。独立结果按 event 数 = 每月 1 个。

## 两周内怎么检验

- 数据：Gamma（价格、臂、规则）+ 手工读 arena.ai 榜单（因 403，必须人工，且必须剔除 AutoEval、确认 style control 关了）。每天记一次：Top1/Top2 公司、名次、分数（若页面给）、三臂 bid/ask、深度。
- 独立结果：**按 event 计，一个月一个，禁按臂或按天计数**。历史可用仅 22 个（2024-12…2026-09），两周前向只新增 1 个（2026-10-31 12:00 ET 检查）→ **两周内不可能得到 30 个独立结果**，本项只能进待选区做 forward。
- 失败标准（预先写死）：在拿到的独立 event 上，按"实际结算 − (入场 ask + 吃单费 + 半价差)"算的净 PnL 中位 ≤ 0，或方向命中率不超过"买当时价格更高的那臂"的基准，即判失败。
- 若只想低成本先验证一半：可先做**无交易的规则核对**（读榜剔除 AutoEval 后，看 2026-09 已结算 event 的冠军是否等于当日 Rank 列第一），但这需要 2026-09-30 的历史快照，本轮内容抓取失败，**未做**。

## 成本与容量

- 吃单费（GUIDE 第 8 节公式，费率取 Gamma `feeSchedule.rate=0.04`）：每份费 = `0.04 × p × (1−p)`。maker 无费；本条按吃单算，因为需要确定成交。
- 每笔总成本 = 费 + 半个买卖价差。逐臂算术（p 用当时 ask）：
  - Google（10 月）ask 0.743：`0.04×0.743×0.257 = 0.00763804`；半价差 `(0.743−0.742)/2 = 0.0005`；合计 **0.00813804/份 = 买价的 1.0953%** → 盈亏平衡概率 75.11%。
  - Anthropic（10 月）ask 0.24：`0.04×0.24×0.76 = 0.007296`；半价差 `(0.24−0.23)/2 = 0.005`；合计 **0.012296/份 = 5.1233%** → 平衡概率 25.23%。
  - Anthropic（11 月）ask 0.43：`0.04×0.43×0.57 = 0.009804`；半价差 `(0.43−0.39)/2 = 0.02`；合计 **0.029804/份 = 6.9312%** → 平衡概率 45.98%。
  - Google（11 月）ask 0.53：`0.04×0.53×0.47 = 0.009964`；半价差 0.015；合计 **0.024964/份 = 4.7102%** → 平衡概率 55.50%。
  → 结论：这条策略必须比市场多算 1.1pp（Google 10 月）到 6.9pp（Anthropic 11 月）才算不亏。11 月那期价差是 3–4 美分（tick 0.01），成本高一个量级；**只在 1 美分 tick、深盘口的臂上做**（10 月 Google 的 tick 是 0.001）。
- 资金占用天数：2026-10 这期从现在（2026-10-20）到 `2026-10-31T16:00:00Z` 约 **11.5 天**；11 月那期到 `2026-12-01T04:59:00Z` 约 42 天。年化换算示例（算术、不复利、不含方差）：若某臂 11.5 天内净赚本金 6.58%，`6.58% × 365/11.5 ≈ 208.8%/年` —— 这是敏感性算术，不是预测。
- 容量：500 份 Anthropic @0.24 ≈ 120 美元（10 月，ask 侧 top10 有 7,448 美元深度）；500 份 Google @0.743 ≈ 372 美元（ask 侧 top10 仅 2,387.70 美元）。→ 1,500 USDT 的整组上限放得下，但**再大就会把 1 美分 tick 吃穿**；单场所 ≤2,500 USDT 的约束不是瓶颈，深度才是。
- 机会频率：**每月 1 个 event**（本轮 22 个已结算 + 2 个在开月度），即每月约 1 次、每次可做 1–3 个臂。年化机会数 ≈ 12 个 event。

## 风险

- **榜单不可机读**：结算源 403，只能人工读；读错（忘关 style control 之外的口径、没剔除 AutoEval、看的是得分页而非 Rank 列）会直接算错 P̂。
- **规则改版**：2024-12 那期根本没写结算源，2025 用"最高 Arena Score"，2026 用"Rank 列优先"。再改一次（比如换回分数、换榜单页、开 style control）会让历史校准失效。
- **检查时点是瞬时**：12:00 PM ET 那一刻的 Rank 列；榜单在检查前后几小时可能刷新，一次新模型上线就能翻盘。这是主要亏钱场景。
- **平手/字母序**：极端同分时字母序偏向 Anthropic；本条不押这个，若有人拿这一点做定价要注意 granular 分数先比较。
- **占位臂陷阱**：`Company A–M`/`Other` 显示 0.5、bid 0 ask 1，没有可成交盘；把"具名臂合计 0.9955<1"当无风险套利是错的。
- **慢结算**：源不可用则市场保持开放，资金被锁到榜单恢复为止；永久不可用结算"Other"，可能让具名臂全部归零。
- **流动性/价差**：11 月那期 3–4 美分价差，成本 4.7%–6.9%，方向稍微错一点就吃掉全部优势。
- **数据缺口**：没有任何历史榜单快照内容与翻盘基率，本条无法证明正收益。

## 改进了什么

不适用（`kind: new`）。

## 门槛自查

1. 机制说得清：满足 — 规则原文明确"按 10-31 12:00 PM ET 的 Rank 列结算、style control 关、排除 AutoEval"，付款方是把月末叙事定价过头的对手方。但"榜首黏性高于定价"这一半是假设，未测。
2. 有免费数据能检验：不满足 — 价格/规则/结算免费免密钥（Gamma、CLOB 已取），但**收益赖以计算的结算源 arena.ai 本轮 403，Wayback 内容两次 HTTP 000**，历史榜单值未取得；历史 L2 也不公开。
3. 小资金能做：满足 — 单臂 500 份仅 120–372 美元（按上表 ask），ask 侧 10 档深度 2,387.70–7,448.40 美元，5,000/2,500 的约束不构成瓶颈；代价是规模上限很低。
4. 不重复：满足（本轮检索范围内） — `grep` 了 `bots/*/CLAIMS.md`、`bots/*/INDEX.md`、`known/`，无 arena/lmarena/AI model 相关条目；dot-032 是做市奖励，收益来源不同。未逐条比对全部 entries 正文。
5. 扣成本后粗算够用：不确定 — 每笔成本已按公式算到 1.10%–6.93%（含半价差），但 P̂ 未校准、无回测，`observed_net_return=null`，不能声称扣成本后为正。
6. 两周内能检验：不满足 — 历史自 2024-12 起只有 22 个已结算 event，一个月才 1 个独立结果，两周内至多新增 1 个，凑不到 30 个；只能 forward 且长期。
7. 出处可查：不确定（部分完成） — 规则原文、臂数、价格、盘口、费用、series 计数都有 URL + 访问日期 + 字段名；但结算源数据本身未取到，榜单分数/置信区间全部"未查到"。

## 出处

- https://gamma-api.polymarket.com/events?slug=which-company-has-the-best-ai-model-end-of-october — 访问 2026-10-20 — 已读（event 841230 规则原文、32 臂、`endDate 2026-10-31T16:00:00Z`、`updatedAt 2026-10-20T04:00:58Z`、volume 2,956,232.94、liquidity 1,513,204.41、`feeSchedule.rate 0.04`）
- https://gamma-api.polymarket.com/events?slug=which-company-has-the-best-ai-model-end-of-november — 访问 2026-10-20 — 已读（35 臂、价格 0.41/0.515/0.041、spread 0.03–0.04、volume 341,608.79）
- https://gamma-api.polymarket.com/series/10030 — 访问 2026-10-20 — 已读（`recurrence: monthly`、`createdAt 2025-02-01T00:23:50Z`）
- https://gamma-api.polymarket.com/events?series_id=10030&limit=60&closed=true — 访问 2026-10-20 — 已读（22 个已结算 event 及臂数、volume；最早 `top-ai-model-on-december-31`）
- https://gamma-api.polymarket.com/events?series_id=10030&limit=60&closed=false — 访问 2026-10-20 — 已读（3 个在开 event：2026-10、2026-11、`which-company-has-best-ai-model-end-of-2026`）
- https://clob.polymarket.com/book?token_id=111088620532234518037120406087772586039940496346205331791940213760503764823657 — 访问 2026-10-20 — 已读（Google Yes：bid 0.742×196、ask 0.743×128.15、前 10 档 1,240.10 / 2,387.70 USD）
- https://clob.polymarket.com/book?token_id=17398972530137600675762712744895375915722542439211248541948693649429200536957 — 访问 2026-10-20 — 已读（Anthropic Yes：bid 0.23×570.38、ask 0.24×186.59、前 10 档 1,220.70 / 7,448.40 USD）
- https://arena.ai/leaderboard/text/overall-no-style-control — 访问 2026-10-20 — 已尝试，HTTP 403，未作为数据源
- https://lmarena.ai/leaderboard/text — 访问 2026-10-20 — 已尝试，HTTP 403，未作为数据源
- https://web.archive.org/cdx/search/cdx?url=arena.ai/leaderboard/text/overall-no-style-control — 访问 2026-10-20 — 已读（仅快照索引，最早 20260130012509；取内容失败 HTTP 000）
- 费用公式与 tech 费率核对采用 GUIDE 第 8 节 + 本轮 Gamma `feeSchedule`；本轮无成交回执，不以配置字段证明实际扣费
