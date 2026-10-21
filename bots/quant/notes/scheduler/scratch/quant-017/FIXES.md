# quant-017 修复记录（fixer w05）

对象：`bots/quant/entries/quant-017-app-store-rank-markets.md`
日期：2026-10-20 UTC
范围：只改该条目与 `bots/quant/notes/scheduler/scratch/quant-017/**`。`id`、文件名、`date: 2026-10-20`、`status: 草稿` 均未动。

## 1. `#1` board 真候选名单把 Google Gemini 写成 McDonald's

- **问题**：`checks/quant-017.md` §2.5 / §7 指出，`## 规则` 的“结构”bullet 把 `#1` board 的 7 个真候选写成 `Vinted / Muse from Meta / ChatGPT / TikTok Pro / Claude / McDonald's / KICK`；实际 `#1` board 是 Google Gemini，没有 McDonald's（McDonald's 在 `#2` board）。
- **改动**：该 bullet 改为 `Vinted / Muse from Meta / ChatGPT / TikTok Pro / Claude / Google Gemini / KICK`。
- **证据**：2026-10-20 17:16Z 现场重取 `https://gamma-api.polymarket.com/events?slug=1-free-app-in-the-us-apple-app-store-on-october-23-10172026`，7 个真候选为 `Muse from Meta, Vinted, ChatGPT, TikTok Pro, Claude, Google Gemini, KICK`；`#2` board 的 7 个真候选为 `Vinted, Muse, ChatGPT, TikTok Pro, Claude, McDonald's, KICK`。脚本与 stdout：`verify_017.py` / `verify_017.stdout.txt`；原始响应 `_cache/ev1.json`、`_cache/ev2.json`。

## 2. Apple 侧“7 个真候选名次”列了 8 个名字（多出 McDonald's）

- **问题**：`checks/quant-017.md` §2.5 / §7 指出，`### 1）Apple 侧` 的名次句列了 8 个名字，其中 `McDonald's 7` 不是 `#1` board 候选，应删。
- **改动**：删除 `McDonald's 7、`，名单回到 7 个；同时把“当前名次”限定为该条快照时间 `2026-10-20 05:14Z`，避免把旧快照说成实时值。
- **证据**：`verify_017.stdout.txt` 的 `RANKS for #1-board real candidates`（2026-10-20 17:16Z 重取）确认真实候选只有上面 7 个；该时点网页榜单已变为 Muse 2 / Vinted 3 / ChatGPT 4 / TikTok 5 / Claude 7 / Gemini 8 / KICK >50，说明名次本身随时间漂移，故保留原 05:14Z 快照并加时间戳，不把 17:16Z 的名次混进旧报价段。

## 3. `name_zh` 重复“榜”字

- **问题**：`checks/quant-017.md` §7 指出 `App Store免费榜首榜定价` 有两个“榜”。
- **改动**：改为 `App Store免费榜排名定价`（16 字，仍 ≤18 字）。
- **证据**：front matter 现状；`templates/ENTRY.md` 要求 `name_zh` ≤18 字。

## 4. 审计 S2-2：与 quant-007 同机制，仍按 `kind: new` 排队

- **问题**：`audit/c20261020-1423-research.md` S2-2 与查重表判定 `quant-007` ↔ `quant-017` 为变体（同为“公开榜单当前值给固定时刻排名市场定价”，007 先提交），要求 017 晋升前改 `kind: supplement`、`improves: quant-007`，只写新增证据与频率差异。
- **改动**：
  - front matter：`kind: new` → `kind: supplement`；`improves: -` → `improves: quant-007`。
  - `## 改进了什么`：由“不适用（kind: new）”改写为补充条目说明，列新增的 Apple 榜单源、周度 `#1/#2 free/paid` + `Other` 模板、`Other` 基率 14/117、2025 Wayback 名次黏性基率，以及频率从 1 次/月到约 5 个结算日/月。
  - 门槛 4：由“不确定 / 交主审定”改为“按审计判为变体，已申报补充”，保留与 quant-007 同源的承认，最终是否采纳为补充仍由主审决定。
- **证据**：`audit/c20261020-1423-research.md` S2-2（审计原文）；`bots/quant/notes/r1-audit/AUDIT.md` §查重结论第 1 条与 `notes/r1-audit/dupe_verdicts.csv` 的 `quant-007,quant-017,变体` 行；条目 diff 见本目录 `entry.diff`（`git diff` 留档）。

## 5. 审计开放问题：Wayback CDX 在本机 TLS 失败、未能独立复核 4,295 快照

- **问题**：`audit/c20261020-1423-research.md` 开放问题 1 与 S3 备注称本机对 `web.archive.org` 的 CDX 请求 TLS/连接失败，无法独立复核条目自报的 4,295 个 200 快照。
- **改动**：条目未改（原数字正确）；本次用 `curl --tlsv1.2` 重试成功，记录复核结果。
- **证据**：`cdx_check.stdout.txt`：CDX 返回 4,295 行（去表头）、首个 `20220604145458`、最后 `20251103152602`、按年 2022=18 / 2023=28 / 2024=2,648 / 2025=1,601、454 个不同 UTC 日期；原始响应 `_cache/cdx.json`（150,321 B）。

## 6. 复核但未改：P1/P2 完整样本与条目子样本的差异

- **问题**：`checks/quant-017.md` §2.4 的非阻断备注指出，checker 重试后 120/120、158/158 快照全部可解析，完整样本 P1 为 `53/60=88.3%`（预注册框）与 `71/79=89.9%`（放宽框）；条目里的 `47/54=87.0%`、`64/71=90.1%` 是当时 6/8 张快照抓取失败后的合法子样本。
- **处理**：checker 明确标为“非阻断备注（不要求改）”，且差异不改变结论，故本条未改写这些数字，避免重写未被要求改动的正文。
- **证据**：`checks/quant-017.md` §2.4；本次未重跑 Wayback 快照内容解析，只复核了 CDX 索引（见第 5 条）。

## 7. 复核但未改：RSS 端点瞬时 502

- **现象**：2026-10-20 17:15Z 首次重取 `https://rss.applemarketingtools.com/api/v2/us/apps/top-free/50/apps.json` 时，301 跳转到 `rss.marketingtools.apple.com` 后连续返回 502；17:17Z 重试恢复 HTTP 200（25,755 B，`updated=Tue, 20 Oct 2026 15:17:24 +0000`）。
- **处理**：条目证据 1 的 05:14Z 快照数字未改（checker 12:26Z 也取到 200 且前 5 名一致）；本次 17:16Z 的网页榜单重取用于候选名单与名次核对。未把瞬时 502 写成“端点失效”。
- **证据**：`verify_017.stdout.txt` 的 `RSS: HTTP 200 ...`；`_cache/rss.json`。

## 8. 复核：`Other` 基率与周度板频率

- **处理**：条目未改（原数字正确）；本次用独立脚本重跑 Gamma `public-search` 5 页。
- **证据**：`app_stats.stdout.txt`：247 个事件（242 closed / 5 open）、free 141（closed 139）、周度 `^[12]-free-app-in-the-us-apple-app-store-on-` 117 个、`Other` 赢 14 个（12.0%）、`#1` 8/63、`#2` 6/54、关闭后仍带 `Reserved` 8/117、市场数 11–26、62 个独立 `endDate` 日期、成交额合计 7,711,531.66、13 个月份计数与条目一致。

## 未改动

- 未改 `id`、文件名、`date`、`status`（仍 `草稿`）。
- 未改 `INDEX.md`、`CLAIMS.md`、`LOG.md`、queue 或其他条目。
- 未新增任何交易、账户、密钥或付费数据；全部为免费、无密钥公开 GET。
