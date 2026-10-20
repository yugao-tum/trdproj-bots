import pandas as pd, json
from datetime import datetime
from zoneinfo import ZoneInfo
m=pd.read_pickle('bots/quant/notes/scheduler/scratch/B21/matched2.pkl')
mp={}
for _,r in m.iterrows():
    try:
        hh,mm=map(int,str(r.gametime).split(':')[:2])
        mp[r.slug]=datetime(r.date_n.year,r.date_n.month,r.date_n.day,hh,mm,tzinfo=ZoneInfo('America/New_York')).timestamp()
    except Exception:
        pass
json.dump(mp,open('bots/quant/notes/scheduler/scratch/B21/kick_map.json','w'))
print('mapped',len(mp))
