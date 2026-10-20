"""Frozen r19 probability-only model. No trades, outcomes, network or parameter search."""
from datetime import date, datetime
from decimal import Decimal


def timestamp(v):
    if isinstance(v, (int, float)):
        from datetime import timezone
        return datetime.fromtimestamp(v, timezone.utc)
    t = datetime.fromisoformat(v.replace('Z', '+00:00'))
    if t.tzinfo is None:
        raise ValueError('naive timestamp prohibited')
    return t


def estimate(rows, strike, op, minimum):
    n = len(rows)
    k = sum(Decimal(str(r['passenger_count'])) > strike if op == 'gt' else
            Decimal(str(r['passenger_count'])) >= strike for r in rows)
    return {'n': n, 'k': k, 'p': (k + .5) / (n + 1) if n >= minimum else None,
            'feature_dates': [r['target_date'] for r in rows],
            'feature_availability_ts': [r['settlement_ts'] for r in rows],
            'latest_feature_available_ts': max((r['settlement_ts'] for r in rows), key=timestamp, default=None)}


def predict(market, labels):
    out = {k: market.get(k) for k in ('ticker', 'target_date', 'split', 'decision_ts', 'operator', 'strike')}
    reasons = list(market.get('exclusion_reasons', []))
    if not market.get('time_eligible', False):
        reasons.append('market_time_or_rule_ineligible')
    op = market.get('operator')
    try:
        strike = Decimal(str(market['strike']))
        if not strike.is_finite() or op not in ('gt', 'gte'):
            raise ValueError()
        target = date.fromisoformat(market['target_date'])
        decision = timestamp(market['decision_ts'])
    except (KeyError, TypeError, ValueError, ArithmeticError):
        reasons.append('invalid_market_inputs')
        out.update(main=None, baseline_28=None, baseline_half=.5, no_trade_reasons=sorted(set(reasons)), model_eligible=False)
        return out
    eligible = []
    seen = set()
    for row in labels:
        if not row.get('label_eligible', False):
            continue
        d = date.fromisoformat(row['target_date'])
        # Exclude current/future labels before touching their values or settlement time.
        if (target - d).days < 7:
            continue
        if timestamp(row['settlement_ts']) >= decision:
            continue
        if d in seen:
            raise ValueError('duplicate eligible label date: ' + str(d))
        seen.add(d)
        value = Decimal(str(row['passenger_count']))
        if not value.is_finite() or value < 0 or value != value.to_integral_value():
            raise ValueError('invalid eligible passenger count')
        eligible.append(row)
    eligible.sort(key=lambda r: r['target_date'], reverse=True)
    same = [r for r in eligible if date.fromisoformat(r['target_date']).weekday() == target.weekday()][:8]
    main = estimate(same, strike, op, 4)
    baseline = estimate(eligible[:28], strike, op, 1)
    market_ineligible = bool(reasons)
    if main['n'] < 4:
        reasons.append('fewer_than_four_eligible_same_weekday_labels')
    # Diagnostic counts can survive market exclusion, but official probabilities cannot.
    if market_ineligible:
        main['p'] = None
        baseline['p'] = None
    out.update(main=main, baseline_28=baseline, baseline_half=.5,
               no_trade_reasons=sorted(set(reasons)), model_eligible=not reasons,
               trade_status='not_evaluated_probability_stage' if not reasons else 'no_trade',
               availability_assumption='Exchange settlement_ts used as public availability proxy; API first-publication vintage not proven; not TSA first vintage.')
    return out


def predict_all(markets, labels):
    if len(markets) != 79 or len({m['target_date'] for m in markets}) != 79:
        raise ValueError('frozen universe must contain exactly 79 distinct target dates')
    ordered = sorted(markets, key=lambda m: m['target_date'])
    for i, m in enumerate(ordered):
        expected = 'development' if i < 39 else 'holdout'
        # Date boundary and fixed membership are independent of data availability.
        if (m['target_date'] <= '2021-08-28') != (i < 39):
            raise ValueError('frozen date boundary mismatch')
        if m.get('split') not in (expected, 'dev' if i < 39 else 'holdout'):
            raise ValueError('split mismatch')
    return [predict(m, labels) for m in ordered]
