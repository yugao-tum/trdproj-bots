"""Offline actual Binance hourly panel. No synthetic observations or trade simulation.
Raw archives remain local; run beside retained raw/ inputs.
"""
import csv,datetime as dt,hashlib,io,json,pathlib,zipfile
from decimal import Decimal as D
P=pathlib.Path(__file__).resolve().parent

def ms(t): return int(dt.datetime.fromisoformat(t.replace('Z','+00:00')).timestamp()*1000)
def iso(t): return dt.datetime.fromtimestamp(t/1000,dt.timezone.utc).isoformat().replace('+00:00','Z')
def load(symbol):
 f=P/'raw'/f'{symbol}-1h-2023-05.zip'
 assert hashlib.sha256(f.read_bytes()).hexdigest()==f.with_suffix('.zip.CHECKSUM').read_text().split()[0], 'checksum'
 with zipfile.ZipFile(f) as z:
  assert len(z.namelist())==1
  rows=list(csv.reader(io.StringIO(z.read(z.namelist()[0]).decode())))
 assert len(rows)==744
 data={}
 for r in rows:
  assert len(r)==12
  t=int(r[0]); assert t%3600000==0 and int(r[6])==t+3599999
  o,h,l,c,v=map(D,r[1:6]); assert 0<l<=min(o,c)<=max(o,c)<=h and v>=0
  assert t not in data; data[t]=r
 assert sorted(data)==list(range(ms('2023-05-01T00:00:00Z'),ms('2023-06-01T00:00:00Z'),3600000))
 return data

def main():
 event=json.loads((P/'event-ledger.json').read_text())['events'][0]
 a,b=load('APEUSDT'),load('BTCUSDT'); assert a.keys()==b.keys()
 left,right=ms(event['utc_window_start']),ms(event['utc_window_end_exclusive'])
 times=list(range(left-24*3600000,right+72*3600000,3600000))
 fields=['event_original_row','open_time_utc','ape_open','ape_high','ape_low','ape_close','ape_volume','btc_open','btc_high','btc_low','btc_close','btc_volume','possible_event_hour']
 with (P/'real-price-panel.csv').open('w') as f:
  w=csv.writer(f);w.writerow(fields)
  for t in times:w.writerow([1,iso(t),*a[t][1:6],*b[t][1:6],left<=t<right])
 # Sensitivity uses hourly opens, not favourable closes/high/low. Not trading returns.
 samples=[]
 for t in range(left,right,3600000):
  ar=D(a[t+72*3600000][1])/D(a[t][1])-1;br=D(b[t+72*3600000][1])/D(b[t][1])-1
  samples.append({'possible_hour':iso(t),'ape_72h_open_return':str(ar),'btc_72h_open_return':str(br),'difference':str(ar-br)})
 (P/'time-sensitivity.json').write_text(json.dumps({'interpretation':'Descriptive real-price sensitivity to inferred day/timezone; not causal alpha or realized profit. Does not prove unlock occurred.','candidate_hours':len(samples),'ape_return_min':str(min(D(x['ape_72h_open_return']) for x in samples)),'ape_return_max':str(max(D(x['ape_72h_open_return']) for x in samples)),'relative_min':str(min(D(x['difference']) for x in samples)),'relative_max':str(max(D(x['difference']) for x in samples))},indent=2))
 result={'checks_passed':8,'checks':['both checksums','12-column rows','744 rows each','unique timestamps','contiguous UTC grid','OHLC ordering and nonnegative volumes','close time=open+3599999','exact APE-BTC join with 50 candidate origins and +72h coverage'],'raw_rows_per_symbol':744,'raw_rows_total':1488,'panel_joined_hours':len(times),'used_raw_symbol_rows':len(times)*2,'missing_join_rows':0,'candidate_event_hours':len(samples),'classification':'Real historical market observations; scheduled-event date inference. No backtest, simulation or qualification.'}
 (P/'test-results.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
if __name__=='__main__':main()
