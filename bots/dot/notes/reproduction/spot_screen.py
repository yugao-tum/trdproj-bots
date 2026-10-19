#!/usr/bin/env python3
"""Pre-registered fixed-rule spot historical simulation; no network or trading."""

from __future__ import annotations

import csv
import json
import math
import sys
from dataclasses import dataclass, field
from datetime import date, datetime, time as dt_time, timedelta, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_EVEN
from pathlib import Path
from typing import Any, Sequence

BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = BASE_DIR.parent / "workers" / "data-probe" / "data" / "history" / "spot_daily.csv"
OUT_DIR = BASE_DIR.parent / "results" / "spot-screen"

SYMBOLS = ("BTCUSDT", "ETHUSDT", "SOLUSDT")
REQUIRED_FIELDS = [
    "symbol",
    "open_time_utc",
    "open_time_raw",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "close_time_utc",
    "close_time_raw",
    "quote_volume",
    "count",
    "taker_buy_volume",
    "taker_buy_quote_volume",
    "ignore",
]
DATA_START = date(2023, 1, 1)
DATA_END = date(2026, 9, 30)
SIM_START = date(2024, 1, 1)
SIM_END = date(2026, 9, 30)
OOS_START = date(2025, 1, 1)
CAPITAL_USDT = 5000.0
ON_EXCHANGE_START = 2500.0
OFF_EXCHANGE_CASH = 2500.0
POSITION_CAP_USDT = 2200.0
TARGET_FRACTION = 0.9
COST_RATES = (0.003, 0.006)
EPS = 1e-9
EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)
CLOSE_TIMES = (dt_time(23, 59, 59, 999000), dt_time(23, 59, 59, 999999))

STRATEGIES = {
    "C21": "SOL prior close > 200-day simple SMA of prior closes; long SOL else cash; Monday open.",
    "C22": "Rank BTC/ETH/SOL by prior 60-day return; Monday buy the top if its momentum > 0 else cash.",
    "C23": "SOL simple 14-day mean-gain/mean-loss RSI (not Wilder); RSI<30 entry; RSI>50 or 14 calendar days exit; daily next open.",
    "C24": "BTC/ETH/SOL equal weight; Monday rebalance; always long.",
}


class DataError(ValueError):
    def __init__(self, message: str, quality: dict[str, Any]):
        super().__init__(message)
        self.quality = quality


@dataclass(frozen=True)
class Bar:
    day: date
    open: float
    high: float
    low: float
    close: float


@dataclass
class Trade:
    day: date
    symbol: str
    side: str
    qty: float
    price: float
    notional: float
    fee: float
    reason: str
    cash_after: float
    qty_after: float


def parse_utc(text: str) -> datetime:
    raw = text.strip()
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    try:
        value = datetime.fromisoformat(raw)
    except ValueError as exc:
        raise ValueError(f"invalid UTC timestamp {text!r}") from exc
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"timestamp lacks timezone: {text!r}")
    return value.astimezone(timezone.utc)


def parse_epoch_raw(text: str) -> datetime:
    try:
        raw = Decimal(text.strip())
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"raw epoch is not numeric: {text!r}") from exc
    if not raw.is_finite():
        raise ValueError("raw epoch is not finite")
    magnitude = abs(raw)
    if magnitude < Decimal("1e11"):
        divisor = 1
    elif magnitude < Decimal("1e14"):
        divisor = 1000
    elif magnitude < Decimal("1e17"):
        divisor = 1000000
    elif magnitude < Decimal("1e20"):
        divisor = 1000000000
    else:
        raise ValueError("cannot infer raw epoch unit")
    total_us = int((raw * Decimal(1_000_000) / Decimal(divisor)).to_integral_value(rounding=ROUND_HALF_EVEN))
    return EPOCH + timedelta(microseconds=total_us)


def _finite_float(text: str, field_name: str, *, positive: bool = False, nonnegative: bool = False) -> float:
    try:
        value = float(text)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} is not numeric") from exc
    if not math.isfinite(value):
        raise ValueError(f"{field_name} is not finite")
    if positive and value <= 0:
        raise ValueError(f"{field_name} must be positive")
    if nonnegative and value < 0:
        raise ValueError(f"{field_name} must be nonnegative")
    return value


def load_and_precheck(
    csv_path: str | Path,
    *,
    expected_start: date = DATA_START,
    expected_end: date = DATA_END,
    require_warmup: bool = True,
) -> tuple[dict[str, list[Bar]], list[date], dict[str, Any]]:
    quality: dict[str, Any] = {
        "csv_path": str(csv_path),
        "schema_ok": False,
        "rows_read": 0,
        "expected_start": expected_start.isoformat(),
        "expected_end": expected_end.isoformat(),
        "symbols": {
            symbol: {
                "rows": 0,
                "duplicates": 0,
                "missing_count": 0,
                "missing_sample": [],
                "extra_count": 0,
            }
            for symbol in SYMBOLS
        },
        "aligned": False,
        "errors": [],
        "notes": [
            "2023 rows are warmup only; simulation starts 2024-01-01.",
            "Daily spot bars cannot verify intraday margin; this screen is spot-only and has no margin.",
            "Daily highs of different symbols are not simultaneous.",
        ],
    }
    bars: dict[str, dict[date, Bar]] = {symbol: {} for symbol in SYMBOLS}
    duplicate_counts = {symbol: 0 for symbol in SYMBOLS}
    with open(csv_path, "r", newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != REQUIRED_FIELDS:
            quality["actual_columns"] = reader.fieldnames
            quality["expected_columns"] = REQUIRED_FIELDS
            quality["errors"].append("CSV schema mismatch")
            raise DataError("CSV schema mismatch", quality)
        quality["schema_ok"] = True
        for line_no, row in enumerate(reader, start=2):
            quality["rows_read"] += 1
            if None in row:
                quality["errors"].append(f"line {line_no}: extra columns")
                continue
            if any(value is None for value in row.values()):
                quality["errors"].append(f"line {line_no}: missing column value")
                continue
            symbol = (row.get("symbol") or "").strip()
            if symbol not in SYMBOLS:
                quality["errors"].append(f"line {line_no}: unknown symbol {symbol!r}")
                continue
            try:
                open_dt = parse_utc(row["open_time_utc"])
                close_dt = parse_utc(row["close_time_utc"])
                if open_dt.time() != dt_time(0, 0):
                    raise ValueError("open_time_utc must be UTC midnight")
                if close_dt.date() != open_dt.date() or close_dt <= open_dt:
                    raise ValueError("close_time_utc is not a same-day close after open")
                if close_dt.time() not in CLOSE_TIMES:
                    raise ValueError("close_time_utc must be 23:59:59.999 or 23:59:59.999999 UTC")
                if parse_epoch_raw(row["open_time_raw"]) != open_dt:
                    raise ValueError("open_time_raw disagrees with open_time_utc")
                if parse_epoch_raw(row["close_time_raw"]) != close_dt:
                    raise ValueError("close_time_raw disagrees with close_time_utc")
                day = open_dt.date()
                if day < expected_start or day > expected_end:
                    raise ValueError(f"date {day} outside {expected_start}..{expected_end}")
                open_p = _finite_float(row["open"], "open", positive=True)
                high_p = _finite_float(row["high"], "high", positive=True)
                low_p = _finite_float(row["low"], "low", positive=True)
                close_p = _finite_float(row["close"], "close", positive=True)
                if not (low_p <= min(open_p, close_p) and high_p >= max(open_p, close_p)):
                    raise ValueError("OHLC inconsistent")
                _finite_float(row["volume"], "volume", nonnegative=True)
                _finite_float(row["quote_volume"], "quote_volume", nonnegative=True)
                _finite_float(row["count"], "count", nonnegative=True)
                _finite_float(row["taker_buy_volume"], "taker_buy_volume", nonnegative=True)
                _finite_float(row["taker_buy_quote_volume"], "taker_buy_quote_volume", nonnegative=True)
            except (KeyError, ValueError) as exc:
                quality["errors"].append(f"line {line_no} {symbol}: {exc}")
                continue
            if day in bars[symbol]:
                duplicate_counts[symbol] += 1
                quality["errors"].append(f"line {line_no} {symbol}: duplicate UTC day {day}")
                continue
            bars[symbol][day] = Bar(day=day, open=open_p, high=high_p, low=low_p, close=close_p)

    expected_days = [expected_start + timedelta(days=offset) for offset in range((expected_end - expected_start).days + 1)]
    expected_set = set(expected_days)
    date_sets: list[set[date]] = []
    for symbol in SYMBOLS:
        got = set(bars[symbol])
        date_sets.append(got)
        missing = sorted(expected_set - got)
        extra = sorted(got - expected_set)
        info = quality["symbols"][symbol]
        info.update(
            {
                "rows": len(got),
                "duplicates": duplicate_counts[symbol],
                "missing_count": len(missing),
                "missing_sample": [item.isoformat() for item in missing[:10]],
                "extra_count": len(extra),
                "first": min(got).isoformat() if got else None,
                "last": max(got).isoformat() if got else None,
            }
        )
        if missing:
            quality["errors"].append(f"{symbol}: {len(missing)} missing days; sample {info['missing_sample']}")
        if extra:
            quality["errors"].append(f"{symbol}: {len(extra)} unexpected days")
        if duplicate_counts[symbol]:
            quality["errors"].append(f"{symbol}: {duplicate_counts[symbol]} duplicate rows")

    quality["aligned"] = len({frozenset(item) for item in date_sets}) == 1
    if not quality["aligned"]:
        quality["errors"].append("symbol date sets are not aligned")
    quality["dates_count"] = len(expected_days)
    if require_warmup:
        warmup_days = (SIM_START - expected_start).days
        quality["warmup_days"] = warmup_days
        if warmup_days < 200:
            quality["errors"].append("fewer than 200 warmup days before 2024-01-01")
        if expected_end < SIM_END:
            quality["errors"].append("data does not reach simulation end")
    if quality["errors"]:
        raise DataError("CSV precheck failed", quality)

    aligned = {symbol: [bars[symbol][day] for day in expected_days] for symbol in SYMBOLS}
    return aligned, expected_days, quality


def c21_signal(closes: Sequence[float], index: int) -> bool:
    if index < 200:
        raise ValueError("C21 requires 200 prior closes")
    previous_close = float(closes[index - 1])
    sma = sum(float(value) for value in closes[index - 200:index]) / 200.0
    return previous_close > sma


def c22_momentum(closes: Sequence[float], index: int, lookback: int = 60) -> float:
    if index < lookback + 1:
        raise ValueError("C22 requires lookback+1 prior closes")
    start = float(closes[index - lookback - 1])
    previous = float(closes[index - 1])
    return previous / start - 1.0


def c22_target(closes_by_symbol: dict[str, Sequence[float]], index: int) -> str | None:
    best_symbol: str | None = None
    best_momentum: float | None = None
    for symbol in SYMBOLS:
        momentum = c22_momentum(closes_by_symbol[symbol], index)
        if best_momentum is None or momentum > best_momentum + 1e-15:
            best_symbol = symbol
            best_momentum = momentum
    if best_symbol is None or best_momentum is None or best_momentum <= 0:
        return None
    return best_symbol


def simple_rsi(closes: Sequence[float], period: int = 14) -> float | None:
    if len(closes) < period + 1:
        return None
    changes = [float(closes[pos]) - float(closes[pos - 1]) for pos in range(len(closes) - period, len(closes))]
    average_gain = sum(max(change, 0.0) for change in changes) / period
    average_loss = sum(max(-change, 0.0) for change in changes) / period
    if average_loss == 0.0:
        return 100.0 if average_gain > 0.0 else 50.0
    if average_gain == 0.0:
        return 0.0
    relative_strength = average_gain / average_loss
    return 100.0 - 100.0 / (1.0 + relative_strength)


@dataclass
class Portfolio:
    cost_rate: float
    cash: float = ON_EXCHANGE_START
    qty: dict[str, float] = field(default_factory=lambda: {symbol: 0.0 for symbol in SYMBOLS})
    trades: list[Trade] = field(default_factory=list)
    buy_shrunk: int = 0
    cash_min: float = ON_EXCHANGE_START
    negative_cash_seen: bool = False
    negative_qty_seen: bool = False
    episodes: list[dict[str, Any]] = field(default_factory=list)
    episode_counter: int = 0
    active_episode: int | None = None
    episode_start: date | None = None
    entry_date: date | None = None

    def has_position(self) -> bool:
        return any(quantity > EPS for quantity in self.qty.values())

    def update_episode(self, day: date) -> None:
        invested = self.has_position()
        if invested and self.active_episode is None:
            self.episode_counter += 1
            self.active_episode = self.episode_counter
            self.episode_start = day
            self.entry_date = day
        elif not invested and self.active_episode is not None:
            self.episodes.append(
                {
                    "episode_id": self.active_episode,
                    "start": self.episode_start,
                    "end": day,
                }
            )
            self.active_episode = None
            self.episode_start = None
            self.entry_date = None

    def _validate(self) -> None:
        for symbol, quantity in self.qty.items():
            if quantity < -EPS:
                self.negative_qty_seen = True
                raise RuntimeError(f"negative quantity for {symbol}")
            if quantity < 0.0:
                self.qty[symbol] = 0.0
        if self.cash < -EPS:
            self.negative_cash_seen = True
            raise RuntimeError("negative cash")
        if self.cash < 0.0:
            self.cash = 0.0
        self.cash_min = min(self.cash_min, self.cash)

    def _record(self, day: date, symbol: str, side: str, qty: float, price: float, reason: str) -> None:
        notional = qty * price
        fee = notional * self.cost_rate
        self.trades.append(
            Trade(
                day=day,
                symbol=symbol,
                side=side,
                qty=qty,
                price=price,
                notional=notional,
                fee=fee,
                reason=reason,
                cash_after=self.cash,
                qty_after=self.qty[symbol],
            )
        )

    def _sell(self, day: date, symbol: str, price: float, qty: float, reason: str) -> None:
        notional = qty * price
        fee = notional * self.cost_rate
        self.cash += notional - fee
        self.qty[symbol] -= qty
        self._validate()
        self._record(day, symbol, "SELL", qty, price, reason)

    def _buy(self, day: date, symbol: str, price: float, qty: float, reason: str) -> None:
        notional = qty * price
        fee = notional * self.cost_rate
        total = notional + fee
        if total > self.cash + EPS:
            raise RuntimeError("buy exceeds available cash")
        self.cash -= total
        self.qty[symbol] += qty
        self._validate()
        self._record(day, symbol, "BUY", qty, price, reason)

    def rebalance(
        self,
        day: date,
        open_prices: dict[str, float],
        selected: Sequence[str],
        reason: str,
    ) -> None:
        selected = list(dict.fromkeys(selected))
        for symbol in selected:
            if symbol not in open_prices or open_prices[symbol] <= 0:
                raise ValueError(f"missing or invalid open price for {symbol}")
        assets = self.cash + sum(
            self.qty[symbol] * open_prices[symbol]
            for symbol in SYMBOLS
            if self.qty[symbol] > EPS
        )
        if assets <= 0:
            raise RuntimeError("non-positive on-exchange assets")
        target_total = min(POSITION_CAP_USDT, TARGET_FRACTION * assets)
        target_qty = {symbol: 0.0 for symbol in SYMBOLS}
        if selected:
            per_symbol = target_total / len(selected)
            for symbol in selected:
                target_qty[symbol] = per_symbol / open_prices[symbol]
        for symbol in SYMBOLS:
            excess = self.qty[symbol] - target_qty[symbol]
            if excess > EPS:
                self._sell(day, symbol, open_prices[symbol], min(excess, self.qty[symbol]), reason)
        for symbol in SYMBOLS:
            shortfall = target_qty[symbol] - self.qty[symbol]
            if shortfall <= EPS:
                continue
            price = open_prices[symbol]
            max_qty = max(0.0, self.cash / (price * (1.0 + self.cost_rate)))
            buy_qty = min(shortfall, max_qty)
            if buy_qty < shortfall - 1e-12:
                self.buy_shrunk += 1
            if buy_qty > EPS:
                self._buy(day, symbol, price, buy_qty, reason)

    def liquidate(self, day: date, close_prices: dict[str, float], reason: str) -> None:
        for symbol in SYMBOLS:
            if self.qty[symbol] > EPS:
                self._sell(day, symbol, close_prices[symbol], self.qty[symbol], reason)


def _open_prices(bars: dict[str, list[Bar]], index: int) -> dict[str, float]:
    return {symbol: bars[symbol][index].open for symbol in SYMBOLS}


def _close_prices(bars: dict[str, list[Bar]], index: int) -> dict[str, float]:
    return {symbol: bars[symbol][index].close for symbol in SYMBOLS}


def _high_prices(bars: dict[str, list[Bar]], index: int) -> dict[str, float]:
    return {symbol: bars[symbol][index].high for symbol in SYMBOLS}


def simulate(strategy: str, bars: dict[str, list[Bar]], dates: list[date], cost_rate: float) -> dict[str, Any]:
    if strategy not in STRATEGIES:
        raise ValueError(f"unknown strategy {strategy}")
    start_index = dates.index(SIM_START)
    end_index = dates.index(SIM_END)
    closes = {symbol: [bar.close for bar in bars[symbol]] for symbol in SYMBOLS}
    portfolio = Portfolio(cost_rate=cost_rate)
    daily: list[dict[str, Any]] = []
    confirmed_open_breach_days = 0
    confirmed_close_breach_days = 0
    possible_high_bound_breach_days = 0
    max_open_on_exchange = 0.0
    max_close_on_exchange = 0.0
    max_high_upper_bound = 0.0

    for index in range(start_index, end_index + 1):
        day = dates[index]
        opens = _open_prices(bars, index)
        on_exchange_open_pretrade_mark = portfolio.cash + sum(
            portfolio.qty[symbol] * opens[symbol] for symbol in SYMBOLS
        )
        confirmed_open_breach = on_exchange_open_pretrade_mark > ON_EXCHANGE_START + EPS
        if confirmed_open_breach:
            confirmed_open_breach_days += 1
        max_open_on_exchange = max(max_open_on_exchange, on_exchange_open_pretrade_mark)

        if strategy == "C21" and day.weekday() == 0:
            selected = ["SOLUSDT"] if c21_signal(closes["SOLUSDT"], index) else []
            portfolio.rebalance(day, opens, selected, "C21 weekly long" if selected else "C21 weekly cash")
        elif strategy == "C22" and day.weekday() == 0:
            target = c22_target(closes, index)
            selected = [target] if target else []
            portfolio.rebalance(day, opens, selected, "C22 weekly momentum" if selected else "C22 weekly cash")
        elif strategy == "C23":
            if portfolio.has_position():
                rsi = simple_rsi(closes["SOLUSDT"][:index], 14)
                age = (day - portfolio.entry_date).days if portfolio.entry_date else 0
                if (rsi is not None and rsi > 50.0) or age >= 14:
                    portfolio.rebalance(day, opens, [], "C23 exit")
            else:
                rsi = simple_rsi(closes["SOLUSDT"][:index], 14)
                if rsi is not None and rsi < 30.0:
                    portfolio.rebalance(day, opens, ["SOLUSDT"], "C23 entry")
        elif strategy == "C24" and day.weekday() == 0:
            portfolio.rebalance(day, opens, list(SYMBOLS), "C24 weekly equal-weight")

        portfolio.update_episode(day)
        close_prices = _close_prices(bars, index)
        high_prices = _high_prices(bars, index)
        on_exchange_close_mark = portfolio.cash + sum(
            portfolio.qty[symbol] * close_prices[symbol] for symbol in SYMBOLS
        )
        on_exchange_high_upper_bound = portfolio.cash + sum(
            portfolio.qty[symbol] * high_prices[symbol] for symbol in SYMBOLS
        )
        confirmed_close_breach = on_exchange_close_mark > ON_EXCHANGE_START + EPS
        possible_high_bound_breach = on_exchange_high_upper_bound > ON_EXCHANGE_START + EPS
        if confirmed_close_breach:
            confirmed_close_breach_days += 1
        if possible_high_bound_breach:
            possible_high_bound_breach_days += 1
        max_close_on_exchange = max(max_close_on_exchange, on_exchange_close_mark)
        max_high_upper_bound = max(max_high_upper_bound, on_exchange_high_upper_bound)

        final_exit_fee = 0.0
        if index == end_index:
            portfolio.liquidate(day, close_prices, "final close liquidation")
            portfolio.update_episode(day)
            final_exit_fee = sum(
                trade.fee
                for trade in portfolio.trades
                if trade.day == day and trade.reason == "final close liquidation"
            )

        holdings_close = sum(portfolio.qty[symbol] * close_prices[symbol] for symbol in SYMBOLS)
        on_exchange_close_after_final_exit = portfolio.cash + holdings_close
        total_equity = on_exchange_close_after_final_exit + OFF_EXCHANGE_CASH
        daily.append(
            {
                "date": day,
                "cash": portfolio.cash,
                "holdings_close": holdings_close,
                "on_exchange_open_pretrade_mark": on_exchange_open_pretrade_mark,
                "on_exchange_close_mark": on_exchange_close_mark,
                "on_exchange_close_after_final_exit": on_exchange_close_after_final_exit,
                "off_exchange_cash": OFF_EXCHANGE_CASH,
                "total_equity": total_equity,
                "on_exchange_high_upper_bound": on_exchange_high_upper_bound,
                "confirmed_open_breach": confirmed_open_breach,
                "confirmed_close_breach": confirmed_close_breach,
                "possible_high_bound_breach": possible_high_bound_breach,
                "episode_id": portfolio.active_episode or 0,
                "final_exit_fee": final_exit_fee,
            }
        )

    return {
        "strategy": strategy,
        "cost_rate": cost_rate,
        "daily": daily,
        "trades": portfolio.trades,
        "episodes": portfolio.episodes,
        "cash_min": portfolio.cash_min,
        "buy_shrunk": portfolio.buy_shrunk,
        "negative_cash_seen": portfolio.negative_cash_seen,
        "negative_qty_seen": portfolio.negative_qty_seen,
        "confirmed_open_breach_days": confirmed_open_breach_days,
        "confirmed_close_breach_days": confirmed_close_breach_days,
        "possible_high_bound_breach_days": possible_high_bound_breach_days,
        "max_open_on_exchange": max_open_on_exchange,
        "max_close_on_exchange": max_close_on_exchange,
        "max_high_upper_bound": max_high_upper_bound,
    }


def _max_drawdown(equities: Sequence[float]) -> float:
    peak = equities[0]
    drawdown = 0.0
    for equity in equities:
        peak = max(peak, equity)
        if peak > 0:
            drawdown = max(drawdown, (peak - equity) / peak)
    return drawdown


def _monthly_returns(rows: Sequence[dict[str, Any]], base_equity: float) -> list[dict[str, Any]]:
    month_ends: dict[str, dict[str, Any]] = {}
    for row in rows:
        month_ends[row["date"].strftime("%Y-%m")] = row
    output: list[dict[str, Any]] = []
    previous_equity = base_equity
    for month in sorted(month_ends):
        row = month_ends[month]
        end_equity = float(row["total_equity"])
        pnl = end_equity - previous_equity
        output.append(
            {
                "month": month,
                "start_equity": previous_equity,
                "end_equity": end_equity,
                "pnl": pnl,
                "net_return": pnl / previous_equity if previous_equity else None,
            }
        )
        previous_equity = end_equity
    return output


def _initial_state() -> dict[str, Any]:
    return {
        "cash": ON_EXCHANGE_START,
        "holdings_close": 0.0,
        "on_exchange_close_mark": ON_EXCHANGE_START,
        "on_exchange_close_after_final_exit": ON_EXCHANGE_START,
        "off_exchange_cash": OFF_EXCHANGE_CASH,
        "total_equity": CAPITAL_USDT,
    }


def _state_from_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "cash": row["cash"],
        "holdings_close": row["holdings_close"],
        "on_exchange_close_mark": row["on_exchange_close_mark"],
        "on_exchange_close_after_final_exit": row["on_exchange_close_after_final_exit"],
        "off_exchange_cash": row["off_exchange_cash"],
        "total_equity": row["total_equity"],
    }


def oos_start_snapshot(
    daily: Sequence[dict[str, Any]],
    oos_start: date = OOS_START,
) -> tuple[dict[str, Any], float]:
    prior = [row for row in daily if row["date"] < oos_start]
    if not prior:
        return _initial_state(), CAPITAL_USDT
    last = prior[-1]
    return _state_from_row(last), float(last["total_equity"])


def _period_metrics(
    name: str,
    rows: Sequence[dict[str, Any]],
    base_equity: float,
    start_state: dict[str, Any],
    trades: Sequence[Trade],
    episodes: Sequence[dict[str, Any]],
    start: date,
    end: date,
) -> dict[str, Any]:
    if not rows:
        raise ValueError(f"empty period {name}")
    end_state = _state_from_row(rows[-1])
    net_pnl = end_state["total_equity"] - base_equity
    monthly = _monthly_returns(rows, base_equity)
    profitable_months = [month for month in monthly if month["pnl"] > 0]
    best_month = max(profitable_months, key=lambda month: month["pnl"]) if profitable_months else None
    net_ex_best = net_pnl - (best_month["pnl"] if best_month else 0.0)
    period_trades = [trade for trade in trades if start <= trade.day <= end]
    calendar_days = (end - start).days + 1
    cagr = None
    if base_equity > 0 and end_state["total_equity"] > 0:
        cagr = (end_state["total_equity"] / base_equity) ** (365.0 / calendar_days) - 1.0
    open_breach_days = sum(1 for row in rows if row["confirmed_open_breach"])
    close_breach_days = sum(1 for row in rows if row["confirmed_close_breach"])
    high_breach_days = sum(1 for row in rows if row["possible_high_bound_breach"])
    max_open = max(float(row["on_exchange_open_pretrade_mark"]) for row in rows)
    max_close = max(float(row["on_exchange_close_mark"]) for row in rows)
    max_high = max(float(row["on_exchange_high_upper_bound"]) for row in rows)
    episodes_started = sum(1 for episode in episodes if start <= episode["start"] <= end)
    return {
        "period": name,
        "start": start.isoformat(),
        "end": end.isoformat(),
        "start_state": start_state,
        "end_state": end_state,
        "start_equity": base_equity,
        "end_equity": end_state["total_equity"],
        "net_pnl_usdt": net_pnl,
        "total_return_on_start_equity": net_pnl / base_equity if base_equity else None,
        "fixed_5000_return": net_pnl / CAPITAL_USDT,
        "calendar_days": calendar_days,
        "cagr": cagr,
        "max_drawdown": _max_drawdown([base_equity] + [float(row["total_equity"]) for row in rows]),
        "trade_count": len(period_trades),
        "fees_usdt": sum(trade.fee for trade in period_trades),
        "notional_traded_usdt": sum(trade.notional for trade in period_trades),
        "months": len(monthly),
        "episodes_started": episodes_started,
        "monthly_returns": monthly,
        "best_profitable_month": best_month["month"] if best_month else None,
        "best_month_pnl_usdt": best_month["pnl"] if best_month else 0.0,
        "net_ex_best_month_usdt": net_ex_best,
        "return_ex_best_month_on_start_equity": net_ex_best / base_equity if base_equity else None,
        "capital_bound_diagnostics": {
            "venue_limit_usdt": ON_EXCHANGE_START,
            "confirmed_open_breach_days": open_breach_days,
            "confirmed_close_breach_days": close_breach_days,
            "possible_high_bound_breach_days": high_breach_days,
            "max_open_on_exchange_usdt": max_open,
            "max_close_on_exchange_usdt": max_close,
            "max_high_upper_bound_usdt": max_high,
            "confirmed_open_breach": open_breach_days > 0,
            "confirmed_close_breach": close_breach_days > 0,
            "possible_high_bound_breach": high_breach_days > 0,
        },
    }


def build_summary(
    bars: dict[str, list[Bar]],
    dates: list[date],
    quality: dict[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    strategies_output: dict[str, Any] = {}
    daily_rows: list[dict[str, Any]] = []
    trade_rows: list[dict[str, Any]] = []
    monthly_rows: list[dict[str, Any]] = []

    for cost_rate in COST_RATES:
        cost_key = f"{cost_rate:.3f}"
        for strategy in STRATEGIES:
            simulation = simulate(strategy, bars, dates, cost_rate)
            daily = simulation["daily"]
            trades = simulation["trades"]
            episodes = simulation["episodes"]
            rows_2024 = [row for row in daily if row["date"] <= date(2024, 12, 31)]
            rows_oos = [row for row in daily if row["date"] >= OOS_START]
            oos_start_state, oos_base_equity = oos_start_snapshot(daily, OOS_START)
            periods = {
                "2024": _period_metrics(
                    "2024",
                    rows_2024,
                    CAPITAL_USDT,
                    _initial_state(),
                    trades,
                    episodes,
                    SIM_START,
                    date(2024, 12, 31),
                ),
                "oos_2025": _period_metrics(
                    "oos_2025",
                    rows_oos,
                    oos_base_equity,
                    oos_start_state,
                    trades,
                    episodes,
                    OOS_START,
                    SIM_END,
                ),
                "full": _period_metrics(
                    "full",
                    daily,
                    CAPITAL_USDT,
                    _initial_state(),
                    trades,
                    episodes,
                    SIM_START,
                    SIM_END,
                ),
            }
            monthly_full = _monthly_returns(daily, CAPITAL_USDT)
            strategies_output.setdefault(
                strategy,
                {"description": STRATEGIES[strategy], "scenarios": {}},
            )
            strategies_output[strategy]["scenarios"][cost_key] = {
                "cost_rate": cost_rate,
                "periods": periods,
                "monthly_returns_full": monthly_full,
                "episodes_total": len(episodes),
                "episodes": [
                    {
                        "episode_id": episode["episode_id"],
                        "start": episode["start"].isoformat(),
                        "end": episode["end"].isoformat(),
                    }
                    for episode in episodes
                ],
                "legality": {
                    "negative_cash_seen": simulation["negative_cash_seen"],
                    "negative_qty_seen": simulation["negative_qty_seen"],
                    "buy_shrunk_count": simulation["buy_shrunk"],
                    "min_cash_usdt": simulation["cash_min"],
                    "cash_floor_ok": not simulation["negative_cash_seen"] and simulation["cash_min"] >= -EPS,
                    "qty_floor_ok": not simulation["negative_qty_seen"],
                    "fees_deducted_from_on_exchange_cash": True,
                    "off_exchange_transfers": 0,
                },
                "capital_bound_diagnostics_full": periods["full"]["capital_bound_diagnostics"],
                "independent_sample": {
                    "episodes_total": len(episodes),
                    "months_total": len(monthly_full),
                    "minimum_30_claim": False,
                    "event_correlation_review": "pending",
                    "note": "Episodes are contiguous invested spells; direct asset switches are not new episodes. Bar or leg counts are not independent samples.",
                },
            }
            for row in daily:
                daily_rows.append(
                    {
                        "cost_rate": cost_key,
                        "strategy": strategy,
                        "date": row["date"].isoformat(),
                        "cash": row["cash"],
                        "holdings_close": row["holdings_close"],
                        "on_exchange_open_pretrade_mark": row["on_exchange_open_pretrade_mark"],
                        "on_exchange_close_mark": row["on_exchange_close_mark"],
                        "on_exchange_close_after_final_exit": row["on_exchange_close_after_final_exit"],
                        "off_exchange_cash": row["off_exchange_cash"],
                        "total_equity": row["total_equity"],
                        "on_exchange_high_upper_bound": row["on_exchange_high_upper_bound"],
                        "confirmed_open_breach": row["confirmed_open_breach"],
                        "confirmed_close_breach": row["confirmed_close_breach"],
                        "possible_high_bound_breach": row["possible_high_bound_breach"],
                        "episode_id": row["episode_id"],
                        "final_exit_fee": row["final_exit_fee"],
                    }
                )
            for trade in trades:
                trade_rows.append(
                    {
                        "cost_rate": cost_key,
                        "strategy": strategy,
                        "date": trade.day.isoformat(),
                        "symbol": trade.symbol,
                        "side": trade.side,
                        "qty": trade.qty,
                        "price": trade.price,
                        "notional": trade.notional,
                        "fee": trade.fee,
                        "reason": trade.reason,
                        "cash_after": trade.cash_after,
                        "qty_after": trade.qty_after,
                    }
                )
            for month in monthly_full:
                monthly_rows.append(
                    {
                        "cost_rate": cost_key,
                        "strategy": strategy,
                        "month": month["month"],
                        "start_equity": month["start_equity"],
                        "end_equity": month["end_equity"],
                        "pnl": month["pnl"],
                        "net_return": month["net_return"],
                    }
                )

    summary = {
        "disclaimer": "Pre-registered fixed-rule historical simulation, not a profit promise or live-trading claim. Time splits are ex post; 2025+ is not truly unseen forward data.",
        "generated_by": "spot_screen.py",
        "data": quality,
        "parameters": {
            "simulation_start": SIM_START.isoformat(),
            "simulation_end": SIM_END.isoformat(),
            "oos_start": OOS_START.isoformat(),
            "capital_usdt": CAPITAL_USDT,
            "initial_on_exchange_cash_usdt": ON_EXCHANGE_START,
            "initial_off_exchange_idle_cash_usdt": OFF_EXCHANGE_CASH,
            "target_position_cap_usdt": POSITION_CAP_USDT,
            "target_fraction_of_on_exchange_assets": TARGET_FRACTION,
            "cost_rates": list(COST_RATES),
            "signal_timing": "prior-day close or earlier; execute at next day's open",
            "final_exit": "forced at 2026-09-30 close with cost",
            "data_start_used_only_for_warmup": DATA_START.isoformat(),
        },
        "contributed_capital": {
            "initial_on_exchange_including_fee_buffer_usdt": ON_EXCHANGE_START,
            "additional_on_exchange_including_fee_buffer_usdt": 0.0,
            "initial_off_exchange_idle_usdt": OFF_EXCHANGE_CASH,
            "total_contributed_usdt": CAPITAL_USDT,
            "initial_uninvested_on_exchange_buffer_above_target_usdt": ON_EXCHANGE_START - POSITION_CAP_USDT,
            "fee_policy": "All trading fees are deducted from on-exchange cash. The off-exchange 2500 is never transferred.",
        },
        "guide_interpretation": {
            "text": "GUIDE says roughly 2500 per venue without specifying contributed principal versus dynamic net assets. This report does not present the strict dynamic reading as the guide's literal wording.",
            "fee_buffer_note": "On-exchange 2500 is the initial contribution and includes the fee buffer. The 2200 target cap leaves 300 before costs. All fees are deducted from on-exchange cash; the off-exchange 2500 is never transferred.",
        },
        "capital_bound_definitions": {
            "venue_limit_usdt": ON_EXCHANGE_START,
            "confirmed_open_lens": "cash plus old positions marked at daily open before any trade; above 2500 is a confirmed open-mark breach, so an opening gap is not hidden by fees.",
            "confirmed_close_lens": "cash plus positions marked at daily close, before end-of-sample forced exit; above 2500 is a confirmed close breach.",
            "possible_high_bound_lens": "cash plus sum(qty*daily high); daily highs across symbols are not simultaneous, so above 2500 is only a possible capital bound breach.",
            "daily_bar_limit": "Daily bars cannot verify intraday margin. This screen is spot-only and has no margin.",
            "tuning": "Thresholds are fixed before running; there is no post-hoc adjustment to force a pass.",
        },
        "strategies": strategies_output,
    }
    return summary, daily_rows, trade_rows, monthly_rows


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True, ensure_ascii=False, default=str)
        handle.write("\n")


def _write_csv(path: Path, fieldnames: Sequence[str], rows: Sequence[dict[str, Any]]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def main() -> int:
    try:
        bars, dates, quality = load_and_precheck(CSV_PATH)
    except DataError as exc:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        _write_json(OUT_DIR / "data_quality.json", exc.quality)
        print(f"data precheck failed: {exc}", file=sys.stderr)
        return 2

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    _write_json(OUT_DIR / "data_quality.json", quality)
    summary, daily_rows, trade_rows, monthly_rows = build_summary(bars, dates, quality)
    _write_json(OUT_DIR / "summary.json", summary)
    _write_csv(
        OUT_DIR / "daily_equity.csv",
        [
            "cost_rate",
            "strategy",
            "date",
            "cash",
            "holdings_close",
            "on_exchange_open_pretrade_mark",
            "on_exchange_close_mark",
            "on_exchange_close_after_final_exit",
            "off_exchange_cash",
            "total_equity",
            "on_exchange_high_upper_bound",
            "confirmed_open_breach",
            "confirmed_close_breach",
            "possible_high_bound_breach",
            "episode_id",
            "final_exit_fee",
        ],
        daily_rows,
    )
    _write_csv(
        OUT_DIR / "trades.csv",
        [
            "cost_rate",
            "strategy",
            "date",
            "symbol",
            "side",
            "qty",
            "price",
            "notional",
            "fee",
            "reason",
            "cash_after",
            "qty_after",
        ],
        trade_rows,
    )
    _write_csv(
        OUT_DIR / "monthly_returns.csv",
        ["cost_rate", "strategy", "month", "start_equity", "end_equity", "pnl", "net_return"],
        monthly_rows,
    )
    print(f"wrote spot screen outputs to {OUT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
