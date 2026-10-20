"""Frozen r19 conditional ledger; Decimal arithmetic, no network, no order execution."""
from decimal import Decimal, ROUND_CEILING
from datetime import datetime
import json, pathlib, hashlib, argparse
D=lambda x: Decimal(str(x))
def ts(x): return datetime.fromisoformat(x.replace('Z','+00:00'))
def fee(q,p,c): return (D(q)*p*c*(1-p)).quantize(D('.01'),rounding=ROUND_CEILING)
def choose(prob,yes,volume,cash,adverse='.05',coef='.07'):
    prob,yes,cash,adverse,coef=map(D,(prob,yes,cash,adverse,coef))
    assert 0<=prob<=1 and 0<=yes<=1 and cash>=0
    # Side ranking by specified unrounded per-contract expected net value; YES breaks exact ties.
    choices=[]
    for side,pwin,observed in [('yes',prob,yes),('no',1-prob,1-yes)]:
        p=observed+adverse
        if p>D('.99'): continue
        expected=pwin-p-coef*p*(1-p)
        choices.append((expected,side,pwin,p))
    if not choices: return {'status':'no_trade','reason':'execution_price_above_0.99'}
    expected,side,pwin,p=max(choices,key=lambda x:(x[0],x[1]=='yes'))
    if expected<D('.05'): return {'status':'no_trade','reason':'edge_below_0.05'}
    cap=min(50,int(D(volume)*D('.01')))
    for q in range(cap,0,-1):
        f=fee(q,p,coef); cost=D(q)*p+f
        if cost<=cash:
            # Conservative size policy: take maximum affordable capacity quantity.
            # If ceil fee makes that size fail, skip; do NOT search smaller sizes for a passing edge.
            # This is not globally optimal order sizing.
            if pwin-p-f/D(q)<D('.05'):
                return {'status':'no_trade','reason':'rounded_fee_edge_below_0.05'}
            return {'status':'conditional_trade','side':side,'quantity':q,'execution_price':p,'fee':f,'cost':cost,'expected_edge':pwin-p-f/D(q)}
    return {'status':'no_trade','reason':'zero_capacity_or_insufficient_cash'}
def simulate(rows,adverse='.05',coef='.07'):
    cash=D(2500); locked=[]; maximum=D(0); fees=D(0); records=[]; cash_events=[]
    def release(until):
        nonlocal cash,locked
        keep=[]
        for item in sorted(locked,key=lambda x:ts(x['settlement_ts'])):
            if until is None or ts(item['settlement_ts'])<=until:
                cash+=item['payout']; cash_events.append({'ts':item['settlement_ts'],'kind':'settlement','ticker':item['ticker'],'amount':item['payout'],'cash_after':cash})
            else: keep.append(item)
        locked=keep
    for r in sorted(rows,key=lambda x:ts(x.get('anchor_ts') or x['decision_ts'])):
        when=ts(r.get('anchor_ts') or r['decision_ts']); release(when)
        out={k:r.get(k) for k in ('ticker','target_date','decision_ts','anchor_ts','split')}; out['cash_before']=cash
        reasons=list(r.get('exclusion_reasons',[]))
        if reasons: trade={'status':'no_trade','reason':';'.join(reasons)}
        elif r.get('prob') is None: trade={'status':'no_trade','reason':'model_unavailable'}
        elif not r.get('tape_complete'): trade={'status':'no_trade','reason':'missing_or_incomplete_tape'}
        elif r.get('yes_price') is None: trade={'status':'no_trade','reason':'no_nonblock_trade_in_window'}
        elif r.get('result') not in ('yes','no') or not r.get('settlement_ts'): trade={'status':'no_trade','reason':'settlement_unavailable'}
        elif ts(r['settlement_ts'])<=when: trade={'status':'no_trade','reason':'settlement_not_after_conditional_entry'}
        else: trade=choose(r['prob'],r['yes_price'],r['window_volume'],cash,adverse,coef)
        if trade['status']=='conditional_trade':
            cash-=trade['cost']; fees+=trade['fee']; payout=D(trade['quantity']) if trade['side']==r['result'] else D(0)
            locked.append({'ticker':r['ticker'],'settlement_ts':r['settlement_ts'],'cost':trade['cost'],'payout':payout})
            trade.update(payout=payout,net_pnl=payout-trade['cost'],settlement_ts=r['settlement_ts'])
            cash_events.append({'ts':r['anchor_ts'],'kind':'conditional_entry','ticker':r['ticker'],'amount':-trade['cost'],'cash_after':cash})
        maximum=max(maximum,sum((x['cost'] for x in locked),D(0)))
        out.update(trade);out['cash_after']=cash;records.append(out)
        assert cash>=0
    release(None)
    return {'adverse_price_add':adverse,'assumed_fee_coefficient':coef,'records':records,'cash_events':cash_events,'summary':{'events':len(rows),'trades':sum(x['status']=='conditional_trade' for x in records),'fees':fees,'venue_final_cash':cash,'total_final_cash':cash+2500,'net_pnl':cash-2500,'return_on_5000':(cash-2500)/5000,'max_locked_cost':maximum,'classification':'conditional_simulation_not_actual_fills','capacity_warning':'1% full-window volume is ex-post conditional capacity, unavailable for a live decision; not guaranteed fill','historical_fee_version_verified':False}}
def dumps(x): return json.dumps(x,ensure_ascii=False,indent=2,default=lambda v:str(v) if isinstance(v,Decimal) else TypeError())+'\n'
def main():
    ap=argparse.ArgumentParser();ap.add_argument('input');ap.add_argument('--out',default='ledger-results.json');a=ap.parse_args()
    p=pathlib.Path(a.input);rows=json.loads(p.read_text())['records']; assert len(rows)==40
    result={'input_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'runs':[simulate(rows,adv,c) for adv in ('.05','.01','.03') for c in ('.07','.035','.14')]}
    pathlib.Path(a.out).write_text(dumps(result))
if __name__=='__main__':main()
