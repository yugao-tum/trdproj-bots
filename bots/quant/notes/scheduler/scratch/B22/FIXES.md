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
