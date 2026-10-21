Follow-up to merged PR #18 (quant-016 historical tradable-price backtest). This PR addresses the two P2 inline review comments left on `q016_hist.py` and re-runs the study with cache reuse.

## Review comment 1 — `q016_hist.py:867`: zero-trade priced events omitted from event statistics

**Fix:** a priced event with no trigger now contributes the declared empty-sum result `0` to the PRIMARY event statistics. The old triggered-only view is retained as a clearly labelled SECONDARY view.

Frozen declaration quoted from the script header (`q016_hist.py`, PRE-DECLARED DESIGN):

> `Event result = sum of net/share over its triggered thresholds (equal one share each).`

and from the frozen entry criterion (`bots/quant/entries/quant-016-rotten-tomatoes-beta-model.md`):

> `独立结果按 event 计（同片各档共享一次结算，算 1 个）`

The empty sum is 0, so all priced events with zeros is the pre-declared PRIMARY view.

| event statistic | n | median net/share | mean net/share | bootstrap 95% CI |
|---|---:|---:|---:|---:|
| **PRIMARY: all priced events, zero-trigger = 0 (v2)** | 66 | **-0.054190** | **-0.062616** | **[-0.132925, +0.014020]** |
| SECONDARY: triggered-only (v1 old view) | 52 | -0.113876 | -0.079474 | [-0.168443, +0.017816] |

This independently reproduces the reviewer's numbers: median -0.113876 → **-0.054190** (review ≈ -0.0542), mean -0.079474 → **-0.062616** (review ≈ -0.0626). Sensitivity window: PRIMARY median **-0.026219**, mean **-0.055922**; SECONDARY median -0.104500, mean -0.071619.

## Review comment 2 — `q016_hist.py:303`: unverified slug fallback counted as mapped

**Fix:** RT search maintenance/error pages are no longer cached or reused as successful searches. Any non-exact-title fallback slug must be verified on a live RT film page (page exists, normalized title matches, year within 1 of the event year); otherwise the event is marked `slug_fallback_unmapped` and `rt_slug` is blank. This also fixes the failed-download-saved-as-complete cache class.

- v1 claim was 85/85 mapped, but it was actually **83 exact-title + 2 unverified fallback** (`evil_dead_burn`, `over_your_live_body`).
- The old example `/m/over_your_live_body` is live **HTTP 404**.
- Refreshing the invalid search cache finds the correct 2026 page `/m/over_your_dead_body_2026` (live **HTTP 200**, title `Over Your Dead Body (2026)`).
- v2: **mapped 85/85, all `rt_search_exact_title`, unmapped = 0**. The wrong fallback was corrected, not silently counted. If search refresh fails, the verifier marks the 404 slug unmapped.
- The corrected event adds a snapshot (`20260426124238`) but has no executable trade in `[t-6h,t]` (`priced_thresholds=0`), so the priced-event/P&L sample stays at 66. Snapshot coverage moves from 73/80 to 74/81; no-primary-snapshot events 11 → 10.

## Cache audit

- `_cache/rt_search`: 2 maintenance pages had been saved as complete searches (the v1 fallback cases). Fixed; after re-run `rt_search files=84 maintenance_or_invalid=0`.
- Wayback snapshots: 109 files, `partial_or_error=0`; no truncated/error HTML accepted. `fetch_snapshot` now validates and deletes invalid cache entries.
- CDX: 90 files, `invalid=0`; suspicious empty lists for `fantasy_life` and `the_weight_2026` were re-queried over wider windows and are genuinely empty inside their target windows (0 captures). CDX/timemap non-empty unparsable responses are no longer written back as `[]`.
- Trades: 669 files, `invalid=0`, `max_rows=131`, no file ≥500 rows; malformed JSON or an incomplete 50-page pagination is now refused instead of cached.

## Verdict

**Unchanged: FAIL.** PRIMARY median event net is -0.054190 (≤0), median filled-share gross is -0.034787 (≤0), model Brier is +0.031268 worse and log loss +0.093056 worse than market. Including zeros and correcting the mapping does not change the frozen FAIL triggers.

## Reproduce / outputs

```bash
cd bots/quant/notes/q016-hist
python3 q016_hist.py > run_output.txt
python3 v2_audit.py > v2_audit_output.txt
python3 v2_evidence.py > v2_evidence.txt
```

- v1 stdout preserved: `run_output_v1.txt` (sha256 `dbfce42c...a9fa`)
- v2 stdout: `run_output.txt` (sha256 `46f410db...dead`)
- v2 `events.csv` (sha256 `7c8bd597...f626`), v1 `events_v1.csv` (sha256 `d0e9121a...8065`)
- Details and old-vs-new table: `REPORT.md` section **“v2 修复”**
- Raw downloads remain in gitignored `_cache/`; all committed files <1 MB.

Refs: merged PR #18; review comments on `q016_hist.py:867` and `q016_hist.py:303`.
