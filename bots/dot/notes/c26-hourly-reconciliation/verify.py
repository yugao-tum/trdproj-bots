#!/usr/bin/env python3
"""Read-only verification of published C26 summaries against eight official responses.

Raw responses are intentionally not bundled. Use --input-dir for archived JSON
files named by provenance.json, or --fetch for public unauthenticated URLs.
Neither mode writes raw data. --require-capture-hash requires exact capture bytes;
otherwise byte differences are reported and canonical OHLCV still must match.
"""
import argparse
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, localcontext
import hashlib
import json
from pathlib import Path
import sys
from urllib.request import Request, urlopen

FIELDS = ('open', 'high', 'low', 'close', 'volume')
HERE = Path(__file__).resolve().parent


def require(condition, message):
    if not condition:
        raise ValueError(message)


def unique(items):
    result = {}
    for key, value in items:
        require(key not in result, 'duplicate JSON key: ' + key)
        result[key] = value
    return result


def load(raw):
    return json.loads(raw, object_pairs_hook=unique, parse_float=Decimal,
                      parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))


def dec(value):
    require(not isinstance(value, bool), 'boolean numeric value')
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ValueError('invalid decimal value') from None
    require(result.is_finite(), 'nonfinite decimal value')
    return result


def norm(value):
    result = format(dec(value), 'f')
    return result.rstrip('0').rstrip('.') if '.' in result else result


def epoch(iso):
    return int(datetime.fromisoformat(iso).replace(tzinfo=timezone.utc).timestamp())


def parse(raw, source):
    doc = load(raw)
    require(doc['data']['pair'] == source['pair'], 'returned pair mismatch')
    rows = []
    for item in doc['data']['ohlc']:
        t = dec(item['timestamp'])
        require(t == t.to_integral_value(), 'fractional epoch')
        values = {key: dec(item[key]) for key in FIELDS}
        require(all(values[k] > 0 for k in FIELDS if k != 'volume'), 'nonpositive price')
        require(values['volume'] >= 0, 'negative volume')
        require(values['low'] <= min(values['open'], values['close']) <=
                max(values['open'], values['close']) <= values['high'], 'OHLC envelope')
        rows.append({'timestamp': int(t), **values})
    start = epoch(source['day']) if source['resolution_seconds'] == 3600 else epoch(source['window_start_utc'])
    expected = [start + i * source['resolution_seconds'] for i in range(source['expected_rows'])]
    require([row['timestamp'] for row in rows] == expected, 'missing, duplicate, shifted or unordered UTC grid')
    if source['resolution_seconds'] == 86400:
        require(expected[-1] + 86400 == epoch(source['window_end_utc_exclusive']), 'daily right boundary')
    canonical_rows = [{'timestamp': row['timestamp'], **{k: norm(row[k]) for k in FIELDS}} for row in rows]
    canonical = json.dumps({'pair': source['pair'], 'ohlc': canonical_rows},
                           sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()
    return rows, hashlib.sha256(canonical).hexdigest()


def aggregate(rows):
    return {'open': rows[0]['open'], 'high': max(row['high'] for row in rows),
            'low': min(row['low'] for row in rows), 'close': rows[-1]['close'],
            'volume': sum((row['volume'] for row in rows), Decimal(0))}


def utc(row):
    return datetime.fromtimestamp(row['timestamp'], timezone.utc).isoformat()


def compare_rows(rows, reference):
    require(len(rows) == len(reference), 'threshold-hit row count mismatch')
    for row, ref in zip(rows, reference):
        require(row['timestamp'] == ref['timestamp'] and utc(row) == ref['utc'], 'threshold-hit time mismatch')
        require(all(row[k] == dec(ref[k]) for k in FIELDS), 'threshold-hit OHLCV mismatch')


def verify(raw_by_id, require_capture_hash=False):
    provenance = load((HERE / 'provenance.json').read_bytes())
    expected = load((HERE / 'summary.json').read_bytes())
    require(len(provenance['sources']) == 8, 'must have six hourly and two daily sources')
    parsed = {}
    source_reports = []
    for source in provenance['sources']:
        raw = raw_by_id[source['id']]
        exact = hashlib.sha256(raw).hexdigest() == source['capture_sha256'] and len(raw) == source['capture_bytes']
        require(exact or not require_capture_hash, 'capture hash/bytes mismatch: ' + source['id'])
        rows, semantic_hash = parse(raw, source)
        require(semantic_hash == source['semantic_sha256'], 'canonical data differs from frozen capture: ' + source['id'])
        parsed[source['id']] = rows
        source_reports.append({'id': source['id'], 'rows': len(rows), 'capture_bytes_match': exact,
                               'semantic_sha256_match': True})
    all_daily_hits = set()
    for source in provenance['sources']:
        if source['resolution_seconds'] == 86400:
            all_daily_hits.update((source['pair'], utc(row)[:10]) for row in parsed[source['id']] if row['low'] <= Decimal('.99'))
    chosen_event_dates = set()
    hourly_rows = low_count = close_count = zeros = 0
    sample_reports = []
    for sample in expected['samples']:
        pair, day = sample['pair'], sample['date']
        symbol = pair.replace('/', '').lower()
        rows = parsed[symbol + '-' + day + '-hourly']
        daily_rows = parsed[symbol + '-daily']
        reference = next(row for row in daily_rows if row['timestamp'] == epoch(day))
        agg = aggregate(rows)
        for key in FIELDS:
            require(agg[key] == dec(sample['hour_aggregate'][key]), day + ' aggregate mismatch')
            require(reference[key] == dec(sample['frozen_daily'][key]), day + ' daily reference mismatch')
            require(agg[key] - reference[key] == dec(sample['aggregate_minus_daily'][key]) == 0, day + ' nonzero delta')
        low = [row for row in rows if row['low'] <= Decimal('.99')]
        close = [row for row in rows if row['close'] <= Decimal('.99')]
        zero = [utc(row) for row in rows if row['volume'] == 0]
        compare_rows(low, sample['low_at_or_below_0_99'])
        compare_rows(close, sample['close_at_or_below_0_99'])
        require(zero == sample['zero_volume_hours'], 'zero-volume timestamps differ')
        require(sample['hour_count'] == len(rows) == 24, 'hour count differs')
        role = 'background_previous_day' if (pair, day) == ('USDT/USD', '2026-06-07') else 'postselected_daily_low_trigger'
        require(sample['sample_role'] == role, 'sample role differs')
        if role == 'postselected_daily_low_trigger':
            chosen_event_dates.add((pair, day))
        hourly_rows += len(rows)
        low_count += len(low)
        close_count += len(close)
        zeros += len(zero)
        sample_reports.append({'pair': pair, 'day': day, 'hour_count': len(rows),
                               'low_hits': len(low), 'close_hits': len(close), 'all_ohlcv_deltas_zero': True})
    require(chosen_event_dates == all_daily_hits, 'chosen dates are not exactly all daily threshold-hit dates')
    counts = {'selected_days': len(expected['samples']), 'hourly_rows': hourly_rows,
              'low_threshold_hours': low_count, 'low_threshold_event_dates': len(chosen_event_dates),
              'close_threshold_hours': close_count, 'zero_volume_hours': zeros,
              'new_strategies': 0, 'new_pnl_backtests': 0}
    require(counts == expected['counts'], 'summary counts differ')
    return {'status': 'PASS', 'sources_verified': len(source_reports), 'counts': counts,
            'sources': source_reports, 'samples': sample_reports,
            'limitations': 'Verifies printed-price data only. Dates are not proven independent shocks; no execution or PnL proof.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument('--input-dir', type=Path, help='directory with eight response files named in provenance.json')
    modes.add_argument('--fetch', action='store_true', help='fetch the eight public official URLs without saving raw data')
    parser.add_argument('--require-capture-hash', action='store_true', help='also require exact archived text bytes')
    args = parser.parse_args()
    provenance = load((HERE / 'provenance.json').read_bytes())
    raw_by_id = {}
    for source in provenance['sources']:
        if args.input_dir is not None:
            raw = (args.input_dir / source['filename']).read_bytes()
        else:
            require(source['url'].startswith('https://www.bitstamp.net/api/v2/ohlc/'), 'nonofficial URL')
            with urlopen(Request(source['url'], headers={'User-Agent': 'C26-public-research-verifier/1.0'}), timeout=60) as response:
                raw = response.read(1_000_001)
            require(len(raw) <= 1_000_000, 'unexpectedly large response')
        raw_by_id[source['id']] = raw
    with localcontext() as ctx:
        ctx.prec = 80
        report = verify(raw_by_id, args.require_capture_hash)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    try:
        main()
    except (ValueError, KeyError, TypeError, OSError, StopIteration) as exc:
        print(json.dumps({'status': 'FAIL', 'error': str(exc)}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
