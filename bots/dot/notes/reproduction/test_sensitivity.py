import unittest
from datetime import date, timedelta
from pathlib import Path

import sensitivity as s


def make_bars():
    start = date(2024, 1, 1)
    dates = [start + timedelta(days=offset) for offset in range(10)]
    prices = {
        "BTCUSDT": [100.0, 110.0, 120.0, 130.0, 140.0, 150.0, 160.0, 170.0, 180.0, 200.0],
        "ETHUSDT": [50.0, 48.0, 46.0, 44.0, 42.0, 40.0, 38.0, 36.0, 34.0, 25.0],
        "SOLUSDT": [20.0, 19.0, 18.0, 17.0, 16.0, 15.0, 14.0, 13.0, 12.0, 10.0],
    }
    bars = {}
    for symbol, closes in prices.items():
        bars[symbol] = [
            s.Bar(day=day, open=price, high=price * 1.01, low=price * 0.99, close=price)
            for day, price in zip(dates, closes)
        ]
    return bars, dates


class ConstantTests(unittest.TestCase):
    def test_preregistered_constants(self):
        self.assertEqual(s.CAPITAL_USDT, 5000.0)
        self.assertEqual(s.VENUE_START_USDT, 1250.0)
        self.assertEqual(s.OFF_EXCHANGE_CASH_USDT, 3750.0)
        self.assertEqual(s.POSITION_CAP_USDT, 1100.0)
        self.assertEqual(s.TARGET_FRACTION, 0.9)
        self.assertEqual(s.STUDY_DIAGNOSTIC_LIMIT_USDT, 2500.0)
        self.assertEqual(s.COST_RATES, (0.003, 0.006))
        self.assertEqual(s.VENUE_START_USDT + s.OFF_EXCHANGE_CASH_USDT, s.CAPITAL_USDT)
        self.assertLess(s.POSITION_CAP_USDT, s.VENUE_START_USDT)
        self.assertLess(s.VENUE_START_USDT, s.STUDY_DIAGNOSTIC_LIMIT_USDT)

    def test_benchmark_pairing(self):
        self.assertEqual(s.BENCHMARK_PAIR["C21"], "SOL_HODL")
        self.assertEqual(s.BENCHMARK_PAIR["C23"], "SOL_HODL")
        self.assertEqual(s.BENCHMARK_PAIR["C22"], "EW_HODL")
        self.assertEqual(s.BENCHMARK_PAIR["C24"], "EW_HODL")
        self.assertIsNone(s.BENCHMARK_PAIR["SOL_HODL"])
        self.assertIsNone(s.BENCHMARK_PAIR["EW_HODL"])


class HalfCapFeeTests(unittest.TestCase):
    def test_half_cap_buy_fee_budget(self):
        portfolio = s.HalfCapPortfolio(cost_rate=0.003, cash=1250.0)
        portfolio.rebalance(date(2024, 1, 1), {"SOLUSDT": 100.0}, ["SOLUSDT"], "test")
        self.assertAlmostEqual(portfolio.qty["SOLUSDT"], 11.0)
        self.assertAlmostEqual(portfolio.trades[0].notional, 1100.0)
        self.assertAlmostEqual(portfolio.trades[0].fee, 3.3)
        self.assertAlmostEqual(portfolio.cash, 146.7)
        self.assertEqual(portfolio.buy_shrunk, 0)
        self.assertFalse(portfolio.negative_cash_seen)
        self.assertFalse(portfolio.negative_qty_seen)

    def test_high_cost_still_fits_initial_budget(self):
        portfolio = s.HalfCapPortfolio(cost_rate=0.006, cash=1250.0)
        portfolio.rebalance(date(2024, 1, 1), {"SOLUSDT": 100.0}, ["SOLUSDT"], "test")
        self.assertAlmostEqual(portfolio.trades[0].notional, 1100.0)
        self.assertAlmostEqual(portfolio.trades[0].fee, 6.6)
        self.assertAlmostEqual(portfolio.cash, 143.4)
        self.assertEqual(portfolio.buy_shrunk, 0)

    def test_final_liquidation_charges_exit_fee(self):
        portfolio = s.HalfCapPortfolio(cost_rate=0.003, cash=1250.0)
        prices = {"SOLUSDT": 100.0}
        portfolio.rebalance(date(2024, 1, 1), prices, ["SOLUSDT"], "buy")
        before_exit = portfolio.cash + portfolio.qty["SOLUSDT"] * 100.0
        portfolio.liquidate(date(2024, 1, 2), prices, "final close liquidation")
        exit_fee = portfolio.trades[-1].fee
        self.assertAlmostEqual(exit_fee, 3.3)
        self.assertAlmostEqual(portfolio.cash, before_exit - exit_fee)
        self.assertEqual(portfolio.qty["SOLUSDT"], 0.0)


class DiagnosticThresholdTests(unittest.TestCase):
    def test_guide_threshold_stays_2500(self):
        portfolio = s.HalfCapPortfolio(cost_rate=0.003, cash=0.0)
        portfolio.qty["SOLUSDT"] = 30.0
        marks = s.capital_marks(
            portfolio,
            {"SOLUSDT": 100.0},
            {"SOLUSDT": 100.0},
            {"SOLUSDT": 100.0},
        )
        self.assertEqual(marks["study_strict_diagnostic_limit_usdt"], 2500.0)
        self.assertTrue(marks["confirmed_close_breach"])
        self.assertTrue(marks["confirmed_open_breach"])
        portfolio.qty["SOLUSDT"] = 24.0
        marks = s.capital_marks(
            portfolio,
            {"SOLUSDT": 100.0},
            {"SOLUSDT": 100.0},
            {"SOLUSDT": 100.0},
        )
        self.assertFalse(marks["confirmed_close_breach"])
        self.assertGreater(marks["close_mark"], s.VENUE_START_USDT)

    def test_exactly_2500_is_not_breach(self):
        portfolio = s.HalfCapPortfolio(cost_rate=0.003, cash=0.0)
        portfolio.qty["SOLUSDT"] = 25.0
        marks = s.capital_marks(
            portfolio,
            {"SOLUSDT": 100.0},
            {"SOLUSDT": 100.0},
            {"SOLUSDT": 100.0},
        )
        self.assertEqual(marks["close_mark"], 2500.0)
        self.assertFalse(marks["confirmed_close_breach"])


class BenchmarkTests(unittest.TestCase):
    def test_ew_hodl_initial_buy_and_no_rebalance(self):
        bars, dates = make_bars()
        simulation = s.simulate_benchmark(
            "EW_HODL",
            bars,
            dates,
            0.003,
            start=dates[0],
            end=dates[-1],
        )
        trades = simulation["trades"]
        buys = [trade for trade in trades if trade.side == "BUY"]
        sells = [trade for trade in trades if trade.side == "SELL"]
        self.assertEqual(len(trades), 6)
        self.assertEqual(len(buys), 3)
        self.assertEqual(len(sells), 3)
        self.assertTrue(all(trade.day == dates[0] for trade in buys))
        self.assertTrue(all(trade.day == dates[-1] for trade in sells))
        self.assertAlmostEqual(sum(trade.notional for trade in buys), 1100.0, places=6)
        self.assertAlmostEqual(sum(trade.fee for trade in buys), 3.3, places=6)
        self.assertAlmostEqual(buys[-1].cash_after, 146.7, places=6)
        self.assertEqual(simulation["daily"][-1]["holdings_close"], 0.0)
        self.assertGreater(simulation["daily"][-1]["final_exit_fee"], 0.0)

    def test_sol_hodl_initial_buy_and_no_rebalance(self):
        bars, dates = make_bars()
        simulation = s.simulate_benchmark(
            "SOL_HODL",
            bars,
            dates,
            0.003,
            start=dates[0],
            end=dates[-1],
        )
        trades = simulation["trades"]
        self.assertEqual(len(trades), 2)
        self.assertEqual(trades[0].side, "BUY")
        self.assertEqual(trades[1].side, "SELL")
        self.assertAlmostEqual(trades[0].notional, 1100.0)
        self.assertAlmostEqual(trades[0].fee, 3.3)
        self.assertAlmostEqual(trades[1].qty, trades[0].qty)
        self.assertEqual(simulation["daily"][-1]["holdings_close"], 0.0)

    def test_benchmark_daily_equity_identity(self):
        bars, dates = make_bars()
        for label in s.BENCHMARKS:
            simulation = s.simulate_benchmark(
                label,
                bars,
                dates,
                0.006,
                start=dates[0],
                end=dates[-1],
            )
            for row in simulation["daily"]:
                expected = row["cash"] + row["holdings_close"] + s.OFF_EXCHANGE_CASH_USDT
                self.assertAlmostEqual(row["total_equity"], expected, places=8)
            self.assertFalse(simulation["negative_cash_seen"])
            self.assertFalse(simulation["negative_qty_seen"])

    def test_benchmark_final_exit_fee_matches_trades(self):
        bars, dates = make_bars()
        simulation = s.simulate_benchmark(
            "EW_HODL",
            bars,
            dates,
            0.003,
            start=dates[0],
            end=dates[-1],
        )
        expected = sum(
            trade.fee
            for trade in simulation["trades"]
            if trade.day == dates[-1] and trade.reason == "final close liquidation"
        )
        self.assertAlmostEqual(simulation["daily"][-1]["final_exit_fee"], expected)
        self.assertEqual(simulation["daily"][-1]["holdings_close"], 0.0)


class MechanismTests(unittest.TestCase):
    def test_c24_rebalances_and_liquidates(self):
        bars, dates = make_bars()
        simulation = s.simulate_mechanism(
            "C24",
            bars,
            dates,
            0.003,
            start=dates[0],
            end=dates[-1],
        )
        self.assertGreater(len(simulation["trades"]), 6)
        self.assertEqual(simulation["daily"][0]["on_exchange_open_pretrade_mark"], 1250.0)
        self.assertEqual(simulation["daily"][-1]["holdings_close"], 0.0)
        self.assertFalse(simulation["negative_cash_seen"])
        self.assertFalse(simulation["negative_qty_seen"])
        for row in simulation["daily"]:
            expected = row["cash"] + row["holdings_close"] + s.OFF_EXCHANGE_CASH_USDT
            self.assertAlmostEqual(row["total_equity"], expected, places=8)


class OosTests(unittest.TestCase):
    def test_oos_start_preserves_prior_equity_and_positions(self):
        daily = [
            {
                "date": date(2024, 12, 30),
                "cash": 1000.0,
                "holdings_close": 1500.0,
                "on_exchange_close_mark": 2500.0,
                "on_exchange_close_after_final_exit": 2500.0,
                "off_exchange_cash": 3750.0,
                "total_equity": 6250.0,
            },
            {
                "date": date(2024, 12, 31),
                "cash": 900.0,
                "holdings_close": 1800.0,
                "on_exchange_close_mark": 2700.0,
                "on_exchange_close_after_final_exit": 2700.0,
                "off_exchange_cash": 3750.0,
                "total_equity": 6450.0,
            },
            {
                "date": date(2025, 1, 1),
                "cash": 900.0,
                "holdings_close": 1700.0,
                "on_exchange_close_mark": 2600.0,
                "on_exchange_close_after_final_exit": 2600.0,
                "off_exchange_cash": 3750.0,
                "total_equity": 6350.0,
            },
        ]
        state, base_equity = s.oos_start_snapshot(daily, date(2025, 1, 1))
        self.assertEqual(base_equity, 6450.0)
        self.assertNotEqual(base_equity, 5000.0)
        self.assertEqual(state["cash"], 900.0)
        self.assertEqual(state["holdings_close"], 1800.0)
        self.assertEqual(state["total_equity"], 6450.0)


class LookaheadTests(unittest.TestCase):
    def test_c21_uses_previous_close_not_current_close(self):
        prior = [100.0] * 199 + [99.0]
        self.assertFalse(s.frozen.c21_signal(prior + [1.0], 200))
        self.assertFalse(s.frozen.c21_signal(prior + [10000.0], 200))

    def test_c22_momentum_ignores_current_close(self):
        closes = [100.0] * 61 + [1.0]
        self.assertAlmostEqual(s.frozen.c22_momentum(closes, 61), 0.0)


class FixtureAndSafetyTests(unittest.TestCase):
    def test_static_csv_fixture(self):
        path = Path(__file__).resolve().parent / "fixtures" / "mini_spot_daily.csv"
        bars, dates, quality = s.frozen.load_and_precheck(
            path,
            expected_start=date(2024, 1, 1),
            expected_end=date(2024, 1, 3),
            require_warmup=False,
        )
        self.assertEqual(len(dates), 3)
        self.assertEqual(quality["rows_read"], 9)
        self.assertTrue(quality["aligned"])
        self.assertEqual(quality["errors"], [])
        self.assertEqual(quality["symbols"]["BTCUSDT"]["rows"], 3)
        self.assertEqual(bars["SOLUSDT"][0].close, 20.0)

    def test_output_path_is_contained(self):
        self.assertTrue(s.OUT_DIR.resolve().is_relative_to(s.WORKDIR.resolve()))
        self.assertNotEqual(s.OUT_DIR.resolve(), s.WORKDIR.resolve())
        self.assertIn("results", s.OUT_DIR.parts)

    def test_no_forbidden_source_tokens(self):
        source = Path(s.__file__).read_text(encoding="utf-8")
        forbidden = (
            "import requests",
            "import urllib",
            "import socket",
            "import subprocess",
            "os.system",
            "eval(",
            "exec(",
            "pickle",
            "http://",
            "https://",
        )
        for token in forbidden:
            self.assertNotIn(token, source)


if __name__ == "__main__":
    unittest.main()
