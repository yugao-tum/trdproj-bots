#!/usr/bin/env python3
"""Fixed same-budget passive comparisons. Offline; writes only beside this script."""
import csv, hashlib, json, math
from datetime import date, timedelta
from pathlib import Path
O=Path(__file__).resolve().parent
R16=O.parents[2]/'r16-proposal'
INPUTS={R16/'01-freeze-inputs/output/panel_utc.csv':'a3b601644697f778990fcfdcc2ff1143140d5373c33d871ff81536d493891f79',R16/'01-freeze-inputs/output/open_extension_utc.csv':'ad044b15871eea467cb8750efbb3855f22fd65addce3b2424f67a57fe772183a'}
ASSETS=('BTC','ETH','SOL')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def writecsv(name,rows):
 with (O/name).open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def simulate(rows,benchmark,venue,cost):
 reserve=5000-venue;cash=float(venue);qty={s:0. for s in ASSETS};previous_close={s:float(rows[0][s+'_open']) for s in ASSETS};previous_venue=venue
 ledger=[];trades=[];fees=0.;notional=0.;peak=5000.;mdd=0.;maxerr=0.
 sid=f'{benchmark}_{venue}_{int(cost*10000)}bps'
 for i,r in enumerate(rows):
  op={s:float(r[s+'_open']) for s in ASSETS};cl={s:float(r[s+'_close']) for s in ASSETS};hi={s:float(r[s+'_high']) for s in ASSETS}
  before=qty.copy();cashbefore=cash;pre=cash+sum(qty[s]*op[s] for s in ASSETS);overnight=sum(qty[s]*(op[s]-previous_close[s]) for s in ASSETS);entryfee=0.;exitfee=0.;turn=0.
  if i==0 and benchmark!='cash':
   weights={'BTC':1.,'ETH':0.,'SOL':0.} if benchmark=='BTC' else {s:1/3 for s in ASSETS}
   budget=venue/(1+cost)
   for s in ASSETS:
    n=budget*weights[s]
    if n:
     q=n/op[s];qty[s]=q;entryfee+=n*cost;turn+=n
     trades.append(dict(scenario_id=sid,date_utc=r['date_utc'],event_phase='open',symbol=s,qty_delta=q,reference_price=op[s],signed_notional=n,fee=n*cost))
   cash=venue-budget-entryfee
  post=cash+sum(qty[s]*op[s] for s in ASSETS);intraday=sum(qty[s]*(cl[s]-op[s]) for s in ASSETS);close=cash+sum(qty[s]*cl[s] for s in ASSETS);high=cash+sum(qty[s]*hi[s] for s in ASSETS);held=qty.copy()
  if i==len(rows)-1:
   for s in ASSETS:
    n=qty[s]*cl[s]
    if n:
     exitfee+=n*cost;turn+=n;trades.append(dict(scenario_id=sid,date_utc=r['date_utc'],event_phase='terminal_close',symbol=s,qty_delta=-qty[s],reference_price=cl[s],signed_notional=-n,fee=n*cost))
   cash=close-exitfee;qty={s:0. for s in ASSETS}
  end=cash+sum(qty[s]*cl[s] for s in ASSETS);err=end-(previous_venue+overnight+intraday-entryfee-exitfee)
  total=reserve+end;peak=max(peak,total);mdd=min(mdd,total/peak-1);maxerr=max(maxerr,abs(err));fees+=entryfee+exitfee;notional+=turn
  ledger.append(dict(scenario_id=sid,date_utc=r['date_utc'],initial_venue=venue,reserve=reserve,cost_side=cost,venue_cash_before_open=cashbefore,venue_cash_after_open=post-sum(held[s]*op[s] for s in ASSETS),**{'qty_'+s+'_before':before[s] for s in ASSETS},**{'qty_'+s+'_after':held[s] for s in ASSETS},venue_pretrade_open=pre,venue_posttrade_open=post,venue_close_before_terminal=close,venue_high_upper_bound=high,total_equity_before_terminal=reserve+close,total_equity_end=total,overnight_pnl=overnight,intraday_pnl=intraday,open_fees=entryfee,terminal_fees=exitfee,trade_notional=turn,conservation_error=err))
  previous_close=cl;previous_venue=end
 observed=max(max(x[k] for k in ('venue_pretrade_open','venue_posttrade_open','venue_close_before_terminal')) for x in ledger);high=max(x['venue_high_upper_bound'] for x in ledger)
 result=dict(scenario_id=sid,benchmark=benchmark,initial_venue=venue,reserve=reserve,cost_side=cost,start=rows[0]['date_utc'],end=rows[-1]['date_utc'],days=len(rows),final_equity=total,total_return=total/5000-1,cagr=(total/5000)**(365/len(rows))-1,mdd_close=mdd,fees=fees,trade_notional=notional,turnover_over_initial_total=notional/5000,max_conservation_error=maxerr,peak_observed_venue=observed,peak_high_upper_bound=high,capital_status='observed_breach' if observed>2500+1e-8 else ('not_conservatively_certified' if high>2500+1e-8 else 'conservative_bound_pass'),terminal_qty_sum=sum(qty.values()),terminal_venue_cash=cash,evidence_class='conditional_simulation')
 assert maxerr<1e-7 and cash>=-1e-7 and result['terminal_qty_sum']==0
 return result,ledger,trades

def tests():
 rows=[dict(date_utc=d,**{s+'_'+k:100. for s in ASSETS for k in ('open','close','high')}) for d in ('2024-01-01','2024-01-02')]
 n=0
 for b in ('cash','BTC','EW'):
  for v in (1250,2500):
   for c in (0.,.003,.006):
    r,l,t=simulate(rows,b,v,c);expected=5000 if b=='cash' else 5000-v+v*(1-c)/(1+c)
    assert abs(r['final_equity']-expected)<1e-8
    assert len(t)==(0 if b=='cash' else 2 if b=='BTC' else 6)
    if b=='cash':assert r['fees']==0 and r['mdd_close']==0
    n+=1
 # Price doubling hand-check and overnight decomposition.
 for s in ASSETS:
  for k in ('open','close','high'):rows[1][s+'_'+k]=200.
 r,l,t=simulate(rows,'BTC',2500,.003)
 assert abs(r['final_equity']-(2500+5000*(1-.003)/(1+.003)))<1e-8
 assert abs(l[1]['overnight_pnl']-2500/1.003)<1e-8
 return {'passed':n+2,'checks':'flat-price entry+exit fee identity, zero-fee, zero-cost cash, trade counts, terminal zero quantities, cash nonnegative, accounting conservation, doubled-price overnight decomposition'}

def main():
 before={str(p):sha(p) for p in INPUTS};assert all(before[str(p)]==h for p,h in INPUTS.items())
 panels=[list(csv.DictReader(p.open())) for p in INPUTS];opens={r['date_utc']:r for r in panels[1]}
 rows=[dict(r,**opens[r['date_utc']]) for r in panels[0] if '2024-01-01'<=r['date_utc'][:10]<='2026-09-30'];assert len(rows)==1004 and len({r['date_utc'] for r in rows})==1004
 assert [r['date_utc'][:10] for r in rows]==[(date(2024,1,1)+timedelta(days=i)).isoformat() for i in range(1004)]
 assert all(math.isfinite(float(r[s+'_'+k])) and float(r[s+'_'+k])>0 for r in rows for s in ASSETS for k in ('open','close','high'))
 metrics=[];ledgers=[];trades=[]
 for b in ('cash','BTC','EW'):
  for v in (2500,1250):
   for c in (.003,.006):
    m,l,t=simulate(rows,b,v,c);metrics.append(m);ledgers+=l;trades+=t
 writecsv('metrics.csv',metrics);writecsv('accounts.csv',ledgers);writecsv('trades.csv',trades)
 (O/'metrics.json').write_text(json.dumps(metrics,indent=2)+'\n');(O/'tests.json').write_text(json.dumps(tests(),indent=2)+'\n')
 assert all(sha(p)==h for p,h in INPUTS.items())
 manifest=dict(actual_model='unknown',input_sha256=before,code_sha256=sha(Path(__file__)),output_sha256={p.name:sha(p) for p in O.iterdir() if p.name in ('metrics.csv','metrics.json','accounts.csv','trades.csv','tests.json','compare.py','comparison.csv','comparison-manifest.json','RESULT.md','PREREGISTRATION.md')},local_only=['accounts.csv','trades.csv'],publication_allowlist=['benchmark.py','metrics.csv','metrics.json','tests.json','manifest.json','RESULT.md','PREREGISTRATION.md','compare.py','comparison.csv','comparison-manifest.json'],source_changed=False)
 (O/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
if __name__=='__main__':main()
