"""Local-only sidecar: original observed daily opens; no frozen-panel changes."""
from pathlib import Path
import hashlib,json
import pandas as pd
P=Path(__file__).resolve().parent
S=Path('retained-inputs/trdproj-research-20261019/workers/data-probe/data/history/spot_daily.csv')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(S)=='a008fbd0514f4d01bd477fc008de9fb24b8dfae5e83ebda2ced8bbf2e89bcf0a'
assert sha(P/'panel_utc.csv')=='a3b601644697f778990fcfdcc2ff1143140d5373c33d871ff81536d493891f79'
d=pd.read_csv(S);d['date_utc']=pd.to_datetime(d.open_time_utc,utc=True)
w=d.pivot(index='date_utc',columns='symbol',values='open').rename(columns={s+'USDT':s+'_open' for s in ['BTC','ETH','SOL']})[['BTC_open','ETH_open','SOL_open']]
assert len(w)==1369 and not w.isna().any().any() and (w>0).all().all()
w.to_csv(P/'open_extension_utc.csv',date_format='%Y-%m-%dT%H:%M:%SZ',float_format='%.8f')
(P/'open-extension-manifest.json').write_text(json.dumps({'source_path':str(S),'source_sha256':sha(S),'source_field':'open','path':str(P/'open_extension_utc.csv'),'sha256':sha(P/'open_extension_utc.csv'),'rows':1369,'columns':['date_utc','BTC_open','ETH_open','SOL_open'],'publish':False,'frozen_close_panel_unchanged':True,'availability':'UTC date_utc is the daily bar open boundary. open records the first trade price within that UTC day, observed when that trade happens; exact first-trade time is not provided in daily klines. It is not known from the previous close and is not a guarantee of executable fill at the boundary.','execution_limit':'Supports a conditional next-open price-reference simulation only. Does not establish bid/ask spread, market impact, simultaneous executable multiasset fills, liquidity, or latency. Keep current frozen close-based A/B results unchanged.'},indent=2)+'\n')
print(sha(P/'open_extension_utc.csv'))
