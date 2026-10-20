# S3 — 第三批 Polymarket 模板候选短名单（预研，未回测）

- 机器人：quant｜日期：2026-10-20（UTC）｜性质：**预研**，不含任何收益结论
- 目标：为 round 2 找出**未被我们或别人碰过**、且"同一问题模板重复出现、有大量已结算事件"的 Polymarket 市场族
- 本轮**没有**做任何回测、没有估计任何 edge。文中所有数字均来自本轮实际发出的 GET 请求或实际运行的脚本（脚本与原始输出见最后一节 VERIFICATION LOG）
- 已读：`/workspace/trdproj-bots/GUIDE.md` 第 2、7、8、10、11 节；`templates/ENTRY.md`；`known/KNOWN.md`（135 条）；`bots/quant/CLAIMS.md`（B01–B20、Q04）；`bots/{dot,muse}/CLAIMS.md`

---

## 0. 方法与被排除范围

**接口**（全部 keyless 公开 GET）：

| 用途 | URL |
|---|---|
| 标签列表 | `https://gamma-api.polymarket.com/tags?limit=100&offset=N`（本轮取到 600 个标签） |
| 系列（同一模板的重复事件） | `https://gamma-api.polymarket.com/series?limit=100&offset=N`（本轮取到 **1254** 个 series） |
| 已结算事件 | `https://gamma-api.polymarket.com/events?tag_slug=<tag>&closed=true&limit=100&offset=N`、`/events?series_id=<id>&closed=true&limit=100&offset=N` |
| 搜索 | `https://gamma-api.polymarket.com/public-search?q=...` |
| 价格历史 | `https://clob.polymarket.com/prices-history?market=<tokenId>&interval=max&fidelity=60` |

**已排除（题目给定 + 查重）**：城市日最高温、全球气温、GDP/CPI/宏观 nowcast、民调、政治官宣、截止日时间衰减、新闻过度反应、长尾偏差、挂单奖励、完整集合、跨场所、单调阶梯、加密价格对期权、提及词、发帖数、网球、足球平局、F1、AI 榜单、App Store、流媒体榜、票房/奖项、烂番茄、地震、麻疹、海峡过境、财报超预期、SPX 收盘、代币 FDV、交易所上线、伤病。`known/KNOWN.md` 中的 `M-M4-poly-rewards`、`A-A5-poly-complete-set`、`A-A3-poly-cross-market`、`V-V2-poly-longshot` 亦在排除内。

**本轮主动放弃的候选**（看过但没进榜，理由见第 3 节）：NHL/NBA 老式 dailies、FX/黄金/原油/NDX "Daily Up or Down"、`#1 Spotify Song`/`#1 Netflix`、`Highest Grossing Movie Weekly`、`First Week Album Sales`、`H200 Rental Price`、`Counter-Strike Knife Index`。

---

## 1. 一个必须写在前面的通用发现（影响所有候选）

**CLOB 价格历史只保留最近约 2–3 周；更早的已结算市场一律返回 0 个点。**

- 随机抽 14 个"最近 1 天内结算"的事件：**14/14 有价格历史**（20–304 点）
- 按月抽：2026-10-06 结算 6/8 有；2026-10-01 结算 5/8 有；**2026-09-01 结算 0/8**；2026-08、2026-06、2026-02、2025-09、2024-06 各抽 3 个，**全部 0**
- 结论：任何候选都**无法**直接用历史 CLOB 价格做回测；只能（a）从今天起往前记录盘口/价格，或（b）用结算结果做纯基准率检验。这和 GUIDE 第 8 节"历史盘口没有公开来源"一致，但比它更严格：**连成交价历史也会在 2–3 周后消失**。

因此下面每个候选的"价格历史"一栏统一写实测点数，**不要**把它当成该候选的差异化优势。

---

## 2. 候选短名单（按 独立结果/2周 → 数据可得性 → 价格历史 排序）

| 排名 | 候选模板（tag / series） | 独立结果/2周（估） | 免费数据 | 价格历史（实测） | 吃单费率 | 一句话机制 |
|---:|---|---|---|---|---:|---|
| 1 | NFL 单场胜负（`nfl-gameday`，series `nfl-2026` id=12185） | ~32 场 | ESPN ✅ | ✅ 659/677 点 | 0.03 | 娱乐资金压主队/大牌，收盘前向模型收敛 |
| 2 | NCAA 大学橄榄球单场（tag `cfb`，series `cfb` id=10002） | ~100 场（未逐场核实） | ESPN ✅ | 未查到（当前赛季样本） | 未查到（旧市场 `feesEnabled=false`） | 同 NFL，但定价更粗、信息更慢 |
| 3 | MLB 单场胜负（tag `mlb`，series id=3） | ~200 场（赛季内） | MLB StatsAPI ✅ | ✅ 62/167 点 | 0.05 | 先发投手公开信息 + 牛棚使用的定价滞后 |
| 4 | "今天哪些城市在龙卷风风险区"（series `tornado-risk-daily` id=12689） | ~31 个事件 | NOAA SPC ✅ | ✅ 11/13 点 | 0.05 | 结算源 SPC outlook 一天多次更新，市场跟进慢 |
| 5 | CS2 / Dota2 单场比赛（series `counter-strike` id=10310、`dota-2` id=10309） | ~280 / ~110 场 | ❌ 未查到 keyless 结果/评分源 | ✅ 218/228 点 | 0.05 | 冷门赛事盘口信息稀薄，模型/评级可定价 |
| 6 | 板球单场胜负（tag `cricket`，series `ipl` id=44） | ~10–70 场 | Cricsheet ✅（历史） | ✅ 24 点 | 0.05 | T20 高方差 + 公开球球数据评级，市场用名气定价 |
| 7 | TSA 周客运量分档（series `tsa-passengers` id=10716） | 2 个事件 | TSA.gov ✅ | ❌ 0 点（已过期） | 0.05 | 日度吞吐已公布 → 周合计可提前 2–4 天定档 |
| 8 | 干旱 D4 州名单/州数（series `drought-d4-weekly` id=12688） | 2 个事件 | US Drought Monitor ✅ | ✅ 168/168 点 | 0.05 | 周四发布前的州级延续性 + 边界阈值 0.05% |
| 9 | FDA 批准截止日（series `fda-approval` id=10133） | ~1.8 个事件 | openFDA ✅ | ❌ 0 点（已过期） | 未查到（旧市场 `feeSchedule=null`） | PDUFA 日期 + AdComm 基准率，市场对"延期"定价不足 |
| 10 | 鸡蛋月度价格分档（series `egg-prices-monthly` id=10035） | 0.5 个事件 | BLS API ✅ | ❌ 0 点（已过期） | 未查到（`feeSchedule=null`） | FRED/BLS 发布前用批发蛋价 nowcast（**与宏观 nowcast 同族，重复风险高**） |

> "独立结果/2 周"是我的**推算**，依据是该 series 的实际事件数与日期跨度（见各条），不是实测交易机会数。

---

## 3. 逐条细节

### 1) NFL 单场胜负（moneyline）

- **tag/slug 模式**：tag `nfl-gameday`；slug `nfl-<away3>-<home3>-YYYY-MM-DD`；series `nfl-2026`（id=12185，`recurrence: daily`）
- **示例**：`nfl-was-sf-2026-10-20`（Commanders vs. 49ers，327 个市场/含让分与总分）、`nfl-hou-jax-2026-10-18`、`nfl-chi-atl-2026-10-18`
- **已结算数量/区间**：`tag_slug=nfl&closed=true` 分页到 **1200 个即触及我的分页上限**（未封顶），累计成交量 **2,483,354,222**；endDate 区间打印为 `..2026-12-31`（**首日为空值，未取到**，不猜）。series `nfl` 在 `series` 列表里只回传最近 ~10 个事件，**不能**用它计数
- **规则原文（引）**：`This market will resolve to "Commanders" if Commanders win the game. ... Overtime is included if played. If the game ends in a tie, this market will resolve 50-50. If the game is postponed, this market will remain open until the game has been completed. If the game is canceled entirely, with no make-up game, this market will resolve 50-50.` 结算源：`https://www.nfl.com/scores`
- **免费数据源**：ESPN 记分板 `https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?dates=20261019` → **HTTP 200, 22,990 bytes**（本轮实测）
- **价格历史**：`nfl-hou-jax-2026-10-18` **659 点**，`nfl-chi-atl-2026-10-18` **677 点**，`nfl-was-sf-2026-10-20` **702 点**
- **feeSchedule**：`{"rate":0.03,"takerOnly":true,"rebateRate":0.15}`
- **候选机制（一行）**：用公开 Elo/EPA 模型给赛前 moneyline 定价，赚"娱乐盘压大牌/主队"造成的 3–5 分钱偏差；费率仅 0.03（体育板块最低档）

### 2) NCAA 大学橄榄球单场

- **tag/slug 模式**：tag `cfb`；slug `cfb-<team>-vs-<team>`、让分版 `cfb-<team>-10pt5-vs-<team>`；series `cfb`（id=10002）、`cfb-2025`（id=10210）
- **示例**：`cfb-florida-st-vs-georgia-tech`（2024-08-24）、`cfb-florida-st-10pt5-vs-georgia-tech`
- **已结算数量/区间**：`tag_slug=cfb&closed=true` **1200 个（分页上限）**，累计量 **550,239,524**；样本里 endDate 到 `2026-12-30`
- **规则原文（引）**：`If the Florida State Seminoles win, the market will resolve to "Florida St." ... If the game is not completed by August 31, 2024 (11:59 PM ET) or it ends in a tie, the market will resolve 50-50.`
- **免费数据源**：`https://site.api.espn.com/apis/site/v2/sports/football/college-football/scoreboard?dates=20261003` → **HTTP 200, 873,603 bytes**（注意：路径写成 `sports/college-football/...` 会 404，正确路径含 `football/`）
- **价格历史**：**未查到**——我能拿到的示例是 2024 年市场，按第 1 节结论必然 0 点；当前赛季的 cfb 事件在 `series_id` 过滤下取回 0 条
- **feeSchedule**：示例市场 `feesEnabled=false`、`feeSchedule=null`（2024 年尚未启费）；GUIDE 第 8 节给的体育板块区间是 0.03–0.05，**当前实际费率未查到**
- **候选机制**：大学盘公开评级（SP+/FPI/Elo）与市场价的偏差比 NFL 更大，且周六同时上百场、容量分散

### 3) MLB 单场胜负

- **tag/slug 模式**：tag `mlb`；slug `mlb-<away3>-<home3>-YYYY-MM-DD`（事件内 30 个市场：胜负、让分、总分、单局）；series `mlb`（id=3，`recurrence: daily`）
- **示例**：`mlb-atl-lad-2026-10-04`（Braves vs. Dodgers）、`mlb-2026-al-central-champion`
- **已结算数量/区间**：series id=3 分页取到 **2000 个（我的上限）**，endDate `2020-10-29..2025-09-27`，累计量 **467,787,031**；`tag_slug=mlb` 另取到 1200 个（上限）
- **规则原文（引）**：`This market will resolve to "Atlanta Braves" if the Atlanta Braves win the game. ... If the game is postponed, this market will remain open until the game has been completed.` 结算源：`https://www.mlb.com/`
- **免费数据源**：MLB 官方 StatsAPI `https://statsapi.mlb.com/api/v1/schedule?sportId=1&date=2026-06-01` → **HTTP 200, 12,086 bytes**；ESPN `.../baseball/mlb/scoreboard?dates=20261001` → **HTTP 200, 20,985 bytes**
- **价格历史**：`mlb-atl-lad-2026-10-04` **62 点**；`mlb-2026-al-central-champion` **167 点**
- **feeSchedule**：`{"rate":0.05,"takerOnly":true,"rebateRate":0.15}`（注意：NFL 是 0.03，MLB 实测 0.05，**不要按板块一刀切**）
- **候选机制**：先发投手/牛棚可用性等公开信息在赛前数小时才确定，市场对"临场换投/打线"的调整慢半拍；0.05 费率要求偏差 ≥ 约 2.5 分（p=0.5 时 fee=0.05×0.25=1.25% 本金）

### 4) 每日"哪些城市在龙卷风风险区"

- **series**：`tornado-risk-daily`（id=12689，`recurrence: daily`）；slug `which-cities-face-tornado-risk-on-<month>-<day>-<year>`
- **示例**：`which-cities-face-tornado-risk-on-august-19-2026`、`...-october-15-2026`、`...-october-16-2026`
- **已结算数量/区间**：**62 个事件**，endDate `2026-08-20..2026-10-20`，累计量 **410,599**；每个事件 25 个市场（25 个城市）
- **规则原文（引）**：`This market will resolve to "Yes" for each listed city that falls within a tornado probability area rated ≥2% in the NOAA Storm Prediction Center Day 1 Convective Outlook on August 19, 2026. ... The SPC Day 1 Convective Outlook assigns tornado probability percentages (2%, 5%, 10%, etc.) to geographic areas`；结算源 `https://www.spc.noaa.gov/products/outlook/day1otlk.html`
- **免费数据源**：SPC Day1 outlook GeoJSON `https://www.spc.noaa.gov/products/outlook/day1otlk_cat.nolyr.geojson` → **HTTP 200, 2,027 bytes**（本轮抓时无风险区，故很小）；outlook 页面本身 200
- **价格历史**：`...-october-15-2026` **11 点**、`...-october-16-2026` **13 点**（薄）
- **feeSchedule**：`{"rate":0.05,"takerOnly":true,"rebateRate":0.25}`
- **候选机制**：结算完全由**当天 12Z/1630Z/2000Z/0100Z 多次更新**的 SPC 产品决定，而市场按"昨天"的信息定价 → 赚"结算源已更新、盘口未更新"的窗口；独立结果按事件（每天 1 个）
- **容量警告**：单事件成交量约 **2,492**（示例事件），几乎无深度

### 5) CS2 / Dota2 单场比赛

- **series**：`counter-strike`（id=10310）、`dota-2`（id=10309），均 `recurrence: daily`；slug `cs2-<teamA>-<teamB>-YYYY-MM-DD`、`dota2-<teamA>-<teamB>-YYYY-MM-DD`
- **示例**：`cs2-mibr-bcg-2026-10-15`、`cs2-hero-envy-2026-10-15`、`dota2-perrito-panzon-estar-backs-2025-09-23`
- **已结算数量/区间**：CS2 **2000 个（上限）**，endDate `2025-09-24..2026-02-15`，累计量 **225,745,246**；Dota2 **2000 个（上限）**，`2025-09-24..2026-06-04`，累计量 **425,522,355**。按跨度推算约 **280 / 110 个事件每 2 周**
- **规则原文（引）**：`This market will resolve to "MIBR" if MIBR win against BC.Game Esports in the named Counter-Strike match. ... If the game is canceled entirely, with no make-up game, this market will resolve 50-50.` 结算源示例：`https://kick.com/stake_pulse`、`https://www.liquipedia.net/dota2/Main_Page`
- **免费数据源**：**未查到** keyless、可批量取历史比赛结果/评级的源（Liquipedia 有 API 但要求合规 UA 与限速，HLTV 需抓取；本轮未验证，不写成结论）
- **价格历史**：`cs2-mibr-bcg-2026-10-15` **218 点**、`cs2-hero-envy-2026-10-15` **228 点**
- **feeSchedule**：`{"rate":0.05,"takerOnly":true,"rebateRate":0.15}`
- **候选机制**：二三线赛事盘口由少量知情者定价，公开评级（Elo/Glicko）与盘口偏离大；但**没有免费结果数据就无法检验**，因此只排第 5

### 6) 板球单场（IPL / T20 国际赛）

- **tag/slug 模式**：tag `cricket`；IPL slug `ipl-<tla>-<tla>-YYYY-MM-DD`；国际赛 `crint-<a>-<b>-YYYY-MM-DD-<prop>`；series `ipl`（id=44）
- **示例**：`ipl-rcb-rr-2025-04-24`、`crint-cym-ber-2026-09-27-most-sixes`、`crint-cym-ber-2026-09-27-team-top-batter`
- **已结算数量/区间**：series `ipl` **98 个**，endDate `2023-03-31..2025-06-03`，累计量 **2,838,140**；`tag_slug=cricket` **1200 个（上限）**，`2024-06-10..2026-05-31`，累计量 **35,003,391**
- **规则原文（引）**：`If the Royal Challengers Bangalore win, the market will resolve to "Royal Challengers Bangalore". ... If the game is postponed, this market will remain open until the game has been completed.`；国际赛 prop 结算源 `https://www.espncricinfo.com/`
- **免费数据源**：Cricsheet 全量 `https://www.cricsheet.org/downloads/all_json.zip` → **HTTP 200, 147,884,302 bytes**；IPL 专项 `https://www.cricsheet.org/downloads/ipl_json.zip` → **HTTP 200, 5,187,770 bytes**（球球数据，可自建评级）。ESPNcricinfo 首页 **403**（不可直接抓）
- **价格历史**：`crint-cym-ber-2026-09-27-most-sixes` **24 点**；`ipl-rcb-rr-2025-04-24` **0 点**（已过期）
- **feeSchedule**：`{"rate":0.05,"takerOnly":true,"rebateRate":0.15}`
- **候选机制**：T20 单场方差极大、盘口多用"球队名气/近期比分"定价，用 Cricsheet 球球数据算出的场地/打线评级可以给出更准的概率；独立结果按比赛计

### 7) TSA 周客运量分档

- **series**：`tsa-passengers`（id=10716，`recurrence: daily` 但事件是周窗口）；slug `number-of-tsa-passengers-<month>-<d>-<d>`、`total-number-of-tsa-passengers-november-23-30`
- **示例**：`number-of-tsa-passengers-may-18-may-24`、`number-of-tsa-passengers-june-29-july-5-20260626182033669`、`total-number-of-tsa-passengers-november-23-30`
- **已结算数量/区间**：**26 个事件**，endDate `2025-11-30..2026-07-05`，累计量 **1,260,362**；每个事件 7 个市场（`<17.5M / 17.5–18.0M / ... / >19.5M / 未报告`）
- **规则原文（引）**：`This market will resolve to the total number of TSA passengers reported between May 18, 2026 and May 24, 2026 (inclusive). The total number of TSA passengers will be calculated by summing all of the TSA daily checkpoint throughputs reported for this date range (e.g. if there were a daily TSA checkpoint throughput of 2 million reported on December 1 and a daily TSA checkpoint throughput of 3 million reported on December 2, the total number of TSA passengers for December 1-2 would be 5 million).`
- **免费数据源**：`https://www.tsa.gov/travel/passenger-volumes` → **HTTP 200, 195,641 bytes**（HTML 表，含每日吞吐；CSV 直链未查到）
- **价格历史**：`number-of-tsa-passengers-may-18-may-24` **0 点**、`...-june-29-july-5-...` **0 点**（均已超过 2–3 周保留窗口）
- **feeSchedule**：`{"rate":0.05,"takerOnly":true,"rebateRate":0.25}`（2026-05、2026-07 两个市场实测；2025-12 的市场 `feeSchedule=null`）
- **候选机制**：周合计 = 已公布的日度吞吐 + 剩余几天的"星期几 × 同比"预测；市场在最后 2–4 天常常没把已公布的日度数字折进分档概率
- **提示**：series 最后一个事件 endDate 2026-07-05，**该模板是否还在继续上新未查到**（近 3 个月未见新事件）

### 8) 干旱 D4 州名单 / 州数

- **series**：`drought-d4-weekly`（id=12688，`recurrence: weekly`）；slug `state-d4-drought-YYYY-MM-DD`、`states-in-d4-drought-YYYY-MM-DD`
- **示例**：`state-d4-drought-2026-09-01`（40 个州级市场）、`states-in-d4-drought-2026-09-01`（6 个档：`0 / 1-2 / 3-4 / 5-6 / 7-9 / 10+`）、`state-d4-drought-2026-10-13`
- **已结算数量/区间**：**16 个事件**（每周 2 个），endDate `2026-08-27..2026-10-15`（`/events` 与 `series_id` 两种取法打印的首日相差 2 天，以 `count_series.py` 输出为准），累计量 **90,086**
- **规则原文（引）**：`This market will resolve to "Yes" for each listed state that has D4 (Exceptional Drought) on 0.05% or more of its land area in the US Drought Monitor release for the week of September 1, 2026. ... D4 area below 0.05% is treated as cartographic noise at state borders and resolves "No". States appear only during the months in which they plausibly reach D4, so this event's roster changes through the year. 40 of the 48 coterminous states are in season for September`；州数市场：`Brackets: 0 / 1-2 / 3-4 / 5-6 / 7-9 / 10+. Exactly one bracket resolves "Yes".`
- **免费数据源**：US Drought Monitor 数据下载页 `https://droughtmonitor.unl.edu/DmData/DataDownload/ComprehensiveStatistics.aspx` → **HTTP 200, 587,046 bytes**；我猜的直连 CSV `.../data/csv/20260901_dmstatistics.csv` → **404**（准确 CSV 路径**未查到**，需从该页面按周取）
- **价格历史**：`state-d4-drought-2026-10-13` **168 点**、`states-in-d4-drought-2026-10-13` **168 点**；`state-d4-drought-2026-09-01` **0 点**
- **feeSchedule**：`{"rate":0.05,"takerOnly":true,"rebateRate":0.25}`
- **候选机制**：D4 面积是周频慢变量（周环比极少跳变），但市场对"某州首次进入 D4（跨 0.05% 阈值）"给的概率常偏离历史转移率；结算源固定为周四 USDM 发布，**发布时间已知**，可提前定位
- **弱点**：独立结果只有 **2 个/2 周**，凑 30 个独立结果需要 ~15 个月；只能进待选区或做"州级横截面"（但按 GUIDE 第 2 节，同周同数据源的州算同一个事件）

### 9) FDA 批准截止日

- **series**：`fda-approval`（id=10133，`recurrence: null`）；slug 多为 `<drug>-approval...`、`fda-approves-<company>-<drug>-for-<indication>`、`fda-approvals-in-<month>`
- **示例**：`fda-approves-gileads-lenacapavir-for-treating-hiv-human-immunodeficiency-virus`、`fda-approves-regenerons-dupixent-for-bullous-pemphigoid`、`fda-approvals-in-july`
- **已结算数量/区间**：**51 个事件**，endDate `2025-06-19..2026-07-30`，累计量 **431,746**
- **规则原文（引）**：`This market will resolve to "Yes" if the U.S. Food and Drug Administration (FDA) grants full or conditional approval for Gilead Sciences' new biologics license application (BLA) for lenacapavir as a treatment for Human Immunodeficiency Virus (HIV) by June 19, 2025, 11:59 PM ET. Otherwise, this market will resolve to "No."`
- **免费数据源**：openFDA `https://api.fda.gov/drug/drugsfda.json?limit=1` → **HTTP 200, 20,287 bytes**（可按批准日期检索，用于构造批准事件历史）
- **价格历史**：`...lenacapavir...` 等均 >2–3 周前结算 → **0 点**（示例实测该事件为旧市场）
- **feeSchedule**：示例市场 `feeSchedule=null`；当前费率**未查到**
- **候选机制**：PDUFA 日期是公开的，批准/延期/CRL 的历史基准率可按适应症与 AdComm 结果分桶；市场系统性高估"按时批准"

### 10) 鸡蛋月度价格分档（重复风险最高）

- **series**：`egg-prices-monthly`（id=10035，`recurrence: monthly`）；slug `price-of-dozen-eggs-in-<month>`
- **示例**：`price-of-dozen-eggs-in-september`、`price-of-dozen-eggs-in-january`
- **已结算数量/区间**：**17 个事件**，endDate `2025-02-12..2026-10-15`，累计量 **7,460,014**（本批候选里成交量最高）；每事件 6–8 个档
- **规则原文（引）**：`This market will resolve to the bracket within which the price for "Eggs, Grade A, Large (Cost per Dozen) in U.S. City Average" lies when the September data point is published by the St. Louis Fed (https://fred.stlouisfed.org/series/APU0000708111). The St. Louis Fed bases its numbers for egg prices on the BLS's CPI release.`
- **免费数据源**：BLS 公开 API `https://api.bls.gov/publicAPI/v2/timeseries/data/APU0000708111` → **HTTP 200, 3,053 bytes**（v2 匿名可用，日限流）；FRED CSV `https://fred.stlouisfed.org/graph/fredgraph.csv?id=APU0000708111` → **连接失败（curl 返回 000，0 字节，两次）**，不可用
- **价格历史**：`price-of-dozen-eggs-in-september`（2025-10-15 结算）**0 点**
- **feeSchedule**：示例市场 `feeSchedule=null`；当前费率**未查到**
- **候选机制**：CPI 发布前用 USDA 批发蛋价的月度均值 nowcast 上月零售均价
- **为什么排最后**：题目明确排除"GDP/CPI/宏观 nowcast"，这条本质是 **CPI 分项 nowcast**，只能当"更高频/更窄口径"的补充，不建议占用 round 2 名额

---

## 4. 看过但没进榜（附理由，避免下一轮重复劳动）

| 模板 | 实测 | 不进榜理由 |
|---|---|---|
| NHL（series id=4） | 203 事件，`2011-07-05..2023-04-03` | 事件太旧、当前无对应上新；体育族与 NFL/MLB 同机制 |
| NBA dailies（`nba-dailies-02112023` 等） | 搜索只回 2023 年 5 个 | 现赛季（2026-10 开季）盘口结构**未查到**，且与 NFL/MLB 同机制 |
| `Daily Up or Down`（金/银/油/气/NDX/DAX/FTSE/HangSeng/NFLX、FX 的 GBPUSD/USDJPY/USDCAD/USDKRW） | series 各 8–10 个事件，endDate 集中在 `2026-10-07..2026-10-19` | 与已覆盖的"SPX 收盘/加密价格"同族；且这类"当日涨跌"没有可用的历史盘口，只能是抛硬币 |
| `#1 Spotify Song`（id=?), `#1/#2 Netflix Show/Movie`、`Highest Grossing Movie Weekly` | 11 / 9 / 9 / 8 个事件 | 流媒体榜、票房已被覆盖 |
| `First Week Album Sales`（id=12328） | 19 事件，`2026-05-22..2027-01-01`，成交量 617,228 | 结算源 Hits Daily Double（`https://hitsdailydouble.com/` HTTP **200, 927,224 bytes**）但具体销量在站内页面，**可编程取数未查到** |
| `H200 Rental Price`（id=11550） | 6 事件 | 事件太少，GPU 租金无免费公开时间序列（**未查到**） |
| `Counter-Strike Knife/Doppler/Case index`（id=10810–10815） | 每周多档 | 标的指数来源（第三方皮肤指数）**未查到**免费历史 |
| `Monthly Tornadoes US`（id=10724） | 10 事件，`2025-12-08..2026-08-01`，成交量 1,748,625；规则：按 NCEI 最终数据集月度计数 | 独立结果 0.5 个/2 周；结算源链接 `https://www.ncei.noaa.gov/access/monitoring/tornadoes/time-series/us` 本轮 **404**（`https://www.spc.noaa.gov/climo/online/monthly/newm.html` 200 但那是初步计数）；`spc.noaa.gov/wcm/` **502**。进待选区，不进前 10 |
| `Flu Hospitalization Rate Week` | 10 事件 | 与已覆盖的麻疹/CDC 周计数同机制 |
| `Will [state] reach D4 by <date>`（`drought` tag 下 37 事件） | — | 属于"截止日型"，与已排除的时间衰减族重叠；本轮只取周频 D4 事件 |

---

## 5. 下一轮（round 2）建议的取数顺序

1. **NFL / MLB 单场**：先用 ESPN/StatsAPI 结果算基准率与"模型 vs 收盘价"偏差——但**注意第 1 节：没有历史盘口**，只能从今天起记录 → 需要先写"记录脚本 + 预注册规则"（在拿到任何价格前定死：模型、阈值、费率、最小偏差）。
2. **tornado-risk-daily**：事件量最大（62/2 月）、数据最干净、结算源明确，最适合验证"结算源更新 → 盘口滞后"；先测 25 城 × 60 天的基准率与盘口是否真的滞后（需前向记录，历史盘口已消失）。
3. **TSA 周合计**：数据最可靠，但**先确认模板是否还在上新**（series 最后事件 2026-07-05），不在上新就直接放弃。
4. **CS2/Dota2**：先解决免费结果/评级数据源，否则不投入。

**预注册声明**：本轮只做模板发现，没有跑任何收益/校准计算，因此不涉及"结果前预设"。round 2 开工前必须把规则、参数、样本切分（先 out-of-sample：例如用 series 里较早的 60% 事件定参数、后 40% 检验）写进条目，再取数。

---

## 6. VERIFICATION LOG

所有命令在 `/workspace/agent-tools/quant-r2prep/work_S3` 下执行；时间 2026-10-20 UTC。`curl` 统一带 `-sL -A "Mozilla/5.0" --max-time 30`。

### V1 标签与 series 总量

```
$ python3 scan_tags.py
tags total 600
done 600
$ python3 scan_series.py
series 1254
```

（`scan_tags.py` 分页取 `/tags`；`scan_series.py` 分页取 `/series` 并把 `events[].closed` 计数，**注意**：`/series` 回传的事件数组只有最近约 10 个，不能当全量计数，故改用 `series_id` 分页。）

### V2 事件计数（tag 维度，脚本 `count_tag.py`，分页至 1200 或空）

```
$ python3 count_tag.py nba nfl mlb nhl ipl cricket tsa-passengers tornado drought egg-prices cfb ncaa-basketball
nba	HTTP 200	events=1200	2024-04-16..2025-12-31	vol=2581475502
  ex: ['nba-play-in-lakers-vs-pelicans', 'nba-play-in-warriors-vs-kings', 'nba-play-in-heat-vs-76ers']
nfl	HTTP 200	events=1200	..2026-12-31	vol=2483354222
  ex: ['nfl-draft-top-5-picks', 'steelers-week-1-starter', '2024-nfl-draft-2nd-pick']
mlb	HTTP 200	events=1200	..2025-11-21	vol=239076059
nhl	HTTP 200	events=1200	..2026-06-30	vol=545315997
ipl	HTTP 200	events=94	2025-03-23..2026-06-06	vol=8090652
cricket	HTTP 200	events=1200	2024-06-10..2026-05-31	vol=35003391
tsa-passengers	HTTP 200	events=0	..	vol=0
tornado	HTTP 200	events=0	..	vol=0
drought	HTTP 200	events=37	2026-08-27..2026-11-01	vol=256981
egg-prices	HTTP 200	events=0	..	vol=0
cfb	HTTP 200	events=1200	..2026-12-30	vol=550239524
  ex: ['college-football-champion-2025', 'cfb-florida-st-vs-georgia-tech', 'cfb-florida-st-10pt5-vs-georgia-tech']
ncaa-basketball	HTTP 200	events=1200	2025-11-03..2026-04-04	vol=42820561
```
（`tsa-passengers`/`tornado`/`egg-prices` 作为 **tag** 不存在 → 0；改用 series。）

### V3 事件计数（series 维度，脚本 `count_series.py`）

```
$ python3 count_series.py nba-2026 nfl-2026 mlb nhl ipl tsa-passengers drought-d4-weekly monthly-tornadoes-us tornado-risk-daily egg-prices-monthly fda-approval first-week-album-sales h200-rental-price counter-strike dota-2
nba-2026 NOT IN SERIES LIST
nfl-2026 NOT IN SERIES LIST
mlb (id=3, rec=daily)	events=2000	2020-10-29..2025-09-27	vol=467787031
nhl (id=4, rec=daily)	events=203	2011-07-05..2023-04-03	vol=686571
ipl (id=44, rec=daily)	events=98	2023-03-31..2025-06-03	vol=2838140
tsa-passengers (id=10716, rec=daily)	events=26	2025-11-30..2026-07-05	vol=1260362
drought-d4-weekly (id=12688, rec=weekly)	events=16	2026-08-27..2026-10-15	vol=90086
monthly-tornadoes-us (id=10724, rec=monthly)	events=10	2025-12-08..2026-08-01	vol=1748625
tornado-risk-daily (id=12689, rec=daily)	events=62	2026-08-20..2026-10-20	vol=410599
egg-prices-monthly (id=10035, rec=monthly)	events=17	2025-02-12..2026-10-15	vol=7460014
fda-approval (id=10133, rec=None)	events=51	2025-06-19..2026-07-30	vol=431746
first-week-album-sales (id=12328, rec=None)	events=19	2026-05-22..2027-01-01	vol=617228
h200-rental-price (id=11550, rec=monthly)	events=6	2026-05-31..2026-10-01	vol=327228
counter-strike (id=10310, rec=daily)	events=2000	2025-09-24..2026-02-15	vol=225745246
dota-2 (id=10309, rec=daily)	events=2000	2025-09-24..2026-06-04	vol=425522355
```
（`nfl-2026` 只存在于事件的 `series` 内嵌对象里（id=12185），不在 `/series` 列表分页中——本轮取到 1254 个 series 仍未包含它，**这是 Gamma 列表接口的不一致，已记录，未进一步解释**。）

### V4 价格历史保留窗口（脚本 `pricehist_test.py` / `cutoff.py`）

```
# 随机 14 个最近结算事件：14/14 有点
   24  2026-10-20  doge-updown-15m-1792461600
  304  2026-10-19  ukr1-met-liv-2026-10-19
nonzero 14 of 14

# 按月抽样（每桶最多 3 个事件）
2026-08-01 2026-08-31 HTTP 200 n 100 -> pts 0 taylor-swift-pregnant-before-marriage
2026-06-01 2026-06-30 HTTP 200 n 100 -> pts 0 2025-us-open-golf-winner
2026-02-01 2026-02-28 HTTP 200 n 100 -> pts 0 super-bowl-champion-2026-731
2025-09-01 2025-09-30 HTTP 200 n 100 -> pts 0 who-will-make-the-basketball-hall-of-fame
2024-06-01 2024-06-30 HTTP 200 n 100 -> pts 0 will-trump-tweet-again-by-june-1
2026-09-01 nonzero 0 / 8
2026-10-01 nonzero 5 / 8   (如 min-arctic-sea-ice-extent-this-summer 296 点)
2026-10-06 nonzero 6 / 8
```

### V5 逐候选价格历史测试（脚本 `ph2.py`）

```
$ python3 ph2.py
nfl ('nfl-hou-jax-2026-10-18', 659, '2026-10-18')
nfl ('nfl-chi-atl-2026-10-18', 677, '2026-10-18')
mlb ('mlb-atl-lad-2026-10-04', 62, '2026-10-12')
mlb ('mlb-2026-al-central-champion', 167, '2026-10-11')
tornado-risk-daily ('which-cities-face-tornado-risk-on-october-15-2026', 11, '2026-10-16')
tornado-risk-daily ('which-cities-face-tornado-risk-on-october-16-2026', 13, '2026-10-17')
drought ('state-d4-drought-2026-10-13', 168, '2026-10-15')
drought ('states-in-d4-drought-2026-10-13', 168, '2026-10-15')
cs2 ('cs2-mibr-bcg-2026-10-15', 218, '2026-10-15')
cs2 ('cs2-hero-envy-2026-10-15', 228, '2026-10-15')
cricket ('crint-cym-ber-2026-09-27-most-sixes', 24, '2026-10-04')
egg ('price-of-dozen-eggs-in-september', 0, '2025-10-15')
```
TSA 两个市场（`number-of-tsa-passengers-may-18-may-24`、`...-june-29-july-5-20260626182033669`）实测 **0 点**，`feeSchedule.rate=0.05`。

### V6 规则原文与费率（`probe.py`、`facts.py` 及逐条 `events?slug=`）

- NFL `nfl-was-sf-2026-10-20`：327 个市场，`fee={"rate":0.03,"rebateRate":0.15}`，`resolutionSource=https://www.nfl.com/scores`，价格历史 **702 点**
- MLB `mlb-atl-lad-2026-10-04`：30 个市场，`fee={"rate":0.05,"rebateRate":0.15}`，`resolutionSource=https://www.mlb.com/`
- 板球 `ipl-rcb-rr-2025-04-24`：`feeSchedule=null`
- CS2 `cs2-mibr-bcg-2026-10-15`：`fee={"rate":0.05,"rebateRate":0.15}`，`resolutionSource=https://kick.com/stake_pulse`
- Dota2 `dota2-perrito-panzon-estar-backs-2025-09-23`：`feeSchedule=null`，`resolutionSource=https://www.liquipedia.net/dota2/Main_Page`
- Drought `state-d4-drought-2026-09-01`：40 个市场；`states-in-d4-drought-2026-09-01`：6 个档；均 `rate=0.05, rebateRate=0.25`
- Tornado 日更：`rate=0.05, rebateRate=0.25`，`resolutionSource=https://www.spc.noaa.gov/products/outlook/day1otlk.html`
- TSA：7 个档（`<17.5M / 17.5–18.0M / 18.0–18.5M / 18.5–19.0M / 19.0–19.5M / >19.5M / 未报告`）
- 鸡蛋：`resolutionSource` 指向 FRED `APU0000708111`
- 月度龙卷风：`Only tornadoes appearing in the final NCEI dataset for that month will count.`

### V7 免费数据源连通性（curl，HTTP / 字节 / 用时）

```
https://www.tsa.gov/travel/passenger-volumes                                              200 195641
https://www.spc.noaa.gov/climo/online/monthly/newm.html                                   200 29948
https://droughtmonitor.unl.edu/DmData/DataDownload/ComprehensiveStatistics.aspx            200 587046
https://www.bls.gov/regions/mid-atlantic/data/averageretailfoodandenergyprices_usandwest_table.htm  403 1325
https://open.fda.gov/apis/                                                                200 118692
https://statsapi.mlb.com/api/v1/schedule?sportId=1&date=2026-06-01                       200 12086
https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?dates=20261019     200 22990
https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard?dates=20261019   200 4384
https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard?dates=20261001     200 20985
https://site.api.espn.com/apis/site/v2/sports/college-football/scoreboard?dates=20261003 404 12           ← 错误路径
https://site.api.espn.com/apis/site/v2/sports/football/college-football/scoreboard?dates=20261003  200 873603
https://www.cricsheet.org/downloads/all_json.zip                                          200 147884302
https://www.cricsheet.org/downloads/ipl_json.zip                                          200 5187770
https://www.espncricinfo.com/                                                             403 372
https://www.spc.noaa.gov/products/outlook/day1otlk_cat.nolyr.geojson                     200 2027
https://www.spc.noaa.gov/wcm/                                                             502 122
https://www.ncei.noaa.gov/access/monitoring/tornadoes/time-series/us                      404 9938
https://droughtmonitor.unl.edu/data/csv/20260901_dmstatistics.csv                         404 1245
https://api.fda.gov/drug/drugsfda.json?limit=1                                            200 20287
https://api.bls.gov/publicAPI/v2/timeseries/data/APU0000708111                            200 3053
https://fred.stlouisfed.org/graph/fredgraph.csv?id=APU0000708111                          000 0        ← 连接失败，两次
https://hitsdailydouble.com/                                                              200 927224
```

### V8 本轮没查到（明确写"未查到"，不要猜）

- NCAA 当前赛季的 `feeSchedule` 实际费率（旧市场 `feesEnabled=false`）
- NBA / NHL 当前赛季单场盘的 slug 结构与费率
- TSA 周客运量模板是否仍在继续上新（最后一次 endDate=2026-07-05）
- US Drought Monitor 的稳定直连 CSV 路径（下载页 200，具体 CSV 404）
- NCEI 龙卷风月度最终计数的可编程 CSV（市场规则里的链接 404）
- CS2/Dota2 的 keyless 比赛结果/评级数据源
- First Week Album Sales 的可编程销量数字来源（站点 200，数字在页面内，未验证可解析）
- 任何候选的历史盘口（第 1 节：已结算市场 >2–3 周即 0 点）
