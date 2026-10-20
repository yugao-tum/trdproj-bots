"""Offline exact-rational source-based ETH maintenance scenarios; no network or orders."""
import csv, json, hashlib
from pathlib import Path
from fractions import Fraction as F
from decimal import Decimal, localcontext
from datetime import datetime, timezone
OUT=Path(__file__).resolve().parent
C=OUT.parents[3]
R20=C/'workers/r20-proposal'
R21=C/'workers/r21-proposal'
def dec(x):
    with localcontext() as ctx:
        ctx.prec=50
        return str(Decimal(x.numerator)/Decimal(x.denominator))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def funding_prefix_bounds(prior, payments):
    values=[prior]
    for amount in payments: values.append(values[-1]+amount)
    return min(values), max(values), values[-1]
def margin_bound(collateral,q,entry,high,funding_min,rate,close_cost,deduction=F(0)):
    if q<=0 or high<=0 or rate<0 or close_cost<0: raise ValueError('Invalid input')
    notional=q*high
    equity=collateral+q*(entry-high)+funding_min
    maintenance=notional*rate-deduction
    reserve=notional*close_cost
    return {'notional':notional,'equity_lower':equity,'maintenance':maintenance,'close_reserve':reserve,
            'surplus_after_maintenance':equity-maintenance,
            'surplus_after_maintenance_and_close':equity-maintenance-reserve,
            'equity_notional_ratio':equity/notional,
            'ratio_headroom_after_maintenance_and_close':equity/notional-rate-close_cost+deduction/notional}
def run():
    paths={'prices':R20/'04-prices/output/daily_prices.csv','funding':R20/'01-funding/output/funding.csv',
      'r20_daily_bounds':R20/'06-collateral/local-derived/daily-bounds.csv',
      'tables':R21/'01-margin-history/output/tables.json','formula':R21/'02-formula/output/RESULT.json'}
    tables=json.loads(paths['tables'].read_text())
    assert sha(paths['tables'])=='4b0c6b0c3ee63dce8b039946e2f8b3864c8d5d591255a1e4555b07d1801f51ee'
    observed_rates={F(str(row['maintenance_rate'])) for source in tables['sources'] for side in ['before','after'] for row in source['tables'][side] if row['notional_floor_usdt_exclusive']==0}
    assert F('.004') in observed_rates and F('.005') in observed_rates
    prices=[r for r in csv.DictReader(paths['prices'].open()) if r['symbol']=='ETHUSDT']
    funding=[r for r in csv.DictReader(paths['funding'].open()) if r['symbol']=='ETHUSDT']
    prices.sort(key=lambda x:int(x['open_time_ms'])); funding.sort(key=lambda x:int(x['fundingTime']))
    old={(r['scenario_id'],int(r['open_time_ms'])):r for r in csv.DictReader(paths['r20_daily_bounds'].open()) if r['scenario_id'].startswith('ETHUSDT')}
    assert len(prices)==1004 and len(funding)==3012
    entry_time=int(prices[0]['open_time_ms']); end_time=int(prices[-1]['close_time_ms'])
    funding=[r for r in funding if entry_time<int(r['fundingTime'])<=end_time]
    assert len(funding)==3011
    all_rows=[]; scenarios=[]; comparisons=0
    for budget in ['1250','625']:
      for cost in ['0.003','0.006']:
        q=F(budget)/(F(prices[0]['spot_open'])*(1+F(cost)))
        entry=F(prices[0]['perp_open'])
        collateral=F(2500)-F(budget)-q*entry*F(cost)
        sid=f'ETHUSDT_b{budget}_c{cost}'
        day_events={int(p['open_time_ms']):[] for p in prices}
        for f in funding:
            day=int(f['fundingTime'])//86400000*86400000
            day_events[day].append(q*F(f['fundingRate'])*F(f['markPrice']))
        cumulative=F(0); base=[]
        for p in prices:
            t=int(p['open_time_ms'])
            lower,upper,cumulative=funding_prefix_bounds(cumulative,day_events[t])
            for key,value in [('funding_prefix_min',lower),('funding_prefix_max',upper)]:
                assert abs(value-F(old[sid,t][key]))<F('1e-40'); comparisons+=1
            eq=collateral+q*(entry-F(p['mark_high']))+lower
            assert abs(eq-F(old[sid,t]['margin_min_lower']))<F('1e-40'); comparisons+=1
            base.append((p,lower))
        for rate in ['0.004','0.005']:
            rows=[]
            for p,lower in base:
                r=margin_bound(collateral,q,entry,F(p['mark_high']),lower,F(rate),F(cost))
                rows.append({'date_utc':p['date_utc'],'open_time_ms':int(p['open_time_ms']),**r})
                all_rows.append({'scenario_id':sid,'maintenance_rate':rate,'date_utc':p['date_utc'],**{k:dec(v) for k,v in r.items()}})
            def pack(r):return {k:(dec(v) if isinstance(v,F) else v) for k,v in r.items()}
            min_surplus=min(rows,key=lambda r:r['surplus_after_maintenance_and_close'])
            min_ratio=min(rows,key=lambda r:r['ratio_headroom_after_maintenance_and_close'])
            near=next(r for r in rows if r['date_utc']=='2025-08-24')
            scenarios.append({'scenario_id':sid,'spot_budget':budget,'cost':cost,'maintenance_rate_scenario':rate,
                'maintenance_deduction_assumed':'0','quantity':dec(q),'initial_collateral':dec(collateral),
                'daily_count':len(rows),'negative_bound_days_after_maintenance':sum(r['surplus_after_maintenance']<0 for r in rows),
                'negative_bound_days_after_maintenance_and_close':sum(r['surplus_after_maintenance_and_close']<0 for r in rows),
                'minimum_after_maintenance':pack(min(rows,key=lambda r:r['surplus_after_maintenance'])),
                'minimum_after_maintenance_and_close':pack(min_surplus),'minimum_ratio_headroom':pack(min_ratio),
                'exact_minimum_surplus_rational':str(min_surplus['surplus_after_maintenance_and_close']),
                'aug24_2025_near_source':pack(near),'max_daily_high_notional':dec(max(r['notional'] for r in rows)),
                'historical_rule_continuity_proven':False,'actual_liquidation_survival_proven':False})
    result={'schema':'r21.eth.source-maintenance-bounds.v1','created_utc':datetime.now(timezone.utc).isoformat(),
       'classification':'Source-supported constant-rate conditional scenarios; not continuous historical-tier reconstruction or execution certification',
       'eth_allocation_cost_cases':4,'maintenance_comparisons_per_case':2,'scenarios':scenarios,
       'independent_r20_daily_bound_checks':comparisons,'source_urls':[s['url'] for s in tables['sources']],
       'source_hashes':{k:sha(v) for k,v in paths.items()},
       'limits':['0.004 is documented at two announcement events, not verified throughout the full 1004-day interval.',
                 '0.005 is the documented old first-tier comparison, not asserted in force during r20.',
                 'Zero deduction is an explicit assumption; conservative versus actual formula only if actual deduction is nonnegative.',
                 'Daily high paired with minimum chronological funding prefix is a lower bound, not a synchronous observed equity value.',
                 '2025-08-24 is five days after the Aug19 event, but no continuous tier coverage is inferred.',
                 'Small unannounced adjustments are allowed under current FAQ; current policy is not retroactively asserted as 2024 policy.',
                 'No actual fills, account tier, liquidation costs or continuous exchange-rule history certified.'],
       'real_trades':0,'network_requests':0,'qualified_claim':False}
    (OUT/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n')
    local=OUT.parent/'local-derived';local.mkdir(exist_ok=True)
    with (local/'daily-maintenance-bounds.csv').open('w') as f:
        w=csv.DictWriter(f,fieldnames=list(all_rows[0]));w.writeheader();w.writerows(all_rows)
    print(json.dumps([{'id':s['scenario_id'],'r':s['maintenance_rate_scenario'],'min':s['minimum_after_maintenance_and_close']['surplus_after_maintenance_and_close'],'day':s['minimum_after_maintenance_and_close']['date_utc'],'negative_days':s['negative_bound_days_after_maintenance_and_close']} for s in scenarios],indent=2))
if __name__=='__main__':run()
