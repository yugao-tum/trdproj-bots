## 做了什么

对 quant-020（Polymarket「公司本季 EPS 是否超预期」，0.40–0.55 带买 YES）做**可成交价 + 时间切分样本外回测**：

- 用 Gamma 枚举全部已关闭 earnings-beat 事件（1386 个 tag 事件 → 1385 个过滤后事件 → 同公司同日 GAAP/非 GAAP 合并后 1384 个），跨 2025-06-05 至 2026-10-20。
- 价格改用 **data-api 逐笔成交**：`p_24h` = `[endDate−72h, endDate−24h]` 最后一笔 YES 成交（NO 按 1−price），入场 ask = `p_24h + 1¢`；费率按条目 0.05，费用 = `0.05×ask×(1−ask)`。
- 按 endDate 最早 60% = DISCOVERY（830 个，切分点 2026-05-05T13:00Z），最新 40% = HOLDOUT（554 个）；规则冻结，不重新拟合。
- 同时对同一批带内事件用旧 CLOB `prices-history` 价格重算，做价格源对比。
- 主窗口有成交 1321/1384；敏感窗口（`endDate−6h`）1356/1384；data-api offset 截断 0 个；带内 101 个事件，旧价格 101/101 可取。
- bootstrap 按 ISO 周聚类、10000 次、固定种子 20261020。

## 验证命令

```bash
python3 bots/quant/notes/q020-oos/q020_oos.py
```

首次下载并缓存到 `_cache/`（gitignore）；再次运行从缓存读取，stdout 已实测 `diff` 完全一致。`run_output.txt` 为完整 stdout，`events.csv` 为逐事件结果。

## 关键结果（data-api 可成交价，1¢ 半价差，费率 0.05）

| 组 | n | YES 率 | 平均入场价 | 中位净 PnL/份 | 均值净 PnL/份 | 每 $ 投入 | 平均占用天数 | 年化 | bootstrap 95% CI |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| DISCOVERY | 54 | 0.4444 | 0.4814 | −0.4313 | −0.0494 | −0.1025 | 1.07 | −3482.88% | [−0.1688, +0.0718] |
| HOLDOUT | 47 | 0.5745 | 0.4881 | +0.4376 | +0.0740 | +0.1517 | 1.25 | +4434.67% | [−0.1074, +0.1841] |
| POOLED | 101 | 0.5050 | 0.4845 | +0.4277 | +0.0081 | +0.0166 | 1.16 | +525.52% | [−0.1005, +0.0972] |

**HOLDOUT 判定：PASS**（条目冻结标准：中位净 PnL/份 +0.4376 > 0；YES 率 0.5745 > 平均入场价 0.4881；n=47 ≥ 30）。但 DISCOVERY 为负、POOLED 均值约 0、CI 跨 0，统计上不显著。

门槛影响：门槛 5 只能算「按冻结判据 PASS、证据弱」；门槛 6 **不满足**——带内事件仅占 7.65%，任一历史 14 天窗口带内最多 24 个，低于两周 30 个的要求。

## 限制

- data-api 是成交打印，不是可成交盘口/深度；1¢ 半价差是预声明假设。
- 结果取 Polymarket `outcomePrices`；SeekingAlpha 付费墙，未独立核对 strike 与公布 EPS。
- 按 endDate 切分非随机；`endDate` 用作 resolution 代理，实际结算到账可能更晚。
- `python3 tools/check.py lint` 退出 1，崩溃于既有 `bots/muse/entries/muse-700/701`，与本任务无关，输出见 `lint_output.txt`。

完整方法与限制见 `bots/quant/notes/q020-oos/REPORT.md`。
