#!/usr/bin/env python3
"""Independent, offline, exact rational two-venue replay. Only bundled source inputs."""
import csv,json,hashlib,sys
from pathlib import Path
from fractions import Fraction as F
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parent

def load(p): return json.loads((ROOT/p).read_text())
def rows(p): return list(csv.DictReader((ROOT/p).open()))
def run():
 manifest=load('inputs.json')
 for p,h in manifest.items():
  if hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=h: raise ValueError('SOURCE HASH MISMATCH: '+p)
 c=load('sources/contract.json'); prices=rows('sources/prices-main.csv')+rows('sources/prices-extension.csv'); events=rows('sources/funding-main.csv')+rows('sources/funding-extension.csv')
 out=ROOT/'results';out.mkdir(exist_ok=True)
 daily=(out/'daily.csv').open('w');fund=(out/'funding.csv').open('w')
 dw=csv.writer(daily); fw=csv.writer(fund)
 dw.writerow(['case_id','date','kraken_equity','binance_cash','binance_equity','nav','funding','lower','upper','liquidation_pnl'])
 fw.writerow(['case_id','timestamp_ms','flow','funding','before','after'])
 result=[];entry=1704067200000
 for sym in c['asset_map']:
  pp=sorted([r for r in prices if r['symbol']==sym],key=lambda r:int(r['open_time_ms']));ss={int(r['timestamp'])*1000:r for r in load('sources/'+sym+'.json')['rows']}
  ee=sorted([r for r in events if r['symbol']==sym and entry<int(r['fundingTime'])<=int(pp[-1]['close_time_ms'])],key=lambda r:int(r['fundingTime']))
  assert len(pp)==1023 and len(ss)==1023 and len(ee)==3068
  assert len({int(e['fundingTime']) for e in ee})==len(ee)
  assert all(int(p['open_time_ms'])==entry+i*86400000 for i,p in enumerate(pp))
  S=F(ss[entry]['open']);P=F(pp[0]['perp_open']);M=F(pp[0]['mark_open']);guard=max(F('1.0015')*P,M,P);loss=max(M-P,0)
  for ck in c['costs']['Kraken_all_in']:
   for cb in c['costs']['Binance_all_in']:
    k,b=F(ck),F(cb);cap=min(2500/(S*(1+k)),2500/(b*P+guard+loss))
    specs=[('A'+r['budget'],F(r['fixed_quantity'])) for r in c['quantity']['A_reference_cases'] if r['symbol']==sym and r['binance_cost']==cb]+[('B',F((cap*10**24).__floor__(),10**24))]
    for mode,q in specs:
     cid=f'{sym}_{mode}_cK{ck}_cB{cb}';kc=2500-q*S*(1+k);bc=2500-b*q*P
     assert kc>=0 and 2500-q*(b*P+guard+loss)>=0
     if mode=='B': assert q<=cap<q+F(1,10**24)
     cumulative=F(0);j=0;first=None;guaranteed=None;minimum=None;minlower=None;endpoints={}
     for p in pp:
      t=int(p['open_time_ms']);end=int(p['close_time_ms']);sp=ss[t];prefix=[cumulative]
      while j<len(ee) and int(ee[j]['fundingTime'])<=end:
       e=ee[j];mark=F(e['markPrice']);flow=q*mark*F(e['fundingRate']);before=bc+cumulative+q*(P-mark);cumulative+=flow;after=bc+cumulative+q*(P-mark)
       fw.writerow([cid,e['fundingTime'],flow,cumulative,before,after]);prefix.append(cumulative)
       if min(before,after)<=0 and first is None: first=int(e['fundingTime'])
       minimum=min(before,after) if minimum is None else min(minimum,before,after)
       j+=1
      lower=bc+min(prefix)+q*(P-F(p['mark_high']));upper=bc+max(prefix)+q*(P-F(p['mark_high']));minlower=lower if minlower is None else min(lower,minlower)
      if upper<0 and guaranteed is None: guaranteed=p['date_utc']
      ke=kc+q*F(sp['close']);be=bc+cumulative+q*(P-F(p['mark_close']));basis=q*(F(sp['close'])-S+P-F(p['perp_close']));cost=q*(k*(S+F(sp['close']))+b*(P+F(p['perp_close'])));pnl=cumulative+basis-cost
      dw.writerow([cid,p['date_utc'],ke,bc+cumulative,be,ke+be,cumulative,lower,upper,pnl])
      if p['date_utc'] in ['2026-09-30','2026-10-19']:
       endpoints[p['date_utc']]={key:str(v) for key,v in dict(funding=cumulative,basis=basis,total_cost=cost,pnl=pnl,return5000=pnl/5000,kraken_exit_cash=kc+q*F(sp['close'])*(1-k),binance_exit_cash=bc+cumulative+q*(P-F(p['perp_close']))-b*q*F(p['perp_close']),mark_nav=ke+be).items()}
       endpoints[p['date_utc']]['counterfactual']=first is not None or guaranteed is not None
     result.append(dict(case_id=cid,quantity=str(q),kraken_open_cash=str(kc),binance_open_cash=str(bc),first_nonpositive_funding_ms=first,first_guaranteed_negative_day=guaranteed,minimum_funding_equity=str(minimum),minimum_daily_lower=str(minlower),endpoints=endpoints))
 assert len(result)==36
 daily.close();fund.close();(out/'results.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps({'cells':36,'daily_rows':36*1023,'funding_rows':36*3068,'exact_arithmetic':'Fraction','independent_outcomes':False,'historical_mmr_certified':False}))
if __name__=='__main__': run()
