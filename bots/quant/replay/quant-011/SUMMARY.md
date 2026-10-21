# 回放汇总：quant-011

**条目**：`bots/quant/entries/quant-011-soccer-draw-pricing.md`  
**生成日期**：2026-10-21（UTC）  
**结论（先说）**：**负**。161 个独立触发（≥30），主窗口每美元投入净 **−22.82%**，中位每份净 **−0.2389**；把吃单费降到 0 仍 **−19.01%**，连 1¢ 半价差也去掉、直接用最后一笔成交打印价仍 **−15.33%**。按预先写死的失败标准判 **FAIL**，本条应 **DROP（丢弃）**，不要再用前向记录救。

> 复用说明：`bots/quant/notes/q011-hist/REPORT.md`（PR #9）用 `q011-hist/q011_hist.py` 跑过 data-api 成交价回放，报告主窗口 161 次触发、中位 −0.2389、每美元 −22.82%。本次 replay 沿用同一主逻辑（只加 `[T−1h,T]` 新鲜度窗口和 CLI 参数），并在 2026-10-21 重跑；主窗口与敏感性窗口的数字**逐项复现**，新增的 `[T−1h,T]` 窗口结果更差。原报告里“匹配 1,987 场”与“2,019/2,090”自相矛盾，以本次 `run_output` 的 **2,019/2,090 = 96.6%** 为准。
>
> 前向说明：`bots/quant/forward/quant-011/PLAN.md` 已在 2026-10-21 登记（2026-10-22 起 14 天），但 `ledger.csv` 只有表头、还没有结果。回放三窗口全负，**建议操作员不要开始或取消这份前向**；本 replay 没有使用、也没有改动 `forward/` 的任何文件。

## 如何复现

- 主脚本：`bots/quant/replay/quant-011/run_replay.py`（Python 3，`pandas`、`requests`；无密钥）
- 汇总脚本：`bots/quant/replay/quant-011/summarize.py`（只用 stdlib，读 `matches.csv`）
- 运行命令（在仓库根目录）：

```bash
python3 bots/quant/replay/quant-011/run_replay.py \
  --cache-dir bots/quant/notes/scheduler/scratch/P-quant-011/_cache \
  --out-dir  bots/quant/notes/scheduler/scratch/P-quant-011
python3 bots/quant/replay/quant-011/summarize.py

# 只看事件匹配、不下载成交：
python3 bots/quant/replay/quant-011/run_replay.py --match-only \
  --cache-dir bots/quant/notes/scheduler/scratch/P-quant-011/_cache
```

- 本次实际 stdout：
  - `bots/quant/notes/scheduler/scratch/P-quant-011/run_replay.stdout.txt`
  - `bots/quant/notes/scheduler/scratch/P-quant-011/summarize_from_replay.stdout.txt`
  - `bots/quant/notes/scheduler/scratch/P-quant-011/verify_sources.stdout.txt`
- 原始下载只进 `bots/quant/notes/scheduler/scratch/P-quant-011/_cache/`（已 `.gitignore`，不入库）；仓内只留处理后的 `trades.csv`、`summary.json`。
- **完整参数**：`bots/quant/replay/quant-011/params.json`。关键值：
  - 联赛：E0/I1/SP1/D1/F1（英超、意甲、西甲、德甲、法甲）
  - 基准率：`qD = (1/B365D)/(1/B365H+1/B365D+1/B365A)`；0.04 宽桶，从 0.14 起；同联赛同桶只用**严格早于该比赛赛季**的赛季（expanding walk-forward，无同赛季泄漏），n≥30；不足则回退五联赛合并同桶（仍 n≥30）。
  - 决策时点：`T = kickoff − 1h`（Gamma `gameStartTime`，UTC）。
  - 三个窗口：主 `[T−6h,T]`；敏感性 `[T−24h,T−1h]`；新鲜度 `[T−1h,T]`。
  - 成交价：窗口内**最后一笔 data-api YES 成交打印**；NO 打印按 `1−p` 换成 YES；可执行 ask 近似为 **last YES print + 0.01**（1¢ 半价差 / 一个 tick）。窗口内无打印 = unpriced，不填单。
  - 触发：`0.15 ≤ ask ≤ 0.30` 且 `ask ≤ base_rate − 0.02`；每场 1 份，持有到结算；一场比赛 = 1 个独立结果。
  - 费用：体育 taker `0.05`；每份 `fee = 0.05 × ask × (1−ask)`；`net = draw_payout − ask − fee`。1¢ 半价差已含在 ask 内，不重复扣。
- **数据下载地址和访问日期**（均 2026-10-21，免费、免密钥）：
  - Gamma closed events keyset：`https://gamma-api.polymarket.com/events/keyset?closed=true&tag_slug=<tag>&limit=100`（tag = EPL / premier-league / serie-a / la-liga / bundesliga / ligue-1；分页 `after_cursor`）
  - data-api 逐笔成交：`https://data-api.polymarket.com/trades?market=<conditionId>&limit=500&offset=N`
  - football-data：`https://www.football-data.co.uk/mmz4281/<season>/<league>.csv`，season = 1718…2627，league = E0/I1/SP1/D1/F1
  - 费率文档：`https://docs.polymarket.com/trading/fees`
  - 全部 URL 清单：`bots/quant/replay/quant-011/data_urls.md`
- **数据本身起点**：football-data 基准率历史最早 **2017-08-04**；被评估的 Polymarket closed 比赛最早 **2024-08-16**。
- **开发窗口**：**2024-08-16..2026-10-19**（被评估的已闭合比赛；Polymarket 无 2022–2024 的加密窗口限制）。基准率训练另用 2017/18–2025/26 的严格更早赛季，主项目可据此知道哪段已被看过。
- **切分依据**：没有调参挑段；三个窗口在看结果前写进脚本。基准率是 walk-forward，不使用同赛季或未来赛季。没有 2025+ 的“留出”要求适用（本条不是 crypto）。

## 成交和成本

- **成交价和时点**：data-api 的逐笔成交打印，不是 CLOB `prices-history`。主窗口取 `T−6h` 到 `T`（`T = kickoff−1h`）内最后一笔 YES 打印，决策与成交都在开赛前至少 1 小时；NO 打印换成 `1−p`。无打印不交易。
- **前视控制**：打印时间戳必须落在窗口内；结算结果只用 football-data `FTR` 与 Gamma `outcomePrices` 事后校验，不进入进场。
- **全部成本**：taker 费 `0.05×ask×(1−ask)`（ask=0.24 时约 0.00912/份，占 ask 的 3.8%）；1¢ 半价差已加到 ask；持有到结算，无二次交易费；无资金费/借币费。
- **资金和容量**：每场 50 USDT（entry 规则上限），按 ask≈0.24 约 208 份/场；单场 `orderMinSize=5`、tick=0.01。每年约 **74 次触发**（161/2.177 年），年投放约 3,700 USDT；未结算敞口按 entry 上限 500 USDT，单场所 2,500 USDT、总资金 5,000 USDT 都放得下。容量未用 L2 盘口验证（见“不可靠或失败原因”）。

## 汇总结果

- **独立结果数及计法**：主窗口 **161 场触发**（一场比赛 = 1 个独立结果，不按三个市场数）；敏感性 **164**；新鲜度 **151**。均 ≥30。
- **扣成本后净收益**（主窗口，1 份/场；`matches.csv` 2019 行，`trades.csv` 201 行触发并集）：

| 指标 | 主窗口 `[T−6h,T]` |
|---|---:|
| 触发场数 | 161 |
| 每份净收益中位数 | **−0.2389** |
| 每份净收益均值 | **−0.0525** |
| 每份净收益合计 | **−8.4533** |
| 每美元投入总净收益 | **−22.82%** |
| 每场净收益率均值 | **−22.18%** |
| 命中率（平局打出） | **18.6%** |
| 结算与 FTR 一致 | 2,019 / 2,019 = **100.0%** |

- **最大回撤**：**44.8%（2,239 USDT，占 5,000 USDT）**，按触发比赛日排序的**已实现**权益峰谷，含每场 50 USDT 的结算损益；**不是逐日盯市**，因为公开数据没有逐日盘口。敏感性窗口 23.1%、新鲜度窗口 41.7%。
- **对 5,000 USDT 的年化贡献**：**−16.4%**。算法：每场净收益率均值 −22.18% × 50 USDT/场 × 74.0 场/年 ÷ 5,000 = −820 USDT/年 ÷ 5,000 = **−16.4%**。敏感性窗口 −1.3%，新鲜度窗口 −17.1%。这是负贡献，不是可部署收益。
- **result**：**负**（扣全部成本后为负，且独立结果 ≥30）。
- **不可靠或失败原因**：
  1. **没有历史 L2 盘口**：closed 市场只有成交打印。ask = last print + 1¢ 是模型，不是观测；entry 要求的 `spread ≤ 0.02` 无法逐场核实。脚本里“modelled half-spread > 0.02 = 0/1986”只是假设，不能当作观测证据。
  2. **last print 可能陈旧**：主窗口最长 6 小时，敏感性 24 小时。为检验这一点新增 `[T−1h,T]` 新鲜度窗口，结果 **更差**（−26.03%），说明不是陈旧打印造成的假阴性。
  3. **匹配误差**：日期 ±1 天 + 归一化队名，2,019/2,090 = 96.6%；69 个未匹配（改期、2026/27 新升班马/队名差异），未进入结果。
  4. **data-api 上限**：每个市场约最近 2 万笔；热门市场在窗口内超过上限时可能截断。
  5. **分联赛样本小**：I1 仅 17 场匹配、4 次触发；F1 7 次触发。结论以 ALL 为准。
  6. **结论对成本不敏感**：零吃单费仍 −19.01%/美元；连 1¢ 半价差也去掉、直接用打印价仍 −15.33%。所以失败不是费用假设造成的。

## 所有变体（所有市场都要写，看了不用的也算）

- **variants（自己的）**：**3**
- **variants_ext（外部来源）**：**-**

| 序号 | 自己 / 外部来源 | 规则与全部参数 | 窗口 | 结果和位置 |
|---|---|---|---|---|
| V1 | 自己 | 主窗口 `[T−6h,T]`；last YES print + 0.01；band 0.15–0.30；`ask ≤ base_rate − 0.02`；fee 0.05；5 联赛；1 份/场 | 2024-08-16..2026-10-19 | 161 触发；中位 −0.2389/份；每美元 **−22.82%**；贡献 −16.4%；`run_replay.stdout.txt` / `summary.json` |
| V2 | 自己 | 敏感性窗口 `[T−24h,T−1h]`；其余同 V1 | 同上 | 164 触发；中位 −0.2389/份；每美元 **−3.21%**；贡献 −1.3% |
| V3 | 自己 | 新鲜度窗口 `[T−1h,T]`；其余同 V1 | 同上 | 151 触发；中位 −0.2389/份；每美元 **−26.03%**；贡献 −17.1% |
| D1 | 自己（诊断，不计入 variants） | V1 但 **taker fee = 0**（ask 仍含 1¢ 半价差） | 同上 | 161 触发；中位 −0.2300/份；每美元 **−19.01%** |
| D2 | 自己（诊断，不计入 variants） | V1 但 **fee = 0 且半价差 = 0**（直接用 last print，不可执行） | 同上 | 161 触发；中位 −0.2200/份；每美元 **−15.33%** |

> D1/D2 是成本压力测试，不是可交易变体；列出来是为了说明负结论不依赖费用假设。除这三个窗口外，没有试过“只做 E0”“换阈值/换桶宽”等事后挑参数的变体；原稿的 E0/I1 B365 分桶表是基准率校准，不是可成交价回放，未计入 variants。

## 产物

| 文件 | 内容 | 大小 |
|---|---|---:|
| `run_replay.py` | 回放主脚本（下载 + 匹配 + 成交 + 三窗口） | 38 KB |
| `summarize.py` | 离线汇总、`trades.csv`/`summary.json` 生成 | 7 KB |
| `params.json` | 完整参数 | 3 KB |
| `data_urls.md` | 数据 URL 清单 | 2 KB |
| `summary.json` | 结构化结果（三变体 + 两个诊断） | 2 KB |
| `trades.csv` | 201 行触发并集（含三窗口各自 net） | 38 KB |
| `SUMMARY.md` | 本文件 | — |

`matches.csv`（2,019 行、约 600 KB）在 `bots/quant/notes/scheduler/scratch/P-quant-011/`，是本回放的中间数据，不放进 `replay/` 以免与原始数据混淆。
