# composer-008 回放摘要（USGS M5.5+ 周计数 vs Gamma 结算档）

**条目**：`composer-008-pm-usgs-weekly-55-quake-count`  
**生成**：2026-10-21 UTC（T12 目录化；数据快照见 JSON `generated_utc`）

## 窗口与数据

| 项 | 值 |
|---|---|
| 数据源 | USGS FDSN `event/1/count`，`minmagnitude=5.5`（免密钥） |
| Gamma | `public-search` closed events，slug 含 `5pt5-or-above-earthquakes` |
| 开发/回放窗口 | 各 closed event 的 spec 周（脚本从 slug 解析起止日） |
| 成本假设 | **未模拟 PM 成交价**；本条回放仅验证「USGS 计数 → 结算档」映射，不含吃单费/价差 |
| 变体 | **1**（单套 bracket 映射：精确数字 → `>` → `≤`） |

## 独立结果

- **计法**：每个 closed 周 event = 1 个独立结果（GUIDE：按 event 数）。
- **可评分**：**5** 周（`bracket_for_count` 能给出预测档且 Gamma 有 winning 档）。
- **USGS 预测档与结算档一致**：**3 / 5**（60%）。

完整行级明细：`notes/cache/usgs_weekly_55_replay.json`（复跑脚本后覆盖）。

## 复现

```bash
cd bots/composer
python3 replay/composer-008/run_replay.py
# 或：python3 notes/usgs_weekly_55_replay.py
```

## 已知局限（写入 008 门槛）

- ET 日历周 vs USGS `starttime/endtime`（UTC）边界可能导致 off-by-one（例 4/13 周 USGS=9、结算 `>9`）。
- 部分周档位标题为裸数字（如 `3`），映射规则可能返回 `null`。
- 结算档对照本身不含成交价。成交价层见下节（T21，2026-10-21）。

## 成交价层（data-api，T21，2026-10-21 11:02 UTC）

脚本 `replay/composer-008/trade_replay.py`，结果 `trade_replay.json`。

| 项 | 值 |
|---|---|
| 价格 | data-api `trades` 的 YES 成交价。不用 CLOB `prices-history` |
| 进场 | 预测档上，spec 周结束前 48 小时内、价格在 (0.02, 0.97) 的 YES 成交，取中位数 |
| 费用 | 每份 `0.05 × p × (1−p)` |
| 样本 | 预测档非空的 **5** 周全部有窗内成交 |
| 胜负 | **3 胜 2 负**（与结算档对照一致） |
| 每份净收益均值 | **+0.0139** |

两笔亏损来自档位错位（4/13 周预测 `9`、结算 `>9`，−0.242；5/11 周预测 `7`、结算 `6`，−0.328）。三笔命中的进场价已是 0.60、0.81、0.93，扣费后剩得少。**n=5，不宣称显著，也不改待核结论。**

局限：用的是周末 USGS 终值去选档，窗内较早的成交当时还不知道终值；USGS 修订未单列。

## 扣成本后净收益

成交价层均值 **+0.0139 / 份**（n=5，见上）。结算档对照本身仍不计价。
