#!/usr/bin/env python3
import json, os, time, urllib.request, urllib.error
UA={'User-Agent':'Mozilla/5.0'}
CACHE='_cache'
os.makedirs(CACHE, exist_ok=True)

def get(url, timeout=60, tries=4):
    last=None
    for i in range(tries):
        try:
            req=urllib.request.Request(url,headers=UA)
            with urllib.request.urlopen(req,timeout=timeout) as r:
                b=r.read()
                return r.status,b
        except Exception as e:
            last=e; time.sleep(2*(i+1))
    raise last

def save(name,url,timeout=60):
    st,b=get(url,timeout=timeout)
    open(os.path.join(CACHE,name),'wb').write(b)
    print(f'{name}\tHTTP {st}\t{len(b)} bytes\t{url}')
    return b

save('search.json','https://gamma-api.polymarket.com/public-search?q=temperature%20increase&limit_per_type=100&events_status=all')
save('era5.csv','https://sites.ecmwf.int/data/climatepulse/data/series/era5_daily_series_2t_global.csv')
save('gistemp.txt','https://data.giss.nasa.gov/gistemp/tabledata_v4/GLB.Ts+dSST.txt')
save('status.json','https://sites.ecmwf.int/data/climatepulse/status/climpulse_status.json')
save('updates.html','https://data.giss.nasa.gov/gistemp/updates_v4/')
save('sept2026.json','https://gamma-api.polymarket.com/events?slug=september-2026-temperature-increase-c')
save('aug2026.json','https://gamma-api.polymarket.com/events?slug=august-2026-temperature-increase-c-20260728155540489')
ev=json.load(open(os.path.join(CACHE,'search.json')))['events']
print('search events',len(ev))
for e in ev:
    slug=e['slug']
    # always refresh event detail
    save('ev_'+slug+'.json','https://gamma-api.polymarket.com/events?slug='+slug,timeout=45)
