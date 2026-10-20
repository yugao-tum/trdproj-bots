"""Independent offline quote checks. No networking, order, account or wallet API."""
from decimal import Decimal, InvalidOperation, ROUND_FLOOR
from math import gcd

D=Decimal
class QuoteError(ValueError): pass

def dec(value):
    try: x=D(str(value))
    except (InvalidOperation, ValueError): raise QuoteError('invalid_decimal')
    if not x.is_finite(): raise QuoteError('nonfinite_decimal')
    return x

def common_step(*steps):
    values=[dec(x) for x in steps]
    if not values or any(x<=0 for x in values): raise QuoteError('invalid_step')
    scale=10**max(0,max(-x.as_tuple().exponent for x in values))
    integers=[int(x*scale) for x in values]
    lcm=1
    for n in integers: lcm=lcm*n//gcd(lcm,n)
    return D(lcm)/D(scale)

def floor_quantity(quantity, step):
    q,s=dec(quantity),dec(step)
    if q<0 or s<=0: raise QuoteError('invalid_quantity_or_step')
    return (q/s).to_integral_value(rounding=ROUND_FLOOR)*s

def validate_book(book):
    if book.get('symbol')!='ETHUSDT': raise QuoteError('wrong_symbol')
    normalized={}
    for side in ('bids','asks'):
        rows=book.get(side)
        if not rows: raise QuoteError('empty_depth')
        parsed=[]
        for row in rows:
            if len(row)!=2: raise QuoteError('bad_level')
            p,q=map(dec,row)
            if p<=0 or q<=0: raise QuoteError('nonpositive_level')
            parsed.append((p,q))
        prices=[p for p,q in parsed]
        desired=sorted(prices,reverse=(side=='bids'))
        if prices!=desired or len(set(prices))!=len(prices): raise QuoteError('unsorted_or_duplicate_depth')
        normalized[side]=parsed
    if normalized['bids'][0][0]>=normalized['asks'][0][0]: raise QuoteError('crossed_or_locked_book')
    return normalized

def vwap(book, side, quantity):
    if side not in ('bids','asks'): raise QuoteError('invalid_side')
    q=dec(quantity)
    if q<=0: raise QuoteError('nonpositive_quantity')
    levels=validate_book(book)[side]
    remaining=q; cash=D(0); used=0
    for price,available in levels:
        take=min(remaining,available); cash+=take*price; remaining-=take; used+=1
        if remaining==0: break
    if remaining: raise QuoteError('insufficient_depth')
    return {'quantity':q,'notional':cash,'vwap':cash/q,'levels_used':used}

def milliseconds(value):
    if isinstance(value,bool) or not isinstance(value,int) or not 10**12<=value<10**13:
        raise QuoteError('timestamp_not_epoch_milliseconds')
    return value

def check_pair(spot,perp,now_ms,lock_ms):
    now,lock=milliseconds(now_ms),milliseconds(lock_ms)
    bounds=[]; event_known=[]
    for book in (spot,perp):
        validate_book(book)
        start,end=milliseconds(book['request_start_ms']),milliseconds(book['response_end_ms'])
        if start>end: raise QuoteError('reversed_request_interval')
        if start<lock: raise QuoteError('pre_lock_observation')
        if end>now or now-end>5000: raise QuoteError('stale_or_future_response')
        event=book.get('exchange_time_ms')
        if event is not None:
            event=milliseconds(event)
            if start-event>5000: raise QuoteError('stale_exchange_event')
            if event>end+1000: raise QuoteError('future_exchange_event')
        event_known.append(event is not None); bounds.append((start,end))
    envelope=max(x[1] for x in bounds)-min(x[0] for x in bounds)
    if envelope>5000: raise QuoteError('pair_interval_envelope_exceeds_5s')
    return {'interval_envelope_ms':envelope,'exchange_time_known':event_known,
            'atomic_snapshot':False,'own_fill_proven':False,
            'event_freshness_fully_observable':all(event_known)}

def budget_quantity(spot, budget, cost, step):
    """Conservative policy: do not shrink merely to fit visible capacity."""
    b,c,s=dec(budget),dec(cost),dec(step)
    if b<=0 or c<0 or s<=0: raise QuoteError('invalid_budget_cost_step')
    levels=validate_book(spot)['asks']
    upper=floor_quantity(b/(levels[0][0]*(1+c)),s)
    if upper<=0: raise QuoteError('zero_quantity')
    # Upper bound capacity required first; this is deliberately conservative.
    if sum(q for p,q in levels)<upper: raise QuoteError('insufficient_full_budget_depth')
    lo,hi=0,int(upper/s)
    while lo<hi:
        mid=(lo+hi+1)//2
        if vwap(spot,'asks',D(mid)*s)['notional']*(1+c)<=b: lo=mid
        else: hi=mid-1
    if not lo: raise QuoteError('zero_quantity')
    return D(lo)*s

def validate_leg_filters(quantity, notional, filters):
    q,n=dec(quantity),dec(notional)
    required=('stepSize','minQty','maxQty','minNotional')
    if any(k not in filters or filters[k] is None for k in required): raise QuoteError('missing_filter')
    step=dec(filters['stepSize'])
    if step<=0 or q!=floor_quantity(q,step): raise QuoteError('quantity_off_grid')
    if q<dec(filters['minQty']) or q>dec(filters['maxQty']): raise QuoteError('quantity_outside_filter')
    if n<dec(filters['minNotional']): raise QuoteError('notional_below_filter')
    if filters.get('maxNotional') is not None and n>dec(filters['maxNotional']): raise QuoteError('notional_above_filter')
    return True
