# B30 复跑说明：AAA 每日汽油均价分档（quant-031）

日期：2026-10-20 UTC｜bot：quant｜产出：`bots/quant/entries/quant-031-aaa-gas-daily-bracket.md`

## 1. 结论（先看）

- 模板：Polymarket series `12954`（`us-gas-price-daily`，daily），每天 1 个 event、6 个 1 美分分档，按 AAA `gasprices.aaa.com` 的 `Regular / Current Avg.` 在 10:00 AM ET 的值结算。
- 完全同规则的已结算历史只有 **4 个**（2026-10-16 至 10-19）；另有 2 个 2025 周度近似事件（close 12:00 UTC，`feeSchedule=null`），不能算同规则。
- 调度侦察写的是 9 个事件（6 已结算），本次 Gamma 实抓只有 6 个（4 已结算）；`us-gas-price-on-october-12/13/14/15-2026` 均返回 0 条，未找到另外 3 个事件。
- AAA 在样本中约 **07:00–10:22 UTC** 翻页（47 个不同时刻的 Wayback 快照；06:35/07:02/07:12 仍是前一天，07:30 起看到当天；最晚 10:22 才看到当天）。事件日 11:00 UTC 的快照已全部是当天值。
- 因此“10:00 ET 值抢跑”这个说法不成立：10:00 ET（14:00 UTC）时值已公布数小时，市场已把获胜档抬到 0.99。
- 用有快照的 11:00 UTC 作为决策时点、只买 ≤0.95：**4 个已结算事件 0 个可成交样本**；放宽到 0.99 只有 1 笔，扣 0.04 费 + 0.5 美分半价差后净 **+0.4595 USDC**。
- 07:00 的“事后赢家 + 页面已翻页”回放能得 4/4 笔、+101.82 USDC，但这是上界，不是可执行规则：它既用了事后才知道的赢家，也假设了当时页面已翻页。正文已明确标注，不能当收益证据。
- 7 条门槛：1、3、7 满足；2、5、6 不满足；4 不确定（宽口径可能是 dot-004 的变体）。`status: 草稿`。

## 2. 文件

| 文件 | 用途 |
|---|---|
| `collect.py` | 拉 7 个 Gamma event 的规则/分档/费率，按 conditionId 拉 data-api 成交；结果在 `_cache/` |
| `analyze_yes.py` | 逐市场只列 YES 成交；输出 `yes_analysis.txt` |
| `rule_test2.py` / `rule_test3.py` | 事件研究 + 11:00 快照规则 + 07/09/11 诊断；`rule_test3_out.txt` 是正文引用的版本 |
| `aaa_snapshots.csv` | 14 个事件日/盘中 Wayback 快照，含 `Price as of`、`Current Avg.`、`Yesterday Avg.` |
| `_cache/` | 原始 event/trade/AAA/Wayback 文件；`.gitignore` 已写 `_cache/` |

## 3. 复跑

```bash
cd bots/quant/notes/scheduler/scratch/B30
python3 collect.py > collect_run.txt 2>&1
python3 analyze_yes.py > yes_analysis.txt 2>&1
python3 rule_test3.py > rule_test3_out.txt 2>&1
cat rule_test3_out.txt
```

`collect.py` 会重新请求 Gamma 和 data-api；`_cache/` 已存在时直接读缓存。AAA Wayback 快照的 URL 与时间戳见 `aaa_snapshots.csv`。

## 4. 关键 stdout（`rule_test3_out.txt`）

```text
EVENT STUDY (ex post winner; diagnostic only)
10-16 AAA 4.3271 bracket $4.3200-4.3299 first07 07:27:34 p 0.8171 first95 None mins_to_95 None
10-17 AAA 4.3085 bracket <$4.3100       first07 07:29:00 p 0.4902 first95 07:56:59 mins_to_95 28.0
10-18 AAA 4.2988 bracket $4.2900-4.2999 first07 07:41:14 p 0.7624 first95 07:41:32 mins_to_95 0.3
10-19 AAA 4.2953 bracket $4.2900-4.2999 first07 07:30:50 p 0.8753 first95 08:45:53 mins_to_95 75.0
10-20 AAA 4.2786 bracket <$4.2800       first07 07:21:50 p 0.8228 first95 07:32:14 mins_to_95 10.4 (not closed)

RULE AT SNAPSHOT TIME (11:00-11:03 UTC)
threshold 0.95 fills 0
threshold 0.99 fills 1
   ('us-gas-price-on-october-18-2026', '2026-10-18 11:25:41', 0.988457, 75.5,
    0.000456, 0.006087, 0.4595)
```

## 5. 诚实边界

- data-api 给的是**成交价**，不是盘口；0.95 门槛的“0 个可成交样本”只能证明 11:00 之后没有 ≤0.95 的 BUY 成交，不能证明当时一定没有 ≤0.95 的卖单（但薄盘口下大概率没有）。
- 事件研究的赢家档是事后按最终 AAA 值选的；07:00 的价格不能当成“当时已知赢家”。
- 历史 AAA 快照在事件日多数只有 11:00 一个点；无法证明 07:2x 时页面已经翻页，只能由 06:35/07:02/07:12 仍为前一天 + 07:30 起为当天，以及成交簇在 07:2x–07:4x 推断。
- 4 个已结算事件不足以做任何统计推断；两周前向也只有约 14 个。
- 未使用任何密钥、账户、付费数据；只读 Gamma、data-api、AAA 页面和 Wayback。

## 6. 复跑时注意

- `collect.py` 里的 `events_index.json` 是脚本写的缓存索引；删掉 `_cache/` 会重新拉取。
- `rule_test2.py` 的 07:00 规则包含事后赢家选择，只作诊断；正文和本报告都不把它当收益结论。
- `tools/check.py lint` 目前会在 muse 两个缺 front matter 的文件上抛 `KeyError: 'id'`，与本条无关；本条 front matter 已单独检查，`status: 草稿`。
