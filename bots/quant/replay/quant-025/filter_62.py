import json, shutil
p='_cache/events_meta.json'
shutil.copy(p,'_cache/events_meta_all63.json')
ev=json.load(open(p))
ev=[r for r in ev if r['date']<='2026-10-19']
json.dump(ev,open(p,'w'))
print('kept',len(ev),'events',min(r['date'] for r in ev),'..',max(r['date'] for r in ev),'markets',sum(len(r['markets']) for r in ev))
