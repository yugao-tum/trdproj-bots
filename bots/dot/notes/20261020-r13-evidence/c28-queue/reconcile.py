"""Source-bound v4.1.0 accounting checks; no RPC, trading or synthetic-to-real promotion."""
E27 = 10**27

def claimable(amount, shares, max_share_rate):
    if min(amount, shares, max_share_rate) <= 0:
        raise ValueError('positive integer accounting inputs required')
    return shares * max_share_rate // E27 if amount * E27 // shares > max_share_rate else amount

def gas_wei(receipt):
    if receipt is None:
        return None
    return int(receipt['gasUsed']) * int(receipt['effectiveGasPrice'])

def reconcile(x):
    missing = [k for k in ('request_id','request','finalization','claim','historical_implementation') if x.get(k) is None]
    if missing:
        return {'status':'incomplete_real_evidence','missing':missing,'profit_wei':None,'elapsed_seconds':None}
    r,f,c = (x[k] for k in ('request','finalization','claim'))
    assert f['from'] <= x['request_id'] <= f['to'], 'v4.1.0 inclusive event range'
    assert r['timestamp'] <= f['timestamp'] <= c['timestamp']
    expected = claimable(int(r['amount_steth_wei']), int(r['shares']), int(f['max_share_rate']))
    assert expected == int(c['amount_eth_wei'])
    gas = {k:gas_wei(x.get(k+'_receipt')) for k in ('request','claim')}
    # Missing purchase cost, full ownership transfers, or receipt evidence precludes profit.
    profit = None
    if x.get('entry_cost_wei') is not None and x.get('ownership_chain_complete') is True and x.get('other_cash_cost_wei') is not None and all(v is not None for v in gas.values()):
        profit = expected-int(x['entry_cost_wei'])-sum(gas.values())-int(x['other_cash_cost_wei'])
    return {'status':'accounting_reconciled_not_backtest','expected_claim_wei':expected,'gas_wei':gas,
            'elapsed_seconds':c['timestamp']-r['timestamp'],'profit_wei':profit}

if __name__ == '__main__':
    import json, pathlib
    print(json.dumps(reconcile(json.loads(pathlib.Path(__file__).with_name('queue-lifecycle.json').read_text())),indent=2))
