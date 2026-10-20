"""Offline C09 row-page/identity audit. No strategy, network, or executable-price proxy."""
import argparse, csv, hashlib, json
from pathlib import Path
from collections import Counter
import pyarrow.parquet as pq
import pyarrow

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def classify(p):
    b=p.read_bytes()
    if b.startswith(b'version https://git-lfs.github.com/spec/v1'): return 'git_lfs_pointer'
    if len(b)>=12 and b[:4]==b'PAR1' and b[-4:]==b'PAR1' and int.from_bytes(b[-8:-4],'little') < len(b)-12: return 'parquet_container_requires_decode'
    return 'not_complete_parquet_container'
def main(base,out):
    names=['dinesh_labels.parquet','dinesh_quotes_20260710.parquet','pancake_nov2024_resolutions.parquet']
    tables={n:pq.read_table(base/n) for n in names}
    files=[{'file':n,'bytes':(base/n).stat().st_size,'sha256':sha(base/n),'classification':classify(base/n),'row_pages_decoded':True,'rows':t.num_rows,'fields':t.column_names,'null_counts':{c:t[c].null_count for c in t.column_names}} for n,t in tables.items()]
    l,q,r=[tables[n].to_pandas() for n in names]
    ls=set(l.slug.dropna());qs=set(q.slug.dropna()); matched=ls&qs
    cat=list(csv.DictReader((base/'catalog_coverage_rows.csv').open()))
    conditions={x['condition_id'] for x in cat}; mids={x['market_id'] for x in cat}
    ex=[json.loads(x) if isinstance(x,str) else (x or {}) for x in r.external_ids]
    sources={k:int(v) for k,v in l.source.value_counts(dropna=False).items()}
    counts={'labels_unique_slugs':len(ls),'labels_duplicate_slug_rows':int(l.slug.duplicated().sum()),'labels_conflicting_y_slug_count':int((l.groupby('slug').y.nunique()>1).sum()),'label_source_counts':sources,'quote_rows':len(q),'quote_unique_slugs':len(qs),'quote_slugs_with_label':len(matched),'quote_rows_with_label':int(q.slug.isin(ls).sum()),'quote_slugs_without_label':len(qs-ls),'quote_min_naive_time':str(q.ts.min()),'quote_max_naive_time':str(q.ts.max()),'quote_timezone':'not encoded; do not assume UTC','quote_categories':{str(k):int(v) for k,v in q.category.value_counts(dropna=False).items()},'quote_invalid_bid_ask_rows':int(((q.bid<0)|(q.ask>1)|(q.bid>q.ask)).sum()),'quote_null_bid_or_ask_rows':int((q.bid.isna()|q.ask.isna()).sum()),'resolution_rows':len(r),'resolution_unique_market_ids':int(r.market_id.nunique()),'resolution_nonnull_evidence_uri':int(r.evidence_uri.notna().sum()),'resolution_external_condition_ids':sum(bool(e.get('condition_id')) for e in ex),'resolution_catalog_condition_id_exact_matches':sum(e.get('condition_id') in conditions for e in ex),'resolution_catalog_market_id_exact_matches':int(r.market_id.isin(mids).sum()),'resolution_received_after_resolved':int((r.received_at>r.resolved_at).sum()),'resolution_label_counts':{str(k):int(v) for k,v in r.winning_outcome_label.value_counts(dropna=False).items()},'complete_trade_event_panels':0,'independently_verified_settlements':0,'new_mechanisms':0,'strategy_backtests':0,'net_pnl':None}
    (out/'aggregate.json').write_text(json.dumps({'decoder':'pyarrow '+pyarrow.__version__,'file_audit':files,'counts':counts},indent=2)+'\n')
    coverage=[['source','identifier','pre_event_rules_end_vintage','trade_timestamp_price_quantity','complementary_executable_book','settlement_label','verified_settlement_evidence'],['Dinesh quotes','slug only','absent','absent; quote timestamps and bid/ask only','absent; no token/side or depth','join labels by slug only','absent'],['Dinesh labels','slug only','absent','absent','absent','y and source flag','absent'],['Pancake resolutions','market UUID + condition ID + provider ID','absent','absent','absent','outcome label/instrument ID','all evidence_uri null' if counts['resolution_nonnull_evidence_uri']==0 else 'URI presence is not verification'],['Marketlens catalogs','market/condition IDs and event labels','close time only, not vintage','absent in catalog','absent in catalog','winning outcome / resolved_at','not independently verified']]
    with (out/'coverage.csv').open('w') as f: csv.writer(f).writerows(coverage)
    examples=[]
    for ix,row in q.sort_values(['slug','ts'],kind='stable').head(10).iterrows():
        labels=l[l.slug==row.slug]
        examples.append({'source_file':names[1],'row_index_zero_based':int(ix),'fields':{k:str(row[k]) for k in ['slug','ts','bid','ask','volume24hr']},'joined_label_values':labels[['y','source']].to_dict('records'),'classification':'quote not trade; volume24hr not trade size'})
    for ix,row in r.sort_values('resolution_id',kind='stable').head(10).iterrows():
        examples.append({'source_file':names[2],'row_index_zero_based':int(ix),'fields':{k:(None if row[k] is None else str(row[k])) for k in ['resolution_id','market_id','winning_outcome_label','resolved_at','evidence_uri','external_ids']},'classification':'vendor resolution row; unverified finality'})
    (out/'LOCAL_ONLY_20_FIELD_EXAMPLES.json').write_text(json.dumps(examples,indent=2,default=str)+'\n')
    (out/'frozen_panel.json').write_text(json.dumps({'earliest_complete_window':None,'sorted_first_30_event_ids':[],'reason':'No source combination supplies canonical event linkage, pre-event rule/end vintage, actual trade time/price/size and verified final settlement. Missing columns cannot be supplied by a slug-only join.','candidate_join_is_not_admissible_panel':True},indent=2)+'\n')
    (out/'input-manifest.json').write_text(json.dumps([{'path':str(base/n),'sha256':sha(base/n),'bytes':(base/n).stat().st_size} for n in names+['catalog_coverage_rows.csv','EVIDENCE_AUDIT.md','artifact_manifest.json']],indent=2)+'\n')
    prior=[json.loads((base/n).read_text()) for n in ['dinesh_labels_fetch.json','dinesh_quote_fetch.json','pancake_resolution_fetch.json']]
    (out/'source-manifest.json').write_text(json.dumps({'market_data_requests_this_task':0,'prior_fetches':[{k:v for k,v in x.items() if k!='headers'} for x in prior],'blocked_dependency':{'target':'gamma-api.polymarket.com','prior_state':'platform policy denial (C13), HTTP403/error1010 (C38)','action_this_task':'not requested; no alternative route','retry_time':'not established; do not retry automatically'},'new_software_dependency':'pyarrow from configured pip registry; no market API requested'},indent=2)+'\n')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--base',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();main(a.base,a.out)
