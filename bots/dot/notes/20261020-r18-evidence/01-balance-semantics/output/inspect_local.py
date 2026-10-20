"""Read-only CSV audit. Does not import/execute the author's collector or use RPC."""
import csv, hashlib, json, sys
from pathlib import Path
from decimal import Decimal
from datetime import datetime, timezone
p=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parents[3]/'r16-proposal/07-github-data/local-data/pool-balances.csv'
# Explicit default absolute input if worker tree nesting differs.
if not p.exists(): p=Path('retained-inputs/trdproj-research-20261019/continuation-20261020/workers/r16-proposal/07-github-data/local-data/pool-balances.csv')
h=lambda:hashlib.sha256(p.read_bytes()).hexdigest()
before=h(); expected='531dd907a5337c9bbeda5dba592ce1dfec3122803c1e98e9c59cf6913333adf6'
assert before==expected
with p.open() as f:
 reader=csv.DictReader(f); fields=reader.fieldnames; rows=list(reader)
keys=['pool_address','token0_address','token1_address','token0_symbol','token1_symbol']
constants={k:sorted(set(r[k] for r in rows)) for k in keys}
blocks=[int(r['block']) for r in rows]; ts=[int(r['ts']) for r in rows]
result={'input_sha256':before,'rows':len(rows),'fields':fields,'constants':constants,'all_constants_unique':all(len(v)==1 for v in constants.values()),'all_balances_and_supply_positive':all(Decimal(r[k])>0 for r in rows for k in ['token0_bal','token1_bal','lp_supply']),'unique_blocks':len(set(blocks)),'all_steps_100':all(b-a==100 for a,b in zip(blocks,blocks[1:])),'timestamps_strictly_increasing':all(b>a for a,b in zip(ts,ts[1:])),'utc_range':[datetime.fromtimestamp(t,timezone.utc).isoformat() for t in [ts[0],ts[-1]]],'endpoint_rows':[rows[0],rows[-1]],'classification':'CONDITIONAL','new_mechanisms':0,'actual_backtests':0,'qualified':0}
assert h()==before
result['input_unchanged']=True
print(json.dumps(result,ensure_ascii=False,indent=2))
