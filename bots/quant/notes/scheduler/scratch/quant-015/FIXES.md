# quant-015 fixer changelog — 2026-10-20

Entry: `bots/quant/entries/quant-015-global-temp-era5-nowcast.md`
Role: fixer (queue item quant-015). Filename, `id`, `date` and `status` were left unchanged. The entry was already promoted to `status: 待核` on 2026-10-20; this pass did not change status or date.

## Where the review problems came from

`bots/quant/notes/scheduler/reviews/`, `.../checks/` and `.../audit/` do not exist in this worktree (verified with `find` / `ls`). I therefore read every available file that mentions quant-015:

- `bots/quant/notes/r2prep-verification/quant-015.md` — round-2 verification log + glm-5.3 fact-check (VERDICT: KEEP; minor time-varying/fetch-log problems).
- `bots/quant/notes/batch2-verification/quant-015.md` — earlier verification + glm-5.3 fact-check (VERDICT: FIX on the old revision: 945-month mislabel, `id: quant-XXX`, `No_Smoothing` wording).
- `bots/quant/notes/r1-audit/AUDIT.md` — repository audit; quant-015 listed as not duplicate, expected 待选区, no entry-level defect.
- `bots/quant/notes/batch3-shortlist-glm-review.md` — only a keyword/duplication reference, no quant-015 defect.

Re-fetched all live sources on 2026-10-20 and re-ran every number in the entry. Raw files are in `_cache/` (gitignored), scripts and stdout are in this directory.

## Problems → changes → evidence

| # | Listed problem | What I changed | Evidence / re-check |
|---:|---|---|---|
| 1 | `r2prep` glm: byte counts are time-varying (`public-search` 829,034 → 829,041 at review time) | Updated the two entry citations of the search response to today's fetch: **829,034 → 829,059 bytes**. Event count/period unchanged (33 events, 32 closed, 1 open, 29 months). | `_cache/search.json` = 829,059 bytes; `pm_count.out` first two lines. |
| 2 | `r2prep` glm: review log's CDX row order was wrong (log-only; entry only claims 82 snapshots / 45 since 2023-01) | **No entry edit.** Re-fetched CDX to confirm the entry's numbers. | `_cache/cdx.json` = 16,974 bytes, 83 JSON rows = 82 snapshots, first `20190721182200`, 45 snapshots from 2023-01. The entry never claimed the bad log ordering. |
| 3 | `batch2` glm (old revision): "945 months (1948-01…2025-12)" was mislabeled and the test was in-sample, not walk-forward | **No edit needed in the current revision.** Current text already uses a true rolling 120-month walk-forward (2000-01…2026-09, 321 months). Re-ran it against fresh files. | `walkforward.out`: `n=321, skipped=0`, `LL_model=1.3638`, `LL_persist=2.0608`, `LL_uniform=2.0794`, hit `123/321=0.3832`, PIT `0.5003`, KS `0.0372`, `2024-2026 LL=1.7819`; matches the entry exactly. |
| 4 | `batch2` glm (old revision): `id: quant-XXX` placeholder | **No edit needed.** Front matter is already `id: quant-015` and matches the filename. | Entry line 2; `tools/check.py` id rule would accept `quant-015`. |
| 5 | `batch2` glm (old revision): `No_Smoothing` wording came from the annual market, not the monthly text | **No edit needed.** The phrase is absent from the current revision; the entry quotes the monthly table title/column/row only. | Entry §规则 and §出处; Sept event description re-read from `_cache/sept2026.json`. |
| 6 | Re-fetch correction (consequence of "re-fetch the source", not a new research claim): ERA5 daily CSV rolled forward during 2026-10-20 | Updated the data line and 出处 from `1,198,225 bytes / 31,721 行 / 末行 2026-10-17 … 0.894 PRELIMINARY / Last updated: 19 Oct 2026` to **`1,198,262 bytes / 31,722 行 / 末行 2026-10-18 … 0.889 PRELIMINARY / Last updated: 20 Oct 2026`**. Front-matter latest day `2026-10-17 → 2026-10-18`. | `wc -c _cache/era5.csv` = 1,198,262; `wc -l` = 31,722; `tail` = `2026-10-18,15.260,14.371,0.889,PRELIMINARY`; `grep 'Last updated'` = `20 Oct 2026`. 2026-10-17 is now `FINAL,0.899`; the analysis month 2026-09 is unaffected. |
| 7 | Re-fetch correction: Pulse status JSON advanced one day | `{"daily": 20261017, …}` → **`{"daily": 20261018, "monthly": 202609, "annual": 2025}`** (both in 数据 and 出处). Monthly status still `202609`, so the entry's "整月 ERA5 到 2026-09 已可用" is unchanged. | `_cache/status.json` = 63 bytes, exact value above. |
| 8 | `batch2`/`r2prep`: CLOB point counts and first point are time-varying (the old log saw 469/468 points and `2026-09-20T06:00Z p=0.47`) | Updated entry evidence 7 and 出处 to the current fetch: Sept event **454–458 points** (was 466–468), October **465–471 points** (was 454–460); the cited `1.35–1.39` token is **458 points**, first point **`2026-09-20T16:00Z` p=0.45**, last `2026-10-09T16:00Z` p=0.905; byte count **12,380 → 12,119**. | `pm_histcheck.out`: sept `[455,457,458,455,454,455]`, oct `[465,471,465,471,471,469]`, 191 tokens, 2 events non-empty. Exact token fetch: 12,119 bytes, 458 points, first `{t:1789920013,p:0.45}` = 2026-09-20 16:00 UTC. |

## Numbers that reproduced exactly (no edit)

All core analysis numbers in the entry match a fresh run against today's files:

- `walkforward.out` — main rolling 120: n=321, hit 123/321=0.3832, persistence 42/321=0.1308, LL 1.3638 / 2.0608 / 2.0794, cov80 0.7726, cov90 0.8816; 2024-2026 LL 1.7819; expanding LL 1.5173, PIT mean 0.6061, KS 0.2279; rolling 60 LL 1.3669, cov80 0.7352.
- Latest month 2026-09: ERA5 mean 0.8191, `a=0.591262`, `b=0.970383`, `σ=0.056299`, pred 1.3861, actual 1.38, bracket probabilities 0.0467 / 0.1799 / 0.3301 / 0.2895 / 0.1212 / 0.0242.
- `pm_model_market.out` — 2026-10-05: model 0.3301 vs market normalized 0.6880; model LL 1.1083 vs market LL 0.3740. 2026-10-09: market normalized 0.9972; market LL 0.0028. Unchanged.
- `firstrelease_local.out` — 45 snapshots, 30/33 months covered, mean revision +0.002, mean absolute 0.012, sd 0.0158, max 0.04, bracket unchanged 23/30=0.7667, exact same 8/30, hit revised 9/30 vs first 7/30 (diff −2), same 7 bracket-change months.
- Gamma: Sept event 26,352 bytes, `closed=true`, volume 11127.859859, openInterest 8452.463409, six brackets, `1.35–1.39` `["1","0"]`, all `umaResolutionStatus=resolved`, fee 0.05 / rebate 0.25; Aug event 25,839 bytes, `>1.29` `["1","0"]`.
- GISTEMP: 17,039 bytes, 2026 row `108 123 130 116 113 117 124 142 138` (Aug 1.42, Sep 1.38); updates page 19,967 bytes with the "middle of every month" quote.

## Files written / changed

- `bots/quant/entries/quant-015-global-temp-era5-nowcast.md` — only the fetch-metadata lines above (front-matter `data`, evidence 7 point ranges, 数据 ERA5/status lines, 出处 search/ERA5/status/CLOB lines). Analysis, rules, gates and conclusions untouched.
- `bots/quant/notes/scheduler/scratch/quant-015/.gitignore` — `_cache/`.
- `.../fetch_data.sh`, `run_all.sh`, `walkforward.py`, `pm_histcheck.py`, `pm_count.py`, `pm_model_market.py`, `firstrelease_local.py`.
- `.../walkforward.out`, `pm_histcheck.out`, `pm_count.out`, `pm_model_market.out`, `firstrelease_local.out`.
- `.../FIXES.md` — this file.
- `_cache/` — raw downloads and 45 Wayback snapshots, gitignored.

## Gate verdict after this pass

1 机制说得清 — 满足 (unchanged: structural release lag, sources quoted).
2 有免费数据能检验 — 不确定 (prediction side reproducible; only 1 closed event with CLOB history, unchanged).
3 小资金能做 — 满足 (unchanged).
4 不重复 — 不确定 / 主审确认 (r1-audit judged not a duplicate of quant-012 or dot-001/002).
5 扣成本后粗算够用 — 不满足 (unchanged; n=1 model loses to market).
6 两周内能检验 — 不满足 (max 2 independent events in 2 weeks).
7 出处可查 — 满足 (all cited URLs re-fetched today; failures/vintage limits disclosed).

Overall: still a 待选区-grade entry (gates 2/5/6 not all met), unchanged in substance. No new claims, no new data source, no status promotion.

## Open problems (not fixed here)

- `status` remains `待核` because the queue instruction says keep it exactly; promotion/demotion is the integrator's call.
- CLOB history keeps shrinking for the closed Sept event (469 → 458 points during the day), so any future re-check must re-read the ranges rather than trust a point count.
- ERA5 "first-release vintage" is still unavailable; the entry's walk-forward uses current reanalysis values, and the Wayback proxy covers 30/33 months only.
- The `r2prep` log's CDX first-row ordering error is in the review log, not the entry; I did not edit review files (outside the allowed paths).
