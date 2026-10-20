"""Offline validation of public Bitstamp USD price records; no network or trading."""
import csv,json,hashlib,pathlib,datetime,decimal,bisect
P=pathlib.Path(__file__).resolve().parent
D=decimal.Decimal
summary=json.loads((P/'coverage-summary.json').read_text()); result={}
for pair,meta in summary.items():
 p=P.parent/'local-data'/pathlib.Path(meta['csv']).name
 assert hashlib.sha256(p.read_bytes()).hexdigest()==meta['sha256']
 rows=list(csv.DictReader(p.open()));ts=[int(r['timestamp']) for r in rows]
 assert len(rows)==1030 and ts==list(range(1623715200,1712707200,86400))
 for r in rows:
  assert D(r['volume'])>0 and D(r['low'])>0
  assert D(r['low'])<=D(r['close'])<=D(r['high'])
  assert D(r['low'])<=D(r['open'])<=D(r['high'])
 def asof(t):
  i=bisect.bisect_right([x+86400 for x in ts],t)-1
  if i<0: return None
  assert t-(ts[i]+86400)<86400
  return rows[i]
 assert asof(1623801599) is None
 assert asof(1623801600)['timestamp']=='1623715200'
 assert asof(1712712815)['timestamp']=='1712620800'
 result[pair]={'validated_rows':len(rows),'first_asof_close':asof(1623801600)['close'],'last_asof_close':asof(1712712815)['close'],'missing':0,'zero_volume':0}
print(json.dumps(result,indent=2))
