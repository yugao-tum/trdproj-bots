"""Independent Decimal collateral diagnostics; no network or execution."""
from decimal import Decimal as D

def equity(cash, qty, entry, mark, funding=0):
    return D(cash) + D(qty) * (D(entry) - D(mark)) + D(funding)

def prefix_bounds(start, payments):
    total = D(start); vals = [total]
    for amount in payments:
        total += D(amount); vals.append(total)
    return min(vals), max(vals), total

def high_time_bounds(cash, qty, entry, high, funding_min, funding_max, full_notional=False):
    # Actual timing of the daily high is unknown. Funding prefix is bounded;
    # these endpoints are bounds, not simultaneous observed quotes.
    low = equity(cash, qty, entry, high, funding_min)
    high_bound = equity(cash, qty, entry, high, funding_max)
    if full_notional:
        low -= D(qty)*D(high); high_bound -= D(qty)*D(high)
    status = ('guaranteed_negative_at_recorded_high' if high_bound < 0 else
              'ambiguous_negative_possible' if low < 0 else
              'nonnegative_lower_bound_not_liquidation_proof')
    return low, high_bound, status

def venue_bounds(cash, qty, entry, spot_low, spot_high, mark_low, mark_high, funding_min, funding_max):
    # Asynchronous extrema are an envelope, never a realized venue max/min.
    constant = D(cash) + D(qty)*D(entry)
    lo = constant+D(funding_min)+D(qty)*(D(spot_low)-D(mark_high))
    hi = constant+D(funding_max)+D(qty)*(D(spot_high)-D(mark_low))
    return lo, hi
