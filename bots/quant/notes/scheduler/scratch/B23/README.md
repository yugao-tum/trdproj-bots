# B23 干旱 D4 周度州名单 — 复现说明

日期：2026-10-20 UTC｜机器人：quant｜产出：`bots/quant/entries/quant-026-drought-d4-weekly-continuity.md`

## 数据与脚本

全部公开、免密钥。原始响应在 `_cache/`（已 gitignore）。

1. `fetch_usdm.py`：从 USDM REST 取 48 个本土州的 2000-01-04..2026-10-13 周度 D4 面积百分比，存 `_cache/usdm/<ST>.csv`。
   - 端点：`https://usdmdataservices.unl.edu/api/StateStatistics/GetDroughtSeverityStatisticsByAreaPercent?aoi=<FIPS>&startdate=1/1/2000&enddate=10/20/2026&statisticsType=1`
   - 必须带 `Accept: text/csv`；不带时返回 0 字节（实测）。
2. `fetch_trades.py`：取 16 个已关闭事件（8 周 × 州名单/州数）的 Gamma 市场与 data-api 成交，存 `_cache/trades_all.json`。
3. 复跑前先解压事件与成交缓存：
   - `gunzip -c _cache/events_closed0.json.gz > _cache/events_closed0.json`
   - `gunzip -c _cache/trades_all.json.gz > _cache/trades_all.json`
4. `analyze_ask.py` → `ask_quotes.json`（每个州市场截止前 72h 内最后的 ask 侧 / bid 侧成交）。
5. `build_dataset.py` → `dataset.csv`（320 个州市场：前一周 D4、当周 D4、结算、截止前最后成交）。
6. `baserates.py` → `baserates.log`（67,056 个连续州-周转移，2000–2026）；`seasonality.py` → `seasonality.log`（`0→D4` 月率）；`roster_rates.py` → `roster_rates.log`（只看 40 个在册州）。
7. `walkforward_rule.py` → `walkforward_rule.log`（分桶延续率 + 5¢ 安全垫规则的回放）。
8. `analyze2.py`、`actual_pnl.py`、`per_week.py`、`capacity.py`、`bracket_check.py`：成交价、实际份数、分周汇总、容量、州数档核对。
9. `source_checks.log`：URL HTTP 状态、USDM 发布节奏原文、州市场规则原文；`entry_checks.log`：条目的字段/章节自检。

注：`fetch_usdm.log` 为空是因为 48 个州的 CSV 已全部在 `_cache/usdm/`，脚本直接跳过；删掉该目录再跑即可重新抓取。

## 关键输出

- 州市场结算 vs USDM 复算：320/320 一致；州数档 8/8 一致（样本内恒为 `10+`）。
- 2000–2026 分桶延续率：`[.05,.25)` 81.16%、`[.25,1)` 90.66%、`[1,5)` 94.29%、`>=5` 98.08%；`0` 状态下周进入 D4 0.38%。
- 主规则（5¢ 安全垫、1¢ 滑点、0.05 taker）：YES 14 笔 13 胜，净 +$2.9848/份等价、资本 $10.0152；NO 9 笔 9 胜，净 +$1.3050、资本 $7.6950；合计 23 笔 22 胜，+$4.2898 / $17.7102 = +24.22%。
- 按最后成交份数计：1,020.57 份、成本 $766.93、净 $245.64（+32.03%），但总名义额只有约 $750/8 周，容量很小。
- 独立结果只有 8 个周发布（州名单与州数同一结算源，合并计 1 个）；两周最多 2 个，门槛 6 不满足。

## 限制

- 历史盘口不可得；价格用 data-api 的「截止前 72h 内最后 ask 侧成交」做代理，再额外加 1¢ 滑点。不是可成交盘口的实测。
- 8 周样本中 4 周有 YES 交易、3 周有 NO 交易；州-周观测高度相关，不按独立结果计。
- 早期（2026-08-25）报价 0.50–0.55 的 edge 最大，后期升到 0.80–0.94，edge 在收敛。可能是新模板上线摩擦，不是持久机制。
