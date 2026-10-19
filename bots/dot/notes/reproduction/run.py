#!/usr/bin/env python3
"""Portable, offline entry point for hand tests and 26 frozen historical scenarios."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def canonical(value, exclusions):
    value = copy.deepcopy(value)
    for path in exclusions:
        parent = value
        for key in path[:-1]:
            parent = parent[key]
        del parent[path[-1]]
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()).hexdigest()

def verify(output):
    expected = json.loads((HERE / 'expected_outputs.json').read_text())
    checks = []
    for family, spec in expected['families'].items():
        directory = output / family
        for name, ref in spec['files'].items():
            actual = canonical(json.loads((directory/name).read_text()), ref['excluded_metadata_paths']) if 'canonical_sha256' in ref else sha(directory/name)
            target = ref.get('canonical_sha256', ref.get('sha256'))
            if actual != target:
                raise AssertionError(f'exact regression mismatch: {family}/{name}')
            checks.append(f'{family}/{name}')
    return {'passed': True, 'scenario_count': 26, 'families': {'spot-screen':8, 'spot-halfcap':12, 'c40':6}, 'verified_outputs': checks, 'comparison': 'Exact SHA256 for CSV bytes and canonical JSON after listed metadata exclusions; no numeric tolerance.'}

def hand_tests():
    names = ['test_spot_screen', 'test_sensitivity', 'test_c40_screen', 'test_operator_regression.HandComputedHodlTests']
    suite = unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName(name) for name in names)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise AssertionError('hand tests failed')
    return result.testsRun

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['hand-tests', 'reproduce', 'verify'])
    parser.add_argument('--input-dir', type=Path)
    parser.add_argument('--output-dir', required=True, type=Path)
    args = parser.parse_args()
    output = args.output_dir.resolve()
    if output == HERE or output.is_relative_to(HERE):
        raise ValueError('Keep run outputs outside the release package; choose a separate output directory')
    origins = json.loads((HERE/'source_origins.json').read_text())
    for name, info in origins.items():
        if sha(HERE/name) != info['release_sha256']:
            raise ValueError('packaged source changed: '+name)
    output.mkdir(parents=True, exist_ok=True)
    if args.mode == 'verify':
        print(json.dumps(verify(output), indent=2)); return
    temp = output/'test-temp'; temp.mkdir(exist_ok=True)
    tempfile.tempdir = str(temp)
    count = hand_tests()
    if args.mode == 'hand-tests':
        print(json.dumps({'hand_tests_passed':count})); return
    if args.input_dir is None:
        parser.error('reproduce requires --input-dir')
    inputs = args.input_dir.resolve()
    manifest = json.loads((HERE/'data_provenance.json').read_text())
    for name, info in manifest['normalized_inputs'].items():
        if sha(inputs/name) != info['sha256']:
            raise ValueError('frozen input hash mismatch: '+name)
    for family in ['spot-screen', 'spot-halfcap', 'c40']:
        if (output/family).exists():
            raise ValueError('refusing to overwrite output family: '+family)
    import spot_screen as spot
    import sensitivity as half
    import c40_screen as c40
    spot.CSV_PATH = inputs/'spot_daily.csv'
    spot.OUT_DIR = output/'spot-screen'
    if spot.main() != 0:
        raise ValueError('original screen failed')
    half.DEFAULT_CSV = spot.CSV_PATH
    half.REFERENCE_ORIGINAL_DIR = spot.OUT_DIR
    half.OUT_DIR = output/'spot-halfcap'
    if half.main(['--csv', str(spot.CSV_PATH), '--execute']) != 0:
        raise ValueError('sensitivity failed')
    c40.SPOT, c40.FUND = spot.CSV_PATH, inputs/'funding.csv'
    c40.SHAS = {c40.SPOT:manifest['normalized_inputs']['spot_daily.csv']['sha256'], c40.FUND:manifest['normalized_inputs']['funding.csv']['sha256'], c40.LOADER:origins['spot_screen.py']['release_sha256'], c40.WORK/'C40_PREREGISTRATION.md':origins['C40_PREREGISTRATION.md']['release_sha256']}
    c40.OUT_DIR = output/'c40'
    c40.main()
    regression = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromName('test_operator_regression.FrozenHalfScaleRegressionTests'))
    if not regression.wasSuccessful():
        raise AssertionError('half-scale regression failed')
    report = verify(output)
    report['hand_tests_passed'] = count
    report['half_scale_regression_tests_passed'] = regression.testsRun
    (output/'verification.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))

if __name__ == '__main__':
    main()
