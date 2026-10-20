import unittest, json, copy
from pathlib import Path
from matcher import match

HERE=Path(__file__).parent

def base():
    relay=dict(origin_chain=1,destination_chain=10,deposit_id='1',depositor='depositor',recipient='recipient',exclusive_relayer='none',input_token='usdc-1',output_token='usdc-10',input_amount='100000000',output_amount='99000000',fill_deadline=200,exclusivity_deadline=100,message='0x')
    ident=dict(chain=10,spoke_pool='spoke-10',bundle='7',leaf='3',token='usdc-10',decimals=6,address='relayer')
    return dict(synthetic=True,tokens=[dict(chain=10,token='usdc-10',decimals=6)],deposits=[dict(id='d1',origin_spoke='spoke-1',relay=relay,finalized=True)],fills=[dict(id='f1',origin_spoke='spoke-1',relay=copy.deepcopy(relay),type='fast',finalized=True,mapping_evidence='synthetic:mapping:1',repayment={k:ident[k] for k in ('chain','token','decimals','address')})],leaves=[dict(**ident,amount_raw='99900000',components_complete=True,components=[dict(allocation_id='a1',fill_id='f1',kind='relayer_repayment',amount_raw='99900000')])],allocations=[dict(**ident,id='a1',fill_id='f1',kind='relayer_repayment',amount_raw='99900000',allocation_evidence='synthetic:allocation:1')],executions=[dict(**ident,tx_hash='synthetic-tx-1',log_index=0,status='paid',finalized=True,amount_raw='99900000',route='direct',transfer_evidence='synthetic:transfer:1')])

cases=[]
def add(name, mutate, expected, reason):
    d=base(); mutate(d); cases.append(dict(name=name,input=d,expected=expected,reason=reason))
add('positive',lambda d:None,'matched','explicit_component_and_finalized_transfer')
add('wrong_chain',lambda d:d['allocations'][0].update(chain=137),'rejected','repayment_identity_mismatch')
add('wrong_token',lambda d:d['allocations'][0].update(token='usdt-10'),'rejected','repayment_identity_mismatch')
add('deposit_refund_not_repayment',lambda d:d['allocations'][0].update(kind='deposit_refund'),'rejected','not_relayer_repayment')
add('deferred_not_received',lambda d:d['executions'][0].update(status='deferred'),'unknown','no_unique_finalized_cash_transfer')
add('duplicate_execution_ignored',lambda d:d['executions'].append(copy.deepcopy(d['executions'][0])),'matched','explicit_component_and_finalized_transfer')
add('duplicate_allocation_rejected',lambda d:d['allocations'].append(copy.deepcopy(d['allocations'][0])),'rejected','duplicate_allocation_id')
add('aggregate_unallocated',lambda d:d['leaves'][0].update(components_complete=False),'unknown','aggregate_allocation_unproven')
add('missing_deposit',lambda d:d.update(deposits=[]),'unknown','source_deposit_missing_ambiguous_or_unfinalized')
add('wrong_decimals',lambda d:d['tokens'][0].update(decimals=18),'rejected','token_decimals_mismatch_or_unknown')
add('deferred_claim_unbound',lambda d:d['executions'][0].update(route='deferred_claim'),'unknown','deferred_claim_allocation_unproven')
add('deferred_claim_bound',lambda d:d['executions'][0].update(route='deferred_claim',claim_to_leaf_evidence='synthetic:claim-allocation:1'),'matched','explicit_component_and_finalized_transfer')
add('unfinalized_cash',lambda d:d['executions'][0].update(finalized=False),'unknown','no_unique_finalized_cash_transfer')
add('relay_mismatch',lambda d:d['fills'][0]['relay'].update(output_amount='98000000'),'unknown','source_deposit_missing_ambiguous_or_unfinalized')
add('aggregate_amount_mismatch',lambda d:d['leaves'][0].update(amount_raw='99900001'),'rejected','leaf_component_sum_mismatch')
add('slow_fill_excluded',lambda d:d['fills'][0].update(type='slow'),'rejected','not_finalized_fast_fill')
add('float_amount',lambda d:d['allocations'][0].update(amount_raw=99.9),'rejected','invalid_atomic_amount')
add('wrong_leaf',lambda d:d['allocations'][0].update(leaf='4'),'unknown','leaf_missing_or_ambiguous')
add('two_cash_events_unknown',lambda d:d['executions'].append(dict(d['executions'][0],tx_hash='synthetic-other-tx')),'unknown','no_unique_finalized_cash_transfer')
add('cross_leaf_cash_reuse',lambda d:d['executions'].append(dict(d['executions'][0],leaf='4')),'rejected','cash_event_bound_to_multiple_identities')

class TestMatcher(unittest.TestCase):
    def test_two_explicit_components(self):
        d=base()
        d['deposits'].append(copy.deepcopy(d['deposits'][0])); d['deposits'][1]['id']='d2';d['deposits'][1]['relay']['deposit_id']='2'
        d['fills'].append(copy.deepcopy(d['fills'][0]));d['fills'][1]['id']='f2';d['fills'][1]['relay']['deposit_id']='2'
        d['allocations'].append(dict(d['allocations'][0],id='a2',fill_id='f2'))
        d['leaves'][0]['components'].append(dict(d['leaves'][0]['components'][0],allocation_id='a2',fill_id='f2'))
        d['leaves'][0]['amount_raw']='199800000';d['executions'][0]['amount_raw']='199800000'
        o=match(d);self.assertEqual(o['status_counts'],{'matched':2});self.assertEqual(o['unallocated'][0]['unallocated_amount_raw'],'0')
        d['leaves'][0]['components_complete']=False
        o=match(d);self.assertEqual(o['status_counts'],{'unknown':2});self.assertEqual(o['unallocated'][0]['unallocated_amount_raw'],'199800000')
for case in cases:
    def test(self,c=case):
        o=match(c['input']); self.assertEqual(o['results'][0]['status'],c['expected']);self.assertEqual(o['results'][0]['reason'],c['reason']);self.assertIsNone(o['results'][0]['pnl'])
        cash=sum(int(x['cash_amount_raw']) for x in o['results']);self.assertEqual(cash,99900000 if c['expected']=='matched' else 0)
        self.assertFalse(o['pnl_computed']);self.assertTrue(o['synthetic'])
    setattr(TestMatcher,'test_'+case['name'],test)

if __name__=='__main__':
    (HERE/'fixtures.json').write_text(json.dumps({'synthetic':True,'cases':cases},indent=2))
    (HERE/'fixture-results.json').write_text(json.dumps({c['name']:match(c['input']) for c in cases},indent=2))
    unittest.main(verbosity=2)
