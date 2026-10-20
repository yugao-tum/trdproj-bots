---
id: quant-025
name_zh: 龙卷风风险区：SPC展望更新时滞
name_en: "Daily tornado-risk city markets: SPC outlook update lag"
bot: quant
date: 2026-10-20
market: polymarket
pm_category: weather
kind: new
improves: -
category: E
return_type: direction
instruments: 每日 25 城「是否位于 SPC Day-1 龙卷风 ≥2% 风险区」YES/NO
venues: Polymarket
data: SPC 归档 Day-1 龙卷风概率 GeoJSON（2026-08-19 起，免费免密钥，含 HTTP Last-Modified）+ Gamma 市场/规则/结算 + data-api 成交（免费，每市场最近约 2 万笔）；历史盘口无公开源，价格用成交价代理
test_2w: 62 个日事件/1550 个市场；宽口径低价 YES 信号 7 个日事件（严格 BUY YES 3 个），两周前向约 1–2 个，凑不到 30；失败标准：扣 0.05 费+1¢ 缓冲后净≤0，或 SPC 多边形与结算不一致 >0
status: 草稿
confidence: 中
---

## 一句话

在 SPC Day-1 龙卷风展望的 1630Z/2000Z 更新文件实际可抓取后，若某城已被列入 ≥2% 风险区、而市场仍以 ≤0.25 美元卖 YES，就买 YES 并持有到 0100Z 最终展望结算；赚市场把「2% 概率标签」误读成「该城只有 2% 概率」的折价。

## 钱从哪里来

- 最可能的付钱方：按较早一版展望、或按「2%」字面定价的散户和撤单做市商。固定 25 城模板、每城市场很薄，新展望发布后常常几十分钟到几小时没有重新报价。
- 机制解释（样本有限）：SPC 每天在固定时点发布/更新展望，市场每天重开一次；2% 区域是地理概率区，不是「城市只有 2% 概率」。城市已在 2% 区内时，最终仍在区内的历史比例 10/15=66.7%（本条样本），而部分市场只给 1–20¢。这个口径差每天重复。
- 边界：这是有预测风险的折价买入，不是无风险套利；0100Z 最终展望可能把城市移出（5/15=33.3%），最大亏损为买入价+费。

## 规则

### 市场模板与示例

- 模板：`Which cities face tornado risk on <Month> <D>?`，series `tornado-risk-daily`（id 12689），每个事件 25 个城市市场（YES/NO）。
- 示例事件：`which-cities-face-tornado-risk-on-september-30-2026`；城市市场如 `...-dallas-tx`、`...-fort-worth-tx`、`...-wichita-ks`。
- 实测日事件 62 个（2026-08-19..2026-10-19），每事件 25 个市场，共 1,550 个市场；事件成交量合计 410,598.8（Gamma 平台字段，未独立审计）。

### 结算规则原文要点（以 Chicago, August 19, 2026 市场为例，逐字）

- “This market will resolve to "Yes" if Chicago, IL falls within a tornado probability area rated ≥2% in the NOAA Storm Prediction Center Day 1 Convective Outlook on August 19, 2026. Otherwise, this market will resolve to "No".”
- “If a city's coordinates fall inside any area rated 2% or higher, that city resolves "Yes". If a city is outside all tornado probability areas, or only within areas rated below 2%, that city resolves "No".”
- “Borderline cases can be independently confirmed using the polygon data (excluding the hatched SIGN overlay, which is not a probability rating) and the city's listed coordinates.”
- “Resolution is based on the scheduled 01:00 UTC Day 1 Convective Outlook update issued on the following UTC calendar day. The SPC Day 1 outlook covers a 24-hour period from 12:00 UTC to 12:00 UTC the following day. Subsequent revisions published after that scheduled update will not be considered. If the SPC outlook is not published or is unavailable, the market remains open until data is available.”
- “This market uses coordinates 41.8781, -87.6298 for Chicago, IL.”
- 结算源：“The resolution source for this market is the NOAA Storm Prediction Center at spc.noaa.gov.” 市场 `resolutionSource=https://www.spc.noaa.gov/products/outlook/day1otlk.html`。

口径要点：最终结算用「次日 01:00 UTC 的 Day-1 更新」（62 个归档文件的 `ISSUE` 实际在 00:35–01:02 UTC，GeoJSON 的 HTTP `Last-Modified` 在 00:35–01:41 UTC），不是 1630Z/2000Z 更新；只用 `LABEL≥0.02` 的概率多边形，排除 `cigtorn`/SIGN 斜线；城市坐标写在各市场规则末尾。

### 预注册规则（本条）

1. **信号可用时点**：不用名义发布时刻，而用归档 GeoJSON 的 HTTP `Last-Modified` + 2 分钟。本样本：1630Z 文件 `Last-Modified` 16:06–17:03 UTC，2000Z 19:35–20:25，0100Z（final）00:35–01:41。前向执行时轮询文件，看到新 `ISSUE` 后下一分钟才允许下单。
2. **窗口**：`[LM(1630Z)+2min, LM(2000Z)+2min)` 和 `[LM(2000Z)+2min, LM(final)+2min)`；`LM` 缺失则退回 `[16:45,19:55)` / `[20:20,次日01:15)`。不在 final 文件可抓取后入场（那一臂是结算时滞，另计，不与本条混合）。
3. **信号**：用该时点已发布的归档 `day1otlk_YYYYMMDD_HHMM_torn.nolyr.geojson`，城市坐标落在任一 `LABEL≥0.02` 的多边形内 → 目标侧 YES；否则不交易（本条只做 YES 折价，不做 NO 侧）。
4. **入场**：窗口内该城市市场第一笔 `BUY Yes` 成交，价格 ≤0.25；若第一笔不是 `BUY Yes` 或价格 >0.25，则跳过，不追、不改价。
5. **仓位**：按该笔成交 size 与 `$50 / 价格` 取小；单市场 ≤$50，单日 ≤$250，场所 ≤$2,500；不加杠杆。
6. **出场**：持有到 UMA 结算；不设止损、不补仓。若 0100Z 最终展望把城市移出，损失为买入价+费。
7. **失败/停止**：若连续 30 个有信号的独立日事件费后净≤0，停止；若 SPC 归档多边形与平台结算出现不一致，先停并复核规则。

不做的：不用 1630Z/2000Z 的 2% 标签直接当概率；不买 NO 侧（NO 侧是另一个机制）；不在最终 0100Z 更新后追（那是 muse 的结算时滞族）。

## 证据

- **规则校验**：62 个已关闭日事件、1,550 个市场；用次日 0100Z 归档 `torn.nolyr.geojson` 对每个城市坐标做点在多边形内判断，与 Gamma `outcomePrices` 结算比对：**0/1,550 不一致**。10 个 YES、1,540 个 NO；有 YES 的日事件 6 个。
- **展望更新**：1630Z 与 2000Z 的城级分类在 1,550 个市场上**完全相同**（0 个变化）；2000Z→0100Z 有 **5 个 True→False**、0 个 False→True。即所有城级变化都发生在最终 0100Z 更新，且都是「移出」。
- **2000Z 在区内的 15 个城-日**：最终仍在区内 10 个（66.7%），被移出 5 个（Indianapolis 8/26、Des Moines 9/8、Omaha 9/14、Oklahoma City 10/14、Indianapolis 10/15）。
- **预注册规则的历史结果**（`reproduce.py`，费 0.05，缓冲 1¢/份）：
  - **严格口径**（窗口内第一笔 `BUY Yes` ≤0.25）：**6 笔、3 个独立日事件，投入 $16.03，净 +$658.23**；5 胜 1 负；单笔最大成本 $6.00。
    - 2026-09-30 Dallas, TX：1630Z 文件 `Last-Modified` 16:30:16；16:39:56 首笔 `BUY Yes` @0.011，300 份；结算 YES，净 +$293.54。
    - 2026-09-30 Fort Worth, TX：同一 1630Z 文件；16:38:56 首笔 `BUY Yes` @0.011，300 份；结算 YES，净 +$293.54。2000Z 窗口又有一笔 00:05:24 `BUY Yes` @0.07、20.01 份，净 +$18.34。
    - 2026-09-04 Columbus, OH：1630Z 文件 `Last-Modified` 16:50:53；16:57:25 首笔 `BUY Yes` @0.01，42 份；结算 YES，净 +$41.14。
    - 2026-09-30 Wichita, KS：1630Z 文件；16:50:35 首笔 `BUY Yes` @0.08，20.1 份；结算 YES，净 +$18.22。
    - 2026-08-26 Indianapolis, IN：2000Z 列在 2% 区；20:46:03 首笔 `BUY Yes` @0.20，30 份；0100Z 被移出，结算 NO，净 −$6.54。
  - **宽口径**（窗口内任一笔成交的 YES 价 ≤0.25，不要求是 `BUY Yes`）：**10 笔、7 个独立日事件，投入 $16.93，净 +$674.71**；5 胜 5 负。多出的 4 笔是 0.01–0.04 的小额成交；Wichita 用 16:33:41 的 5¢ `SELL Yes` 代替严格口径的 8¢ `BUY Yes`，亏损都很小。
  - **缓冲敏感性**（严格口径）：1¢ → +$658.23；3¢ → +$643.99；5¢ → +$629.75。结论对缓冲不敏感，因为赢的时候赢 0.906–0.980/份，输的时候最多 0.218/份。
  - **凸性**：宽口径 10 笔 5 胜 5 负，平均赢利约 0.958/份、平均亏损约 0.073/份，盈亏平衡的生存率约 7.0%；历史胜率 5/10=50%，远高于平衡点。这是本条的主要机制证据，但样本只有 10 笔/7 个城-日，不能当统计证明。
- 来源自报/未核实：Gamma 的 volume/liquidity 是平台字段，未独立审计；成交价来自 data-api 的已执行成交，**不是历史盘口**，无法证明我们能在同一价格、同一数量成交；见风险。

## 数据

- Gamma series/events：`https://gamma-api.polymarket.com/series?slug=tornado-risk-daily`；`https://gamma-api.polymarket.com/events?series_id=12689&closed=true&limit=100&offset=0`（62 个事件，2026-08-19..2026-10-19）。
- 规则/结算/费：每个市场 `description`、`outcomePrices`、`feeSchedule`（`rate=0.05`, `takerOnly=true`, `rebateRate=0.25`）。
- SPC 归档页：`https://www.spc.noaa.gov/products/outlook/archive/2026/day1otlk_20260930_1630.html`（200，Updated 16:26:43 UTC；Valid 301630Z–011200Z）；同目录 `day1otlk_YYYYMMDD_HHMM.html` 与 `-geojson.zip`。zip 内含 `day1otlk_..._torn.nolyr.geojson`（LABEL 0.02/0.05，带 ISSUE/VALID/EXPIRE 字段）。本条用 0100Z 次日文件做结算校验，1630Z/2000Z 文件做信号；可用时点用每个文件的 HTTP `Last-Modified`（`fetch_headers.py` → `_cache/last_modified.csv`）。
- 成交：`https://data-api.polymarket.com/trades?market=<conditionId>&limit=1000`（免费免密钥；本例每市场 1–27 笔，全部 1,550 个市场共 10,674 笔）。历史盘口无公开源。
- 脚本/输出：`bots/quant/notes/scheduler/scratch/B22/reproduce.py`、`reproduce.out`；抓取脚本 `fetch_outlooks.py`、`fetch_trades.py`、`fetch_headers.py`；分类 `classify.py`。原始缓存 `_cache/`（已 `.gitignore`）。

## 两周内怎么检验

- 历史回放：用已归档的 62 个日事件、1,550 个市场，按上述预注册规则重跑；`reproduce.py` 已给出 6 笔严格信号/3 个独立日事件。两周内可以跑完这段历史，但**只有 3 个严格独立结果，远少于 30**。
- 前向：从 2026-10-20 起，每天轮询 1630Z/2000Z 归档 GeoJSON，看到新 `ISSUE` 后按 `Last-Modified`+2 分钟记录 25 城分类和 CLOB 实际 ask/成交；按 ≤0.25、单笔 ≤$50 纸面下单，持有到结算。两周约有 14 个日事件、预计 1–2 个低价信号，仍凑不到 30；要攒到 30 个独立低价信号约需 8–9 个月（宽口径，近 2 个月 7 个独立日事件）或约 20 个月（严格口径，近 2 个月 3 个独立日事件）。
- 失败标准：扣 0.05 吃单费 + 1¢/份缓冲后净 ≤0；或 SPC 归档多边形与平台结算不一致 >0；或前向连续 30 个有信号事件净 ≤0。样本不足时只报告，不调阈值补样本。

## 成本与容量

- 费率：天气 0.05（GUIDE §8；市场 `feeSchedule.rate=0.05`）。每份费 = `0.05×p×(1−p)`；p=0.08 时 0.37¢，p=0.011 时 0.05¢。半价差/滑点按 1¢/份计，另做 3¢、5¢ 敏感性。
- 资金占用：买入到 UMA 结算约 1–3 天（0100Z 最终展望→UMA 提案/挑战；未逐笔核对 UMA 时间戳）。
- 容量：严格口径 6 笔共 712.1 份、投入 $16.03；单笔最大 300 份（$3.30 @1.1¢）和 30 份（$6.00 @20¢）；最大单日成本 $9.61（2026-09-30）；宽口径 10 笔共 $16.93。即使放大 10 倍，单日也只有约 $100；**无法部署 5,000 USDT**。这是本条最大的硬伤。
- 月机会：62 天 7 个宽口径独立日事件、3 个严格日事件 → 每月约 3.5 个宽口径/1.5 个严格信号。

## 风险

- **预测风险**：0100Z 最终展望可能移出城市；样本 5/15 被移出。买入价 ≤0.25 时单笔最大亏损 25¢/份+费，损失有上限，但会连续出现（宽口径 10 笔里 5 笔是输的）。
- **执行风险**：历史只有成交价，没有盘口；第一笔 `BUY Yes` 可能只是很小的量，或我们看到的成交已被别人吃掉。单笔 20–300 份的容量说明深度很薄；挂单可能排不到，吃单可能把价格推高。
- **结算/规则风险**：最终展望的「scheduled 01:00 UTC update」以归档 `ISSUE` 为准（实际 00:35–01:02）；后续修订不采用。城市坐标是规则写死的，不能用城市中心/地图目测替代。极少数边界城市可能因坐标/多边形精度产生争议；本条 0/1,550 不一致，但样本只覆盖 2 个月。
- **平台风险**：市场 `restricted=true`，实际交易资格未验证；UMA 争议会锁仓 4–6 天；天气板块流动性薄。
- **数据风险**：SPC 归档页/GeoJSON 若改版或缺失，信号无法复现；GeoJSON 的 `Last-Modified` 可能比名义更新晚 30–60 分钟，前向执行必须等到文件真正可抓取，不能用名义 1630Z/2000Z 下单。

## 改进了什么

不适用。

## 门槛自查

1. **机制说得清**：**满足**。付钱的是把 SPC「2% 概率标签」当成城市 2% 概率、或没跟上 1630Z/2000Z 更新的交易者；固定 25 城、每天重开、市场薄，使这个口径差反复出现。边界是有预测风险的折价买入，不是无风险套利。
2. **有免费数据能检验**：**满足（数据量）**。SPC 归档 GeoJSON、Gamma 规则/结算、data-api 成交全部免费免密钥；62 个日事件/1,550 个市场/10,674 笔成交，结算校验 0/1,550 不一致。但符合低价 YES 信号的独立日只有 7 个（严格 3 个）。
3. **小资金能做**：**不满足**。单笔 20–300 份、全样本投入 $16.03（严格）/$16.93（宽），放大 10 倍也只有约 $100/日；无法部署 5,000 USDT，容量是结构性硬伤。
4. **不重复**：**满足**。与 dot-001（站点观测最高温尾部）、dot-002（集合预报误差）、muse 天气热门/冷门（温度市场）用的变量和结算源都不同；与 dot-004（已定事实后的报价收敛）的区别是 dot-004 要求事实与合同终局已逐字确认后才买，本条主臂在 0100Z 最终展望**之前**用 1630Z/2000Z 更新建仓，事实尚未最终确定，承担预测被修风险；与 muse-own-xmkt-resolution-lag 的区别同样是本条主臂赚展望更新时滞，不是 UMA 结算风险；本条的 0100Z 后臂被明确排除在主规则之外。
5. **扣成本后粗算够用**：**满足（粗算，样本小）**。严格 6 笔扣 0.05 费+1¢ 缓冲净 +$658.23（+$629.75 @5¢）；宽口径 10 笔净 +$674.71。赢面 0.906–0.980/份、输面 ≤0.218/份，盈亏平衡生存率约 7.0%，历史宽口径 5/10 生存；但只有 3–7 个独立日事件，不能当统计显著。
6. **两周内能检验**：**不满足**。两周约 14 个日事件、1–2 个低价信号；历史 62 天也只有 7 个宽口径/3 个严格独立日事件。要 30 个独立低价信号约需 8–9 个月（宽口径）或约 20 个月（严格口径）的前向记录。这是本条进待选区而非收录的主因。
7. **出处可查**：**满足**。SPC 归档页/zip、Gamma series/event、data-api 成交、GUIDE §8 均已给出 URL 和访问日期；脚本与 stdout 在 scratch/B22。

## 出处

- https://gamma-api.polymarket.com/series?slug=tornado-risk-daily — 访问 2026-10-20 — 已读（series id 12689，62 个事件，25 城/事件）
- https://gamma-api.polymarket.com/events?series_id=12689&closed=true&limit=100&offset=0 — 访问 2026-10-20 — 已读（事件/市场/规则/结算/费）
- https://gamma-api.polymarket.com/events?slug=which-cities-face-tornado-risk-on-september-30-2026 — 访问 2026-10-20 — 已读（示例事件，25 个市场，volume 4,935.38）
- https://www.spc.noaa.gov/products/outlook/archive/2026/day1otlk_20260930_1630.html — 访问 2026-10-20 — 已读（Updated 16:26:43 UTC；Valid 301630Z–011200Z）
- https://www.spc.noaa.gov/products/outlook/archive/2026/day1otlk_20260930_1630-geojson.zip — 访问 2026-10-20 — 已读（含 `torn.nolyr.geojson`，LABEL 0.02/0.05，ISSUE 16:26；HTTP Last-Modified 16:30:16）
- https://www.spc.noaa.gov/products/outlook/archive/2026/day1otlk_20260930_2000.html — 访问 2026-10-20 — 已读（Updated 19:58:05 UTC）
- https://www.spc.noaa.gov/products/outlook/archive/2026/day1otlk_20261001_0100.html — 访问 2026-10-20 — 已读（Updated 00:35:04 UTC；结算用次日 0100Z）
- https://www.spc.noaa.gov/products/outlook/day1otlk.html — 访问 2026-10-20 — 已读（Day-1 产品入口）
- https://data-api.polymarket.com/trades?market=0x4ea215eb9352e9723fed1435ab9824c2cb15a439bcc28c0980a2b02fea84839b&limit=1000 — 访问 2026-10-20 — 已读（Wichita 市场成交，含 16:33:41 @0.05 SELL Yes、16:50:35 @0.08 BUY Yes）
- https://data-api.polymarket.com/trades?market=0x84cba6ff32d9afc8012f76e83d9c269c0f1c1d0c77c4ffde66b5396ab5a94391&limit=1000 — 访问 2026-10-20 — 已读（Columbus 市场成交，含 16:57:25 @0.01、42 份）
- GUIDE.md §8（Polymarket 费率/公开数据） — 访问 2026-10-20 — 已读
- bots/quant/notes/scheduler/scratch/B22/reproduce.py、reproduce.out、fetch_headers.py — 2026-10-20 — 已读（本条所有数字的复跑脚本与 stdout）
