# quant 第 1 轮待核条目审计（2026-10-20）

范围：`bots/quant/entries/` 共 23 条；本轮 `待核` **15 条（15/15，已满额）**，`草稿` 8 条。只读审计，未修改任何条目。

产物：`audit.py`、`run_output.txt`、`url_status.csv`、`dupes.csv`、`dupe_verdicts.csv`、`lint_full.txt`、`lint_quant.txt`。原始抓取缓存在 `_cache/`（已 gitignore）。

判定口径：2xx/3xx = 活；404/410/DNS = 死链；401/403/429/451/400/422/5xx/超时/TLS = **需人工复核**（403/429 不等于页面已死）；含 `<...>`、`{...}`、`...`、`N/K` 等占位符的 API URL 记 `template`，不请求。

## 一句话结论

- **没有发现“把 404 页面写成已读”的编造迹象**：本轮 5 个 404 全部在条目里注明失败/未取数或明确“不引用”；其余问题主要是 403/429/超时和缺参数的接口基地址。
- **15 条中没有一条预测为“收录”**：唯一门 5/门 6 都写“满足”的 quant-001 是 `improvement`，按 §3.1 走“改进采纳”；quant-002/018 是 `supplement`，走“补充采纳”；其余 12 条 `new` 至少门 5 或门 6 不是“满足”。
- 主要风险不是编造，而是 **9 条自认两周凑不到/可能凑不到 30 个独立结果**（另有 4 条第 5 条直接写“不满足”），以及 **quant-012 / 018 / 019 三条“官方计数阶梯”同族**（018 已按 supplement，019 未声明）。
- 预期分最高的是 **quant-001（改进采纳 2.0）**；其后是 7 条 `待选区`（各 1.3）。
- **建议换一条：quant-007 → quant-021**；其余不动。只给建议，未改状态/日期。

## 15 条待核总表（按预期分排序）

| # | 条目（市场×权重） | 出处（本轮实测） | 查重判定（先到） | 门槛自查问题 | 预期结局（分）与一句理由 |
|---:|---|---|---|---|---|
| 1 | quant-001 波动管理动量加 BTC 趋势总开关（crypto×1.0） | 3 URL：2 活，1 需复核（ScienceDirect 403，条目已注 403/用摘要）；0 死链 | T-T2-vm：不同（improvement，known 先到）；dot-022/024/021 不同 | 4 不确定 | **改进采纳 2.0**：可复现、回撤下降；但收益低于 VM，若主审要求“更好”含收益则降为待选区 1.0 |
| 2 | quant-020 财报超预期：中价带基准率（polymarket/finance×1.3） | 12 URL：6 活，6 模板，0 死/受阻 | quant-014：不同（同 finance，标的/机制不同；同 commit） | 4、5 不确定 | **待选区 1.3**：1,378 个已结算事件、247/250 可取价格，30+ 可检验；但中价带为事后划定，整体缺口小于成本 |
| 3 | quant-005 发帖数分档（polymarket/mentions×1.3） | 18 URL：15 活，3 模板，0 死/受阻 | quant-004：不同（总发帖数 vs 单词提及；004 草稿；同 commit） | 1、5 不确定 | **待选区 1.3**：30+ 历史事件、xtracker 免费；无回测，“谁付钱”未用成交验证 |
| 4 | quant-012 地震周计数：USGS 基率（polymarket/weather×1.3） | 17 URL：14 活，3 模板，0 死/受阻 | quant-018/019：同族（018 已 supplement，019 未声明）；dot-001/002/015 不同 | 6 不满足；2、4、5 不确定 | **待选区 1.3**：USGS 26 年基率、证据强；自认两周最多 4 个 event，30 个约需 15 周 |
| 5 | quant-014 SPX 收盘价：已实现波动率（polymarket/finance×1.3） | 13 URL：11 活，1 模板，1 需复核（Yahoo 429，非死链） | quant-020：不同；dot-018：不同 | 1、2、5、6 不确定 | **待选区 1.3**：只有 21 个历史价格 event 且交易日高度相关；自认更可能待选区 |
| 6 | quant-016 烂番茄开分：早期评论二项（polymarket/culture×1.3） | 18 URL：14 活，4 模板，0 死/受阻 | quant-010：不同（同文化 nowcast，变量不同；010 先到） | 6 不满足；2、4、5 不确定 | **待选区 1.3**：市场侧价格历史可取；模型侧 JS 无法回放，两周 5–6 个 event |
| 7 | quant-009 上币截止日：按基准率（polymarket/crypto×1.3） | 21 URL：12 活，3 模板，2 死，4 需复核（404 archive CDX / Coinbase RSS 均条目标注失败；403 Coinbase blog；400/422 缺参数基地址） | dot-007/dot-018：不同；quant-008 草稿：不同 | 4、5、6 不确定 | **待选区 1.3**：24 个 event / 12 簇、无回测；要凑 30 需并入 next coin 周度系列 |
| 8 | quant-006 网球 Elo 给 PM 定价（polymarket/sports×1.3） | 18 URL：9 活，6 模板，2 死，1 需复核（GitHub API 404 条目已注；rewards 404 未引用；ATP 403） | quant-021/011、dot-013：不同（仅同体育板块） | 2、4、5、6 不确定 | **待选区 1.3**：无历史 Elo/历史盘口，只能前向；两名球员都在榜比例本轮 0/3 |
| 9 | quant-018 海峡周通行：PortWatch 基率（polymarket/geopolitics×1.3） | 17 URL：16 活，1 模板，0 死/受阻 | quant-012：变体（已 supplement，012 先到） | 4、5、6 不确定 | **补充采纳 0.65**：PortWatch 34/41 结算一致；逐档价格只有 6 个 event，前向两周 4 个 |
| 10 | quant-019 麻疹病例阶梯：CDC 计数流（polymarket/other×1.3） | 11 URL：7 活，3 模板，1 需复核（CDC 403；条目自报 200，需人工复核） | quant-012：变体（同计数阶梯，未声明 supplement；012 先到） | 6 不满足；2、4、5 不确定 | **变体→补充采纳 0.65**：基率可复现，但两周 1–2 个 event；若主审按 new 收则待选区 1.3 |
| 11 | quant-002 月初月末与周一效应反证（crypto×1.0） | 1 URL：1 活 | E-E2-turn-of-month：不同（supplement，known 先到） | 5 不满足（结论就是扣成本不够） | **补充采纳 0.5**：给 known 条目补样本外反证；负结果仍有证据价值 |
| 12 | quant-013 Coinbase 溢价 z 分数（crypto×1.0） | 10 URL：8 活，2 需复核（Semantic Scholar/arXiv 429，非死链） | A-A3-kimchi、E-E3-btc-leadlag：不同（known 先到） | 5 不满足；4、6 不确定 | **退回 0**：事件级 3 日净收益中位数 BTC −0.41%、SOL −0.23%，按预注册标准已失败 |
| 13 | quant-011 足球三向盘平局基准率（polymarket/sports×1.3） | 10 URL：6 活，4 模板，0 死/受阻 | quant-006/021：不同 | 5 不满足；1、4、6 不确定 | **退回 0**：合并样本净 −0.3%，吃单后不够；门 5 自认不满足 |
| 14 | quant-010 周榜日更抢跑（polymarket/culture×1.3） | 20 URL：16 活，2 模板，1 死，1 需复核（open.spotify 404 条目已注未解析；FlixPatrol 403） | quant-016：不同（同文化 nowcast） | 5 不满足；2、4、6 不确定 | **退回 0**：示例 A 吃单即使 100% 赢也净亏；只能 maker，成交概率未验证 |
| 15 | quant-007 月度 AI 榜首（polymarket/tech×1.3） | 14 URL：9 活，3 模板，2 需复核（arena/lmarena 403；条目已注 403） | quant-017：变体（自家草稿；007 先到） | 2、6 不满足；5、7 不确定 | **退回 0**：结算源 403/历史榜单未取得，只有 22 个已结算 event，两周最多新增 1 个 |

说明：GUIDE §3.1 对 `improvement`/`supplement` 的实际结局是“改进采纳/补充采纳”，表中直接写这两个值；括号内为结局分×市场权重。

## 死链 / 受阻 URL 明细

**死链（404；均已条目标注或明确未引用）**

- quant-006：`https://api.github.com/repos/JeffSackmann/tennis_atp`（条目写 404，不作为来源）；`https://polymarket.com/api/rewards/markets/current`（条目写“本轮未访问，不引用”）。
- quant-009：`https://archive.org/wayback/cdx/`（条目写返回码 000，本次 404，均失败）；`https://www.coinbase.com/rss/blog?category=listing`（条目写 404，不作为来源）。
- quant-010：`https://open.spotify.com/charts`（规则指定结算源；条目写“未从该页解析出榜单数据”）。

**需人工复核（403/429/451/400/422，非死链）**

- quant-001：`https://www.sciencedirect.com/science/article/abs/pii/S0304405X14002566` 403；条目已注“直接打开返回 403，内容来自搜索摘要”。
- quant-006：`https://www.atptour.com/en/scores/current` 403。
- quant-007：`https://arena.ai/leaderboard/text/overall-no-style-control` 403；`https://lmarena.ai/leaderboard/text` 403；条目已注 arena 403。
- quant-009：`https://www.coinbase.com/blog/listing` 403；`https://www.coinbase.com/blog/rss` 403；`https://clob.polymarket.com/prices-history` 400（缺参数基地址）；`https://gamma-api.polymarket.com/public-search` 422（缺参数基地址）。
- quant-010：`https://flixpatrol.com/top10/netflix/world/` 403；条目已注 403。
- quant-013：`https://api.semanticscholar.org/graph/v1/paper/search?query=coinbase%20premium%20bitcoin` 429；`https://export.arxiv.org/api/query?search_query=abs:%22Coinbase%22+AND+abs:%22Bitcoin%22` 429。
- quant-014：`https://query1.finance.yahoo.com/v8/finance/chart/%5ESPX?range=5y&interval=1d` 429。
- quant-019：`https://www.cdc.gov/measles/data-research/index.html` 403（条目自报 200；Cloudflare 类，需人工复核）。

本轮无 DNS 失败。403/429 只说明本机/本 UA 被挡或限流，不能据此判页面已死；404/410 才算死链。

## 查重结论

28 组重点 pair 的人工判定在 `dupe_verdicts.csv`。没有 `重复`；3 组 `变体`：

1. **quant-007 ↔ quant-017（变体）**：同为“用公开榜单当前值/黏性给 PM 排名市场定价”，只换榜单源与频率。quant-007 首提交 `2026-10-20T06:20:10+02:00`，quant-017 为 `2026-10-20T06:50:31+02:00`，007 先到；017 若第 2 轮提交，应按 `supplement` 而不是并列新条目。
2. **quant-012 ↔ quant-018（变体，已按 supplement 合规）**：同为官方计数阶梯按基率/流量定价；018 已写 `improves: quant-012`。012 首提交 `2026-10-20T06:20:10+02:00`，018 为 `06:50:31+02:00`，012 先到。
3. **quant-012 ↔ quant-019（变体，未声明 supplement）**：同机制，只换计数源（地震→麻疹）。019 与 018 同一提交时间，012 先到；**建议把 019 改为 `kind: supplement`、`improves: quant-012`，否则有拆条风险**。

其余重点 pair 判 `不同`：001↔T-T2-vm（improvement）、002↔E-E2-turn-of-month（supplement）、005↔quant-004（总发帖数 vs 单词提及）、006↔021/011/dot-013（不同运动/信号）、009↔dot-007/dot-018（上币截止日 vs 阶梯/期权）、010↔016（榜单 vs 影评）、011↔021（足球 vs F1）、012↔015/dot-001（地震 vs 气温）、013↔A-A3-kimchi/E-E3（跨所溢价方向 vs 收敛/领涨）、014↔020/dot-018（SPX vs 财报/期权）。

另与 `known/KNOWN.md` 的概念近邻也判 `不同`：009↔`E-E1-listing-chase`/`E-E1-listing-short`/`E-E1-upbit-pump-short`（PM 二元截止日 vs 现货/永续方向）；020↔`E-E1-index-etf-event`/`E-E1-macro-window`（EPS beat vs 指数/宏观事件）；019↔`A-A3-poly-cross-market`（两条不同结算日的计数阶梯，不是同一命题的跨市场价差）。

先到先得要点：`known/KNOWN.md` 首提交 `2026-10-20T00:31:59Z`，早于所有 quant 条目；dot 的 `dot-001`/`dot-007` 为 `2026-10-20T02:54:09+08:00`，早于 quant-012/009 的 `06:20:10+02:00`。但上述 pair 均判不同，先到只影响“变体”的 007/012。

## 门槛自查与“凑不到 30”扫描

正文明确写“两周凑不到/可能凑不到 30 个独立结果”的 9 条：**006、007、009、010、012、014、016、018、019**。其中第 6 条直接写 `不满足` 的是 **007、012、016、019**；010/011/013 的第 5 条写 `不满足`。

这说明多数条目的问题不是“没写清楚”，而是作者自己已经把“不可收录”的证据写出来了；按 GUIDE，这类应进待选区或退回，不应期待收录。`run_output.txt` 第 28–87 行有逐条原文片段。

## 草稿替换建议

`bots/quant/LOG.md` 的“第 2 轮（2026-10-26 起）排队”列出 3 条：**quant-021（F1）、quant-017（App Store）、quant-015（全球月均温）**。LOG 同时写明不再提交 003/008/022/023/004。

| 草稿 | 关键证据（引自已写好的条目） | 主要问题 | 若本轮提交的预期 |
|---|---|---|---|
| quant-021 F1 杆位/冠军 | 2014–2026 共 269 场；2024–2026 有 49 个独立 Winner event；预注册规则扣 1¢ 半价差 + 0.05 费后净 +0.343/份（21 笔），半价差 5¢ 时约 +0.303 | 价格是最后成交价、不是可成交 ask；门 4/5 不确定 | 待选区 1.3；若主审认定 stale 价不可执行则退回 |
| quant-017 App Store 榜首 | 117 个已结算周度榜；名次黏性预先写死口径 47/54=87.0%（事后放宽 64/71=90.1%）；`Other` 14/117=12.0% | 无收益回测；已关闭价格历史只有 16 个 event/4 个结算日；门 2/6 不满足或不确定；与 quant-007 同机制 | 待选区 1.3，但作为 007 的变体，不能与 007 同轮并列 |
| quant-015 全球月均温 | 2000–2026 共 321 个月走前校准；log loss 1.3638，均匀分布 2.0794 | 价格侧只有 1 个已关闭 event，且模型 log loss 1.1083 输给市场 0.3740；门 5/6 不满足 | 待选区 1.3，证据偏“模型校准”而非“可赚钱” |

**建议：换一条，quant-007 → quant-021。** 理由：

- quant-007 的预期是 **退回 0**：结算源 arena/lmarena 均 403，历史榜单值未取得；只有 22 个已结算 event，两周最多新增 1 个，门 2/6 直接不满足。
- quant-021 至少是 **待选区 1.3**：49 个历史独立结果、已有样本外检验和正净收益记录，主要缺陷（last-trade 价不是 ask）是“收益待证”，不是“数据拿不到”。
- 不换 quant-017：它与 quant-007 是同一机制（公开榜单定价），换进来仍会被判变体；不换 quant-015：价格侧只有 1 个已关闭 event，且模型输给市场，门 5 直接不满足。
- 代价：021 原本排在“第 2 轮”，换入会消耗第 2 轮队列；第 2 轮仍有 B21–B25 新题。若不愿动第 2 轮队列，则选择 **“不换”**，但 007 的上限仍是 0，换入 021 不劣。

以上仅为建议；本轮未修改任何条目、`status` 或 `date`。若采纳，需人工在 2026-10-25 23:59 UTC 前改 `quant-007` 为草稿、`quant-021` 为待核并改提交日。

## 验证

- `python3 bots/quant/notes/r1-audit/audit.py`：可重跑；本次 162 个唯一非模板 URL，缓存命中后不再重复请求；stdout 在 `run_output.txt`。
- `python3 tools/check.py lint`：**全仓仍非 0**，原因是 `bots/muse/entries/muse-700-defined-risk-iron-fly.md`、`muse-701-skew-harvest-sign-correction.md` 在 front matter 前多了一行 blockquote，`check.py` 读不到字段并最终 `KeyError: 'id'`；这是本分支未触碰的既有文件（`git log` 显示 muse 提交 `35a012a`），不属于本次改动。完整输出见 `lint_full.txt`。
- 只对 quant 条目跑同一 `lint()`：`检查完毕，问题 0 个`，见 `lint_quant.txt`。因此本轮新增笔记没有引入 lint 问题，但“全仓 lint = 0”这一验收项因他人文件未通过而无法满足。
- `python3 tools/check.py dupes` 退出 0，但会把 `https://clob.polymarket.com/book?token_id=<id>` 等模板 URL 当成同一出处；本审计已把模板排除在查重 URL 之外，人工判定以 `dupe_verdicts.csv` 为准。
