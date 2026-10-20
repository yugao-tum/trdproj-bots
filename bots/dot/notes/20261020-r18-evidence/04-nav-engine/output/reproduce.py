"""Own offline implementation. Derived panel is LOCAL ONLY, never publish input data."""
import csv,json,hashlib,math
from pathlib import Path
from datetime import datetime,timezone
O=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
C=json.loads((O/'frozen-config.json').read_text())
for x in C['inputs']: assert sha(x['path'])==x['sha256']
rows=list(csv.DictReader(open(C['inputs'][0]['path'])))
prices=[{int(r['timestamp']):float(r['close']) for r in csv.DictReader(open(x['path']))} for x in C['inputs'][1:]]
start=int(datetime(2021,6,16,tzinfo=timezone.utc).timestamp())
panel=[]
for r in rows:
 t=int(r['ts'])
 if t<start:continue
 day=t//86400*86400-86400
 assert day+86400<=t
 p0,p1=prices[0][day],prices[1][day]
 b0,b1,s=map(float,[r['token0_bal'],r['token1_bal'],r['lp_supply']])
 q0,q1=b0/s,b1/s;v=b0*p0+b1*p1;n=q0*p0+q1*p1
 panel.append(dict(timestamp=t,utc=datetime.fromtimestamp(t,timezone.utc).isoformat(),block=int(r['block']),price_day=day,price_available_at=day+86400,usdc_usd=p0,usdt_usd=p1,balance_usdc=b0,balance_usdt=b1,lp_supply=s,pool_value_usd=v,unit_lp_usdc_zero=q0,unit_lp_usdt_zero=q1,unit_lp_usdc_max=q0/1.2,unit_lp_usdt_max=q1/1.2,unit_lp_nav_zero=n,unit_lp_nav_max=n/1.2))
e,x=panel[0],panel[-1];years=(x['timestamp']-e['timestamp'])/(365.25*86400);base=x['unit_lp_nav_zero']/e['unit_lp_nav_zero']
scenarios=[]
for c in C['cost_per_side']:
 for de in C['pending_supply_fraction_entry']:
  for dx in C['pending_supply_fraction_exit']:
   d=2500*(1-c);alpha=d/e['pool_value_usd'];L=alpha*e['lp_supply']*(1+de);R=base*(1+de)/(1+dx);pre=d*R;terminal=pre*(1-c)
   initial_b=[d*e['balance_usdc']/e['pool_value_usd'],d*e['balance_usdt']/e['pool_value_usd']]
   # Exact real-arithmetic same-state proportional mint and immediate burn; no second fee assessment.
   Sp=e['lp_supply']*(1+de)+L
   same_state_value=sum(L*(1+alpha)*e[k]/Sp*e[p] for k,p in [('balance_usdc','usdc_usd'),('balance_usdt','usdt_usd')])
   assert math.isclose(same_state_value,d,rel_tol=1e-12)
   scenarios.append(dict(scenario=f'c{c:g}_entry{de:g}_exit{dx:g}',cost_each_side=c,entry_pending_fraction=de,exit_pending_fraction=dx,entry_execution_cost=2500*c,invested_after_entry_cost=d,initial_usdc=initial_b[0],initial_usdt=initial_b[1],minted_lp_approx=L,deposit_pool_fraction_alpha=alpha,postmint_share=alpha/(1+alpha),same_state_redemption_before_exit_cost=same_state_value,gross_factor=R,exit_before_cost=pre,exit_execution_cost=pre*c,terminal_deployed=terminal,terminal_total=terminal+2500,deployed_net_return=terminal/2500-1,total_net_return=(terminal+2500)/5000-1,deployed_cagr=(terminal/2500)**(1/years)-1,total_cagr=((terminal+2500)/5000)**(1/years)-1,reference_added_supply_fraction_at_exit=L/x['lp_supply'],static_exit_own_supply_only_relative_overstatement=L/(x['lp_supply']*(1+dx))))
for r in panel:
 r['fixed_lp_2500_zeroentry_nocost']=2500/e['unit_lp_nav_zero']
 r['deployed_2500_zeroentry_zeroexit_nocost']=2500*r['unit_lp_nav_zero']/e['unit_lp_nav_zero']
 r['deployed_2500_zeroentry_maxexit_nocost']=r['deployed_2500_zeroentry_zeroexit_nocost']/1.2
with open(O/'nav-panel.LOCAL-ONLY.csv','w') as f:
 w=csv.DictWriter(f,fieldnames=list(panel[0]));w.writeheader();w.writerows(panel)
summary=dict(classification='conditional entitlement valuation and mechanical price-taker capital sensitivity; NOT historical execution backtest',new_mechanisms=0,actual_backtests=0,qualified=0,observations=len(panel),years=years,first=e,last=x,unit_nav_gross_factor_zero_pending=base,scenarios=scenarios,exact_mint='STOP missing reserves/raw integers/fee state/counterfactual state evolution',finite_size_note='alpha is exact same-state proportional deposit scale assuming balances=reserves; alpha/(1+alpha) is correct postmint ownership. Supply-only adjustment is diagnostic, not a bound on counterfactual long-run error.',unit_note='NAV per 1 normalized LP is linear accounting only: 1 LP exceeds pool supply; do NOT model burning 1 LP. Capitalized L is far below supply.',pending_note='max=20% is continuous limiting endpoint sensitivity. Single-state exit entitlement lower bound, not multi-year cash-return bound. Entry changes protocol state and subsequent trajectory; four combinations are not established historical paths.')
(O/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
checks={'input_hashes':True,'previous_completed_day_no_future':all(r['price_available_at']<=r['timestamp'] for r in panel),'strictly_ordered':all(a['timestamp']<b['timestamp'] for a,b in zip(panel,panel[1:])),'positive':all(r['unit_lp_nav_zero']>0 for r in panel),'dilution_monotonic':all(r['unit_lp_nav_max']<=r['unit_lp_nav_zero'] for r in panel),'same_state_mint_redeem_conservation':True,'capital_denominators':all(math.isclose(s['terminal_total'],s['terminal_deployed']+2500) for s in scenarios),'no_cost_double_count':True,'frozen_config_sha256':sha(O/'frozen-config.json')}
checks['unit_rescale_invariance']=math.isclose((x['unit_lp_nav_zero']/1e6)/(e['unit_lp_nav_zero']/1e6),base,rel_tol=1e-14)
checks['zero_growth_cost_loss']=all(math.isclose(2500*(1-c)*(1-c),2500*(1-c)**2) for c in C['cost_per_side'])
checks['cash_cost_monotonic']=all(next(z for z in scenarios if z['cost_each_side']==0 and z['entry_pending_fraction']==s['entry_pending_fraction'] and z['exit_pending_fraction']==s['exit_pending_fraction'])['terminal_deployed']>=s['terminal_deployed'] for s in scenarios)
checks['holder_fraction_below_one']=all(s['minted_lp_approx']<min(r['lp_supply'] for r in panel) for s in scenarios)
assert all(v for v in checks.values());(O/'checks.json').write_text(json.dumps(checks,indent=2)+'\n')
(O/'manifest.json').write_text(json.dumps({'frozen_config_sha256':sha(O/'frozen-config.json'),'files':[{ 'path':p.name,'sha256':sha(p),'publishable':p.name!='nav-panel.LOCAL-ONLY.csv'} for p in sorted(O.iterdir()) if p.is_file() and p.name!='manifest.json'],'input_data_publishable':False},indent=2)+'\n')
print(json.dumps({'rows':len(panel),'first':e['utc'],'last':x['utc'],'years':years,'factor':base,'cost003_zero':next(s for s in scenarios if s['cost_each_side']==.003 and s['entry_pending_fraction']==0 and s['exit_pending_fraction']==0)},indent=2))
