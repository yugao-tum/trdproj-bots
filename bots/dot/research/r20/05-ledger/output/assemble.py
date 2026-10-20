"""Local-only adapter. Main code does not download data or publish files."""
import csv,json,hashlib,pathlib,datetime
from ledger import run
ROOT=pathlib.Path(__file__).resolve().parents[2]
OUT=pathlib.Path(__file__).resolve().parent
PRICES=ROOT/'04-prices/output/daily_prices.csv'
FUNDING=ROOT/'01-funding/output/funding.csv'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def csv_write(p,rows):
 with p.open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def main(funding_path=FUNDING):
 prices=list(csv.DictReader(PRICES.open()));funding_path=pathlib.Path(funding_path)
 funding=list(csv.DictReader(funding_path.open()))
 # Field naming is explicit, no price/rate/timestamp inference.
 if funding and set(['symbol','fundingTime','fundingRate','markPrice'])<=set(funding[0]):
  funding=[dict(symbol=x['symbol'],funding_time_ms=x['fundingTime'],funding_rate=x['fundingRate'],mark_price=x['markPrice']) for x in funding]
 elif funding and set(['symbol','funding_time_ms','funding_rate','mark_price'])<=set(funding[0]): pass
 else: raise ValueError('Unrecognized funding schema; obtain collector interface')
 results=[];daily=[];flows=[]
 for symbol in ['BTCUSDT','ETHUSDT','SOLUSDT']:
  p=[x for x in prices if x['symbol']==symbol]; f=[x for x in funding if x['symbol']==symbol]
  if len(p)!=1004 or not f: raise ValueError('Incomplete input')
  for budget in ['1250','625']:
   for cost in ['0.003','0.006']:
    sid=f'{symbol}-b{budget}-c{cost}';r=run(p,f,budget,cost)
    results.append(dict(scenario_id=sid,symbol=symbol,**r['summary']))
    daily.extend(dict(scenario_id=sid,symbol=symbol,**x) for x in r['daily'])
    flows.extend(dict(scenario_id=sid,symbol=symbol,**x) for x in r['funding'])
 csv_write(OUT/'daily-ledger.csv',daily);csv_write(OUT/'funding-ledger.csv',flows)
 obj=dict(schema='r20.conditional-hedge-ledger.v1',created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scenario_count=len(results),classification='Conditional hypothetical complete-path accounting; not real executed or survival-certified returns',survival_warning='If margin equity becomes negative, reported endpoint cash is counterfactual, not a feasible strategy result. Absence of negativity does not certify liquidation survival.',source_prices_sha256=sha(PRICES),source_funding_sha256=sha(funding_path),source_prices=str(PRICES),source_funding=str(funding_path),daily_ledger='daily-ledger.csv',funding_ledger='funding-ledger.csv',scenarios=results)
 (OUT/'ledger-results.json').write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
 (OUT/'manifest.json').write_text(json.dumps({p.name:sha(p) for p in OUT.iterdir() if p.is_file() and p.name!='manifest.json'},indent=2)+'\n')
 print(json.dumps({'scenario_count':12,'daily_rows':len(daily),'funding_rows':len(flows),'results_sha256':sha(OUT/'ledger-results.json')},indent=2))
if __name__=='__main__':
 import sys
 main(sys.argv[1] if len(sys.argv)>1 else FUNDING)
