import argparse,csv,json
from pathlib import Path
from fractions import Fraction as F
P=Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('--reference',type=Path,required=True);a=ap.parse_args()
def read(p):return list(csv.DictReader(p.open()))
def key(r):return tuple(r[k] for k in ['scenario_id','view','capital','frequency'])
ours={key(r):r for r in read(P/'correlation-summary.csv')};ref=read(a.reference/'correlation-summary.csv');deltas=[];bad=[]
assert len(ours)==len(ref)==288
for r in ref:
 x=ours[key(r)];d=abs(float(x['pearson_btc_lagged_sma200_gross_reference'])-float(r['btc_lagged_sma200_gross_reference']));deltas.append(d)
 if d>1e-10 or x['n']!=r['n'] or ('counterfactual' in x['classification'])!=('counterfactual' in r['classification']):bad.append(key(r))
b={r['date']:r for r in read(P/'benchmark-endpoints.csv')};bend=[]
for r in read(a.reference/'benchmark-endpoints.csv'):
 exact=float(F(b[r['end']]['pnl5000']))*int(r['capital'])/5000;delta=abs(exact-float(r['pnl']));bend.append(delta);assert delta<1e-8
ep={(r['scenario_id'],r['view'],r['capital']):r for r in read(P/'case-endpoints.csv')};ed=[]
for r in read(a.reference/'case-endpoints.csv'):
 x=ep[r['scenario_id'],r['view'],r['capital']]
 for field in ['strategy_pnl','benchmark_pnl','benchmark_return']:ed.append(abs(float(F(x[field]))-float(r[field])))
assert max(ed)<1e-8
partial={(r['scenario_id'],r['capital']):r for r in read(P/'october-partial.csv')};pd=[]
for r in read(a.reference/'case-endpoints.csv'):
 if r['view'].startswith('october'):
  x=partial[r['scenario_id'],r['capital']]
  for k,field in [('strategy_return','october_partial_strategy_return'),('benchmark_return','october_partial_benchmark_return')]:pd.append(abs(float(F(x[k]))-float(r[field])))
assert max(pd)<1e-10 and not bad
result={'all_288_correlations_pass_1e10':True,'maximum_correlation_abs_difference':max(deltas),'all_labels_and_observation_counts_match':True,'benchmark_endpoint_max_abs_difference':max(bend),'october_partial_max_abs_difference':max(pd),'case_endpoint_max_abs_difference':max(ed),'mismatches':bad,'comparison_not_calculation_dependency':True}
(P/'comparison.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
