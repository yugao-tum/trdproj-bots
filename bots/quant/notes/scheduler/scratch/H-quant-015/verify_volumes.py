#!/usr/bin/env python3
"""Verify the source-reported volumes quoted in quant-015 and the GISTEMP header."""
import requests
slugs=['august-2026-temperature-increase-c-20260728155540489',
       'october-2026-temperature-increase-c-20260928t160000000z',
       'january-2025-temperature-increase-c',
       'september-2025-temperature-increase-c']
for s in slugs:
    r=requests.get('https://gamma-api.polymarket.com/events',params={'slug':s},timeout=40)
    d=r.json(); e=d[0] if d else {}
    print(f'{s}\tHTTP {r.status_code}\tvolume={e.get("volume")}\topenInterest={e.get("openInterest")}')
g=requests.get('https://data.giss.nasa.gov/gistemp/tabledata_v4/GLB.Ts+dSST.txt',timeout=40)
for line in g.text.splitlines():
    if 'GHCN-v4' in line:
        print('GISTEMP header:',line.strip()); break
