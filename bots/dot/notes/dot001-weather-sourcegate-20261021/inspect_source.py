import pyarrow.parquet as pq, collections, json, hashlib, pathlib, datetime, decimal
p=pathlib.Path(__file__).parent
f=p/'history-01a77489-79e6-55b6-95f0-a47778dd0bcf-compact.parquet'
rows=pq.ParquetFile(f).read().to_pylist()
iso=lambda t:datetime.datetime.fromtimestamp(t/1000,datetime.timezone.utc).isoformat()
T=int(datetime.datetime(2026,7,15,18,tzinfo=datetime.timezone.utc).timestamp()*1000)
def ident(i):
 x=rows[i];return {'row_index':i,'event_type':x['event_type'],'t':x['t'],'utc_assuming_epoch_ms':iso(x['t']),'is_reseed':x['is_reseed'],'offset_from_T_ms':x['t']-T}
pre=[i for i,x in enumerate(rows) if x['t']<=T and x['event_type']=='snapshot']
post=[i for i,x in enumerate(rows) if x['t']>T and x['event_type'] in ['snapshot','trade']]
pre_i=max(pre,key=lambda i:(rows[i]['t'],i));post_i=min(post,key=lambda i:(rows[i]['t'],i))
last=rows[pre_i]; lev={s:json.loads(last[s]) for s in ['bids','asks']}
shape={s:{'level_count':len(lev[s]),'all_fields_present':all({'price','size'}<=set(x) for x in lev[s]),'all_sizes_positive':all(decimal.Decimal(x['size'])>0 for x in lev[s])} for s in lev}
sorted_t=sorted(set(x['t'] for x in rows)); gaps=sorted([(b-a,a,b) for a,b in zip(sorted_t,sorted_t[1:])],reverse=True)
reseed_t=sorted(x['t'] for x in rows if x['is_reseed'])
result={'schema':str(pq.ParquetFile(f).schema_arrow),'rows':len(rows),'types':dict(collections.Counter(x['event_type'] for x in rows)),'is_reseed':dict(collections.Counter(str(x['is_reseed']) for x in rows)),'min_time':iso(min(sorted_t)),'max_time':iso(max(sorted_t)),'time_unit':'epoch milliseconds inferred by agreement with CSV; not source-documented exchange or receive semantics','decision_utc':iso(T),'latest_stored_snapshot_at_or_before_T':ident(pre_i),'first_stored_snapshot_or_trade_after_T':ident(post_i),'snapshot_before_T_structure':shape,'rows_time_decreases':sum(b['t']<a['t'] for a,b in zip(rows,rows[1:])),'repeated_timestamp_rows':len(rows)-len(sorted_t),'max_gap_ms':gaps[0][0],'max_gap_from':iso(gaps[0][1]),'max_gap_to':iso(gaps[0][2]),'nearest_reseed_before_T':iso(max(t for t in reseed_t if t<=T)),'nearest_reseed_after_T':iso(min(t for t in reseed_t if t>T)),'missing_schema_fields':['market_id','condition_id','token_id','exchange_time','receive_time','sequence_number','connection_id','rules','fee_schedule'],'depth_reconstruction':'NOT RUN: token semantics and delta ordering/continuity unverified; structural snapshot is not validated executable book'}
(p/'FILE-INSPECTION.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
