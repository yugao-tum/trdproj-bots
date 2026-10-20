#!/usr/bin/env python3
"""Independent accounting identity audit; does not import execution engine or solve its targets."""
import csv,json,math,hashlib,copy
from pathlib import Path
from collections import defaultdict
from datetime import date,timedelta
HERE=Path(__file__).resolve().parent
R17=HERE.parent.parent
R16=R17.parent/'r16-proposal'
ASSETS=('BTC','ETH','SOL')
def rows(p):
 with open(p) as f:return list(csv.DictReader(f))
def day(v):return v[:10]
def num(r,k):return float(r[k])
def yes(v):return str(v).lower() in ('true','1','1.0')
def audit(accounts,trades,signals,prices):
 errors=[]; maxima=defaultdict(float); checks=0
 def eq(label,a,b,where):
  nonlocal checks
  checks+=1; d=abs(float(a)-float(b)); maxima[label]=max(maxima[label],d)
  if not math.isfinite(d) or d>1e-7+abs(float(b))*1e-10:errors.append(dict(check=label,where=where,actual=a,expected=b,error=d))
 def ok(label,cond,where):
  nonlocal checks
  checks+=1
  if not cond:errors.append(dict(check=label,where=where))
 groups=defaultdict(list); tx=defaultdict(list)
 for r in accounts:groups[r['scenario_id']].append(r)
 for t in trades:tx[(t['scenario_id'],day(t['date_utc']),t['event_phase'])].append(t)
 ok('exactly_four_scenarios',len(groups)==4,'all')
 configs=[]; seen=set(); summary={}
 for sc,rs in groups.items():
  dates=[day(r['date_utc']) for r in rs]; expected=[str(date(2024,1,1)+timedelta(days=i)) for i in range(1004)]
  ok('continuous_1004_dates',dates==expected,sc)
  initial=num(rs[0],'initial_venue'); reserve=5000-initial; rate=num(rs[0],'cost_side');configs.append((initial,rate))
  qprev={s:0. for s in ASSETS}; cashprev=initial; prev_equity=5000.; prev_close=None; prev_gate=None; fees=0.; equity=[5000.]
  for i,r in enumerate(rs):
   d=day(r['date_utc']); loc=sc+'/'+d; sig=signals[d]; p=prices[d]; g=num(sig,'gate_lagged')
   permitted=(i==0 or yes(sig['base_rebalance_day']) or g!=prev_gate)
   expected_reason='initial' if i==0 else ('gate_change' if g!=prev_gate else ('base' if yes(sig['base_rebalance_day']) else 'hold'))
   ok('reason_matches_signal',r['reason']==expected_reason,loc)
   eq('reserve',num(r,'reserve'),reserve,loc);eq('initial_venue',num(r,'initial_venue'),initial,loc);eq('cost_side',num(r,'cost_side'),rate,loc);eq('gate',num(r,'gate'),g,loc)
   ok('decision_previous_day',day(sig['decision_date_utc'])==str(date.fromisoformat(d)-timedelta(days=1)),loc)
   ok('execution_same_day',day(sig['execution_date_utc'])==d,loc)
   cash=num(r,'venue_cash_before_open'); after=num(r,'venue_cash_after_open')
   eq('cash_continuity',cash,cashprev,loc)
   qb={s:num(r,'qty_'+s+'_before') for s in ASSETS};qa={s:num(r,'qty_'+s+'_after') for s in ASSETS}
   for s in ASSETS:eq('inventory_continuity',qb[s],qprev[s],loc+'/'+s)
   openfees=0.;notional=0.
   def event(phase,qstart,cstart):
    batch=tx.get((sc,d,phase),[]); seen.add((sc,d,phase)); delta={s:0. for s in ASSETS}; total=0.;f=0.; symbols=[]
    for t in batch:
     s=t['symbol'];symbols.append(s);where=loc+'/'+phase+'/'+s
     ok('symbol',s in ASSETS,where)
     if s not in ASSETS:continue
     price=p[s+'_open' if phase=='open' else s+'_close'];qty=num(t,'qty_delta');n=num(t,'signed_notional');fee=num(t,'fee')
     eq('reference_price',num(t,'reference_price'),price,where);eq('notional_qty_price',n,qty*price,where);eq('fee_rate',fee,abs(n)*rate,where)
     eq('event_qty_before',num(t,'qty_before'),qstart[s],where);eq('event_qty_after',num(t,'qty_after'),qstart[s]+qty,where)
     eq('event_cash_before_repeated',num(t,'cash_before_event'),cstart,where)
     delta[s]+=qty;total+=n;f+=fee
    ok('one_row_per_symbol',len(set(symbols))==len(symbols),loc+'/'+phase)
    cend=cstart-total-f
    for t in batch:eq('event_cash_after_repeated',num(t,'cash_after_event'),cend,loc+'/'+phase)
    return {s:qstart[s]+delta[s] for s in ASSETS},cend,f,sum(abs(num(t,'signed_notional')) for t in batch)
   qo,co,openfees,turn=event('open',qb,cash)
   if not permitted:ok('hold_day_no_trade',not tx.get((sc,d,'open')),loc)
   for s in ASSETS:
    eq('open_qty',qa[s],qo[s],loc+'/'+s);ok('no_short',qa[s]>=-1e-10,loc+'/'+s)
    if g==0:eq('gate_off_zero_inventory',qa[s],0,loc+'/'+s)
   eq('self_financing_cash',after,co,loc);ok('no_borrow',after>=-1e-7,loc)
   pre=cash+sum(qb[s]*p[s+'_open'] for s in ASSETS);post=after+sum(qa[s]*p[s+'_open'] for s in ASSETS)
   close=after+sum(qa[s]*p[s+'_close'] for s in ASSETS);high=after+sum(qa[s]*p[s+'_high'] for s in ASSETS)
   if permitted:
    for s in ASSETS:eq('target_post_fee_weight',qa[s]*p[s+'_open'],post*num(sig,s+'_weight'),loc+'/'+s)
   overnight=0. if prev_close is None else sum(qb[s]*(p[s+'_open']-prev_close[s+'_close']) for s in ASSETS)
   intraday=sum(qa[s]*(p[s+'_close']-p[s+'_open']) for s in ASSETS)
   eq('venue_pretrade_open',num(r,'venue_pretrade_open'),pre,loc);eq('venue_posttrade_open',num(r,'venue_posttrade_open'),post,loc)
   eq('venue_close',num(r,'venue_close_before_terminal'),close,loc);eq('high_upper_bound',num(r,'venue_high_upper_bound'),high,loc)
   eq('total_before_terminal',num(r,'total_equity_before_terminal'),close+reserve,loc)
   eq('open_fees',num(r,'open_fees'),openfees,loc)
   eq('overnight_pnl',num(r,'overnight_pnl'),overnight,loc);eq('intraday_pnl',num(r,'intraday_pnl'),intraday,loc)
   if d=='2026-09-30':
    qe,ce,tf,terminalturn=event('terminal_close',qa,after)
    for s in ASSETS:eq('terminal_zero',qe[s],0,loc+'/'+s)
   else:
    ok('no_early_terminal',not tx.get((sc,d,'terminal_close')),loc);qe=qa;ce=after;tf=0.;terminalturn=0.
   eq('trade_notional_including_terminal',num(r,'trade_notional'),turn+terminalturn,loc)
   total=ce+sum(qe[s]*p[s+'_close'] for s in ASSETS)+reserve
   eq('terminal_fees',num(r,'terminal_fees'),tf,loc);eq('end_cash',num(r,'venue_cash_end'),ce,loc)
   for s in ASSETS:eq('end_qty',num(r,'qty_'+s+'_end'),qe[s],loc+'/'+s)
   eq('total_equity_end',num(r,'total_equity_end'),total,loc);eq('daily_pnl_identity',total-prev_equity,overnight+intraday-openfees-tf,loc)
   qprev=qe;cashprev=ce;prev_close=p;prev_gate=g;prev_equity=total;fees+=openfees+tf;equity.append(total)
  peak=5000.;mdd=0.
  for v in equity:peak=max(peak,v);mdd=min(mdd,v/peak-1)
  summary[sc]={'days':len(rs),'final_equity':equity[-1],'return_5000':equity[-1]/5000-1,'cagr_1004_365':(equity[-1]/5000)**(365/1004)-1,'mdd_including_initial_5000':mdd,'fees':fees}
 ok('fixed_configurations',sorted(configs)==[(1250.,.003),(1250.,.006),(2500.,.003),(2500.,.006)],'all')
 for key in tx:ok('no_orphan_trade_event',key in seen, str(key))
 return {'pass':not errors,'checks':checks,'error_count':len(errors),'first_errors':errors[:20],'max_errors':dict(maxima),'scenarios':summary}
def main():
 inputs={'metrics':R17/'02-next-open-ledger/output/metrics.json','accounts':R17/'02-next-open-ledger/output/accounts.csv','trades':R17/'02-next-open-ledger/output/trades.csv','signals':R17/'01-continuous-signals/output/signals.csv','panel':R16/'01-freeze-inputs/output/panel_utc.csv','open':R16/'01-freeze-inputs/output/open_extension_utc.csv'}
 a=rows(inputs['accounts']);t=rows(inputs['trades']);ss={day(r['date_utc']):r for r in rows(inputs['signals'])}
 pp={day(r['date_utc']):{k:float(v) for k,v in r.items() if k!='date_utc'} for r in rows(inputs['panel'])}
 for r in rows(inputs['open']):pp[day(r['date_utc'])].update({k:float(v) for k,v in r.items() if k!='date_utc'})
 result=audit(a,t,ss,pp); negative={}
 for field,value in [('fee',str(float(t[0]['fee'])+1)),('qty_delta',str(float(t[0]['qty_delta'])+1)),('date_utc','2023-12-31')]:
  corrupt=copy.deepcopy(t);corrupt[0][field]=value;n=audit(a,corrupt,ss,pp);negative[field]={'detected':not n['pass'],'first_error':n['first_errors'][:1]}
 metrics=json.loads((R17/'02-next-open-ledger/output/metrics.json').read_text());metric_errors=[]
 for m in metrics:
  own=result['scenarios'][m['scenario_id']]
  for theirs,ours in [('final_equity','final_equity'),('total_return','return_5000'),('cagr','cagr_1004_365'),('mdd','mdd_including_initial_5000'),('fees','fees')]:
   if abs(m[theirs]-own[ours])>1e-8:metric_errors.append({'scenario':m['scenario_id'],'metric':theirs,'reported':m[theirs],'independent':own[ours]})
 result['metric_errors']=metric_errors;result['pass']=result['pass'] and not metric_errors
 result['negative_tests']=negative;result['classification']='conditional_simulation';result['pass']=result['pass'] and all(v['detected'] for v in negative.values())
 (HERE/'audit-results.json').write_text(json.dumps(result,indent=2)+'\n')
 sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
 manifest={'actual_model':'unknown','role':'native04','inputs':{k:{'path':str(p),'sha256':sha(p)} for k,p in inputs.items()},'code_sha256':sha(Path(__file__)),'outputs':{'audit-results.json':sha(HERE/'audit-results.json')}}
 for name in ('RESULT.md','README.md'):
  if (HERE/name).exists():manifest['outputs'][name]=sha(HERE/name)
 (HERE/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 print(json.dumps({'pass':result['pass'],'checks':result['checks'],'error_count':result['error_count'],'first_errors':result['first_errors'][:3]}))
if __name__=='__main__':main()
