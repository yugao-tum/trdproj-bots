#!/usr/bin/env python3
"""Offline packaging utility: verified official ZIPs -> frozen normalized CSVs.
No network, installation, extraction to disk, or strategy execution.
"""
import argparse
import csv
import hashlib
import io
import json
from datetime import datetime, timezone
from pathlib import Path
import zipfile

HERE = Path(__file__).resolve().parent

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def utc(seconds):
    return datetime.fromtimestamp(seconds, timezone.utc).isoformat().replace('+00:00', 'Z')

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive-dir', required=True, type=Path)
    parser.add_argument('--output-dir', required=True, type=Path)
    args = parser.parse_args()
    manifest = json.loads((HERE / 'data_provenance.json').read_text())
    sources = {}
    for path in args.archive_dir.resolve().rglob('*.zip'):
        if path.name in sources:
            raise ValueError('ambiguous archive filename: ' + path.name)
        sources[path.name] = path
    rows = {'spot_daily.csv': [], 'funding.csv': []}
    for item in manifest['archives']:
        filename = item['archive_url'].rsplit('/', 1)[1]
        path = sources.get(filename)
        if path is None or digest(path) != item['archive_sha256']:
            raise ValueError('missing or changed official archive: ' + filename)
        checksum = path.with_name(path.name + '.CHECKSUM')
        if not checksum.exists() or checksum.read_text().split()[0] != item['archive_sha256']:
            raise ValueError('missing or changed official checksum: ' + filename)
        with zipfile.ZipFile(path) as archive:
            if archive.namelist() != [item['csv_member']]:
                raise ValueError('unexpected archive member')
            info = archive.getinfo(item['csv_member'])
            if info.file_size != item['csv_uncompressed_bytes'] or info.file_size > 64 * 1024 * 1024:
                raise ValueError('unexpected uncompressed size')
            raw = list(csv.reader(io.StringIO(archive.read(info).decode('utf-8-sig'))))
        if item['asset'] == 'spot':
            for row in raw:
                if len(row) != 12:
                    raise ValueError('spot column count')
                divisor = 1_000_000 if abs(int(row[0])) >= 10**14 else 1000
                rows['spot_daily.csv'].append([item['symbol'], utc(int(row[0])/divisor), row[0], *row[1:6], utc(int(row[6])/divisor), *row[6:]])
        else:
            if raw[0] != ['calc_time', 'funding_interval_hours', 'last_funding_rate']:
                raise ValueError('funding schema')
            for row in raw[1:]:
                if len(row) != 3:
                    raise ValueError('funding column count')
                seconds = int(row[0]) / 1000
                grid = round(seconds / (8 * 3600)) * (8 * 3600)
                jitter = (seconds - grid) * 1000
                if abs(jitter) > 30:
                    raise ValueError('funding jitter exceeds frozen allowance')
                rows['funding.csv'].append([item['symbol'], utc(grid), row[0], utc(seconds), row[1], row[2], str(jitter)])
    output = args.output_dir.resolve()
    if any((output / name).exists() for name in rows):
        raise ValueError('refusing to overwrite normalized inputs')
    # Check all byte hashes in memory before committing either file.
    payloads = {}
    for name, values in rows.items():
        values.sort(key=lambda row: (row[0], row[1]))
        buf = io.StringIO(newline='')
        writer = csv.writer(buf)
        writer.writerow(manifest['normalized_inputs'][name]['schema'])
        writer.writerows(values)
        payload = buf.getvalue().encode('utf-8')
        if hashlib.sha256(payload).hexdigest() != manifest['normalized_inputs'][name]['sha256']:
            raise ValueError('normalized CSV hash mismatch: ' + name)
        payloads[name] = payload
    output.mkdir(parents=True, exist_ok=True)
    for name, payload in payloads.items():
        (output / name).write_bytes(payload)
    print('Verified 234 official archives and reconstructed both frozen CSV hashes')

if __name__ == '__main__':
    main()
