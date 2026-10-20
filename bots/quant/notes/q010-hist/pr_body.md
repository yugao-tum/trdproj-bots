## 做了什么

对 quant-010 做了一次**可成交价历史回测**（不是前向记录，不是只用中间价）：

- 枚举 Gamma 全部 closed 周榜 #1 event：show 系列 10440/10772（53+43 个），movie 系列 10441/10775（52+45 个）。
- 结算源：Netflix Tudum keyless TSV（`all-weeks-global.tsv`、`all-weeks-countries.tsv`，访问 2026-10-20；全球 TV/Films 用 English 表，美国用 US 表）。
- 成交价：data-api `trades?market=<conditionId>`，取官方发布前 24h 内最后一条成交；`ask = YES价 + 1¢`；按 GUIDE §8 计 `fee = rate × ask × (1−ask)`；持有到 Gamma `outcomePrices`。
- 独立结果：一个 chart-week 一簇，同周 global+US 合并；show 53 簇，movie 52 簇。
- 信号：Netflix 无 keyless 日榜历史（FlixPatrol 403），用条目允许的最简单冻结代理“上一周同榜 #1 预测本周 #1”，脚本头已预声明；这是代理，不是原日榜 nowcast。

## 验证命令

```bash
cd bots/quant/notes/q010-hist
python3 q010_hist.py
python3 q010_hist.py --kind movie
```

缓存存在时不发网络请求；两次 from-cache 重跑的 `run_output*.txt` 与 `events*.csv` 已用 `diff` 验证逐字节一致。`tools/check.py lint` 原始输出在 `lint_output.txt`（该命令在 `bots/muse/entries/*.md` 上 `KeyError: 'id'` 崩溃，不是本目录文件）。

## 关键结果（脚本 stdout 原样）

Show 主口径（条目自己的 #1 show 模板）：

```
chart-week span: 2025-03-16 .. 2026-10-11 (53 unique weeks)
  simulated market-events: 82
  independent chart-week clusters: 53
  hit rate (events): 0.3871 (36/93) | cluster mean: 0.3962
  net/share: median -0.0110 | mean -0.0032 | cluster median -0.0110 | cluster mean -0.0017
  cluster bootstrap 95% CI of mean net/share: [-0.0083, +0.0099]
VERDICT: FAIL
```

Movie 扩展：

```
chart-week span: 2025-10-12 .. 2026-10-18 (53 unique weeks)
  simulated market-events: 85
  independent chart-week clusters: 52
  hit rate (events): 0.3474 (33/95) | cluster mean: 0.3491
  net/share: median -0.0110 | mean -0.0086 | cluster median -0.0110 | cluster mean -0.0088
VERDICT: FAIL
```

“100% 会赢”上界（买最终赢家，仍按 ask）：show 81.33% 的赢家单净 ≤0，movie 87.18%。条目示例 A 的吃单成本问题在多数事件上成立。

## 结论与限制

按条目自己的失败标准：53/52 个独立簇 ≥30，但信号命中率 39.62%/34.91% 远低于 80%，簇中位净收益 −0.0110/份 ≤0 → **FAIL**。门槛 5 仍不满足；门槛 6 变成“可检验但代理口径为负”，原日榜信号仍无法 keyless 复现。

主要限制：代理不是原日榜 nowcast；决策价取发布前 24h 内最后一条成交（常在发布前几分钟，市场已接近有效）；Netflix 日榜历史（FlixPatrol 403）与 Spotify 历史日榜（kworb 只有当前日）未取到；6 个 event 的 Tudum #1 不在候选市场里（Gamma 结算 Other）；data-api 最后成交 +1¢ 不是 L2 深度。详见 `REPORT.md`。
