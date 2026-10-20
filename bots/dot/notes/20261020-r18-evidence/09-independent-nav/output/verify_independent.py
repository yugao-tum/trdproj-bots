"""Independent Decimal/Fraction audit; no imports from sibling implementations.
Raw input remains local; output only fixed tiny samples and aggregate checks.
"""
import csv, json, hashlib, math
from decimal import Decimal as D, getcontext
from fractions import Fraction as F
from pathlib import Path
from datetime import datetime, timezone
getcontext().prec=55
C=Path(__file__).resolve().parents[4]
W=C/'workers/r18-proposal'; OUT=Path(__file__).resolve().parent
raw=C/'workers/r16-proposal/07-github-data/local-data/pool-balances.csv'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rows=list(csv.DictReader(raw.open()))
prices={s:{int(r['timestamp']):D(r['close']) for r in csv.DictReader((W/f'03-usd-prices/local-data/{s}-daily.csv').open())} for s in ['usdcusd','usdtusd']}
def point(r):
 t=int(r['ts']); bar=t//86400*86400-86400
 assert bar+86400<=t
 p=[prices[s][bar] for s in ['usdcusd','usdtusd']]
 b=[D(r['token0_bal']),D(r['token1_bal'])]; supply=D(r['lp_supply'])
 return {'ts':t,'block':int(r['block']),'source_bar_start':bar,'source_bar_end':bar+86400,'balances':b,'supply':supply,'prices':p,'nav':sum(x*y for x,y in zip(b,p))/supply}
selected=[r for r in rows if int(r['ts'])>=1623801600]
a,z=point(selected[0]),point(selected[-1]); R=z['nav']/a['nav']; years=D(z['ts']-a['ts'])/D(86400)/D('365.25')
scenarios=[]
for c in map(D,['0','.003','.006']):
 for de in map(D,['0','.2']):
  for dx in map(D,['0','.2']):
   # Derive independently via deposited token quantities and minted LP units.
   pool_value=sum(b*p for b,p in zip(a['balances'],a['prices']))
   deposit_fraction=D(2500)*(1-c)/pool_value
   minted=deposit_fraction*a['supply']*(1+de)
   exit_tokens=[minted*b/(z['supply']*(1+dx)) for b in z['balances']]
   cash=sum(b*p for b,p in zip(exit_tokens,z['prices']))*(1-c)
   formula=D(2500)*(1-c)**2*R*(1+de)/(1+dx)
   assert abs(cash-formula)<D('1e-45')
   scenarios.append({'cost':c,'entry_pending_fraction':de,'exit_pending_fraction':dx,'terminal_leg':cash,'terminal_total':D(2500)+cash,'leg_cagr':(cash/D(2500))**(1/years)-1,'total_cagr':((D(2500)+cash)/D(5000))**(1/years)-1})
# Independent exhaustive small-domain integer proof checks, no sibling test calls.
n=0; dust=None
for S in range(1,80):
 M=(S-1)//5
 for root in range(1,35):
  for old in range(1,root+1):
   m=(S*(root-old))//(5*root+old)
   assert 5*m<S and m<=M
   for L,B in [(1,1),(1,S),(S,1),(S,7),(max(1,S//2),31)]:
    amt=(L*B)//(S+m)
    lo=(L*B)//(S+M); hi=(L*B)//S
    assert lo<=amt<=hi and (5*L*B)//(6*S)<=amt
    if m>0 and amt<F(5,6)*hi and dust is None: dust={'S':S,'root':root,'old_root':old,'m':m,'L':L,'B':B,'no_fee_output':hi,'fee_output':amt}
   n+=1
assert dust is not None
# Raw endpoint agreement and source semantics, read source not sibling implementation.
inspection=json.loads((W/'01-balance-semantics/output/inspection.json').read_text())
assert rows[0]==inspection['endpoint_rows'][0] and rows[-1]==inspection['endpoint_rows'][1]
source=json.loads((W/'01-balance-semantics/local-evidence/scripts__get_specific_pool_info.py.evidence.json').read_text())['content']
sourcehash=hashlib.sha256(source.encode()).hexdigest()
assert sourcehash=='ad9ea9540eaf6cbfa72faf0f72ab831d9f801ab1a5919dfbc95b309a0b9d0c15'
assert 'balanceOf' in source and 'totalSupply' in source
# Fixed event samples: baseline strictly before preregistered start and first/last event snapshot.
pr=json.loads((W/'07-tail-events/output/preregistration.json').read_text())
parse=lambda s:int(datetime.fromisoformat(s.replace('Z','+00:00')).timestamp())
start=parse(pr['fixed_event']['nav_start']); end=parse(pr['fixed_event']['nav_end_exclusive'])
event=[r for r in selected if start<=int(r['ts'])<end]
baseline=point(next(r for r in reversed(selected) if int(r['ts'])<start))
eventpoints=[point(event[0]),point(event[-1])]
res={'classification':'CONDITIONAL independent arithmetic reproduction, NOT realized cash or exact integer historical replay','input_sha256':sha(raw),'expected_input_sha256':'531dd907a5337c9bbeda5dba592ce1dfec3122803c1e98e9c59cf6913333adf6','source_content_sha256':sourcehash,'raw_rows':len(rows),'eligible_rows':len(selected),'raw_endpoint_agreement':True,'first':a,'last':z,'years':years,'gross_nav_factor':R,'all_required_prior_day_prices_present':all((int(r['ts'])//86400*86400-86400) in prices[s] for r in selected for s in prices),'scenarios':scenarios,'integer_states_tested':n,'integer_rounding_counterexample':dust,'event_preregistration_sha256':sha(W/'07-tail-events/output/preregistration.json'),'fixed_event_baseline':baseline,'fixed_event_endpoint_samples':eventpoints,'new_mechanisms':0,'realized_executions':0,'qualified':0}
assert res['input_sha256']==res['expected_input_sha256']
(OUT/'independent-results.json').write_text(json.dumps(res,indent=2,default=str)+'\n')
print(json.dumps({'eligible_rows':len(selected),'gross_factor':str(R),'years':str(years),'integer_states':n,'dust':dust,'scenario0':scenarios[0]},default=str))
# Consume outputs only AFTER the independent computation above; never import implementation.
summarypath=W/'04-nav-engine/output/summary.json'
if summarypath.exists():
 other=json.loads(summarypath.read_text()); comparisons=[]
 def near(x,y,tol=D('1e-11')):
  err=abs(D(str(x))-D(str(y))); assert err<=tol, (x,y,err)
  return str(err)
 assert other['observations']==len(selected)
 near(R,other['unit_nav_gross_factor_zero_pending'],D('1e-14'))
 for ours in scenarios:
  match=[s for s in other['scenarios'] if D(str(s['cost_each_side']))==ours['cost'] and D(str(s['entry_pending_fraction']))==ours['entry_pending_fraction'] and D(str(s['exit_pending_fraction']))==ours['exit_pending_fraction']]
  assert len(match)==1
  s=match[0]; errs={}
  for x,y in [('terminal_leg','terminal_deployed'),('terminal_total','terminal_total'),('leg_cagr','deployed_cagr'),('total_cagr','total_cagr')]:errs[x]=near(ours[x],s[y])
  comparisons.append({'scenario':s['scenario'],'absolute_error':errs})
 wanted={p['ts']:p for p in [a,z,baseline,*eventpoints]}
 audited=[]
 for p in csv.DictReader((W/'04-nav-engine/output/nav-panel.LOCAL-ONLY.csv').open()):
  t=int(p['timestamp'])
  if t not in wanted:continue
  v=wanted[t]
  assert int(p['price_day'])==v['source_bar_start'] and int(p['price_available_at'])<=t
  error=near(v['nav'],p['unit_lp_nav_zero'],D('.002')) # absolute tolerance <1e-15 relative at 1e12 NAV per whole LP
  near(v['nav']*D(5)/6,p['unit_lp_nav_max'],D('.002'))
  audited.append({'timestamp':t,'unit_nav_absolute_error':error})
 assert len(audited)==len(wanted)
 compare={'status':'PASS conditional arithmetic, not execution validity','summary_sha256':sha(summarypath),'frozen_config_sha256':sha(W/'04-nav-engine/output/frozen-config.json'),'scenarios':comparisons,'fixed_endpoint_and_preregistered_event_samples':audited,'rounding_tolerance':'cash and CAGR absolute 1e-11; unit LP NAV absolute .002 because unit LP NAV scale ~1e12; exact Decimal inputs derive from rounded author CSV'}
 (OUT/'comparison.json').write_text(json.dumps(compare,indent=2)+'\n')
 print('04 12 scenario comparisons and 5 fixed sample rows PASS')
extra={}
cp=W/'05-cost-budget/output/cost-results.json'
if cp.exists():
 x=json.loads(cp.read_text()); count=0
 for row in x['rows']:
  de,dx=map(D,row['scenario'].replace('entry','').replace('exit','').split('_'))
  c=D(str(row['each_side_haircut'])); k=R*(1+de)/(1+dx)*(1-c)**2
  for label,target in [('break_even',D(2500)),('investment_3pct',D(2500)*D('1.03')**years),('total_3pct',D(5000)*D('1.03')**years-D(2500)),('total_8pct',D(5000)*D('1.08')**years-D(2500))]:
   near(D(2500)*k-target,row['budgets'][label]['signed_terminal_headroom_USD'],D('1e-9')); count+=1
 extra['cost_budget']={'status':'PASS signed headroom formula, gas not estimated','checks':count,'sha256':sha(cp)}
bp=W/'08-hold-benchmark/output/benchmark-results.json'
if bp.exists():
 x=json.loads(bp.read_text()); checks=[]
 for row in x['scenarios']:
  c=D(str(row['cost_per_side'])); scale=D(2500)*(1-c)/sum(b*p for b,p in zip(a['balances'],a['prices']))
  terminal=scale*sum(b*p for b,p in zip(a['balances'],z['prices']))*(1-c)
  near(terminal,row['hold_terminal_before_unknown_gas'])
  checks.append({'cost':str(c),'terminal':str(terminal)})
 extra['fixed_token_hold']={'status':'PASS fixed initial tokens and two cost deductions','sha256':sha(bp),'scenarios':checks}
cap=W/'06-capital-capacity/output/capital-capacity.json'
if cap.exists():
 x=json.loads(cap.read_text()); tvl=sum(b*p for b,p in zip(a['balances'],a['prices']))
 near(tvl,x['entry_balance_tvl_usd'],D('1e-7'))
 for row in x['scenarios']:
  c=D(str(row['c'])); alpha=D(2500)*(1-c)/tvl
  near(alpha,row['initial_tvl_fraction']); near(alpha/(1+alpha),row['new_lp_fraction_of_postmint_supply'])
 extra['capacity']={'status':'PASS entry TVL, alpha and postmint share; not proof of finite-path accuracy','sha256':sha(cap)}
(OUT/'cross-checks.json').write_text(json.dumps(extra,indent=2)+'\n')
print('05/06/08 available output arithmetic comparisons PASS')
tp=W/'07-tail-events/output/diagnostics.json'
if tp.exists() and 'nav' in (td:=json.loads(tp.read_text())):
 points=[point(r) for r in selected]; ev=[p for p in points if start<=p['ts']<end]
 trough=min(ev,key=lambda p:p['nav']); loss=trough['nav']/baseline['nav']-1
 peak=ev[0]['nav']; mdd=D(0)
 for p in ev:
  peak=max(peak,p['nav']);mdd=min(mdd,p['nav']/peak-1)
 near(loss,td['nav']['event']['minimum_vs_fixed_baseline']);near(mdd,td['nav']['event']['sampled_peak_to_trough'])
 assert trough['ts']==parse(td['nav']['event']['trough']['timestamp'])
 # Last row per UTC day; recovery starts after trough, no future-day prices.
 daily={p['ts']//86400:p for p in points}; run=[]; recovery=None
 for day,p in sorted(daily.items()):
  if not(trough['ts']<p['ts']<parse(pr['fixed_event']['recovery_end_exclusive'])):continue
  if p['nav']>=baseline['nav']:
   if run and day!=run[-1]+1:run=[]
   run.append(day)
   if len(run)==3:recovery={'first_day':datetime.fromtimestamp(run[0]*86400,timezone.utc).date().isoformat(),'confirmed_day':datetime.fromtimestamp(day*86400,timezone.utc).date().isoformat()};break
  else:run=[]
 assert recovery==td['nav']['event']['recovery']
 extra['tail_event']={'status':'PASS independently computed all fixed-event observations and three-day recovery, no parameter/window search','sha256':sha(tp),'fixed_baseline_loss':str(loss),'event_mdd':str(mdd),'trough_timestamp':trough['ts'],'recovery':recovery}
 (OUT/'cross-checks.json').write_text(json.dumps(extra,indent=2)+'\n')
 print('07 fixed event trough, loss, MDD, three-day recovery PASS')
