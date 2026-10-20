#!/usr/bin/env python3
import csv,hashlib,json,sys,types,datetime
from pathlib import Path
OUT=Path(__file__).resolve().parent
ROOT=Path('retained-inputs')
SRC=ROOT/'workers/operator-cold-reproduction/packages/reproduction/spot_screen.py'
DATA=ROOT/'workers/data-probe/data/history/spot_daily.csv'
OLD=ROOT/'results/spot-screen/summary.json'
PROVENANCE=DATA.parent/'manifest.json'
INPUTS=[SRC,DATA,OLD,PROVENANCE,OUT/'PREREGISTRATION.md']
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
before={str(p):digest(p) for p in INPUTS}
def module(name,text):
 m=types.ModuleType(name);m.__file__=str(SRC);sys.modules[name]=m;exec(compile(text,str(SRC),'exec'),m.__dict__);m.STRATEGIES={'C21':m.STRATEGIES['C21']};return m
text=SRC.read_text()
old='selected = ["SOLUSDT"] if c21_signal(closes["SOLUSDT"], index) else []'
new='''latest = c21_signal(closes["SOLUSDT"], index)
            preceding = c21_signal(closes["SOLUSDT"], index - 1)
            confirmed = latest if latest == preceding else portfolio.has_position()
            selected = ["SOLUSDT"] if confirmed else []'''
assert text.count(old)==1
b=module('baseline',text);v=module('variant',text.replace(old,new))
bars,dates,quality=b.load_and_precheck(DATA)
assert not quality['errors']
base,bd,bt,bm=b.build_summary(bars,dates,quality)
variant,vd,vt,vm=v.build_summary(bars,dates,quality)
original=json.loads(OLD.read_text())['strategies']['C21']
assert base['strategies']['C21']==original,'Baseline differs from frozen C21'
# No lookahead: changing execution-day and later closes cannot alter either confirmation signal.
closes=[z.close for z in bars['SOLUSDT']]
checks=0
for i,d in enumerate(dates):
 if b.SIM_START<=d<=b.SIM_END and d.weekday()==0:
  mutated=closes[:i]+[999999.]*(len(closes)-i)
  assert (b.c21_signal(closes,i),b.c21_signal(closes,i-1))==(b.c21_signal(mutated,i),b.c21_signal(mutated,i-1));checks+=1
# Behavioral synthetic signal tests and signal-data invariance.
assert b.c21_signal([1.0]*199+[2.0],200) is True
assert b.c21_signal([2.0]*199+[1.0],200) is False
assert b.c21_signal([1.0]*200,200) is False
try: b.c21_signal([1.0]*199,199)
except ValueError: pass
else: raise AssertionError('warmup guard missing')

def writecsv(name,rows):
 if rows:
  with (OUT/name).open('w') as f:
   w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
writecsv('baseline-trades.csv',bt);writecsv('variant-trades.csv',vt)
writecsv('baseline-daily.csv',bd);writecsv('variant-daily.csv',vd)
pairs=[];comparisons=[]
for cost in ['0.003','0.006']:
 bs=base['strategies']['C21']['scenarios'][cost];vs=variant['strategies']['C21']['scenarios'][cost]
 for period in ['2024','oos_2025','full']:
  x,y=bs['periods'][period],vs['periods'][period]
  keys=['net_pnl_usdt','fees_usdt','notional_traded_usdt','trade_count','cagr','max_drawdown','total_return_on_start_equity','net_ex_best_month_usdt']
  comparisons.append({'cost':cost,'period':period,'baseline':{k:x[k] for k in keys},'variant':{k:y[k] for k in keys},'delta_net_pnl_usdt':y['net_pnl_usdt']-x['net_pnl_usdt'],'fees_saved_usdt':x['fees_usdt']-y['fees_usdt'],'variant_capital':y['capital_bound_diagnostics']})
 bx=[r for r in bd if r['cost_rate']==cost];vx=[r for r in vd if r['cost_rate']==cost]
 pb=pv=5000.
 for x,y in zip(bx,vx):
  assert x['date']==y['date']
  db=x['total_equity']-pb;dv=y['total_equity']-pv
  pairs.append({'cost':cost,'date':x['date'],'baseline_pnl':db,'variant_pnl':dv,'incremental_pnl':dv-db,'baseline_equity':x['total_equity'],'variant_equity':y['total_equity']});pb=x['total_equity'];pv=y['total_equity']
writecsv('paired-daily-pnl.csv',pairs)
# Every execution date's marked PnL, not fictitious independently attributable closed-trade pairs.
events=[]
for cost in ['0.003','0.006']:
 days=sorted(set(r['date'] for r in bt+vt if r['cost_rate']==cost))
 for day in days:
  br=[r for r in bt if r['cost_rate']==cost and r['date']==day];vr=[r for r in vt if r['cost_rate']==cost and r['date']==day]
  dayrow=next(r for r in pairs if r['cost']==cost and r['date']==day)
  events.append({'cost':cost,'date':day,'baseline_trades':len(br),'variant_trades':len(vr),'fees_saved':sum(r['fee'] for r in br)-sum(r['fee'] for r in vr),'baseline_signed_notional':sum(r['notional']*(1 if r['side']=='BUY' else -1) for r in br),'variant_signed_notional':sum(r['notional']*(1 if r['side']=='BUY' else -1) for r in vr),'same_day_incremental_marked_pnl':dayrow['incremental_pnl']})
writecsv('paired-execution-events.csv',events)
decisions=[]
held=False
for i,d in enumerate(dates):
 if b.SIM_START<=d<=b.SIM_END and d.weekday()==0:
  latest=b.c21_signal(closes,i);preceding=b.c21_signal(closes,i-1)
  chosen=latest if latest==preceding else held
  decisions.append({'date':d.isoformat(),'latest_sma_signal':latest,'preceding_sma_signal':preceding,'previous_held':held,'variant_selected':chosen,'baseline_selected':latest,'different':chosen!=latest})
  for cost in ['0.003','0.006']:
   row=next(r for r in vd if r['date']==d.isoformat() and r['cost_rate']==cost)
   assert (row['holdings_close']>1e-9)==chosen
  held=chosen
writecsv('weekly-decisions.csv',decisions)

assert before=={str(p):digest(p) for p in INPUTS}
result={'phase':'real historical backtest, retrospective holdout','variant_rule':'two completed-day SMA confirmation, Monday-only','comparisons':comparisons,'baseline_exact_match':True,'monday_no_lookahead_checks':checks,'inputs_unchanged':True,'variant_scenarios':variant['strategies']['C21']['scenarios']}
(OUT/'results.json').write_text(json.dumps(result,indent=2))
(OUT/'source-manifest.json').write_text(json.dumps({'accessed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'local_cached_inputs':before,'data_fetch':'none; reused frozen official-data cache; no new external retrieval','original_source_url':json.loads(PROVENANCE.read_text())['source'],'original_acquisition_utc':json.loads(PROVENANCE.read_text())['generated_at_utc'],'model':'native OpenAI assistant; exact model identifier unavailable','task_count':1},indent=2))
print(json.dumps({'comparisons':comparisons,'no_lookahead_checks':checks},indent=2))
