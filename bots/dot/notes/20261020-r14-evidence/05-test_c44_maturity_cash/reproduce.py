"""Offline conditional accounting only. Never claims executable/net realized PnL."""
import json, hashlib, argparse
from pathlib import Path
from decimal import Decimal as D, getcontext
getcontext().prec=50
O=Path(__file__).resolve().parent
B=Path('retained-inputs')
def run(base=B):
 p=json.loads((O/'preregister.json').read_text())
 for f,h in p['selected_input_hashes'].items():
  assert hashlib.sha256((base/f).read_bytes()).hexdigest()==h, f
 def read(f):return json.loads((base/f).read_text(),parse_float=D)
 h=read('workers/operator-c44-history/evidence/09-history-eusd.body')['results']
 h=sorted(h,key=lambda r:r['timestamp']); e=next(r for r in h if r['timestamp'][:10]>'2023-09-11')
 tx=next(r for r in read('workers/operator-c44-history/evidence/16-eusd-public-participant-pnl.body')['results'] if r['action']=='redeemPy')
 receipt=read('workers/operator-c44-chain/receipt-decoded.json')
 def words(idx):
  data=next(l['data'][2:] for l in receipt['logs'] if int(l['logIndex'],16)==idx)
  return [int(data[i:i+64],16) for i in range(0,len(data),64)]
 pt,sy=words(327); total_sy,eusd=words(331)
 ratio=D(sy)/D(pt)*D(eusd)/D(total_sy)
 assert words(321)[1]+sy==total_sy
 price=e['ptPrice']; cap=D(2500); a=tx['assetUsd'];fee=D('.003');q0=cap/price;q=cap/(price*(1+fee))
 # Scenario fixes one eUSD per PT, consistent with observed units to integer tolerance.
 assert abs(ratio-1)<D('1e-17')
 assert e['timestamp'][:10]=='2023-09-12';assert len(h)==472
 scenarios={}
 for name,f in [('zero_cost_ceiling',D(0)),('guide_cost_proxy',fee)]:
  units=cap/(price*(1+f));value=units*a*(1-f);pnl=value-cap
  scenarios[name]={'pt_quantity':str(units),'terminal_indexed_mark_usd':str(value),'conditional_pnl_before_gas_usdt':str(pnl),'capital_return_before_gas':str(pnl/D(5000)),'venue_return_before_gas':str(pnl/cap),'breakeven_eusd_usd_before_gas':str(price*(1+f)/(1-f)),'peg_loss_tolerance_before_gas':str(1-price*(1+f)/(1-f))}
 return {'stage':'conditional accounting; no complete historical executable backtest','entry_date':e['timestamp'],'entry_mark_usd':str(price),'entry_daily_volume_usd':str(e['tradingVolume']),'entry_pool_tvl_usd':str(e['tvl']),'terminal_date':tx['timestamp'],'terminal_indexed_eusd_usd':str(a),'receipt_eusd_per_pt_unit_check':str(ratio),'mixed_tx_gas_eth':str(D(int(receipt['gasUsed'],16)*int(receipt['effectiveGasPrice'],16))/D(10**18)),'scenarios':scenarios,'actual_executable_cash_pnl':None,'independent_complete_outcomes':0,'total_daily_rows':933,'selected_maturities':1,'external_requests':0}
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--base',type=Path,default=B);a=ap.parse_args();print(json.dumps(run(a.base),indent=2))
