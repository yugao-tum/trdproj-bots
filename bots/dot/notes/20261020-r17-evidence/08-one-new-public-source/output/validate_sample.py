"""Offline validation only. No network, signing, trading, or credentials."""
import json, pathlib
p=pathlib.Path(__file__).parent
c=json.loads((p/'competition-sample.json').read_text())
os=json.loads((p/'settled-orders-sample.json').read_text())
ts=json.loads((p/'trade-sample.json').read_text())
assert len(os)==len(ts)==1
o,t=os[0],ts[0]
checks={'uid_join':o['uid']==t['orderUid'], 'settlement_tx_join':t['txHash']==c['transactionHashes'][0], 'auction_order_membership':o['uid'] in c['auction']['orders'], 'fulfilled':o['status']=='fulfilled','buy_amount_equal':o['executedBuyAmount']==t['buyAmount'],'sell_amount_equal':o['executedSellAmount']==t['sellAmount'], 'nonzero_dynamic_fee':int(o['executedFee'])>0, 'zero_deprecated_fee':int(o['executedFeeAmount'])==0, 'three_protocol_fee_components':len(t['executedProtocolFees'])==3}
assert all(checks.values())
r={'checks':checks,'auction_id':c['auctionId'],'block_number':t['blockNumber'],'log_index':t['logIndex'],'sample_orders':1,'sample_trades':1,'raw_executed_fee':o['executedFee'],'fee_token':o['executedFeeToken'],'creation_time_not_fill_time':o['creationDate'],'missing_exact_fill_timestamp':True,'gas_cost_is_estimated_attribution_not_receipt':True,'new_mechanisms':0,'new_backtests':0,'complete_cash_chains':0,'qualification_count':0}
(p/'validation.json').write_text(json.dumps(r,indent=2)+'\n'); print(json.dumps(r,indent=2))
