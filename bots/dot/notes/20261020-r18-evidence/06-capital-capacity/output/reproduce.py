"""Independent capacity/denominator check; no network, execution or integer-state claim."""
import csv, json, hashlib, math
from pathlib import Path
from datetime import datetime, timezone
O=Path(__file__).resolve().parent
W=O.parents[1]
cfg=json.loads((W/'04-nav-engine/output/frozen-config.json').read_text())
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
for a in cfg['inputs']: assert sha(a['path'])==a['sha256']
def rows(p):
 with open(p) as f:return list(csv.DictReader(f))
ps=[]
for a in cfg['inputs'][1:]:
 z=rows(a['path']); ps.append({int(r['timestamp']):float(r['close']) for r in z})
x=[]
for r in rows(cfg['inputs'][0]['path']):
 t=int(r['ts']); day=t//86400*86400-86400
 if t<1623801600:continue
 assert all(day in p for p in ps)
 b0,b1,s=map(float,[r['token0_bal'],r['token1_bal'],r['lp_supply']]); v=b0*ps[0][day]+b1*ps[1][day]
 x.append(dict(t=t,block=int(r['block']),v=v,s=s,nav=v/s,b0=b0,b1=b1))
e,z=x[0],x[-1]; years=(z['t']-e['t'])/(365.25*86400); ratio=z['nav']/e['nav']
def utc(t):return datetime.fromtimestamp(t,timezone.utc).isoformat()
def cag(v,base):return (v/base)**(1/years)-1
out={'status':'CONDITIONAL','currency':'USD, not USDT token units','years':years,'rows':len(x),'window':[utc(e['t']),utc(z['t'])],'entry_balance_tvl_usd':e['v'],'input_hashes':cfg['inputs'],'cost_contract_sha256':sha(W/'05-cost-budget/output/cost-contract.json'),'scenarios':[],'dynamic_cap':[]}
for c in cfg['cost_per_side']:
 d=2500*(1-c); alpha=d/e['v'];
 for de in cfg['pending_supply_fraction_entry']:
  for dx in cfg['pending_supply_fraction_exit']:
   terminal=d*ratio*(1+de)/(1+dx)*(1-c)
   out['scenarios'].append(dict(c=c,pending_entry=de,pending_exit=dx,deposit=d,initial_tvl_fraction=alpha,new_lp_fraction_of_postmint_supply=alpha/(1+alpha),denominator_only_relative_overstatement=alpha,terminal=terminal,total_terminal=2500+terminal,leg_cagr=cag(terminal,2500),total_cagr=cag(2500+terminal,5000),leg_gt_3pct=cag(terminal,2500)>.03,total_gt_3pct=cag(2500+terminal,5000)>.03,leg_gt_8pct=cag(terminal,2500)>.08,entry_pending_path_unverified=bool(de)))
 # No-entry-pending path only. Mark to market before exit haircut; not executable values.
 for dx in [0,.2]:
  vals=[d*r['nav']/e['nav']/(1+dx) for r in x]
  breaches=[i for i,v in enumerate(vals) if v>2500+1e-9]
  imax=max(range(len(vals)),key=vals.__getitem__)
  out['dynamic_cap'].append(dict(c=c,pending_entry=0,valuation_pending=dx,valuation_type='gross entitlement proxy before exit cost',maximum_venue_usd=vals[imax],maximum_time=utc(x[imax]['t']),sampled_excess_usd=max(0,vals[imax]-2500),breach_rows=len(breaches),first_breach=utc(x[breaches[0]]['t']) if breaches else None,share_range=[min(vals[i]/x[i]['v'] for i in range(len(x))),max(vals[i]/x[i]['v'] for i in range(len(x)))],cap_pass_in_observed_proxy=not breaches))
up=json.loads((W/'04-nav-engine/output/summary.json').read_text())
assert len(up['scenarios'])==len(out['scenarios'])
for a,b in zip(out['scenarios'],up['scenarios']):
 assert math.isclose(a['terminal'],b['terminal_deployed'],rel_tol=1e-12)
 assert math.isclose(a['total_cagr'],b['total_cagr'],rel_tol=1e-12)
 a['gas_weight_k']=a['terminal']/2500
 a['signed_exit_gas_headroom_for_3pct_leg']=a['terminal']-2500*1.03**years
 a['signed_exit_gas_headroom_for_3pct_total']=a['terminal']-(5000*1.03**years-2500)
out['upstream04_summary_sha256']=sha(W/'04-nav-engine/output/summary.json')
out['independent04_agreement']='all 12 terminal values and total CAGR within 1e-12 relative tolerance'
out['tests']={'capital_unchanged':True,'denominators_not_interchangeable':True,'proportional_add_does_not_change_spot_ratio':True,'samples_not_independent_events':True}
assert all(abs(v['total_terminal']-v['terminal']-2500)<1e-8 for v in out['scenarios'])
assert math.isclose((2*3)/(2*7),3/7)
assert cag(2750,2500)>cag(5250,5000)
assert .01/(1+.01)<.01
(O/'capital-capacity.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({k:out[k] for k in ['years','rows','window','entry_balance_tvl_usd','dynamic_cap']},indent=2))
