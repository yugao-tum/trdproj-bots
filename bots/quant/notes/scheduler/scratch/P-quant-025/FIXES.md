# P-quant-025 / quant-025 — fixer changelog

Date: 2026-10-21 (UTC). Target: `bots/quant/entries/quant-025-spc-tornado-outlook-lag.md`.
Filename, `id: quant-025`, `date: 2026-10-20` and `status: 草稿` unchanged. No other repository file touched.

Files read for this fix:
- `bots/quant/notes/scheduler/reviews/c20261020-1423-research.md` (B22 section and both re-checks)
- `bots/quant/notes/scheduler/checks/B22.md` (all sections; B22 = quant-025)
- `bots/quant/notes/scheduler/checks/B23.md` (only mentions quant-025 as a different mechanism; no action)
- `bots/quant/notes/scheduler/audit/c20261021-030001-research.md` (S6, S10, table row)
- `bots/quant/notes/scheduler/queue.tsv` (P-quant-025 note)

All scripts and stdout are under this directory. `_cache/` is gitignored and every file is < 1 MB.

## Re-run (from an empty cache)

```bash
python3 fetch_outlooks.py     # events 63 / markets 1575 (2026-10-21 live); then filter to entry sample
python3 filter_62.py          # kept 62 events, 2026-08-19..2026-10-19, 1550 markets
python3 fetch_headers.py      # rows 186, status {200: 186}
python3 classify.py           # markets 1550, final mismatch 0, 10 YES / 1540 NO, 6 events with >=1 YES
python3 fetch_trades.py       # 1550/1550 markets, 10,674 trades
python3 reproduce.py          # strict 6/3, cost $16.03, net +$658.23; broad 10/7, cost $16.93, net +$674.71
python3 verify_sources.py     # all 10 cited URLs HTTP 200; sizes / ranges / capacity arithmetic
python3 verify_rules.py       # Aug-19 and Sep-30 live rule text
python3 verify_trades.py      # Wichita / Columbus trades cited in the entry
```

The fresh run matches the entry: 62 events / 1,550 markets / 10,674 trades / 0 settlement mismatches / 10 YES / 6 events with YES / 1630→2000 0 flips / 2000→final 5 flips / 15→10 (66.7%). Strict and broad P&L match the numbers in `scratch/B22/reproduce.out`.

## Problems -> changes -> evidence

1. **Rule 4 entry text contradicted the script** (checks/B22 §7.1; audit S6).
   Old: “第一笔 `BUY Yes` ... 若第一笔不是 `BUY Yes` 或价格 >0.25，则跳过” — read literally, a preceding `SELL Yes`/`BUY No` blocks entry, which would drop Indianapolis 8/26 and Wichita 9/30 and change strict to 4 trades / +$646.55.
   Changed to: “窗口内第一笔 `BUY Yes` 成交（之前的 `SELL Yes`/`BUY No` 不计），价格 ≤0.25；若窗口内没有 `BUY Yes` 或该笔价格 >0.25，则跳过”。 This matches the 6-trade script.
   Evidence: `reproduce.out` (`strict BUY YES: trades=6 events=3 ... net=$658.23`); the 6 strict fills include Wichita 16:50:35 `BUY Yes` and Indianapolis 20:46:03 `BUY Yes` after earlier opposite-side trades.

2. **Risk size range was wrong** (checks/B22 §7.2).
   The check saw “5–185 份”; the checked-out file had already been partly changed to “单笔 20–300 份”, which still missed the broad minimum (4.99).
   Changed to: “单笔 5–300 份（宽口径最小 4.99、最大 300；严格 20.01–300）”.
   Evidence: `verify_sources.out` — strict size min/max 20.01/300; broad size min/max 4.99478/300.

3. **Gate 3 was mis-classified as “不满足”** (audit S10).
   GUIDE §2 gate 3 asks whether ~5,000 USDT can do it (per venue ≤~2,500) and whether capacity is written down, not whether 5,000 can be fully deployed. The entry already caps $50/market, $250/day, $2,500/venue.
   Changed gate 3 to **“满足（容量很小）”**, with the $16/$17 full-sample and ~$2.6–2.7/day (10×) numbers kept as capacity caveats. Moved the economic-capacity point into “成本与容量” and gate 5, and clarified that it is an economic-capacity flaw, not a small-capital threshold failure.
   Evidence: `verify_sources.out` capacity arithmetic (`16.93×10/62 = $2.73/day`; `16.03×10/62 = $2.59/day`; `9.61×10 = $96.10` max-day upper bound); GUIDE.md §2 gate 3.
   Note: checks/B22 still said gate 3 “不满足”; the later audit (2026-10-21 03:00) explicitly identifies that as a misjudgment and prescribes this wording. The later audit is followed here.

4. **One “verbatim” settlement quote was not verbatim** (found by this re-fetch).
   Old: “If **a** city's coordinates fall inside ...”.
   Live Aug-19 Chicago rule: “If **the** city's coordinates fall inside ...”.
   Changed one word to “the”. This is the only quote mismatch; the other five quoted sentences are exact.
   Evidence: `verify_rules.out` — with the corrected wording the sentence is `QUOTE_PRESENT` on the Aug-19 market, and the old “a city's” variant is `OLD_A_VARIANT_ABSENT`; the other five Aug-19 quotes are `QUOTE_PRESENT`.

5. **Queue asked for a historical tradable-price backtest net of fees.**
   The backtest already existed and is reproducible. Added an explicit label at the top of “证据” saying it is an executed-fill (tradable-price) replay using data-api trades, net of 0.05 taker fee + 1¢/share buffer, and that it does not prove we could get the same price/size.
   Evidence: `reproduce.out`; `verify_trades.out` (Wichita 16:33:41 SELL Yes 0.05×38 and 16:50:35 BUY Yes 0.08×20.1; Columbus 16:57:25 BUY Yes 0.01×42).

6. **Sources re-verified, and the sample snapshot has moved.**
   All 10 cited URLs returned HTTP 200 on 2026-10-21; SPC values match (1630 updated 16:26:43 UTC, 2000 19:58:05, final 00:35:04; 1630 zip Last-Modified 16:30:16; Sep-30 volume 4,935.376533; fee 0.05/takerOnly/rebateRate 0.25).
   Live Gamma now has **63** closed events (2026-10-20 added). The entry sample is kept at the verified 62 events (2026-08-19..2026-10-19); added a dated snapshot note so a future checker does not read 63 as a mismatch.
   Evidence: `verify_sources.out`; `verify_numbers.out` (62 events × 25 markets, volume sum 410,598.793553, 1,550/1,550 `restricted=true`, 1,550/1,550 fee rate 0.05); `issue_range.out` (62 sample final files: ISSUE 00:28–01:37 UTC, Last-Modified 00:35–01:41 UTC).

7. **Verdict written plainly in the entry.**
   Added “本轮结论：不应丢弃” — keep as a 待选区 candidate, not a this-round `待核` promotion. It is not dropped because the mechanism, free data and sources hold; it cannot be promoted because gate 6 is structurally unmet (3–7 independent low-price signals) and gate 5 is uncertain (one day = 94.7% of strict PnL, capacity ~$17/62 days).

## Gate verdict after fix

| Gate | Verdict | Reason |
|---|---|---|
| 1 mechanism | 满足（持续解释弱） | SPC 2% geographic area vs literal 2%; payer clear; persistence only weakly explained |
| 2 data | 满足（仅前向记录替代口径） | free keyless data; history has only 6 events with YES / 7 broad / 3 strict signals |
| 3 small capital | 满足（容量很小） | $50/market, $250/day, $2,500/venue fit; economic capacity ~$17/62 days |
| 4 not duplicate | 满足 | SPC polygons vs site temperature / GISTEMP / USDM; different payer |
| 5 net of cost | 不确定 | in-sample +$658.23 strict / +$674.71 broad, but 3 event-days, 9/30 = 94.7%, fill-price proxy |
| 6 two-week test | **不满足** | 1–2 signals per two weeks; 30 independent signals need ~8–9 (broad) / ~20 (strict) months |
| 7 sources | 满足 | all 10 URLs HTTP 200, rules/scripts re-runnable, ISSUE range correct |

## Open problems

- Gate 6 is structural; no text fix can create 30 independent events in two weeks.
- Gate 5 remains uncertain: the positive P&L is one event-day and uses executed fills, not order-book depth.
- Capacity (~$17 over 62 days) is an economic flaw; it does not block gate 3 but makes the strategy undeployable at 5,000 USDT.
- Recommendation: keep as 待选区候选 (草稿), do not promote this round and do not drop.
