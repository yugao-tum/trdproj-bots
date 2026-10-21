# H-quant-012：quant-012 负结果加固

日期：2026-10-21 ｜ 目标：`bots/quant/entries/quant-012-earthquake-count-base-rate.md`（`status: 待核`、`date: 2026-10-20` 未改）｜ 工作树：`quant-batch/c20261021-060001-research/w02`

## 一句话结论

**证据是负的，建议核对时降为待选区或退回，不应按收录处理。** 历史吃单代理全样本 `+1.41%`（费 0.05）/ `+2.45%`（费 0）只是 2025-12..2026-10 的累计投入口径；把同一规则按时间推到 **2026-07..10，45 个成交档为 `−1.99%`（费 0.05）/ `−1.22%`（费 0）**。基率模型 log loss 全样本 `1.4455` 劣于市场 `1.4152`（点估计，不显著）。真 maker 成交代理全样本 `−0.98%`、时间外 `−8.25%`。原“maker”报价 `q=1−p−0.01` 在 **81/103（78.6%）** 档会穿 NO 卖价、实际是吃单。

## 复用而非重跑

`bots/quant/notes/q012-hist/` 已合入 `main`，直接复用：

- `REPORT.md`、`q012_hist.py`、`run_output.txt`
- `buckets.csv`（514 行）、`events.csv`（68 行）
- md5：`buckets.csv f563d8e005f13217a4478f0f7638ecd1`、`events.csv 61ca26645b55de274abba1fb45e44c48`
- 与 `bots/quant/notes/scheduler/scratch/I01/` 同名文件逐字节一致（`analyze_merged_output.txt`）。

没有重新下载 68 个事件的成交；只对 103 个触发档补取了 `[窗口开始, 窗口结束]` 的成交打印用于 maker 代理。原始/缓存都在 `_cache/`（`.gitignore` 已忽略，单文件 <1 MB）。

## 新证据

### 1）时间外样本（`analyze_merged.py` / `analyze_merged_output.txt`）

切分点写死为 `window_start >= 2026-07-01`，未用时间外样本调参。

| 样本 | 成交档 | 中位净利/份 | 均值净利/份 | 合计/投入 | 费 0 合计 |
|---|---:|---:|---:|---:|---:|
| 全样本 | 103 | +0.1147 | +0.0107（95% CI −0.0628..+0.0799） | +1.1010/78.0863 = +1.41% | +2.45% |
| 内样本 <2026-07-01 | 58 | +0.1292 | +0.0318 | +1.8469/40.6284 = +4.55% | +5.84% |
| **时间外 >=2026-07-01** | **45** | **+0.1051** | **−0.0166（95% CI −0.1247..+0.0795）** | **−0.7459/37.4579 = −1.99%** | **−1.22%** |

时间外 log loss 只有 4 个全档有价事件（模型 `1.7732` vs 市场 `1.7511`），样本太小，不能单独下强结论；主结论是“时间外收益点估计为负，且 CI 跨 0，不能证明正 edge”。

### 2）真 maker 成交代理（`maker_proxy.py` / `maker_proxy_output.txt`）

- 静态穿价检查：103 个触发档中 81 个的 `q=1−model−0.01 ≥ NO 卖价(1−市场YES+0.01)`，只有 22 个在价差内，0 个低于 NO 买价 → 原规则多数是吃单。
- 代理：在 t0 挂 NO 买单 `q_mid=1−市场YES`、`q_bid=1−市场YES−0.01`；只有 `[t0, window_end]` 出现 taker 卖 NO 且成交价 ≤ q 才成交；maker 费 0，持到结算。
- `q_mid`：81/103 成交，中位 `+0.1300`、均值 `−0.0071`、合计 **−0.98%**；内样本 `+4.46%`，**时间外 `−8.25%`**。
- `q_bid`：75/103 成交，中位 `+0.1325`、均值 `−0.0199`、合计 **−2.79%**；内样本 `+1.44%`，**时间外 `−8.02%`**。
- 限制：`data-api` 只有成交打印，没有盘口/排队；打印穿过限价是成交的必要条件，不是充分条件。这是代理，不是实盘证明。

### 3）出处复验（`verify_sources.py` / `verify_sources_output.txt`）

所有具体 URL（两个带 `<conditionId>`/`page=N` 的模板用真实示例代替）HTTP 200，关键数字逐项复现：

- USGS CSV：1,513 行（含表头）、`mag≥6.5` 1,216 条、1,395 个 7 日 bin、均值 0.8717、分布 `0:663,1:440,2:178,3:70,4:29,5:5,6:7,7:1,8:1,12:1`、P(≥3)=0.0817、P(≥5)=0.0108。
- USGS `/count` 2015-01-01..2026-01-01：6.5 → 462；7.0 → 153；5.5 → 5,031。
- USGS text 2026-10-12..10-19：3 条（`us6000u2mq` 6.9、`us6000u214` 6.8、`us6000u1z5` 6.7）。
- Gamma 10/19 事件：规则五个关键词（ET 窗口、USGS、48h、lowest bracket、anywhere on Earth）逐字命中；7 档；`closed=false`；`volume=6025.908212`、`liquidity=7533.111`（均已漂移）。
- Gamma tag=earthquake closed：69 个事件、成交 $5,869,974.95、分类 37/17/12/3、endDate 2024-09-30..2026-10-19。
- CLOB：开放 token 有历史；已关闭 token 仍 `{"history":[]}`。
- data-api 示例：HTTP 200，字段含 `side/price/size/timestamp/outcome`。

### 4）费率修正（审计 S9）

原文写“本族每个市场 `feeSchedule.rate=0.05`”是错的：

- 2026-10-21 实取 10/19 事件：7 档全部 `rate=0, rebateRate=0`；
- 10/12 事件：4 档 `0.05/0.25`、3 档 `0/0`；
- 9/28 事件：7 档 `0.05/0.25`。

已改成逐事件读；历史回测的 0.05 是保守值，费 0 敏感性也在正文给出。另：`clobRewards` 日率从 2026-10-20 的 20 变成 2026-10-21 的 50，`rewardsAmount=0`，不能当固定收入。

### 5）查重

- `quant-018`（PortWatch）、`quant-019`（CDC）都已声明 `improves: quant-012`；本条是最早 base。
- `composer-008`（2026-10-21）同为 USGS 周计数阶梯、M5.5+、Poisson、买 YES；晚于本条（2026-10-20），按 §3.3 最多算同族变体/补充。
- `dot-032` 是纯流动性奖励，不是同一收益来源。

## 七门判定

1. 机制说得清：**基本满足**，但“为什么持续”没有被时序证据支持。
2. 有免费数据能检验：**满足（有保留）**；准确口径是 40 个严格组中 35 个有价、34 个有成交，不是 40 个都有价；无完整盘口。
3. 小资金能做：**满足（容量很小）**。
4. 不重复：**基本满足**，同族 018/019 已 supplement，composer-008 晚到；仍需主审确认。
5. 扣成本后粗算够用：**不满足（负）**；时间外 −1.99%/−1.22%，maker 代理 −0.98%/−8.25%，log loss 劣于市场。
6. 两周内能检验：**满足可检验性，但结果 FAIL**；35 个有价严格结果 ≥30。
7. 出处可查：**满足**；所有具体 URL 重抓 200，数字复算一致，费率旧写法已修。

## 复现

```
cd bots/quant/notes/q012-hist
python3 q012_hist.py | tee run_output.txt   # 已有输出，可跳过

cd ../scheduler/scratch/H-quant-012
python3 analyze_merged.py | tee analyze_merged_output.txt
python3 maker_proxy.py | tee maker_proxy_output.txt
python3 verify_sources.py | tee verify_sources_output.txt
python3 field_check.py | tee field_check_output.txt
```

## 未解决问题

- 没有历史盘口/深度，maker 排队与逆向选择无法量化；maker 代理只能证伪“原公式是 maker”，不能证明“真 maker 一定亏”。
- 时间外成交档只有 45 个、全档有价事件只有 4 个，时间外 log loss 不能下强结论；收益侧 CI 跨 0。
- M5.5+ 有 9/28 个事件自算计数与结算档不一致（M6.5+ 38/38、M7.0+ 2/2 一致）；不一致原因未逐事件定因（目录修订/震级口径/窗口文本）。
- `composer-008` 的同族关系需主审按 §3.3 判定；本条不改其他 bot 文件。
- `python3 tools/check.py lint` 仍被仓库既有 `muse-700/701` 缺字段卡住（`KeyError: 'id'`），与本条无关；见 `lint_output.txt`。
