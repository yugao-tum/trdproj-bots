import csv,json,hashlib
from pathlib import Path
from decimal import Decimal as D
B=Path(__file__).resolve().parents[2]
checks=[]; sources={}
def get(n,name):
 p=next(B.glob(n+'*'))/'output'/name
 sources[str(p.relative_to(B))]=hashlib.sha256(p.read_bytes()).hexdigest()
 return p
def js(n,name):return json.loads(get(n,name).read_text())
def rows(n,name):return list(csv.DictReader(get(n,name).open()))
def ok(label,a,b,tol=1e-7):
 assert abs(float(a)-float(b))<tol,(label,a,b)
 checks.append({'check':label,'actual':float(a),'expected':float(b),'pass':True})
def ledger(n,tag,cost,trades,daily,expected):
 cash=2500.; qty={}
 for i,t in enumerate(trades):
  q=float(t['qty']);p=float(t['price']);v=float(t['notional']);f=float(t['fee']);sgn=1 if t['side']=='BUY' else -1
  ok(f'{tag} trade{i} qtyprice',q*p,v);ok(f'{tag} trade{i} fee',v*cost,f)
  cash-=sgn*v+f;qty[t['symbol']]=qty.get(t['symbol'],0)+sgn*q
  ok(f'{tag} trade{i} cash',cash,t['cash_after']);ok(f'{tag} trade{i} holding',qty[t['symbol']],t['qty_after'])
 for i,d in enumerate(daily):
  ok(f'{tag} day{i} equity',float(d['cash'])+float(d['holdings_close'])+float(d['off_exchange_cash']),d['total_equity'])
 ok(tag+' terminal cash',cash+2500-5000,expected)
 ok(tag+' terminal daily',float(daily[-1]['total_equity'])-5000,expected)
 return {'trades':len(trades),'days':len(daily),'net_pnl':cash-2500,'fees':sum(float(t['fee']) for t in trades)}
metrics={}
r=js('03','results.json')
for c in [.003,.006]:
 for variant,tag in [('baseline','baseline'),('variant','band_5pp')]:
  expected=next(x for x in r['comparisons'] if x['cost']==c and x['period']=='full')['net_pnl_usdt'][variant]
  key=f'C24 {tag} {c}';metrics[key]=ledger('03',key,c,rows('03',f'{tag}-{c}-trades.csv'),rows('03',f'{tag}-{c}-daily.csv'),expected)
r=js('04','results.json')
for c in [.003,.006]:
 for tag in ['baseline','variant']:
  expected=next(x for x in r['comparisons'] if float(x['cost'])==c and x['period']=='full')[tag]['net_pnl_usdt']
  filt=lambda rs:[x for x in rs if float(x['cost_rate'])==c]
  key=f'C21 {tag} {c}';metrics[key]=ledger('04',key,c,filt(rows('04',f'{tag}-trades.csv')),filt(rows('04',f'{tag}-daily.csv')),expected)
r=js('05','results.json');p=D(r['entry_mark_usd']);e=D(r['terminal_indexed_eusd_usd'])
for case,c in [('zero_cost_ceiling',D(0)),('guide_cost_proxy',D('.003'))]:
 pnl=D(2500)/(1+c)/p*e*(1-c)-2500
 ok('C44 '+case,pnl,r['scenarios'][case]['conditional_pnl_before_gas_usdt'])
 ok('C44 break even '+case,p*(1+c)/(1-c),r['scenarios'][case]['breakeven_eusd_usd_before_gas'])
f=js('06','fixed-inputs.json');r=js('06','results.json');g=D(f['end_index'])/D(f['start_index']);net=g*D('.997')**2-1
ok('C25 gross',(g-1)*100,r['gross_index_pct']);ok('C25 loose total',net*50,r['net_total_pct_loose_cap'])
a=D(2500)/(g*D('.997'));ok('C25 endpoint-cap budget',a,r['endpoint_cap_initial_budget']);ok('C25 endpoint total',(D('2492.5')-a)/50,r['endpoint_cap_case']['total_capital_return_pct'])
rr=rows('01','financing-classification.csv')
for field,total in [('log_count',1295),('decoded_count',1229),('unknown_count',66),('liquidations',80)]:ok('C37 '+field,sum(int(x[field]) for x in rr),total)
ok('C37 borrowed',sum(x['classification']=='borrowed_event_linked_to_liquidator' for x in rr),3)
ok('C37 own',sum(x['own_funds_proven']=='True' for x in rr),0)
m=js('02','source-manifest.json'); raw=Path(m['inputs'][0]['path']); sources['r13-minute-response.json']=hashlib.sha256(raw.read_bytes()).hexdigest(); candles=json.loads(raw.read_text())['data']['ohlc']; ok('C26 minutes',len(candles),180); ok('C26 zero-volume',sum(D(x['volume'])==0 for x in candles),157); ok('C26 positive-volume',sum(D(x['volume'])>0 for x in candles),23)
out=Path(__file__).parent
(out/'VERIFICATION.json').write_text(json.dumps({'pass':True,'checks':len(checks),'scope':'Independent arithmetic/ledger reconstruction, not live execution or independent market-price validation','metrics':metrics,'checks_detail':checks},indent=2))
(out/'source-manifest.json').write_text(json.dumps({'local_input_sha256':sources,'access_date_utc':'2026-10-20'},indent=2))
print('PASS',len(checks),json.dumps(metrics))
