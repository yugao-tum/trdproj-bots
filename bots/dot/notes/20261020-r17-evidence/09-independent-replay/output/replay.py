#!/usr/bin/env python3
"""Offline, one-command isolated replay; existing replay directory is never overwritten."""
from pathlib import Path
import hashlib,json,shutil,subprocess,sys,csv
O=Path(__file__).resolve().parent
R=O.parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
name=sys.argv[1] if len(sys.argv)>1 else 'replay-local-only'
assert Path(name).name==name and name not in ('.','..')
D=O/name;D.mkdir(exist_ok=False)
W=D/'r17-proposal';W.mkdir();shutil.copy2(R/'INTERFACES.md',W/'INTERFACES.md')
(D/'r16-proposal').symlink_to(R.parent/'r16-proposal',target_is_directory=True)
names=['01-continuous-signals','02-next-open-ledger','03-capital-boundaries','05-same-budget-benchmarks','06-event-tail-diagnostics']
codes=['generate_signals.py','ledger_nextopen.py','check_capital.py','benchmark.py','analyze_events.py']
inputs=list((R.parent/'r16-proposal/01-freeze-inputs/output').glob('*.csv'))+[R.parent/'r16-proposal/02-frozen-signals/reproduce_frozen.py',R/'INTERFACES.md']
for n in names+['04-independent-cash-audit']:
 inputs += [p for p in (R/n/'output').iterdir() if p.is_file()]
before={str(p):sha(p) for p in inputs};dump(O/'source-sha-before.json',before)
for n,c in zip(names,codes):
 t=W/n/'output';t.mkdir(parents=True);shutil.copy2(R/n/'output'/c,t/c)
 (t/'RESULT.md').write_text('Isolated replay output. See outer RESULT.md; not an independent source report.\n')
 cmd=[sys.executable,str(t/c)]
 if n.startswith('02'):
  p=D/'r16-proposal/01-freeze-inputs/output'
  cmd+=['--signals',str(W/names[0]/'output/signals.csv'),'--panel',str(p/'panel_utc.csv'),'--opens',str(p/'open_extension_utc.csv'),'--out',str(t)]
 run=subprocess.run(cmd,text=True,capture_output=True);(t/'run.log').write_text(run.stdout+run.stderr)
 assert run.returncode==0,(n,run.stderr[-2000:])
compare={}
for n,files in [(names[0],['signals.csv','phase_sequence.csv','causal-tests.json','boundaries.json']), (names[1],['accounts.csv','trades.csv','metrics.json']), (names[2],['capital-results.json']), (names[3],['accounts.csv','trades.csv','metrics.json']), (names[4],['event_summary.json','event_pnl.csv','year_metrics.csv','benchmark_correlations.json'])]:
 for f in files:
  a=R/n/'output'/f;b=W/n/'output'/f
  compare[n+'/'+f]={'original':sha(a),'replay':sha(b),'byte_identical':sha(a)==sha(b)}
assert all(v['byte_identical'] for v in compare.values()),compare
audit=json.loads((R/'04-independent-cash-audit/output/audit-results.json').read_text());assert audit['pass']
# Own targeted audit: event accounting, fees, terminal close, gate states, cash continuity.
def read(p):return list(csv.DictReader(p.open()))
a=read(W/names[1]/'output/accounts.csv');t=read(W/names[1]/'output/trades.csv');maxerr=0.;picked={};capital={}
for sid in sorted(set(r['scenario_id'] for r in a)):
 rows=[r for r in a if r['scenario_id']==sid];assert len(rows)==1004
 idx={0,1003};idx.update(i for i,r in enumerate(rows) if r['reason']=='gate_change' or r['date_utc'][5:] in ('01-01','12-31'))
 idx.add(max(range(len(rows)),key=lambda i:float(rows[i]['trade_notional'])))
 picked[sid]=len(idx)
 for i in sorted(idx):
  r=rows[i];ts=[z for z in t if z['scenario_id']==sid and z['date_utc']==r['date_utc']];fee=float(r['cost_side'])
  for phase,ckbefore,ckafter in [('open','venue_cash_before_open','venue_cash_after_open'),('terminal_close','venue_cash_after_open','venue_cash_end')]:
   ev=[z for z in ts if z['event_phase']==phase]
   if phase=='terminal_close' and i!=1003:continue
   e=abs(float(r[ckafter])-(float(r[ckbefore])-sum(float(z['signed_notional'])+float(z['fee']) for z in ev)));maxerr=max(maxerr,e);assert e<1e-7
   for z in ev:
    assert abs(float(z['fee'])-abs(float(z['qty_delta'])*float(z['reference_price']))*fee)<1e-7
  if i:assert abs(float(r['venue_cash_before_open'])-float(rows[i-1]['venue_cash_end']))<1e-7
  if int(r['gate'])==0:assert all(abs(float(r['qty_'+s+'_after']))<1e-12 for s in ['BTC','ETH','SOL'])
 assert rows[0]['reason']=='initial' and sum(r['reason']=='initial' for r in rows)==1
 assert all(float(rows[-1]['qty_'+s+'_end'])==0 for s in ['BTC','ETH','SOL'])
 assert float(rows[-1]['terminal_fees'])>0
 obs=[max(float(r[k]) for k in ['venue_pretrade_open','venue_posttrade_open','venue_close_before_terminal'])>2500+1e-7 for r in rows]
 upper=[float(r['venue_high_upper_bound'])>2500+1e-7 for r in rows]
 capital[sid]={'observed_reference_breach_days':sum(obs),'upper_only_days':sum(u and not b for u,b in zip(upper,obs)),'max_upper':max(float(r['venue_high_upper_bound']) for r in rows)}
after={str(p):sha(p) for p in inputs};dump(O/'source-sha-after.json',after);assert before==after
m=json.loads((W/names[1]/'output/metrics.json').read_text());assert all(x['cagr']<.03 for x in m)
tests={'pass':True,'classification':'conditional_simulation','source_hashes_unchanged':True,'exact_replay_files':compare,'own_targeted_day_checks':picked,'own_cash_max_residual':maxerr,'full_audit_reused_not_rerun':{'pass':audit['pass'],'checks':audit['checks'],'source_sha256':sha(R/'04-independent-cash-audit/output/audit-results.json')},'capital':capital,'all_four_below_3pct_and_8pct_cagr':True,'new_mechanisms':0}
dump(O/'tests.json',tests);dump(O/'metrics-summary.json',m)
print(json.dumps({'pass':True,'byte_identical_outputs':len(compare),'targeted_days':picked,'cash_residual':maxerr,'capital':capital},indent=2))
