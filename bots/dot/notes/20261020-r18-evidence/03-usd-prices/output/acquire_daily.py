import urllib.request,json,datetime,hashlib,pathlib,time,csv
out=pathlib.Path('retained-inputs/trdproj-research-20261019/continuation-20261020/workers/r18-proposal/03-usd-prices/output');rawdir=out.parent/'local-data';rawdir.mkdir(exist_ok=True)
start=1623715200;end=1712707200; manifest=[];summary={}
for pair in ['usdcusd','usdtusd']:
 allrows=[]
 for a,b in [(start,min(start+999*86400,end)),(min(start+999*86400,end),end)]:
  n=(b-a)//86400
  if not n:continue
  url=f'https://www.bitstamp.net/api/v2/ohlc/{pair}/?step=86400&limit={n}&start={a}'
  try:
   r=urllib.request.urlopen(url,timeout=40);raw=r.read();p=rawdir/f'{pair}-{a}.json';p.write_bytes(raw);rows=json.loads(raw)['data']['ohlc'];allrows+=rows;manifest.append(dict(url=url,file=str(p),sha256=hashlib.sha256(raw).hexdigest(),rows=len(rows),status=r.status)); print(pair,a,len(rows),flush=True)
  except Exception as e: print('ERROR',str(e),flush=True);raise
  time.sleep(.5)
 rows={int(v['timestamp']):v for v in allrows if start<=int(v['timestamp'])<end};missing=sorted(set(range(start,end,86400))-set(rows));zero=[t for t,r in rows.items() if float(r['volume'])<=0]
 p=rawdir/f'{pair}-daily.csv'
 with p.open('w') as f:
  w=csv.DictWriter(f,fieldnames=['timestamp','open','high','low','close','volume']);w.writeheader();w.writerows(rows[t] for t in sorted(rows))
 summary[pair]=dict(rows=len(rows),first=min(rows),last=max(rows),missing=missing,zero_volume=zero,csv=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
(out/'coverage-manifest.json').write_text(json.dumps(manifest,indent=2));(out/'coverage-summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))
