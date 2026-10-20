import csv,json,hashlib,datetime,zipfile,io,pathlib,urllib.request,urllib.error,time,sys
P=pathlib.Path(__file__).parent
B=P.parents[3]
OLD=B/'workers/r13-proposal/10-acquire_c19_hedge_basis_inputs/output'
F=B.parent/'workers/data-probe/data/history/funding.csv'
H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
now=lambda:datetime.datetime.now(datetime.timezone.utc).isoformat()
routes={'spot':'spot/monthly/klines','perp':'futures/um/monthly/klines','mark':'futures/um/monthly/markPriceKlines'}
def url(k,m):return f'https://data.binance.vision/data/{routes[k]}/BTCUSDT/1h/BTCUSDT-1h-{m}.zip'
def dump(n,x):(P/n).write_text(json.dumps(x,indent=2)+'\n')
if '--fetch' in sys.argv:
 assert not (P/'PRE-REGISTRATION.json').exists()
 dump('PRE-REGISTRATION.json',dict(utc=now(),task='r15-native05',role='cash data availability only',symbol='BTCUSDT',month='2024-02',reason='earliest month absent from retained January archives',interval='1h',new_requests_max=6,stop='first failure; no retry, page loop, alternate endpoint or expansion',historical_test='retrospective data schema test, no PnL computation',costs={'base_per_side':0.003,'stress_per_side':0.006,'historical_actual':'unknown'},capital={'total':5000,'venue_cap':2500,'full_collateral':'not established'},dedup='C19 / known A-A1-funding-carry; no new mechanism'))
 (P/'PRE-REGISTRATION.sha256').write_text(H(P/'PRE-REGISTRATION.json')+'  PRE-REGISTRATION.json\n')
 (P/'raw').mkdir(exist_ok=True)
 req=[]
 for k in routes:
  for suffix in ['', '.CHECKSUM']:
   u=url(k,'2024-02')+suffix;name=f'BTCUSDT-{k}-2024-02.zip'+suffix;r={'url':u,'utc':now(),'local':'raw/'+name}
   try:
    with urllib.request.urlopen(u,timeout=40) as response:
     body=response.read();r['status']=response.status
    (P/r['local']).write_bytes(body);r.update(bytes=len(body),sha256=hashlib.sha256(body).hexdigest())
   except Exception as e:
    r.update(status=getattr(e,'code',None),error=str(e),retry_after=getattr(e,'headers',{}).get('Retry-After'))
   req.append(r);dump('source-manifest.json',{'requests':req,'model':'native OpenAI; model ID not exposed','external_model_calls':0});print(r['url'],r['status'],flush=True)
   if r['status']!=200:sys.exit(1)
   time.sleep(1.1)

def audit_zip(path,kind,month):
 check=pathlib.Path(str(path)+'.CHECKSUM').read_text().split()[0]
 assert H(path)==check
 with zipfile.ZipFile(path) as z:
  names=z.namelist();assert len(names)==1
  rows=list(csv.reader(io.StringIO(z.read(names[0]).decode())))
 header=None
 if not rows[0][0].isdigit(): header=rows.pop(0)
 ts=[int(r[0]) for r in rows]
 assert all(len(r)==12 for r in rows)
 expected=744 if month=='2024-01' else 696
 assert len(ts)==expected and len(set(ts))==expected
 assert all(b-a==3600000 for a,b in zip(ts,ts[1:]))
 assert all(int(r[6])-int(r[0])==3599999 for r in rows)
 return {'kind':kind,'month':month,'rows':len(rows),'start_ms':min(ts),'last_open_ms':max(ts),'timestamp_unit':'ms','price_unit':'USDT / BTC','header':header,'sha256':H(path),'checksum_match':True,'missing_hours':0,'duplicate_hours':0,'field_count':12}
if '--audit' in sys.argv:
 results=[]
 for k in routes:
  results.append(audit_zip(OLD/'raw'/f'BTCUSDT-{k}.zip',k,'2024-01'))
  results.append(audit_zip(P/'raw'/f'BTCUSDT-{k}-2024-02.zip',k,'2024-02'))
 with F.open() as f:r=csv.DictReader(f);fields=r.fieldnames;fund=list(r)
 fs=[]
 for sym in sorted(set(r['symbol'] for r in fund)):
  rows=[r for r in fund if r['symbol']==sym];ts=[r['calc_time_utc'] for r in rows]
  fs.append({'symbol':sym,'rows':len(rows),'first':min(ts),'last':max(ts),'calendar_days':len(set(t[:10] for t in ts)),'funding_intervals_hours':sorted(set(r['funding_interval_hours'] for r in rows)),'duplicates':len(ts)-len(set(ts))})
 dump('aggregate.json',{'archive_audit':results,'funding_schema':fields,'funding_coverage':fs,'settlement_mark_present':False,'historical_fee_schedule_present':False,'historical_margin_rules_present':False,'twelve_month_triplet_verified':False,'verified_triplet_months':2,'verified_synchronized_hours':1440,'new_profit_conclusion':None,'classification':'data availability supplement; conditional accounting only','additional_2024_requests':60,'additional_2024_endpoint_requests':6,'additional_requests_note':'10 months x 3 archives x ZIP+CHECKSUM =60; January 2025 three-pack exit endpoint may add6; unrequested/unverified'})
 inputs=[F,OLD/'archive-source-manifest.json',B/'workers/r15-proposal/remote-snapshot.json']+[OLD/'raw'/f'BTCUSDT-{k}.zip' for k in routes]
 dump('input-manifest.json',[{'path':str(p),'bytes':p.stat().st_size,'sha256':H(p)} for p in inputs])
 with (P/'download-plan.csv').open('w') as f:
  w=csv.writer(f);w.writerow(['month','kind','archive_url','checksum_url','status','purpose'])
  for m in range(1,13):
   month=f'2024-{m:02}';state='verified SHA256' if m<=2 else 'planned URL, not fetched or availability verified'
   for k in routes:w.writerow([month,k,url(k,month),url(k,month)+'.CHECKSUM',state,'12 calendar months; hourly prices are not charge marks'])
 print('PASS: 6 archive checksum/schema/time-grid audits; funding schema audited; 1440 synchronized BTC hourly timestamps; no PnL rerun')
