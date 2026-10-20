import json, tempfile, unittest
from pathlib import Path
from audit_event_panel import classify, sha
O=Path(__file__).parent
class AuditTests(unittest.TestCase):
 def test_lfs_pointer_not_data(self):
  with tempfile.TemporaryDirectory(dir=O) as d:
   p=Path(d)/'x';p.write_bytes(b'version https://git-lfs.github.com/spec/v1\noid sha256:abc\nsize 1234\n');self.assertEqual(classify(p),'git_lfs_pointer')
 def test_footer_alone_not_complete(self):
  with tempfile.TemporaryDirectory(dir=O) as d:
   p=Path(d)/'x';p.write_bytes(b'footer-json PAR1');self.assertEqual(classify(p),'not_complete_parquet_container')
 def test_inputs_pinned(self):
  for x in json.loads((O/'input-manifest.json').read_text()):self.assertEqual(sha(Path(x['path'])),x['sha256'])
 def test_real_pages_decoded(self):
  d=json.loads((O/'aggregate.json').read_text());self.assertEqual([x['rows'] for x in d['file_audit']],[187094,783350,258]);self.assertTrue(all(x['row_pages_decoded'] for x in d['file_audit']))
 def test_join_accounting(self):
  c=json.loads((O/'aggregate.json').read_text())['counts'];self.assertEqual(c['quote_slugs_with_label']+c['quote_slugs_without_label'],c['quote_unique_slugs']);self.assertEqual(sum(c['quote_categories'].values()),c['quote_rows']);self.assertLessEqual(c['quote_rows_with_label'],c['quote_rows'])
 def test_no_false_finality_or_returns(self):
  c=json.loads((O/'aggregate.json').read_text())['counts'];self.assertEqual(c['resolution_nonnull_evidence_uri'],0);self.assertEqual(c['complete_trade_event_panels'],0);self.assertIsNone(c['net_pnl']);self.assertEqual(c['strategy_backtests'],0)
 def test_exactly_20_local_examples(self):self.assertEqual(len(json.loads((O/'LOCAL_ONLY_20_FIELD_EXAMPLES.json').read_text())),20)
 def test_empty_panel_not_fabricated(self):self.assertEqual(json.loads((O/'frozen_panel.json').read_text())['sorted_first_30_event_ids'],[])
if __name__=='__main__':unittest.main()
