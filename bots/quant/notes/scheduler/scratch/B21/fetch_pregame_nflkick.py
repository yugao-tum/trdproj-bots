import json,re,datetime,sys
import requests
from concurrent.futures import ThreadPoolExecutor

EV='bots/quant/notes/scheduler/scratch/B21/_cache/nfl_events_all.json'
OUT='bots/quant/notes/scheduler/scratch/B21/pregame_quotes.json'
S=requests.Session(); S.headers['User-Agent']='Mozilla/5.0 (research; quant bot)'

ev=json.load(open(EV))
try:
    KM=json.load(open('bots/quant/notes/scheduler/scratch/B21/kick_map.json'))
except Exception:
    KM={}
games=[]
for e in ev:
    if not re.fullmatch(r'nfl-[a-z]{2,3}-[a-z]{2,3}-\d{4}-\d{2}-\d{2}',e['slug']): continue
    m=next((x for x in e.get('markets',[]) if x['slug']==e['slug']),None)
    if not m or not m.get('conditionId'): continue
    st=e.get('startTime') or m.get('gameStartTime') or e.get('endDate')
    if not st: continue
    kick=KM.get(e['slug']) or datetime.datetime.fromisoformat(st.replace('Z','+00:00')).timestamp()
    games.append({'slug':e['slug'],'cid':m['conditionId'],'kick':kick,
                  'outcomes':m.get('outcomes'),'prices':m.get('outcomePrices'),
                  'volume':m.get('volume'),'rate':(m.get('feeSchedule') or {}).get('rate')})
print('games',len(games),file=sys.stderr)

def one(g):
    kick=g['kick']
    # 60 minutes before kickoff
    p={'market':g['cid'],'limit':60,'end':int(kick-3600)}
    try:
        r=S.get('https://data-api.polymarket.com/trades',params=p,timeout=30)
        d=r.json() if r.status_code==200 else []
    except Exception as ex:
        return {'slug':g['slug'],'err':str(ex)}
    last={}
    for t in d:
        o=t.get('outcome')
        if o not in last: last[o]={'price':t['price'],'side':t['side'],'ts':t['timestamp'],'size':t['size']}
    return {**g,'last':last}

with ThreadPoolExecutor(max_workers=8) as ex:
    res=list(ex.map(one,games))
ok=[x for x in res if 'last' in x]
print('fetched',len(ok),'errors',len(res)-len(ok),file=sys.stderr)
json.dump(res,open(OUT,'w'))
print('with quotes',sum(1 for x in ok if len(x.get('last',{}))>=2),file=sys.stderr)
