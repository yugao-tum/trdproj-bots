#!/usr/bin/env python3
"""Portable quant018 supplement reproduction. Reads the two attributed pinned CSVs; never executes competitor code or fetches network data."""
from collections import defaultdict
from fractions import Fraction as F
from pathlib import Path
import argparse,csv,hashlib,json,math,statistics
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def gitblob(b): return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
def rows(p):
 with p.open(newline='') as h:return list(csv.DictReader(h))
def compact(x):
 if isinstance(x,F):return {'decimal':float(x),'exact':str(x)}
 if isinstance(x,dict):return {k:compact(v) for k,v in x.items()}
 if isinstance(x,(list,tuple)):return [compact(v) for v in x]
 return x

def pearson(x,y):
 """Two-pass centered Pearson, independent of upstream numpy implementation."""
 assert len(x)==len(y) and len(x)>1
 x=list(map(float,x)); y=list(map(float,y)); n=len(x)
 a=math.fsum(x)/n; b=math.fsum(y)/n
 xx=[v-a for v in x]; yy=[v-b for v in y]
 den=math.sqrt(math.fsum(v*v for v in xx)*math.fsum(v*v for v in yy))
 return math.fsum(u*v for u,v in zip(xx,yy))/den if den else None

def brier(probs,outcomes):
 """Equivalent quadratic identity; normalized market inputs supplied separately."""
 assert sum(outcomes)==1
 return 1+sum(p*p for p in probs)-2*sum(p*y for p,y in zip(probs,outcomes))

def select_no(p,model,epsilon=F('1e-12')):
 if p is None:return None
 paid=1-p+F('0.01')
 if 0<paid<1 and p-model+epsilon >= F('.02'):return paid
 return None

def p1(buckets,events):
 grouped=defaultdict(list)
 for r in buckets: grouped[r['slug']].append(r)
 assert len(events)==43 and len(buckets)==242 and len(grouped)==43
 assert len({(r['slug'],r['label']) for r in buckets})==242
 score=[]
 for e in events:
  g=grouped[e['slug']]; outcomes=[int(r['resolved_yes']) for r in g]
  d={'slug':e['slug'],'week':e['week_start'],'model':brier([F(r['p_model']) for r in g],outcomes)}
  for kind in ['first','start']:
   if all(r[kind+'_p']!='' for r in g):
    vals=[F(r[kind+'_p']) for r in g]; d[kind]=brier([p/sum(vals) for p in vals],outcomes)
    assert abs(float(d[kind])-float(e['brier_mkt_'+kind]))<1e-14
  assert abs(float(d['model'])-float(e['brier_model']))<1e-14
  score.append(d)
 complete=[s for s in score if 'start' in s]
 assert len(complete)==34
 means={v:sum(s[v] for s in complete)/34 for v in ['first','start','model']}
 variants={}
 for kind in ['start','entry','first']:
  profit=[]; by_event=defaultdict(lambda:{'shares':0,'outlay':F(0),'payout':F(0),'profit':F(0)})
  for r in buckets:
   if r['strait']!='Bab el-Mandeb Strait':continue
   p=F(r[kind+'_p']) if r[kind+'_p'] else None
   paid=select_no(p,F(r['p_model']))
   if paid is not None:
    gain=1-int(r['resolved_yes'])-paid
    a=by_event[r['slug']];a['shares']+=1;a['outlay']+=paid;a['payout']+=1-int(r['resolved_yes']);a['profit']+=gain
    profit.append(gain)
  agg={k:sum(a[k] for a in by_event.values()) for k in ['shares','outlay','payout','profit']}
  agg.update({'available_events':sum(e['strait']=='Bab el-Mandeb Strait' for e in events),'traded_events':len(by_event),'winning_events':sum(a['profit']>0 for a in by_event.values()),'losing_events':sum(a['profit']<0 for a in by_event.values()),'share_median':statistics.median(profit),'event_median':statistics.median(a['profit'] for a in by_event.values())})
  variants[kind]=agg
 base=variants['start'];n=base['shares'];p=base['profit']
 uncertainty=brier_uncertainty(complete)
 return {'paired_uncertainty':uncertainty,'event_rows':43,'bucket_rows':242,'common_rows':34,'common_start_dates_not_independent_weeks':len({s['week'] for s in complete}),'mean_brier_common_rows':means,'start_market_minus_model':means['start']-means['model'],'first_market_minus_model':means['first']-means['model'],'cash_original_variants':variants,'additional_fixed_trade_cost':{'already_charged_spread':n*F('.01'),'safety_buffer_not_cash_cost':F('.01'),'profit_after_1c':p-n*F('.01'),'profit_after_5c':p-n*F('.05'),'zero_profit_additional_per_share':p/n,'zero_profit_total_additional':p,'units':'1 USD payout units; not executed cash or capital/time returns'},'unknown':['model as-of release/vintage','fills','actual historical fees','cash entry','settlement','redemption/cash release']}

def brier_uncertainty(scores):
 """Explicit scalar resampling from the frozen 02 protocol, not copied code."""
 import numpy as np
 def percentile(v,p):
  v=sorted(v);z=(len(v)-1)*p;a=math.floor(z);b=math.ceil(z)
  return v[a]+(z-a)*(v[b]-v[a])
 grouped=defaultdict(list)
 for s in scores:grouped[s['week']].append(s)
 result={}
 for mode,seed in [('date_cluster',20261020),('event_iid',20261021)]:
  groups=[grouped[k] for k in sorted(grouped)] if mode=='date_cluster' else [[s] for s in scores]
  # Each sampled event has equal weight; groups are not averaged with equal weights.
  totals=[[math.fsum(float(s[k]) for s in group) for k in ['first','start','model']] for group in groups]
  counts=[len(g) for g in groups];n=len(groups)
  draws=np.random.Generator(np.random.PCG64(seed)).integers(0,n,size=(20000,n))
  values={k:[] for k in ['first_minus_model','start_minus_model','first_minus_start']}
  for draw in draws:
   ids=[int(i) for i in draw];den=sum(counts[i] for i in ids)
   means=[math.fsum(totals[i][j] for i in ids)/den for j in range(3)]
   for k,v in zip(values,[means[0]-means[2],means[1]-means[2],means[0]-means[1]]):values[k].append(v)
  result[mode]={'seed':seed,'draws':20000,'contrast_CI95':{k:[percentile(v,.025),percentile(v,.975)] for k,v in values.items()}}
 return result


def main():
 a=argparse.ArgumentParser();a.add_argument('--repo',type=Path,required=True);a.add_argument('--output',type=Path,required=True);args=a.parse_args()
 sources={}
 for name,blob in [('buckets','b23cc8339dfff1fc071f8c5e7668f08b2c86a399'),('events','b2431ed00027544d6b030b2a2b2065b90425480c')]:
  p=args.repo/'bots/quant/notes/q018-price-test'/(name+'.csv');raw=p.read_bytes()
  # Ordinary Git checkout bytes or the separately documented one-extra-LF export.
  assert gitblob(raw)==blob or (raw[-1:]==b'\n' and gitblob(raw[:-1])==blob), 'Pinned source blob mismatch: '+name
  sources[name]=p
 out={'source_commit':'4a7357a7f81bec8a70b4331ebfb7ba16bc5e24be','attribution':'quant-018 / quant-012','scope':'Frozen-column retrospective supplement, no observed fills or new mechanism','result':compact(p1(rows(sources['buckets']),rows(sources['events'])))}
 args.output.write_text(json.dumps(out,indent=2)+'\n')
if __name__=='__main__':main()
