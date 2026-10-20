"""Offline genuine Blockscout row normalization; never infer a complete lifecycle."""
import csv,json,pathlib,hashlib
from decimal import Decimal,localcontext
D=pathlib.Path(__file__).parent

def nxm(v):
 with localcontext() as ctx:
  ctx.prec=90
  return format(Decimal(int(v))/Decimal(10**18),'f')

def normalize(x):
 dec=x.get('decoded') or {}; kind=dec.get('method_call','unknown').split('(')[0]; p={a['name']:a['value'] for a in dec.get('parameters',[])}
 row={'block_number':x['block_number'],'log_index':x['index'],'tx_hash':x['transaction_hash'],'timestamp':x.get('block_timestamp'),'pool_address':x['address']['hash'],'event':kind,'token_id':p.get('tokenId'),'tranche_id':p.get('trancheId',p.get('tranche')),'user':p.get('user'),'parameters':p,'pool_principal_delta_base':None,'holder_principal_cash_base':None,'holder_reward_cash_base':None,'manager_reward_cash_base':None}
 if kind=='StakeDeposited':
  row.update(pool_principal_delta_base=str(int(p['amount'])),holder_principal_cash_base=str(-int(p['amount'])))
 elif kind=='StakeBurned': row['pool_principal_delta_base']=str(-int(p['amount']))
 elif kind=='Withdraw':
  stake=int(p['amountStakeWithdrawn']); reward=int(p['amountRewardsWithdrawn']); row['pool_principal_delta_base']=str(-stake)
  if str(p.get('tokenId'))=='0': row['manager_reward_cash_base']=str(reward)
  else: row.update(holder_principal_cash_base=str(stake),holder_reward_cash_base=str(reward))
 elif kind=='DepositExtended':
  row.update(pool_principal_delta_base=str(int(p['topUpAmount'])),holder_principal_cash_base=str(-int(p['topUpAmount'])))
 return row

def unique_rows(items):
 seen={}; rows=[]
 for x in items:
  key=(x['address']['hash'].lower(),x['transaction_hash'].lower(),x['index'])
  digest=hashlib.sha256(json.dumps(x,sort_keys=True).encode()).hexdigest()
  if key in seen:
   if seen[key]!=digest: raise ValueError('conflicting duplicate log')
   continue
  seen[key]=digest;rows.append(normalize(x))
 return sorted(rows,key=lambda r:(r['block_number'],r['log_index']))

def main():
 raw=json.loads((D/'raw/pool1-logs-p1.json').read_text());rows=unique_rows(raw['items']); factory=json.loads((D/'raw/factory-logs.json').read_text())
 fields=[k for k in rows[0] if k!='parameters']+['parameters_json']
 with (D/'actual-event-rows.csv').open('w') as f:
  w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
  for r in rows:
   out=dict(r);out['parameters_json']=json.dumps(out.pop('parameters'),sort_keys=True);w.writerow(out)
 from collections import Counter
 burns=[dict(r,amount_nxm=nxm(-int(r['pool_principal_delta_base']))) for r in rows if r['event']=='StakeBurned']
 summary={'claim':'C45','status':'draft_partial_authentic_events','complete_origin_lifecycles':0,'actual_holder_return':None,'qualified':False,'raw_factory_rows':len(factory['items']),'raw_pool_rows':len(raw['items']),'pool_rows_actually_normalized':len(rows),'factory_rows_used_for_holder_cashflow':0,'new_native_actual_rows':0,'event_counts':dict(Counter(r['event'] for r in rows)),'pool_burns':burns,'pagination_complete':False,'next_page_params':raw['next_page_params'],'ordering':['block_number','log_index'],'units':'NXM base units; 1 NXM = 10^18; integer calculations','semantics':{'pool_delta':'deposit positive; withdrawal/burn negative','holder_cash':'deposit negative; withdrawn principal and rewards positive; pool burn is not an immediate holder cash movement','manager_fee':'tokenId 0 reward withdrawals separate; no observed fee rows','reward':'expected minted/accrued reward is not holder receipt; genuine Withdraw still requires receipt success and NXM transfer reconciliation'},'missing':['origin StakeDeposited and DepositExtended history keyed by token/tranche','Withdraw including zero-principal reward-only rows','NFT ownership/transfer chain and origin ownership continuity','complete pool share history to allocate pool-level burn','historical implementation identity and successful receipts/actual NXM transfers','manager fee actual withdrawal rows and fee-state history'],'source_limits':['Blockscout pagination denied HTTP403; stopped after one request; no alternative route','GitHub commit metadata rate-limited403 earlier; reset unknown; no native retry','StakingPool.sol is master snapshot only, not fixed commit or historical implementation proof','fixed staking-events.sql excludes Withdraw rows when amountStakeWithdrawn=0 and does not select rewards','fixed reward SQL describes expected accrual, not actual recipient cash'],'native_requests':1,'native_model':'inherited OpenAI native agent; exact model identifier not exposed','native_cost':None}
 (D/'event-reconstruction.json').write_text(json.dumps(summary,indent=2)+'\n')
if __name__=='__main__':main()
