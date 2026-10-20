import importlib.util,pathlib,json,copy,hashlib,unittest
P=pathlib.Path(__file__).resolve().parent
sp=importlib.util.spec_from_file_location('decoder',P/'complete-log-decoder.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
D=json.loads((P/'decoded-events.json').read_text());S,B=m.schemas();V='0xba12222222228d8ba445958a75a0704d566bf2c8'
class Tests(unittest.TestCase):
 def test_keccak_empty(self):self.assertEqual(m.keccak(b''),'c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470')
 def test_not_sha3(self):self.assertNotEqual(m.keccak(b''),hashlib.sha3_256(b'').hexdigest())
 def test_transfer_hash(self):self.assertEqual(m.keccak(b'Transfer(address,address,uint256)'),'ddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef')
 def test_liquidation_hash(self):self.assertEqual(m.keccak(b'LiquidationCall(address,address,address,uint256,uint256,address,bool)'),'e413a321e8681d831f4dbccbca790d2952b56f977908e45be37335533e005286')
 def test_flash_hash(self):self.assertEqual(m.keccak(b'FlashLoan(address,address,uint256,uint256)'),'0d7d75e01ab95780d3cd1c8ec0dd6c2ce19e3a20427eec8bf53283b6fb8e95f0')
 def test_all_logs(self):self.assertEqual(sum(x['log_count']for x in D),1295);self.assertEqual(len(D),12)
 def test_all_liquidations(self):self.assertEqual(sum(x['liquidations']for x in D),80);self.assertEqual(D[0]['liquidations'],68)
 def test_no_mismatch(self):self.assertEqual(sum(x['mismatch_count']for x in D),0)
 def test_no_self_funded(self):self.assertFalse(any(x['own_funds_proven'] for x in D))
 def test_three_positive(self):self.assertEqual(sum(x['linked_loan_events']for x in D),3)
 def test_disbursement_repayment(self):
  for x in D:
   for e in x['financing_evidence']:self.assertTrue(e['disbursement_logs']);self.assertTrue(e['repayment_to_vault_logs'])
 def test_spoofed_emitter_rejected(self):
  l=copy.deepcopy(D[4]['loan_events_detail']);l[0]['emitter']='0x'+'12'*20;self.assertEqual(m.classify(l,set(D[4]['liquidation_payment_addresses']),V),[])
 def test_wrong_recipient_rejected(self):self.assertEqual(m.classify(D[4]['loan_events_detail'],{'0x'+'12'*20},V),[])
 def test_unknown_preserved(self):
  e=next(e for d in D for e in d['events'] if e['status']=='unknown_signature');self.assertIn('raw_data',e);self.assertIn('raw_topics',e)
 def test_truncation_rejected(self):
  e=D[4]['loan_events_detail'][0];raw={'logIndex':hex(e['log_index']),'address':e['emitter'],'topics':e['raw_topics'],'data':e['raw_data'][:-2]};self.assertEqual(m.decode(raw,S)['status'],'schema_mismatch')
 def test_oversized_address_rejected(self):
  with self.assertRaises(AssertionError):m.value('address','f'*64)
 def test_invalid_bool_rejected(self):
  with self.assertRaises(AssertionError):m.value('bool','0'*63+'2')
if __name__=='__main__':unittest.main(verbosity=2)
