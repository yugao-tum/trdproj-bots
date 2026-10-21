# B22 / quant-025 — review fixes changelog

Date: 2026-10-20 (UTC). Source review: `bots/quant/notes/scheduler/reviews/c20261020-1423-research.md` (B22 section). No check or audit file mentions B22 (`grep -rl 'B22|quant-025'` over `checks/`, `audit/` returned nothing except the review). Filename, `id`, `date` and `status: 草稿` unchanged.

All cited numbers were re-derived from a fresh cache this run:

```bash
python3 fetch_outlooks.py   # events=62 markets=1550 missing coords=0 geojson ok=186 miss=0
python3 fetch_headers.py    # rows=186 status={200:186}
python3 classify.py         # markets 1550 final mismatch 0; 10 YES; 2000->final 5 flips
python3 fetch_trades.py     # 1550/1550 trade files ok
python3 reproduce.py        # see reproduce.out (strict 6/3, +$658.23; broad 10/7, +$674.71)
python3 verify_fixes.py     # see verify_fixes.out (Gamma fields + capacity arithmetic)
```

Stdout saved as `fetch_outlooks.out`, `fetch_headers.out`, `classify.out`, `fetch_trades.out`, `reproduce.out`, `verify_fixes.out`. Raw data under `_cache/` (gitignored, all files <1 MB).

## Fixes

1. **Review §B22 item 1 — gate 2 over-claimed "满足（数据量）" while admitting only 3–7 independent signals.**
   Changed §门槛自查 #2 to **有条件满足/表述需改写**: data are free, but only 6 events with ≥1 YES, 7 broad / 3 strict low-price signals, 1,550 markets highly correlated, not 30 independent results; only the "forward record from 2026-10-20" alternative applies, gate 6 remains unmet.
   Evidence: `classify.out` (`events with >=1 yes 6 of 62`), `reproduce.out` (`strict ... events=3`, `broad ... events=7`).

2. **Review §B22 item 2 — gate 5 over-claimed "满足（粗算，样本小）" from a 3-day sample.**
   Changed §门槛自查 #5 to **不确定（样本内为正但只有 3 个独立日；不能当粗算够用）**, and added that the strict positive P&L is concentrated on 2026-09-30 (+$623.63 of +$658.23 = 94.7%).
   Evidence: `reproduce.out` `strict max event cost=$9.61; event PnL: 2026-08-26:-6.54, 2026-09-04:+41.14, 2026-09-30:+623.63`; `verify_fixes.out` `strict_2026-09-30_pnl_share=623.63/658.23=0.9474`.

3. **Review §B22 item 3 — capacity line used only the max-day-cost upper bound.**
   Changed §成本与容量: added `$16.93×10≈$169/62 天（约 $2.7/日；严格 $160.30≈$2.6/日）`; clarified `$100/日` is the `$9.61×10` max-day upper bound, not the average. Synced §门槛自查 #3 to the same two numbers.
   Evidence: `verify_fixes.out` `broad_cost_x10=$169.30 over 62d = $2.73/day`, `strict_cost_x10=$160.30 ... $2.59/day`, `max_day_x10=$96.10/day (upper bound, not average)`.

4. **Review §B22 item 4 — event volume 410,598.8.**
   No change; re-verified as 410,598.793553.
   Evidence: `verify_fixes.out` `volume_sum=410598.793553`.

5. **Review §B22 item 5 — 10 YES / 1,540 NO, 6 events with YES, 5 removals.**
   No change; all re-verified.
   Evidence: `classify.out` (`YES rate 10 1550`; `events with >=1 yes 6 of 62`), `reproduce.out` (`inside at 2000=15; survive to final=10 (66.7%)`).

6. **Review §B22 item 6 — keep `status: 草稿`, do not promote to 待核.**
   No change. `status: 草稿` and `date: 2026-10-20` untouched. Entry remains a 待选区 candidate, not this round's 待核.

7. **Review §B22 item 7 / queue note — settlement source and payer must be visibly distinct from other weather entries.**
   Clarified §门槛自查 #4: named the other settlement sources explicitly — dot-001/dot-002 settle on `weather.gov` station hourly temperature, quant-015 on NASA GISTEMP monthly table; this entry settles on SPC Day-1 tornado probability polygons (`spc.noaa.gov`), with the payer being traders pricing off an old outlook or the literal "2%".
   Evidence: dot-001 `:38-39,84`, dot-002 `:37-38,69`, quant-015 `:15,148`; this entry `:46` and `verify_fixes.out` `chicago.resolutionSource=https://www.spc.noaa.gov/products/outlook/day1otlk.html`.

8. **Review §B22 item 8 — `restricted=true` was not per-market confirmed.**
   Re-checked live Gamma: all 1,550 markets across the 62 events have `restricted=true`. Updated §风险 platform bullet to say so and keep "实际交易资格未验证". The claim is now a checked fact, not an assumption.
   Evidence: `verify_fixes.out` `restricted_true=1550/1550`, `restricted_values=['true']`; `chicago.restricted=True`.

## Not changed

- Settlement quotes (`:41-46`), update-flip evidence (`:64-66`), P&L numbers and buffer sensitivity (`:68-76`), data URLs/access dates (`:81-85`, `:124+`), and all non-flagged prose. They re-ran exactly as written.
- No claim was deleted as unverifiable. The only downgrade is gate 2 and gate 5, both from "满足/满足（粗算）" to "有条件/不确定", per review.

---

# Fix2 — re-check fix1 (2026-10-20 UTC)

Source: same review file, “Re-check fix1（B22）” section. Re-ran `fetch_outlooks.py` (62 events / 1,550 markets / 186 GeoJSON, 0 misses), `fetch_headers.py` (final rerun 186/186 HEAD 200; first attempt had one transient timeout on 2026-10-10 2000Z), and new `verify_fix2.py`. Outputs: `fetch_outlooks.out`, `fetch_headers.out`, `verify_fix2.out`. Filename, `id: quant-025`, `date: 2026-10-20` and `status: 草稿` unchanged.

1. **Problem: final-ISSUE range was wrong (00:35–01:02 UTC) at `:48` and repeated at `:106`.**
   Changed both to **00:28–01:37 UTC**; kept GeoJSON `Last-Modified` at 00:35–01:41 UTC.
   Evidence: `verify_fix2.out` — `files_with_issue=62/62`, `ISSUE time-of-day min=00:28 max=01:37`, `LM time-of-day min=00:35:09 max=01:41:04`; `fetch_headers.out` gives 1630Z 16:06–17:03, 2000Z 19:35–20:25, final 00:35–01:41.

2. **Problem: quoted rules were the 2026-08-19 version, but Sept-30+ markets changed the missing-data fallback and revisions wording; entry could be read as applying the Aug-19 “remains open” rule to all events.**
   Added a “版本注” after the verbatim quotes: Aug-19 is the quoted version; Sept-30 live rules say `If the SPC Day 1 Convective Outlook has not been published by the time the market closes, this market will resolve to "No".` and `That scheduled update is the revisions cutoff; subsequent revisions published after it will not be considered.`; forward execution must check each event’s rule version.
   Evidence: `verify_fix2.out` “live Gamma rule text” section, both event slugs and their Chicago market `description`; `resolutionSource` and `feeSchedule` unchanged.

3. **Problem: gate 1 said “满足” and presented the fixed-25-city/thin-market persistence as if structural.**
   Changed to **满足（持续解释弱）**, and now says fixed cities / daily reopening / thin books / slow quotes only make the gap *possible*, not guaranteed; persistence is not independently proven. No gate verdict was upgraded.
   Evidence: entry §门槛自查 #1; no new data claim.

Gate status after fix2: gates 3 (capacity) and 6 (two-week independent results) remain **不满足**; gate 2 remains **有条件满足**; gate 5 remains **不确定**. Entry stays a 待选区 candidate, not `待核`.

---

# Fix3 — re-check fix2 (2026-10-20 UTC)

Source: same review file, “Re-check fix2（B22 / B23）” B22 section. Fresh rebuild from an empty `_cache/`: `fetch_outlooks.py` → 62 events / 1,550 markets / 186 GeoJSON, 0 misses; `fetch_headers.py` → 186/186 HTTP 200; `classify.py` → 0/1,550 settlement mismatches, 10 YES, 6 events with ≥1 YES; `fetch_trades.py` → 1,550/1,550 files, 10,674 trades; `reproduce.py` → strict 6/3 and broad 10/7. The re-run `.out` files are byte-identical to fix2 (same md5), so no cited number moved. Filename, `id: quant-025`, `date: 2026-10-20` and `status: 草稿` unchanged.

1. **Problem: `test_2w` listed only two failure criteria and “严格 BUY YES 3 个” could be read as 3 trades rather than 3 independent event-days.**
   Rewrote the `test_2w` field to `宽口径 10 笔/7 个日事件（严格 6 笔/3 个日事件）` and added the third failure criterion `或前向连续 30 个有信号事件净≤0。`
   Evidence: `reproduce.out` — `strict BUY YES: trades=6 events=3`; `broad price proxy: trades=10 events=7`.

2. **Problem: `:28` said “部分市场只给 1–20¢”, which reads like historical order-book depth; data-api only has executed trades.**
   Changed to `样本成交价低到 1–20¢（不是历史盘口）`.
   Evidence: `verify_fix3.out` — `strict ... yespx_min=0.010 yespx_max=0.200`, `broad ... yespx_min=0.010 yespx_max=0.200`; the data section already states `历史盘口无公开源`.

3. **Problem: gate 2 still said “有条件满足/表述需改写” even though the entry already specifies the forward-record alternative.**
   Changed the verdict to **满足（仅前向记录替代口径）**, keeping the caveat that history has only 6 events with ≥1 YES / 7 broad / 3 strict signals and gate 6 remains unmet.
   Evidence: entry §门槛自查 #2; `classify.out` — `events with >=1 yes 6 of 62`; `reproduce.out` strict/broad event counts.

4. **Problem: queue note requires the settlement source/payer to be visibly distinct from other weather entries.**
   In gate 4, added quant-026 (USDM D4 weekly) alongside dot-001/dot-002 (`weather.gov`) and quant-015 (NASA GISTEMP): B22 settles on SPC Day-1 tornado polygons, quant-026 on USDM state D4 area percentages, with different variables and payers.
   Evidence: `verify_fix3.out` — B22 `resolutionSource=https://www.spc.noaa.gov/products/outlook/day1otlk.html`; quant-026 `resolutionSource=https://droughtmonitor.unl.edu/DmData/DataTables.aspx`.

5. **Problem: gates 3 and 6 are structurally unmet (capacity ~$16 cost, 30 independent signals need 8–9 / 20 months).**
   No text change; both remain **不满足**, as the review requires. `status: 草稿` kept; entry remains a 待选区 candidate, not `待核`.
