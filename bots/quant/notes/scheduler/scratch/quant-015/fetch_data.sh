#!/bin/sh
# Re-fetch the four live sources used by quant-015 (no keys, no login).
set -e
mkdir -p _cache
UA='Mozilla/5.0'
curl -sS -L --retry 4 --retry-all-errors --max-time 60 -A "$UA" \
  -o _cache/era5.csv \
  https://sites.ecmwf.int/data/climatepulse/data/series/era5_daily_series_2t_global.csv
curl -sS -L --retry 4 --retry-all-errors --max-time 30 -A "$UA" \
  -o _cache/gistemp.txt \
  https://data.giss.nasa.gov/gistemp/tabledata_v4/GLB.Ts+dSST.txt
curl -sS -L --retry 3 --retry-all-errors --max-time 30 -A "$UA" \
  -o _cache/status.json \
  https://sites.ecmwf.int/data/climatepulse/status/climpulse_status.json
curl -sS -L --retry 3 --retry-all-errors --max-time 30 -A "$UA" \
  -o _cache/sept2026.json \
  'https://gamma-api.polymarket.com/events?slug=september-2026-temperature-increase-c'
curl -sS -L --retry 3 --retry-all-errors --max-time 30 -A "$UA" \
  -o _cache/aug2026.json \
  'https://gamma-api.polymarket.com/events?slug=august-2026-temperature-increase-c-20260728155540489'
curl -sS -L --retry 3 --retry-all-errors --max-time 60 -A "$UA" \
  -o _cache/search.json \
  'https://gamma-api.polymarket.com/public-search?q=temperature%20increase&limit_per_type=100&events_status=all'
curl -sS -L --retry 4 --retry-all-errors --max-time 60 -A "$UA" \
  -o _cache/cdx.json \
  'https://web.archive.org/cdx/search/cdx?url=data.giss.nasa.gov%2Fgistemp%2Ftabledata_v4%2FGLB.Ts%2BdSST.txt&from=1999&to=2026&output=json&filter=statuscode%3A200&collapse=timestamp%3A6'
curl -sS -L --retry 3 --retry-all-errors --max-time 30 -A "$UA" \
  -o _cache/updates.html https://data.giss.nasa.gov/gistemp/updates_v4/
