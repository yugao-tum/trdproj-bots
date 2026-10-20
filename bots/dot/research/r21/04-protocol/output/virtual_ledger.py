"""Offline hypothetical observation ledger. No network, account or order interface."""
from decimal import Decimal, getcontext, ROUND_FLOOR
from math import gcd
from hashlib import sha256
from copy import deepcopy
import json
getcontext().prec = 50
D = Decimal
CONFIG = {
    'schema': 'r21.virtual-protocol.v1', 'symbol': 'ETHUSDT',
    'total_capital': '5000', 'venue_capital': '2500', 'spot_budget': '1250',
    'primary_cost': '0.003', 'stress_cost': '0.006',
    'max_pair_envelope_ms': 5000, 'max_retrieval_age_ms': 5000,
    'max_exchange_time_ahead_ms': 1000, 'max_exchange_time_age_ms': 5000,
    'quantity_policy': 'maximum_common_grid_quantity_fitting_primary_ask_cost; no depth rescue',
    'funding_policy': 'actual_timestamp_strictly_after_entry; idempotent_exact_key',
    'cost_policy': 'additional_assumed_cost_on_observed_depth_quotes; not actual fee',
    'mode': 'offline_virtual_only', 'rebalance': False, 'transfers': False,
}
def canonical_hash(x):
    return sha256(json.dumps(x, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()
def dec(x):
    v = D(str(x))
    if not v.is_finite(): raise ValueError('nonfinite')
    return v
def txt(x): return format(x, 'f')
def common_step(a, b):
    a, b = dec(a), dec(b)
    if min(a,b) <= 0: raise ValueError('nonpositive quantity grid')
    scale = 10 ** max(0, -a.as_tuple().exponent, -b.as_tuple().exponent)
    ai, bi = int(a*scale), int(b*scale)
    return D(ai // gcd(ai,bi) * bi) / scale
def floor_grid(q, step):
    return (dec(q)/dec(step)).to_integral_value(rounding=ROUND_FLOOR) * dec(step)
def epoch_ms(value):
    if type(value) is not int or not 946684800000 <= value < 4102444800000:
        raise ValueError("timestamp must be integer Unix milliseconds in 2000-2099")
    return value
def levels(book, side):
    if side not in ("bids", "asks"): raise ValueError("invalid book side")
    rows = [(dec(p),dec(q)) for p,q in book.get(side,[])]
    if not rows or any(min(p,q)<=0 for p,q in rows): raise ValueError('empty/nonpositive book')
    prices = [p for p,q in rows]
    if len(set(prices)) != len(prices): raise ValueError('duplicate price level')
    if prices != sorted(prices, reverse=(side=='bids')): raise ValueError('unsorted book')
    return rows
def notional(book, side, quantity):
    q = dec(quantity)
    if q <= 0: raise ValueError('nonpositive quantity')
    left, cash = q, D(0)
    for p,size in levels(book,side):
        take = min(left,size); cash += take*p; left -= take
        if not left: return cash
    raise ValueError('insufficient visible depth')
def validate_pair(spot, perp, now_ms, locked_at_ms=None):
    now_ms=epoch_ms(now_ms)
    if locked_at_ms is not None: locked_at_ms=epoch_ms(locked_at_ms)
    warnings=[]
    for book in (spot,perp):
        if book.get('symbol') != CONFIG['symbol']: raise ValueError('wrong book symbol')
        start,end = epoch_ms(book['request_start_ms']),epoch_ms(book['response_end_ms'])
        if start>end or end>now_ms: raise ValueError('invalid request interval')
        if locked_at_ms is not None and start < locked_at_ms: raise ValueError('quote predates root lock')
        if now_ms-end > CONFIG['max_retrieval_age_ms']: raise ValueError('stale retrieval')
        bids,asks=levels(book,'bids'),levels(book,'asks')
        if bids[0][0] >= asks[0][0]: raise ValueError('crossed or locked book')
        event=book.get('exchange_time_ms')
        if event is None: warnings.append('exchange event time unavailable; retrieval freshness is not event freshness')
        elif epoch_ms(event)>end+CONFIG['max_exchange_time_ahead_ms'] or end-epoch_ms(event)>CONFIG['max_exchange_time_age_ms']:
            raise ValueError('stale/future exchange timestamp')
    if max(b['response_end_ms'] for b in (spot,perp))-min(b['request_start_ms'] for b in (spot,perp))>CONFIG['max_pair_envelope_ms']:
        raise ValueError('pair retrieval envelope exceeds five seconds')
    return sorted(set(warnings))
def validate_filters(f):
    if f.get('symbol')!=CONFIG['symbol']: raise ValueError('wrong filter symbol')
    for name in ('qty_step','min_qty','max_qty','min_notional'):
        if name not in f or dec(f[name])<=0: raise ValueError('missing/nonpositive filter '+name)
    if dec(f['min_qty'])>dec(f['max_qty']): raise ValueError('invalid quantity limits')
def choose_quantity(spot,perp,spot_filter,perp_filter):
    for f in (spot_filter,perp_filter): validate_filters(f)
    step=common_step(spot_filter['qty_step'],perp_filter['qty_step'])
    budget,cost=dec(CONFIG['spot_budget']),dec(CONFIG['primary_cost'])
    upper=floor_grid(budget/(levels(spot,'asks')[0][0]*(1+cost)),step)
    if upper<=0: raise ValueError('budget cannot fund one common lot')
    # Do not silently reduce a target allocation merely because the visible book is shallow.
    notional(spot,'asks',upper)
    lo,hi=0,int(upper/step)
    while lo<hi:
        mid=(lo+hi+1)//2
        if notional(spot,'asks',step*mid)*(1+cost)<=budget: lo=mid
        else: hi=mid-1
    q=step*lo
    if q<=0: raise ValueError('budget cannot fund common lot after depth cost')
    sn,pn=notional(spot,'asks',q),notional(perp,'bids',q)
    for f,n in ((spot_filter,sn),(perp_filter,pn)):
        if not dec(f['min_qty'])<=q<=dec(f['max_qty']): raise ValueError('quantity violates filter')
        if n<dec(f['min_notional']): raise ValueError('minimum notional unmet')
    return q,sn,pn,step

def initialize_virtual(spot,perp,spot_filter,perp_filter,lock,now_ms):
    """Pure value transform. Production caller must supply independently recorded ROOT lock."""
    expected=canonical_hash(CONFIG)
    if lock.get('authorized_by')!='root' or lock.get('entry_authorized') is not True or lock.get('protocol_sha256')!=expected:
        raise ValueError('matching explicit root protocol lock required')
    locked=epoch_ms(lock['locked_at_ms']); now_ms=epoch_ms(now_ms)
    if locked>now_ms: raise ValueError('future lock')
    warnings=validate_pair(spot,perp,now_ms,locked)
    q,sn,pn,step=choose_quantity(spot,perp,spot_filter,perp_filter)
    entry_time=max(spot['response_end_ms'],perp['response_end_ms'])
    accounts={}
    for cost in (CONFIG['primary_cost'],CONFIG['stress_cost']):
        c=dec(cost); sc=sn*(1+c); pf=pn*c
        collateral=dec(CONFIG['venue_capital'])-sc-pf
        if collateral<0: raise ValueError('entry costs exceed venue cash')
        accounts[cost]={'initial_collateral':txt(collateral),'spot_entry_cost':txt(sc),
            'spot_entry_fee':txt(sn*c),'perp_entry_fee':txt(pf),'funding_cash':'0'}
    return {'schema':'r21.virtual-ledger.v1','protocol_sha256':expected,'root_lock':deepcopy(lock),
        'entry':{'entry_time_ms':entry_time,'quantity':txt(q),'common_step':txt(step),
            'entry_reference_id':canonical_hash({'spot':spot,'perp':perp}),
            'spot_notional':txt(sn),'perp_notional':txt(pn),
            'spot_vwap':txt(sn/q),'perp_vwap':txt(pn/q),
            'filter_snapshot_id':canonical_hash({'spot':spot_filter,'perp':perp_filter})},
        'accounts':accounts,'funding_events':{},'last_funding_time_ms':entry_time,
        'warnings':warnings+['hypothetical reference only, not an order, fill, account payment or certified liquidation survival'],
        'position_is_real':False}

def apply_funding(state,payments,observed_as_of_ms):
    """Atomic replay; exact duplicate no-op, conflicting duplicate rejects whole batch."""
    out=deepcopy(state); q=dec(out['entry']['quantity']); entry=epoch_ms(out['entry']['entry_time_ms'])
    observed_as_of_ms=epoch_ms(observed_as_of_ms)
    if observed_as_of_ms<entry: raise ValueError('observation predates entry')
    accepted=duplicates=excluded=0
    for p in sorted(payments,key=lambda x:epoch_ms(x['fundingTime'])):
        if p.get('symbol')!=CONFIG['symbol']: raise ValueError('wrong funding symbol')
        ts=epoch_ms(p['fundingTime']); rate,mark=dec(p['fundingRate']),dec(p['markPrice'])
        if mark<=0 or ts>observed_as_of_ms: raise ValueError('invalid/unobserved funding')
        if ts<=entry: excluded+=1; continue
        key=f"{CONFIG['symbol']}:{ts}"
        ev={'funding_time_ms':ts,'rate':txt(rate),'mark':txt(mark),'cash':txt(q*rate*mark)}
        if key in out['funding_events']:
            old=out['funding_events'][key]
            if any(dec(old[k])!=dec(ev[k]) for k in ('rate','mark','cash')): raise ValueError('conflicting funding duplicate')
            duplicates+=1; continue
        out['funding_events'][key]=ev; accepted+=1
        for a in out['accounts'].values(): a['funding_cash']=txt(dec(a['funding_cash'])+q*rate*mark)
        out['last_funding_time_ms']=max(out['last_funding_time_ms'],ts)
    return out,{'accepted':accepted,'duplicates':duplicates,'excluded_at_or_before_entry':excluded}

def valuation(state,spot_reference,perp_mark,spot_book=None,perp_book=None,now_ms=None):
    """Mark diagnostics and hypothetical close value are distinct; absent quotes return null."""
    q=dec(state['entry']['quantity']); ps=dec(spot_reference); pm=dec(perp_mark)
    if min(ps,pm)<=0: raise ValueError('nonpositive valuation price')
    initial_perp=dec(state['entry']['perp_notional']); results={}; close_inputs=None; quote_error=None
    if spot_book is not None and perp_book is not None:
        try:
            if now_ms is None: raise ValueError('valuation quote evaluation time missing')
            validate_pair(spot_book,perp_book,now_ms)
            close_inputs=(notional(spot_book,'bids',q),notional(perp_book,'asks',q))
        except ValueError as e: quote_error=str(e)
    else: quote_error='paired exit quotes unavailable'
    for cost,a in state['accounts'].items():
        c=dec(cost); funding=dec(a['funding_cash']); margin=dec(a['initial_collateral'])+funding+initial_perp-q*pm
        total=dec(CONFIG['total_capital'])-dec(CONFIG['venue_capital'])+q*ps+margin
        close=None; price_pnl=None; total_cost=None; funding_needed=None
        if close_inputs:
            sn,pn=close_inputs
            close=dec(CONFIG['total_capital'])-dec(CONFIG['venue_capital'])+sn*(1-c)+dec(a['initial_collateral'])+funding+initial_perp-pn-pn*c
            price_pnl=sn-dec(state['entry']['spot_notional'])+initial_perp-pn
            total_cost=dec(a['spot_entry_fee'])+dec(a['perp_entry_fee'])+c*(sn+pn)
            funding_needed=max(D(0),total_cost-price_pnl)
        results[cost]={'margin_equity_mark':txt(margin),'total_equity_mark':txt(total),
            'hypothetical_exit_equity':None if close is None else txt(close),
            'quote_valuation_error':quote_error,'quote_valuation_time_ms':None if close_inputs is None else max(spot_book['response_end_ms'],perp_book['response_end_ms']),
            'maintenance_tier_verified':False,
            'observed_negative_margin':margin<0,'observed_nonpositive_margin':margin<=0,'actual_recorded_funding_conditional_cash':txt(funding),
            'nonfunding_price_pnl':None if price_pnl is None else txt(price_pnl),
            'full_assumed_entry_exit_cost':None if total_cost is None else txt(total_cost),
            'funding_only_cost_recovery_gap':None if total_cost is None else txt(max(D(0),total_cost-funding)),
            'funding_needed_for_break_even_at_current_quotes':None if funding_needed is None else txt(funding_needed),
            'remaining_funding_shortfall_at_current_quotes':None if funding_needed is None else txt(max(D(0),funding_needed-funding)),
            'forecast_break_even_days':None,'short_window_annualized_return':None}
    return {'accounts':results,'is_execution_or_survival_proof':False}

def normalize_public_interface(interface):
    """Adapter for role03 r21.public-quote-interface.v1; does not initialize a ledger."""
    from datetime import datetime
    def ms(s): return int(datetime.fromisoformat(s.replace('Z','+00:00')).timestamp()*1000)
    if interface.get('schema')!='r21.public-quote-interface.v1': raise ValueError('unknown public interface')
    if interface.get('symbol')!=CONFIG['symbol']: raise ValueError('wrong interface symbol')
    if interface.get('spot_status')!='TRADING' or interface.get('futures_status')!='TRADING': raise ValueError('market not reported trading')
    books={}
    for name,b in interface['books'].items():
        books[name]={'symbol':interface['symbol'],'request_start_ms':ms(b['request_utc']),
            'response_end_ms':ms(b['response_utc']),'exchange_time_ms':b.get('exchange_event_time_ms'),
            'bids':deepcopy(b['bids']),'asks':deepcopy(b['asks']),'lastUpdateId':b['lastUpdateId']}
    fs={}
    for name,prefix in (('spot','spot'),('perp','futures')):
        lot=interface[prefix+'_lot_size']; market=interface[prefix+'_market_lot_size']
        # Zero-valued market grid/minimum disables that market constraint, not the LOT_SIZE grid.
        steps=[dec(lot['stepSize'])]+([dec(market['stepSize'])] if dec(market['stepSize'])>0 else [])
        step=steps[0]
        for s in steps[1:]:step=common_step(step,s)
        minima=[dec(lot['minQty'])]+([dec(market['minQty'])] if dec(market['minQty'])>0 else [])
        maxima=[dec(lot['maxQty'])]+([dec(market['maxQty'])] if dec(market['maxQty'])>0 else [])
        minimum=interface['spot_notional_filter']['minNotional'] if name=='spot' else interface['futures_min_notional']['notional']
        fs[name]={'symbol':interface['symbol'],'qty_step':txt(step),'min_qty':txt(max(minima)),
            'max_qty':txt(min(maxima)),'min_notional':minimum,
            'acceptance_verified':False,'dynamic_reference_unverified':True}
    return {'spot':books['spot'],'perp':books['perp'],'spot_filter':fs['spot'],'perp_filter':fs['perp'],
        'source_snapshot_id':canonical_hash(interface),
        'limitation':'Quote-based notional is not spot 5-minute weighted-average acceptance check; no true fill or current/historical rule acceptance certified.'}
