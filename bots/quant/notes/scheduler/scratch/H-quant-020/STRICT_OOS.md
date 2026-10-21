# quant-020 strict pre-selection OOS (H-quant-020, 2026-10-21)

Question: the `q020-oos` holdout was cut by time (60/40), but the 0.40-0.55
band was chosen from the **latest 250 closed events as of 2026-10-20**.  Does
the observed-ask-fill edge survive after removing that selection window?

## Inputs (all already frozen, no new network calls)

- `bots/quant/notes/q020-oos/events.csv` (1384 deduped closed events, 2026-10-20 snapshot).
- `bots/quant/notes/scheduler/scratch/H-quant-020/tradable_fills.csv` (101 in-band events, 97 with an observed ask-side print).  A live data-api spot-check of 3 events (`spotcheck_fills.out`) reproduces the last ask print exactly.
- Band and entry rule are unchanged: `0.40 <= p24 <= 0.55`, buy YES, last ask-side data-api print in `[endDate-72h, endDate-24h]`, fee `0.05 * ask * (1-ask)`.

## Selection-window proxy

- Take the 250 newest `endDate` rows of `events.csv`; cutoff = `2026-07-30T13:00Z`.
- `STRICT_OOS` = in-band observed fills with `endDate < cutoff`, n=68.
- `SELECTION` = in-band observed fills with `endDate >= cutoff`, n=29.
- Old 60/40 holdout: 43 observed fills; **29** are inside the selection window, only 14 are before it.  Old-price holdout (47 events): **32** inside.

## Results (fee 0.05, weekly block bootstrap 10,000 draws, seed 20261020)

| group | n | YES rate | mean ask | median net/share | mean net/share | per $ | 95% CI |
|---|---:|---:|---:|---:|---:|---:|---:|
| STRICT_OOS | 68 | 0.4706 | 0.5221 | -0.4120 | **-0.0634** | **-12.14%** | [-0.1638, +0.0366] |
| SELECTION | 29 | 0.6207 | 0.5067 | +0.4476 | **+0.1017** | **+20.08%** | [-0.1822, +0.2824] |

- Fee 0.04: strict mean -0.0610 (-11.68%/$, CI [-0.1615,+0.0390]).
- Fee 0.00: strict mean -0.0515 (-9.86%/$, CI [-0.1520,+0.0486]).
- Original CLOB band flag (`in_band_old`): strict n=42, mean -0.0503 (-9.78%/$, median -0.4322); selection n=20, mean +0.1376.
- `q020-oos` +1c assumption instead of observed ask: strict n=68, mean -0.0237 (-4.92%/$).
- Cutoff sensitivity (observed ask, fee 0.05): pre-2026-06-01 n=60 mean -0.0715; pre-2026-07-01 n=62 mean -0.0741; pre-2026-08-01 n=69 mean -0.0552.

## Verdict

Negative.  The positive holdout result sits mostly inside the window used to
choose the band.  Once that window is removed, both mean and median net P&L
per share are negative, and fee=0 does not turn them positive.  Recommend
demotion to 待选区 (or drop under gate 5); do not treat the old "HOLDOUT PASS"
as clean out-of-sample evidence.

## Limitations

- The 250-event cutoff is a proxy: the original 247 sample used the 1378-event
  snapshot, this script uses the 1384-event q020-oos snapshot.  Cutoff
  sensitivity above covers the boundary uncertainty.
- Ask-side prints are not full L2 depth; `side` is interpreted as taker side.
- Outcomes are Polymarket `outcomePrices`; SeekingAlpha strike/report values
  were not independently fetched (paywall).

## Reproduce

```bash
python3 bots/quant/notes/scheduler/scratch/H-quant-020/strict_oos.py \
  | tee bots/quant/notes/scheduler/scratch/H-quant-020/strict_oos.out
```
