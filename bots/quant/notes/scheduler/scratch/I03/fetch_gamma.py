import json, urllib.request, time, sys, os
H={'User-Agent':'research/1.0'}
def get(u):
    for a in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(u,headers=H),timeout=60) as f:
                return json.load(f)
        except Exception as e:
            print('retry',u,e,file=sys.stderr); time.sleep(2)
    raise SystemExit('failed '+u)
out=[]
for off in (0,100,200,300,400):
    d=get(f'https://gamma-api.polymarket.com/events?tag_slug=f1&closed=true&limit=100&offset={off}')
    print(off,len(d),file=sys.stderr)
    out.extend(d)
json.dump(out,open('_cache/closed_events.json','w'))
print('rows',len(out),'unique',len({e['id'] for e in out}))
