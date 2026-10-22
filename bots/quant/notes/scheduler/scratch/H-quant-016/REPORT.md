# H-quant-016 hardening notes

Date: 2026-10-21 UTC. Role: improvement worker w06. Target: `bots/quant/entries/quant-016-rotten-tomatoes-beta-model.md` (status/date deliberately unchanged: `date: 2026-10-20`, `status: 待核`; only the integrator may change status).

## What was done

Reused merged notes with paths: `bots/quant/notes/batch2-verification/quant-016.md` (original fetch log and scripts) and `bots/quant/notes/scheduler/audit/c20261020-170337-research.md` §S2 (the earlier audit already flagged the floor/round error). The `q012-hist/` and `q006-hist/` reports are for other entries (earthquake / tennis), not for quant-016, so their results were not reused.

1. Re-fetched every cited source with `verify_sources.py` (stdout `verify_sources.out`).
2. Re-tested the RT rounding rule on 22 film pages with `check_rounding.py` (`check_rounding.out`).
3. Built a historical tradable-price dataset from data-api fills + CLOB `prices-history`
   (`fetch_data.py`, `fetch_data.out`, `markets.json`; raw JSON in gitignored `_cache/`).
4. Ran pre-registered model-free rules and descriptive calibration
   (`backtest.py`, `backtest.out`; `extra_stats.py`, `extra_stats.out`).

## Headline results

- Rounding is **round half up**, not floor: 22/22 pages match `round(100k/n)`, only
  10/22 match floor; all 12 pages that can distinguish the two match round.
  (Examples: `the_wild_robot` 252/261=96.5517→97; `other_mommy` 16/89=17.9775→18.)
- Historical price-side sample: 85 closed events, 84 with `endDate` and parseable `N+` brackets,
  525 brackets. At T-24h, 341 brackets / 82 events have a last YES-equivalent fill
  within 24h.
- T-24h market calibration: Brier **0.024829** vs constant base rate **0.247659**
  (event-level 0.029557 vs 0.250723).
- Pre-registered model-free rules at T-24h (taker fee 0.05 + 1c half-spread):
  - A buy NO, p>=0.90: 125 brackets / 59 events, mean net **-0.024966**/share, 0/59 positive.
  - B buy YES, p<=0.10: 170 / 64, mean **-0.018371**, 1/63 positive.
  - C buy NO, 0.25<=p<=0.75: 24 / 22, mean **-0.100814**, 9/13 positive.
  - Maker-fee-0 variant still negative: -0.024283 / -0.017724 / -0.089090.
  - CLOB-price sensitivity (495 brackets / 82 events at T-24h): -0.023901 / -0.024166 / -0.031979; same sign.
  - The only near-positive side is buying YES at p>=0.90: 125 brackets, +0.0036/share
    with the optimistic 1c half-spread; not the entry direction and not a strategy.
  - Both time halves (before/after 2026-08-01) are negative for all three rules.
  - Horizon sensitivity: T-48h A/B/C = -0.033131 / -0.005608 / -0.059512;
    T-6h = -0.017897 / -0.008070 / -0.094716; all negative.
- Market-implied boundary (p=0.5 crossing) equals the final boundary in **55/65**
  events (84.6%) at T-24h; 59/65 within 2 points.
- Market-implied boundary pair (buy YES lo, buy NO hi, 51 events): +0.0308 / -0.0272,
  sum +0.0036 per event, i.e. zero after costs.
- Exploratory (NOT pre-registered) buy YES on 0.25<=p<=0.90: 36 brackets / 31 events,
  mean +0.0881, event mean +0.1130, 22/9 positive, sign-test p=0.0294. Treated as a
  lead only; it does not validate the Beta model and needs independent pre-registration.

## What cannot be tested

Historical `(k,n)` at decision time is not available: RT `/reviews` is JS-rendered with
zero date fields; Wayback availability returned HTTP 429, Wayback CDX and archive.today
failed at TLS (000), and the Common Crawl index returned HTTP 504 on 2026-10-21. Therefore the Beta model itself
has **no** historical out-of-sample test. The price-side test above can only falsify the
"market misprices narrow brackets" premise, not validate the model.

## Files and reproduction

```
python3 fetch_data.py       # needs network; rewrites markets.json and _cache/
python3 backtest.py         # writes stdout only
python3 extra_stats.py
python3 check_rounding.py
python3 verify_sources.py
```

`_cache/` is gitignored and contains raw HTTP responses. `gamma_closed.json` was removed
because it exceeded 1 MB; `fetch_data.py` re-downloads it.

## Entry changes

- Fixed S2: floor → round half up, threshold `p >= (T-0.5)/100` with T±1 sensitivity.
- Fixed S6: removed the "status 只给草稿" sentence; replaced with an explicit
  recommendation to demote to 待选区 (status field untouched).
- Fixed stale/contradictory snapshots: open events 47→49 markets, $56,087→$70,508;
  fee rate 0.05→0 on current open markets; month table 84+1 empty endDate; RT page
  counts 78/102→82/106 and 15/87→16/89.
- Added evidence §7 with the historical price-side backtest and an explicit negative
  verdict for gate 5/6.

---

## 2026-10-22 更新（本轮 H-quant-016 改进工作）

**本文上文的“模型侧不可检验”结论已被后续合并笔记推翻，不要按上文引用。** 已合并的
`bots/quant/notes/q016-hist/`（提交 `e950778`）用 Wayback CDX 快照恢复了历史 `(k,m)`，
其中 66 个 event 有可成交价；`model_hist_round.py` 按本条 round-half-up 重算后模型仍
Brier 0.060450 vs 市场 0.035369、每美元 −0.325353，判 FAIL。

本轮把证据做成可重跑的成交价回放（canonical）：

- 目录：`bots/quant/replay/quant-016/`
- 脚本：`replay_model.py`（Beta 模型）、`replay_market.py`（市场侧 A/B/C）
- 汇总：`SUMMARY.md`（窗口 2026-03-02..2026-10-19；66 个独立 priced event；23 个变体）
- 逐笔/逐 event：`trades_model.csv`、`events_model.csv`
- stdout 副本：本目录 `replay_model_copy.out`、`replay_market_copy.out`、`replay_model_clob_copy.out`

2026-10-22 复核要点：

- `verify_entry_citations.py` 重抓：Gamma/CLOB/data-api/RT 18 PASS；Wayback CDX 恢复 200，
  归档快照 spot check 通过；availability / archive.ph / Common Crawl 仍 TLS 失败。
  stdout：`verify_entry_citations_replay.out`。
- RT 实时页按日期漂移：`clayface` 2026-10-22 为 67/22/89、score 75（条目只把带日期的快照当证据）。
- 取整重跑：23 个有显示分数的页面 23/23 round、11 个可区分样本全部 round。
  stdout：`check_rounding_replay.out`。

主回放数字（与已合并 `model_hist_round.out` 逐位一致）：

- 66 event / 192 有价档；87 笔 / 49 event；命中 8/87；Brier 0.060450 vs 0.035369；
  PRIMARY event 中位 −0.046602/份、均值 −0.055558/份；合计 −3.666836 / 投入 11.270339
  = 每美元 **−0.325353**。
- 模拟 300 USDT/event、5,000 USDT 账户：第 27/66 个 event 本金耗尽；max_dd 100%；
  线性年化贡献 −203.6%，按现金账户上限报告 −100%。
