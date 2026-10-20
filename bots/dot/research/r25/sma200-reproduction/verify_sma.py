"""Independent frozen-SMA diagnostics; public code contains no market rows."""
import argparse,csv,json,hashlib,math,statistics,tempfile,subprocess,sys,shutil
from pathlib import Path
from fractions import Fraction as F
P=Path(__file__).resolve().parent

def csvread(p):return list(csv.DictReader(p.open()))
def correlation(a,b):
 ma=statistics.fmean(a);mb=statistics.fmean(b);aa=[x-ma for x in a];bb=[y-mb for y in b];return sum(x*y for x,y in zip(aa,bb))/math.sqrt(sum(x*x for x in aa)*sum(y*y for y in bb))
def monthly(dates,rs):
 result={}
 for d,r in zip(dates,rs):result[d[:7]]=result.get(d[:7],F(1))*(1+r)
 return {k:v-1 for k,v in result.items()}
def returns(nav,capital=5000):
 old=F(capital);out=[]
 for x in nav:out.append(x/old-1);old=x
 return out

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--core',type=Path,required=True);ap.add_argument('--inputs',type=Path,required=True);ap.add_argument('--warmup',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();a.out.mkdir(exist_ok=True,parents=True)
 hashes=json.loads((P/'source-hashes.json').read_text());assert hashlib.sha256(a.warmup.read_bytes()).hexdigest()==hashes['spot_daily.csv'];assert hashlib.sha256(a.core.read_bytes()).hexdigest()==hashes['reproduce.py']
 with tempfile.TemporaryDirectory(prefix='independent-sma-') as temp:
  t=Path(temp);(t/'sources').mkdir();shutil.copyfile(a.core,t/'reproduce.py');shutil.copyfile(a.inputs.parent/'inputs.json',t/'inputs.json')
  for n in json.loads((t/'inputs.json').read_text()):shutil.copyfile(a.inputs/Path(n).name,t/n)
  subprocess.run([sys.executable,'-I',str(t/'reproduce.py')],cwd=t,check=True,capture_output=True)
  ledger=csvread(t/'results/daily.csv');ends=json.loads((t/'results/results.json').read_text())
 # Exact prior-close/prior200close definition; never current close in signal.
 spot={r['open_time_utc'][:10]:F(r['close']) for r in csvread(a.warmup) if r['symbol']=='BTCUSDT'}
 prices=csvread(a.inputs/'prices-main.csv')+csvread(a.inputs/'prices-extension.csv')
 for r in prices:
  if r['symbol']=='BTCUSDT':spot[r['date_utc']]=F(r['spot_close'])
 history=sorted(spot);br={};diagnostic=[];nav=F(5000)
 for i,d in enumerate(history):
  if not '2024-01-01'<=d<='2026-10-19':continue
  assert i>=200;past=history[i-200:i];sma=sum((spot[x] for x in past),F(0))/200;prev=spot[history[i-1]];signal=prev>sma;ret=(spot[d]/prev-1)*signal;nav*=1+ret;br[d]=ret
  diagnostic.append(dict(date=d,prior_close=str(prev),prior_sma200=str(sma),exposure=int(signal),daily_return=str(ret),nav5000=str(nav),pnl5000=str(nav-5000)))
 assert len(br)==1023
 bycase={}
 for r in ledger:bycase.setdefault(r['case_id'],[]).append(r)
 cases={r['case_id']:r for r in ends};output=[];partials=[];endpoints=[]
 for cid,ls in bycase.items():
  dates=[x['date'] for x in ls];mark=[F(x['nav']) for x in ls];case=cases[cid];failed=case['endpoints']['2026-10-19']['counterfactual']
  label='counterfactual_after_local_failure' if failed else 'conditional_not_survival_certified'
  for view,n,end in [('september_separate_exit',1004,'2026-09-30'),('october_same_position_continuation',1023,'2026-10-19')]:
   for capital in [5000,2500]:
    path=[x-5000+capital for x in mark[:n]];path[-1]=capital+F(case['endpoints'][end]['pnl']);rs=returns(path,capital);ds=dates[:n];bench=[br[d] for d in ds];ms=monthly(ds,rs);bm=monthly(ds,bench);full=sorted(m for m in ms if m<'2026-10');assert len(full)==33
    for freq,x,y in [('daily',rs,bench),('monthly_complete33',[ms[m] for m in full],[bm[m] for m in full])]:
     output.append(dict(scenario_id=cid,view=view,capital=capital,frequency=freq,n=len(x),pearson_btc_lagged_sma200_gross_reference=correlation(list(map(float,x)),list(map(float,y))),classification=label))
    if n==1023:partials.append(dict(scenario_id=cid,capital=capital,partial_month='2026-10',days=19,strategy_return=str(ms['2026-10']),benchmark_return=str(bm['2026-10']),classification=label))
    growth=math.prod(1+float(r) for r in bench);endpoints.append(dict(scenario_id=cid,view=view,capital=capital,strategy_pnl=str(path[-1]-capital),benchmark_pnl=capital*(growth-1),benchmark_return=growth-1,classification=label))
 def write(name,rs):
  with (a.out/name).open('w') as f:w=csv.DictWriter(f,fieldnames=list(rs[0]));w.writeheader();w.writerows(rs)
 write('correlation-summary.csv',output);write('october-partial.csv',partials);write('case-endpoints.csv',endpoints)
 # Compact benchmark endpoints only, not full underlying daily rows.
 be=[{k:r[k] for k in ['date','nav5000','pnl5000']} for r in diagnostic if r['date'] in ['2026-09-30','2026-10-19']];write('benchmark-endpoints.csv',be)
 (a.out/'checks.json').write_text(json.dumps({'correlation_rows':len(output),'cases':len(bycase),'benchmark_days':len(br),'full_months':33,'partial_october_days':19,'failed_cases':sum(r['endpoints']['2026-10-19']['counterfactual'] for r in ends),'failed_correlation_rows':sum(r['classification'].startswith('counterfactual') for r in output),'warmup_earliest_date':history[0],'benchmark_definition':'prior close greater than mean of prior200 closes; gross BTC close-to-close; no current-close signal','no_guide_threshold_or_pass':True},indent=2)+'\n')
if __name__=='__main__':main()
