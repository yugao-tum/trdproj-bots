#!/usr/bin/env python3
"""Independent valuation/checker; never imports ledger valuation or capital routines."""
import csv,json,hashlib
from datetime import date,timedelta
from pathlib import Path
from collections import defaultdict
ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
R16=ROOT.parent/'r16-proposal/01-freeze-inputs/output'
COINS=('BTC','ETH','SOL'); TOL=1e-7; CAP=2500.
def rows(p):
 with open(p,newline='') as f:return list(csv.DictReader(f))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def classify(observed,upper):
 return 'observed_breach' if observed>CAP+TOL else 'upper_bound_only' if upper>CAP+TOL else 'upper_bound_safe'
def synthetic():
 cases=[('observed_open_breach',2501,2600,'observed_breach'),('asynchronous_highs_not_proof',2400,2600,'upper_bound_only'),('upper_safe',2400,2499,'upper_bound_safe'),('inclusive_limit',2500,2500,'upper_bound_safe'),('idle_cash_counts',2000+501,2501,'observed_breach'),('reserve_not_offset',2600,2700,'observed_breach')]
 for name,obs,upper,want in cases:assert classify(obs,upper)==want,name
 (OUT/'synthetic-tests.json').write_text(json.dumps({'passed':len(cases),'cases':[{'name':x[0],'status':x[3]} for x in cases]},indent=2)+'\n')
def run():
 synthetic()
 a=ROOT/'02-next-open-ledger/output/accounts.csv';t=ROOT/'02-next-open-ledger/output/trades.csv'
 if not a.exists() or not t.exists(): print('Pending native02 actual accounts/trades; synthetic tests passed');return
 p=R16/'panel_utc.csv'; o=R16/'open_extension_utc.csv'
 assert sha(p)=='a3b601644697f778990fcfdcc2ff1143140d5373c33d871ff81536d493891f79'
 assert sha(o)=='ad044b15871eea467cb8750efbb3855f22fd65addce3b2424f67a57fe772183a'
 prices={r['date_utc'][:10]:r for r in rows(p)}
 for r in rows(o):prices[r['date_utc'][:10]].update(r)
 accounts=defaultdict(list);trades=defaultdict(list)
 for r in rows(a):accounts[r['scenario_id']].append(r)
 for r in rows(t):trades[(r['scenario_id'],r['date_utc'],r['event_phase'])].append(r)
 assert len(accounts)==4
 results=[];detail=[];seen=set()
 for sid,data in sorted(accounts.items()):
  data.sort(key=lambda r:r['date_utc']); assert len(data)==1004
  assert len(set(r['date_utc'] for r in data))==1004
  assert [r['date_utc'] for r in data]==[(date(2024,1,1)+timedelta(days=i)).isoformat() for i in range(1004)]
  init=float(data[0]['initial_venue']);reserve=float(data[0]['reserve']);fee=float(data[0]['cost_side'])
  assert (init,reserve) in ((2500.,2500.),(1250.,3750.)) and fee in (.003,.006)
  seen.add((init,reserve,fee)); prevcash=init;prevq={s:0. for s in COINS}; residuals=[];first={};counts=defaultdict(int);maxima={};mincash=init;minqty=0.
  for r in data:
   d=r['date_utc'];px=prices[d];before=float(r['venue_cash_before_open']);after=float(r['venue_cash_after_open'])
   assert float(r['reserve'])==reserve and float(r['initial_venue'])==init and float(r['cost_side'])==fee
   qb={s:float(r['qty_'+s+'_before']) for s in COINS};qa={s:float(r['qty_'+s+'_after']) for s in COINS}
   residuals.append(abs(before-prevcash))
   residuals.extend(abs(qb[s]-prevq[s]) for s in COINS)
   mincash=min(mincash,before,after);minqty=min(minqty,*qb.values(),*qa.values())
   vals={'pretrade_open':before+sum(qb[s]*float(px[s+'_open']) for s in COINS),'posttrade_open':after+sum(qa[s]*float(px[s+'_open']) for s in COINS),'close':after+sum(qa[s]*float(px[s+'_close']) for s in COINS),'high_upper':after+sum(qa[s]*float(px[s+'_high']) for s in COINS),'low_lower':after+sum(qa[s]*float(px[s+'_low']) for s in COINS)}
   for s in COINS:assert float(px[s+'_low'])<=float(px[s+'_open'])<=float(px[s+'_high']) and float(px[s+'_low'])<=float(px[s+'_close'])<=float(px[s+'_high'])
   for key,v in vals.items():
    if key not in maxima or v>maxima[key]['amount']:maxima[key]={'amount':v,'date_utc':d}
   obs=max(vals[x] for x in ('pretrade_open','posttrade_open','close'));up=max(obs,vals['high_upper']);status=classify(obs,up)
   counts[status]+=1;first.setdefault(status,d)
   op=trades[(sid,d,'open')];te=trades[(sid,d,'terminal_close')]
   # Sum notionals/fees only, not repeated event cash fields.
   residuals.append(abs(after-(before-sum(float(x['signed_notional'])+float(x['fee']) for x in op))))
   for s in COINS:residuals.append(abs(qa[s]-qb[s]-sum(float(x['qty_delta']) for x in op if x['symbol']==s)))
   for x in op+te:
    assert x['symbol'] in COINS
    ref=float(px[x['symbol']+('_open' if x['event_phase']=='open' else '_close')])
    residuals.extend([abs(float(x['reference_price'])-ref),abs(float(x['signed_notional'])-float(x['qty_delta'])*ref),abs(float(x['fee'])-abs(float(x['signed_notional']))*fee)])
   if d!='2026-09-30':assert not te
   endcash=float(r['venue_cash_end']);endq={s:float(r['qty_'+s+'_end']) for s in COINS}
   residuals.append(abs(endcash-(after-sum(float(x['signed_notional'])+float(x['fee']) for x in te))))
   for s in COINS:residuals.append(abs(endq[s]-qa[s]-sum(float(x['qty_delta']) for x in te if x['symbol']==s)))
   if d=='2026-09-30':assert max(abs(x) for x in endq.values())<TOL
   residuals.append(abs(float(r['total_equity_end'])-reserve-endcash-sum(endq[s]*float(px[s+'_close']) for s in COINS)))
   mincash=min(mincash,endcash);minqty=min(minqty,*endq.values());prevcash=endcash;prevq=endq
   detail.append({'scenario_id':sid,'date_utc':d,**vals,'status':status})
  assert mincash>=-TOL and minqty>=-TOL and max(residuals)<TOL,(sid,mincash,minqty,max(residuals))
  overall='observed_breach' if counts['observed_breach'] else 'upper_bound_only' if counts['upper_bound_only'] else 'upper_bound_safe'
  results.append({'scenario_id':sid,'initial_venue':init,'reserve':reserve,'cost_side':fee,'days':len(data),'overall_status':overall,'daily_counts':dict(counts),'first_dates':first,'maxima':maxima,'minimum_venue_cash':mincash,'minimum_quantity':minqty,'maximum_identity_residual':max(residuals),'fixed_reserve':True,'no_reset_or_external_transfer':True,'terminal_inventory_zero':True,'in_transit_assumed_zero':True})
 assert len(seen)==4
 with open(OUT/'daily-capital-local-only.csv','w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(detail[0]));w.writeheader();w.writerows(detail)
 result={'evidence_grade':'conditional_simulation','units':'USD-equivalent quote currency; initial total 5000; venue limit 2500','valuation_caveat':'open/close are sampled reference marks under simultaneous portfolio valuation assumption, not proof of executable synchronized fills; per-asset high sums are conservative nonsimultaneous bounds','scenarios':results}
 (OUT/'capital-results.json').write_text(json.dumps(result,indent=2)+'\n')
 report=['# r17 独立资本边界核验','', '等级：conditional_simulation（真实历史价格，非实盘、非规则已认证）。资本为美元等值报价单位，总额5000，场内上限2500。','', '高价逐币相加是不同步的保守上界，不能把 upper_bound_only 判成已证实同时超限。open/close 超限仅是在统一参考估值条件下的直接观察，并不证明三币真实同步成交。','']
 for x in results:report.append(f"- {x['scenario_id']}: {x['overall_status']}; days={x['daily_counts']}; first={x['first_dates']}; max close={x['maxima']['close']['amount']:.8f}; max high-upper={x['maxima']['high_upper']['amount']:.8f}; residual={x['maximum_identity_residual']:.3g}.")
 report+=['','独立从库存与原始 open/high/low/close 重算，不使用02资本字段作结论。逐日连接前后库存/现金，按每笔名义额与费用复算现金；确认固定储备、无外部注资/提款/重置、无负现金/负库存、终端库存归零。在途零是无划转账本假设，非外部账户实证。buffer1250仅是一种事前固定配置，不保证任意未来路径不超2500；不择优、不改额度。','', '复现：python check_capital.py。daily-capital-local-only.csv 仅本地，不上传。']
 (OUT/'RESULT.md').write_text('\n'.join(report)+'\n')
 files=['capital-results.json','synthetic-tests.json','RESULT.md','daily-capital-local-only.csv']
 (OUT/'manifest.json').write_text(json.dumps({'agent_model':'unknown','task':'r17-native03','inputs':{str(x):sha(x) for x in (a,t,p,o)},'code_sha256':sha(__file__),'outputs':{x:sha(OUT/x) for x in files},'local_only':['daily-capital-local-only.csv']},indent=2)+'\n')
 print(json.dumps(results,indent=2))
if __name__=='__main__':run()
