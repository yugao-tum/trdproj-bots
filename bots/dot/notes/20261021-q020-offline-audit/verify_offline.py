#!/usr/bin/env python3
"""Independent standard-library arithmetic only. No imports/execution of source script, networking, or cache."""
import csv,json,statistics as st,datetime as dt,hashlib,argparse
from pathlib import Path
P=Path(__file__).resolve().parent
ap=argparse.ArgumentParser(description="Offline arithmetic on externally supplied, pinned quant derived inputs; never executes source code")
ap.add_argument('--source-dir', type=Path, required=True)
ap.add_argument('--output', type=Path, required=True)
a=ap.parse_args()
manifest=json.loads((P/'source_manifest.json').read_text())
for source in manifest:
    path=a.source_dir/source['file']
    assert hashlib.sha256(path.read_bytes()).hexdigest()==source['sha256_lf'], 'Input hash mismatch: '+source['file']
rows=list(csv.DictReader((a.source_dir/'tradable_fills.csv').open()))
obs=[r for r in rows if r['ask_observed']!='']
f=lambda r,k:float(r[k])
def summary(rs):
    out={'n':len(rs),'wins':sum(int(r['y']) for r in rs)}
    out['mean_ask']=st.mean(f(r,'ask_observed') for r in rs)
    out['fee_sensitivity']={str(rate):{'mean_fee':st.mean(rate*f(r,'ask_observed')*(1-f(r,'ask_observed')) for r in rs),'mean_net':st.mean(int(r['y'])-f(r,'ask_observed')-rate*f(r,'ask_observed')*(1-f(r,'ask_observed')) for r in rs),'median_net':st.median(int(r['y'])-f(r,'ask_observed')-rate*f(r,'ask_observed')*(1-f(r,'ask_observed')) for r in rs)} for rate in [0.05,0.04,0]}
    out['mean_plus1c_net']=st.mean(int(r['y'])-f(r,'ask_plus1c_same')-.05*f(r,'ask_plus1c_same')*(1-f(r,'ask_plus1c_same')) for r in rs)
    return out
errors={}
for key,calc in {'ask_observed':lambda r:f(r,'buy_yes'),'fee_observed':lambda r:.05*f(r,'ask_observed')*(1-f(r,'ask_observed')),'net_observed':lambda r:int(r['y'])-f(r,'ask_observed')-.05*f(r,'ask_observed')*(1-f(r,'ask_observed')),'capital_days':lambda r:(dt.datetime.fromisoformat(r['endDate'].replace('Z','+00:00')).timestamp()-int(r['buy_yes_ts']))/86400}.items():
    errors[key]=max(abs(f(r,key)-calc(r)) for r in obs)
ages=[(dt.datetime.fromisoformat(r['endDate'].replace('Z','+00:00')).timestamp()-int(r['buy_yes_ts']))/3600 for r in obs]
both=[r for r in obs if r['sell_yes']]
gaps=[abs(int(r['buy_yes_ts'])-int(r['sell_yes_ts']))/3600 for r in both]
notionals=[f(r,'buy_yes_size')*f(r,'ask_observed') for r in obs]
result={'fields':list(rows[0]),'rows':len(rows),'unique_slugs':len(set(r['slug'] for r in rows)),'priced':len(obs),'split_total':{s:sum(r['split']==s for r in rows) for s in ['discovery','holdout']},'unpriced':[{k:r[k] for k in ['slug','split','n_trades','y']} for r in rows if not r['ask_observed']], 'groups':{s:summary([r for r in obs if s=='pooled' or r['split']==s]) for s in ['pooled','discovery','holdout']},'max_absolute_reconstruction_errors':errors,'truncated_true':sum(r['truncated']=='True' for r in rows),'selected_ask_age_hours':{'min':min(ages),'median':st.median(ages),'max':max(ages),'outside_24_to_72':sum(not 24<=a<=72 for a in ages)},'ask_minus_bid_print':{'n':len(both),'mean':st.mean(f(r,'buy_yes')-f(r,'sell_yes') for r in both),'median':st.median(f(r,'buy_yes')-f(r,'sell_yes') for r in both),'negative':sum(f(r,'buy_yes')<f(r,'sell_yes') for r in both),'same_timestamp':sum(g==0 for g in gaps),'abs_timestamp_gap_hours_median':st.median(gaps),'abs_timestamp_gap_hours_max':max(gaps)},'selected_print_yes_equivalent_notional':{'n':len(notionals),'min':min(notionals),'median':st.median(notionals),'max':max(notionals),'at_least_200':sum(n>=200 for n in notionals)},'local_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [a.source_dir/s['file'] for s in manifest]}}
result.pop('unpriced',None)
a.output.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
