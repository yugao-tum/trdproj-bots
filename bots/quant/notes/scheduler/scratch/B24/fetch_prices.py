import json,requests,time,os,datetime,sys
S=requests.Session();S.headers['User-Agent']='Mozilla/5.0'
M=json.load(open('/tmp/opencode/matched.json'))
M=[m for m in M if m['match']]
# dedupe by cricsheet file, keep highest volume PM market
by={}
for m in M:
    f=m['match']['file']
    if f not in by or (m.get('volume') or 0)>(by[f].get('volume') or 0): by[f]=m
M=list(by.values())
print('unique matches',len(M))
os.makedirs('/tmp/opencode/trades',exist_ok=True)
def epoch(s):
    if not s: return None
    s=str(s).replace(' ','T')
    try:
        d=datetime.datetime.fromisoformat(s.replace('Z','+00:00'))
        if d.tzinfo is None: d=d.replace(tzinfo=datetime.timezone.utc)
        return int(d.timestamp())
    except Exception: return None
out=[]
for i,m in enumerate(M):
    cid=m['cid']; st=epoch(m.get('gameStartTime')) or (epoch(m['date']+'T12:00:00+00'))
    cache=f'/tmp/opencode/trades/{cid}.json'
    if os.path.exists(cache):
        trades=json.load(open(cache))
    else:
        trades=[]; off=0; pages=0
        while pages<10:
            try:
                r=S.get('https://data-api.polymarket.com/trades',params={'market':cid,'limit':1000,'offset':off},timeout=30)
                if r.status_code!=200: break
                d=r.json()
            except Exception as e:
                print('ERR',m['slug'],e); break
            if not d: break
            trades+=d; pages+=1
            if min(t['timestamp'] for t in d) < st: break
            if len(d)<1000: break
            off+=1000
        json.dump(trades,open(cache,'w'))
        time.sleep(0.05)
    pre=[t for t in trades if t['timestamp']<st]
    rec=dict(slug=m['slug'],cid=cid,date=m['date'],start=st,outs=m['outs'],match_file=m['match']['file'],
             n_trades=len(trades),n_pre=len(pre))
    if pre:
        # last trade per outcome (newest pre)
        last={}
        for t in sorted(pre,key=lambda x:x['timestamp']):
            last[t.get('outcome')]=t
        rec['last']={k:{'price':v['price'],'ts':v['timestamp'],'side':v['side'],'size':v['size']} for k,v in last.items()}
    out.append(rec)
    if i%20==0: print(i,m['slug'],len(trades),len(pre),flush=True)
json.dump(out,open('/tmp/opencode/price_raw.json','w'))
print('done',len(out),'with pre',sum(1 for r in out if r['n_pre']>0))
