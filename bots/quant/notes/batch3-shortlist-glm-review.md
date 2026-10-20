# Fact-Check Report: S3.md (quant batch3 shortlist)

## Script re-runs (saved to `rev_S3/`, from `work_S3/`)
- `count_series.py` (6 series): **output matches V3 exactly** (tsa 26 ev/1,260,362; drought-d4 16/90,086; tornado 62/410,599; egg 17/7,460,014; fda 51/431,746; ipl 98/2,838,140).
- `ph2.py`: **all point counts match V5** (659/677, 62/167, 11/13, 168/168, 24, 218/228, egg 0). Note: its TSA slugs return `MISS`; the TSA "0 点" slugs in the entry text are different markets — I fetched them separately: both exist, 7 markets, fee 0.05/0.25; may-18-may-24 price history = **0 points ✓** (claim true, but V5 as printed is not the exact output of the saved script).
- `count_tag.py drought`: 37 events, vol 256,981 ✓ matches V2.

## URL re-fetches (~20)
All Gamma fields verified: NFL event 327 mkts, fee 0.03/0.15, resSrc nfl.com/scores, rule quote **verbatim** ✓; MLB 30 mkts 0.05/0.15 + quote ✓; tornado 25 mkts, 0.05/0.25, quote verbatim ✓; state-d4 40 mkts + "0.05%…40 of the 48" ✓; states-in-d4 6 brackets ✓; egg 8 mkts, feeSchedule=null, FRED APU0000708111 quote ✓; TSA 7 brackets + quote ✓; CS2 fee 0.05/0.15, event resSrc kick.com/stake_pulse ✓; IPL feeSchedule=null, RCB quote ✓; `nfl-2026` id=12185 rec=daily embedded in event ✓. External byte counts match exactly (ESPN cfb 873,603; MLB 12,086; Cricsheet 5,187,770; SPC 2,027; FDA 20,287; BLS 3,053; TSA.gov 195,641); FRED `000` failure **reproduces** (honest); ESPN NFL now 22,970 vs 22,990 (time-varying, timestamped); /series now 1250 vs 1254 (time-varying).

## Problems
1. **MISMATCH (quote fabrication risk)** — §3.5 quotes CS2 rule: *"if MIBR win against BC.Game Esports in the named Counter-Strike match… If the game is canceled entirely, with no make-up game, this market will resolve 50-50."* Source actually says "if MIBR **win the match against** BC.Game Esports" and "**If the match is canceled (not played at all) or ends in a tie**… 50-50" — the cancel clause is NFL wording, not in this market. Fix: replace with actual text.
2. **MISMATCH (arithmetic label)** — §3.3: "p=0.5 时 fee=0.05×0.25=1.25% 本金" — 1.25% is per share/notional; per GUIDE (费率×(1−p)) it is **2.5% of capital**, matching the entry's own "≥约 2.5 分". Fix label.
3. **Format non-compliance** — no YAML front matter (id/market/kind/status/test_2w…), no 门槛自查, no per-template 出处 with access dates. It is correctly parked as `notes/batch3-shortlist.md`; do not submit as a 待核 entry without reformatting (B21–B25 claims already registered).
4. **Duplication risks unflagged** — FDA deadline base-rate ≈ quant-009/quant-020 mechanism (variant); MLB pitching/lineup lag ≈ dot C13; TSA bracket nowcast ≈ quant-005 family. Only egg is flagged. Fix: add flags/合并说明.
5. Minor: V5 log omits the TSA MISS lines actually produced by `ph2.py`.

No keys/paid data; no unrun backtests claimed (explicitly disclaimed); 来源自报 labelling N/A (no third-party results cited).

VERDICT: FIX — one quoted rule text (CS2) is not in the source and must be corrected, though virtually all numbers and scripts reproduce.
GATES_PASSING: 3/7
