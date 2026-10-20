# Fact-check report: Q04b.md (quant)

## Network re-fetches (11 fetches)

**VERIFIED** — Gamma `events?slug=`: NVIDIA earnings (startTime `2026-08-26T21:00:00Z`, desc "August 26, 2026 at 5:00 PM ET"); Kansas rally (startTime 23:00Z, all 22 markets `endDate` 22:05Z, desc 6:00 PM ET → "三个来源互不一致" confirmed); JD-Vance RNC (desc "September 9, 2026 at 10 AM ET", gamma `2026-09-10T23:00:00Z` = +33h); NASA 15:00Z; Warsh 14:00Z; Ternus 17:00Z; UN-meetings desc "between market creation and September 22, 2026, 11:59 PM ET" (date_only downgrade rule works as described). `feeSchedule.rate`=0.04 on every market sampled. CLOB: `interval=max` on the 2026-07-05 Brazil-vs-Norway token returns exactly 15 bytes `{"history":[]}`; `startTs/endTs` 3,000,s returns the exact quoted error string.

**MISMATCH** — §1: "改成 `startTs/endTs` 区间后能拿到 **309 个点**". Live fetch with the described window ([t_start−12d, t_start+1d], fidelity=60) returns **11 points**; the worker's own cached file for that token also has 11; all 27 markets of that event have 9–13 cached points; fidelity=10 gives 68. The qualitative claim (startTs/endTs rescues empty history) is true; "309" is unreproducible. Fix: replace with 11 (or delete the count).

## Script re-run (step 3b)

Embedded `parse_start.py`/`ext_fetch.py`/`q04b_bt.py` are byte-identical to work-dir files. Re-ran both analysis scripts: outputs reproduce **exactly** (0 diff lines). All 72 rows of `results_q04b.csv` match the entry's four tables; supplementary table recomputed exactly (avg cost 0.801–0.806, win 0.830–0.858, excess +2.4–5.6pp); all fee rates 0.04. §2.5 stats (median 3.98h, 524 ≤10min, 677/1493=45.3%, 36/1493=2.4%, 657=550@23:59+107@03:59), §4 counts (80 explicit / 1,876 tokens, ranks 401–600), eventDate 46/1313, eventStartTime 665/23,605 (576=endDate), and 前作 numbers (t=2.37, t=6.21, R3 +1.56%, spread 0.001–0.86 in quant-004 line 113) all verified.

## Rule compliance (GUIDE.md)

1. **Missing ENTRY.md front matter** (id/name_zh/market/pm_category/kind/improves/status/confidence…) and missing **门槛自查**, **出处** (with access dates), **test_2w** sections — fine as a work report, not submittable as an entry. Fix: reformat as `kind: improvement`, `improves: quant-004`.
2. 来源自报： N/A (all self-computed) ✓. Fee formula ✓. Keyless/paid/trading ✓. No unrun-backtest claims ✓; honesty excellent (concludes R1 not significant OOS).
3. Minor ambiguity: §0 "半价差 0.02 时 −7.91%（t=−2.66）" is the 400-sample only (200-sample: −8.37%, t=−1.88) — label the sample.

## Duplication

None: quant-004 is the author's own prior entry; Q04b is corrective new evidence (proper supplement/improvement); KNOWN.md and muse/dot contain no mention-market claims.

VERDICT: FIX — one unreproducible number ("309 个点") and missing entry-format sections; everything else reproduces bit-for-bit and duplication is clean.
GATES_PASSING: 4/7
