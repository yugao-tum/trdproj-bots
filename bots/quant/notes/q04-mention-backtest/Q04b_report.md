# Q04b：提及市场回测——把入场锚点换成真实讲话时间

- bot：quant
- 日期：2026-10-20（UTC）
- 工作目录：`/workspace/agent-tools/quant-r2prep/work_Q04b`
- 复用缓存：`/workspace/agent-tools/quant-batch2/work_Q04/cache`（Gamma 事件 1,313 个已关闭事件、CLOB 价格历史 3,124 个 token）
- 只用了免密钥公开 GET；没有下单、没有密钥、没有付费。
- 前作：`/workspace/trdproj-bots/bots/quant/notes/q04-mention-backtest/`、条目 `quant-004-pm-mention-base-rates.md`（本次只读，未改动）。

## 0. 结论先说

1. **Q04 的显著性主要来自前视偏差，纠正后消失。** 同样这 200 个最近事件里，Q04 用市场自己的 `endDate`（缺失时退回事件 `endDate`）当锚点时 R1（YES 价 0.05–0.35 买 NO）H24 的 t=2.37；改成“真实开始前 2 小时”后，R1 每 USDC **+1.67%**、事件均值 +4.23%、**t=1.19**（50 个事件），前后半段分别是 t=2.28 和 **t=−0.13**。
2. **扩到 400 个事件（163 个有可靠开始时间，120 个有成交）**，R1 全样本每 USDC **+5.04%**、事件均值 +5.41%、t=2.38；但**后半段 t=0.94**（每笔 +1.88%、事件均值 +3.43%），前半段 t=2.73。半价差从 0.01 加到 0.02 后全样本 t 降到 1.83、后半段 0.60。
3. 因此对本轮问题的直接回答：**R1 扣除吃单费+半个价差后，在样本外（时间后半段）不显著**；全样本的正号只在 400 事件版本、0.01 半价差设定下接近显著，属于多重比较（4 个块 × 2 个半价差 × 3 条规则 = 24 个组合）里挑出来的边缘结果，不能当作已证明的边。
4. R3（[0.05,0.95] 全部买 NO）在真实锚点下**显著为负**：200 样本 −6.13%/笔（t=−1.42），400 样本 −5.56%（t=−1.87），半价差 0.02 时 −7.91%（t=−2.66）。R2 在所有设定下都不显著。
5. 200 样本里只有 **87/200 = 43.5%** 的事件能拿到“描述里有明确日期+时刻+时区”的真实开始时间；期间型（周/月）44 个、只有日期没时刻 36 个、开放式“下一条视频/下一场直播”25 个、无时间 8 个全部排除。

---

## 1. 复现命令

```bash
cd /workspace/agent-tools/quant-r2prep/work_Q04b
mkdir -p cache
cp /workspace/agent-tools/quant-batch2/work_Q04/cache/events_mention-markets_*.json cache/
ln -sfn /workspace/agent-tools/quant-batch2/work_Q04/cache/clob cache/clob

python3 parse_start.py > start_times_output.txt 2>&1   # 步骤1：解析真实开始时间
python3 ext_fetch.py                                  # 步骤3b：抓 201–400 名事件的价格历史（1,554 个 token）
python3 q04b_bt.py > run_q04b.txt 2>&1                # 步骤2/3：无前视回测
python3 gen_md.py                                     # 生成本文件
```

本次新抓的只有 `ext_fetch.py` 里那 1,554 个 CLOB 历史（`curl -sL -A "Mozilla/5.0" --max-time 30`）。注意：`cache/clob` 是指向共享缓存的软链接，所以这 1,554 个 JSON 写在了 `/workspace/agent-tools/quant-batch2/work_Q04/cache/clob/` 下；只读仓库 `/workspace/trdproj-bots` 未被触碰。

抓取过程中发现的接口事实（有 curl 复现）：

- `interval=max` 对**较早**的已关闭市场返回 `{"history":[]}`。例：2026-07-05 Brazil vs Norway 那个市场，`?market=<token>&interval=max&fidelity=60` 只回 15 字节 `{"history":[]}`；改成 `startTs/endTs` 区间后能拿到数据（核查时 [开始−12天, 开始+1天]、fidelity=60 实测 11 个点，fidelity=10 为 68 个点；原稿写的 309 个点无法复现，已更正）。
- `startTs/endTs` 区间太长会被拒：`{"error":"invalid filters: 'startTs' and 'endTs' interval is too long"}`（用 3,000,000 秒试的）。所以扩展集每个 token 用 `[t_start−12d, t_start+1d]`、`fidelity=60`。

---

## 2. 步骤一：每个事件的“真实开始时间”

### 2.1 判定规则（在跑任何 P&L 之前写死，见 `parse_start.py` 顶注）

1. **只在描述文本里找**：`<Month> <D>, <YYYY>` + 可选 `at H[:MM] AM/PM <TZ>`，时区支持 ET/EST/EDT/CT/PT/UTC（用 `zoneinfo` 转 UTC）。
2. **排除期间型**：描述里出现 `between <date> ... and <date>`、`from <date> ... to <date>`，或标题含 `This Week`。
3. **排除“死线”**：紧挨在前面是 `by` 的时间（如 `by October 31, 2026, 11:59 PM ET`）不算开始；`between market creation and <date>, 11:59 PM ET` 也不算（这条规则把 `what-will-trump-say-during-his-united-nations-meetings` 从“explicit”降级为 date_only）。
4. **排除只有日期没有时刻**（date_only）、**开放式“next video/livestream/episode/trailer”**、**没有任何时间**的事件；有多个不同时刻的判 ambiguous（本次样本 0 个）。
5. **最终开始时间 = min(描述解析值, Gamma `event.startTime`)**（两者都存在时）。取更早的那个，保证入场点一定在讲话之前；取更晚的那个才可能引入前视。
6. **不用** `endDate`；`eventDate`（46/1313 个事件有，全为 00:00 时刻，是日期不是开始时间）；`markets[].eventStartTime`（本样本 1,493 个市场里 0 个有这个字段，全库 23,605 个市场里只有 665 个有）。

### 2.2 计数（精确输出见文末 `start_times_output.txt`）

| 类别 | 全部 1,313 个事件 | 200 个最近事件 |
|---|---:|---:|
| 有明确开始时间（explicit，可入场） | 425 | **87** |
| 期间型（period，排除） | 212 | 44 |
| 只有日期没时刻（date_only） | 323 | 36 |
| 开放式 next video/livestream（排除） | 92 | 25 |
| 没写时间（no_start_time） | 249 | 8 |
| 无描述 | 9 | 0 |
| 多个时刻（ambiguous，排除） | 3 | 0 |

- 200 样本里 **87 个事件（43.5%）拿到可靠开始时间**，覆盖 **1,493 个已结算市场**（这 1,493 个市场 `feeSchedule.rate` 全部是 0.04）。
- 400 事件扩展样本里 **163 个事件**可靠，覆盖 3,047 个已结算市场。

### 2.3 例子（slug / 描述原文 / 解析出的 UTC）

| slug | description 原文（日期时间片段） | 解析出的 UTC 开始时间 | Gamma `event.startTime` 差 |
|---|---|---|---:|
| `what-will-nvidia-say-during-their-next-earnings-call-20260826` | `August 26, 2026 at 5:00 PM ET` | 2026-08-26 21:00:00+00:00 | +0.00 h |
| `what-will-trump-say-during-remarks-at-nasa` | `August 28, 2026 at 11AM ET` | 2026-08-28 15:00:00+00:00 | +0.00 h |
| `what-will-kevin-warsh-say-during-his-speech-at-jackson-hole-01` | `August 28, 2026, 10 AM ET` | 2026-08-28 14:00:00+00:00 | +0.00 h |
| `what-will-trump-say-during-healthcare-affordability-announcement` | `August 31, 2026 at 3PM ET` | 2026-08-31 19:00:00+00:00 | +0.00 h |
| `what-will-john-ternus-say-during-his-apple-keynote-20260902` | `September 9, 2026, 1 PM ET` | 2026-09-09 17:00:00+00:00 | +0.00 h |
| `what-will-trump-say-during-his-midterm-rally-in-kansas-october-19` | `October 19, 2026 at 6:00 PM ET` | 2026-10-19 22:00:00+00:00 | +1.00 h |
| `what-will-jd-vance-say-during-rnc-convention` | `September 9, 2026 at 10 AM ET` | 2026-09-09 14:00:00+00:00 | +33.00 h |

（Kansas 这条特别值得记：描述写 6:00 PM ET，按 EDT=UTC−4 应为 22:00Z，但 Gamma `event.startTime` 是 23:00Z，市场自己的 `endDate` 是 22:05Z。三个来源互不一致；按 min 规则取 22:00Z，对“不许前视”是安全方向。）

### 2.4 Gamma 字段核对

- 87/87 个 explicit 事件都有 `event.startTime`；**81 个与描述解析值在 1 分钟内一致**（多数完全相等），median 差 0.0h，max 33.0h。
- 不一致的 6 个：
  - `what-will-jd-vance-say-during-rnc-convention`：描述 `September 9, 2026 at 10 AM ET`，Gamma 是 `2026-09-10T23:00:00Z`（+33h）。真实大会是晚间场，**描述写错了**，min 规则取描述值（更早）→ 入场更早，不产生前视。
  - `what-will-trump-say-during-rnc-convention-night-1`（+11.25h）、`...-september-10`（+11.0h）：同类错写。
  - `what-will-trump-say-during-remarks-in-north-carolina`（−1.0h）、`...xi-jinping`（−0.25h）、`...kansas-october-19`（+1.0h）：小时级偏差，min 规则处理。
- `eventDate` 只出现在 46/1313 个事件里，且都是 `00:00:00` 时刻（`eventDate hour/endDate hour` 统计里 46 个的 hour 全为 0），不能当作开始时间。
- `markets[].eventStartTime` 全库 23,605 个市场里 665 个有；在本次 1,493 个 explicit 市场里 **0 个**。它多数等于市场自己的 `endDate`（576/665 差 0 小时），不是讲话开始。

### 2.5 前视偏差到底有多大（同一 200 样本，1,493 个 explicit 市场）

| 指标 | 数值 |
|---|---:|
| `market.endDate − t_start`（小时）中位数 | 3.98 |
| 同上 p10 / p90 | 0.08 / 23.65 |
| `endDate − t_start` 在 10 分钟内的市场 | 524 |
| Q04 的 H6 锚点（`endDate−6h`）落在真实开始**之后**的市场 | **677 / 1,493 = 45.3%** |
| Q04 的 H24 锚点（`endDate−24h`）落在真实开始**之后**的市场 | 36 / 1,493 = 2.4% |

（这里的 `endDate` 指 Q04 实际用的 `markets[].endDate`，1,493 个市场里有 524 个它只比真实开始晚 ≤10 分钟，也有 657 个晚于开始 6–30 小时，其中 550 个 `endDate` 是当天 23:59、107 个是次日 03:59——都是“日终/周终”式截止，不是讲话时刻。）这解释了为什么 Q04 里 H6 的 R1 t=6.21 最漂亮、H24 是 2.37：**H6 有近一半的入场点在讲话之后**。另外 44 个期间型事件（周市场）的 `endDate` 是统计期结束，H24 锚点必然落在期间内部，等于用“已经说了一部分的词频”定价——这正是前作自己注明的偏差。

---

## 3. 步骤二/三：入场价与回测

### 3.1 事前写死的规则

- **入场价** = CLOB 中间价序列里，`t ≤ t_start − H` 的最后一个点，且该点必须 `≥ t_start − 10d`（沿用 Q04 的 10 天陈旧上限），并且必然 `< t_start`。H=**2 小时（主）**，H=**12 小时（稳健性）**。
- **成本** = 每份 `rate × p × (1−p)` 吃单费（`rate` 取市场自己的 `feeSchedule.rate`，缺省 0.04）+ 半个价差 **0.01（主）/ 0.02（敏感性）**，都从现金支出里扣；`ret=(payout−cost)/cost`。
- **规则不变**：R1 YES∈[0.05,0.35] 买 NO；R2 YES∈[0.65,0.95] 买 YES；R3 YES∈[0.05,0.95] 买 NO。全部报告，不挑。
- **统计按事件**：事件内先平均，再对事件均值做 t = mean/(sd/√n_events)。
- **样本外切分**：按 `t_start` 排序，取有成交的事件对半分成前半/后半。
- 4 个块（200/400 事件 × H2/H12）× 2 个半价差 × 3 条规则 = **24 个组合，全部下表列出**（每个组合再分 ALL/前半/后半）。

### 3.2 样本与覆盖

| 块 | explicit 事件 | 有入场价的市场 | 有成交的事件 | 掉样本原因 |
|---|---:|---:|---:|---|
| 200, H2 | 87 | 905 | 53 | CLOB 历史空 573，窗口内无点 15 |
| 200, H12 | 87 | 804 | 47 | CLOB 历史空 573，窗口内无点 116 |
| 400, H2 | 163 | 2,446 | 129 | CLOB 历史空 576，窗口内无点 25 |
| 400, H12 | 163 | 1,993 | 106 | CLOB 历史空 576，窗口内无点 478 |

- 入场点相对 `t_start` 的中位间隔：H2 为 3.0h（min 2.2 / max 6.5），H12 为 13.0h（min 12.2 / max 27.5）。即**所有入场点都在开始之前**。
- 价格点相对 cutoff 的陈旧度（中位数）：H2/H12 都是 1.0h（`fidelity=60` 的整点序列），p90 1.0h，最大 15.5h。
- “CLOB 历史空”的 573–576 个市场，与 Q04 报告的 1,482/3,124 空历史一致（很多冷门词市场没有中间价序列），这是**存活偏差**：能取到价格的多是有交易的市场。

### 3.3 结果（每 USDC 净收益，已扣费与半价差）

**200 事件，H2（主设定）**

| 规则 | 半价差 | 分组 | 笔数 | 事件数 | 胜率 | 每 USDC 均值 | 事件均值 | 事件 t |
|---|---:|---|---:|---:|---:|---:|---:|---:|
| R1 NO [0.05,0.35] | 0.01 | ALL | 256 | 50 | 0.8359 | +0.01669 | +0.04228 | +1.19 |
| R1 NO [0.05,0.35] | 0.01 | FIRST_HALF | 141 | 25 | 0.8582 | +0.04682 | +0.09184 | +2.28 |
| R1 NO [0.05,0.35] | 0.01 | SECOND_HALF | 115 | 25 | 0.8087 | -0.02025 | -0.00727 | -0.13 |
| R2 YES [0.65,0.95] | 0.01 | ALL | 276 | 52 | 0.8225 | +0.01651 | +0.01753 | +0.50 |
| R2 YES [0.65,0.95] | 0.01 | FIRST_HALF | 129 | 26 | 0.8295 | +0.01322 | +0.01187 | +0.20 |
| R2 YES [0.65,0.95] | 0.01 | SECOND_HALF | 147 | 26 | 0.8163 | +0.01939 | +0.02319 | +0.58 |
| R3 NO [0.05,0.95] | 0.01 | ALL | 778 | 53 | 0.5141 | -0.06125 | -0.08173 | -1.42 |
| R3 NO [0.05,0.95] | 0.01 | FIRST_HALF | 369 | 26 | 0.5501 | -0.03598 | -0.06268 | -0.76 |
| R3 NO [0.05,0.95] | 0.01 | SECOND_HALF | 409 | 27 | 0.4817 | -0.08405 | -0.10007 | -1.22 |
| R1 NO [0.05,0.35] | 0.02 | ALL | 256 | 50 | 0.8359 | +0.00435 | +0.02957 | +0.85 |
| R1 NO [0.05,0.35] | 0.02 | FIRST_HALF | 141 | 25 | 0.8582 | +0.03409 | +0.07842 | +1.98 |
| R1 NO [0.05,0.35] | 0.02 | SECOND_HALF | 115 | 25 | 0.8087 | -0.03210 | -0.01928 | -0.34 |
| R2 YES [0.65,0.95] | 0.02 | ALL | 276 | 52 | 0.8225 | +0.00396 | +0.00497 | +0.14 |
| R2 YES [0.65,0.95] | 0.02 | FIRST_HALF | 129 | 26 | 0.8295 | +0.00086 | -0.00061 | -0.01 |
| R2 YES [0.65,0.95] | 0.02 | SECOND_HALF | 147 | 26 | 0.8163 | +0.00669 | +0.01055 | +0.27 |
| R3 NO [0.05,0.95] | 0.02 | ALL | 778 | 53 | 0.5141 | -0.08366 | -0.10411 | -1.88 |
| R3 NO [0.05,0.95] | 0.02 | FIRST_HALF | 369 | 26 | 0.5501 | -0.05677 | -0.08321 | -1.04 |
| R3 NO [0.05,0.95] | 0.02 | SECOND_HALF | 409 | 27 | 0.4817 | -0.10791 | -0.12423 | -1.60 |

**200 事件，H12（稳健性）**

| 规则 | 半价差 | 分组 | 笔数 | 事件数 | 胜率 | 每 USDC 均值 | 事件均值 | 事件 t |
|---|---:|---|---:|---:|---:|---:|---:|---:|
| R1 NO [0.05,0.35] | 0.01 | ALL | 223 | 45 | 0.8296 | +0.00781 | +0.03278 | +0.97 |
| R1 NO [0.05,0.35] | 0.01 | FIRST_HALF | 116 | 22 | 0.8017 | -0.02415 | +0.01054 | +0.22 |
| R1 NO [0.05,0.35] | 0.01 | SECOND_HALF | 107 | 23 | 0.8598 | +0.04245 | +0.05406 | +1.13 |
| R2 YES [0.65,0.95] | 0.01 | ALL | 266 | 45 | 0.8271 | +0.01645 | +0.02609 | +0.79 |
| R2 YES [0.65,0.95] | 0.01 | FIRST_HALF | 124 | 22 | 0.8548 | +0.04021 | +0.04542 | +0.92 |
| R2 YES [0.65,0.95] | 0.01 | SECOND_HALF | 142 | 23 | 0.8028 | -0.00431 | +0.00760 | +0.17 |
| R3 NO [0.05,0.95] | 0.01 | ALL | 685 | 47 | 0.4949 | -0.08056 | -0.10024 | -1.85 |
| R3 NO [0.05,0.95] | 0.01 | FIRST_HALF | 327 | 23 | 0.4985 | -0.11796 | -0.13342 | -1.79 |
| R3 NO [0.05,0.95] | 0.01 | SECOND_HALF | 358 | 24 | 0.4916 | -0.04640 | -0.06843 | -0.87 |
| R1 NO [0.05,0.35] | 0.02 | ALL | 223 | 45 | 0.8296 | -0.00441 | +0.02026 | +0.61 |
| R1 NO [0.05,0.35] | 0.02 | FIRST_HALF | 116 | 22 | 0.8017 | -0.03601 | -0.00176 | -0.04 |
| R1 NO [0.05,0.35] | 0.02 | SECOND_HALF | 107 | 23 | 0.8598 | +0.02985 | +0.04132 | +0.88 |
| R2 YES [0.65,0.95] | 0.02 | ALL | 266 | 45 | 0.8271 | +0.00395 | +0.01337 | +0.41 |
| R2 YES [0.65,0.95] | 0.02 | FIRST_HALF | 124 | 22 | 0.8548 | +0.02755 | +0.03257 | +0.67 |
| R2 YES [0.65,0.95] | 0.02 | SECOND_HALF | 142 | 23 | 0.8028 | -0.01667 | -0.00499 | -0.11 |
| R3 NO [0.05,0.95] | 0.02 | ALL | 685 | 47 | 0.4949 | -0.10364 | -0.12312 | -2.36 |
| R3 NO [0.05,0.95] | 0.02 | FIRST_HALF | 327 | 23 | 0.4985 | -0.13724 | -0.15252 | -2.11 |
| R3 NO [0.05,0.95] | 0.02 | SECOND_HALF | 358 | 24 | 0.4916 | -0.07295 | -0.09494 | -1.25 |

**400 事件，H2（主设定）**

| 规则 | 半价差 | 分组 | 笔数 | 事件数 | 胜率 | 每 USDC 均值 | 事件均值 | 事件 t |
|---|---:|---|---:|---:|---:|---:|---:|---:|
| R1 NO [0.05,0.35] | 0.01 | ALL | 618 | 120 | 0.8576 | +0.05037 | +0.05413 | +2.38 |
| R1 NO [0.05,0.35] | 0.01 | FIRST_HALF | 336 | 60 | 0.8780 | +0.07691 | +0.07398 | +2.73 |
| R1 NO [0.05,0.35] | 0.01 | SECOND_HALF | 282 | 60 | 0.8333 | +0.01875 | +0.03427 | +0.94 |
| R2 YES [0.65,0.95] | 0.01 | ALL | 683 | 125 | 0.8199 | +0.01089 | +0.01548 | +0.69 |
| R2 YES [0.65,0.95] | 0.01 | FIRST_HALF | 343 | 62 | 0.8105 | +0.00574 | +0.01587 | +0.47 |
| R2 YES [0.65,0.95] | 0.01 | SECOND_HALF | 340 | 63 | 0.8294 | +0.01608 | +0.01510 | +0.51 |
| R3 NO [0.05,0.95] | 0.01 | ALL | 2095 | 129 | 0.5098 | -0.05562 | -0.06479 | -1.87 |
| R3 NO [0.05,0.95] | 0.01 | FIRST_HALF | 1165 | 64 | 0.5167 | -0.04858 | -0.05346 | -1.18 |
| R3 NO [0.05,0.95] | 0.01 | SECOND_HALF | 930 | 65 | 0.5011 | -0.06443 | -0.07594 | -1.44 |
| R1 NO [0.05,0.35] | 0.02 | ALL | 618 | 120 | 0.8576 | +0.03753 | +0.04117 | +1.83 |
| R1 NO [0.05,0.35] | 0.02 | FIRST_HALF | 336 | 60 | 0.8780 | +0.06373 | +0.06082 | +2.28 |
| R1 NO [0.05,0.35] | 0.02 | SECOND_HALF | 282 | 60 | 0.8333 | +0.00632 | +0.02152 | +0.60 |
| R2 YES [0.65,0.95] | 0.02 | ALL | 683 | 125 | 0.8199 | -0.00156 | +0.00297 | +0.13 |
| R2 YES [0.65,0.95] | 0.02 | FIRST_HALF | 343 | 62 | 0.8105 | -0.00673 | +0.00331 | +0.10 |
| R2 YES [0.65,0.95] | 0.02 | SECOND_HALF | 340 | 63 | 0.8294 | +0.00364 | +0.00263 | +0.09 |
| R3 NO [0.05,0.95] | 0.02 | ALL | 2095 | 129 | 0.5098 | -0.07909 | -0.08842 | -2.66 |
| R3 NO [0.05,0.95] | 0.02 | FIRST_HALF | 1165 | 64 | 0.5167 | -0.07204 | -0.07713 | -1.80 |
| R3 NO [0.05,0.95] | 0.02 | SECOND_HALF | 930 | 65 | 0.5011 | -0.08792 | -0.09954 | -1.96 |

**400 事件，H12（稳健性）**

| 规则 | 半价差 | 分组 | 笔数 | 事件数 | 胜率 | 每 USDC 均值 | 事件均值 | 事件 t |
|---|---:|---|---:|---:|---:|---:|---:|---:|
| R1 NO [0.05,0.35] | 0.01 | ALL | 534 | 101 | 0.8427 | +0.02667 | +0.03731 | +1.50 |
| R1 NO [0.05,0.35] | 0.01 | FIRST_HALF | 296 | 50 | 0.8547 | +0.03890 | +0.03794 | +1.01 |
| R1 NO [0.05,0.35] | 0.01 | SECOND_HALF | 238 | 51 | 0.8277 | +0.01146 | +0.03670 | +1.12 |
| R2 YES [0.65,0.95] | 0.01 | ALL | 579 | 103 | 0.8221 | +0.00815 | -0.00384 | -0.15 |
| R2 YES [0.65,0.95] | 0.01 | FIRST_HALF | 269 | 51 | 0.8104 | -0.00422 | -0.03348 | -0.82 |
| R2 YES [0.65,0.95] | 0.01 | SECOND_HALF | 310 | 52 | 0.8323 | +0.01888 | +0.02523 | +0.84 |
| R3 NO [0.05,0.95] | 0.01 | ALL | 1671 | 106 | 0.4973 | -0.08233 | -0.08264 | -2.13 |
| R3 NO [0.05,0.95] | 0.01 | FIRST_HALF | 905 | 53 | 0.5182 | -0.06859 | -0.05006 | -0.86 |
| R3 NO [0.05,0.95] | 0.01 | SECOND_HALF | 766 | 53 | 0.4726 | -0.09856 | -0.11522 | -2.23 |
| R1 NO [0.05,0.35] | 0.02 | ALL | 534 | 101 | 0.8427 | +0.01418 | +0.02462 | +1.00 |
| R1 NO [0.05,0.35] | 0.02 | FIRST_HALF | 296 | 50 | 0.8547 | +0.02630 | +0.02528 | +0.68 |
| R1 NO [0.05,0.35] | 0.02 | SECOND_HALF | 238 | 51 | 0.8277 | -0.00088 | +0.02397 | +0.74 |
| R2 YES [0.65,0.95] | 0.02 | ALL | 579 | 103 | 0.8221 | -0.00422 | -0.01608 | -0.64 |
| R2 YES [0.65,0.95] | 0.02 | FIRST_HALF | 269 | 51 | 0.8104 | -0.01646 | -0.04532 | -1.12 |
| R2 YES [0.65,0.95] | 0.02 | SECOND_HALF | 310 | 52 | 0.8323 | +0.00640 | +0.01260 | +0.42 |
| R3 NO [0.05,0.95] | 0.02 | ALL | 1671 | 106 | 0.4973 | -0.10592 | -0.10680 | -2.87 |
| R3 NO [0.05,0.95] | 0.02 | FIRST_HALF | 905 | 53 | 0.5182 | -0.09163 | -0.07383 | -1.33 |
| R3 NO [0.05,0.95] | 0.02 | SECOND_HALF | 766 | 53 | 0.4726 | -0.12281 | -0.13977 | -2.82 |

补充（从 `trades_q04b.csv` 直接算，hs=0.01）：

| 块 | R1 平均 YES 价 | R1 平均每份成本 | 胜率 | 盈亏平衡胜率 | 超额 |
|---|---:|---:|---:|---:|---:|
| 200 H2 | 0.195 | 0.805 | 0.836 | 0.805 | +3.1pp |
| 200 H12 | 0.194 | 0.806 | 0.830 | 0.806 | +2.4pp |
| 400 H2 | 0.199 | 0.801 | 0.858 | 0.801 | +5.6pp |
| 400 H12 | 0.195 | 0.805 | 0.843 | 0.805 | +3.7pp |

R1 在 200 样本里每事件中位 5 笔、最多 18 笔（50 个事件，只有 5 个事件各 1 笔）——事件内相关性已经用“先按事件平均”处理。

---

## 4. 扩展样本

- **事前指定**：把 Q04 的 200 个最近事件往前扩 200 个（按 `endDate` 排名 201–400，范围 2026-07-05 至 2026-08-25）。这 200 个事件里 76 个是 explicit（其余是期间/开放式/只有日期），涉及 **1,554 个唯一 YES token**。
- 全部抓取：1,554 个，非空 1,551 个（3 个失败）。
- 合并后 400 事件里 explicit 163 个、已结算市场 3,047 个、H2 可用 2,446 个市场 / 129 个事件。
- **没有继续往前扩**：再往前 200 个（排名 401–600，2026-04-30 至 2026-07-05）还有 **80 个 explicit 事件、1,876 个已关闭市场的 token**（已数，未抓），属时间预算之外，未查。
- 老事件必须用 `startTs/endTs` 才能取到历史（见第 1 节），这是本轮新发现；`interval=max` 会静默返回空数组，不会报错——**如果不做非空检查，会误以为“没有数据”而不是“接口没给”**。

---

## 5. 诚实解读（中文）

**做法上修掉的东西**：入场点现在锚在“事件描述里写明的开始时刻（并用 Gamma `startTime` 取下界）前 2 小时”，且强制早于开始；期间型、只有日期、开放式事件全部剔除；成本含吃单费与半价差，并做了 0.02 的敏感性；样本外按时间前后半切分；24 个组合全部列出。

**结果怎么读**：

- **R1 不再是显著策略。** 200 事件、H2、半价差 0.01：全样本 +1.67%/笔、t=1.19；后半段 −2.03%/笔、t=−0.13。半价差加到 0.02 后全样本 +0.44%/笔、t=0.85。前作 H24 的 t=2.37、H6 的 t=6.21 在真实锚点下不复现，且上一节量化了原因（H6 有 45.3% 的入场点在讲话之后）。
- **400 事件版本看起来更好，但也不构成样本外证据。** R1 H2、hs=0.01：全样本 +5.04%/笔、t=2.38；前半 t=2.73、**后半 t=0.94**。hs=0.02 时全样本 t=1.83、后半 0.60。正号集中在 2026-07-05 至 08-07 的前半段；按时间顺序看，8 个 R1 设定（2 样本 × 2 水平 × 2 半价差）的后半段 t 落在 −0.34 至 +1.13 之间，没有一个显著。
- **R3 是明确的反例**：全区间买 NO 在真实锚点下显著亏（−5.6% 至 −8.4%/笔，t 到 −2.66），说明“提及市场整体高估热词”这个粗结论不成立，前作 R3 的 +1.56% 是锚点错误的产物。
- **R2（高价买 YES）始终≈0**：全样本 −0.2% 至 +1.7%/笔，t 绝对值 ≤0.79；半价差 0.02 下为 −0.2% 至 +0.4%/笔。没有任何可做的边。
- **多重比较**：24 个组合里最好的一个（R1/400/H2/hs=0.01，t=2.38，单看双侧 p≈0.02）在 24 次尝试下并不稀奇；按 24 倍放大后 p≈0.4，不显著。
- **成本结构决定了这个市场很难做**：R1 平均每份成本 0.80，胜率必须 >80% 才不亏；实测胜率 83.6%–85.8%，超额只有 2.4–5.6 个百分点。半个价差从 0.01 变 0.02 就吃掉约 1.3–1.6 个百分点。真实 L2 盘口不公开，0.01 的假设可能偏乐观（前作观察到同事件不同词市场 spread 从 0.001 到 0.86）。
- **仍然存在的偏差**：CLOB 历史缺失的 573–576 个市场（约 38% 的 explicit 市场）被丢弃，能取到价格的偏向有成交的市场；`fidelity=60` 的中间价不是可成交价；事件描述本身的时刻可能写错（RNC 三例），min 规则只保证“不晚于描述时刻”，不能保证“不晚于真实讲话”——如果某个事件描述时刻比实际讲话晚 2 小时以上，仍会引入前视，本轮无法逐一核实真实转播时间（未查到免费、可批量核对的转播时间源）。

**一句话**：把锚点修正到真实开始时间后，**前作最有希望的 R1 在扣掉吃单费与半个价差后不再显著，样本外（时间后半段）为负或接近零**；本轮回测不支持 `quant-004` 作为有正期望的策略，条目应维持“未证明”，不能按已证明的边来写。

---

## 6. 未查到 / 局限

- **真实讲话的转播时间**：没有找到免费、免密钥、可批量查询“某场活动实际开始时刻”的源（Gamma 只有 `startTime` 这个可能被人工填错/更新的字段）。本轮只能用“描述 + Gamma 取更早者”近似；RNC 三例证明描述会写错。
- **历史 L2 盘口**：不公开（GUIDE 第 8 节同）。半价差 0.01/0.02 都是假设，不是实测。
- **201–400 名事件中 3 个 token 的 CLOB 历史抓取失败**：未查明原因（HTTP 200 但空/解析失败），已按缺失处理。
- **成交量加权**：本轮所有交易等权 1 份，没有按 volume 加权，也没有考虑单市场深度；容量结论未做。
- **`markets[].eventStartTime` 的含义**：本样本 0 个存在，未进一步核实其全库语义（665 个市场里 576 个等于 `endDate`）。

---

## 7. 附：完整脚本（分析用；本文件的表格由 `gen_md.py` 从 `results_q04b.csv` 生成）

### parse_start.py

```python
#!/usr/bin/env python3
"""Q04b step 1: recover the TRUE start time of each mention-market event.

Pre-specified (written before looking at outcomes):
  * Explicit start = a calendar date AND clock time AND timezone in the event
    description, e.g. "scheduled for October 17, 2026 at 2:00 PM ET".
  * EXCLUDE period / week markets: description matches
    "between <date> ... and <date>" / "from <date> to <date>" / "this week".
  * EXCLUDE events whose description gives no clock time (date-only), and
    open-ended "next video / next livestream / next trailer" events, and
    events with >1 distinct explicit datetime that is not a range.
  * Source of each start time is recorded: 'description' (primary),
    cross-checked against Gamma event.startTime / markets[].eventStartTime.
"""
import glob, json, re, collections, datetime as dt
from zoneinfo import ZoneInfo

MONTHS = {m: i for i, m in enumerate(
    "January February March April May June July August September October "
    "November December".split(), 1)}
TZ = {"ET": "America/New_York", "EST": "America/New_York", "EDT": "America/New_York",
      "CT": "America/Chicago", "CST": "America/Chicago", "CDT": "America/Chicago",
      "PT": "America/Los_Angeles", "PST": "America/Los_Angeles", "PDT": "America/Los_Angeles",
      "UTC": "UTC", "GMT": "UTC"}
DATE = r"(?:January|February|March|April|May|June|July|August|September|October|November|December)"
# date + optional ", at H:MM AM/PM TZ"
DT_RE = re.compile(
    r"\b(" + DATE + r")\s+(\d{1,2}),?\s+(\d{4})"
    r"(?:,?\s+(?:at\s+)?(\d{1,2})(?::(\d{2}))?\s*([AP])\.?M\.?\s*(ET|EST|EDT|CT|CST|CDT|PT|PST|PDT|UTC|GMT))?")
RANGE_RE = re.compile(
    r"\bbetween\s+" + DATE + r"\s+\d{1,2},?\s+\d{4}.*?\band\s+" + DATE + r"\s+\d{1,2},?\s+\d{4}", re.S)
FROMTO_RE = re.compile(
    r"\bfrom\s+" + DATE + r"\s+\d{1,2},?\s+\d{4}.*?\bto\s+" + DATE + r"\s+\d{1,2},?\s+\d{4}", re.S)


def parse_dt(s):
    if not s:
        return None
    try:
        return dt.datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    except Exception:
        return None


def find_datetimes(text):
    out = []
    for m in DT_RE.finditer(text):
        mon, day, yr, hh, mi, ap, tz = m.groups()
        # deadline phrasing "by <date>, 11:59 PM ET" is NOT a start time
        before = text[max(0, m.start() - 60):m.start()]
        if re.search(r"\bby\s*$", before):
            continue
        # "... between market creation and <date>, 11:59 PM ET" = deadline, not start
        if re.search(r"\b(between|from)\b[^.]*$", before):
            continue
        if hh is None:
            out.append({"dt": None, "raw": m.group(0), "date_only": True})
            continue
        h = int(hh) % 12 + (12 if ap.upper() == "P" else 0)
        local = dt.datetime(int(yr), MONTHS[mon], int(day), h, int(mi or 0),
                            tzinfo=ZoneInfo(TZ[tz]))
        out.append({"dt": local.astimezone(dt.timezone.utc), "raw": m.group(0),
                    "date_only": False, "tz": tz})
    return out


def classify(e):
    d = re.sub(r"\s+", " ", e.get("description") or "")
    slug = e.get("slug") or ""
    title = e.get("title") or ""
    if not d:
        return {"kind": "no_description", "start_utc": None}
    # period / week markets
    if RANGE_RE.search(d) or FROMTO_RE.search(d) or re.search(r"\bthis week\b|\bThis Week\b", title):
        return {"kind": "period", "start_utc": None}
    dts = find_datetimes(d)
    full = [x for x in dts if not x["date_only"]]
    uniq = sorted({x["dt"] for x in full})
    if len(uniq) == 1:
        x = [y for y in full if y["dt"] == uniq[0]][0]
        return {"kind": "explicit", "start_utc": uniq[0], "raw": x["raw"],
                "tz": x["tz"], "date_only_seen": len(dts) - len(full)}
    if len(uniq) > 1:
        return {"kind": "ambiguous_multiple", "start_utc": None,
                "raws": [x["raw"] for x in full][:4]}
    if any(x["date_only"] for x in dts):
        return {"kind": "date_only", "start_utc": None,
                "raw": [x["raw"] for x in dts if x["date_only"]][0]}
    if re.search(r"\bnext (video|livestream|episode|trailer|gaming video|release)\b", d, re.I):
        return {"kind": "open_ended_no_start", "start_utc": None}
    return {"kind": "no_start_time", "start_utc": None}


def main():
    evs = []
    for f in sorted(glob.glob("cache/events_mention-markets_*.json")):
        evs += json.load(open(f))
    evs = {str(e["id"]): e for e in evs}
    rows = []
    for eid, e in evs.items():
        c = classify(e)
        st = parse_dt(e.get("startTime"))
        mst = [parse_dt(m.get("eventStartTime")) for m in (e.get("markets") or [])]
        mst = [x for x in mst if x]
        row = {"event_id": eid, "slug": e.get("slug"), "title": e.get("title"),
               "endDate": e.get("endDate"), "startTime_gamma": e.get("startTime"),
               "n_markets": len(e.get("markets") or []), **c}
        if c["kind"] == "explicit":
            row["gamma_startTime_delta_h"] = (
                round((st - c["start_utc"]).total_seconds() / 3600, 2) if st else None)
            row["gamma_market_eventStartTime_delta_h"] = (
                round((mst[0] - c["start_utc"]).total_seconds() / 3600, 2) if mst else None)
        rows.append(row)
    rows.sort(key=lambda r: r["endDate"] or "")
    json.dump(rows, open("start_times.json", "w"), indent=1, default=str)

    kinds = collections.Counter(r["kind"] for r in rows)
    print("all events:", len(rows), dict(kinds))
    NOW = dt.datetime(2026, 10, 20, tzinfo=dt.timezone.utc)
    past = [r for r in rows if parse_dt(r["endDate"]) and parse_dt(r["endDate"]) <= NOW]
    print("events with endDate <= 2026-10-20:", len(past))
    sample = past[-200:]
    print("\nPRE-SPECIFIED 200 most recent events by endDate:",
          sample[0]["endDate"], "..", sample[-1]["endDate"])
    print("kinds in sample:", dict(collections.Counter(r["kind"] for r in sample)))
    ex = [r for r in sample if r["kind"] == "explicit"]
    print("explicit-start events in sample:", len(ex),
          "| markets in them:", sum(r["n_markets"] for r in ex))
    print("\nexamples (slug | quoted text | parsed UTC):")
    for r in ex[:12]:
        print(f"  {r['slug']}")
        print(f"     \"{r['raw']}\"  ->  {r['start_utc']}  (tz={r['tz']}, "
              f"gamma startTime delta={r.get('gamma_startTime_delta_h')}h, "
              f"mkt eventStartTime delta={r.get('gamma_market_eventStartTime_delta_h')}h, "
              f"endDate={r['endDate']})")
    print("\nexcluded kinds, examples:")
    for k in ("period", "ambiguous_multiple", "date_only", "open_ended_no_start", "no_start_time"):
        rs = [r for r in sample if r["kind"] == k]
        print(f"  {k}: {len(rs)}")
        for r in rs[:3]:
            print(f"     {r['slug']}  raw={r.get('raw') or r.get('raws')} endDate={r['endDate']}")
    # how often does gamma startTime agree with parsed start?
    dl = [r["gamma_startTime_delta_h"] for r in ex if r.get("gamma_startTime_delta_h") is not None]
    agree = sum(1 for x in dl if abs(x) < 0.02)
    print(f"\nGamma event.startTime present for {len(dl)}/{len(ex)} explicit events; "
          f"agrees with parsed start within 1 min: {agree}; "
          f"abs delta hours: median={sorted(map(abs,dl))[len(dl)//2] if dl else None}, "
          f"max={max(map(abs,dl)) if dl else None}")
    md = [r["gamma_market_eventStartTime_delta_h"] for r in ex
          if r.get("gamma_market_eventStartTime_delta_h") is not None]
    print(f"Gamma markets[].eventStartTime present for {len(md)}/{len(ex)} explicit events; "
          f"agrees within 1 min: {sum(1 for x in md if abs(x)<0.02)}; max abs delta={max(map(abs,md)) if md else None}h")


if __name__ == "__main__":
    main()
```

### ext_fetch.py

```python
#!/usr/bin/env python3
"""Q04b step 3b: fetch CLOB price history for explicit-start events OLDER than
the Q04 200-event sample.

PRE-SPECIFIED extension: the 200 events immediately before the Q04 sample
(ranks 201-400 by endDate).  Window per token = [t_start-12d, t_start+1d],
fidelity=60 (minute-level would be too many points).

Note: for these older markets `interval=max` returns {"history":[]} (tested:
2026-07-05 Brazil vs Norway market), so startTs/endTs is required.
Only keyless public GETs, via curl.
"""
import glob, json, os, subprocess, datetime as dt
from concurrent.futures import ThreadPoolExecutor
from parse_start import classify, parse_dt

NOW = dt.datetime(2026, 10, 20, tzinfo=dt.timezone.utc)
OUT = "cache/clob"


def main():
    evs = {}
    for f in sorted(glob.glob("cache/events_mention-markets_*.json")):
        for e in json.load(open(f)):
            evs[str(e["id"])] = e
    past = [e for e in evs.values() if parse_dt(e.get("endDate")) and parse_dt(e["endDate"]) <= NOW]
    past.sort(key=lambda e: e["endDate"])
    ext = past[-400:-200]
    jobs = []
    for e in ext:
        c = classify(e)
        if c["kind"] != "explicit":
            continue
        st = c["start_utc"]
        g = parse_dt(e.get("startTime"))
        if g is not None:
            st = min(st, g)
        a = int((st - dt.timedelta(days=12)).timestamp())
        b = int((st + dt.timedelta(days=1)).timestamp())
        for m in (e.get("markets") or []):
            if not m.get("closed"):
                continue
            try:
                t = json.loads(m["clobTokenIds"])
            except Exception:
                continue
            if isinstance(t, list) and len(t) == 2:
                jobs.append((t[0], a, b))
    seen = {}
    for tok, a, b in jobs:
        seen.setdefault(tok, (a, b))
    print(f"[ext] events {ext[0]['endDate']} .. {ext[-1]['endDate']}: {len(ext)} events, "
          f"{len(seen)} unique YES tokens", flush=True)

    def work(item):
        tok, (a, b) = item
        p = os.path.join(OUT, tok + ".json")
        url = (f"https://clob.polymarket.com/prices-history?market={tok}"
               f"&startTs={a}&endTs={b}&fidelity=60")
        r = subprocess.run(["curl", "-sL", "-A", "Mozilla/5.0", "--max-time", "30", url],
                           capture_output=True, text=True)
        try:
            obj = json.loads(r.stdout)
        except Exception:
            obj = {"_error": True, "raw": r.stdout[:200]}
        with open(p, "w") as f:
            json.dump(obj, f)
        return isinstance(obj, dict) and not obj.get("_error") and bool(obj.get("history"))

    items = list(seen.items())
    ok = 0
    with ThreadPoolExecutor(max_workers=6) as pool:
        for i, good in enumerate(pool.map(work, items), 1):
            ok += 1 if good else 0
            if i % 200 == 0:
                print(f"[ext] {i}/{len(items)} fetched, non-empty {ok}", flush=True)
    print(f"[ext] done: {len(items)} fetched, non-empty {ok}", flush=True)


if __name__ == "__main__":
    main()
```

### q04b_bt.py

```python
#!/usr/bin/env python3
"""Q04b: mention-market backtest with NO look-ahead.

Entry time is anchored on the TRUE event start recovered in parse_start.py
(description text first, cross-checked / tightened with Gamma event.startTime),
NOT on Gamma endDate (which is a deadline or a period end).

PRE-SPECIFIED (written before looking at any P&L):
  * Sample: same 200 most recent closed events (endDate <= now) as Q04, so the
    only change is the entry clock.  Additionally, older explicit-start events
    are added only if their CLOB history can be fetched (see ext_fetch.py).
  * Keep only events whose start time is explicit AND reliable:
      - one date + clock + timezone in the description (see parse_start.py),
      - description is not a period/week market,
      - "by <date>, 11:59 PM ET" deadlines and "between ... and ..." are not starts.
    t_start = min(description_parsed, Gamma event.startTime) when both exist
    (the earlier of the two = conservative, cannot be after the speech).
  * Entry price = last CLOB mid-price point with t <= t_start - H, and the point
    must also be >= t_start - 10d (same 10-day staleness window as Q04).
    H = 2h (primary, pre-specified) and H = 12h (robustness).
  * Cost per share = rate*p*(1-p) taker fee (rate from feeSchedule, else 0.04)
    + half spread 0.01 (primary) and 0.02 (sensitivity).
  * P&L: buy 1 share at p, hold to resolution; ret = (payout - cost)/cost.
  * Rules, unchanged from Q04: R1 buy NO for YES in [0.05,0.35]; R2 buy YES for
    YES in [0.65,0.95]; R3 buy NO for YES in [0.05,0.95].
  * Stats: average inside event first, then t = mean/(sd/sqrt(n_events)).
  * Out-of-sample split: events sorted by t_start, first half vs second half.
"""
import csv, glob, json, math, os, statistics as st, sys
import datetime as dt
from parse_start import classify, parse_dt, find_datetimes

CACHE_CLOB = "cache/clob"
N_RECENT = 200
LOOKBACK_SEC = 10 * 86400
HORIZONS = [("H2", 2 * 3600), ("H12", 12 * 3600)]
HALF_SPREADS = [0.01, 0.02]
RULES = [("R1", "NO", 0.05, 0.35), ("R2", "YES", 0.65, 0.95), ("R3", "NO", 0.05, 0.95)]
NOW = dt.datetime(2026, 10, 20, tzinfo=dt.timezone.utc)


def as_list(x):
    if isinstance(x, list):
        return x
    if isinstance(x, str):
        try:
            v = json.loads(x)
            return v if isinstance(v, list) else []
        except Exception:
            return []
    return []


def fee_rate_of(m):
    fs = m.get("feeSchedule")
    if isinstance(fs, str):
        try:
            fs = json.loads(fs)
        except Exception:
            fs = None
    if isinstance(fs, dict) and fs.get("rate") is not None:
        return float(fs["rate"]), "feeSchedule"
    if m.get("feeRate") is not None:
        return float(m["feeRate"]), "feeRate"
    return 0.04, "default"


def resolution(m):
    outs = [str(x).strip().lower() for x in as_list(m.get("outcomes"))]
    prices = [str(x).strip() for x in as_list(m.get("outcomePrices"))]
    toks = [str(x) for x in as_list(m.get("clobTokenIds"))]
    if len(outs) != 2 or len(prices) != 2 or len(toks) != 2:
        return None
    if "yes" not in outs or "no" not in outs:
        return None
    yi, ni = outs.index("yes"), outs.index("no")
    if prices[yi] == "1" and prices[ni] == "0":
        ry = True
    elif prices[yi] == "0" and prices[ni] == "1":
        ry = False
    else:
        return None
    return {"yes_token": toks[yi], "resolved_yes": ry}


def load_events():
    evs = {}
    for f in sorted(glob.glob("cache/events_mention-markets_*.json")):
        for e in json.load(open(f)):
            evs[str(e["id"])] = e
    return evs


def start_of(e):
    """Return (t_start_utc, kind, source, parsed, gamma)."""
    c = classify(e)
    if c["kind"] != "explicit":
        return None, c["kind"], None, None, None
    parsed = c["start_utc"]
    gamma = parse_dt(e.get("startTime"))
    if gamma is not None:
        t = min(parsed, gamma)
        src = "description+gamma(min)" if gamma != parsed else "description=gamma"
    else:
        t = parsed
        src = "description"
    return t, "explicit", src, parsed, gamma


def market_rows(e, t_start, src):
    out = []
    eid = str(e["id"])
    for m in (e.get("markets") or []):
        if not m.get("closed"):
            continue
        res = resolution(m)
        if res is None:
            continue
        rate, rsrc = fee_rate_of(m)
        out.append({"event_id": eid, "event_slug": e.get("slug"),
                    "market_id": str(m.get("id")), "market_slug": m.get("slug"),
                    "question": m.get("question"), "yes_token": res["yes_token"],
                    "resolved_yes": res["resolved_yes"], "fee_rate": rate,
                    "fee_src": rsrc, "t_start": t_start, "start_src": src,
                    "start_date": t_start.date().isoformat()})
    return out


def get_hist(token):
    p = os.path.join(CACHE_CLOB, token + ".json")
    if not os.path.exists(p):
        return None
    obj = json.load(open(p))
    if isinstance(obj, dict) and obj.get("_error"):
        return None
    return obj.get("history", []) if isinstance(obj, dict) else obj


def pick(hist, cutoff, floor):
    best = None
    for pt in (hist or []):
        try:
            t, p = float(pt["t"]), float(pt["p"])
        except Exception:
            continue
        if floor <= t <= cutoff:
            if best is None or t > best[0]:
                best = (t, p)
    return best


def summarize(trades):
    if not trades:
        return dict(trades=0, events=0, win=float("nan"), mean=float("nan"),
                    emean=float("nan"), t=float("nan"))
    by = {}
    for t in trades:
        by.setdefault(t["event_id"], []).append(t["ret"])
    em = [sum(v) / len(v) for v in by.values()]
    sd = st.stdev(em) if len(em) > 1 else float("nan")
    tt = (sum(em) / len(em)) / (sd / math.sqrt(len(em))) if len(em) > 1 and sd > 0 else float("nan")
    return dict(trades=len(trades), events=len(by),
                win=sum(1 for x in trades if x["ret"] > 0) / len(trades),
                mean=sum(x["ret"] for x in trades) / len(trades),
                emean=sum(em) / len(em), t=tt)


def f(x, n=4):
    if x is None:
        return "NA"
    if isinstance(x, float) and (math.isnan(x) or math.isinf(x)):
        return "NA"
    return f"{x:.{n}f}" if isinstance(x, float) else str(x)


def run_sample(name, sample, results, detail, tag):
    print(f"\n######## SAMPLE {name}: {len(sample)} events "
          f"({sample[0].get('endDate')} .. {sample[-1].get('endDate')}) ########")
    rows = []
    kinds = {}
    srcs = {}
    explicit_events = 0
    for e in sample:
        t, kind, src, parsed, gamma = start_of(e)
        kinds[kind] = kinds.get(kind, 0) + 1
        if t is None:
            continue
        explicit_events += 1
        srcs[src] = srcs.get(src, 0) + 1
        rows += market_rows(e, t, src)
    print(f"[start] kinds in sample: {kinds}")
    print(f"[start] explicit+reliable events: {explicit_events}/{len(sample)}; source: {srcs}")
    print(f"[start] resolved markets inside those events: {len(rows)} "
          f"(feeSchedule rate: {sum(1 for r in rows if r['fee_src']=='feeSchedule')})")
    print(f"[start] markets in the whole sample (incl. periods/open-ended): "
          f"{sum(len(e.get('markets') or []) for e in sample)}")

    for hname, hsec in HORIZONS:
        subset = []
        why = {}
        for m in rows:
            h = get_hist(m["yes_token"])
            if not h:
                why["no_or_empty_history"] = why.get("no_or_empty_history", 0) + 1
                continue
            got = pick(h, m["t_start"].timestamp() - hsec, m["t_start"].timestamp() - LOOKBACK_SEC)
            if got is None:
                why["no_point_in_window"] = why.get("no_point_in_window", 0) + 1
                continue
            m = dict(m)
            m["p"] = got[1]
            m["age_h"] = (m["t_start"].timestamp() - hsec - got[0]) / 3600.0
            m["gap_h"] = (m["t_start"].timestamp() - got[0]) / 3600.0
            subset.append(m)
        why["usable"] = len(subset)
        ages = sorted(m["age_h"] for m in subset)
        gaps = sorted(m["gap_h"] for m in subset)
        print(f"\n===== {tag} {hname} =====  markets with an entry price: {len(subset)} "
              f"({len({m['event_id'] for m in subset})} events); dropped reasons {why}")
        if ages:
            print(f"[{tag} {hname}] staleness before cutoff (h): median={st.median(ages):.1f} "
                  f"p90={ages[int(0.9*(len(ages)-1))]:.1f} max={max(ages):.1f}")
            print(f"[{tag} {hname}] entry-to-start gap (h): median={st.median(gaps):.1f} "
                  f"min={min(gaps):.1f} max={max(gaps):.1f}")

        for hs in HALF_SPREADS:
            for rname, side, lo, hi in RULES:
                trades = []
                for m in subset:
                    p = m["p"]
                    if not (lo - 1e-12 <= p <= hi + 1e-12):
                        continue
                    price = p if side == "YES" else 1.0 - p
                    win = m["resolved_yes"] if side == "YES" else (not m["resolved_yes"])
                    fee = m["fee_rate"] * price * (1.0 - price)
                    cash = price + fee + hs
                    ret = ((1.0 if win else 0.0) - cash) / cash
                    trades.append(dict(ret=ret, event_id=m["event_id"],
                                       start_date=m["start_date"], side=side, p=p,
                                       paid=price, fee=fee, win=win, market_id=m["market_id"]))
                    detail.append(dict(sample=tag, h=hname, hs=hs, rule=rname, side=side,
                                       event_id=m["event_id"], event_slug=m["event_slug"],
                                       start_date=m["start_date"], start_src=m["start_src"],
                                       market_slug=m["market_slug"], question=m["question"],
                                       yes_price=p, paid=price, fee_rate=m["fee_rate"],
                                       fee=fee, cash_out=cash, gap_h=round(m["gap_h"], 2),
                                       resolved_yes=m["resolved_yes"], win=win, ret=ret))
                ev_dates = {t["event_id"]: t["start_date"] for t in trades}
                es = sorted(ev_dates.items(), key=lambda kv: kv[1])
                mid = len(es) // 2
                first = {k for k, _ in es[:mid]}
                second = {k for k, _ in es[mid:]}
                print(f"\n  {rname} buy {side} YES in [{lo},{hi}]  half_spread={hs}")
                for split, ts in (("ALL", trades),
                                  ("FIRST_HALF", [t for t in trades if t["event_id"] in first]),
                                  ("SECOND_HALF", [t for t in trades if t["event_id"] in second])):
                    s = summarize(ts)
                    print(f"    {split:<12} trades={s['trades']:>4} events={s['events']:>4} "
                          f"win={f(s['win']):>6} mean_ret/USDC={f(s['mean'],5):>9} "
                          f"event_mean={f(s['emean'],5):>9} t={f(s['t'],2):>6}")
                    results.append(dict(sample=tag, h=hname, half_spread=hs, rule=rname, side=side,
                                        yes_lo=lo, yes_hi=hi, split=split,
                                        trades=s["trades"], events=s["events"],
                                        win_rate=s["win"], mean_ret_per_usdc=s["mean"],
                                        event_mean_ret=s["emean"], event_tstat=s["t"]))


def main():
    evs = load_events()
    past = [e for e in evs.values() if parse_dt(e.get("endDate")) and parse_dt(e["endDate"]) <= NOW]
    past.sort(key=lambda e: e["endDate"])
    sample = past[-N_RECENT:]
    ext = past[-2 * N_RECENT:]
    print(f"[events] cached events={len(evs)} past={len(past)} "
          f"Q04-comparable sample={len(sample)} ({sample[0]['endDate']} .. {sample[-1]['endDate']})")
    results, detail = [], []
    run_sample("Q04-200", sample, results, detail, "S200")
    run_sample("EXT-400", ext, results, detail, "S400")

    with open("results_q04b.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(results[0].keys()))
        w.writeheader(); w.writerows(results)
    with open("trades_q04b.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(detail[0].keys()))
        w.writeheader(); w.writerows(detail)
    print(f"\n[save] results_q04b.csv ({len(results)} rows), trades_q04b.csv ({len(detail)} rows)")


if __name__ == "__main__":
    main()
```


## 8. 附：完整输出

### start_times_output.txt

```text
all events: 1313 {'explicit': 425, 'no_start_time': 249, 'no_description': 9, 'date_only': 323, 'period': 212, 'ambiguous_multiple': 3, 'open_ended_no_start': 92}
events with endDate <= 2026-10-20: 1306

PRE-SPECIFIED 200 most recent events by endDate: 2026-08-26T23:59:00Z .. 2026-10-19T23:05:00Z
kinds in sample: {'explicit': 87, 'no_start_time': 8, 'open_ended_no_start': 25, 'date_only': 36, 'period': 44}
explicit-start events in sample: 87 | markets in them: 1493

examples (slug | quoted text | parsed UTC):
  what-will-nvidia-say-during-their-next-earnings-call-20260826
     "August 26, 2026 at 5:00 PM ET"  ->  2026-08-26 21:00:00+00:00  (tz=ET, gamma startTime delta=0.0h, mkt eventStartTime delta=Noneh, endDate=2026-08-26T23:59:00Z)
  what-will-ulta-say-during-their-next-earnings-call
     "August 27, 2026 at 4:30 PM ET"  ->  2026-08-27 20:30:00+00:00  (tz=ET, gamma startTime delta=0.0h, mkt eventStartTime delta=Noneh, endDate=2026-08-27T23:59:00Z)
  what-will-best-buy-say-during-their-next-earnings-call
     "August 27, 2026 at 8:00 AM ET"  ->  2026-08-27 12:00:00+00:00  (tz=ET, gamma startTime delta=0.0h, mkt eventStartTime delta=Noneh, endDate=2026-08-27T23:59:00Z)
  what-will-trump-say-during-remarks-at-nasa
     "August 28, 2026 at 11AM ET"  ->  2026-08-28 15:00:00+00:00  (tz=ET, gamma startTime delta=0.0h, mkt eventStartTime delta=Noneh, endDate=2026-08-28T23:59:00Z)
  what-will-kevin-warsh-say-during-his-speech-at-jackson-hole-01
     "August 28, 2026, 10 AM ET"  ->  2026-08-28 14:00:00+00:00  (tz=ET, gamma startTime delta=0.0h, mkt eventStartTime delta=Noneh, endDate=2026-08-30T03:59:00Z)
  what-will-trump-say-during-healthcare-affordability-announcement
     "August 31, 2026 at 3PM ET"  ->  2026-08-31 19:00:00+00:00  (tz=ET, gamma startTime delta=0.0h, mkt eventStartTime delta=Noneh, endDate=2026-08-31T23:59:00Z)
  what-will-dell-say-during-their-next-earnings-call-20260901
     "September 1, 2026 at 4:30 PM ET"  ->  2026-09-01 20:30:00+00:00  (tz=ET, gamma startTime delta=0.0h, mkt eventStartTime delta=Noneh, endDate=2026-09-01T23:59:00Z)
  what-will-snowflake-say-during-their-next-earnings-call-20260902
     "September 2, 2026 at 5:00 PM ET"  ->  2026-09-02 21:00:00+00:00  (tz=ET, gamma startTime delta=0.0h, mkt eventStartTime delta=Noneh, endDate=2026-09-02T23:59:00Z)
  what-will-docusign-say-during-their-next-earnings-call-20260903
     "September 3, 2026 at 5:00 PM ET"  ->  2026-09-03 21:00:00+00:00  (tz=ET, gamma startTime delta=0.0h, mkt eventStartTime delta=Noneh, endDate=2026-09-03T23:59:00Z)
  what-will-lululemon-say-during-their-next-earnings-call-20260903
     "September 3, 2026 at 4:30 PM ET"  ->  2026-09-03 20:30:00+00:00  (tz=ET, gamma startTime delta=0.0h, mkt eventStartTime delta=Noneh, endDate=2026-09-03T23:59:00Z)
  what-will-trump-say-during-remarks-at-steel-across-america
     "September 8, 2026 at 10AM ET"  ->  2026-09-08 14:00:00+00:00  (tz=ET, gamma startTime delta=0.0h, mkt eventStartTime delta=Noneh, endDate=2026-09-08T23:59:00Z)
  what-will-john-ternus-say-during-his-apple-keynote-20260902
     "September 9, 2026, 1 PM ET"  ->  2026-09-09 17:00:00+00:00  (tz=ET, gamma startTime delta=0.0h, mkt eventStartTime delta=Noneh, endDate=2026-09-09T23:59:00Z)

excluded kinds, examples:
  period: 44
     what-will-the-nyt-front-page-headlines-say-this-week-august-24-august-30-20260830  raw=None endDate=2026-08-30T23:59:00Z
     what-will-trump-say-this-week-august-24-august-30  raw=None endDate=2026-08-30T23:59:00Z
     what-will-trump-post-this-week-august-24-august-30-2026  raw=None endDate=2026-08-30T23:59:00Z
  ambiguous_multiple: 0
  date_only: 36
     what-will-be-said-during-episode-24-of-big-brother-20260826  raw=August 26, 2026 endDate=2026-08-26T23:59:00Z
     what-will-be-said-during-episode-25-of-big-brother-20260827  raw=August 27, 2026 endDate=2026-08-27T23:59:00Z
     what-will-be-said-during-episode-26-of-big-brother-20260830  raw=August 30, 2026 endDate=2026-08-30T23:59:00Z
  open_ended_no_start: 25
     what-will-be-said-on-the-next-lemonade-stand-podcast-august-26  raw=None endDate=2026-08-26T23:59:00Z
     what-will-mrbeast-say-during-his-next-gaming-youtube-video-20260829  raw=None endDate=2026-08-29T23:59:00Z
     what-will-mrbeast-say-during-his-next-youtube-video-20260729175811859  raw=None endDate=2026-08-31T23:59:00Z
  no_start_time: 8
     what-will-andy-burnham-say-at-the-next-prime-ministers-questions-event  raw=None endDate=2026-08-26T23:59:00Z
     what-will-be-said-on-the-first-joe-rogan-experience-episode-of-the-week-august-24  raw=None endDate=2026-08-30T23:59:00Z
     what-will-karoline-leavitt-say-during-the-next-white-house-press-briefing-20260723175551503  raw=None endDate=2026-09-01T03:59:00Z

Gamma event.startTime present for 87/87 explicit events; agrees with parsed start within 1 min: 81; abs delta hours: median=0.0, max=33.0
Gamma markets[].eventStartTime present for 0/87 explicit events; agrees within 1 min: 0; max abs delta=Noneh
```

### run_q04b.txt

```text
[events] cached events=1313 past=1306 Q04-comparable sample=200 (2026-08-26T23:59:00Z .. 2026-10-19T23:05:00Z)

######## SAMPLE Q04-200: 200 events (2026-08-26T23:59:00Z .. 2026-10-19T23:05:00Z) ########
[start] kinds in sample: {'explicit': 87, 'no_start_time': 8, 'open_ended_no_start': 25, 'date_only': 36, 'period': 44}
[start] explicit+reliable events: 87/200; source: {'description=gamma': 81, 'description+gamma(min)': 6}
[start] resolved markets inside those events: 1493 (feeSchedule rate: 1493)
[start] markets in the whole sample (incl. periods/open-ended): 3124

===== S200 H2 =====  markets with an entry price: 905 (53 events); dropped reasons {'no_or_empty_history': 573, 'no_point_in_window': 15, 'usable': 905}
[S200 H2] staleness before cutoff (h): median=1.0 p90=1.0 max=1.0
[S200 H2] entry-to-start gap (h): median=3.0 min=2.2 max=3.0

  R1 buy NO YES in [0.05,0.35]  half_spread=0.01
    ALL          trades= 256 events=  50 win=0.8359 mean_ret/USDC=  0.01669 event_mean=  0.04228 t=  1.19
    FIRST_HALF   trades= 141 events=  25 win=0.8582 mean_ret/USDC=  0.04682 event_mean=  0.09184 t=  2.28
    SECOND_HALF  trades= 115 events=  25 win=0.8087 mean_ret/USDC= -0.02025 event_mean= -0.00727 t= -0.13

  R2 buy YES YES in [0.65,0.95]  half_spread=0.01
    ALL          trades= 276 events=  52 win=0.8225 mean_ret/USDC=  0.01651 event_mean=  0.01753 t=  0.50
    FIRST_HALF   trades= 129 events=  26 win=0.8295 mean_ret/USDC=  0.01322 event_mean=  0.01187 t=  0.20
    SECOND_HALF  trades= 147 events=  26 win=0.8163 mean_ret/USDC=  0.01939 event_mean=  0.02319 t=  0.58

  R3 buy NO YES in [0.05,0.95]  half_spread=0.01
    ALL          trades= 778 events=  53 win=0.5141 mean_ret/USDC= -0.06125 event_mean= -0.08173 t= -1.42
    FIRST_HALF   trades= 369 events=  26 win=0.5501 mean_ret/USDC= -0.03598 event_mean= -0.06268 t= -0.76
    SECOND_HALF  trades= 409 events=  27 win=0.4817 mean_ret/USDC= -0.08405 event_mean= -0.10007 t= -1.22

  R1 buy NO YES in [0.05,0.35]  half_spread=0.02
    ALL          trades= 256 events=  50 win=0.8359 mean_ret/USDC=  0.00435 event_mean=  0.02957 t=  0.85
    FIRST_HALF   trades= 141 events=  25 win=0.8582 mean_ret/USDC=  0.03409 event_mean=  0.07842 t=  1.98
    SECOND_HALF  trades= 115 events=  25 win=0.8087 mean_ret/USDC= -0.03210 event_mean= -0.01928 t= -0.34

  R2 buy YES YES in [0.65,0.95]  half_spread=0.02
    ALL          trades= 276 events=  52 win=0.8225 mean_ret/USDC=  0.00396 event_mean=  0.00497 t=  0.14
    FIRST_HALF   trades= 129 events=  26 win=0.8295 mean_ret/USDC=  0.00086 event_mean= -0.00061 t= -0.01
    SECOND_HALF  trades= 147 events=  26 win=0.8163 mean_ret/USDC=  0.00669 event_mean=  0.01055 t=  0.27

  R3 buy NO YES in [0.05,0.95]  half_spread=0.02
    ALL          trades= 778 events=  53 win=0.5141 mean_ret/USDC= -0.08366 event_mean= -0.10411 t= -1.88
    FIRST_HALF   trades= 369 events=  26 win=0.5501 mean_ret/USDC= -0.05677 event_mean= -0.08321 t= -1.04
    SECOND_HALF  trades= 409 events=  27 win=0.4817 mean_ret/USDC= -0.10791 event_mean= -0.12423 t= -1.60

===== S200 H12 =====  markets with an entry price: 804 (47 events); dropped reasons {'no_or_empty_history': 573, 'no_point_in_window': 116, 'usable': 804}
[S200 H12] staleness before cutoff (h): median=1.0 p90=1.0 max=1.2
[S200 H12] entry-to-start gap (h): median=13.0 min=12.2 max=13.2

  R1 buy NO YES in [0.05,0.35]  half_spread=0.01
    ALL          trades= 223 events=  45 win=0.8296 mean_ret/USDC=  0.00781 event_mean=  0.03278 t=  0.97
    FIRST_HALF   trades= 116 events=  22 win=0.8017 mean_ret/USDC= -0.02415 event_mean=  0.01054 t=  0.22
    SECOND_HALF  trades= 107 events=  23 win=0.8598 mean_ret/USDC=  0.04245 event_mean=  0.05406 t=  1.13

  R2 buy YES YES in [0.65,0.95]  half_spread=0.01
    ALL          trades= 266 events=  45 win=0.8271 mean_ret/USDC=  0.01645 event_mean=  0.02609 t=  0.79
    FIRST_HALF   trades= 124 events=  22 win=0.8548 mean_ret/USDC=  0.04021 event_mean=  0.04542 t=  0.92
    SECOND_HALF  trades= 142 events=  23 win=0.8028 mean_ret/USDC= -0.00431 event_mean=  0.00760 t=  0.17

  R3 buy NO YES in [0.05,0.95]  half_spread=0.01
    ALL          trades= 685 events=  47 win=0.4949 mean_ret/USDC= -0.08056 event_mean= -0.10024 t= -1.85
    FIRST_HALF   trades= 327 events=  23 win=0.4985 mean_ret/USDC= -0.11796 event_mean= -0.13342 t= -1.79
    SECOND_HALF  trades= 358 events=  24 win=0.4916 mean_ret/USDC= -0.04640 event_mean= -0.06843 t= -0.87

  R1 buy NO YES in [0.05,0.35]  half_spread=0.02
    ALL          trades= 223 events=  45 win=0.8296 mean_ret/USDC= -0.00441 event_mean=  0.02026 t=  0.61
    FIRST_HALF   trades= 116 events=  22 win=0.8017 mean_ret/USDC= -0.03601 event_mean= -0.00176 t= -0.04
    SECOND_HALF  trades= 107 events=  23 win=0.8598 mean_ret/USDC=  0.02985 event_mean=  0.04132 t=  0.88

  R2 buy YES YES in [0.65,0.95]  half_spread=0.02
    ALL          trades= 266 events=  45 win=0.8271 mean_ret/USDC=  0.00395 event_mean=  0.01337 t=  0.41
    FIRST_HALF   trades= 124 events=  22 win=0.8548 mean_ret/USDC=  0.02755 event_mean=  0.03257 t=  0.67
    SECOND_HALF  trades= 142 events=  23 win=0.8028 mean_ret/USDC= -0.01667 event_mean= -0.00499 t= -0.11

  R3 buy NO YES in [0.05,0.95]  half_spread=0.02
    ALL          trades= 685 events=  47 win=0.4949 mean_ret/USDC= -0.10364 event_mean= -0.12312 t= -2.36
    FIRST_HALF   trades= 327 events=  23 win=0.4985 mean_ret/USDC= -0.13724 event_mean= -0.15252 t= -2.11
    SECOND_HALF  trades= 358 events=  24 win=0.4916 mean_ret/USDC= -0.07295 event_mean= -0.09494 t= -1.25

######## SAMPLE EXT-400: 400 events (2026-07-05T23:59:00Z .. 2026-10-19T23:05:00Z) ########
[start] kinds in sample: {'period': 82, 'date_only': 98, 'explicit': 163, 'open_ended_no_start': 42, 'no_start_time': 15}
[start] explicit+reliable events: 163/400; source: {'description=gamma': 156, 'description+gamma(min)': 7}
[start] resolved markets inside those events: 3047 (feeSchedule rate: 3047)
[start] markets in the whole sample (incl. periods/open-ended): 6918

===== S400 H2 =====  markets with an entry price: 2446 (129 events); dropped reasons {'no_or_empty_history': 576, 'no_point_in_window': 25, 'usable': 2446}
[S400 H2] staleness before cutoff (h): median=1.0 p90=1.0 max=4.5
[S400 H2] entry-to-start gap (h): median=3.0 min=2.2 max=6.5

  R1 buy NO YES in [0.05,0.35]  half_spread=0.01
    ALL          trades= 618 events= 120 win=0.8576 mean_ret/USDC=  0.05037 event_mean=  0.05413 t=  2.38
    FIRST_HALF   trades= 336 events=  60 win=0.8780 mean_ret/USDC=  0.07691 event_mean=  0.07398 t=  2.73
    SECOND_HALF  trades= 282 events=  60 win=0.8333 mean_ret/USDC=  0.01875 event_mean=  0.03427 t=  0.94

  R2 buy YES YES in [0.65,0.95]  half_spread=0.01
    ALL          trades= 683 events= 125 win=0.8199 mean_ret/USDC=  0.01089 event_mean=  0.01548 t=  0.69
    FIRST_HALF   trades= 343 events=  62 win=0.8105 mean_ret/USDC=  0.00574 event_mean=  0.01587 t=  0.47
    SECOND_HALF  trades= 340 events=  63 win=0.8294 mean_ret/USDC=  0.01608 event_mean=  0.01510 t=  0.51

  R3 buy NO YES in [0.05,0.95]  half_spread=0.01
    ALL          trades=2095 events= 129 win=0.5098 mean_ret/USDC= -0.05562 event_mean= -0.06479 t= -1.87
    FIRST_HALF   trades=1165 events=  64 win=0.5167 mean_ret/USDC= -0.04858 event_mean= -0.05346 t= -1.18
    SECOND_HALF  trades= 930 events=  65 win=0.5011 mean_ret/USDC= -0.06443 event_mean= -0.07594 t= -1.44

  R1 buy NO YES in [0.05,0.35]  half_spread=0.02
    ALL          trades= 618 events= 120 win=0.8576 mean_ret/USDC=  0.03753 event_mean=  0.04117 t=  1.83
    FIRST_HALF   trades= 336 events=  60 win=0.8780 mean_ret/USDC=  0.06373 event_mean=  0.06082 t=  2.28
    SECOND_HALF  trades= 282 events=  60 win=0.8333 mean_ret/USDC=  0.00632 event_mean=  0.02152 t=  0.60

  R2 buy YES YES in [0.65,0.95]  half_spread=0.02
    ALL          trades= 683 events= 125 win=0.8199 mean_ret/USDC= -0.00156 event_mean=  0.00297 t=  0.13
    FIRST_HALF   trades= 343 events=  62 win=0.8105 mean_ret/USDC= -0.00673 event_mean=  0.00331 t=  0.10
    SECOND_HALF  trades= 340 events=  63 win=0.8294 mean_ret/USDC=  0.00364 event_mean=  0.00263 t=  0.09

  R3 buy NO YES in [0.05,0.95]  half_spread=0.02
    ALL          trades=2095 events= 129 win=0.5098 mean_ret/USDC= -0.07909 event_mean= -0.08842 t= -2.66
    FIRST_HALF   trades=1165 events=  64 win=0.5167 mean_ret/USDC= -0.07204 event_mean= -0.07713 t= -1.80
    SECOND_HALF  trades= 930 events=  65 win=0.5011 mean_ret/USDC= -0.08792 event_mean= -0.09954 t= -1.96

===== S400 H12 =====  markets with an entry price: 1993 (106 events); dropped reasons {'no_point_in_window': 478, 'no_or_empty_history': 576, 'usable': 1993}
[S400 H12] staleness before cutoff (h): median=1.0 p90=1.0 max=15.5
[S400 H12] entry-to-start gap (h): median=13.0 min=12.2 max=27.5

  R1 buy NO YES in [0.05,0.35]  half_spread=0.01
    ALL          trades= 534 events= 101 win=0.8427 mean_ret/USDC=  0.02667 event_mean=  0.03731 t=  1.50
    FIRST_HALF   trades= 296 events=  50 win=0.8547 mean_ret/USDC=  0.03890 event_mean=  0.03794 t=  1.01
    SECOND_HALF  trades= 238 events=  51 win=0.8277 mean_ret/USDC=  0.01146 event_mean=  0.03670 t=  1.12

  R2 buy YES YES in [0.65,0.95]  half_spread=0.01
    ALL          trades= 579 events= 103 win=0.8221 mean_ret/USDC=  0.00815 event_mean= -0.00384 t= -0.15
    FIRST_HALF   trades= 269 events=  51 win=0.8104 mean_ret/USDC= -0.00422 event_mean= -0.03348 t= -0.82
    SECOND_HALF  trades= 310 events=  52 win=0.8323 mean_ret/USDC=  0.01888 event_mean=  0.02523 t=  0.84

  R3 buy NO YES in [0.05,0.95]  half_spread=0.01
    ALL          trades=1671 events= 106 win=0.4973 mean_ret/USDC= -0.08233 event_mean= -0.08264 t= -2.13
    FIRST_HALF   trades= 905 events=  53 win=0.5182 mean_ret/USDC= -0.06859 event_mean= -0.05006 t= -0.86
    SECOND_HALF  trades= 766 events=  53 win=0.4726 mean_ret/USDC= -0.09856 event_mean= -0.11522 t= -2.23

  R1 buy NO YES in [0.05,0.35]  half_spread=0.02
    ALL          trades= 534 events= 101 win=0.8427 mean_ret/USDC=  0.01418 event_mean=  0.02462 t=  1.00
    FIRST_HALF   trades= 296 events=  50 win=0.8547 mean_ret/USDC=  0.02630 event_mean=  0.02528 t=  0.68
    SECOND_HALF  trades= 238 events=  51 win=0.8277 mean_ret/USDC= -0.00088 event_mean=  0.02397 t=  0.74

  R2 buy YES YES in [0.65,0.95]  half_spread=0.02
    ALL          trades= 579 events= 103 win=0.8221 mean_ret/USDC= -0.00422 event_mean= -0.01608 t= -0.64
    FIRST_HALF   trades= 269 events=  51 win=0.8104 mean_ret/USDC= -0.01646 event_mean= -0.04532 t= -1.12
    SECOND_HALF  trades= 310 events=  52 win=0.8323 mean_ret/USDC=  0.00640 event_mean=  0.01260 t=  0.42

  R3 buy NO YES in [0.05,0.95]  half_spread=0.02
    ALL          trades=1671 events= 106 win=0.4973 mean_ret/USDC= -0.10592 event_mean= -0.10680 t= -2.87
    FIRST_HALF   trades= 905 events=  53 win=0.5182 mean_ret/USDC= -0.09163 event_mean= -0.07383 t= -1.33
    SECOND_HALF  trades= 766 events=  53 win=0.4726 mean_ret/USDC= -0.12281 event_mean= -0.13977 t= -2.82

[save] results_q04b.csv (72 rows), trades_q04b.csv (17328 rows)
```

