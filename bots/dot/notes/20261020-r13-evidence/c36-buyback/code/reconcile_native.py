"""Offline Decimal reconstruction. No network, wallet or external-model calls.
Run: python code/reconcile_native.py [output directory]
Raw and per-fill ledger are LOCAL ONLY; aggregate evidence is publishable.
"""
import csv, hashlib, json, sys
from collections import defaultdict
from datetime import datetime, timezone
from decimal import Decimal, getcontext
from pathlib import Path
getcontext().prec = 50
D = Decimal
START, END = 1791763200000, 1792368000000
TOL = D('0.00000001')  # one HYPE base unit, NOT an exact-reconciliation claim

def utc(ms):
    return datetime.fromtimestamp(ms / 1000, timezone.utc).isoformat(timespec='milliseconds')
def dedup(pages):
    seen = {}; duplicates = 0
    for page in pages:
        for r in page:
            key = (r['coin'], str(r['tid']))
            if key in seen:
                if seen[key] != r:
                    raise ValueError('conflicting trade identity')
                duplicates += 1
            else:
                seen[key] = r
    return sorted(seen.values(), key=lambda r:(r['time'], D(r['startPosition']), str(r['tid']))), duplicates

def summarize(rows):
    qty = cash = D(0); fees = defaultdict(Decimal); residuals=[]
    for i, r in enumerate(rows):
        if not START <= r['time'] < END: raise ValueError('outside half-open frozen interval')
        if r['coin'] != '@107' or r['side'] != 'B' or r['dir'] != 'Buy': raise ValueError('unexpected asset/direction')
        if D(r['sz']) <= 0 or D(r['px']) <= 0: raise ValueError('nonpositive fill')
        if r['feeToken'] not in ('HYPE','USDC'): raise ValueError('unsupported fee denomination')
        qty += D(r['sz']); cash += D(r['px'])*D(r['sz']); fees[r['feeToken']] += D(r['fee'])
        if i:
            prev=rows[i-1]
            predicted=D(prev['startPosition'])+D(prev['sz'])-(D(prev['fee']) if prev['feeToken']=='HYPE' else D(0))
            residuals.append(D(r['startPosition'])-predicted)
    opening=D(rows[0]['startPosition']); last=rows[-1]
    closing=D(last['startPosition'])+D(last['sz'])-(D(last['fee']) if last['feeToken']=='HYPE' else D(0))
    net=qty-fees['HYPE']; bridge=closing-opening-net
    return {'raw_quantity_HYPE':str(qty),'execution_notional_USDC':str(cash),'reported_fee_HYPE':str(fees['HYPE']),
        'reported_fee_USDC':str(fees['USDC']),'net_acquired_HYPE':str(net),'cash_debit_USDC':str(cash+fees['USDC']),
        'vwap_USDC_per_HYPE':str(cash/qty),'first_fill_utc':utc(rows[0]['time']),'last_fill_utc':utc(rows[-1]['time']),
        'trade_boundary_opening_HYPE':str(opening),'trade_boundary_closing_HYPE':str(closing),
        'inventory_delta_HYPE':str(closing-opening),'inventory_bridge_residual_HYPE':str(bridge),
        'continuity_edges':len(residuals),'exact_nonzero_residual_edges':sum(x != 0 for x in residuals),
        'max_abs_edge_residual_HYPE':str(max(map(abs,residuals),default=D(0))),
        'edges_exceeding_one_base_unit':sum(abs(x)>TOL for x in residuals),
        'inventory_bridge_within_one_base_unit':abs(bridge)<=TOL,'timestamp_groups':len(set(r['time'] for r in rows)),
        'zero_hash_rows':sum(r['hash']=='0x'+'0'*64 for r in rows)}

def write_csv(p,fields,rows):
    with p.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)

def main(out):
    raw=out/'raw'; pages=[json.loads((raw/f'fills_part_{i:02}.json').read_text()) for i in range(1,5)]
    rows,duplicates=dedup(pages); s=summarize(rows)
    meta=json.loads((raw/'spot_meta.json').read_text()); pair=next(x for x in meta['universe'] if x['name']=='@107')
    tokens={x['index']:x for x in meta['tokens']}
    assert pair['tokens']==[150,0] and tokens[150]['name']=='HYPE' and tokens[0]['name']=='USDC'
    ledger=json.loads((raw/'af_ledger_week.json').read_text())
    s.update({'task_id':'continuation-r13-02','claim':'C36','raw_rows':sum(map(len,pages)),'identical_overlap_duplicates':duplicates,'unique_used_fills':len(rows),
      'pair':{'name':'@107','base':'HYPE','base_index':150,'quote':'USDC','quote_index':0,'HYPE_weiDecimals':tokens[150]['weiDecimals']},
      'nonfunding_ledger_entries':len(ledger),'ledger_tokens':sorted(set(x['delta'].get('token','') for x in ledger)),
      'ledger_incoming_KNTQ':sum(x['delta'].get('token')=='KNTQ' and x['delta'].get('destination')=='0x'+'fe'*20 for x in ledger),
      'complete_window_coverage_proven':False,'midnight_balances_proven':False,'supply_bridge_closed':False,'strategy_backtest':False,
      'precision_note':'Input startPosition strings exhibit sub-base-unit representation residuals; Decimal preserves these instead of calling them exact zeros.',
      'native_network_requests':0,'native_external_model_calls':0})
    (out/'reconciliation-summary.json').write_text(json.dumps(s,indent=2)+'\n')
    local=[];daily={}
    for r in rows:
        q=D(r['sz']);c=q*D(r['px']);date=utc(r['time'])[:10]
        d=daily.setdefault(date,{'date_utc':date,'fills':0,'bought_HYPE':D(0),'cash_paid_USDC':D(0),'fee_HYPE':D(0),'fee_USDC':D(0)})
        d['fills']+=1;d['bought_HYPE']+=q;d['cash_paid_USDC']+=c;d['fee_'+r['feeToken']]+=D(r['fee'])
        local.append({'time_utc':utc(r['time']),'tid':r['tid'],'hash':r['hash'],'oid':r['oid'],'pair':'HYPE/USDC','quantity_HYPE':q,'price_USDC_per_HYPE':r['px'],'cash_debit_USDC':c+(D(r['fee']) if r['feeToken']=='USDC' else D(0)),'reported_fee':r['fee'],'fee_token':r['feeToken'],'start_position_HYPE':r['startPosition'],'identity_note':'API tid is primary; hash may be zero, not independent onchain proof'})
    write_csv(out/'buyback-ledger.csv',list(local[0]),local)
    write_csv(out/'buyback-daily-summary.csv',list(next(iter(daily.values()))),daily.values())
    bridge=[('executed_purchases',s['raw_quantity_HYPE'],'HYPE','observed fills; adds AF holdings, not automatically a separate supply burn'),
      ('execution_cash_paid',s['cash_debit_USDC'],'USDC','executed notional plus reported USDC fee; not profit'),
      ('reported_execution_fee',s['reported_fee_HYPE'],'HYPE','API reported fee'),
      ('trade_boundary_inventory_delta',s['inventory_delta_HYPE'],'HYPE','not exact midnight states'),
      ('inventory_rounding_residual',s['inventory_bridge_residual_HYPE'],'HYPE','preserved Decimal source residual'),
      ('economically_inaccessible_or_burned_inventory','','HYPE','official policy assertion; actual incremental burn not independently verified'),
      ('observed_destruction','','HYPE','unknown; missing explicit destruction/supply records; do not encode as zero'),
      ('circulating_supply_start','','HYPE','unknown'),('circulating_supply_end','','HYPE','unknown'),
      ('mints_and_unlocks','','HYPE','unknown; unlock affects circulating but not necessarily total supply'),
      ('redistributions','','HYPE','unknown; absent from returned token-specific ledger is not proof of absence'),
      ('protocol_fee_cash_inflows','','USDC','unknown; 162 KNTQ sends cannot establish fee revenue'),
      ('midnight_cash_start','','USDC','unknown'),('midnight_cash_end','','USDC','unknown')]
    write_csv(out/'supply-bridge.csv',['component','amount','unit','evidence_scope'],[dict(zip(['component','amount','unit','evidence_scope'],x)) for x in bridge])
    print(json.dumps(s,indent=2))

if __name__=='__main__': main(Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parents[1])
