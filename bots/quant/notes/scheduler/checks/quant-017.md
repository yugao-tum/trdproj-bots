# quant-017 独立核查（checker w07）

核查对象：`bots/quant/entries/quant-017-app-store-rank-markets.md`（status `草稿`，未改动条目）。
核查时间：2026-10-20 UTC。脚本与缓存全部放在仓库外：`/tmp/c20261020-1423-research-w07/`（`cache/`、`out/`）。
结论：规则、CDX/基率、`Other` 基率、CLOB 覆盖和成本算术基本可复现；但 `#1` board 的“7 个真候选”名单把 **Google Gemini** 写成了 **McDonald's**，并因此列成了 8 个名字。需要改这两处（外加 `name_zh` 的一个重复字）。

## 1. 每个 URL 的重取结果

| # | URL（条目引用） | 本次结果 | 与条目对比 |
|---|---|---|---|
| 1 | `https://rss.applemarketingtools.com/api/v2/us/apps/top-free/50/apps.json` | HTTP 200，25,699 B，`updated=Tue, 20 Oct 2026 12:26:46 +0000`，50 条 | **OK / 随时间变化**。条目 25,783 B、`05:14:43`；两次抓取时间不同。前 5 名仍为 Capital One Mobile、Vinted、Muse from Meta、ChatGPT、TikTok Pro。 |
| 2 | `https://apps.apple.com/us/charts/iphone` | HTTP 200，1,018,512 B；HTML 内嵌顺序前 10 与当前 RSS 一致 | **OK / 大小随时间变化**。条目 1,017,064 B；名字顺序一致。 |
| 3 | `https://web.archive.org/cdx/search/cdx?url=apps.apple.com%2Fus%2Fcharts%2Fiphone&output=json&fl=timestamp,statuscode,length&filter=statuscode:200&collapse=digest` | HTTP 200，150,321 B；**4,295** 个 200 快照；首个 `20220604145458`，最后 `20251103152602`；按年 2022=18、2023=28、2024=2,648、2025=1,601；**454** 个 UTC 日期 | **OK，逐项一致**（`out/` 无单独文件，见本节命令输出）。 |
| 4 | `https://web.archive.org/web/20250101050435id_/https://apps.apple.com/us/charts/iphone` | HTTP 200；gzip 解压后 **751,307 B**；`schema:top-free` 第 1 位 = `CapCut - Video Editor` | **OK（内容）/ 字节数不同**。条目写 767,828 B；本次解压 751,307 B，首项一致。 |
| 5 | `https://web.archive.org/cdx/search/cdx?url=rss.applemarketingtools.com%2Fapi%2Fv2%2Fus%2Fapps%2Ftop-free%2F50%2Fapps.json&output=json&fl=timestamp,statuscode&limit=3` | HTTP 200，`[["timestamp","statuscode"],["20230522143120","200"]]` | **OK，一致**（只有 1 个快照）。 |
| 6 | `https://web.archive.org/cdx/search/cdx?url=itunes.apple.com%2Fus%2Frss%2Ftopfreeapplications%2Flimit%3D50%2Fjson&output=json&fl=timestamp,statuscode&limit=8` | HTTP 200，`[["timestamp","statuscode"],["20180107065423","200"]]` | **OK，一致**（只有 1 个快照）。 |
| 7 | `https://web.archive.org/cdx/search/cdx?url=apps.apple.com%2Fus%2Fcharts%2Fiphone%2Ffree-apps&output=json&fl=timestamp,statuscode&limit=8` | HTTP 200，`[]` | **OK，一致**（无快照）。 |
| 8 | `https://web.archive.org/cdx/search/cdx?url=apps.apple.com%2Fus%2Fapp-store%2Fcharts%2Fiphone&output=json&fl=timestamp,statuscode&limit=8` | HTTP 200，`[]` | **OK，一致**（无快照）。 |
| 9 | `https://gamma-api.polymarket.com/public-search?q=app%20store&limit_per_type=50&events_status=all&page=1..5` | 5 页均 HTTP 200；去重 **247** 个事件；`pagination.totalResults=247`；242 closed / 5 open；free 141 / paid 76 / other 30 | **OK，一致**。 |
| 10 | `https://gamma-api.polymarket.com/events?slug=1-free-app-in-the-us-apple-app-store-on-october-23-10172026` | HTTP 200，47,012 B；12 个市场；7 真候选 + 4 `Reserved` + 1 `Other`；`negRisk=true`、`restricted=true`、`feeType=culture_fees`、`rate=0.05`；规则原文见 §3 | **OK（规则）；价格/量随时间变化**。本次 volume 6,249.996237、liquidity 4,941.96658；条目 5,918.22 / 5,115.60。 |
| 11 | `https://gamma-api.polymarket.com/events?slug=2-free-app-in-the-us-apple-app-store-on-october-23-10172026` | HTTP 200，48,055 B；12 个市场；volume 3,197.808697、liquidity 1,937.82306；规则原文见 §3 | **OK（规则/volume）；liquidity 随时间变化**（条目 1,558.69）。 |
| 12 | `https://clob.polymarket.com/prices-history?market=<247 个事件的第一个 YES token>&interval=max&fidelity=60` | 247 个请求全部 HTTP 200；**21** 个事件 >0 点，**226** 个 0 点；其中 **16 closed / 5 open**；正点数的 closed 事件只落在 `2026-09-25`、`2026-10-02`、`2026-10-09`、`2026-10-16` 四个日期；这 16 个事件共 **196** 个市场，**92** 个有 >0 点、104 个 0 点 | **OK，逐项一致**。脚本：`/tmp/c20261020-1423-research-w07/clob_check.py`，输出 `out/clob_check.txt`。 |
| 13 | 通配符 CDX（`rss.applemarketingtools.com*`、`apps.apple.com/us/charts/iphone*` 等） | 多次 TLS `UNEXPECTED_EOF`，HTTP 000 | **未取到**；条目也标了 000/超时，未用于结论。 |

## 2. 数字重算

### 2.1 `#1` board 的报价与算术（用条目自己的快照数字）

条目表格的 7 个真候选：Muse .715、Vinted .06、ChatGPT .063、Claude .0315、KICK .01、Google Gemini .005、TikTok .0045。

- `ΣYES = .715+.06+.063+.0315+.01+.005+.0045 = 0.889` ✅
- `ΣbestBid = .71+.02+.05+.003+.002+.001+.001 = 0.787` ✅
- `ΣbestAsk = .72+.10+.076+.06+.018+.009+.008 = 0.991` ✅
- 全买 NO：`7 − 0.787 = 6.213`；NO 吃单费 `Σ 0.05·p·(1−p)`，`p=1−bid`，逐项和 `=0.0140`；净成本 `6.227`。
- 盈亏平衡：`P(Other)·(7−6.227) = (1−P(Other))·(6.227−6)` → `P(Other)=0.227 = 22.7%` ✅（条目 22.7%）。
- 用 `Other` 基率 `14/117=12.0%`，明确负 EV。✅

`#2` board：`7 − 0.362 = 6.638`；费 `0.01579`；净 `6.6538`；盈亏平衡 `P(Other)=0.6538 = 65.4%` ✅（条目 65.4%）。

### 2.2 EV 表（用 `P1=64/71=0.901408`、半价差 1.5¢）

`p=0.84`：费 `.05·.84·.16=.00672`，成本 `.84+.00672+.015=.86172`，EV `.901408−.86172=+.03969` → 条目 +4.0¢/+4.6% ✅
`p=0.88`：成本 `.88+.00528+.015=.90028`，EV `+.00113` → 条目 +0.1¢ ✅
`p=0.90`：成本 `.90+.0045+.015=.9195`，EV `−.01809` → 条目 −1.8¢/−2.0% ✅
盈亏平衡：解 `p+.05p(1−p)+.015=.901408` → `p≈.8813`，条目 0.881 ✅
`P1=87.04%` 时盈亏平衡约 `0.849`、+2% 门槛约 `0.828` ✅（与条目一致）。

### 2.3 `Other` 基率、频率、成交额

脚本 `/tmp/c20261020-1423-research-w07/app_stats.py`，输出 `out/app_stats.txt`：

```text
events 247
closed 242 open 5
free title 141 closed 139
weekly closed 117
other winners 14 rate 0.11965811965811966 by sub {'#1': [8, 63], '#2': [6, 54]}
reserved present 8 / 117
markets minmax 11 26
unique endDate dates 62
volume sum 7711531.657859
endDate months [('2025-10', 4), ('2025-11', 5), ('2025-12', 7), ('2026-01', 8), ('2026-02', 6), ('2026-03', 14), ('2026-04', 15), ('2026-05', 16), ('2026-06', 12), ('2026-07', 8), ('2026-08', 8), ('2026-09', 8), ('2026-10', 6)]
paid title 76 other 30
```

这与条目 `14/117=12.0%`、`#1 8/63=12.7%`、`#2 6/54=11.1%`、`8/117=6.8%`、`11–26` 个市场、`62` 个结算日、成交额 `7,711,532`、13 个月份计数全部一致。✅

### 2.4 Wayback P1/P2（本次重跑；条目 54/71 子样本）

脚本 `/tmp/c20261020-1423-research-w07/wb_stats.py`，输出 `out/wb_stats.txt`。窗口按半开区间 `[04:00,08:00)` / `[14:00,18:00)`（与条目 C0 的“120 个目标快照/60 天”复现一致）：

```text
strict days/targets 60 120 P1 (60, 53, 0.8833333333333333) P2 (17, 23, 0.7391304347826086)
relaxed days/targets 79 158 P1 (79, 71, 0.8987341772151899) P2 (25, 34, 0.7352941176470589)
top6 mean overlap 0.9029535864978903 min 0.3333333333333333 max 1.0 order same 14 / 79
```

- 条目预注册框：60 个双窗口日 / 120 张目标快照 ✅。
- 条目“解析 54 个、P1=47/54=87.0%”来自当时 6 张快照三次重试失败；本次重试后 120/120 全部解析，完整样本是 **53/60=88.3%**。条目 47/54 是合法子样本，但全样本更高，且差异 1.3pp，不改变结论。
- 放宽框：79 天 / 158 张 ✅；本次 158/158 全部解析，完整样本 **71/79=89.9%**；条目“71 天、P1=64/71=90.1%”是 8 张失败后的子样本，差异 0.3pp。
- P2：本次严格 `17/23=73.9%`、放宽 `25/34=73.5%`；条目 `15/21=71.4%`、`23/32=71.9%`，方向一致，差异来自失败快照。
- top-6 集合平均重合 **90.3%**（条目 90.4%），顺序完全相同 **14/79**（条目 12/71）；翻面例子 `2025-01-04 ChatGPT→Threads`、`2025-01-11 Watch Duty→Lemon8`、`2025-01-24 ChatGPT→Watch Duty`、`2025-03-05 Jimmy John's→ChatGPT` 全部复现。✅

### 2.5 候选名单：本次唯一明确的硬错误

本次 Gamma 实取：

- `#1` board 的 7 个真候选 = **Muse from Meta / Vinted / ChatGPT / TikTok Pro / Claude by Anthropic / Google Gemini / KICK**；**没有 McDonald's**。
- `#2` board 的 7 个真候选 = **Vinted / Muse from Meta / ChatGPT / TikTok Pro / Claude / McDonald's / KICK**；**没有 Google Gemini**。

条目表格本身是正确的（`#1` 表含 Google Gemini、不含 McDonald's；`#2` 表含 McDonald's、不含 Gemini），但正文两处写错：

- `## 规则` 的“结构”bullet：写成 `Vinted / Muse from Meta / ChatGPT / TikTok Pro / Claude / McDonald's / KICK`（把 Gemini 写成了 McDonald's）。
- `### 1）Apple 侧` 的“7 个真候选在 top-free-50 里的当前名次”列了 **8 个名字**：`Vinted 2、Muse 3、ChatGPT 4、TikTok 5、McDonald's 7、Claude 8、Google Gemini 9、KICK 不在 top 50`。McDonald's 不是 `#1` 候选，应删去。

这两处不影响 §2.1 的算术（算术用的是表格里的 7 个含 Gemini 的数字），但属于事实错误，需改。

## 3. 结算规则原文对照（live Gamma description）

逐句对照 `#1`/`#2` 事件 description（本次 HTTP 200）：

| 条目写法 | live 原文 | 判定 |
|---|---|---|
| “according to the iOS app, ranked #2 ... as of 12:00 PM ET on the specified date” | `This market will resolve according to the iOS app, ranked #2 in the United States on the iPhone Apple App Store's overall Top Charts under "Free Apps", as of 12:00 PM ET on the specified date.` | ✅ 逐字一致（`#1` 版把 #2 换成 #1）。 |
| “To find the overall chart ... (https://apps.apple.com/us/charts/iphone)” | `To find the overall chart, click "Apps" at the bottom of the US iOS App Store app, scroll down to "Top Free Apps" and click "See All". Then under "Free Apps" in the "Top Charts" section, you'll see the list that will be used as the resolution source to this market (https://apps.apple.com/us/charts/iphone).` | ✅ 要点一致；条目用 `...` 省略了 “that will be used as the resolution source to this market”。 |
| “If the chart is unavailable at 12:00 PM ET, this market may remain open for up to 48 hours ... If the data remains unavailable, this market will resolve according to the last published ranking.” | 同文 | ✅ 逐字一致。 |
| `negRisk=true`；12 个市场；7 真候选 + 4 `Reserved app 2..5` + 1 `Other`；5 个占位臂 `["0.5","0.5"]`、bid 0 / ask 1、volume 0 | 本次实取完全一致 | ✅ |
| `startDate=2026-10-17T21:06:16Z`；`endDate=2026-10-23T23:59:00Z` | `#2` 的 startDate 正是 `2026-10-17T21:06:16Z`；`#1` 是 `21:06:58Z`；两者 endDate 都是 `2026-10-23T23:59:00Z` | ✅（条目用 `#2` 做示例，已注明）。 |
| `endDate` 不是结算时刻；结算 = 2026-10-23 12:00 PM ET = 16:00 UTC（EDT=UTC−4） | 规则原文 “as of 12:00 PM ET”；2026-10-23 仍在 EDT | ✅ |
| `feeType="culture_fees"`、`feeSchedule rate=0.05`、`rebateRate=0.25` | 本次实取 `culture_fees` / `rate:0.05` / `takerOnly:true` / `rebateRate:0.25` | ✅；条目正确指出这不是 GUIDE 表里的 tech 0.04。 |
| `umaBond`/`umaReward` 未返回 | 本次两者均为 `None` | ✅ |
| `restricted=true` | 本次为 true | ✅ |

## 4. Look-ahead / 成本 / 独立性 / 容量

- **Look-ahead**：策略只要求在结算日 11:00–12:00 ET 读取当前 Apple 榜单；不使用 12:00 之后的数据。Wayback 的 2025 年 P1 只用作“10 小时翻面风险”的刻度，不是入场信号；历史快照有“必须有 AM+PM 两张”的选择条件（数据可得性条件），但不构成未来信息。✅ 无交易层面的 look-ahead。
- **成本**：吃单费 `0.05·p·(1−p)`；p=.90 时费/名义 0.50%，加半价差约 2.2%/笔；p=.98 时费 0.098¢ + 半价差 1.5¢ = 1.6¢，票面只剩 2¢，确实几乎没有空间。条目“只在 0.90–0.96、价差 ≤2¢ 的窄窗口做”与算术一致。✅
- **独立性**：同一天 `#1`/`#2` 共享同一次 12:00 ET 榜单快照，按日期只算 1 个；条目明确按日期计。近期约 5 个结算日/月 → 两周 2–3 个，**凑不到 30**。✅（这也是 gate 6 不满足的原因。）
- **容量**：条目快照的单臂 `liquidityNum` 123–546 USDC；本次 `#1` 为 509–1,092、`#2` 为 132–810 USDC（随时间变化）。单笔 ≤200 USDT、单日 ≤600 USDT，贴近单臂上限；5,000 USDT 放不满。✅
- **风险**：最后 1 小时榜单跳变、结算源网页与 RSS 非同一接口、`Other`/`Reserved` 不可成交、历史基率时代错配，条目都已写明。✅

## 5. 查重（known/ 与全部 bots/*/entries）

- `known/KNOWN.md` 无 App Store / App 排名 / 榜单快照条目。
- `bots/*/entries/` 相关：`quant-007`（月度 AI 榜首，arena.ai，月末 12:00 ET）、`quant-010`（Netflix/Spotify 周榜日更 nowcast）、`dot-001`（城市日最高温的日末观测尾部）、`muse-own2-tail-weather-expiry-favfade`（天气临到期热门买 NO）。这些都不是 App Store 榜单。
- 与 `quant-007` 同属“公开榜单 → 固定时刻排名市场”的机制家族，条目自己已标“可能被判变体，交主审”。关键差异：标的是 Apple 免费榜（同一榜单既是信号源又是结算源）、频率周度、negRisk 带 `Other` 兜底、有 117 个已关闭板的 `Other` 基率；与 `quant-010` 的“日榜推周榜”也不同源。**判为不重复但同族，gate 4 仍有中等风险。**
- 与 `quant-015` 无重叠。

## 6. 七条门槛

1. **机制说得清：满足**。付款方是结算日最后几十分钟仍按旧叙事报价的对手方；机制是固定时刻的一次公开榜单快照。单点横截面（Capital One 当前第 1 但不在候选、Muse 当前第 3 却报 .715）支持“价格未跟上榜单”，但不是收益证明。
2. **有免费数据能检验：部分满足 / 不确定**。榜单、规则、Gamma/CLOB 都免费可读；但收益侧只有 4 个独立结算日有 CLOB 历史（16 个已关闭事件），2025 年为 0 点，拿不到 ≥30 个独立价格结果。名次黏性有 2025 年 Wayback 基率，但那不是收益。
3. **小资金能做：满足**。单臂 ≤200 USDT、单日 ≤600 USDT、不加杠杆；容量与占款都写了。
4. **不重复：不确定（低–中风险）**。与 `quant-007` 同族，但数据源、频率、结算模板不同；条目已自标，交主审。
5. **扣成本后粗算够用：不满足 / 未证明**。没有价格回测（`backtest_count=0`）；0.88 以上按 90.1% 基率已负 EV，0.86 以下才有 2% 以上毛边，但没有历史盘口证明能买到。basket-NO 在 12.0% `Other` 基率下也是负 EV。
6. **两周内能检验：不满足**。按日期计，两周约 2–3 个独立结果，30 个约需 6 个月。应进待选区。
7. **出处可查：基本满足（修候选名单后满足）**。所有关键数字有 URL/日期/脚本；Gamma 自报量都标了“来源自报，未核实”；失败快照和 CLOB 0 点都照写。唯一硬错误是 `#1` 候选名单。

## 7. 需要改的地方（精确）

1. `## 规则` → “结构” bullet：把 `Vinted / Muse from Meta / ChatGPT / TikTok Pro / Claude / McDonald's / KICK` 改为 `Vinted / Muse from Meta / ChatGPT / TikTok Pro / Claude / Google Gemini / KICK`。
2. `### 1）Apple 侧` → “7 个真候选在 top-free-50 里的当前名次（我算的）”一句：删去 `McDonald's 7、`，保留 7 个名字：`Vinted 2、Muse from Meta 3、ChatGPT 4、TikTok Pro 5、Claude 8、Google Gemini 9、KICK 不在 top 50`。
3. `name_zh`：`App Store免费榜首榜定价` 有两个“榜”，建议改为 `App Store免费榜排名定价`（非事实错误，顺手修）。
4. 非阻断备注（不要求改）：本次重试后 120/120、158/158 快照都可解析，完整样本 P1 为 `53/60=88.3%`（预注册框）与 `71/79=89.9%`（放宽框）；条目的 `47/54`、`64/71` 是当时 6/8 张失败快照的子样本，结论不变。

CHECK: quant-017 FIX
1. `## 规则`“结构” bullet 的 7 个真候选名单：`Claude / McDonald's / KICK` → `Claude / Google Gemini / KICK`（`#1` board 没有 McDonald's）。
2. `### 1）Apple 侧` 的“7 个真候选…当前名次”句：删除 `McDonald's 7、`，使名单回到 7 个（`Vinted 2、Muse from Meta 3、ChatGPT 4、TikTok Pro 5、Claude 8、Google Gemini 9、KICK 不在 top 50`）。
3. `name_zh`：`App Store免费榜首榜定价` → `App Store免费榜排名定价`（去掉重复的“榜”）。


---

## 补充核查（批次 c20261020-170337-research）

# CHECK quant-017 — App Store #1/#2 free-app rank markets

Independent fact-check, 2026-10-20 UTC. Entry checked: `bots/quant/entries/quant-017-app-store-rank-markets.md` (status `草稿`, not edited). All scripts, raw downloads and stdout are outside the repo under `/tmp/c20261020-170337-research-w07/` (`scripts/`, `cache/`, `out/`); no raw file was added to the repo.

## 1. URL re-fetch log

| # | URL (as cited in entry) | Result | Live value vs entry |
|---|---|---|---|
| 1 | `https://rss.applemarketingtools.com/api/v2/us/apps/top-free/50/apps.json` | **OK** HTTP 200, 25,755 B | Entry's 25,783 B / `updated=05:14:43Z` was its snapshot. Re-fetch `updated=Tue, 20 Oct 2026 15:16:48 +0000`, same 50 names but Muse/Vinted swapped: `Capital One Mobile, Muse from Meta, Vinted, ChatGPT, TikTok Pro, PineDrama, Claude, Google Gemini, Threads, McDonald's, Kalshi, CapCut`. **Changed (time-varying), not a correction.** |
| 2 | `https://apps.apple.com/us/charts/iphone` | **OK** HTTP 200, 1,018,732 B | Entry 1,017,064 B. HTML name order now exactly matches the RSS top-12; at entry's 05:14Z snapshot the order was `Capital One → Vinted → Muse`, now `Capital One → Muse → Vinted`. **Changed (time-varying).** |
| 3 | `https://web.archive.org/cdx/search/cdx?url=apps.apple.com%2Fus%2Fcharts%2Fiphone&output=json&fl=timestamp,statuscode,length&filter=statuscode:200&collapse=digest` | **OK** HTTP 200 | **Exact match**: 4,295 rows; first `20220604145458`, last `20251103152602`; years 2022 18 / 2023 28 / 2024 2,648 / 2025 1,601; 454 distinct UTC dates. |
| 4 | `https://web.archive.org/web/20250101050435id_/https://apps.apple.com/us/charts/iphone` | **OK** HTTP 200, 751,307 B decoded | `schema:top-free` item 1 = `CapCut - Video Editor` (matches entry's 出处 line). Entry's 767,828 B is a different decompression size; content item matches. |
| 5 | CDX for `rss.applemarketingtools.com/api/v2/us/apps/top-free/50/apps.json` | **OK** | Only `[["timestamp","statuscode"],["20230522143120","200"]]` — 1 snapshot, matches. |
| 6 | CDX for `itunes.apple.com/us/rss/topfreeapplications/limit=50/json` | **OK** | Only `[["timestamp","statuscode"],["20180107065423","200"]]` — 1 snapshot, matches. |
| 7 | CDX for `apps.apple.com/us/charts/iphone/free-apps` | **OK** | `[]`, matches. |
| 8 | CDX for `apps.apple.com/us/app-store/charts/iphone` | **OK** | `[]`, matches. |
| 9 | `https://gamma-api.polymarket.com/public-search?q=app%20store&limit_per_type=50&events_status=all&page=1..5` | **OK** (5× HTTP 200) | 247 unique events; pages 50/50/50/50/47, `hasMore=false` on page 5, `totalResults=247`. **Exact match.** |
| 10 | `https://gamma-api.polymarket.com/events?slug=2-free-app-in-the-us-apple-app-store-on-october-23-10172026` | **OK** HTTP 200 | Rules, `negRisk=true`, 12 markets, 7 real + 4 `Reserved` + `Other`, `feeSchedule rate=0.05` all still exact. Live volume 3,197.81 (same), liquidity 1,850.86 (entry 1,558.69), arm prices changed. **Changed (time-varying).** |
| 11 | `https://gamma-api.polymarket.com/events?slug=1-free-app-in-the-us-apple-app-store-on-october-23-10172026` | **OK** HTTP 200 | Rules, `negRisk=true`, 12 markets, 7 real + 4 `Reserved` + `Other`, fee 0.05 exact. Live volume 6,376.27 (entry 5,918.22), liquidity 4,326.73 (entry 5,115.60), arm prices changed. **Changed (time-varying).** |
| 12 | `https://clob.polymarket.com/prices-history?market=<first token of each of 247 events>&interval=max&fidelity=60` | **OK** (247 requests, 0 errors) | **21 events >0 points; 226 zero; 16 closed positive; 5 open positive; closed positives only on 2026-09-25/10-02/10-09/10-16 (4 dates); 196 markets in those 16 events, 92 >0 / 104 zero.** Point range now 62–711 (entry 51–711; the 51 was a shorter open-event history at its run). **Exact except the min point count, which is time-varying.** |
| 13 | Wildcard CDX (`rss.applemarketingtools.com*`, `apps.apple.com/us/charts/iphone*`) | **DEAD/timeout** | Confirmed HTTP 000/TLS EOF on wildcard queries; exact-URL queries above work with retries. Entry correctly says wildcard was not used. |

## 2. Numbers recomputed

Scripts/outputs (all in `/tmp/c20261020-170337-research-w07/`):

- `scripts/fetch17_base.py` — all base fetches.
- `scripts/parse17.py` → `out/parse17.txt` — CDX frame and P1/P2.
- `scripts/other17.py` → `out/other17.txt` — event recount and `Other` base rate.
- `scripts/clob17.py` → `out/clob17.txt` — CLOB history census.
- `scripts/summarize17.py` → `out/summarize17.txt` — live Apple/Gamma snapshot.

### 2.1 CDX and rank persistence

`out/parse17.txt` key output (full re-fetch, all targeted snapshots parsed):

```text
[prereg] target 120 parsed 120 both-days 60 P1 53/60=0.8833 P2 17/23=0.7391
[wide]   target 158 parsed 158 both-days 79 P1 71/79=0.8987 P2 25/34=0.7353
wide top6 set overlap mean 0.9030 min 0.3333 max 1.0
wide top6 order identical 14 / 79
```

- The entry's `47/54=87.04%`, `15/21=71.43%`, `64/71=90.14%`, `23/32=71.88%` are the **subset of days whose snapshots the worker could parse** (6 pre-reg and 8 wide snapshots failed after its retries). My re-fetch retrieved all of them, so the full-sample values are **53/60=88.33%** (Wilson 95% CI 77.8–94.2%), **17/23=73.91%** (53.5–87.5%), **71/79=89.87%** (81.3–94.8%), **25/34=73.53%** (56.9–85.4%). The entry discloses the failed fetches, so this is not fabrication, but the headline "pre-registered result" is now superseded by the fuller sample. Conclusions (rank stickiness ~88–90%; last-hour flip risk still unmeasured) are unchanged.
- CDX counts, per-year counts and 454 dates reproduce exactly.
- Entry's secondary top-6 overlap 90.4% mean / 66.7% min / 12-of-71 order-identical → my full wide set gives 90.30% mean / 33.3% min / 14-of-79 order-identical. The min differs because the 8 extra days include a very different top-6. Secondary only.

### 2.2 Live market arithmetic (entry's snapshot values)

- `#1` board, 7 real arms: `0.715+0.06+0.063+0.0315+0.01+0.005+0.0045 = 0.889` YES sum; `0.71+0.02+0.05+0.003+0.002+0.001+0.001 = 0.787` bid sum; `0.72+0.10+0.076+0.06+0.018+0.009+0.008 = 0.991` ask sum. **All correct.**
- `#2` board, 7 real arms: `0.39+0.1555+0.1485+0.0975+0.0795+0.0285+0.022 = 0.9215` YES sum. **Correct.** Bid sum `0.16+0.033+0.139+0.005+0.006+0.008+0.011 = 0.362` (from the same snapshot; the entry's 0.362 is right).
- Basket-NO `#1`: `7 − 0.787 = 6.213`; fees `Σ0.05·p·(1−p)` with `p=1−YESbid` = `0.010295+0.000980+0.002375+0.000150+0.000100+0.000050+0.000050 = 0.014000`; net 6.227; breakeven `P(Other)=0.227`. **Correct.** `#2`: `7 − 0.362 = 6.638`, fees 0.01579, net 6.6538, breakeven 0.6538. **Correct.**
- Live re-fetch (15:16Z) basket-NO: `#1` bid sum 0.738, fees 0.01238, net 6.2744, breakeven **27.4%**; `#2` bid sum 0.345, fees 0.01525, net 6.6702, breakeven **67.0%**. Both still far above the measured `Other` base rate **12.0%**, so the "do not buy the basket" conclusion survives the price move.
- Fee table: `0.05·p·(1−p)` for p=0.10/0.385/0.50/0.90/0.93 = 0.0045/0.01184/0.0125/0.0045/0.003255 per share, i.e. 4.50%/3.075%/2.50%/0.50%/0.35% of notional. **Correct.**
- EV table at P1=0.9014, half-spread 1.5¢: p=0.84 cost 0.8617 EV +0.0397; p=0.88 cost 0.9003 EV +0.0011; p=0.89 cost 0.9099 EV −0.0085; p=0.90 cost 0.9195 EV −0.0181. **Correct.** Breakeven 0.8812; pre-registered 0.8490. **Correct.**

### 2.3 `Other` base rate and frequency

`out/other17.txt` key output:

```text
page 1..5 events 50/50/50/50/47 pagination totalResults 247 hasMore False
unique 247 closed 242 open 5
kinds Counter({'free': 141, 'paid': 76, 'other': 30})
US weekly boards closed 117 resolved 117 Other 14 rate 0.1197
1- closed 63 other 8 rate 0.127
2- closed 54 other 6 rate 0.1111
endDate range 2025-10-10..2026-10-16
market counts 11 26
volume sum 7711531.657859
reserved after close 8 / 117
by month {'2025-10': 4, '2025-11': 5, '2025-12': 7, '2026-01': 8, '2026-02': 6, '2026-03': 14, '2026-04': 15, '2026-05': 16, '2026-06': 12, '2026-07': 8, '2026-08': 8, '2026-09': 8, '2026-10': 6}
```

This reproduces every number in entry §4/§6: 247/242/5, 141/76/30, 117 boards, 14 `Other` = 12.0% (8/63=12.7%, 6/54=11.1%), 8/117 still carry `Reserved`, 11–26 markets, volume 7,711,531.66 ≈ 7,711,532, 62 distinct end dates, all monthly counts. **Exact.**

### 2.4 CLOB census

`out/clob17.txt`:

```text
events 247 positive 21 zero 226 err 0
closed positive 16 open positive 5
closed positive end dates 4 ['2026-09-25', '2026-10-02', '2026-10-09', '2026-10-16']
point ranges 62 711
closed-positive all markets 196 history>0 92 zero 104 err 0
```

Matches entry §5 except the minimum point count (62 vs 51, time-varying open event). The 2025-and-earlier sample remains 0 points, so no 2025 price backtest is possible.

## 3. Resolution-rule quotes vs live page

Fetched live `https://polymarket.com/event/1-free-app-in-the-us-apple-app-store-on-october-23-10172026` (HTTP 200, 1,063,985 B) and the Gamma event. The live page contains the same description text:

- `「...ranked #1 ... as of 12:00 PM ET on the specified date.」` — exact.
- `「If the chart is unavailable at 12:00 PM ET, this market may remain open for up to 48 hours ... If the data remains unavailable, this market will resolve according to the last published ranking.」` — exact.
- `「To find the overall chart, click "Apps" at the bottom ... (https://apps.apple.com/us/charts/iphone).」` — exact; entry line 40 elides `that will be used as the resolution source to this market` with `...`, which is an ellipsis, not a misquote.
- `endDate=2026-10-23T23:59:00Z` = 19:59 ET; October ET is EDT=UTC−4, so 12:00 PM ET = 16:00 UTC. Entry's time-zone note is correct.

## 4. Look-ahead / cost / independence / capacity

- **Look-ahead:** the proposed rule reads only the chart current at 11:00–12:00 ET and holds to settlement; no future information is used. The 2025 Wayback base rate is used only as a risk scale, not as a return backtest. The entry explicitly says the last-hour (15:00→16:00 UTC) flip rate is unmeasured and can only be forward-recorded. **OK, disclosed.**
- **Cost:** per-market `feeType=culture_fees`, `rate=0.05` (not the GUIDE tech 0.04) is correct; `takerOnly=true`, `rebateRate=0.25`. Fee formula and half-spread arithmetic reproduce. The only unit slip is in rule 8 (see corrections).
- **Independence:** entry counts one result per date, merging `#1`/`#2` (and paid/Play if same source/day). That is the right event-level count; 2–3 dates per two weeks is below 30. **OK.**
- **Capacity:** 200 USDT per arm, 600 USDT per day; live `liquidityNum` is 174–880 USDC per arm (entry's old snapshot 123–546). 200 USDT is within the visible book for most arms, but would take essentially the whole book on the thinnest one (McDonald's 174.7); 5,000 USDT cannot be deployed, and the 600 USDT sleeve is realistic. **OK with the thin-arm caveat.**
- **Unpriced risk:** the `Other` arm has bid=0/ask=1, so an unlisted app winning cannot be hedged; the entry states this. **OK.**

## 5. Duplicate risk

- `grep -ril -E "app store|app-store|itunes|apple.*chart" known/ bots/*/entries/ bots/*/CLAIMS.md bots/*/INDEX.md` → `known/KNOWN.md` no hit; no other bot's entry on App Store. Only incidental `chart` in two muse whale entries (not this mechanism).
- **quant-007** (`月度AI榜首市场：按榜单排名定价`) is the same core mechanism: a public leaderboard's current value is compared with a market that settles on a fixed 12:00 PM ET snapshot of that leaderboard. The Apple version changes the leaderboard, the #1/#2/weekly template and adds an `Other` arm. Under GUIDE §6 that is a **variant risk**, not clearly a new mechanism. The entry itself says this and defers to the integrator. **Gate 4 is the weakest gate.**
- **quant-010** (`周榜日更抢跑`) is related but distinct: it nowcasts a weekly aggregate from daily charts, whereas quant-017 uses the instantaneous chart at the settlement minute. The entry's distinction is fair.
- No `known/` mechanism covers app-store ranks. No duplicate of the exact template.

## 6. Gates 1–7 assessment

| Gate | Entry self-check | Checker verdict | Reason |
|---|---|---|---|
| 1 mechanism clear | 满足 | **PASS (with caveat)** | Who pays and why is stated; the cross-sectional evidence (Capital One #1 but not listed; Muse #3 priced 0.715) is real but is not a return proof. |
| 2 free data | 不确定 | **PARTIAL** | Chart/RSS and Wayback data are free and now reproducible; return-side CLOB history covers only 4 independent closed dates, 2025 = 0 points. The entry honestly says only forward recording is possible. |
| 3 small capital | 满足 | **PASS** | 200/600 USDT, no leverage; book depth supports ~200 USDT/arm. |
| 4 not duplicate | 不确定 | **FAIL/UNCERTAIN** | Core mechanism is the same fixed-time public-leaderboard snapshot as quant-007; only the leaderboard/template/frequency differ. Likely a variant under GUIDE §6. |
| 5 cost-adjusted | 不确定 | **NOT PROVEN** | No price backtest (`backtest_count=0`); basket-NO is negative EV at the measured 12.0% `Other` rate; final-hour edge unmeasured. |
| 6 two-week test | 不满足 | **FAIL** | 2–3 independent dates in two weeks vs 30 required; ~6 months needed. |
| 7 sources | 满足 | **PASS** | URLs, access dates, scripts and raw outputs are present; self-reported Gamma volume/liquidity are labelled. |

Unambiguous passes: 1, 3, 7 (3/7). Gate 2 partial; 4/5/6 not met. This is consistent with the entry being a `草稿` / 待选区 candidate, not a 收录 candidate.

## 7. Corrections

1. **Line 42: wrong `#1` candidate set.** The `#1` board's 7 real arms are `Vinted / Muse from Meta / ChatGPT / TikTok Pro / Claude / Google Gemini / KICK`; `McDonald's` is only on the `#2` board. Replace `Claude / McDonald's / KICK` with `Claude / Google Gemini / KICK` (or list `#1` and `#2` separately). Source: `out/summarize17.txt`.
2. **Line 64: "7 个真候选" but eight names.** The sentence lists Vinted, Muse, ChatGPT, TikTok, McDonald's, Claude, Google Gemini, KICK. Either say "两个 board 合计 8 个候选（#1 专属 Google Gemini，#2 专属 McDonald's）" or list the `#1` seven and `#2` seven separately. The current phrasing is internally inconsistent with line 42 and with the table at lines 71–79.
3. **Rank-persistence headline numbers.** The full re-fetch (all 120 pre-registered and 158 wide snapshots parsed) gives `P1=53/60=88.33%` (Wilson 77.8–94.2%) and `P2=17/23=73.91%` (53.5–87.5%) for the pre-registered frame, and `P1=71/79=89.87%` (81.3–94.8%), `P2=25/34=73.53%` (56.9–85.4%) for the wider frame. The entry's `47/54`, `15/21`, `64/71`, `23/32` are the subsets where 6/8 snapshots failed after its retries. Update the numbers, or explicitly label them "failed-fetch subset" everywhere they appear (`data:`, `test_2w:`, 整理说明, §3, rules 8–9, cost section, gate 2/5).
4. **Line 55: unit error at p=0.90.** `0.90 时 EV≈−1.8%` should be `−2.0%` (the cost section's `−1.8¢` is correct; −1.8¢/0.9195 = −1.96%). Change to `−2.0%` or `−1.8¢ (−2.0%)`.
5. **Line 122: CLOB point range.** Re-fetch gives 62–711 points, not 51–711. The 51 was a shorter open-event history at the earlier run; update or say "本次复算 62–711".
6. **Gate 4 wording.** Change `不重复：不确定` to `不重复：不满足/待主审（与 quant-007 同族，按 GUIDE §6 可能只是变体；若主审认定为变体，应按 supplement/improvement 处理）`. The current text already admits the risk but still scores the gate as merely "uncertain".

CHECK: quant-017 FIX

1. Line 42: replace `Claude / McDonald's / KICK` with `Claude / Google Gemini / KICK` in the `#1` real-candidate list.
2. Line 64: say "两个 board 合计 8 个候选（#1 专属 Google Gemini，#2 专属 McDonald's）" or split the `#1`/`#2` lists; do not call the eight names "7 个真候选".
3. Replace the persistence numbers with the full-sample values: pre-reg `P1=53/60=88.33%` (CI 77.8–94.2%), `P2=17/23=73.91%` (CI 53.5–87.5%); wide `P1=71/79=89.87%` (CI 81.3–94.8%), `P2=25/34=73.53%` (CI 56.9–85.4%). If keeping the old values, label them "failed-fetch subset" everywhere and do not call them the pre-registered result.
4. Line 55: change `0.90 时 EV≈−1.8%` to `−2.0%` (or `−1.8¢ (−2.0%)`).
5. Line 122: change `51–711` to `62–711` (or state the 51 was the earlier run's open-event minimum).
6. Gate 4: mark `不重复` as `不满足/待主审` and state that quant-007 is the same fixed-time public-leaderboard mechanism; recommend integrator decide supplement vs new.
