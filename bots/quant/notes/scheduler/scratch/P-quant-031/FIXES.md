# P-quant-031 / quant-031 fixer changelog

- 条目：`bots/quant/entries/quant-031-aaa-gas-daily-bracket.md`
- 队列项：P-quant-031（entry quant-031），2026-10-21 UTC
- 保持不动：文件名、`id: quant-031`、`date: 2026-10-21`、`status: 草稿`
- 依据：`bots/quant/notes/scheduler/reviews/c20261020-170337-research.md` B30 段；`bots/quant/notes/scheduler/audit/c20261021-030001-research.md` 只在 `held` 清单提到 B30，无新问题；`checks/` 无点名 B30/quant-031 的文件。

## 1. Review 的 7 条问题（逐条复核）

| # | Review 问题 | 现状 / 本次动作 | 证据 |
|---|---|---|---|
| 1 | CLOB 保留期“2–3 周”是一刀切错误 | 已改为“2025 事件 history 为空；2026-10 事件只从创建日起；`p` 不是卖价”，本次保留并复跑 | `verify_out.txt`：2025 事件 10 个市场 `ph_points 0`；`fetch_out.txt`：2026-10 已结算市场 135–172 点 |
| 2 | “0 个 ≤0.95 可成交样本”混淆“没成交”与“没卖单” | 已改为“0 笔 ≤0.95 实际 BUY 成交；决策时最优卖价未取到”，风险节标题同步 | `replay.py`：≤0.95 fills 0/5；data-api 无历史 L2 |
| 3 | 门 5/6 不满足，只能待选区 | 门 5/6 明确“不满足”；“处置建议”直说应 drop | 见下第 3 节 |
| 4 | 与 dot-004 的宽口径重复风险 | 保留 `kind: new`，写窄区别并明示“若判同一机制应改 supplement”；`slot` 不占新机制名额 | 条目“与最接近条目的区别”、字段 `slot: -` |
| 5 | 10-20 已结算，旧文“未结算观察”时间漂移 | 已改为 5 个已结算（10-16…10-20）+ 1 个未结算（10-21）；`date` 未动 | Gamma 实抓：5 closed / 1 open；`verify_out.txt` |
| 6 | “0.3–75 分钟”有支撑 | 保留，限定“有后续成交的 4 个事件”；10-16 单列 | `event_study_out.txt`：0.3 / 28.0 / 75.0 / 10.4 |
| 7 | `name_zh` 14 字、字段正常 | 未改 | front matter 检查 |

## 2. 第 2 轮补全（本次新增）

| 问题 | 改法 | 证据 |
|---|---|---|
| 缺 8 个 round-2 字段 | 在 `confidence` 后加：`evidence: 回放`、`result: 不显著`、`slot: -`、`variants: 3`、`variants_ext: -`、`window: 2026-10-16..2026-10-20`、`max_dd: -`、`contribution: 0.00%` | `python3 tools/check.py lint --bot quant` → 问题 0 个 |
| `evidence: 回放` 需要 replay 目录 | 新建 `bots/quant/replay/quant-031/`：`replay.py`、`decision_points.csv`、`trades.csv`、`SUMMARY.md` | 见第 3 节复跑命令 |
| `result` 未定义 | 写 `不显著`：只有 5 个独立结果（<30），且条目规则 ≤0.95 为 0 笔成交，不能判正负 | `SUMMARY.md`“汇总结果” |
| `contribution` 未算 | ≤0.95 规则 0 笔成交 → `0.00%`；放宽到 0.99 为 0.7067/5×73÷5000 ≈ 1.03%/年，仅在正文注明，不写进字段 | `SUMMARY.md` |
| `variants` 未数 | 3 个：≤0.95、≤0.99、不限价；事件研究/CLOB 中间价/2025 近似事件均不计变体 | `trades.csv` 两行变体；`SUMMARY.md` 变体表 |

## 3. 回放复跑（真实成交价，净费）

```bash
cd <repo-root>
python3 bots/quant/replay/quant-031/replay.py --write-trades
```

结果（`trades.csv`，2026-10-21 复跑）：

```text
limit<=0.95: fills 0 of 5
limit<=0.99: fills 2 of 5
  10-18 11:25:41 p=0.988457 size=75.50 net/sh=0.006087 net$=+0.4595
  10-19 10:20:54 p=0.988360 size=40.00 net/sh=0.006180 net$=+0.2472
  median_net/sh=0.006133 total_net$=+0.7067 cost$=114.74 ROI%=0.6159
market (any price): fills 3 of 5
  ... 10-20 13:59:21 p=0.999000 net/sh=-0.004040 net$=-0.2855
  median_net/sh=0.006087 total_net$=+0.4212 cost$=185.69 ROI%=0.2268
```

成本：吃单费 `0.04×p×(1−p)` + 半价差 0.005/份；成交价来自 data-api 逐笔 BUY，不用 CLOB `prices-history`；250 USDC/事件、按实际打印份数封顶。与 `backtest_trades_out.txt` 完全一致。

## 4. 处置结论（直说）

**建议退回/放弃（drop），不占第 2 轮 `待核` 名额。** 门 5 不满足（≤0.95 成交 0/5；≤0.99 仅 2 笔、+0.7067 USDC），门 6 不满足（历史 5 + 两周前向约 14 = 19 <30），门 2 只能靠前向补齐，门 4 仍有 dot-004 宽口径重复风险。`status: 草稿`、`date: 2026-10-21` 未改。

## 5. 复跑文件

`bots/quant/notes/scheduler/scratch/P-quant-031/`：`fetch_out.txt`、`verify_out.txt`、`backtest_trades_out.txt`、`recheck_out.txt`、`aaa_snapshots_all.csv`。原始下载放在 `_cache/`，该目录被 `.gitignore` 忽略，每个文件 <1 MB，不入库。
