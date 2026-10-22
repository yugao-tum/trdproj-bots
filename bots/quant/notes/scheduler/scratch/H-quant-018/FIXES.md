# H-quant-018 fix log (2026-10-21, updated 2026-10-22)

Scope: `bots/quant/entries/quant-018-strait-transit-count-base-rate.md`,
`bots/quant/replay/quant-018/**`, this scratch directory. No `status`, `date`,
`id` or filename change. No trading, keys or paid data.

## 2026-10-22 pass (review c20261022-063202)

Problems read from `reviews/c20261022-063202-research.md` §H-quant-018,
`reviews/c20261021-070001-research.md`, and audits c20261020-1423 /
c20261020-170337 / c20261021-030001 / c20261021-070001. All fixes are
inside the three allowed paths.

| # | Problem | Change | Evidence |
|---|---|---|---|
| A | **Stale headline edge.** Review 063202 #4: lines quoting YES 0.127/0.16 and +0.0682/份 could still be read as a live opportunity; audit c20261020-170337 §2.2 re-grabbed 0.024/0.333. | Marked the quote as a **2026-10-20 snapshot**, added the 2026-10-21 (0.024/0.333) and 2026-10-22 (0.006/0.155) re-fetches, and stated that at the 10-22 quote NO costs 0.994 against fair 0.9412, i.e. **−0.0528/份**, so the rule does not trigger. Removed the “live +7.8%” reading in §4.2 and 钱从哪里来. | Live re-fetch in `verify_sources_stdout.txt`: Bab `<170` bid/ask 0.006/0.155; entry now carries both timestamps. audit c20261020-170337 §2.2 cited beside the old snapshot. |
| B | **Internal contradiction on destination.** The intro said “建议降为待选区” while §§4.5 and 结论 said “不应按待选区候选处理；降为草稿或并入 quant-012”. | Rewrote the intro conclusion to one line: **demote to 草稿 or merge into quant-012; counter-evidence/supplement only, max 0.5, no independent 待核 slot**. Changed the frozen “容量失败 → 进待选区” wording to “按失败处理；本条已不建议进待选区”. | `grep -n "待选区" entry` now shows only the removed-candidate statement and the frozen-criteria disclaimer; no conflicting recommendation. |
| C | **Gate 5/6 wording lacked the post-decision result.** Review 063202 #3 asked to add “独立事件 10<30, bootstrap CI 跨 0, STRICT60 11/12 不可成交”. | Gate 5 now names the bootstrap interval and STRICT60 −0.92; gate 6 already names 10<30 and 1/12 fillable, and the conclusion says 11/12 events unfillable. | Entry 门槛自查 5/6 and 结论与建议; `replay/quant-018/stdout.txt` prints `strict60 shares=1 events=1 median=-0.9200`; `SUMMARY.md` V4 row. |
| D | **Contribution could be read as measured.** Review 070001 #2. | Kept `contribution: 1.5%` but every occurrence is labelled **上限粗算，未由成交深度验证**; SUMMARY says V3's higher arithmetic is not used. | `grep -n "上限粗算" entry SUMMARY.md`; replay's `annualised contribution ... 1.5%` comes from 1-share × assumed 200 USDT/event. |
| E | **Round-2 fields and replay consistency.** | Re-ran `verify_citations.py` after the 10-22 edits: 8 fields valid and agree with `replay/quant-018/SUMMARY.md` (`variants=4`, `window=2026-07-20..2026-10-18`, `result=不显著`, `contribution=1.5%`). | `verify_citations_stdout.txt`: `summary: 25 checks, PASS=25, FAIL=0`. |
| F | **Sources must exist and say what is claimed.** | Re-ran `verify_sources.py` (17 出处 URLs) and `verify_citations.py` (whole entry, 25 checks). Whole-entry local refs now **19** paths and **5** frozen sha1s. | `verify_sources_stdout.txt`: `17 URLs, PASS=17, CHANGED=0, FAIL=0`. `verify_citations_stdout.txt`: `25 checks, PASS=25, FAIL=0`. PortWatch still 5,696 rows / 2,848 per strait / latest 2026-10-18. |
| G | **Replay must reproduce.** | Re-ran `python3 bots/quant/replay/quant-018/replay.py`; also re-ran the scratch `tradable_backtest.py` and `brier_start_check.py`. | replay `diff stdout.txt → empty`; tradable stdout reproduces 21 shares/10 events, +0.7116, per-$1 +0.0465, draft +0.0094, event median −0.1800, 5¢ draft −0.0203, OOS +0.5900; brier start 0.743627 vs model 0.774672 (diff −0.031045). |
| H | **Status request conflict.** Review 063202/070001 asked `status: 草稿`; the queue task and HARD RULES say keep the existing `status`/`date` exactly. | Left `status: 待核` and `date: 2026-10-20` untouched; wrote the demotion recommendation in the entry and here. Integrator decides. | Front matter lines 17-18 unchanged; `grep -n '^status\|^date' entry`. |
| I | **Lint.** | Ran `python3 tools/check.py lint --bot quant`. | `检查完毕，问题 0 个` (see `lint_output.txt`). |

Verdict: the honest evidence stays **negative/insignificant** — 10 triggered
independent events < 30, bootstrap intervals cross 0, draft event median
−0.1800, 5¢ stress −0.0203/$, STRICT60 1 fill at −0.92. The entry recommends
demotion/merge, not promotion. No number was inflated.

---


Sources read: `notes/scheduler/reviews/c20261021-070001-research.md` (H-quant-018
section), `reviews/c20261020-1423-research.md`, `checks/B23.md`,
`audit/c20261020-1423-research.md`, `audit/c20261020-170337-research.md`,
`audit/c20261021-030001-research.md`, `audit/c20261021-070001-research.md`.

| # | Problem (source) | Change | Evidence |
|---|---|---|---|
| 1 | **Slot/status conflict.** Review 070001 §H-quant-018 #1 and audit S3/S5: quant-018 is only a supplement to quant-012 (and composer-004/dot-051 are further supplements), so it must not hold a second independent 待核 slot; the review asked for `status: 草稿`. | Could not change front-matter `status`/`date` (queue task and HARD RULES: keep exactly as-is; integrator promotes/demotes). Instead wrote the demotion recommendation explicitly in the intro, `改进了什么`, `门槛自查 4` and `结论与建议`: **quant-012 is the primary entry; 018 is its supplement; integrator should demote it to 草稿 or merge it into quant-012; 018 does not claim a separate slot.** | Edited entry lines near the intro, §“改进了什么”, gate 4 and conclusion; `grep -n "quant-012" entry` shows the primary/supplement statement. Front matter unchanged: `status: 待核`, `date: 2026-10-20`. |
| 2 | **Contribution 1.5% looked like measured profit.** Review 070001 #2: the 1.5% multiplies the 1-share replay by an unverified 200 USDT/event cap; label it an upper-bound estimate. | Added “**上限粗算，未由成交深度验证**；1 份/档，200 USDT/event 是假设而非实测容量” at both places where 1.5% appears (成本与容量, gate 5, conclusion) and in `replay/quant-018/SUMMARY.md`. | `grep -n "上限粗算"` in entry and SUMMARY; replay still prints 1.5% from the same formula. |
| 3 | **Headline could be read as 21 independent results.** Review 070001 #4: keep the 10 triggered events as the headline, not 21 shares. | Entry already used 10 events; no numeric change. Added the same 10-event headline to the 4.6 note and kept `result: 不显著`. | Entry 4.5/4.6/gate 5/6 and replay stdout all show `events=10`, `bootstrap [-0.216,+0.261]`, `result 不显著`. |
| 4 | **Brier “start-price subset” row previously used first prices.** Audit S3/S7 (already partially fixed in an earlier pass). | Verified the table now has two rows: “有周起点价的子集（市场仍用首价）0.8093” and “周起点价子集（市场用 start 价）0.7436, model 0.7747, **−0.0310**”; §4.4 and dot-051 cross-check state that gate 3 PASS applies only to first-price. No new number. | `python3 scratch/H-quant-018/brier_start_check.py` → `start=0.743627`, `model=0.774672`, `start-model=-0.031045`, Bab subset −0.065706; saved in `brier_start_check_stdout.txt`. |
| 5 | **Need a real tradable-price replay, net of fees, with OOS.** Round-2 requirement / queue note. | Re-ran the existing real-print replay from scratch: `[T−24h,T]` last data-api print, fee 0 from Gamma, base 1¢ and 5¢ stress, 12 draft events + 1 post-draft OOS (2026-10-12). No parameter change. | `python3 scratch/H-quant-018/tradable_backtest.py` reproduces the saved stdout exactly: base all 21 shares/10 events total +0.7116, per-$1 +0.0465, event median +0.0850; draft per-$1 +0.0094, event median −0.1800; 5¢ draft per-$1 −0.0203; OOS +0.5900 (1 event). `diff tradable_backtest_stdout.txt` is empty. |
| 6 | **Replay must reproduce and be runnable offline.** | Re-ran `python3 bots/quant/replay/quant-018/replay.py`; it reads frozen inputs, writes `trades.csv`, and its stdout matched the committed `stdout.txt` byte-for-byte. | `diff bots/quant/replay/quant-018/stdout.txt <(python3 bots/quant/replay/quant-018/replay.py)` → no output. |
| 7 | **“Verify every cited source exists and says what is claimed.”** | Re-ran `verify_sources.py` (17 出处 URLs, all HTTP 200) and added `verify_citations.py`, which scans the whole entry (body included): external URLs, OOS resolution `170-189`, data-api print fields, PortWatch 5,696 rows/2,848 days/latest 2026-10-18, all 14 cited local paths, 3 frozen sha1s, and the 8 round-2 fields vs `SUMMARY.md`. | `verify_sources_stdout.txt`: `17 URLs, PASS=17, FAIL=0`. `verify_citations_stdout.txt`: `25 checks, PASS=25, FAIL=0`. |
| 8 | **Round-2 fields must be valid and agree with replay SUMMARY.** | Checked all 8 fields: `evidence: 回放`, `result: 不显著`, `slot: -`, `variants: 4` (2026-10-22: V1/V2 pre-decision, V3/V4 post-decision), `variants_ext: -`, `window: 2026-07-20..2026-10-18`, `max_dd: -` (Polymarket, GUIDE §7 allows `-`; replay summary says the same), `contribution: 1.5%`. Cross-checked against `replay/quant-018/SUMMARY.md`. | `verify_citations.py` §4: “8 round-2 fields valid” and “entry fields agree with replay/SUMMARY.md” both PASS. `python3 tools/check.py lint --bot quant` → `检查完毕，问题 0 个`. |
| 9 | **Snapshot drift (PortWatch rows/latest date, clobRewards, volume, bids).** Audit S10. | Kept the dated 2026-10-20 snapshot and the 2026-10-21 re-check side by side; latest re-fetch: 5,696 rows, 2,848 days per strait, latest 2026-10-18. No old number was overwritten. | `verify_sources_stdout.txt` and `verify_citations_stdout.txt` PortWatch lines; entry §4.1 and 数据 already contain both dated snapshots. |
| 10 | **Honest negative evidence.** Reviewed economics are weak (10 events < 30; 5¢ draft per-$1 negative; bootstrap crosses 0). | Kept `result: 不显著`; conclusion recommends 待选区 and explicitly says this is a negative/insignificant result, not a profitable strategy. Did not inflate any number. | Entry conclusion; replay summary “不可靠或失败原因”; replay stdout `events=10 (<30) => INSUFFICIENT`. |

## Status of the 7 gates (after this pass)

1 mechanism: basic (single cross-section only); 2 free data: conditional (data-api prints, no historical depth); 3 small capital: yes; 4 no duplication: **no — supplement to quant-012**; 5 net-of-cost: **uncertain, leaning negative**; 6 two-week ≥30 independent: **no (10 events)**; 7 sources: yes (17/17 URLs, 25/25 whole-entry checks).

## Open problems

- The review’s requested `status` change was not applied because this fixer task forbids changing `status`/`date`; integrator must demote/merge.
- Only 10 triggered independent events; one post-draft OOS event. Cannot reach the 30-event gate without more forward history.
- data-api gives prints, not order-book depth; 1¢/5¢ half-spread is an assumption.
- PortWatch is the current revised vintage, not the `T`-time vintage; the 2026-03..05 seven mismatches remain unexplained.
