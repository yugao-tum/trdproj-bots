"""Operator-written deterministic regression checks; local inputs only, no writes."""
import csv
import unittest
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

import sensitivity as s


class HandComputedHodlTests(unittest.TestCase):
    def test_hand_computed_round_trips_and_no_rebalance(self):
        dates = [date(2024, 12, 30) + timedelta(days=i) for i in range(5)]
        for label, ends, expected in [
            ("SOL_HODL", {"BTCUSDT": 120, "ETHUSDT": 80, "SOLUSDT": 120}, {0.003: 5212.74, 0.006: 5205.48}),
            ("EW_HODL", {"BTCUSDT": 120, "ETHUSDT": 80, "SOLUSDT": 100}, {0.003: 4993.40, 0.006: 4986.80}),
        ]:
            bars = {}
            for symbol in s.SYMBOLS:
                prices = [100, 150, 75, 200, ends[symbol]]
                bars[symbol] = [s.Bar(d, p, p, p, p) for d, p in zip(dates, prices)]
            for rate, terminal_nav in expected.items():
                with self.subTest(label=label, rate=rate):
                    out = s.simulate_benchmark(label, bars, dates, rate, start=dates[0], end=dates[-1])
                    self.assertAlmostEqual(out['daily'][-1]['total_equity'], terminal_nav, places=8)
                    self.assertEqual(len(out['trades']), 2 if label == 'SOL_HODL' else 6)
                    self.assertTrue(all(t.day in (dates[0], dates[-1]) for t in out['trades']))
                    self.assertTrue(all(t.day != date(2025, 1, 1) for t in out['trades']))
                    carry, nav = s.oos_start_snapshot(out['daily'])
                    self.assertEqual(nav, out['daily'][1]['total_equity'])
                    self.assertGreater(carry['holdings_close'], 0)


class FrozenHalfScaleRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        s.verify_inputs(s.DEFAULT_CSV)
        cls.bars, cls.dates, _ = s.frozen.load_and_precheck(s.DEFAULT_CSV)
        root = s.REFERENCE_ORIGINAL_DIR
        cls.old_daily, cls.old_trades = defaultdict(list), defaultdict(list)
        with (root/'daily_equity.csv').open() as f:
            for row in csv.DictReader(f): cls.old_daily[(row['strategy'], row['cost_rate'])].append(row)
        with (root/'trades.csv').open() as f:
            for row in csv.DictReader(f): cls.old_trades[(row['strategy'], row['cost_rate'])].append(row)

    def test_all_four_rules_both_costs_exact_half_cashflow(self):
        for variant in s.MECHANISMS:
            for rate in s.COST_RATES:
                with self.subTest(variant=variant, rate=rate):
                    out = s.simulate_mechanism(variant, self.bars, self.dates, rate)
                    key = (variant, f'{rate:.3f}')
                    old = self.old_daily[key]
                    self.assertEqual(len(out['daily']), len(old))
                    for row, ref in zip(out['daily'], old):
                        self.assertEqual(str(row['date']), ref['date'])
                        for field in ['cash', 'holdings_close', 'on_exchange_open_pretrade_mark', 'on_exchange_close_mark', 'on_exchange_high_upper_bound', 'final_exit_fee']:
                            self.assertAlmostEqual(row[field], 0.5*float(ref[field]), places=7)
                        self.assertAlmostEqual(row['total_equity'], 5000+0.5*(float(ref['total_equity'])-5000), places=7)
                    self.assertEqual(len(out['trades']), len(self.old_trades[key]))
                    for trade, ref in zip(out['trades'], self.old_trades[key]):
                        self.assertEqual(str(trade.day), ref['date'])
                        self.assertEqual(trade.side, ref['side'])
                        self.assertEqual(trade.symbol, ref['symbol'])
                        self.assertAlmostEqual(trade.price, float(ref['price']), places=8)
                        for field in ['qty', 'notional', 'fee', 'cash_after', 'qty_after']:
                            self.assertAlmostEqual(getattr(trade, field), 0.5*float(ref[field]), places=7)


if __name__ == '__main__':
    unittest.main()
