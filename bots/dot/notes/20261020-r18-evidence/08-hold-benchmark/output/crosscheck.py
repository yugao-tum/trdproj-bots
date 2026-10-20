"""Check independently computed comparator initial state and LP reference against role04."""
import hashlib,json,math
from pathlib import Path
P=Path(__file__).resolve().parent
engine=P.parent.parent/'04-nav-engine/output/summary.json'
a=json.loads((P/'benchmark-results.json').read_text());b=json.loads(engine.read_text())
assert a['window']['first_utc']==b['first']['utc'] and a['window']['last_utc']==b['last']['utc']
assert a['window']['pool_observations']==b['observations']
checks=0;errors=[]
for s in a['scenarios']:
 for c in s['comparisons']:
  e=next(x for x in b['scenarios'] if x['cost_each_side']==s['cost_per_side'] and x['entry_pending_fraction']==c['entry_pending_fraction'] and x['exit_pending_fraction']==c['exit_pending_fraction'])
  for coin,key in [('USDC','initial_usdc'),('USDT','initial_usdt')]:
   assert math.isclose(float(s['initial_token_quantities'][coin]),e[key],abs_tol=1e-9,rel_tol=0);checks+=1
  error=abs(c['lp_terminal_before_unknown_gas']-e['terminal_deployed']);errors.append(error)
  assert error<1e-8;checks+=1
r={'status':'PASS file arithmetic only, not historical execution validation','assertions':checks+2,'max_lp_terminal_difference_usd':max(errors),'engine_summary_sha256':hashlib.sha256(engine.read_bytes()).hexdigest(),'benchmark_sha256':hashlib.sha256((P/'benchmark-results.json').read_bytes()).hexdigest()}
(P/'crosscheck-results.json').write_text(json.dumps(r,indent=2)+'\n');print(r)
