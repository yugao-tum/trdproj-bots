"""Offline normalized-evidence matcher. No RPC, pricing, PnL, or proof verification.
Evidence assertions are inputs, not independently authenticated by this program.
"""
import json
import sys
from collections import Counter

RELAY_FIELDS = ('origin_chain', 'destination_chain', 'deposit_id', 'depositor',
                'recipient', 'exclusive_relayer', 'input_token', 'output_token',
                'input_amount', 'output_amount', 'fill_deadline',
                'exclusivity_deadline', 'message')
IDENTITY = ('chain', 'spoke_pool', 'bundle', 'leaf', 'token', 'decimals', 'address')

def uint(v):
    return isinstance(v, str) and v.isascii() and v.isdigit() and str(int(v)) == v

def match(data):
    results = []
    seen_cash = set()
    seen_fill = set()
    ds = data.get('deposits', [])
    fs = data.get('fills', [])
    ls = data.get('leaves', [])
    es = data.get('executions', [])
    allocations = data.get('allocations', [])
    execution_bindings = {}
    for e in es:
        uid = (e.get('chain'), e.get('tx_hash'), e.get('log_index'))
        execution_bindings.setdefault(uid, set()).add(tuple(e.get(k) for k in IDENTITY))
    def result(a, status, reason, cash='0'):
        results.append({'allocation_id': a.get('id'), 'status': status,
                        'reason': reason, 'cash_amount_raw': cash,
                        'identity': {k:a.get(k) for k in IDENTITY},
                        'pnl': None})
    for a in allocations:
        def reject(reason): result(a, 'rejected', reason)
        def unknown(reason): result(a, 'unknown', reason)
        if any(k not in a for k in (*IDENTITY, 'fill_id', 'amount_raw', 'kind')):
            reject('missing_required_identity'); continue
        if a['kind'] != 'relayer_repayment':
            reject('not_relayer_repayment'); continue
        if not uint(a['amount_raw']) or int(a['amount_raw']) == 0:
            reject('invalid_atomic_amount'); continue
        fills = [f for f in fs if f.get('id') == a['fill_id']]
        if len(fills) != 1:
            unknown('fill_missing_or_ambiguous'); continue
        f = fills[0]
        if f.get('type') != 'fast' or f.get('finalized') is not True:
            reject('not_finalized_fast_fill'); continue
        relay = f.get('relay', {})
        if any(k not in relay for k in RELAY_FIELDS):
            unknown('incomplete_relay_data'); continue
        deposits = [d for d in ds if d.get('relay') == relay and d.get('origin_spoke') == f.get('origin_spoke')]
        if len(deposits) != 1 or deposits[0].get('finalized') is not True:
            unknown('source_deposit_missing_ambiguous_or_unfinalized'); continue
        if f.get('mapping_evidence') is None:
            unknown('token_mapping_not_bound'); continue
        if any(a[k] != f.get('repayment', {}).get(k) for k in ('chain', 'token', 'decimals', 'address')):
            reject('repayment_identity_mismatch'); continue
        dec = a['decimals']
        registry = [t for t in data.get('tokens', []) if (t.get('chain'),t.get('token')) == (a['chain'],a['token'])]
        if len(registry) != 1 or type(dec) is not int or registry[0].get('decimals') != dec:
            reject('token_decimals_mismatch_or_unknown'); continue
        leaves = [l for l in ls if all(l.get(k) == a[k] for k in IDENTITY)]
        if len(leaves) != 1:
            unknown('leaf_missing_or_ambiguous'); continue
        leaf = leaves[0]
        if not uint(leaf.get('amount_raw')):
            reject('invalid_leaf_amount'); continue
        # Neither a refund event nor an address match identifies a deposit-level payout.
        if not a.get('allocation_evidence') or leaf.get('components_complete') is not True:
            unknown('aggregate_allocation_unproven'); continue
        group = [x for x in allocations if all(x.get(k) == a[k] for k in IDENTITY)]
        comps = leaf.get('components', [])
        if len({x.get('id') for x in group}) != len(group):
            reject('duplicate_allocation_id'); continue
        if not all(uint(x.get('amount_raw')) for x in comps) or sum(int(x['amount_raw']) for x in comps) != int(leaf['amount_raw']):
            reject('leaf_component_sum_mismatch'); continue
        matching = [x for x in comps if x.get('allocation_id') == a['id'] and x.get('fill_id') == a['fill_id'] and x.get('kind') == a['kind'] and x.get('amount_raw') == a['amount_raw']]
        if len(matching) != 1:
            reject('component_binding_mismatch'); continue
        # A fill can appear only once, including attempts to allocate it into another leaf.
        if a['fill_id'] in seen_fill:
            reject('duplicate_fill_allocation'); continue
        executions = [e for e in es if all(e.get(k) == a[k] for k in IDENTITY)]
        if not executions:
            unknown('not_paid_or_deferred'); continue
        unique = {}
        ambiguous = False
        for e in executions:
            uid = (e.get('chain'), e.get('tx_hash'), e.get('log_index'))
            if uid in unique and unique[uid] != e: ambiguous = True
            unique[uid] = e
        if ambiguous:
            reject('conflicting_execution_identity'); continue
        paid = [e for e in unique.values() if e.get('status') == 'paid' and e.get('finalized') is True and e.get('transfer_evidence') and e.get('amount_raw') == leaf['amount_raw']]
        if len(paid) != 1:
            unknown('no_unique_finalized_cash_transfer'); continue
        e = paid[0]
        if len(execution_bindings[(e.get('chain'), e.get('tx_hash'), e.get('log_index'))]) != 1:
            reject('cash_event_bound_to_multiple_identities'); continue
        if e.get('route') == 'deferred_claim' and not e.get('claim_to_leaf_evidence'):
            unknown('deferred_claim_allocation_unproven'); continue
        if e.get('route') not in ('direct', 'deferred_claim'):
            reject('unknown_payment_route'); continue
        if not e.get('tx_hash') or type(e.get('log_index')) is not int or e['log_index'] < 0:
            reject('missing_execution_identity'); continue
        cash_id = (e['chain'], e['tx_hash'], e['log_index'], a['id'])
        if cash_id in seen_cash:
            reject('duplicate_cash_allocation'); continue
        seen_cash.add(cash_id); seen_fill.add(a['fill_id'])
        result(a, 'matched', 'explicit_component_and_finalized_transfer', a['amount_raw'])
    unallocated = []
    for leaf in ls:
        matched_amount = sum(int(r['cash_amount_raw']) for r in results if r['status']=='matched' and all(r['identity'].get(k)==leaf.get(k) for k in IDENTITY))
        unallocated.append({'identity': {k:leaf.get(k) for k in IDENTITY},
                            'unallocated_amount_raw': str(int(leaf['amount_raw'])-matched_amount) if uint(leaf.get('amount_raw')) else None,
                            'meaning': 'Not attributed cash; may include pending or depositor components.'})
    return {'synthetic': data.get('synthetic') is True, 'results': results,
            'status_counts': dict(Counter(r['status'] for r in results)),
            'observed_sample': False, 'pnl_computed': False, 'unallocated': unallocated,
            'warning': 'Conditional on supplied evidence assertions; not a chain verifier or economic ledger.'}

if __name__ == '__main__':
    with open(sys.argv[1]) as f: data = json.load(f)
    print(json.dumps(match(data), indent=2))
