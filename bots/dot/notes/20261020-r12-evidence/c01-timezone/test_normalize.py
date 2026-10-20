import json, unittest
from pathlib import Path
from normalize import normalize
ROOT=Path(__file__).parent
CASES=json.loads((ROOT/'fixtures.json').read_text())
class SyntheticFixtures(unittest.TestCase):
    def test_cases(self):
        results=[]
        for case in CASES:
            with self.subTest(case=case['id']):
                self.assertTrue(case['synthetic'])
                actual=normalize(**case['input']); expected=case['expected']; results.append(dict(id=case['id'],synthetic=True,actual=actual))
                self.assertEqual(actual['status'],expected['status']); self.assertEqual(actual['reason'],expected['reason']); self.assertFalse(actual['actual_viewer_proven'])
                if expected['status'] in ('rejected','uncertain'): self.assertEqual(actual['candidates'],[])
                if 'utc_candidates' in expected: self.assertEqual([c['utc'] for c in actual['candidates']],expected['utc_candidates'])
                if 'folds' in expected: self.assertEqual([c['station_fold'] for c in actual['candidates']],expected['folds'])
                for key,outkey in [('utc','utc'),('station_time','station_time'),('fold','station_fold'),('date_differ','utc_station_date_differ')]:
                    if key in expected:self.assertEqual(actual['candidates'][0][outkey],expected[key])
        (ROOT/'fixture-results.json').write_text(json.dumps(results,indent=2)+'\n')
    def test_bad_evidence(self):
        for e in (None,{}, {'executed_source_version':'yes'}):
            r=normalize('2026-10-20T00:00:00Z','America/New_York','UTC',e)
            self.assertEqual(r['status'],'normalized_reference' if e=={} else 'rejected')
if __name__=='__main__': unittest.main(verbosity=2)
