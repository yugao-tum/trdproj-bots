# r16 native02: Frozen VM signals and original formula

Supplement to quant-001 / T-T2-vm, not a new mechanism. No parameter search or best-control selection. VM_base and VM_BTC_SMA50 are primary; SMA100/200 are fixed original controls only. No SAR selection.

## Shared interface
`signals.csv` is long by (fold_id, date_utc, variant), wide by asset. `weights.csv` is a smaller projection of identical weights. All original files remain untouched. Local daily output is not intended for publication: signals.csv and original_returns.csv exceed 1 MB and must remain local. Publish reproduction code, hashes, schema and aggregate metrics only.

- date_utc: UTC daily bar open label t, with price only observable at the end of that UTC day. Row t earns close[t-1] to close[t]. These are target weights already lagged; do not lag again.
- BTC_weight / ETH_weight / SOL_weight: final base times lagged daily gate.
- base_BTC_weight / base_ETH_weight / base_SOL_weight: lagged five-day frozen VM weights before gate.
- gate_lagged: 1/0 from BTC close[t-1] versus its SMA as of t-1. For base always 1. A daily gate is NOT five-day frozen.
- base_rebalance_day: EFFECTIVE return day, not information/signal day. True on row offsets 1, 6, 11... from each fold-specific warm-up start. Information/decision was at prior close. Base can remain numerically unchanged on an update day.
- is_test: false on exactly 250 warm-up rows per fold; true on test days. Warmup rows overlap between independently recomputed folds and must never be double-counted in test evaluation.
- *_asset_return: original same-row close-to-close returns, first warm-up row zero.
- gross_return: sum(weight * asset_return).
- original_turnover: sum(abs(weight[t]-weight[t-1])); first row zero due original pandas row sum behavior and initial zero weights.

Full information cutoff is prior-day close, with VM momentum additionally internally shifted by one row before final lag. Weekly volatility is four W-FRI sums, annualized sqrt(52), shifted one weekly bucket then forward filled. This reproduces the original, without changing weekly sum approximation to compounding or annualization. Five-day phase anchors at the original fold warm-up start. Trading at that exact cutoff close is an idealized execution assumption, not next-open execution proof.

## Coverage
Frozen input a3b601644697f778990fcfdcc2ff1143140d5373c33d871ff81536d493891f79: 2023-01-01..2026-09-30, 1369 daily rows, BTC/ETH/SOL. Original fold1 unavailable due missing 250-day warmup; do not shift its start to manufacture coverage. Fold2 warmup 2023-04-25, test 2023-12-31..2024-12-29 (365 days). Fold3 warmup 2024-04-24, test 2024-12-30..2025-12-29 (365). Fold4 warmup 2025-04-24, test 2025-12-30..2026-09-30 (275), truncated versus opponent's 2026-10-13 endpoint. No claim of reproducing four-fold marketing totals.

## Reproduction and accounting limits
Independent implementation matches audited original freeze/vm_weights/apply computations exactly on these data. Reference check extracts only those three computational functions via AST; no downloader, module top-level code, main program or external process is executed. All weights are nonnegative and sum at most one.

original_returns.csv supplies original gross/turnover/net and test_nav (reset to unit NAV before each fold). Fees 0.001 and 0.003 per side reproduce opponent settings; 0.006 is a separately labeled stress extension. Original drawdown excludes the initial unit NAV, intentionally preserved in metric label. No forced terminal liquidation is added to original formula. This is constant-target weighted-return arithmetic, NOT a conserved shares/cash ledger; unchanged target weights can hide required drift rebalancing. Native03 and native04 must evaluate their different accounting definitions independently using this SAME frozen signals file.

Classification: historical-data signal/formula reproduction with conditional same-close execution assumptions; not verified correct-accounting tradable backtest, not competition-qualified, not scored. Gate transitions / rebalance days are not automatically independent return mechanisms or qualifying independent events.
