#!/usr/bin/env python3
"""Offline, bounded normalization of already-downloaded official ZIP/CHECKSUM pairs.

No network, third-party dependencies, ZIP extraction, or strategy execution.
Both final byte hashes must match before either normalized file is written.
"""
import argparse
import csv
import hashlib
import io
import json
import re
import zipfile
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
LIMIT = 5 * 1024 * 1024
DAY_US = 86400 * 1000000


def digest(payload):
    return hashlib.sha256(payload).hexdigest()


def bounded_read(path):
    if path.stat().st_size > LIMIT:
        raise ValueError('file exceeds 5 MiB limit: ' + path.name)
    with path.open('rb') as src:
        payload = src.read(LIMIT + 1)
    if len(payload) > LIMIT:
        raise ValueError('file grew beyond 5 MiB limit')
    return payload


def archive_rows(root, item):
    relative = Path(item['relative_archive'])
    if relative.is_absolute() or '..' in relative.parts:
        raise ValueError('unsafe relative archive path')
    root = root.resolve()
    path = (root / relative).resolve()
    if not path.is_relative_to(root):
        raise ValueError('archive resolves outside supplied directory')
    payload = bounded_read(path)
    checksum_path = path.with_name(path.name + '.CHECKSUM')
    checksum = bounded_read(checksum_path).decode('ascii').split()
    if len(checksum) != 2 or checksum[0] != item['archive_sha256'] or checksum[1].lstrip('*') != path.name:
        raise ValueError('official checksum or filename mismatch: ' + path.name)
    if digest(payload) != item['archive_sha256']:
        raise ValueError('frozen archive SHA256 mismatch: ' + path.name)
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        if archive.namelist() != [item['csv_member']]:
            raise ValueError('unexpected ZIP member list')
        info = archive.getinfo(item['csv_member'])
        if info.flag_bits & 1 or info.file_size != item['csv_uncompressed_bytes'] or info.file_size > LIMIT:
            raise ValueError('unexpected ZIP member size or encryption')
        with archive.open(info) as src:
            content = src.read(LIMIT + 1)
        if len(content) != info.file_size or len(content) > LIMIT:
            raise ValueError('unexpected expanded size')
    return list(csv.reader(io.StringIO(content.decode('utf-8-sig'))))


def to_us(raw):
    n = int(raw)
    if len(str(n)) == 13:
        us, unit = n * 1000, 'milliseconds'
    elif len(str(n)) == 16:
        us, unit = n, 'microseconds'
    else:
        raise ValueError('unrecognized timestamp unit')
    if not 1577836800000000 <= us < 1893456000000000:
        raise ValueError('timestamp outside 2020–2029')
    return us, unit


def iso(us):
    seconds, microseconds = divmod(us, 1000000)
    return datetime.fromtimestamp(seconds, timezone.utc).replace(microsecond=microseconds).isoformat().replace('+00:00', 'Z')


def dec(value):
    value = Decimal(value)
    if not value.is_finite():
        raise ValueError('nonfinite value')
    return value


def validate_header(header, kind):
    allowed = [{'opentime'}, {'open'}, {'high'}, {'low'}, {'close'}, {'volume'}, {'closetime'}, {'quotevolume', 'quoteassetvolume'}, {'count', 'numberoftrades'}, {'takerbuyvolume', 'takerbuybaseassetvolume'}, {'takerbuyquotevolume', 'takerbuyquoteassetvolume'}, {'ignore'}]
    if kind == 'markPriceKlines':
        for i in (5, 7, 8, 9, 10):
            allowed[i].add('ignore')
    normalized = [re.sub('[^a-z0-9]', '', value.lower()) for value in header]
    if len(normalized) != 12 or any(value not in allowed[i] for i, value in enumerate(normalized)):
        raise ValueError('unknown or out-of-order header')


def parse_row(raw, item, line):
    if len(raw) != 12:
        raise ValueError('expected 12 source columns')
    t, unit = to_us(raw[0])
    end, endunit = to_us(raw[6])
    o, h, l, c = map(dec, raw[1:5])
    if unit != endunit or min(o, h, l, c) <= 0 or h < max(o, l, c) or l > min(o, h, c):
        raise ValueError('invalid unit/OHLC')
    if t % DAY_US or not t <= end < t + DAY_US:
        raise ValueError('invalid daily timestamp')
    kind = item.get('kind', 'spot')
    if kind != 'markPriceKlines':
        volume, quote, taker, takerquote = map(dec, [raw[5], raw[7], raw[9], raw[10]])
        count = int(raw[8])
        if min(volume, quote, taker, takerquote, count) < 0 or taker > volume or takerquote > quote or (volume == 0 and count != 0):
            raise ValueError('invalid traded volume')
    return dict(symbol=item['symbol'], kind=kind, date=iso(t)[:10], open_time_raw=raw[0], open_time_us=t, open_time_utc=iso(t), timestamp_unit=unit, open=raw[1], high=raw[2], low=raw[3], close=raw[4], volume_field=raw[5], close_time_raw=raw[6], close_time_us=end, close_time_utc=iso(end), bar_declared_seconds=Decimal(end-t)/Decimal(1000000)+Decimal('0.001' if unit == 'milliseconds' else '0.000001'), quote_volume_field=raw[7], count_field=raw[8], taker_buy_volume_field=raw[9], taker_buy_quote_volume_field=raw[10], ignore_field=raw[11], source_url=item['archive_url'], source_line=line, errors=[], volume_semantics='IGNORE (official mark documentation)' if kind == 'markPriceKlines' else 'base/quote traded volume; not order-book capacity')


def normalize(spot_root, futures_root, output):
    sources = json.loads((HERE / 'official_sources.json').read_text())
    manifest = json.loads((HERE / 'inputs.json').read_text())
    if len(sources['archives']) != 199:
        raise ValueError('unexpected frozen archive count')
    if any((output / item['filename']).exists() for item in manifest['files'].values()):
        raise ValueError('refusing to overwrite normalized inputs')
    spot, futures, seen = [], [], set()
    for item in sources['archives']:
        raw = archive_rows(spot_root if item['asset'] == 'spot' else futures_root, item)
        header = bool(raw and raw[0] and not raw[0][0].isdigit())
        if header:
            validate_header(raw.pop(0), item.get('kind', 'spot'))
        if item['asset'] == 'spot' and header:
            raise ValueError('unexpected header in frozen spot archive')
        for index, row in enumerate(raw):
            parsed = parse_row(row, item, index + 2 if header else index + 1)
            key = (item['asset'], parsed['symbol'], parsed['kind'], parsed['open_time_us'])
            if key in seen:
                raise ValueError('duplicate daily source row')
            seen.add(key)
            if item['asset'] == 'spot':
                # Preserve the original frozen spot normalization, including its
                # timestamp float conversion. Integer timestamp fields remain raw.
                divisor = 1000000 if parsed['timestamp_unit'] == 'microseconds' else 1000
                utc = lambda value: datetime.fromtimestamp(int(value)/divisor, timezone.utc).isoformat().replace('+00:00', 'Z')
                spot.append([item['symbol'], utc(row[0]), row[0], *row[1:6], utc(row[6]), *row[6:]])
            elif item['window_start'] <= parsed['date'] <= item['expiry_date']:
                parsed['archive_sha256'] = item['archive_sha256']
                parsed['in_fixed_window'] = True
                futures.append(parsed)
    spot.sort(key=lambda row: (row[0], row[1]))
    futures.sort(key=lambda row: (row['symbol'], row['kind'], row['open_time_us']))
    if len(spot) != 4107 or len(futures) != 1615:
        raise ValueError('unexpected frozen row counts')
    payloads = {}
    for label, values in (('spot_csv', spot), ('fixed_futures_csv', futures)):
        item = manifest['files'][label]
        buffer = io.StringIO(newline='')
        writer = csv.writer(buffer)
        writer.writerow(item['columns_in_order'])
        for row in values:
            if isinstance(row, dict):
                row = [json.dumps(row[k], ensure_ascii=False) if isinstance(row[k], (dict, list)) else row[k] for k in item['columns_in_order']]
            writer.writerow(row)
        payload = buffer.getvalue().encode('utf-8')
        if len(payload) != item['bytes'] or digest(payload) != item['sha256']:
            raise ValueError('normalized byte hash mismatch: ' + item['filename'])
        payloads[item['filename']] = payload
    output.mkdir(parents=True, exist_ok=True)
    for filename, payload in payloads.items():
        (output / filename).write_bytes(payload)
    return {'archive_pairs_verified': 199, 'spot_rows': len(spot), 'fixed_futures_rows': len(futures), 'normalized_sha256': {name: digest(payload) for name, payload in payloads.items()}, 'network_requests': 0}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--spot-archive-dir', type=Path, required=True)
    parser.add_argument('--futures-archive-dir', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(normalize(args.spot_archive_dir, args.futures_archive_dir, args.output_dir), indent=2))
