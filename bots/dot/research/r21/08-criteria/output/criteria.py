"""Offline evidence interpretation only. No network, account, order or position creation."""
from decimal import Decimal

D = Decimal


def summarize(events, *, entry_ms, no_gaps_confirmed=False, data_errors=(),
              observed_margin_equity=None, entry_cost=None, exit_cost=None,
              executable_net_pnl=None, valuation_time_ms=None):
    """Events: unique economic funding keys, actual timestamps, signed cash strings.

    Evaluate a descriptive checkpoint without annualization or a strategy verdict.
    Source caller owns schema/quantity verification and explicit gap reconciliation.
    """
    rows = {}
    errors = list(data_errors)
    duplicates = 0
    excluded = 0
    for e in events:
        ts = e['funding_time_ms']
        if not isinstance(ts, int):
            raise ValueError('Actual integer millisecond timestamp required')
        if ts <= entry_ms:
            excluded += 1
            continue
        cash = D(e['cash_usdt'])
        if not cash.is_finite():
            raise ValueError('Finite cash required')
        key = str(e['event_key'])
        if key != f'ETHUSDT:{ts}':
            raise ValueError('Key must identify the exact ETH funding timestamp')
        value = (ts, cash)
        if key in rows:
            if rows[key] != value:
                errors.append('conflicting_event:' + key)
            else:
                duplicates += 1
            continue
        rows[key] = value
    ordered = sorted(rows.values(), key=lambda x: x[0])
    first = ordered[:30]
    cash = sum((c for _, c in first), D(0))
    pos = sum((c for _, c in first if c > 0), D(0))
    negatives = sum(c < 0 for _, c in first)
    top = sum(sorted((c for _, c in first if c > 0), reverse=True)[:3], D(0))
    costs_known = entry_cost is not None and exit_cost is not None
    cost = D(entry_cost) + D(exit_cost) if costs_known else None
    if cost is not None and (not cost.is_finite() or cost < 0):
        raise ValueError('Nonnegative finite assumed cost required')
    gap = max(D(0), cost - cash) if cost is not None else None
    margin_bad = observed_margin_equity is not None and D(observed_margin_equity) <= 0
    net = None if executable_net_pnl is None else D(executable_net_pnl)
    if net is not None and (not net.is_finite() or not isinstance(valuation_time_ms, int) or valuation_time_ms <= entry_ms):
        raise ValueError('Finite net value requires explicit post-entry quote valuation timestamp')
    return {
        'unique_post_entry_events': len(rows),
        'initial_window_events': len(first),
        'initial_window_complete': len(first) == 30 and no_gaps_confirmed and not errors,
        'count_definition': 'Distinct actual funding settlement events; not IID observations',
        'excluded_at_or_before_entry': excluded,
        'duplicate_copies_ignored': duplicates,
        'data_errors': errors,
        'actual_observed_funding_conditional_cash_usdt': str(cash),
        'negative_funding_count': negatives,
        'negative_funding_share': str(D(negatives) / len(first)) if first else None,
        'top_three_positive_payment_share': str(top / pos) if pos > 0 else None,
        'assumed_full_entry_and_exit_cost_usdt': str(cost) if cost is not None else None,
        'funding_only_cost_recovery_gap_usdt': str(gap) if gap is not None else None,
        'break_even_days': None,
        'annualized_return': None,
        'quoted_exit_net_pnl_usdt': str(net) if net is not None else None,
        'quoted_exit_valuation_time_ms': valuation_time_ms if net is not None else None,
        'quote_value_is_exact_30th_settlement_value': False,
        'nonannualized_return_total5000': str(net / D(5000)) if net is not None else None,
        'nonannualized_return_venue2500': str(net / D(2500)) if net is not None else None,
        'feasible_path_invalidated_by_nonpositive_margin': margin_bad,
        'later_values_require_counterfactual_label': margin_bad,
        'initial_window_forces_stop': False,
        'qualified': False,
        'interpretation': 'Descriptive conditional evidence; short-window losses do not by themselves disprove multi-year carry',
    }
