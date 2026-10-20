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
