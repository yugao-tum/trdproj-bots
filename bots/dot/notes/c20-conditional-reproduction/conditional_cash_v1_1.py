#!/usr/bin/env python3
"""Read-only, explicitly conditional historical cash model. No network or orders."""
import argparse
import csv
import hashlib
import json
from dataclasses import dataclass
from datetime import date,datetime,timedelta,timezone
from decimal import Decimal,getcontext
from pathlib import Path
getcontext().prec=50
D=Decimal
VERSION="1.1-io-only"
ROOT=Path(__file__).resolve().parent
SYMBOLS=tuple('BTCUSDT_'+s for s in ('241227','250328','250627','250926','251226','260327','260626','260925'))
COSTS=(('base_30bps',D('.003')),('stress_60bps',D('.006')))
TOTAL=D(5000);VENUE=D(2500);IDLE=D(2500);N=D(1200);GATE=D('.017')
H=90


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def exp(symbol):return datetime.strptime(symbol[-6:],'%y%m%d').date()

def ds(d):return d.isoformat()

def number(x):
    x=D(str(x))
    if not x.is_finite():raise ValueError('nonfinite price')
    return x

def unique_put(mapping,key,row):
    if key in mapping:raise ValueError(f'duplicate key: {key}')
    mapping[key]=row

def price_record(raw):
    p={k:number(raw[k]) for k in ('open','high','low','close')}
    if min(p.values())<=0 or p['high']<max(p.values()) or p['low']>min(p.values()):raise ValueError('invalid OHLC')
    return p

def normalized_date(raw):
    raw=str(raw)
    if len(raw)==13:us=int(raw)*1000
    elif len(raw)==16:us=int(raw)
    else:raise ValueError('unrecognized timestamp unit')
    if us%(86400*1000000):raise ValueError('bar does not open at UTC midnight')
    return datetime.fromtimestamp(us//1000000,timezone.utc).date().isoformat()


@dataclass
class Data:
    spot:dict
    trade:dict
    mark:dict


def load_frozen_data(frozen):
    paths={}
    for label,item in frozen['files'].items():
        path=Path(item['path'])
        if sha(path)!=item['sha256']:raise ValueError(f'frozen input changed: {label}')
        paths[label]=path
    spot={};trade={};mark={}
    with paths['spot_csv'].open(newline='') as src:
        for raw in csv.DictReader(src):
            if raw['symbol']!='BTCUSDT':continue
            day=normalized_date(raw['open_time_raw'])
            if raw['open_time_utc'][:10]!=day:raise ValueError('spot date normalization mismatch')
            unique_put(spot,day,price_record(raw))
    with paths['fixed_futures_csv'].open(newline='') as src:
        for raw in csv.DictReader(src):
            if raw['symbol'] not in SYMBOLS or raw['kind'] not in ('klines','markPriceKlines'):raise ValueError('unexpected universe or kind')
            if json.loads(raw['errors']):raise ValueError('source audit row has errors')
            if raw['in_fixed_window']!='True':raise ValueError('row outside frozen window')
            day=normalized_date(raw['open_time_raw'])
            if raw['date']!=day:raise ValueError('future date normalization mismatch')
            e=exp(raw['symbol'])
            if not ds(e-timedelta(days=100))<=day<=ds(e):raise ValueError('source row outside scheduled boundary')
            dest=trade if raw['kind']=='klines' else mark
            unique_put(dest,(raw['symbol'],day),price_record(raw))
    return Data(spot,trade,mark)


def required_dates(symbol):
    e=exp(symbol);entry=e-timedelta(days=H);exit_=e-timedelta(days=1)
    holding=[entry+timedelta(days=i) for i in range((exit_-entry).days)]
    return e,entry-timedelta(days=1),entry,exit_,holding


def planned_quality(data,symbol):
    e,signal,entry,exit_,holding=required_dates(symbol)
    return {
        'signal_missing':[kind for kind,row in [('spot',data.spot.get(ds(signal))),('trade',data.trade.get((symbol,ds(signal))))] if row is None],
        'entry_exit_missing':[f'{side}:{kind}' for side,d in [('entry',entry),('exit',exit_)] for kind,row in [('spot',data.spot.get(ds(d))),('trade',data.trade.get((symbol,ds(d))))] if row is None],
        'holding_mark_missing_dates':[ds(d) for d in holding if (symbol,ds(d)) not in data.mark],
        'exit_mark_open_missing':(symbol,ds(exit_)) not in data.mark,
        'holding_spot_close_missing_dates':[ds(d) for d in holding if ds(d) not in data.spot],
    }


def initial_accounts(S0,F0,c):
    S0,F0,c=number(S0),number(F0),number(c)
    if min(S0,F0)<=0 or not 0<=c<1:raise ValueError('invalid price/cost')
    q=N/S0;Q=q*F0;spotfee=c*N;futurefee=c*Q
    spot_pre=N+spotfee;future_pre=Q+futurefee;reserve=VENUE-spot_pre-future_pre
    return dict(q=q,spot_entry_notional=N,future_entry_notional=Q,initial_future_collateral=Q,spot_entry_fee=spotfee,future_entry_fee=futurefee,spot_wallet_preplaced=spot_pre,future_wallet_preplaced=future_pre,venue_reserve=reserve,initial_capital_required=spot_pre+future_pre,idle_external=IDLE)


def exit_accounts(initial,S0,F0,S1,F1,c):
    S0,F0,S1,F1,c=map(number,(S0,F0,S1,F1,c));q=initial['q'];M=initial['initial_future_collateral']
    spot_notional=q*S1;future_notional=q*F1
    spotfee=c*spot_notional;futurefee=c*future_notional
    spotgross=spot_notional-N;futuregross=q*(F0-F1)
    future_before_fee=M+futuregross;future_end=future_before_fee-futurefee;spot_end=spot_notional-spotfee
    totalfees=initial['spot_entry_fee']+initial['future_entry_fee']+spotfee+futurefee
    final=IDLE+initial['venue_reserve']+spot_end+future_end
    algebra=spotgross+futuregross-totalfees
    if abs((final-TOTAL)-algebra)>D('1e-40'):raise AssertionError('cash ledger differs from four-leg formula')
    return dict(spot_exit_notional=spot_notional,future_exit_notional=future_notional,spot_exit_fee=spotfee,future_exit_fee=futurefee,spot_gross_change=spotgross,future_gross_change=futuregross,future_wallet_before_exit_fee=future_before_fee,future_wallet_after_exit=future_end,spot_wallet_after_exit=spot_end,total_four_side_cost=totalfees,algebraic_final_cash=final,algebraic_net_cash_change=algebra,exit_future_cash_sufficient=future_end>=0)


def capital_diagnostics(rec,daily,terminal_cash=None):
    observations=[];missing=[]
    for row in daily:
        label=row['date']+':daily_close'
        value=row.get('daily_venue_mtm_proxy')
        if value is None:missing.append(label)
        else:observations.append((label,value))
    entry_eq=rec.get('entry_future_mark_equity');exit_eq=rec.get('exit_future_mark_equity')
    reserve=rec['venue_reserve'];q=rec['q']
    entry_venue=reserve+N+entry_eq if entry_eq is not None else None
    exit_venue=reserve+q*rec['spot_exit_open']+exit_eq if exit_eq is not None and rec.get('spot_exit_open') is not None else None
    exit_cash=terminal_cash-IDLE if terminal_cash is not None else None
    for label,value in [('entry_mark_open',entry_venue),('exit_pre_close_mark_open',exit_venue),('exit_after_close_cash',exit_cash)]:
        if value is None:missing.append(label)
        else:observations.append((label,value))
    breaches=[{'point':label,'venue_mtm_proxy':value} for label,value in observations if value>VENUE]
    rec.update(entry_venue_mtm_proxy=entry_venue,entry_venue_over_2500=entry_venue>VENUE if entry_venue is not None else None,exit_pre_close_venue_mtm_proxy=exit_venue,exit_pre_close_venue_over_2500=exit_venue>VENUE if exit_venue is not None else None,exit_after_close_venue_cash_conditional=exit_cash,exit_after_close_venue_over_2500=exit_cash>VENUE if exit_cash is not None else None,max_observed_venue_mtm_proxy=max((v for _,v in observations),default=None),observed_venue_mtm_points=len(observations),venue_over_2500_point_count=len(breaches),venue_over_2500_points=breaches,venue_mtm_missing_point_count=len(missing),venue_mtm_missing_points=missing,capital_gate_failed=bool(breaches),capital_gate_verified=False,capital_gate_status='failed_observed_proxy_breach' if breaches else 'unknown_unverified_intraday_maximum')


def simulate_episode(data,symbol,cost_label,c):
    e,signal,entry,exit_,holding=required_dates(symbol)
    quality=planned_quality(data,symbol)
    rec=dict(symbol=symbol,subgroup='earlier_four_retrospective' if symbol in SYMBOLS[:4] else 'later_four_retrospective',cost_scenario=cost_label,cost_per_side=c,signal_date=ds(signal),entry_date=ds(entry),exit_date=ds(exit_),scheduled_expiry_date=ds(e),holding_calendar_days=len(holding),initial_nav=TOTAL,venue_budget=VENUE,idle_external=IDLE,signal_triggered=None,position_entered=False,conditional_net_cash_change=None,conditional_change_divided_by_5000=None,conditional_final_cash=None,observed_realized_return=None,execution_verified=False,margin_survival_verified=False,historical_actual_fee_verified=False,quantity_filters_verified=False,unseen_oos=False,source_quality=quality,capital_gate_failed=False,capital_gate_verified=False,capital_gate_status='unknown')
    daily=[]
    if quality['signal_missing']:
        rec['status']='missing_signal_data';return rec,daily
    ss=data.spot[ds(signal)]['close'];sf=data.trade[(symbol,ds(signal))]['close']
    u=sf/ss-1;trigger=u>GATE
    rec.update(signal_spot_close=ss,signal_future_close=sf,signal_basis=u,signal_triggered=trigger)
    if not trigger:
        rec.update(status='cash_only_signal_not_triggered',conditional_net_cash_change=D(0),conditional_change_divided_by_5000=D(0),conditional_final_cash=TOTAL,active_mark_path_complete=None,known_cash_path_infeasible=False,max_observed_venue_mtm_proxy=VENUE,observed_venue_mtm_points=0,venue_over_2500_point_count=0,venue_over_2500_points=[],venue_mtm_missing_point_count=0,venue_mtm_missing_points=[],capital_gate_status='cash_only_constant_2500_in_model')
        return rec,daily
    if any(x.startswith('entry:') for x in quality['entry_exit_missing']):
        rec.update(status='missing_entry_price',position_entered=None);return rec,daily
    S0=data.spot[ds(entry)]['open'];F0=data.trade[(symbol,ds(entry))]['open']
    rec.update(spot_entry_open=S0,future_entry_open=F0)
    initial=initial_accounts(S0,F0,c);rec.update(initial)
    if initial['venue_reserve']<0:
        rec.update(status='initial_capital_infeasible',known_cash_path_infeasible=True,capital_gate_failed=True,capital_gate_status='failed_initial_allocation');return rec,daily
    rec['position_entered']=True
    q=initial['q'];M=initial['initial_future_collateral'];reserve=initial['venue_reserve']
    equities=[]
    for day in holding:
        mark=data.mark.get((symbol,ds(day)));spot=data.spot.get(ds(day))
        dr=dict(symbol=symbol,cost_scenario=cost_label,date=ds(day),q=q,future_cash_collateral=M,venue_reserve=reserve,idle_external=IDLE,spot_close=None,mark_close=None,mark_high=None,future_equity_mark_close=None,future_equity_mark_high=None,daily_nav_proxy_close=None,daily_venue_mtm_proxy=None,daily_venue_over_2500=None,mark_missing=mark is None,spot_missing=spot is None,maintenance_margin_unknown=True)
        if spot:dr['spot_close']=spot['close']
        if mark:
            ec=M+q*(F0-mark['close']);eh=M+q*(F0-mark['high']);equities.append(eh)
            dr.update(mark_close=mark['close'],mark_high=mark['high'],future_equity_mark_close=ec,future_equity_mark_high=eh)
            if spot:
                dr['daily_nav_proxy_close']=IDLE+reserve+q*spot['close']+ec
                dr['daily_venue_mtm_proxy']=dr['daily_nav_proxy_close']-IDLE
                dr['daily_venue_over_2500']=dr['daily_venue_mtm_proxy']>VENUE
        daily.append(dr)
    for when,day in [('entry',entry),('exit',exit_)]:
        mark=data.mark.get((symbol,ds(day)))
        eq=M+q*(F0-mark['open']) if mark else None
        rec[f'{when}_mark_open']=mark['open'] if mark else None
        rec[f'{when}_future_mark_equity']=eq
        if eq is not None:equities.append(eq)
    known_fail=bool(equities and min(equities)<=0)
    path_complete=not quality['holding_mark_missing_dates'] and not quality['exit_mark_open_missing']
    rec.update(active_mark_path_complete=path_complete,known_cash_path_infeasible=known_fail,minimum_observed_future_equity_high_or_boundary=min(equities) if equities else None,daily_nav_proxy_complete=path_complete and not quality['holding_spot_close_missing_dates'])
    if any(x.startswith('exit:') for x in quality['entry_exit_missing']):
        rec['status']='missing_exit_price';capital_diagnostics(rec,daily);return rec,daily
    S1=data.spot[ds(exit_)]['open'];F1=data.trade[(symbol,ds(exit_))]['open']
    rec.update(spot_exit_open=S1,future_exit_open=F1)
    terminal=exit_accounts(initial,S0,F0,S1,F1,c)
    # Ledger leg amounts are explicitly conditional algebra; no cross-wallet rescue is allowed.
    rec.update({k:v for k,v in terminal.items() if not k.startswith('algebraic_')})
    if known_fail:
        rec['status']='known_cash_path_infeasible';capital_diagnostics(rec,daily);return rec,daily
    if not terminal['exit_future_cash_sufficient']:
        rec['status']='exit_future_cash_infeasible';capital_diagnostics(rec,daily);return rec,daily
    rec.update(status='conditional_terminal_cash_survival_unverified',conditional_net_cash_change=terminal['algebraic_net_cash_change'],conditional_change_divided_by_5000=terminal['algebraic_net_cash_change']/TOTAL,conditional_final_cash=terminal['algebraic_final_cash'])
    capital_diagnostics(rec,daily,terminal['algebraic_final_cash'])
    return rec,daily


def evaluate(data):
    records=[];daily=[]
    for symbol in SYMBOLS:
        for label,c in COSTS:
            r,d=simulate_episode(data,symbol,label,c);records.append(r);daily.extend(d)
    return records,daily


def dump_json(path,obj):path.write_text(json.dumps(obj,ensure_ascii=False,indent=2,default=str))

def dump_csv(path,rows):
    fields=list(dict.fromkeys(k for r in rows for k in r))
    with path.open('w',newline='') as out:
        w=csv.DictWriter(out,fieldnames=fields);w.writeheader()
        for r in rows:w.writerow({k:json.dumps(v,ensure_ascii=False,default=str) if isinstance(v,(dict,list)) else v for k,v in r.items()})



def run_public(input_dir,output_dir):
    manifest=json.loads((ROOT/'inputs.json').read_text())
    frozen={'files':{label:{'path':str(input_dir/item['filename']),'sha256':item['sha256']} for label,item in manifest['files'].items()}}
    for name in ('RESULTS.json','EPISODES-16.csv','DAILY-PROXY-LEDGER.csv'):
        if (output_dir/name).exists():raise ValueError('refusing to overwrite: '+name)
    data=load_frozen_data(frozen)
    records,daily=evaluate(data)
    baseline=[r for r in records if r['cost_scenario']=='base_30bps']
    capital_summary={}
    for label,_ in COSTS:
        rr=[r for r in records if r['cost_scenario']==label]
        vals=[r['max_observed_venue_mtm_proxy'] for r in rr if r.get('max_observed_venue_mtm_proxy') is not None]
        capital_summary[label]={'max_observed_venue_mtm_proxy':max(vals) if vals else None,'observed_breach_point_count':sum(r.get('venue_over_2500_point_count',0) for r in rr),'active_episodes_with_observed_breach':sum(r['position_entered'] is True and r['capital_gate_failed'] for r in rr),'missing_observation_point_count':sum(r.get('venue_mtm_missing_point_count',0) for r in rr),'full_intraday_capital_gate_verified':False}
    summary={'format_version':VERSION,'model':'independent episode conditional historical cash ledger; no continuous portfolio aggregation','new_full_executable_backtests':0,'conditional_historical_simulations':1,'new_empirical_pnl_mechanisms':1,'scheduled_maturities':8,'cost_scenario_rows':len(records),'signal_triggered_maturities':sum(r['signal_triggered'] is True for r in baseline),'signal_cash_only_maturities':sum(r['signal_triggered'] is False for r in baseline),'capital_proxy_diagnostics':capital_summary,'observed_realized_return':None,'continuous_portfolio_return':None,'sharpe':None,'max_drawdown':None,'margin_survival_verified':False,'execution_verified':False,'unseen_oos':False,'input_sha256':{k:v['sha256'] for k,v in manifest['files'].items()},'records':records}
    output_dir.mkdir(parents=True,exist_ok=True)
    dump_json(output_dir/'RESULTS.json',summary);dump_csv(output_dir/'EPISODES-16.csv',records);dump_csv(output_dir/'DAILY-PROXY-LEDGER.csv',daily)
    print(json.dumps({k:v for k,v in summary.items() if k!='records'},ensure_ascii=False,indent=2,default=str))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description='Offline C20 conditional cash reproduction, version1.1. No network or trading.')
    parser.add_argument('--input-dir',type=Path,required=True)
    parser.add_argument('--output-dir',type=Path,required=True)
    args=parser.parse_args();run_public(args.input_dir.resolve(),args.output_dir.resolve())
