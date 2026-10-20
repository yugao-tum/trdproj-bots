## 做了什么

用 data-api 的 closed 市场成交 + football-data 逐文件 CSV，补上 quant-011 原先缺失的“历史可成交平局价格”回测。

- 联赛（脚本头预声明）：E0、I1、SP1、D1、F1（条目用的 E0/I1 + 另外三个同时有 football-data 与 Polymarket closed 平局市场的 top-5 联赛）。
- 基准率：B365 收盘赔率去水后的 qD 分桶（0.04 宽），只用比赛赛季**之前**的赛季，expanding walk-forward；同联赛同桶 n≥30，否则回退五联赛合并。
- T = gameStartTime − 1h；主窗口 `[T−6h,T]`，敏感性 `[T−24h,T−1h]`；ask = 窗口内最后一笔 YES 成交价 + 1¢（只有打印，没有历史盘口）。
- 触发：ask ∈ [0.15,0.30] 且 `ask ≤ 基准率 − 0.02`；体育 taker 费 0.05，`fee=0.05·ask·(1−ask)`；每场 1 份，持到结算，一场 = 1 个独立结果。

## 验证命令

```bash
python3 bots/quant/notes/q011-hist/q011_hist.py
```

从 `_cache/` 重跑，`run_output.txt` 与 `matches.csv` 的 sha256 与首次一致（已 diff 验证）。缓存已 gitignore。

## 关键结果（复制自 run_output.txt）

- 2,090 个 closed 平局 event；匹配 football-data 2,019（96.6%），unmatched 69，重复 event 合并 2；priced 1,986。
- Polymarket 平局结算 vs `FTR`：2,019 / 2,019 = 100.0%。
- 主窗口 triggered 161：净收益/份中位数 **−0.2389**、均值 **−0.0525**、每美元投入总净收益 **−22.82%**、命中率 **18.6%**。
- 敏感性窗口 triggered 164：中位数 **−0.2389**、均值 **−0.0074**、每美元投入 **−3.21%**、命中率 **23.2%**。
- Brier：基准率 0.18578 vs 市场 0.18487；LogLoss：0.55686 vs 0.55419；配对符号检验 p=0.9106（无显著差异）。
- **判定：FAIL**（161 ≥ 30，主窗口中位净收益 ≤ 0；每美元投入总净收益也为负）。

## 对门槛 5/6

- 门槛 5：已有真实 closed-market 成交价 + 费用的结果，负收益，**不满足**。
- 门槛 6：不再需要靠两周前向记录；历史 161 个触发样本已超过 30 门线。条目“历史平局价格不可得”在 data-api closed trades 路径下已不成立（未改条目）。

## 限制

- closed 市场没有历史盘口，ask 用 last print + 1¢ 近似；无法逐场验证真实 spread，`spread ≤ 0.02` 只是模型假设。
- last print 可能陈旧；未建模价格漂移、大单冲击、队列/挂单成交。
- 匹配 96.6%，69 个未匹配主要是改期和 2026/27 队名差异；I1 只有 4 次触发、F1 7 次，分联赛结论弱。
- B365 基准率有联赛漂移和桶内小样本问题；data-api 单市场约 2 万笔上限，热门市场理论上可能截断。
- 未做年化、资金曲线、回撤和仓位上限；仅 taker，费率按 0.05。

`python3 tools/check.py lint` 输出见 `lint_output.txt`；退出码 1 是 muse-700/701 缺 `id` 导致，与本次改动无关。
