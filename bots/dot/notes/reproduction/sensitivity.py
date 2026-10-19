#!/usr/bin/env python3
"""Half-capital sensitivity and passive risk benchmarks for frozen spot screen v1.

Read-only local input; no network, trading, keys, wallets, or paid data.
Default output is the package-local results/spot-halfcap directory.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import sys
sys.dont_write_bytecode = True
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Sequence


WORKDIR = Path(__file__).resolve().parent
FROZEN_DIR = WORKDIR
FROZEN_PATH = FROZEN_DIR / "spot_screen.py"
DEFAULT_CSV = WORKDIR / "inputs" / "spot_daily.csv"
REFERENCE_ORIGINAL_DIR = WORKDIR / "results" / "spot-screen"
OUT_DIR = WORKDIR / "results" / "spot-halfcap"

FROZEN_SPOT_SCREEN_SHA256 = "8e56d8e5c2e73c97710c795ee11a1fbdf86f6d5a2fac1f3688160d68160b3d8c"
EXPECTED_CSV_SHA256 = "a008fbd0514f4d01bd477fc008de9fb24b8dfae5e83ebda2ced8bbf2e89bcf0a"


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


if _sha256_file(FROZEN_PATH) != FROZEN_SPOT_SCREEN_SHA256:
    raise RuntimeError("frozen spot_screen.py SHA256 mismatch")

_spec = importlib.util.spec_from_file_location("frozen_spot_screen", FROZEN_PATH)
if _spec is None or _spec.loader is None:
    raise RuntimeError("cannot load frozen spot_screen.py")
frozen = importlib.util.module_from_spec(_spec)
sys.modules["frozen_spot_screen"] = frozen
_spec.loader.exec_module(frozen)

Bar = frozen.Bar
SYMBOLS = frozen.SYMBOLS
DATA_START = frozen.DATA_START
DATA_END = frozen.DATA_END
SIM_START = frozen.SIM_START
SIM_END = frozen.SIM_END
OOS_START = frozen.OOS_START

CAPITAL_USDT = 5000.0
VENUE_START_USDT = 1250.0
OFF_EXCHANGE_CASH_USDT = 3750.0
POSITION_CAP_USDT = 1100.0
TARGET_FRACTION = 0.9
COST_RATES = (0.003, 0.006)
STUDY_DIAGNOSTIC_LIMIT_USDT = 2500.0
EPS = 1e-9

MECHANISMS = ("C21", "C22", "C23", "C24")
BENCHMARKS = ("SOL_HODL", "EW_HODL")
VARIANTS = MECHANISMS + BENCHMARKS

BENCHMARK_PAIR = {
    "C21": "SOL_HODL",
    "C22": "EW_HODL",
    "C23": "SOL_HODL",
    "C24": "EW_HODL",
    "SOL_HODL": None,
    "EW_HODL": None,
}

VARIANT_DESCRIPTIONS = {
    "C21": "C21.screen-v1.halfcap: frozen C21 rule from v1; SOL versus cash; Monday open; 1250 venue and 1100 target.",
    "C22": "C22.screen-v1.halfcap: frozen C22 rule from v1; BTC/ETH/SOL 60-day momentum; Monday open; 1250 venue and 1100 target.",
    "C23": "C23.screen-v1.halfcap: frozen C23 rule from v1; SOL simple 14-day mean-change RSI, not Wilder; daily next open; 1250 venue and 1100 target.",
    "C24": "C24.screen-v1.halfcap: frozen C24 rule from v1; BTC/ETH/SOL equal weight; Monday rebalance; 1250 venue and 1100 target.",
    "SOL_HODL": "Passive risk benchmark: initial 1100 notional SOL buy at 2024-01-01 open; hold; exit at 2026-09-30 close; no rebalance.",
    "EW_HODL": "Passive risk benchmark: initial 1100 notional split equally across BTC/ETH/SOL at 2024-01-01 open; hold; exit at 2026-09-30 close; no rebalance.",
}


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


@dataclass
class HalfCapPortfolio:
    cost_rate: float
    cash: float = VENUE_START_USDT
    qty: dict[str, float] = field(default_factory=lambda: {symbol: 0.0 for symbol in SYMBOLS})
    trades: list[Trade] = field(default_factory=list)
    buy_shrunk: int = 0
    cash_min: float = field(init=False)
    negative_cash_seen: bool = False
    negative_qty_seen: bool = False
    episodes: list[dict[str, Any]] = field(default_factory=list)
    episode_counter: int = 0
    active_episode: int | None = None
    episode_start: date | None = None
    entry_date: date | None = None

    def __post_init__(self) -> None:
        self.cash_min = self.cash

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


def capital_marks(
    portfolio: HalfCapPortfolio,
    opens: dict[str, float],
    closes: dict[str, float],
    highs: dict[str, float],
) -> dict[str, Any]:
    open_mark = portfolio.cash + sum(
        portfolio.qty[symbol] * opens[symbol]
        for symbol in SYMBOLS
        if portfolio.qty[symbol] > EPS
    )
    close_mark = portfolio.cash + sum(
        portfolio.qty[symbol] * closes[symbol]
        for symbol in SYMBOLS
        if portfolio.qty[symbol] > EPS
    )
    high_upper_bound = portfolio.cash + sum(
        portfolio.qty[symbol] * highs[symbol]
        for symbol in SYMBOLS
        if portfolio.qty[symbol] > EPS
    )
    return {
        "open_mark": open_mark,
        "close_mark": close_mark,
        "high_upper_bound": high_upper_bound,
        "confirmed_open_breach": open_mark > STUDY_DIAGNOSTIC_LIMIT_USDT + EPS,
        "confirmed_close_breach": close_mark > STUDY_DIAGNOSTIC_LIMIT_USDT + EPS,
        "possible_high_bound_breach": high_upper_bound > STUDY_DIAGNOSTIC_LIMIT_USDT + EPS,
        "study_strict_diagnostic_limit_usdt": STUDY_DIAGNOSTIC_LIMIT_USDT,
    }


def _assert_legal(portfolio: HalfCapPortfolio) -> None:
    if portfolio.negative_cash_seen or portfolio.negative_qty_seen:
        raise RuntimeError("negative cash or quantity was seen")
    if portfolio.cash < -EPS:
        raise RuntimeError("negative final cash")
    if any(quantity > EPS for quantity in portfolio.qty.values()):
        raise RuntimeError("final portfolio still holds positions")


def _validate_simulation(simulation: dict[str, Any]) -> None:
    for row in simulation["daily"]:
        expected = row["cash"] + row["holdings_close"] + OFF_EXCHANGE_CASH_USDT
        if abs(row["total_equity"] - expected) > 1e-6:
            raise RuntimeError("daily equity identity failed")
        if row["cash"] < -EPS:
            raise RuntimeError("negative daily cash")
        if row["holdings_close"] < -EPS:
            raise RuntimeError("negative daily holdings")
    if simulation["daily"]:
        last = simulation["daily"][-1]
        if last["holdings_close"] > EPS:
            raise RuntimeError("final holdings not liquidated")
        if abs(last["total_equity"] - (last["on_exchange_close_after_final_exit"] + OFF_EXCHANGE_CASH_USDT)) > 1e-6:
            raise RuntimeError("final equity identity failed")


def _open_prices(bars: dict[str, list[Bar]], index: int) -> dict[str, float]:
    return {symbol: bars[symbol][index].open for symbol in SYMBOLS}


def _close_prices(bars: dict[str, list[Bar]], index: int) -> dict[str, float]:
    return {symbol: bars[symbol][index].close for symbol in SYMBOLS}


def _high_prices(bars: dict[str, list[Bar]], index: int) -> dict[str, float]:
    return {symbol: bars[symbol][index].high for symbol in SYMBOLS}


def simulate_mechanism(
    strategy: str,
    bars: dict[str, list[Bar]],
    dates: list[date],
    cost_rate: float,
    *,
    start: date = SIM_START,
    end: date = SIM_END,
) -> dict[str, Any]:
    if strategy not in MECHANISMS:
        raise ValueError(f"unknown mechanism {strategy}")
    start_index = dates.index(start)
    end_index = dates.index(end)
    closes = {symbol: [bar.close for bar in bars[symbol]] for symbol in SYMBOLS}
    portfolio = HalfCapPortfolio(cost_rate=cost_rate)
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
        pre_open_marks = capital_marks(portfolio, opens, opens, opens)
        if pre_open_marks["confirmed_open_breach"]:
            confirmed_open_breach_days += 1
        max_open_on_exchange = max(max_open_on_exchange, pre_open_marks["open_mark"])

        if strategy == "C21" and day.weekday() == 0:
            selected = ["SOLUSDT"] if frozen.c21_signal(closes["SOLUSDT"], index) else []
            portfolio.rebalance(day, opens, selected, "C21 weekly long" if selected else "C21 weekly cash")
        elif strategy == "C22" and day.weekday() == 0:
            target = frozen.c22_target(closes, index)
            selected = [target] if target else []
            portfolio.rebalance(day, opens, selected, "C22 weekly momentum" if selected else "C22 weekly cash")
        elif strategy == "C23":
            if portfolio.has_position():
                rsi = frozen.simple_rsi(closes["SOLUSDT"][:index], 14)
                age = (day - portfolio.entry_date).days if portfolio.entry_date else 0
                if (rsi is not None and rsi > 50.0) or age >= 14:
                    portfolio.rebalance(day, opens, [], "C23 exit")
            else:
                rsi = frozen.simple_rsi(closes["SOLUSDT"][:index], 14)
                if rsi is not None and rsi < 30.0:
                    portfolio.rebalance(day, opens, ["SOLUSDT"], "C23 entry")
        elif strategy == "C24" and day.weekday() == 0:
            portfolio.rebalance(day, opens, list(SYMBOLS), "C24 weekly equal-weight")

        portfolio.update_episode(day)
        close_prices = _close_prices(bars, index)
        high_prices = _high_prices(bars, index)
        close_marks = capital_marks(portfolio, opens, close_prices, high_prices)
        if close_marks["confirmed_close_breach"]:
            confirmed_close_breach_days += 1
        if close_marks["possible_high_bound_breach"]:
            possible_high_bound_breach_days += 1
        max_close_on_exchange = max(max_close_on_exchange, close_marks["close_mark"])
        max_high_upper_bound = max(max_high_upper_bound, close_marks["high_upper_bound"])

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
        total_equity = on_exchange_close_after_final_exit + OFF_EXCHANGE_CASH_USDT
        daily.append(
            {
                "date": day,
                "cash": portfolio.cash,
                "holdings_close": holdings_close,
                "on_exchange_open_pretrade_mark": pre_open_marks["open_mark"],
                "on_exchange_close_mark": close_marks["close_mark"],
                "on_exchange_close_after_final_exit": on_exchange_close_after_final_exit,
                "off_exchange_cash": OFF_EXCHANGE_CASH_USDT,
                "total_equity": total_equity,
                "on_exchange_high_upper_bound": close_marks["high_upper_bound"],
                "confirmed_open_breach": pre_open_marks["confirmed_open_breach"],
                "confirmed_close_breach": close_marks["confirmed_close_breach"],
                "possible_high_bound_breach": close_marks["possible_high_bound_breach"],
                "episode_id": portfolio.active_episode or 0,
                "final_exit_fee": final_exit_fee,
            }
        )

    _assert_legal(portfolio)
    simulation = {
        "variant": strategy,
        "kind": "mechanism",
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
    _validate_simulation(simulation)
    return simulation


def simulate_benchmark(
    label: str,
    bars: dict[str, list[Bar]],
    dates: list[date],
    cost_rate: float,
    *,
    start: date = SIM_START,
    end: date = SIM_END,
) -> dict[str, Any]:
    if label not in BENCHMARKS:
        raise ValueError(f"unknown benchmark {label}")
    start_index = dates.index(start)
    end_index = dates.index(end)
    portfolio = HalfCapPortfolio(cost_rate=cost_rate)
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
        pre_open_marks = capital_marks(portfolio, opens, opens, opens)
        if pre_open_marks["confirmed_open_breach"]:
            confirmed_open_breach_days += 1
        max_open_on_exchange = max(max_open_on_exchange, pre_open_marks["open_mark"])

        if index == start_index:
            selected = ["SOLUSDT"] if label == "SOL_HODL" else list(SYMBOLS)
            portfolio.rebalance(day, opens, selected, f"{label} initial buy")

        portfolio.update_episode(day)
        close_prices = _close_prices(bars, index)
        high_prices = _high_prices(bars, index)
        close_marks = capital_marks(portfolio, opens, close_prices, high_prices)
        if close_marks["confirmed_close_breach"]:
            confirmed_close_breach_days += 1
        if close_marks["possible_high_bound_breach"]:
            possible_high_bound_breach_days += 1
        max_close_on_exchange = max(max_close_on_exchange, close_marks["close_mark"])
        max_high_upper_bound = max(max_high_upper_bound, close_marks["high_upper_bound"])

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
        total_equity = on_exchange_close_after_final_exit + OFF_EXCHANGE_CASH_USDT
        daily.append(
            {
                "date": day,
                "cash": portfolio.cash,
                "holdings_close": holdings_close,
                "on_exchange_open_pretrade_mark": pre_open_marks["open_mark"],
                "on_exchange_close_mark": close_marks["close_mark"],
                "on_exchange_close_after_final_exit": on_exchange_close_after_final_exit,
                "off_exchange_cash": OFF_EXCHANGE_CASH_USDT,
                "total_equity": total_equity,
                "on_exchange_high_upper_bound": close_marks["high_upper_bound"],
                "confirmed_open_breach": pre_open_marks["confirmed_open_breach"],
                "confirmed_close_breach": close_marks["confirmed_close_breach"],
                "possible_high_bound_breach": close_marks["possible_high_bound_breach"],
                "episode_id": portfolio.active_episode or 0,
                "final_exit_fee": final_exit_fee,
            }
        )

    _assert_legal(portfolio)
    simulation = {
        "variant": label,
        "kind": "benchmark",
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
    _validate_simulation(simulation)
    return simulation


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
        "cash": VENUE_START_USDT,
        "holdings_close": 0.0,
        "on_exchange_close_mark": VENUE_START_USDT,
        "on_exchange_close_after_final_exit": VENUE_START_USDT,
        "off_exchange_cash": OFF_EXCHANGE_CASH_USDT,
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
    final_exit_fee = sum(trade.fee for trade in period_trades if trade.reason == "final close liquidation")
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
        "final_exit_fee_usdt": final_exit_fee,
        "months": len(monthly),
        "episodes_started": episodes_started,
        "monthly_returns": monthly,
        "best_profitable_month": best_month["month"] if best_month else None,
        "best_month_pnl_usdt": best_month["pnl"] if best_month else 0.0,
        "net_ex_best_month_usdt": net_ex_best,
        "return_ex_best_month_on_start_equity": net_ex_best / base_equity if base_equity else None,
        "capital_bound_diagnostics": {
            "study_strict_diagnostic_limit_usdt": STUDY_DIAGNOSTIC_LIMIT_USDT,
            "initial_deployed_venue_usdt": VENUE_START_USDT,
            "initial_target_position_cap_usdt": POSITION_CAP_USDT,
            "confirmed_open_breach_days": open_breach_days,
            "confirmed_close_breach_days": close_breach_days,
            "possible_high_bound_breach_days": high_breach_days,
            "max_open_on_exchange_usdt": max_open,
            "max_close_on_exchange_usdt": max_close,
            "max_high_upper_bound_usdt": max_high,
            "confirmed_open_breach": open_breach_days > 0,
            "confirmed_close_breach": close_breach_days > 0,
            "possible_high_bound_breach": high_breach_days > 0,
            "threshold_unchanged": True,
        },
    }


def build_summary(
    bars: dict[str, list[Bar]],
    dates: list[date],
    quality: dict[str, Any],
    hashes: dict[str, str],
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    variants_output: dict[str, Any] = {}
    daily_rows: list[dict[str, Any]] = []
    trade_rows: list[dict[str, Any]] = []
    monthly_rows: list[dict[str, Any]] = []
    comparison_rows: list[dict[str, Any]] = []

    simulations: list[tuple[str, str, float, dict[str, Any]]] = []
    for cost_rate in COST_RATES:
        for variant in MECHANISMS:
            simulations.append((variant, "mechanism", cost_rate, simulate_mechanism(variant, bars, dates, cost_rate)))
        for variant in BENCHMARKS:
            simulations.append((variant, "benchmark", cost_rate, simulate_benchmark(variant, bars, dates, cost_rate)))

    for variant, kind, cost_rate, simulation in simulations:
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
        cost_key = f"{cost_rate:.3f}"
        variants_output.setdefault(
            variant,
            {
                "description": VARIANT_DESCRIPTIONS[variant],
                "kind": kind,
                "benchmark_pair": BENCHMARK_PAIR[variant],
                "scenarios": {},
            },
        )
        variants_output[variant]["scenarios"][cost_key] = {
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
                "final_holdings_zero": all(float(row["holdings_close"]) <= EPS for row in daily[-1:]),
            },
            "capital_bound_diagnostics_full": periods["full"]["capital_bound_diagnostics"],
            "independent_sample": {
                "episodes_total": len(episodes),
                "months_total": len(monthly_full),
                "minimum_30_claim": False,
                "event_correlation_review": "not performed; episodes and months are not automatically independent",
                "note": "Episodes are contiguous invested spells; direct asset switches are not new episodes. Trade legs, bars, and months are not independent results.",
            },
        }
        for row in daily:
            daily_rows.append(
                {
                    "variant": variant,
                    "kind": kind,
                    "cost_rate": cost_key,
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
                    "variant": variant,
                    "kind": kind,
                    "cost_rate": cost_key,
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
                    "variant": variant,
                    "kind": kind,
                    "cost_rate": cost_key,
                    "month": month["month"],
                    "start_equity": month["start_equity"],
                    "end_equity": month["end_equity"],
                    "pnl": month["pnl"],
                    "net_return": month["net_return"],
                }
            )
        for period_name, period in periods.items():
            comparison_rows.append(
                {
                    "variant": variant,
                    "kind": kind,
                    "benchmark_pair": BENCHMARK_PAIR[variant] or "",
                    "cost_rate": cost_key,
                    "period": period_name,
                    "start": period["start"],
                    "end": period["end"],
                    "start_equity_usdt": period["start_equity"],
                    "end_equity_usdt": period["end_equity"],
                    "net_pnl_usdt": period["net_pnl_usdt"],
                    "net_contribution_fixed_5000": period["fixed_5000_return"],
                    "return_on_start_equity": period["total_return_on_start_equity"],
                    "cagr": period["cagr"],
                    "max_drawdown": period["max_drawdown"],
                    "trade_count": period["trade_count"],
                    "fees_usdt": period["fees_usdt"],
                    "notional_traded_usdt": period["notional_traded_usdt"],
                    "episodes_started": period["episodes_started"],
                    "max_open_on_exchange_usdt": period["capital_bound_diagnostics"]["max_open_on_exchange_usdt"],
                    "max_close_on_exchange_usdt": period["capital_bound_diagnostics"]["max_close_on_exchange_usdt"],
                    "max_high_upper_bound_usdt": period["capital_bound_diagnostics"]["max_high_upper_bound_usdt"],
                    "study_strict_diagnostic_limit_usdt": period["capital_bound_diagnostics"]["study_strict_diagnostic_limit_usdt"],
                    "confirmed_open_breach_days": period["capital_bound_diagnostics"]["confirmed_open_breach_days"],
                    "confirmed_close_breach_days": period["capital_bound_diagnostics"]["confirmed_close_breach_days"],
                    "possible_high_bound_breach_days": period["capital_bound_diagnostics"][
                        "possible_high_bound_breach_days"
                    ],
                    "best_profitable_month": period["best_profitable_month"],
                    "best_month_pnl_usdt": period["best_month_pnl_usdt"],
                    "net_ex_best_month_usdt": period["net_ex_best_month_usdt"],
                }
            )

    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    summary = {
        "disclaimer": "Pre-registered half-capital sensitivity and passive risk benchmark; not a profit promise, not a live track record, and not truly unseen OOS.",
        "status": "draft; pending review; pending verification 0; not a live track record",
        "generated_by": "sensitivity.py",
        "implementation_provenance": "Self-written simulator; CLI/report metadata and test fixtures were reviewed before the original execution.",
        "generated_at_utc": generated_at,
        "run_command": "python sensitivity.py --execute",
        "inputs": {
            "script_path": str(Path(__file__).resolve()),
            "script_sha256": _sha256_file(Path(__file__).resolve()),
            "frozen_spot_screen_path": str(FROZEN_PATH),
            "frozen_spot_screen_sha256": FROZEN_SPOT_SCREEN_SHA256,
            "input_csv_path": hashes["csv_path"],
            "input_csv_sha256": hashes["csv_sha256"],
        },
        "data": quality,
        "parameters": {
            "simulation_start": SIM_START.isoformat(),
            "simulation_end": SIM_END.isoformat(),
            "oos_start": OOS_START.isoformat(),
            "data_start_used_only_for_warmup": DATA_START.isoformat(),
            "capital_usdt": CAPITAL_USDT,
            "initial_on_exchange_cash_usdt": VENUE_START_USDT,
            "initial_off_exchange_idle_cash_usdt": OFF_EXCHANGE_CASH_USDT,
            "target_position_cap_usdt": POSITION_CAP_USDT,
            "target_fraction_of_on_exchange_assets": TARGET_FRACTION,
            "study_strict_diagnostic_limit_usdt": STUDY_DIAGNOSTIC_LIMIT_USDT,
            "cost_rates": list(COST_RATES),
            "signal_timing": "prior-day close or earlier; execute at next day's open",
            "final_exit": "forced at 2026-09-30 close with cost",
            "original_v1_parameters": {
                "total_capital_usdt": 5000.0,
                "initial_on_exchange_cash_usdt": 2500.0,
                "initial_off_exchange_idle_cash_usdt": 2500.0,
                "target_position_cap_usdt": 2200.0,
                "target_fraction_of_on_exchange_assets": 0.9,
                "study_strict_diagnostic_limit_usdt": 2500.0,
            },
            "half_capital_scaling": "venue 2500->1250 and target 2200->1100; total capital 5000 and 0.9 NAV constraint unchanged; dynamic diagnostic threshold remains 2500.",
            "parameter_tuning": "none; one pre-registered sensitivity; no post-hoc changes",
        },
        "contributed_capital": {
            "initial_on_exchange_including_fee_buffer_usdt": VENUE_START_USDT,
            "additional_on_exchange_including_fee_buffer_usdt": 0.0,
            "initial_off_exchange_idle_usdt": OFF_EXCHANGE_CASH_USDT,
            "total_contributed_usdt": CAPITAL_USDT,
            "initial_uninvested_on_exchange_buffer_above_target_usdt": VENUE_START_USDT - POSITION_CAP_USDT,
            "fee_policy": "All trading fees are deducted from on-exchange cash. The off-exchange 3750 is never transferred.",
        },
        "guide_interpretation": {
            "text": "GUIDE says roughly 2500 per venue without specifying contributed principal versus dynamic net assets.",
            "sensitivity_note": "This run deploys 1250 to the venue but keeps the guide diagnostic threshold at 2500; 1250 is not a redefinition of the guide cap.",
            "fee_buffer_note": "The 1100 target cap leaves 150 before costs; fees are deducted from on-exchange cash.",
        },
        "capital_bound_definitions": {
            "study_strict_diagnostic_limit_usdt": STUDY_DIAGNOSTIC_LIMIT_USDT,
            "initial_deployed_venue_usdt": VENUE_START_USDT,
            "initial_target_position_cap_usdt": POSITION_CAP_USDT,
            "confirmed_open_lens": "cash plus old positions marked at daily open before any trade; above 2500 is a confirmed open-mark breach.",
            "confirmed_close_lens": "cash plus positions marked at daily close, before end-of-sample forced exit; above 2500 is a confirmed close breach.",
            "possible_high_bound_lens": "cash plus sum(qty*daily high); daily highs across symbols are not simultaneous, so above 2500 is only a possible capital bound breach.",
            "daily_bar_limit": "Daily bars cannot verify intraday margin. This screen is spot-only and has no margin.",
            "tuning": "Thresholds are fixed before running; no post-hoc adjustment to force a pass.",
            "threshold_unchanged": True,
        },
        "benchmarks": {
            "SOL_HODL": {
                "initial_notional_usdt": POSITION_CAP_USDT,
                "initial_weights": {"SOLUSDT": 1.0},
                "entry": "2024-01-01 open",
                "exit": "2026-09-30 close",
                "rebalance": "none after initial buy",
                "cost_rates": list(COST_RATES),
                "paired_mechanisms": ["C21", "C23"],
            },
            "EW_HODL": {
                "initial_notional_usdt": POSITION_CAP_USDT,
                "initial_weights": {symbol: 1.0 / len(SYMBOLS) for symbol in SYMBOLS},
                "entry": "2024-01-01 open",
                "exit": "2026-09-30 close",
                "rebalance": "none after initial buy",
                "cost_rates": list(COST_RATES),
                "paired_mechanisms": ["C22", "C24"],
            },
        },
        "variant_order": list(VARIANTS),
        "variants": variants_output,
        "selection_rule": "No winner selected; all six variants and both cost scenarios are reported in full.",
        "oos_note": "The 2025-01-01 split is an ex post fixed-rule time split, not truly unseen forward data. OOS starts from the 2024-12-31 state and NAV; fixed-5000 contribution and return on actual start NAV are reported separately.",
        "independent_sample_note": "Episodes and months are descriptive only. Trade legs, bars, and months are not independent results; no 30-independent-result claim is made.",
        "limitations": [
            "Daily OHLC cannot prove executable depth or intraday fills; next-open execution is an assumption.",
            "Costs are fixed 0.30%/0.60% per actual leg; no additional slippage model beyond that.",
            "No taxes, funding, borrow, staking, or interest on idle cash.",
            "The 2025+ split is ex post, not truly unseen forward data.",
            "All variants share the same history and assets; they are not independent samples.",
            "Benchmark comparison is descriptive, not factor attribution or an alpha test.",
            "No live trading, wallet, keys, or track record.",
        ],
    }
    return summary, daily_rows, trade_rows, monthly_rows, comparison_rows


def _fmt_pct(value: float | None) -> str:
    return "null" if value is None else f"{100.0 * value:.2f}%"


def _fmt_usdt(value: float | None) -> str:
    return "null" if value is None else f"{value:.2f}"


def _fmt_int(value: int | None) -> str:
    return "null" if value is None else str(value)


def render_markdown(summary: dict[str, Any]) -> str:
    data = summary["data"]
    params = summary["parameters"]
    variants = summary["variants"]
    lines: list[str] = []

    def add(text: str = "") -> None:
        lines.append(text)

    add("# R6 spot 半资本敏感性与被动风险基准")
    add("")
    add("状态：草稿；待核0；由 `sensitivity.py` 在安全审查批准后执行生成。")
    add("")
    add("本报告只覆盖 C21–C24 冻结规则的半资本变体和两个被动风险基准；不新增机制，不更改 v1 原输出，不声称真正未见 OOS。")
    add("")

    add("## 范围与冻结身份")
    add("")
    add("- 机制变体：C21.screen-v1.halfcap、C22.screen-v1.halfcap、C23.screen-v1.halfcap、C24.screen-v1.halfcap。")
    add("- 被动基准：SOL_HODL、EW_HODL；不是新机制，不参与最佳变体选择。")
    add("- 原 v1 输出保持不变；本轮结果只写 `results/spot-halfcap/`。")
    add("- 时期：暖机 2023；模拟 2024-01-01 至 2026-09-30；2024 分段；OOS 标签 2025-01-01 起；全段。")
    add("")

    add("## 数据与预检")
    add("")
    add(f"- CSV：`{summary['inputs']['input_csv_path']}`")
    add(f"- CSV SHA256：`{summary['inputs']['input_csv_sha256']}`")
    add(f"- 行数：{_fmt_int(data.get('rows_read'))}；对齐日期：{_fmt_int(data.get('dates_count'))}；三币对齐：{data.get('aligned')}")
    add("")
    add("| 币种 | 行数 | 缺失 | 重复 | 首日 | 末日 |")
    add("|---|---:|---:|---:|---|---|")
    for symbol in SYMBOLS:
        info = data["symbols"][symbol]
        add(
            f"| {symbol} | {_fmt_int(info.get('rows'))} | {_fmt_int(info.get('missing_count'))} | "
            f"{_fmt_int(info.get('duplicates'))} | {info.get('first')} | {info.get('last')} |"
        )
    add("")
    add("2023 年仅作暖机。OHLC 一致性、UTC 日唯一、原始时间戳、三币日历对齐均由冻结预检执行。")
    add("")

    add("## 资金参数")
    add("")
    add("| 项目 | 原 v1 | 本轮 half-cap |")
    add("|---|---:|---:|")
    original = params["original_v1_parameters"]
    add(f"| 总资本 USDT | {_fmt_usdt(original['total_capital_usdt'])} | {_fmt_usdt(params['capital_usdt'])} |")
    add(f"| 初始场内现金 USDT | {_fmt_usdt(original['initial_on_exchange_cash_usdt'])} | {_fmt_usdt(params['initial_on_exchange_cash_usdt'])} |")
    add(f"| 场外闲置 USDT | {_fmt_usdt(original['initial_off_exchange_idle_cash_usdt'])} | {_fmt_usdt(params['initial_off_exchange_idle_cash_usdt'])} |")
    add(f"| 目标持仓上限 USDT | {_fmt_usdt(original['target_position_cap_usdt'])} | {_fmt_usdt(params['target_position_cap_usdt'])} |")
    add(f"| 目标占场内资产 | {original['target_fraction_of_on_exchange_assets']:.2f} | {params['target_fraction_of_on_exchange_assets']:.2f} |")
    add(f"| 本研究严格动态诊断阈值 USDT | {_fmt_usdt(original['study_strict_diagnostic_limit_usdt'])} | {_fmt_usdt(params['study_strict_diagnostic_limit_usdt'])}（不变） |")
    add(f"| 每边成本情景 | 0.30% / 0.60% | {', '.join(f'{100.0 * rate:.2f}%' for rate in params['cost_rates'])} |")
    add("")
    add("1250 是初始部署预算；2500 仍是本研究严格动态诊断阈值，未改成 1250 或 1100。脚本显式参数化，不做全局字符串替换。")
    add("")

    add("## 冻结规则与基准")
    add("")
    for variant in MECHANISMS:
        add(f"- **{variant}**：{variants[variant]['description']}")
    add("")
    add("| 基准 | 初始名义 USDT | 初始权重 | 再平衡 | 入场 | 出场 | 配对机制 |")
    add("|---|---:|---|---|---|---|---|")
    for label in BENCHMARKS:
        info = summary["benchmarks"][label]
        weights = ", ".join(f"{symbol}={weight:.4f}" for symbol, weight in info["initial_weights"].items())
        pair = ", ".join(info["paired_mechanisms"])
        add(
            f"| {label} | {_fmt_usdt(info['initial_notional_usdt'])} | {weights} | {info['rebalance']} | "
            f"{info['entry']} | {info['exit']} | {pair} |"
        )
    add("")
    add("基准只作风险参照：C21/C23 对 SOL_HODL，C22/C24 对 EW_HODL。基准不参与最佳选择，也不作 Alpha 归因。")
    add("")

    add("## 结果")
    period_titles = {
        "2024": "2024 分段（2024-01-01 至 2024-12-31）",
        "oos_2025": "OOS 时间切分（2025-01-01 至 2026-09-30，事后切分）",
        "full": "全段（2024-01-01 至 2026-09-30）",
    }
    for period_name in ("2024", "oos_2025", "full"):
        add(f"### {period_titles[period_name]}")
        add("")
        add("| 变体 | 成本/边 | 期初NAV | 净PnL | 净贡献/5000 | 对期初NAV | CAGR | 最大回撤 | 交易腿 | 费用 | 本段新开段数 | 最高收盘 | 2500越限日(开/收) |")
        add("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
        for variant in VARIANTS:
            for cost_key in ("0.003", "0.006"):
                period = variants[variant]["scenarios"][cost_key]["periods"][period_name]
                diag = period["capital_bound_diagnostics"]
                add(
                    f"| {variant} | {cost_key} | {_fmt_usdt(period['start_equity'])} | {_fmt_usdt(period['net_pnl_usdt'])} | "
                    f"{_fmt_pct(period['fixed_5000_return'])} | {_fmt_pct(period['total_return_on_start_equity'])} | "
                    f"{_fmt_pct(period['cagr'])} | {_fmt_pct(period['max_drawdown'])} | {_fmt_int(period['trade_count'])} | "
                    f"{_fmt_usdt(period['fees_usdt'])} | {_fmt_int(period['episodes_started'])} | "
                    f"{_fmt_usdt(diag['max_close_on_exchange_usdt'])} | "
                    f"{_fmt_int(diag['confirmed_open_breach_days'])}/{_fmt_int(diag['confirmed_close_breach_days'])} |"
                )
        add("")
    add("净贡献/5000 使用固定总资本分母；对期初NAV 使用该时期实际起始 NAV。OOS 两者不同，不能混分母。")
    add("")

    add("## 资金边界诊断（全段）")
    add("")
    add("| 变体 | 成本/边 | 最高开盘 | 最高收盘 | 最高日高上界 | 可能上界越限日 |")
    add("|---|---:|---:|---:|---:|---:|")
    for variant in VARIANTS:
        for cost_key in ("0.003", "0.006"):
            diag = variants[variant]["scenarios"][cost_key]["periods"]["full"]["capital_bound_diagnostics"]
            add(
                f"| {variant} | {cost_key} | {_fmt_usdt(diag['max_open_on_exchange_usdt'])} | "
                f"{_fmt_usdt(diag['max_close_on_exchange_usdt'])} | {_fmt_usdt(diag['max_high_upper_bound_usdt'])} | "
                f"{_fmt_int(diag['possible_high_bound_breach_days'])} |"
            )
    add("")
    add("确定越限按 2500 的本研究严格动态诊断阈值；多币日高不同步，`sum(qty*high)` 只称可能上界。日线不能验证盘中保证金；本模拟为无保证金现货。1250 部署预算和 1100 目标上限不替换 2500 诊断阈值。")
    add("")

    add("## 独立样本与解释边界")
    add("")
    add("| 变体 | 有仓段总数 | 月份数 | 30独立结果声明 |")
    add("|---|---:|---:|---|")
    for variant in VARIANTS:
        sample = variants[variant]["scenarios"]["0.003"]["independent_sample"]
        add(
            f"| {variant} | {_fmt_int(sample['episodes_total'])} | {_fmt_int(sample['months_total'])} | "
            f"{sample['minimum_30_claim']} |"
        )
    add("")
    add("有仓段是连续持仓区间；直接换币不自动成为新段。交易腿、日线、月数和共享同一段历史都不自动独立；未做事件相关性审查，不宣布 30 个独立结果通过。")
    add("")

    add("## 限制")
    add("")
    for item in summary["limitations"]:
        add(f"- {item}")
    add("")

    add("## 复现与状态")
    add("")
    add("- 运行命令：`python sensitivity.py --execute`")
    add(f"- `sensitivity.py` SHA256：`{summary['inputs']['script_sha256']}`")
    add(f"- 冻结 `spot_screen.py` SHA256：`{summary['inputs']['frozen_spot_screen_sha256']}`")
    add(f"- 输入 CSV SHA256：`{summary['inputs']['input_csv_sha256']}`")
    add("- 单测命令：`python -m unittest -v test_sensitivity.py`")
    add("- 输出：`summary.json`、`R6-SPOT-HALFCAP.csv`、`daily_equity.csv`、`trades.csv`、`monthly_returns.csv`、`data_quality.json`、`manifest.json`。")
    add("")
    add("状态：草稿；待核0；不构成实盘 track record，不声称真正未见 OOS。")
    add("")
    return "\n".join(lines)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True, ensure_ascii=False, default=str)
        handle.write("\n")


def _write_text(path: Path, text: str) -> None:
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(text)


def _write_csv(path: Path, fieldnames: Sequence[str], rows: Sequence[dict[str, Any]]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_outputs(
    summary: dict[str, Any],
    daily_rows: Sequence[dict[str, Any]],
    trade_rows: Sequence[dict[str, Any]],
    monthly_rows: Sequence[dict[str, Any]],
    comparison_rows: Sequence[dict[str, Any]],
) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    _write_json(OUT_DIR / "data_quality.json", summary["data"])
    _write_json(OUT_DIR / "summary.json", summary)
    _write_csv(
        OUT_DIR / "R6-SPOT-HALFCAP.csv",
        [
            "variant",
            "kind",
            "benchmark_pair",
            "cost_rate",
            "period",
            "start",
            "end",
            "start_equity_usdt",
            "end_equity_usdt",
            "net_pnl_usdt",
            "net_contribution_fixed_5000",
            "return_on_start_equity",
            "cagr",
            "max_drawdown",
            "trade_count",
            "fees_usdt",
            "notional_traded_usdt",
            "episodes_started",
            "max_open_on_exchange_usdt",
            "max_close_on_exchange_usdt",
            "max_high_upper_bound_usdt",
            "study_strict_diagnostic_limit_usdt",
            "confirmed_open_breach_days",
            "confirmed_close_breach_days",
            "possible_high_bound_breach_days",
            "best_profitable_month",
            "best_month_pnl_usdt",
            "net_ex_best_month_usdt",
        ],
        comparison_rows,
    )
    _write_csv(
        OUT_DIR / "daily_equity.csv",
        [
            "variant",
            "kind",
            "cost_rate",
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
            "variant",
            "kind",
            "cost_rate",
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
        [
            "variant",
            "kind",
            "cost_rate",
            "month",
            "start_equity",
            "end_equity",
            "pnl",
            "net_return",
        ],
        monthly_rows,
    )
    _write_text(OUT_DIR / "R6-SPOT-HALFCAP.md", render_markdown(summary))
    output_names = [
        "data_quality.json",
        "summary.json",
        "R6-SPOT-HALFCAP.csv",
        "daily_equity.csv",
        "trades.csv",
        "monthly_returns.csv",
        "R6-SPOT-HALFCAP.md",
    ]
    manifest = {
        "generated_at_utc": summary["generated_at_utc"],
        "run_command": summary["run_command"],
        "status": summary["status"],
        "inputs": summary["inputs"],
        "outputs": {name: _sha256_file(OUT_DIR / name) for name in output_names},
        "parameters": summary["parameters"],
        "note": "Output hashes are computed after writing; manifest.json is not self-hashed.",
    }
    _write_json(OUT_DIR / "manifest.json", manifest)


def verify_inputs(csv_path: Path) -> dict[str, str]:
    resolved = csv_path.resolve()
    if not resolved.exists():
        raise OSError(f"CSV not found: {resolved}")
    actual_csv = _sha256_file(resolved)
    if actual_csv != EXPECTED_CSV_SHA256:
        raise RuntimeError(f"input CSV SHA256 mismatch: {actual_csv}")
    if _sha256_file(FROZEN_PATH) != FROZEN_SPOT_SCREEN_SHA256:
        raise RuntimeError("frozen spot_screen.py SHA256 mismatch")
    return {"csv_path": str(resolved), "csv_sha256": actual_csv}


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Half-capital sensitivity for frozen spot screen v1")
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="verify inputs without writing outputs (default)")
    mode.add_argument(
        "--execute",
        action="store_true",
        help="write results; run only after security review approval",
    )
    args = parser.parse_args(argv)
    try:
        hashes = verify_inputs(args.csv)
        bars, dates, quality = frozen.load_and_precheck(args.csv)
    except (OSError, RuntimeError, frozen.DataError) as exc:
        print(f"input verification or precheck failed: {exc}", file=sys.stderr)
        return 2
    if not args.execute:
        print("dry run: frozen inputs verified and data precheck passed; no outputs written")
        print(f"rows_read={quality['rows_read']} dates={quality['dates_count']} aligned={quality['aligned']}")
        print(
            f"variants={' '.join(VARIANTS)} costs={COST_RATES} "
            f"venue={VENUE_START_USDT} target={POSITION_CAP_USDT} diagnostic={STUDY_DIAGNOSTIC_LIMIT_USDT}"
        )
        return 0
    summary, daily_rows, trade_rows, monthly_rows, comparison_rows = build_summary(bars, dates, quality, hashes)
    write_outputs(summary, daily_rows, trade_rows, monthly_rows, comparison_rows)
    print(f"wrote half-cap sensitivity outputs to {OUT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
