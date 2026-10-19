import calendar
import csv
import os
import tempfile
import unittest
from datetime import date, datetime, timedelta, timezone

from spot_screen import (
    DataError,
    Portfolio,
    REQUIRED_FIELDS,
    SYMBOLS,
    c21_signal,
    c22_momentum,
    load_and_precheck,
    oos_start_snapshot,
)


def fixture_row(symbol, day, **overrides):
    open_dt = datetime(day.year, day.month, day.day, tzinfo=timezone.utc)
    close_dt = open_dt + timedelta(hours=23, minutes=59, seconds=59, milliseconds=999)
    open_raw = calendar.timegm(open_dt.utctimetuple())
    close_raw = calendar.timegm(close_dt.utctimetuple()) * 1000 + close_dt.microsecond // 1000
    row = {
        "symbol": symbol,
        "open_time_utc": open_dt.isoformat().replace("+00:00", "Z"),
        "open_time_raw": str(open_raw),
        "open": "100",
        "high": "101",
        "low": "99",
        "close": "100",
        "volume": "10",
        "close_time_utc": close_dt.isoformat(timespec="milliseconds").replace("+00:00", "Z"),
        "close_time_raw": str(close_raw),
        "quote_volume": "1000",
        "count": "5",
        "taker_buy_volume": "4",
        "taker_buy_quote_volume": "400",
        "ignore": "0",
    }
    row.update(overrides)
    return row


def write_fixture(path, days, skipped=(), overrides=None):
    overrides = overrides or {}
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=REQUIRED_FIELDS)
        writer.writeheader()
        for day in days:
            for symbol in SYMBOLS:
                if (day, symbol) in skipped:
                    continue
                writer.writerow(fixture_row(symbol, day, **overrides.get((day, symbol), {})))


class LookaheadTests(unittest.TestCase):
    def test_c21_uses_previous_close_not_current_close(self):
        prior = [100.0] * 199 + [99.0]
        self.assertFalse(c21_signal(prior + [1.0], 200))
        self.assertFalse(c21_signal(prior + [10000.0], 200))

    def test_c22_momentum_ignores_current_close(self):
        closes = [100.0] * 61 + [1.0]
        self.assertAlmostEqual(c22_momentum(closes, 61), 0.0)


class FeeBudgetTests(unittest.TestCase):
    def test_flat_round_trip_loss_equals_two_fees(self):
        portfolio = Portfolio(cost_rate=0.003)
        prices = {"SOLUSDT": 100.0}
        portfolio.rebalance(date(2024, 1, 1), prices, ["SOLUSDT"], "buy")
        portfolio.liquidate(date(2024, 1, 2), prices, "final close liquidation")
        self.assertAlmostEqual(2500.0 - portfolio.cash, 13.2)
        self.assertAlmostEqual(sum(trade.fee for trade in portfolio.trades), 13.2)

    def test_final_liquidation_charges_exit_fee(self):
        portfolio = Portfolio(cost_rate=0.003)
        prices = {"SOLUSDT": 100.0}
        portfolio.rebalance(date(2024, 1, 1), prices, ["SOLUSDT"], "buy")
        before_exit = portfolio.cash + portfolio.qty["SOLUSDT"] * 100.0
        portfolio.liquidate(date(2024, 1, 2), prices, "final close liquidation")
        exit_fee = portfolio.trades[-1].fee
        self.assertAlmostEqual(exit_fee, 6.6)
        self.assertAlmostEqual(portfolio.cash, before_exit - exit_fee)
        self.assertEqual(portfolio.qty["SOLUSDT"], 0.0)

    def test_buy_fee_is_deducted_from_cash(self):
        portfolio = Portfolio(cost_rate=0.003)
        portfolio.rebalance(
            date(2024, 1, 1),
            {"SOLUSDT": 100.0},
            ["SOLUSDT"],
            "test",
        )
        self.assertAlmostEqual(portfolio.qty["SOLUSDT"], 22.0)
        self.assertAlmostEqual(portfolio.trades[0].notional, 2200.0)
        self.assertAlmostEqual(portfolio.trades[0].fee, 6.6)
        self.assertAlmostEqual(portfolio.cash, 293.4)
        self.assertFalse(portfolio.negative_cash_seen)

    def test_buy_is_shrunk_when_fee_budget_is_short(self):
        portfolio = Portfolio(cost_rate=0.5)
        portfolio.rebalance(
            date(2024, 1, 1),
            {"SOLUSDT": 100.0},
            ["SOLUSDT"],
            "test",
        )
        self.assertEqual(portfolio.buy_shrunk, 1)
        self.assertAlmostEqual(portfolio.cash, 0.0)
        self.assertLessEqual(portfolio.qty["SOLUSDT"] * 100.0 * 1.5, 2500.0 + 1e-6)


class OosContinuationTests(unittest.TestCase):
    def test_oos_start_preserves_prior_equity_and_positions(self):
        daily = [
            {
                "date": date(2024, 12, 30),
                "cash": 1000.0,
                "holdings_close": 1500.0,
                "on_exchange_close_mark": 2500.0,
                "on_exchange_close_after_final_exit": 2500.0,
                "off_exchange_cash": 2500.0,
                "total_equity": 5000.0,
            },
            {
                "date": date(2024, 12, 31),
                "cash": 900.0,
                "holdings_close": 1800.0,
                "on_exchange_close_mark": 2700.0,
                "on_exchange_close_after_final_exit": 2700.0,
                "off_exchange_cash": 2500.0,
                "total_equity": 5200.0,
            },
            {
                "date": date(2025, 1, 1),
                "cash": 900.0,
                "holdings_close": 1700.0,
                "on_exchange_close_mark": 2600.0,
                "on_exchange_close_after_final_exit": 2600.0,
                "off_exchange_cash": 2500.0,
                "total_equity": 5100.0,
            },
        ]
        state, base_equity = oos_start_snapshot(daily, date(2025, 1, 1))
        self.assertEqual(base_equity, 5200.0)
        self.assertEqual(state["cash"], 900.0)
        self.assertEqual(state["holdings_close"], 1800.0)
        self.assertEqual(state["total_equity"], 5200.0)
        self.assertNotEqual(base_equity, 5000.0)


class CsvPrecheckTests(unittest.TestCase):
    def test_gap_is_reported(self):
        days = [date(2024, 1, 1), date(2024, 1, 2), date(2024, 1, 3)]
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "spot_daily.csv")
            write_fixture(path, days, skipped={(days[1], symbol) for symbol in SYMBOLS})
            with self.assertRaises(DataError) as context:
                load_and_precheck(
                    path,
                    expected_start=days[0],
                    expected_end=days[-1],
                    require_warmup=False,
                )
        errors = " ".join(context.exception.quality["errors"])
        self.assertIn("missing days", errors)

    def test_raw_epoch_mismatch_is_rejected(self):
        days = [date(2024, 1, 1), date(2024, 1, 2), date(2024, 1, 3)]
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "spot_daily.csv")
            write_fixture(
                path,
                days,
                overrides={(days[0], "BTCUSDT"): {"open_time_raw": "1"}},
            )
            with self.assertRaises(DataError) as context:
                load_and_precheck(
                    path,
                    expected_start=days[0],
                    expected_end=days[-1],
                    require_warmup=False,
                )
        errors = " ".join(context.exception.quality["errors"])
        self.assertIn("open_time_raw disagrees", errors)

    def test_close_must_be_exact_utc_day_end(self):
        days = [date(2024, 1, 1), date(2024, 1, 2), date(2024, 1, 3)]
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "spot_daily.csv")
            write_fixture(
                path,
                days,
                overrides={(days[0], "BTCUSDT"): {"close_time_utc": f"{days[0].isoformat()}T23:59:59Z"}},
            )
            with self.assertRaises(DataError) as context:
                load_and_precheck(
                    path,
                    expected_start=days[0],
                    expected_end=days[-1],
                    require_warmup=False,
                )
        errors = " ".join(context.exception.quality["errors"])
        self.assertIn("23:59:59.999", errors)

    def test_nan_price_is_rejected(self):
        days = [date(2024, 1, 1), date(2024, 1, 2), date(2024, 1, 3)]
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "spot_daily.csv")
            write_fixture(
                path,
                days,
                overrides={(days[0], "BTCUSDT"): {"open": "nan"}},
            )
            with self.assertRaises(DataError) as context:
                load_and_precheck(
                    path,
                    expected_start=days[0],
                    expected_end=days[-1],
                    require_warmup=False,
                )
        errors = " ".join(context.exception.quality["errors"])
        self.assertIn("not finite", errors)


if __name__ == "__main__":
    unittest.main()
