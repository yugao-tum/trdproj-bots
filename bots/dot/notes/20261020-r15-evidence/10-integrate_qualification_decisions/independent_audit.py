import csv,json,pathlib,hashlib,collections,datetime
B=pathlib.Path(__file__).resolve().parents[2]; O=pathlib.Path(__file__).parent
checks=0; errors=[]; sources=[]; groups=[]; samples=[]
def eq(a,b,label):
 global checks
 checks+=1
 if abs(a-b)>1e-7:errors.append([label,a,b])
def read(p):
 sources.append({'path':str(p.relative_to(B)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size})
 return list(csv.DictReader(p.open()))
def audit(rows,label):
 cumulative=0
 for r in rows:
  f=lambda k:float(r[k] or 0)
  total=sum(f(k) for k in ['venue_cash','position_value','external_cash','in_transit'])
  eq(total,f('total_equity'),label+' balance '+r['day']);eq(total-5000,f('net_pnl'),label+' net '+r['day'])
  cumulative+=f('daily_pnl');eq(cumulative,f('net_pnl'),label+' cumulative '+r['day'])
  eq(f('external_cash')+f('in_transit')-3750,f('net_withdrawn'),label+' withdrawal '+r['day'])
 last=rows[-1]
 groups.append({'label':label,'rows':len(rows),'net_pnl_recomputed':cumulative,'trade_fees':float(last['trade_fees']),'withdrawal_fees':float(last['withdrawal_fees']),'net_withdrawn':float(last['net_withdrawn']),'max_open':max(float(r['open_pre_conservative']) for r in rows),'max_high_bound':max(float(r['high_upper_venue'])+float(r['in_transit']) for r in rows),'intraday_verified':False})
 for tag,r in [('first',rows[0]),('last',last),('max_open',max(rows,key=lambda r:float(r['open_pre_conservative']))),('max_high_bound',max(rows,key=lambda r:float(r['high_upper_venue'])+float(r['in_transit'])))]:
  samples.append({'label':label,'sample':tag,'day':r['day'],'equity':float(r['total_equity']),'net_pnl':float(r['net_pnl'])})
for p in sorted((B/'01-build_capital_cash_benchmarks/output').glob('*-ledger.csv')):audit(read(p),'01 '+p.stem)
for n,file,keys in [('02','daily-accounting.csv',['strategy','cost','scenario']),('03','daily-ledger.csv',['strategy','cost','withdrawal_fee','withdrawal_delay_days'])]:
 d=next(B.glob(n+'-*'))/'output'; gg=collections.defaultdict(list)
 for r in read(d/file):gg[tuple(r[k] for k in keys)].append(r)
 for k,rr in gg.items():audit(rr,n+' '+' '.join(k))
 tr=read(d/'trades.csv')
 for r in tr:
  eq(abs(float(r['quantity_delta'])*float(r['price'])),float(r['notional']),n+' notional');eq(float(r['notional'])*float(r['cost']),float(r['fee']),n+' fee')
 samples.append({'label':n,'sample':'first_trade','row':tr[0]})
 # Holding episode PnL from actual daily cash-flow ledger; no independence assumed.
 for key,rr in gg.items():
  if key[0] not in ['C22','C23']:continue
  if n=='02':
   ep=collections.defaultdict(float)
   for r in rr:
    if r['episode']:ep[r['episode']]+=float(r['daily_pnl'])
  else:
   ep=collections.defaultdict(float)
   trips=[t for t in read(d/'roundtrips.csv') if all(t[k]==v for k,v in zip(keys,key))]
   for t in trips:ep[t['oversold_cluster']]+=float(t['pnl'])
  if ep:samples.append({'label':n+' '+' '.join(key),'sample':'max_profit_episode_or_cluster','episode':max(ep,key=ep.get),'net':max(ep.values()),'not_independence_proof':True})
d=next(B.glob('04-*'))/'output'
for p in sorted(d.glob('local_daily*.csv')):
 rr=read(p);audit(rr,'04 '+p.stem)
 active=[r for r in rr if float(r['position_value'])>0];samples.append({'label':'04 '+p.stem,'sample':'first_holding_day','day':active[0]['day']})
 rate,mode=p.stem.removeprefix('local_daily_').split('_',1);ep=[]
 for e in read(d/'episodes.csv'):
  if e['rate']==rate and e['mode']==mode:
   # Entry-day through exit-day inclusive daily cash-flow changes.
   net=sum(float(r['daily_pnl']) for r in rr if e['entry']<=r['day']<=e['exit']);ep.append((net,e['entry'],e['exit']))
 if ep:samples.append({'label':'04 '+p.stem,'sample':'max_profit_episode','net_entry_exit':max(ep)})
d=next(B.glob('09-*'))/'output'
if (d/'local_daily.csv').exists():
 gg=collections.defaultdict(list)
 for r in read(d/'local_daily.csv'):gg[tuple(r[k] for k in ['strategy','symbol','cost','withdrawal_fee','delay_opens','mode'])].append(r)
 for k,rr in gg.items():audit(rr,'09 '+' '.join(k))
# Independent reconciliation of recomputed ledger totals to every published summary row.
bylabel={g['label']:g for g in groups}
for n in ['01','02','03','04','09']:
 p=next(B.glob(n+'-*'))/'output/summary.json'
 sources.append({'path':str(p.relative_to(B)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size})
 ss=json.loads(p.read_text());ss=ss['scenarios'] if n=='04' else ss
 for r in ss:
  if n=='01':label='01 '+r['scenario']+'-ledger';net=r['net_pnl']
  elif n=='02':label='02 C22 '+str(r['cost'])+' '+r['scenario'];net=r['pnl']
  elif n=='03':label='03 '+' '.join(str(r[k]) for k in ['strategy','cost','withdrawal_fee','withdrawal_delay_days']);net=r['full']['pnl']
  elif n=='04':label='04 local_daily_'+str(r['cost_rate'])+'_'+r['mode'];net=r['net_pnl']
  else:label='09 '+' '.join(str(r[k]) for k in ['strategy','symbol','cost','withdrawal_fee','delay_opens','mode']);net=r['pnl']
  eq(bylabel[label]['net_pnl_recomputed'],net,label+' summary reconciliation')
result={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'checks':checks,'errors':errors,'groups':groups,'samples':samples,'source_files':list({s['path']:s for s in sources}.values()),'limitations':['Independent ledger arithmetic and trade-cost checks; not independent market-data reconstruction.','Daily bounds do not prove all-day venue compliance.','Cash withdrawals are transfers, not alpha.','Maximum episode figures are retrospective diagnostics, never selection parameters.']}
(O/'audit-results.json').write_text(json.dumps(result,indent=2));print(json.dumps({'checks':checks,'errors':errors[:8],'groups':len(groups)}))
