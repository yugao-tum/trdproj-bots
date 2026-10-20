"""Local-only immutable input audit. No network and no source mutation."""
from pathlib import Path
import hashlib,json
import numpy as np
import pandas as pd
OUT=Path(__file__).resolve().parent
SOURCE=Path('retained-inputs/trdproj-research-20261019/workers/data-probe/data/history')
SCRIPT=Path('retained-inputs/competition-retrospective-20261020/quant-reproduce-readonly.py')
EXPECTED='a008fbd0514f4d01bd477fc008de9fb24b8dfae5e83ebda2ced8bbf2e89bcf0a'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def save(name,obj): (OUT/name).write_text(json.dumps(obj,indent=2,ensure_ascii=False)+'\n')
assert sha(SOURCE/'spot_daily.csv')==EXPECTED
raw=pd.read_csv(SOURCE/'spot_daily.csv',dtype={'open_time_raw':'int64','close_time_raw':'int64'})
m=json.loads((SOURCE/'manifest.json').read_text())
spot_archives=[a for a in m['archives'] if a['asset']=='spot']
assert len(spot_archives)==135
for a in spot_archives:
 archive=SOURCE.parents[1]/a['archive_local']
 assert a['status']=='ok' and a['checksum']['match'] and a['checksum']['filename_match']
 assert sha(archive)==a['archive_sha256']==a['checksum']['expected_sha256']
 assert a['gap_count']==0 and a['duplicate_count']==0 and a['row_count_matches_month']
raw['date']=pd.to_datetime(raw.open_time_utc,utc=True)
assert set(raw.symbol)=={'BTCUSDT','ETHUSDT','SOLUSDT'}
assert not raw.duplicated(['symbol','date']).any()
idx=pd.date_range(raw.date.min(),raw.date.max(),freq='D',tz='UTC')
report={}; panel=pd.DataFrame(index=idx); panel.index.name='date_utc'
for sym in ['BTC','ETH','SOL']:
 d=raw[raw.symbol==sym+'USDT'].set_index('date').sort_index()
 missing=idx.difference(d.index)
 close_time=pd.to_datetime(d.close_time_utc,utc=True)
 unit=np.where(d.open_time_raw.to_numpy()>10**14,1000,1)
 norm_open=pd.to_datetime(d.open_time_raw.to_numpy()//unit,unit='ms',utc=True)
 # Close is 1ms below day end pre-2025; 1us below day end since 2025.
 norm_close_us=np.where(unit==1000,d.close_time_raw.to_numpy(),d.close_time_raw.to_numpy()*1000)
 norm_close=pd.to_datetime(norm_close_us,unit='us',utc=True)
 assert np.all(norm_open==d.index) and np.all(norm_close==close_time)
 assert np.all(d.index==d.index.normalize())
 assert np.all(close_time>d.index) and np.all(close_time<d.index+pd.Timedelta(days=1))
 prices=d[['open','high','low','close']].astype(float)
 bad=(~np.isfinite(prices).all(axis=1))|(prices<=0).any(axis=1)|(prices.high<prices[['open','close','low']].max(axis=1))|(prices.low>prices[['open','close','high']].min(axis=1))
 assert not len(missing) and not bad.any()
 for field in ['close','high','low']: panel[sym+'_'+field]=d[field]
 report[sym]={'rows':len(d),'first':d.index.min().isoformat(),'last':d.index.max().isoformat(),'missing_dates':[x.isoformat() for x in missing],'duplicate_rows':0,'invalid_ohlc_rows':int(bad.sum()),'utc_raw_timestamp_consistent':True}
assert not panel.isna().any().any()
panel.to_csv(OUT/'panel_utc.csv',date_format='%Y-%m-%dT%H:%M:%SZ',float_format='%.8f')
folds=[]
original=[('2022-12-31','2023-12-30'),('2023-12-31','2024-12-29'),('2024-12-30','2025-12-29'),('2025-12-30','2026-10-13')]
for i,(a,b) in enumerate(original,1):
 a,b=pd.Timestamp(a,tz='UTC'),pd.Timestamp(b,tz='UTC');warm=a-pd.Timedelta(days=250);end=min(b,idx.max());valid=warm>=idx.min()
 folds.append({'fold_id':i,'original_test_start':str(a.date()),'original_test_end':str(b.date()),'warmup_start':str(warm.date()),'warmup_days_required':250,'warmup_days_available':len(idx[(idx>=warm)&(idx<a)]),'test_start':str(a.date()) if valid else None,'test_end':str(end.date()) if valid else None,'test_days_available':len(idx[(idx>=a)&(idx<=end)]),'original_test_days':(b-a).days+1,'include_comparable':valid,'coverage':'full_original_fold' if valid and end==b else ('truncated_original_fold' if valid else 'exclude_missing_original_warmup_and_first_test_day'),'missing_requested_dates':len(pd.date_range(warm,b,freq='D').difference(idx))})
save('folds.json',{'schema_version':1,'warmup_calendar_days':250,'first_date_with_250_prior_bars':str((idx.min()+pd.Timedelta(days=250)).date()),'folds':folds,'rules':['Do not run excluded fold 1 or relabel later start as original fold 1.','Recompute each fold from its exact warmup_start; five-day freeze phase anchors to that date.','Fold 4 ends at 2026-09-30, not original 2026-10-13.','No four-fold compound or original-return replication claim.','All UTC date strings describe bar OPEN labels; close/high/low become known only at bar end.','Source strategy source is inspected only, never imported or executed.']})
save('quality.json',{'source_sha256':EXPECTED,'panel_rows':len(panel),'per_symbol':report,'local_spot_archive_hashes_verified':len(spot_archives),'gaps_in_common_panel':0,'imputation':False,'raw_prices_changed':False,'source_manifest_complete_spot':m['completeness']['spot']})
save('input-manifest.json',{'schema_version':1,'inputs':[{'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size} for p in [SOURCE/'spot_daily.csv',SOURCE/'manifest.json',SCRIPT]],'panel':{'path':str(OUT/'panel_utc.csv'),'sha256':sha(OUT/'panel_utc.csv'),'rows':len(panel),'columns':['date_utc']+list(panel.columns),'publish':False,'timezone':'UTC','timestamp_semantics':'UTC bar open date; daily high, low and close unavailable until that bar ends. No same-bar lookahead permitted.'}})
print(json.dumps({'panel_sha256':sha(OUT/'panel_utc.csv'),'rows':len(panel),'folds':folds},indent=2))
