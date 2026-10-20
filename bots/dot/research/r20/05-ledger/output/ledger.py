"""Frozen C19 constant-quantity cash ledger. No network, execution or liquidation model."""
from decimal import Decimal, getcontext
getcontext().prec = 50
D=Decimal
ZERO=D(0)
YEAR_MS=D('31557600000')

def dec(x):
    v=D(str(x))
    if not v.is_finite(): raise ValueError('Nonfinite input')
    return v

def text(x):
    if isinstance(x,D): return format(x,'f')
    if isinstance(x,list): return [text(y) for y in x]
    if isinstance(x,dict): return {k:text(v) for k,v in x.items()}
    return x

def run(prices, payments, budget='1250', cost='0.003', total='5000', venue='2500'):
    if not prices: raise ValueError('No price rows')
    rows=sorted(prices,key=lambda x:int(x['open_time_ms']))
    if len({int(x['open_time_ms']) for x in rows})!=len(rows): raise ValueError('Duplicate price date')
    b,c,t,v=map(dec,(budget,cost,total,venue))
    if not (ZERO<b<v<=t and ZERO<=c<1): raise ValueError('Invalid allocation/cost')
    first,last=rows[0],rows[-1]
    entry,exit=int(first['open_time_ms']),int(last['close_time_ms'])
    if exit<=entry: raise ValueError('Nonpositive window')
    s0,p0,s1,p1=map(dec,(first['spot_open'],first['perp_open'],last['spot_close'],last['perp_close']))
    if min(s0,p0,s1,p1)<=0: raise ValueError('Nonpositive price')
    q=b/(s0*(1+c))
    spot_entry_notional=q*s0; spot_entry_fee=spot_entry_notional*c
    perp_entry_fee=q*p0*c
    collateral=v-b-perp_entry_fee
    if collateral<0: raise ValueError('Entry exceeds cash')
    selected=[]; times=set(); excluded_entry=excluded_outside=0
    for pay in sorted(payments,key=lambda x:int(x['funding_time_ms'])):
        ts=int(pay['funding_time_ms'])
        if ts in times: raise ValueError('Duplicate funding timestamp')
        times.add(ts)
        if ts==entry: excluded_entry+=1; continue
        if not entry<ts<=exit: excluded_outside+=1; continue
        rate,mark=dec(pay['funding_rate']),dec(pay['mark_price'])
        if mark<=0: raise ValueError('Nonpositive settlement mark')
        selected.append((ts,rate,mark))
    cumulative=ZERO; cashflows=[]
    for ts,rate,mark in selected:
        cash=q*rate*mark
        before=collateral+cumulative+q*(p0-mark)
        cumulative+=cash
        after=collateral+cumulative+q*(p0-mark)
        cashflows.append(dict(funding_time_ms=ts,rate=rate,settlement_mark=mark,quantity=q,cashflow=cash,cumulative_funding=cumulative,margin_equity_before=before,margin_equity_after=after,short_notional=q*mark,full_collateral_gap_after=after-q*mark))
    daily=[]; i=0; cf=ZERO
    for row in rows:
        ts=int(row['close_time_ms'])
        while i<len(cashflows) and cashflows[i]['funding_time_ms']<=ts:
            cf+=cashflows[i]['cashflow']; i+=1
        spot_close,perp_close,mark_close=map(dec,(row['spot_close'],row['perp_close'],row['mark_close']))
        if min(spot_close,perp_close,mark_close)<=0: raise ValueError('Nonpositive daily close')
        margin=collateral+cf+q*(p0-mark_close)
        spot_value=q*spot_close
        venue_mark=spot_value+margin
        daily.append(dict(open_time_ms=int(row['open_time_ms']),close_time_ms=ts,spot_value=spot_value,perp_pnl_mark=q*(p0-mark_close),cumulative_funding=cf,margin_equity_mark=margin,venue_equity_mark=venue_mark,total_equity_mark=t-v+venue_mark,full_collateral_gap_mark=margin-q*mark_close,venue_above_strict_2500=venue_mark>v,mark_close=mark_close,perp_close=perp_close))
    spot_exit_notional=q*s1; spot_exit_fee=spot_exit_notional*c
    perp_exit_fee=q*p1*c
    spot_pnl=q*(s1-s0); perp_pnl=q*(p0-p1)
    fees=spot_entry_fee+perp_entry_fee+spot_exit_fee+perp_exit_fee
    margin_exit_before_fee=collateral+cumulative+perp_pnl
    margin_exit=margin_exit_before_fee-perp_exit_fee
    spot_proceeds=spot_exit_notional-spot_exit_fee
    ending=t-v+margin_exit+spot_proceeds
    decomposition=spot_pnl+perp_pnl+cumulative-fees
    residual=(ending-t)-decomposition
    if abs(residual)>D('1e-40'): raise AssertionError('Cash conservation failed')
    years=D(exit-entry)/YEAR_MS
    cagr=(ending/t)**(1/years)-1 if ending>0 else None
    benchmark=t-b+q*s1*(1-c)
    obs_records=[(x['margin_equity_before'],x['funding_time_ms'],'funding_before') for x in cashflows]+[(x['margin_equity_after'],x['funding_time_ms'],'funding_after') for x in cashflows]+[(x['margin_equity_mark'],x['close_time_ms'],'daily_mark_close') for x in daily]+[(margin_exit_before_fee,exit,'exit_before_fee'),(margin_exit,exit,'exit_after_fee')]
    obs=[x[0] for x in obs_records]
    minimum=min(obs_records,key=lambda x:x[0]); negatives=sorted([x for x in obs_records if x[0]<0],key=lambda x:x[1])
    venue_ending=ending-(t-v)
    venue_cagr=(venue_ending/v)**(1/years)-1 if venue_ending>0 else None
    summary=dict(budget=b,cost=c,quantity=q,spot_entry_price=s0,perp_entry_price=p0,spot_exit_price=s1,perp_exit_price=p1,total_initial=t,venue_initial=v,external_cash=t-v,spot_entry_notional=spot_entry_notional,spot_entry_fee=spot_entry_fee,perp_entry_fee=perp_entry_fee,initial_collateral=collateral,initial_short_notional=q*p0,initial_full_collateral_gap=collateral-q*p0,spot_exit_fee=spot_exit_fee,perp_exit_fee=perp_exit_fee,total_fees=fees,spot_price_pnl=spot_pnl,perp_price_pnl=perp_pnl,basis_change_pnl=spot_pnl+perp_pnl,funding_cash=cumulative,ending_margin_cash=margin_exit,spot_exit_cash=spot_proceeds,ending_total_equity=ending,total_net_pnl=ending-t,total_return=(ending-t)/t,total_cagr=cagr,venue_capital_return=(ending-t)/v,venue_capital_cagr=venue_cagr,venue_capital_cagr_denominator=v,spot_budget_return=(ending-t)/b,spot_budget_return_is_not_fully_funded_strategy_return=True,years=years,cash_conservation_residual=residual,entry_time_ms=entry,exit_time_ms=exit,payment_count=len(selected),payments_at_entry_excluded=excluded_entry,payments_outside_window_excluded=excluded_outside,daily_price_rows=len(rows),min_observed_margin_equity=min(obs),min_observed_margin_timestamp_ms=minimum[1],min_observed_margin_event_type=minimum[2],first_observed_negative_margin_timestamp_ms=negatives[0][1] if negatives else None,first_observed_negative_margin_event_type=negatives[0][2] if negatives else None,observed_negative_margin=min(obs)<0,spot_hold_ending_total_equity=benchmark,spot_hold_net_pnl=benchmark-t,hedge_minus_spot_hold=ending-benchmark,classification='Hypothetical complete-path conditional accounting; not feasible-execution certification',survival_status='Independent role06 assessment required; unknown maintenance tier, fills and continuous mark path')
    return text(dict(summary=summary,funding=cashflows,daily=daily))
