import json,urllib.request,time
H={'User-Agent':'research/1.0'}
def get(u):
    for a in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(u,headers=H),timeout=60) as f: return json.load(f)
        except Exception as e:
            err=e; time.sleep(1.5*(a+1))
    raise RuntimeError(str(err)+' '+u)
out={}
for s in range(2014,2027):
    d=get(f'https://api.jolpi.ca/ergast/f1/{s}.json')
    rs=d['MRData']['RaceTable']['Races']
    for r in rs:
        out[f'{s}-{r["round"]}']={'date':r.get('date'),'time':r.get('time'),
            'qual_date':(r.get('Qualifying') or {}).get('date'),'qual_time':(r.get('Qualifying') or {}).get('time')}
    print(s,len(rs),sum(1 for r in rs if r.get('Qualifying')),flush=True)
json.dump(out,open('_cache/schedule.json','w'),indent=0)
print('total',len(out))
