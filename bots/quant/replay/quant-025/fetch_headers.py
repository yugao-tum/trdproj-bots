import json, os, re, requests, datetime, csv
from concurrent.futures import ThreadPoolExecutor
UA={"User-Agent":"Mozilla/5.0 (research)"}
B="https://www.spc.noaa.gov/products/outlook/archive/2026/"
ev=json.load(open('_cache/events_meta.json'))
rows=[]
for r in ev:
    for tag,date in [('1630',r['prev']),('2000',r['prev']),('final',r['next'])]:
        hh='0100' if tag=='final' else tag
        fn=f"_cache/geojson/{date}_{hh}_torn.nolyr.geojson"
        rows.append((tag,date,hh,fn))
def head(x):
    tag,date,hh,fn=x
    u=f"{B}day1otlk_{date}_{hh}_torn.nolyr.geojson"
    last=None
    for attempt in range(3):
        try:
            resp=requests.head(u,headers=UA,timeout=30,allow_redirects=True)
            last=resp
            if resp.status_code==200:
                lm=resp.headers.get('Last-Modified')
                return (tag,date,hh,u,resp.status_code,lm)
        except Exception as e:
            last=e
        import time as _time; _time.sleep(1+attempt)
    if isinstance(last,Exception) or last is None:
        return (tag,date,hh,u,'ERR',str(last))
    return (tag,date,hh,u,last.status_code,last.headers.get('Last-Modified'))
out=[]
with ThreadPoolExecutor(max_workers=6) as ex:
    for x in ex.map(head,rows): out.append(x)
with open('_cache/last_modified.csv','w',newline='') as f:
    w=csv.writer(f); w.writerow(['tag','date','hh','url','status','last_modified']); w.writerows(out)
print('rows',len(out),'status', {s:sum(1 for x in out if x[4]==s) for s in set(x[4] for x in out)})
# compute delays vs ISSUE
def parse_http(s):
    return datetime.datetime.strptime(s,'%a, %d %b %Y %H:%M:%S %Z').replace(tzinfo=datetime.timezone.utc)
delays=[]
for tag,date,hh,url,status,lm in out:
    if not lm or status!=200: continue
    fn=f"_cache/geojson/{date}_{hh}_torn.nolyr.geojson"
    d=json.load(open(fn)); 
    if not d['features']: continue
    issue=d['features'][0]['properties'].get('ISSUE_ISO')
    if not issue: continue
    iss=datetime.datetime.fromisoformat(issue)
    lmdt=parse_http(lm)
    delays.append(((lmdt-iss).total_seconds()/60,tag,date,issue,lm))
print('delay minutes min/median/max',round(min(x[0] for x in delays),1),round(sorted(x[0] for x in delays)[len(delays)//2],1),round(max(x[0] for x in delays),1))
for x in sorted(delays,reverse=True)[:10]: print(x)
