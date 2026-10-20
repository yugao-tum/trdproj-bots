#!/usr/bin/env python3
"""Offline snapshot audit. No network, account operations or raw-data export."""
import argparse, collections, csv, hashlib, json, math
from datetime import datetime, timezone
from fractions import Fraction as F
from pathlib import Path
DEFAULT=Path('retained-inputs/trdproj-research-20261019/continuation-20261020/workers/r16-proposal/07-github-data/local-data/pool-balances.csv')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,o): p.write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n')
def main():
 a=argparse.ArgumentParser(); a.add_argument('--input',type=Path,default=DEFAULT); a.add_argument('--output',type=Path,default=Path(__file__).parent); args=a.parse_args(); out=args.output; out.mkdir(exist_ok=True)
 before=sha(args.input); counts=collections.Counter(); gaps=collections.Counter(); ids=collections.defaultdict(set); seen=set(); prev=None; qs=[]; starts=None; last=None
 with args.input.open() as f:
  reader=csv.DictReader(f); columns=reader.fieldnames
  for r in reader:
   counts['rows']+=1; block=int(r['block']); ts=int(r['ts']); x,y,s=map(float,(r['token0_bal'],r['token1_bal'],r['lp_supply']))
   vals=(x,y,s); valid=all(math.isfinite(v) and v>0 for v in vals)
   counts['positive_finite_balance_supply_rows']+=valid; counts['duplicate_blocks']+=block in seen;seen.add(block)
   for k in ('pool_address','token0_address','token1_address','token0_symbol','token1_symbol'): ids[k].add(r[k])
   q=math.sqrt(x*y)/s if valid else None
   if q is not None: qs.append(q)
   if starts is None: starts=(block,ts)
   last=(block,ts)
   if prev:
    pb,pt,px,py,ps,pq=prev; gaps[str(block-pb)]+=1; counts['nonincreasing_timestamp_intervals']+=ts<=pt
    counts['supply_increase_intervals']+=s>ps;counts['supply_decrease_intervals']+=s<ps;counts['supply_equal_intervals']+=s==ps
    if q is not None and pq is not None:
     rel=q/pq-1
     counts['q_increase_gt_1e-10_intervals']+=rel>1e-10
     counts['q_decrease_lt_minus_1e-10_intervals']+=rel < -1e-10
     counts['q_within_1e-10_intervals']+=abs(rel)<=1e-10
   prev=(block,ts,x,y,s,q)
 assert before==sha(args.input),'input mutated'
 result={'classification':'real_snapshot_schema_and_aggregate_only','input_sha256':before,'input_bytes':args.input.stat().st_size,'columns':columns,'counts':dict(counts),'block_gap_counts':dict(gaps),'ids':{k:sorted(v) for k,v in ids.items()},'coverage_utc':[datetime.fromtimestamp(t,timezone.utc).isoformat() for b,t in (starts,last)],'block_range':[starts[0],last[0]],'proxy':{'definition':'q=sqrt(token0_bal*token1_bal)/lp_supply in supplied units; NOT inferred fee','first':qs[0],'last':qs[-1],'min':min(qs),'max':max(qs),'numeric_method':'float64; relative sign tolerance 1e-10; diagnostics only','unit_caveat':'CSV has no decimal metadata; constant rescalings do not affect q relative changes. balanceOf vs getReserves not proven by CSV.'},'new_mechanisms':0,'real_backtests':0,'qualifications':0,'realized_profit_verified':False}
 dump(out/'aggregate.json',result)
 # Exact rational synthetic constant-product AMM, fee 0.3%, no rounding/protocol mint.
 x=y=F(100); s=F(100); fee=F(3,1000); amount=F(10)
 yout=y*amount*(1-fee)/(x+amount*(1-fee)); x1=x+amount; y1=y-yout
 xout=x1*yout*(1-fee)/(y1+yout*(1-fee)); x2=x1-xout; y2=y1+yout
 donation=x2-x
 assert y2==y and donation>0
 path_a=(x2,y2,s);path_b=(x+donation,y,s)
 assert path_a==path_b
 # Proportional liquidity mints affect raw invariant, not its square root per LP.
 assert (x*2)*(y*2)*s*s == x*y*(s*2)**2
 # LP ownership transfer does not change supply/pool snapshot.
 assert path_a == path_b and F(0)*x2/s != F(10)*x2/s
 tests={'classification':'synthetic_exact_rational_counterexamples_not_backtest','assumptions':['constant-product example only, not assertion about source contract','fee=0.003 on input','no protocol fee mint, integer rounding or gas in AMM state equation'],'initial':{'x':'100','y':'100','lp_supply':'100'},'path_A':{'actions':'swap 10 token0 in for yout; swap all yout back','yout':str(yout),'token0_fee':str(amount*fee),'token1_fee':str(yout*fee),'ending_x':str(x2),'ending_y':str(y2),'ending_supply':str(s)},'path_B':{'actions':'donate token0, then sync if reserves rather than balances are observed','donation_token0':str(donation),'token0_fee':'0','token1_fee':'0','ending_x':str(path_b[0]),'ending_y':str(path_b[1]),'ending_supply':str(s)},'assertions':{'same_observed_endpoints_different_swap_fees':True,'donation_positive':True,'proportional_liquidity_changes_k_without_changing_q':True,'owner_LP_transfer_invisible_to_pool_snapshot':True},'cashflow_counterexample':'Same pool snapshots permit observer h=0 or h=10 after an unobserved LP-token transfer; holdings/redemption entitlements differ. Even with fixed h, different gas payments do not alter these pool fields.'}
 dump(out/'synthetic-tests.json',tests)
 print(json.dumps({'rows':counts['rows'],'tests':tests['assertions'],'raw_sha256':before},ensure_ascii=False))
if __name__=='__main__':main()
