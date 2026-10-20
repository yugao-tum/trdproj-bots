#!/usr/bin/env python3
"""Read-only daily quote diagnostics; optional 04 normalized schema via --nav.
NAV schema JSON array: timestamp UTC ISO, q0,q1,nav (float). No source mutation.
"""
import csv,json,hashlib,argparse,datetime as dt,math
from pathlib import Path
UTC=dt.timezone.utc
def date(s): return dt.datetime.fromisoformat(s.replace('Z','+00:00'))
def qtile(a,p):
 a=sorted(a); x=(len(a)-1)*p; i=int(x); return a[i]+(a[min(i+1,len(a)-1)]-a[i])*(x-i)
def dd(values):
 peak=values[0]; worst=0
 for v in values: peak=max(peak,v); worst=min(worst,v/peak-1)
 return worst
def recovery(rows,threshold,start,end,key):
 run=[]
 for r in rows:
  if not start<=r['date']<end: continue
  if r[key]>=threshold:
   if run and (date(r['date'])-date(run[-1])).days!=1: run=[]
   run.append(r['date'])
   if len(run)==3:return {'first_day':run[0],'confirmed_day':run[2]}
  else: run=[]
 return {'right_censored':True}
def analyze_nav(rows):
 rows=sorted(rows,key=lambda r:r['timestamp']); daily={}
 for r in rows:
  r['date']=r['timestamp'][:10]; daily[r['date']]=r
 days=list(daily.values()); vals=[r['nav'] for r in rows]
 returns=[b['nav']/a['nav']-1 for a,b in zip(days,days[1:]) if (date(b['date'])-date(a['date'])).days==1]
 base=[r for r in rows if r['timestamp']<'2023-03-11T00:00:00Z'][-1]
 event=[r for r in rows if '2023-03-11T00:00:00Z'<=r['timestamp']<'2023-03-22T00:00:00Z']
 trough=min(event,key=lambda r:r['nav']); initial=rows[0]
 return {'rows':len(rows),'days':len(days),'daily_adjacent_returns':len(returns),'full_sample_drawdown':dd(vals),'daily_return_quantile_01':qtile(returns,.01),'daily_return_quantile_05':qtile(returns,.05),'event':{'baseline':base,'trough':trough,'minimum_vs_fixed_baseline':trough['nav']/base['nav']-1,'sampled_peak_to_trough':dd([base['nav']]+[r['nav'] for r in event]),'quantity_at_trough_vs_baseline':{k:trough[k]/base[k]-1 for k in ['q0','q1']},'recovery':recovery(days,base['nav'],trough['date'],'2023-04-20','nav')},'single_exit_lower_sensitivity':{'factor':5/6,'minimum_vs_no_pending_baseline':5/6*trough['nav']/base['nav']-1,'note':'Uniform instantaneous continuous-quantity bound; not time-varying actual fee state. Constant scaling preserves within-series returns and drawdown; no integer execution assertion.'},'trend_correlation':'not_identified_no_frozen_aligned_benchmark','independent_event_clusters':1,'independent_result_count_not_established':True}
def main():
 p=argparse.ArgumentParser();p.add_argument('--nav'); a=p.parse_args();out=Path(__file__).resolve().parent;base=out.parents[1]
 report={'preregistration_sha256':hashlib.sha256((out/'preregistration.json').read_bytes()).hexdigest(),'prices':{}}
 for coin in ['usdcusd','usdtusd']:
  path=base/'03-usd-prices/local-data'/f'{coin}-daily.csv';rows=[]
  for r in csv.DictReader(path.open()):
   rows.append({'date':dt.datetime.fromtimestamp(int(r['timestamp']),UTC).date().isoformat(),**{k:float(r[k]) for k in ['open','high','low','close','volume']}})
  assert len({r['date'] for r in rows})==len(rows)
  gaps=[(a['date'],b['date']) for a,b in zip(rows,rows[1:]) if (date(b['date'])-date(a['date'])).days!=1]
  event=[r for r in rows if '2023-03-10'<=r['date']<='2023-03-20']
  report['prices'][coin]={'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'rows':len(rows),'gaps':gaps,'event_min_close':min(event,key=lambda r:r['close']),'event_min_daily_low_non_executable':min(event,key=lambda r:r['low']),'event_close_recovery_marker':recovery(rows,.995,'2023-03-10','2023-04-19','close') if coin=='usdcusd' else None}
 if a.nav:
  nr=[]
  for r in csv.DictReader(Path(a.nav).open()):
   t=int(r['timestamp']); pd=int(r['price_day']); assert pd==t//86400*86400-86400; assert int(r['price_available_at'])<=t
   h=float(r['fixed_lp_2500_zeroentry_nocost'])
   nr.append({'timestamp':r['utc'].replace('+00:00','Z'),'price_day':dt.datetime.fromtimestamp(pd,UTC).date().isoformat(),'q0':h*float(r['unit_lp_usdc_zero']),'q1':h*float(r['unit_lp_usdt_zero']),'nav':float(r['deployed_2500_zeroentry_zeroexit_nocost'])})
  report['nav']=analyze_nav(nr);report['nav_input_sha256']=hashlib.sha256(Path(a.nav).read_bytes()).hexdigest()
 else:report['nav_status']='pending_04; no NAV inference from price alone'
 (out/'diagnostics.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
