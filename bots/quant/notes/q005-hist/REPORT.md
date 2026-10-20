# quant-005 历史可成交价回测报告

- 分支：`quant-review/q005-hist`
- 脚本：`q005_hist.py`（stdlib + pandas/numpy/requests，下载缓存在 `_cache/`，已被 `.gitignore` 排除）
- 数据访问日期（UTC）：2026-10-20
- 结论：**FAIL**（冻结标准：逐事件买入侧扣费后净收益中位数 ≤ 0）

## 1. 数据源与访问方式（全部 keyless）

| 数据 | URL | 用途 |
|---|---|---|
| Gamma events | `https://gamma-api.polymarket.com/events?series_id=<id>&closed=true&limit=100&offset=N` | 已结算事件、档位、`outcomePrices`、`endDate`、`feeSchedule` |
| xtracker posts | `https://xtracker.polymarket.com/api/users/elonmusk/posts`、`.../realDonaldTrump/posts` | 逐条帖 `createdAt`，重建窗口计数与历史条件分布 |
| data-api trades | `https://data-api.polymarket.com/trades?market=<conditionId>&limit=500&offset=N` | 已关闭市场的真实成交；`outcome="No"` 时 YES 价 = 1 − price |

本次实抓：Elon feed 13,683 条（2025-10-31..2026-10-20）；Trump feed 5,777 条（2026-01-15..2026-10-20）。未使用 API key、未登录、未下单、未读任何凭据文件。

## 2. Universe（Gamma closed=true）

```
  series 10816 elon48: closed=126, 有已结算档=126, span=2026-01-03..2026-10-19
  series 10000 elon7d: closed=187, 有已结算档=187, span=2024-06-07..2026-10-16
  series 11108 trump7d: closed=73, 有已结算档=73, span=2026-02-13..2026-10-20
```

一个 event 的所有档算 1 个独立结果；共 **385** 个 closed event。

## 3. 方法（脚本头部已写死）

- 事件窗口 = `[Gamma endDate − 窗口长度, endDate)`；48h / 7d 由 series 决定。
- 决策点：窗口 50%（主），75%（敏感性）。`n_elapsed = createdAt ∈ [start, decision)`。
- 历史窗口：同长度、结束早于 decision、12h 步长、结束时刻对齐事件 endDate；只用 decision 前已结束窗口的最终计数（walk-forward）。
- 条件分布：历史窗口的“已过比例计数” ≤ `n_elapsed` **且最终计数 ≥ `n_elapsed`**；主口径再剔除条件样本中最终计数最高的 10%（保守版）。条件样本 <30 或剔除后 <20 → 跳过。
- 可成交价：`[decision−6h, decision]` 内该档最后一笔 data-api 成交的 YES 价 + 1¢ 作为 ask。
- 费用：统一 `fee = 0.05 × ask × (1−ask)` 每份（GUIDE §8；早期 `feesEnabled=false` 实际为 0，这里统一收费更保守）。
- 买入：`edge_k = p_k − ask_k − fee_k − 0.01`，只买最大且 >0 的一档，持有到 Gamma 结算。
- 统计：ISO 周 block bootstrap，10000 次，固定 seed=20260520。

> 关于条件规则：entry 原文只写“部分计数 ≤ n_elapsed”。若严格照字面执行，会买入 `upper < n_elapsed` 的、逻辑上已经不可能的档位；因此主口径加了硬约束 `最终计数 ≥ n_elapsed`。字面版结果另存 `run_output_literal_le.txt`，两者结论相同（都 FAIL）。

## 4. 结果（复制自 `run_output.txt`）

样本漏斗：

```
  全部 closed 事件=385；模型可建模=257；有可成交价=253；50% 触发=252
  skip no_post_history_before_window: 87
  skip insufficient_conditional_history: 39
  skip no_executable_price_in_6h: 4
  skip tracker_feed_gap: 2
  skip no_positive_edge: 1
```

主口径（50% 决策点）：

```
  触发事件数 n=252，覆盖 ISO 周=47
  每份净收益: median=-0.034596, mean=-0.012555
  每 $1 本金净收益: median=-1.047500, mean=-0.454007
  命中率=0.0992 (25/252)
  ISO 周 block bootstrap 95% CI of mean(每份) = [-0.048273, 0.026127] (B=10000, seed=20260520)
  all-event 口径（未触发=0）: median=-0.014690, mean=-0.008218, hit=0.0649
```

敏感性（75% 决策点）：

```
  触发事件数 n=197，覆盖 ISO 周=41
  每份净收益: median=-0.036922, mean=-0.025202
  每 $1 本金净收益: median=-1.047067, mean=-0.451793
  命中率=0.0914 (18/197)
  ISO 周 block bootstrap 95% CI of mean(每份) = [-0.067587, 0.020305]
```

模型 vs 市场对数损失（225 个可定价事件，按有价档位归一化）：

```
  保守经验模型: 4.230090
  原始经验模型: 2.269900
  NB 平滑检查:  1.802055
  市场归一化价: 1.473311
```

模型在两个口径上都比市场差；保守版因把已实现档位剔出样本而出现零概率，均值被 log(1e−9) 拉高，但原始经验模型与 NB 也均劣于市场。

结算源一致性：

```
  可核对=257, 不一致=20
```

字面版（仅 `partial ≤ n_elapsed`，`run_output_literal_le.txt`）：

```
  触发事件数 n=257，覆盖 ISO 周=47
  每份净收益: median=-0.023076, mean=-0.010894
  每 $1 本金净收益: median=-1.048500, mean=-0.580455
  命中率=0.0778 (20/257)
  ISO 周 block bootstrap 95% CI of mean(每份) = [-0.040968, 0.021331]
  75%：n=231, median=-0.023076, mean=-0.029317, hit=0.0519
  对数损失 n=228: 保守 5.123744 / 原始 2.454425 / NB 1.924052 / 市场 1.468303
  结算一致性：可核对=261, 不一致=21
```

## 5. 判定

```
  FAIL — 触发样本 n=252，每份净收益中位数 -0.034596 ≤ 0。
  VERDICT=FAIL
```

按 entry 预先写死的失败标准，本条不通过：50% 决策点触发 252 个独立事件，扣费后每份净收益中位数为负；75% 敏感性同样为负；命中率仅 9.9%，模型对数损失劣于市场归一化价。bootstrap 均值 CI 跨 0，但冻结判据用的是中位数，且中位数与均值都为负。

## 6. 对 gate 5 / gate 6 的含义

- **gate 5（扣成本后粗算够用）**：由“不确定”变为 **不满足**。原条目 +4.9%/份是单个时点、重叠样本、CLLOB 中间价的算术；换成 data-api 真实成交价 + 1¢ 后，252 个事件的买入侧中位数为 −3.46¢/份，单点优势没有复现。
- **gate 6（两周内能检验）**：已用 keyless 的 data-api 成交 + xtracker 帖时间戳完成历史检验，不再依赖非可执行的 `prices-history`；检验本身可复现，但结果是 FAIL。历史 L2/盘口深度仍无公开源，未做容量检验。

建议：按 entry 的失败标准退回，不进入影子盘/前向；不要把本条作为“待核”继续推进。

## 7. 限制（不要当成已解决）

1. **tracker 漏帖/删除**：257 个可核对事件里 20 个（7.8%）用帖时间戳算出的落档与 Gamma 结算档不一致；tracker 只保留抓到的帖，删除/漏抓会系统性改变最终计数。另有 2 个 archived/重复 slug 在窗口内 0 帖但结算高于 0，已按 `tracker_feed_gap` 跳过。
2. **prints ≠ book**：`last trade + 1¢` 不是真实卖一价，尤其尾部档可能只有 0.1¢ 的陈旧成交；没有历史 L2 和深度。真实可成交 ask 若更高，策略只会更差，不会更好；但本回测不能证明“按该价一定能成交”。容量/滑点未测。
3. **非平稳与重叠窗口**：历史窗口 12h 步长、互相重叠；2026 年发帖速率上升，模型系统性低估后期最终计数（对数损失差于市场）。条件样本不是独立样本，只用于构造分布。
4. **费用口径**：统一 0.05；早期市场实际 `feesEnabled=false`，若按 0 收费结果会略好，但不足以改变中位数为负的结论（未单独重跑该口径）。
5. **历史覆盖**：Elon 帖历史从 2025-10-31、Trump 从 2026-01-15 开始；87 个更早事件因无窗口前历史被跳过，39 个因条件样本不足被跳过。
6. **data-api 截断**：GUIDE 说每个市场最多约 2 万笔；本次分档市场大多未触及，但未逐市场验证是否被截断。
7. **结算边界**：窗口按 `[start, end)` 左闭右开；Gamma/UMA 的边界与“replies / community reposts”口径可能与本脚本的 tracker 计数不同。

## 8. 复现与校验

```
cd bots/quant/notes/q005-hist
python3 q005_hist.py
```

缓存重跑输出逐字节一致（同一 `_cache/`）：

```
run_output.txt  sha256 c41881bb5bf0fd4e912c057692f0b00e49d18b817bb1d2bf49481811049a4332
events.csv      sha256 ab4dc2bb9b047e94b3992f335eeb0ba12cec7d03a264461a6096fb6f7f840c70
```

`events.csv` 137,274 bytes（<1 MB），含 385 个事件、跳过原因、模型样本量、买入档、ask、edge、结算与 75% 敏感性字段。

`python3 tools/check.py lint` 输出（`lint_output.txt`，退出码 1）：

```
bots/muse/entries/muse-700-defined-risk-iron-fly.md: 缺字段或为空：id, name_zh, name_en, bot, date, market, pm_category, kind, improves, category, return_type, instruments, venues, data, test_2w, status, confidence
bots/muse/entries/muse-701-skew-harvest-sign-correction.md: 缺字段或为空：id, name_zh, name_en, bot, date, market, pm_category, kind, improves, category, return_type, instruments, venues, data, test_2w, status, confidence
Traceback (most recent call last):
  File "/workspace/oc-jobs/quant-review/wt/q005-hist/tools/check.py", line 266, in <module>
    sys.exit({"lint": lint, "dupes": dupes, "stats": stats, "score": score}.get(command, lint)())
  File "/workspace/oc-jobs/quant-review/wt/q005-hist/tools/check.py", line 88, in lint
    bad(rel, f"id 和 {seen[f['id']]} 重复")
KeyError: 'id'
```

该失败来自主分支已有的 `bots/muse/entries/muse-700/701`（缺 `id` 导致 `check.py` 崩溃），与本目录新增文件无关；本任务未修改这些文件。
