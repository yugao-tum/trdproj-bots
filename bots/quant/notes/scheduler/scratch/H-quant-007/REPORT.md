# quant-007 历史可成交价回测（待核条目的负证据）

日期：2026-10-21 ｜ 角色：improvement（H-quant-007）｜ 条目：`quant-007-ai-leaderboard-monthly`

## 结论

**负。** 22 个已结算 event、21 个有价格。按检查前 7 天买"榜单 Rank-1 公司"的 Yes、持到结算（吃单费 `0.04·p·(1−p)`，加 0.5¢ 滑点）：

- 净均值 **−0.0342/份**，95% bootstrap `[−0.1413, +0.0385]`；中位 **+0.0144**。
- 命中 15/21 = 71.4%；同一时点买"市场自己最贵臂"命中 **21/22 = 95.5%**，净均值 **+0.0246**。
- 两者不一致的 5 个 event：榜名 **0/5**、最贵臂 **5/5**；配对差均值 **−5.91pp**，95% 区间 `[−11.95pp, −1.11pp]`。
- 条目自己的 `ask≤0.85` 子样本：n=7，均值 **−0.0137**、中位 **−0.0203**。
- 唯一正的口袋是 21 天提前量：均值 +0.1008，但 44% 来自 2026-02 单个 event，区间含 0。
- 2026 年 9 个 event 榜名 9/9 全对，但同期榜名第一与市场最贵臂**完全是同一臂**，测不到增量。

**建议**：核对方将 `quant-007` 降为草稿/退回（待选区），不收录。条目 `status`/`date` 未改。

## 2026-10-21 加固：用 data-api 真实成交价复跑（第二遍，独立于日频标记价）

价格不再用 `prices-history` 的日频最后成交/标记点，而是每个 event 取进场时刻之前**最后一笔 data-api 已执行 BUY**（同一 YES token，份数 ≥1），按该成交价付 `0.04·p·(1−p)` 吃单费。脚本 `q007_trades.py` → `q007_trades_output.txt`、`q007_trades_fills.csv`。

- T−7：n=21/22（2025-01 DeepSeek 在进场前 30 天窗口内无 YES BUY，记 `未取到`），命中 15/21，**净均值 −0.0320**（95% `[−0.1422, +0.0459]`），中位 **+0.0154**；0.5¢ 滑点 −0.0369；费率为 0 时 −0.0300。
- 基准（同一时刻市场最贵具名臂，同样按最后一笔 BUY 成交）：命中 21/22，净均值 **+0.0223**；配对差（榜名−最贵臂）**−0.0544**，95% `[−0.1131, −0.0093]`，不含 0；5 个分歧 event 榜名 **0/5**、最贵臂 **5/5**。
- 条目自己的 `fill≤0.85` 子样本：n=6，均值 **−0.0282**、中位 **−0.0159**；0.5¢ 滑点 −0.0333。（日频价口径下 n=7、均值 −0.0137，两个口径都为负。）
- T−14：均值 −0.0122；T−21：+0.0648（95% `[−0.0228, +0.1410]`，含 0，仍依赖 2026-02 单个 event）。
- 真实成交价与日频标记价的差：榜名臂均值 **+0.28¢**、中位 +0.31¢、最大 |差| **8.50¢**；最贵臂均值 +0.74¢。方向不变。
- 成交都在进场前 0.01–12.9 小时，最小 1.06 份；所以这是"1 份可成交价"，不是深度/排队模拟。

## 来源逐条复核（`q007_verify_all.py` → `q007_verify_all_output.txt`）

- Gamma 10 月 event：id 841230、32 臂（21 具名 + 11 占位）、`endDate 2026-10-31T16:00:00Z`、规则原文 8 条关键短语全部命中；`named_arms`、占位臂 `Company A–I,K + Other` 与条目一致。
- **更正费用说法**：04:17Z 复核时，**21 个具名臂** `feeSchedule.rate=0`，**11 个占位臂仍为 0.04**；不是"全部为 0"。条目已按此改写。具名臂 Yes 合计 04:17Z 为 **0.9955**（01:21Z 曾为 1.0065），随成交变动。
- 10 月 CLOB `/book` 仍为空盘（Google bid 0.001 / ask 0.999；Anthropic 0.01 / 0.99），原 0.742/0.743 深度不可复现——与条目一致。
- 11 月 event：35 臂、占位到 `Company M`、`endDate 2026-12-01T04:59:00Z`；价格是时变值。
- series 10030：`monthly`、`createdAt 2025-02-01T00:23:50Z`、`restricted=true`；closed 22 个、open 3 个；arms 序列 `[5,6,12,15,12,13,16,13,12,15,23,15,17,25,25,25,27,29,19,26,32,32]`；6 个 Rank 规则 event；22/22 有唯一赢家。
- `arena.ai` 三路径与 `lmarena.ai` 全部 **403**（条目已写明）；Wayback 只给索引。
- HF 数据集：`gated=false`、`cc-by-4.0`、README 含 `text`/`text_style_control` 与六列；parquet 可读（Range GET 206，magic `PAR1`）；`text` overall **55,466 行**、日期 **2023-05-08..2026-10-20**（条目原写 10-15，已按本次复核改为 10-20）；`text_style_control` overall 51,154 行、**2024-08-28..2026-10-20**。镜像 rank-1 抽查 2026-07-21 / 2026-08-21 / 2026-09-13 与回测快照逐项一致。
- 复用的合并笔记 `bots/quant/notes/batch1-verification/quant-007.md`、`bots/quant/notes/r1-audit/AUDIT.md` 均存在；本报告与条目引用其结论而未改写其文字。

## 方法（先写死，未拟合参数）

1. 事件：Gamma `series_id=10030&closed=true`，赢家取 `outcomePrices[0]=="1"` 的臂。
2. 榜名：HF `lmarena-ai/leaderboard-dataset` config `text`、`category="overall"`，取 `leaderboard_publish_date <= 检查时刻−L` 的最新快照，`rank==1` 的 `organization`；别名映射到市场臂。
3. 价格：主口径为 CLOB `prices-history?...&interval=max&fidelity=1440` 在 `t <= 进场时刻` 的最后一点；加固口径为 data-api `trades` 在该时刻前最后一笔同 token BUY 的真实成交价。
4. 成本：吃单费 `0.04·p·(1−p)`（2026-10-20 Gamma 费率快照；2026-10-21 该 event 费率已变 0，故保守），滑点 0/0.5¢/1¢。
5. 基准：同一时刻价格最高的具名臂，同费用/滑点。
6. 独立结果：每 event 1 份、1 个结果，禁按臂/天拆分。

## 复现

```
cd bots/quant/notes/scheduler/scratch/H-quant-007
# 首次：下载 closed.json / px_*.json / text_full.parquet 到 _cache/（已 .gitignore）
python3 q007_hist.py      # -> backtest_raw.csv, fetch_output.txt
python3 q007_analyze.py   # -> analyze_output.txt
python3 q007_fills.py     # -> fills_output.txt（data-api 成交抽查）
python3 q007_verify.py    # -> verify_output.txt（逐 URL 复核）
python3 q007_trades.py    # -> q007_trades_output.txt, q007_trades_fills.csv（全部 event 真实成交价复跑）
python3 q007_verify_all.py # -> q007_verify_all_output.txt（逐条来源断言复核）
```

`_cache/` 约 11 MB，含派生的 `overall.csv`（3.7 MB）、`overall_sc.csv`、`closed.json` 与 414 个价格历史 JSON；原始 HF parquet（60 MB）下载后未保留。全部 `_cache/` 已被 `.gitignore`。

## 数据质量 / 已知问题

- **官方结算页仍 403**：`arena.ai` 与 `lmarena.ai` 全部 403，榜名只能靠 HF 第三方镜像；镜像 `text` 是否等同 `overall-no-style-control` 无法直接确认。
- **镜像在旧年份与结算不一致**：rank-1 vs 实际结算 2026 年 9/9，2024–2025 只有 6/13。旧年份负结果可能是镜像失真；但 2026 年又没有"榜名≠市场"的样本，所以正反都无法定论——证据不足 + 现有可测方向为负。
- **价格是日频最后成交点**，不是盘口；data-api 全样本复跑的最后一笔 BUY 与日频点差均值 +0.28¢、最大 8.50¢。真实成交口径仍是"1 份、进场前最后一笔"，不还原深度/排队；2026-04 仅 1.41 份。
- **费率不救**：吃单费设 0 后 7 天均值仍 −0.0322、配对差 −0.0597。
- **style-control 口径不影响**：config `text_style_control` 重跑后 22 个 event 的 rank-1 完全相同、三档结果逐位一致（`q007_hist_sc.py`/`fetch_sc_output.txt`）。
- **镜像日期只有"日"**：检查当日快照可能晚于 12:00 ET（2026-09-30 快照显示 Google，市场结算 Anthropic），故只用 T−7/14/21。
- **费率时变**：2026-10-21 Gamma 显示 10 月 event 具名臂 `rate=0`，与 2026-10-20 的 0.04 不同；回测统一用 0.04，偏保守。

## 七门（本次复核后）

1 机制描述清楚（但核心假设被否证）；2 部分满足（数据可免费取，官方源 403、镜像有偏差）；3 满足但深度数字不可复现；4 满足（017 已回挂 supplement）；5 **不满足**（回测负）；6 **不满足**（22 < 30）；7 基本满足（URL/日期/脚本齐全）。
