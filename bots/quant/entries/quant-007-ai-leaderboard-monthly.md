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
data: Gamma events/markets、CLOB prices-history、data-api trades 均免费免密钥；结算源 arena.ai 直连仍 403，但 2026-10-21 找到 HF `lmarena-ai/leaderboard-dataset`（cc-by-4.0，config `text`、category `overall` 日度快照，2023-05-08..2026-10-15）作历史榜名的第三方镜像；已用其 + 已关闭市场真实价格做 22 个已结算 event 的回测（见证据）
test_2w: 独立结果按 event 计（一月一 event、一 event 只一个结算快照，禁按臂计数）；历史 22 个已结算 event 已全部回测（21 个有价格），仍 <30，两周内只新增 1 个（2026-10-31 12:00 ET）；失败标准：净 PnL 均值 ≤0，或同口径不如「买市场当时最贵臂」的基准；本次已触发失败
status: 待核
confidence: 中
---

整理说明：本稿只由实际抓取的 Gamma/CLOB/data-api 响应与规则原文写成。原稿写作时**官方榜单页取不到**：`arena.ai` 与其 `/api/` 路径返回 403，`web.archive.org` 内容抓取两次 HTTP 000。**2026-10-21 复核新增**：HF 上的 `lmarena-ai/leaderboard-dataset` 提供了 `text` / `overall` 的日度历史快照（cc-by-4.0），因此第一次能对 22 个已结算 event 做"榜名 + 可成交价 + 结算"的回测。回测结果是**负的**（见证据），本条因此只应进待选区，不应收录；建议核对方降级。

## 复核结论（2026-10-21，负证据）

- 22 个已结算 event 中 21 个能同时拿到"检查前榜名"和"已关闭市场历史价"。按检查前 7 天买入榜名第 1 的公司 Yes、持到结算（吃单费 0.04·p·(1−p)，再各加 0.5¢/1¢ 滑点），**均值 −0.034/−0.039 每份**，中位 +0.014/+0.010；95% bootstrap 区间 `[−0.141, +0.039]`，不能拒绝 0。
- 同一时点买"市场自己最贵的臂"（基准）均值 **+0.025**、命中 **21/22 = 95.5%**；榜名第 1 只命中 15/21 = 71.4%。两者不一致的 5 个 event 里，**榜名 0/5、市场最贵臂 5/5**；配对差均值 **−5.91pp**（95% 区间 `[−11.95pp, −1.11pp]`，不含 0）。
- 条目自己写的进场条件（榜名臂价 ≤0.85）下 n=7，均值 **−0.014**、中位 **−0.020**，仍是负的。
- 唯一正的口袋是"提前 21 天进场"：均值 +0.101，但 44% 来自 2026-02 一个 event（榜名 Anthropic 0.069、市场最贵 Google 0.87、Anthropic 赢），且 95% 区间 `[−0.008, +0.217]` 含 0；不能当作可复制的边。
- 2026 年 9 个 event 榜名全对（9/9），但**这 9 个里榜名第 1 与市场最贵臂完全是同一臂**，所以测不到"榜名相对市场"的增量；现行 Rank 规则的 6 个 event 也一样。换言之：现有数据无法证明榜名信号有价值，反而在它能与市场分歧的样本里全错。

## 一句话

在 Polymarket 每月一次的「哪家公司拥有最好的 AI 模型」negRisk 组里，用结算源（arena.ai Text Arena Overall，style control 关）的榜单名次去比市场的吃单价：买"当前第一名所属公司"，持有到月末检查时点。**2026-10-21 的历史回测（22 个已结算 event）没有支持这个边：按检查前 7 天买榜名第一，净均值为负，且显著输给"买市场当时最贵臂"；详见证据。** 本条保留为负证据与规则记录，不建议收录。

## 钱从哪里来

付款方是把"谁最强"当叙事出价的对手方，而结算只看**某一瞬间**的榜单列。规则原文（见下）规定结算取 2026-10-31 12:00 PM ET 那一刻的 Rank 列，不是月度平均、也不是"曾经第一"。榜单前列在几周内通常变化有限，而市场叙事（新模型发布、发布传闻）会把近月的臂推得比"到那一刻仍第一"的实际概率更高或更低，价差就是这个偏差。这条钱的持续性依赖两点：(a) 榜首在 2–6 周窗口内的黏性显著高于市场定价；(b) 榜单页本身公开可读，信息差不该存在，所以偏差只能来自纪律/注意力而非信息。**2026-10-21 已用历史数据检验 (a)：不成立。** 检查前 7 天榜名第一的命中率 15/21=71.4%，市场自己最贵臂 21/22=95.5%；榜名第一的均价 0.742 对命中率 0.682，甚至略偏贵。与 dot-032（做市奖励）不同，付款方不是平台预算，是对手方。

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
- 信号：设榜单 Top1 公司为 L、Top2 公司为 C。若 L 的 ask ≤ 0.85 且（我给出的）P̂(L 到检查时仍第一) − (ask_L + 费 + 半价差) ≥ +2pp，则买 L；若 C 的 ask ≥ P̂(C 翻盘) + 费 + 半价差 + 2pp，则买 C 的 No（等价于押 L）。P̂ 的计算方式必须先固定（例如"以分差/名次差为主的单调映射 + 历史翻盘基率"）。**原稿没有榜单数据，P̂ 未校准；2026-10-21 的回测只能检验"无条件买榜名第一"和条目自己的 `ask≤0.85` 子样本，二者都为负，故不再补写 P̂ 参数。**
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
- **官方榜单页仍取不到**：`arena.ai/leaderboard/text/overall-no-style-control`、`arena.ai/leaderboard/text/overall`、`arena.ai/api/leaderboard/text`、`lmarena.ai/leaderboard/text` 在 2026-10-21 复核时仍全部 **HTTP 403**；`web.archive.org/cdx/...` 索引 200，列出 2026-01-30 起的快照，但内容两次 HTTP 000。**新增替代**：HF `lmarena-ai/leaderboard-dataset` 的 `text`/`overall` 日度快照给出了历史名次（第三方镜像，非官方页）。
- **2026-10-21 复核时点变化**：10 月 event 的 Gamma `outcomePrices` 具名臂合计从 0.9955 变为 **1.0065**（Google last 0.799）；11 月 Anthropic 变为 bid 0.43/ask 0.44；10 月 event 的 `feeSchedule.rate` 现在全部为 **0**（原快照为 0.04）。这些是时变值，旧数字保留原抓取时点，不当作现值。CLOB `/book` 用原 token 复核时返回空盘口（bid 0.001 / ask 0.999），已无法复现 2026-10-20 的 0.742/0.743 快照。

### 历史可成交价格回测（2026-10-21 新增，结果：负）

**数据与规则（先写死）**

- 样本：Gamma `series_id=10030&closed=true` 的全部 **22 个已结算 event**（2024-12..2026-09；其中 6 个使用现行"Rank 列"规则）。赢家取该 event 中 `outcomePrices[0]=="1"` 的臂。
- 榜名：HF `lmarena-ai/leaderboard-dataset`（license `cc-by-4.0`，`gated=false`）config `text`（推断为 no-style-control；与 `text_style_control` 并列，官方页 403 无法确认）、`category="overall"`，取 `leaderboard_publish_date <= 检查时刻−L 天` 的**最新**快照，`rank==1` 的 `organization` 按别名映射到市场臂（OpenAI/ChatGPT、Anthropic/Claude、Google/Gemini、SpaceXAI/xAI、Meta/Llama）。
- 价格：`clob.polymarket.com/prices-history?market=<yes_token>&interval=max&fidelity=1440` 中 `t <= 进场时刻` 的最后一点；另用 data-api `trades` 抽查真实成交价。
- 成本：吃单费 `0.04×p×(1−p)`（按 2026-10-20 的 Gamma 费率快照；2026-10-21 该 event 费率已变 0，故此处**保守**），再分别加 0/0.5¢/1¢ 滑点。每 event 1 份，持到结算，不做 maker、不拟合任何参数。
- 基准：同一时刻"市场自己最贵（`prices-history` 最高）的具名臂"，同样的费用与滑点。

**结果（`analyze_output.txt` 原样）**

| 进场时点 | n | 榜名命中 | 净均值 (0.5¢ 滑点) | 95% bootstrap | 净中位 |
|---|---:|---:|---:|---|---:|
| 检查前 7 天 | 21/22 | 15/21 = 71.4% | **−0.0342** | [−0.1413, +0.0385] | +0.0144 |
| 检查前 14 天 | 21/22 | 15/21 | −0.0032 | [−0.1089, +0.0745] | +0.0433 |
| 检查前 21 天 | 21/22 | 15/21 | +0.1008 | [−0.0081, +0.2173] | +0.0771 |

- 7 天的均值 **−3.4¢**、中位 **+1.4¢**（均值被个别大亏拉负）；1¢ 滑点下均值 −0.0391、中位 +0.0096。2024–2025 共 12 个 event 均值 **−0.102**，2026 年 9 个 **+0.056**（95% 区间 [+0.017, +0.107]）。2026 年 9/9 榜名都对，但这 9 个里榜名第一与市场最贵臂**完全是同一臂**，所以正收益是"买最贵臂"的收益，不是榜名增量。
- 21 天的正均值不稳健：总净利 +2.116 中 **+0.923（44%）来自 2026-02 一个 event**（榜名 Anthropic 0.069，市场最贵 Google 0.87，Anthropic 赢）；去掉它后均值约 +0.060，区间变宽。
- **基准对比（7 天）**：买市场最贵臂命中 **21/22 = 95.5%**，净均值 **+0.0246**，中位 +0.0238（95% 区间 [−0.0814, +0.0935]）。榜名第一与最贵臂不一致的只有 **5 个 event，榜名 0/5、最贵臂 5/5**；配对差（榜名−最贵臂）均值 **−0.0591**，95% 区间 **[−0.1195, −0.0111]**，不含 0。榜名第一均价 0.742 对命中率 0.682，Brier 0.0472；最贵臂均价 0.9225 对命中率 0.9545，Brier 0.0488。
- **条目自己的 `ask≤0.85` 子样本（7 天）**：n=7，均值 **−0.0137**、中位 **−0.0203**、合计 −0.0962（投入 2.034）；7 个里 5 个是 2024–2025 年"榜名与市场分歧"的 event，全部押错。
- **镜像校验**：HF 镜像的 rank-1 与市场实际结算一致率，7/14/21 天都是 **15/22**；2026 年 **9/9**，2024–2025 只有 **6/13**。所以镜像在旧年份很可能与当期真实榜单/规则不一致，旧年份的负结果不能全部归因于策略；但 2026 年（镜像与结算一致）又完全没有"榜名≠市场"的样本，**无法证明增量**。这是本条最根本的证据缺口。

**判定**：按预先写死的失败标准（净均值 ≤0，或不如"买最贵臂"基准），**FAIL**。回测不是"没做"，而是做了且为负；唯一正的口袋依赖单个 event 与 21 天提前量，不构成可复制证据。数据接口与脚本在 `bots/quant/notes/scheduler/scratch/H-quant-007/`（`q007_hist.py`→`fetch_output.txt`/`backtest_raw.csv`，`q007_analyze.py`→`analyze_output.txt`，`q007_fills.py`→`fills_output.txt`，`q007_verify.py`→`verify_output.txt`，`q007_hist_sc.py`→`fetch_sc_output.txt`）。

**费用敏感性**：即使把吃单费设为 0，7 天均值仍为 **−0.0322**、配对差 **−0.0597**；`ask≤0.85` 子样本均值 −0.0099、中位 −0.0195。所以"2026-10-21 费率变 0"不能救本条。

**稳健性检查（style control 口径）**：用同一数据集的并列 config `text_style_control`（2024-08-28 起有快照）重跑，22 个 event 的 `rank==1` 公司**完全相同**，7/14/21 天的命中与净收益也逐位一致（`q007_hist_sc.py` + `fetch_sc_output.txt`）。所以"config `text` 是否就是 no-style-control"这一不确定性**不影响本次结论**。

**局限（不隐藏）**

- `prices-history` 是日频最后成交/标记点，不等于可成交盘口；data-api 抽查 3 个 event 的进场前最后一笔真实买入为 0.985（vs 0.982）、0.710（vs 0.795，仅 1.41 份）、0.250（vs 0.220），差 0.3–8.5¢，无法还原深度与排队。
- 镜像 `text` 是否与规则指定的 `overall-no-style-control` 页完全同口径，无法从官方页验证（403）；2026 年 9/9 吻合只是弱支持。
- 镜像日期只有"日"，检查当天 2026-09-30 的快照 rank-1 是 Google，而市场在 12:00 ET 结算为 Anthropic；所以只使用检查前 7/14/21 天，避免当日歧义，但也意味着无法精确复现"检查瞬间"。
- 没做 maker 成交假设；每 event 1 份，绝对金额不是实盘 PnL。

## 数据

- `https://gamma-api.polymarket.com/events?slug=<slug>`：规则原文、`endDate`、`negRisk`、32/35 个臂、`outcomePrices`、`bestBid/bestAsk/spread`、`feeSchedule`、`orderPriceMinTickSize`、`orderMinSize`。免费免密钥。
- `https://gamma-api.polymarket.com/series/10030` 与 `https://gamma-api.polymarket.com/events?series_id=10030&limit=60&closed=true|false`：`recurrence: monthly`、`createdAt 2025-02-01T00:23:50Z`，已结算 22 个 event、在开 3 个（2026-10、2026-11、年度 `end-of-2026`）。免费免密钥。
- `https://clob.polymarket.com/book?token_id=<id>`：现价盘口与 10 档深度。免费免密钥；**历史 L2 不公开**，只能从今天起自行记录。
- `https://clob.polymarket.com/prices-history?market=<yes_token>&interval=max&fidelity=1440`：**已关闭市场也可取**的日频历史价（最后成交/标记点）。这是本次回测的价格来源；不需要密钥。
- `https://data-api.polymarket.com/trades?market=<conditionId>&limit=1000&offset=N`：已关闭市场的逐笔成交（`side/price/size/timestamp/asset`），用于抽查历史价是否可成交；每个市场只能翻到最近约 2 万笔。
- 结算源：`https://arena.ai/leaderboard/text/overall-no-style-control`（规则指定的那一页）。2026-10-21 仍 403，**无法直接取数**；`web.archive.org/cdx/...` 只给时间戳。
- **历史榜名（第三方镜像）**：`https://huggingface.co/datasets/lmarena-ai/leaderboard-dataset`，config `text`（与 `text_style_control` 并列；**推断**为 no-style-control，官方页 403 无法确认）、`category="overall"`、列 `rank/organization/model_name/rating/leaderboard_publish_date`，日度快照 2023-05-08..2026-10-15，`gated=false`、CC-BY-4.0，免费免密钥。用 `https://datasets-server.huggingface.co/rows?...` 可先看 schema；完整 parquet `text/full-00000-of-00001.parquet` 约 60 MB，下载后只派生 `_cache/overall.csv`（3.7 MB）；原始 parquet 未保留、未入库。
- 结算结果核对：Gamma 已结算 event 的 `outcomePrices`（0/1）。

**同类数量与起始时间（本轮已核）**：series `10030`（`best-ai-company`，`Best AI Company`）最早 event `top-ai-model-on-december-31`（`endDate 2024-12-31`），至 2026-09 逐月连续，**已结算 22 个月度 event**（2024-12、2025-01…2025-12、2026-01…2026-09），加在开的 2026-10、2026-11 与年度 2026 = 25 个。即 **约每月 1 个同类 event**，规模从 5 臂（2024-12）增长到 32 臂（2026-10）/35 臂（2026-11）。独立结果按 event 数 = 每月 1 个。

## 两周内怎么检验

- **历史回测已做（2026-10-21）**：22 个已结算 event、21 个有价格；7/14/21 天三个进场时点。结论 FAIL（细节见"证据"）。独立结果仍按 **event** 计，一个月一个，禁按臂/按天拆分。
- 历史样本天花板：22 个 event < GUIDE 要求的 30 个，且 2026 年只有 9 个；两周内只新增 1 个（2026-10-31 12:00 ET 检查）。所以即使不看负结果，本条也**不满足门 6**，只能进待选区/forward，不能收录。
- 若还要往前做 forward：每天用 HF 镜像或人工读榜记一次 Top1/Top2、榜名臂 bid/ask/深度；失败标准保持不变——净 PnL 均值 ≤0，或同口径不如"买市场当时最贵臂"。
- 现行 Rank 规则的 6 个 event 已可做规则核对：2026-04..2026-09 的结算冠军与检查前 7 天榜名第一 **6/6 一致**（但同期市场最贵臂也 6/6 一致）。

## 成本与容量

- 吃单费（GUIDE 第 8 节公式，费率取 2026-10-20 抓到的 Gamma `feeSchedule.rate=0.04`）：每份费 = `0.04 × p × (1−p)`。maker 无费；本条按吃单算，因为需要确定成交。
- **费率是时变的**：2026-10-21 复核时，2026-10 event 全部具名臂的 `feeSchedule` 已变为 `rate=0, rebateRate=0`。若按今天的字段算，成本只有半价差，回测里的 0.04 是**保守**处理；但这不改变负结论的方向。
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
- **回测已给出负结果**：检查前 7 天买榜名第一净均值 −0.034/份，且显著输给"买市场最贵臂"（配对差 −5.9pp）；条目自己的 `ask≤0.85` 子样本中位 −0.020。**不是"未验证"，是"已验证且不利"。**
- **镜像可能失真**：HF 镜像在 2024–2025 只与结算 6/13 吻合，可能是镜像口径/回填问题；这会让旧年份的负结果偏保守或偏错，但 2026 年镜像 9/9 吻合、且没有"榜名≠市场"的样本，所以也无法把负结果翻成正证据。
- **单一 event 依赖**：21 天提前量的正均值 44% 来自 2026-02 一个 event；若把它当"边"，样本量只有 1，属于典型事后挑样本。

## 改进了什么

不适用（`kind: new`）。

## 门槛自查

1. 机制说得清：满足（描述层面） — 规则原文明确"按 10-31 12:00 PM ET 的 Rank 列结算、style control 关、排除 AutoEval"，付款方是把月末叙事定价过头的对手方。但机制赖以成立的关键假设"榜首黏性高于市场定价"**已被历史数据否证**（榜名 15/21 vs 市场最贵臂 21/22）。
2. 有免费数据能检验：**部分满足（原为不满足）** — 价格、结算、历史榜名都能免费免密钥取得：Gamma + CLOB `prices-history` + data-api trades + HF 镜像。缺口是官方 `arena.ai` 仍 403，榜名只能用第三方镜像；镜像在 2024–2025 只与结算 6/13 吻合。
3. 小资金能做：满足 — 单臂 500 份仅 120–372 美元（按 2026-10-20 ask），5,000/2,500 的约束不构成瓶颈；但 2026-10-21 复核时原 CLOB 盘口已为空、深度数字不可复现，容量结论只能按旧快照看。
4. 不重复：满足（本轮检索范围内） — `grep` 了 `bots/*/CLAIMS.md`、`bots/*/INDEX.md`、`known/`，无 arena/lmarena/AI model 相关条目；dot-032 是做市奖励，收益来源不同。quant-017 已按 supplement 回挂本条，不构成第二条新机制。
5. 扣成本后粗算够用：**不满足** — 已按吃单费 + 0.5¢ 滑点算：7 天净均值 −0.034/份，条目自己的 `ask≤0.85` 子样本中位 −0.020；21 天的正均值不稳健且依赖单个 event。
6. 两周内能检验：不满足 — 历史自 2024-12 起只有 22 个已结算 event（21 个有价格），一个月才 1 个独立结果，两周内至多新增 1 个，凑不到 30 个；只能 forward 且长期。
7. 出处可查：基本满足 — 规则原文、臂数、价格、费用、series 计数、HF 镜像、回测数字都有 URL + 访问日期 + 字段名/脚本；但官方结算页 403、镜像口径只能间接校验。

**建议**：七条里 1（描述）与 4 满足、2 部分、3 受旧快照限制、5/6 不满足；核心边已被负回测否证。**建议核对方将本条降为草稿/退回（待选区），不要收录。**（按要求本次未改 `status` 与 `date`，降级由整合者执行。）

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

**2026-10-21 复核新增（全部重新抓取，脚本与 stdout 在 `bots/quant/notes/scheduler/scratch/H-quant-007/`）**

- https://gamma-api.polymarket.com/events?slug=which-company-has-the-best-ai-model-end-of-october — 访问 2026-10-21 — 已读（event 841230 仍在；32 臂；`updatedAt 2026-10-21T01:21:08Z`、volume 3,013,798.12、liquidity 1,521,898.35；Google last 0.799 / bid 0.799 / ask 0.800；Anthropic 0.20 / 0.18 / 0.19；具名臂合计 1.0065；**`feeSchedule.rate` 已变为 0**）→ 旧数字是 2026-10-20 时点快照，非现值。
- https://gamma-api.polymarket.com/events?slug=which-company-has-the-best-ai-model-end-of-november — 访问 2026-10-21 — 已读（35 臂；Anthropic bid 0.43 / ask 0.44；Google 0.49 / 0.51；OpenAI 0.035 / 0.049；volume 344,129.62）
- https://gamma-api.polymarket.com/series/10030 — 访问 2026-10-21 — 已读（`Best AI Company`、`monthly`、`createdAt 2025-02-01T00:23:50Z`、`restricted=true`）
- https://gamma-api.polymarket.com/events?series_id=10030&limit=60&closed=true — 访问 2026-10-21 — 已读（22 个已结算；臂数序列 5,6,12,15,12,13,16,13,12,15,23,15,17,25,25,25,27,29,19,26,32,32；含 "arena rank" 的现行规则 event 6 个）
- https://gamma-api.polymarket.com/events?series_id=10030&limit=60&closed=false — 访问 2026-10-21 — 已读（3 个在开：2026 年度、2026-10、2026-11）
- https://huggingface.co/api/datasets/lmarena-ai/leaderboard-dataset — 访问 2026-10-21 — 已读（`gated:false`、`private:false`、license `cc-by-4.0`、`lastModified 2026-10-20T03:03:04Z`）
- https://huggingface.co/datasets/lmarena-ai/leaderboard-dataset/raw/main/README.md — 访问 2026-10-21 — 已读（configs 含 `text` 与 `text_style_control`；`full` = 所有历史发布；schema：`rank`、`organization`、`leaderboard_publish_date`；2024-01-09 Elo→Bradley-Terry、2025-05-16 style control 成默认）
- https://huggingface.co/datasets/lmarena-ai/leaderboard-dataset/resolve/main/text/full-00000-of-00001.parquet — 访问 2026-10-21 — 已读（60 MB；筛 `category="overall"` 后派生 `_cache/overall.csv`，覆盖 2023-05-08..2026-10-15；原始 parquet 未保留）
- https://datasets-server.huggingface.co/rows?dataset=lmarena-ai%2Fleaderboard-dataset&config=text&split=full&offset=0&length=3 — 访问 2026-10-21 — 已读（schema 与首行，用于确认列名）
- https://clob.polymarket.com/prices-history?market=114976310403134140071475285729050128086700898119247346798479138721789575328536&interval=max&fidelity=1440 — 访问 2026-10-21 — 已读（已关闭 2026-09 Anthropic 市场有日频历史；回测对所有具名臂用同一接口）
- https://data-api.polymarket.com/trades?market=0x537df24dbae425e973a421983b6ee570d582cac06b5fdbebef099d3d07913985&limit=1000 — 访问 2026-10-21 — 已读（逐笔成交；抽查 3 个 event 的进场前最后一笔买价见 `fills_output.txt`）
- https://arena.ai/leaderboard/text/overall-no-style-control — 访问 2026-10-21 — 已尝试，仍 **HTTP 403**，未作为数据源
- https://lmarena.ai/leaderboard/text — 访问 2026-10-21 — 已尝试，仍 **HTTP 403**
- https://web.archive.org/cdx/search/cdx?url=arena.ai/leaderboard/text/overall-no-style-control&output=json&limit=6&from=2026&filter=statuscode:200 — 访问 2026-10-21 — 已读（仅索引；最早 20260130012509；内容仍取不到）
- bots/quant/notes/batch1-verification/quant-007.md — 访问 2026-10-21 — 已读（复用其中 glm-5.3 对规则原文、22 个已结算 event、URL 403 状态的核对；本次重新抓取确认，未直接改原结论）
- bots/quant/notes/r1-audit/AUDIT.md — 访问 2026-10-21 — 已读（r1 审计判"退回 0"，理由为结算源 403、只有 22 个 event、门 2/6 不满足；本次补了 HF 镜像与回测，但结论仍是负，故不推翻其退回判断）
- 回测脚本与输出：`bots/quant/notes/scheduler/scratch/H-quant-007/q007_hist.py` + `fetch_output.txt` + `backtest_raw.csv`；`q007_analyze.py` + `analyze_output.txt`；`q007_fills.py` + `fills_output.txt`；`q007_verify.py` + `verify_output.txt` — 访问 2026-10-21 — 已跑（数字均从 stdout 原样抄录）
