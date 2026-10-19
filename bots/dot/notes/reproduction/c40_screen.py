#!/usr/bin/env python3
"""Frozen C40 spot-only proxy. Local reviewed inputs only; no network or trades."""
from __future__ import annotations
import csv
import hashlib
import importlib.util
import json
import math
import sys
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent
WORK = Path(__file__).resolve().parent
SPOT = ROOT / 'inputs/spot_daily.csv'
FUND = ROOT / 'inputs/funding.csv'
LOADER = ROOT / 'spot_screen.py'
OUT_DIR = ROOT / 'results/c40'
SHAS = {
    SPOT: 'a008fbd0514f4d01bd477fc008de9fb24b8dfae5e83ebda2ced8bbf2e89bcf0a',
    FUND: '310508098d4b9a30a33823368a80e8fe7c034c05f8cb37513d7de3b101a449a8',
    LOADER: '8e56d8e5c2e73c97710c795ee11a1fbdf86f6d5a2fac1f3688160d68160b3d8c',
    WORK / 'C40_PREREGISTRATION.md': 'aad6864bd45d9c3baac5540a559a1357741d9de8a654ffb6c55960d0771ceed6',
}
SYMBOLS = ('BTCUSDT', 'ETHUSDT', 'SOLUSDT')
START, END, OOS = date(2024,1,2), date(2026,9,30), date(2025,1,1)
CAPITAL, VENUE, IDLE, TARGET = 5000.0, 1250.0, 3750.0, 1100.0
RATES = (0.003, 0.006)

def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def load_spot():
    if digest(LOADER) != SHAS[LOADER]:
        raise ValueError('reviewed spot loader changed')
    spec = importlib.util.spec_from_file_location('c40_reviewed_spot_loader', LOADER)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module.load_and_precheck(SPOT)

def utc(s):
    t = datetime.fromisoformat(s.replace('Z', '+00:00'))
    if t.tzinfo is None or t.utcoffset() != timedelta(0):
        raise ValueError('timestamp is not explicitly UTC')
    return t

def load_funding(path):
    expected_fields = ['symbol','calc_time_utc','calc_time_raw','calc_time_raw_utc',
                       'funding_interval_hours','last_funding_rate','jitter_ms']
    events = {s:{} for s in SYMBOLS}
    epoch = datetime(1970,1,1,tzinfo=timezone.utc)
    with open(path, newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        if reader.fieldnames != expected_fields: raise ValueError('funding schema')
        for row in reader:
            if None in row or any(v is None for v in row.values()): raise ValueError('funding columns')
            s, t = row['symbol'], utc(row['calc_time_utc'])
            raw = epoch + timedelta(milliseconds=int(row['calc_time_raw']))
            if s not in events or t in events[s]: raise ValueError('funding symbol/duplicate')
            rate, jitter = float(row['last_funding_rate']), float(row['jitter_ms'])
            if not all(map(math.isfinite, (rate,jitter))): raise ValueError('nonfinite funding')
            if abs(rate) > .05 or float(row['funding_interval_hours']) != 8: raise ValueError('funding scale/interval')
            if raw != utc(row['calc_time_raw_utc']): raise ValueError('raw UTC mismatch')
            # CSV jitter was serialized from floating epoch seconds; allow 0.001 ms
            # rounding only. Raw integer millisecond UTC equality stays exact.
            if abs((raw-t).total_seconds()*1000-jitter) > .001 or abs(jitter)>30:
                raise ValueError('funding jitter mismatch')
            events[s][t] = rate
    first = datetime(2024,1,1,tzinfo=timezone.utc)
    grid = [first+timedelta(hours=8*i) for i in range(3012)]
    daily = {}
    for s, items in events.items():
        if set(items) != set(grid): raise ValueError('incomplete funding grid '+s)
        daily[s] = {grid[i].date(): [items[t] for t in grid[i:i+3]] for i in range(0,len(grid),3)}
    return daily, {'rows':9036,'rows_per_symbol':3012,'complete_8h_grid':True,'last_date':str(grid[-1].date())}

def signal(bars, i, prior_rates):
    if i < 20 or len(prior_rates) != 3: raise ValueError('signal warmup/funding length')
    closes = [b.close for b in bars[i-20:i]]
    entry = all(r < 0 for r in prior_rates) and closes[-1] >= min(closes)*1.01
    exit_funding = all(r >= 0 for r in prior_rates[1:])
    return entry, exit_funding

def simulate(symbol, bars, funding, rate, start=START, end=END):
    if rate not in RATES: raise ValueError('unregistered cost')
    cash, qty, entry_day, active_id, counter = VENUE, 0.0, None, None, 0
    days, trades, episodes = [], [], []
    active_episode = None
    def trade(day, side, price, reason):
        nonlocal cash, qty, entry_day, active_id, counter, active_episode
        if side == 'BUY':
            if qty != 0: raise ValueError('already holding')
            notional = min(TARGET, .9*cash)
            fee = notional*rate
            if notional+fee > cash+1e-9: raise ValueError('entry budget')
            qty = notional/price
            cash -= notional+fee
            counter += 1; active_id=counter; entry_day=day
            active_episode = {'episode_id':counter,'entry':str(day),'entry_notional':notional,'entry_fee':fee}
            amount=qty
        else:
            if qty <= 0: raise ValueError('selling without spot')
            amount=qty; notional=amount*price; fee=notional*rate
            cash += notional-fee; qty=0.0
            active_episode.update(exit=str(day),exit_notional=notional,exit_fee=fee,
                                  net_pnl=notional-fee-active_episode['entry_notional']-active_episode['entry_fee'],
                                  calendar_holding_days=(day-entry_day).days,exit_reason=reason)
            episodes.append(active_episode); active_episode=None; entry_day=None
        tid=active_id
        trades.append({'symbol':symbol,'cost_rate':rate,'date':str(day),'side':side,'price':price,
                       'qty':amount,'notional':notional,'fee':fee,'reason':reason,'episode_id':tid,
                       'cash_after':cash,'qty_after':qty})
        if side=='SELL': active_id=None
        if cash < -1e-8 or qty < 0: raise ValueError('negative capital')
    for i,b in enumerate(bars):
        d=b.day
        if d < start or d > end: continue
        prior = funding[d-timedelta(days=1)]
        entry_signal, exit_funding = signal(bars,i,prior)
        opening = cash+qty*b.open
        exited=False
        if qty>0 and (exit_funding or (d-entry_day).days>=7):
            why='prior-day funding nonnegative' if exit_funding else 'entry plus seven calendar days'
            trade(d,'SELL',b.open,why); exited=True
        if qty==0 and not exited and entry_signal: trade(d,'BUY',b.open,'prior-day negative funding and price confirmation')
        close_mark=cash+qty*b.close; high_bound=cash+qty*b.high
        before_final_qty=qty; eid=active_id
        if d==end and qty>0: trade(d,'SELL',b.close,'final close liquidation')
        days.append({'symbol':symbol,'cost_rate':rate,'date':str(d),'prior_rate_00':prior[0],
                     'prior_rate_08':prior[1],'prior_rate_16':prior[2],
                     'entry_signal':entry_signal,'exit_funding_signal':exit_funding,
                     'episode_id_close_before_liquidation':eid,'qty_before_final_liquidation':before_final_qty,
                     'on_exchange_open_pretrade_mark':opening,'on_exchange_close_preliquidation_mark':close_mark,
                     'on_exchange_high_upper_bound':high_bound,'cash':cash,'qty':qty,'idle_cash':IDLE,
                     'equity':IDLE+cash+qty*b.close,'open_breach':opening>2500+1e-9,
                     'close_breach':close_mark>2500+1e-9,'high_bound_breach':high_bound>2500+1e-9})
    expected = [str(start+timedelta(days=i)) for i in range((end-start).days+1)]
    if [r['date'] for r in days] != expected: raise ValueError('simulation calendar mismatch')
    if qty != 0 or active_episode is not None: raise ValueError('not flat at end')
    return {'daily':days,'trades':trades,'episodes':episodes}

def period_metrics(sim, start, end):
    ds = sim['daily']; selected=[r for r in ds if start<=r['date']<=end]
    prior = [r for r in ds if r['date']<start]
    base = prior[-1]['equity'] if prior else CAPITAL
    final=selected[-1]['equity']; ndays=len(selected)
    peak=base; dd=0.0
    for r in selected:
        peak=max(peak,r['equity']);dd=max(dd,1-r['equity']/peak)
    ts=[r for r in sim['trades'] if start<=r['date']<=end]
    months=[]; last=base
    bymonth={r['date'][:7]:r for r in selected}
    for month,r in bymonth.items():
        val=r['equity'];months.append({'month':month,'start_equity':last,'end_equity':val,
                  'pnl':val-last,'return_on_start_nav':val/last-1,'contribution_on_5000':(val-last)/CAPITAL});last=val
    return {'start':start,'end':end,'calendar_days':ndays,'start_equity':base,'end_equity':final,
            'net_pnl':final-base,'fixed_5000_return':(final-base)/CAPITAL,'return_on_start_nav':final/base-1,
            'cagr':(final/base)**(365/ndays)-1,'max_drawdown':dd,'fees':sum(r['fee'] for r in ts),
            'trade_legs':len(ts),'episodes_started':sum(r['side']=='BUY' for r in ts),
            'carry_in_qty':prior[-1]['qty'] if prior else 0.0,
            'ex_best_month_pnl':final-base-max(r['pnl'] for r in months),
            'max_venue_open':max(r['on_exchange_open_pretrade_mark'] for r in selected),
            'max_venue_close':max(r['on_exchange_close_preliquidation_mark'] for r in selected),
            'max_venue_high_bound':max(r['on_exchange_high_upper_bound'] for r in selected),
            'open_breach_days':sum(r['open_breach'] for r in selected),
            'close_breach_days':sum(r['close_breach'] for r in selected),
            'high_bound_breach_days':sum(r['high_bound_breach'] for r in selected),
            'months':months}

def write_csv(path, rows):
    if not rows: path.write_text('');return
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def main():
    for path,h in SHAS.items():
        if digest(path)!=h: raise ValueError('frozen input changed: '+str(path))
    bars,dates,quality=load_spot();fund,fquality=load_funding(FUND)
    if '--preflight-only' in sys.argv:
        print(json.dumps({'spot':quality,'funding':fquality}));return
    out=OUT_DIR
    if out.exists(): raise ValueError('refusing to overwrite existing result directory')
    sims={};daily=[];trades=[];episodes=[];months=[]
    for symbol in SYMBOLS:
        for rate in RATES:
            sim=simulate(symbol,bars[symbol],fund[symbol],rate)
            periods={label:period_metrics(sim,a,b) for label,a,b in [
                ('full',str(START),str(END)),('pre_oos',str(START),'2024-12-31'),('oos',str(OOS),str(END))]}
            sims[f'{symbol}|{rate}']={'symbol':symbol,'cost_rate':rate,'periods':periods,
                                     'episodes_total':len(sim['episodes']),'independent_events':'unknown'}
            daily.extend(sim['daily']);trades.extend(sim['trades'])
            episodes.extend(dict(symbol=symbol,cost_rate=rate,**r) for r in sim['episodes'])
            months.extend(dict(symbol=symbol,cost_rate=rate,**r) for r in periods['full']['months'])
    out.mkdir()
    summary={'variant':'C40.spot-proxy-v1','operator':'reviewed self-written simulation',
             'executed_utc':datetime.now(timezone.utc).isoformat(),'capital':CAPITAL,
             'scenario_separate_capital':True,'funding_cashflow_received':0,'scenarios':sims,
             'data_quality':{'spot':quality,'funding':fquality},
             'caveats':['Fixed retrospective OOS split, not genuinely unseen live data',
                        'Funding sign is not proof of crowding; OI/CVD unavailable',
                        'Daily open/close fills assumed; extra spread/slippage unverified',
                        'Episodes are not independent events; cross-coin clusters unreviewed']}
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    for name,rows in [('daily_equity.csv',daily),('trades.csv',trades),('episodes.csv',episodes),('monthly_returns.csv',months)]: write_csv(out/name,rows)
    manifest={'files':{p.name:{'sha256':digest(p),'bytes':p.stat().st_size} for p in sorted(out.iterdir())},
              'input_and_code':{p.name:digest(p) for p in [*SHAS,Path(__file__)]}}
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({k:{'episodes':v['episodes_total'],'full':v['periods']['full']['net_pnl'],
                        'oos':v['periods']['oos']['net_pnl']} for k,v in sims.items()},indent=2))

if __name__=='__main__': main()
