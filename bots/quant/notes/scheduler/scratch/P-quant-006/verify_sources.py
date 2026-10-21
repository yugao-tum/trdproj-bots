import json, csv, urllib.request, urllib.parse, hashlib, os, re, sys
from collections import Counter
BASE=os.path.dirname(os.path.abspath(__file__))
CACHE=os.path.join(BASE,'_cache')
UA={'User-Agent':'Mozilla/5.0 (research; contact research@example.com)'}
def get(url):
    req=urllib.request.Request(url,headers=UA)
    with urllib.request.urlopen(req,timeout=60) as r:
        b=r.read()
        return r.status, len(b), b, r.headers.get('Last-Modified','')
def save(name,b):
    p=os.path.join(CACHE,name)
    open(p,'wb').write(b)
    return p
urls=[
 ('atp_elo','https://tennisabstract.com/reports/atp_elo_ratings.html'),
 ('wta_elo','https://tennisabstract.com/reports/wta_elo_ratings.html'),
 ('fees','https://docs.polymarket.com/trading/fees'),
 ('gamma_open','https://gamma-api.polymarket.com/events?closed=false&limit=8&tag_slug=tennis&order=startDate&ascending=false'),
 ('gamma_atp_friend','https://gamma-api.polymarket.com/events?slug=atp-friend-geerts-2026-08-25'),
 ('search_tennis','https://gamma-api.polymarket.com/public-search?q=tennis&limit_per_type=5'),
 ('search_cs','https://gamma-api.polymarket.com/public-search?q=Counter-Strike&limit_per_type=3&events_status=active'),
 ('trades','https://data-api.polymarket.com/trades?market=0x5a9641cc6e3a60a0e729493ef4d9fe81d5aacfc06d5c49511248462afe969be9&limit=3'),
 ('clob','https://clob.polymarket.com/prices-history?market=0x5a9641cc6e3a60a0e729493ef4d9fe81d5aacfc06d5c49511248462afe969be9&interval=max'),
 ('archive_repo','https://github.com/Aneeshers/tennis-sackmann-archive'),
 ('archive_atp2026','https://raw.githubusercontent.com/Aneeshers/tennis-sackmann-archive/main/atp/atp_matches_2026.csv'),
 ('sackmann_api','https://api.github.com/repos/JeffSackmann/tennis_atp'),
]
out=[]
for name,u in urls:
    try:
        st,ln,b,lm=get(u)
        save(name+'.bin',b)
        out.append((name,u,st,ln,lm))
    except Exception as e:
        out.append((name,u,'ERR',str(e),''))
for name,u,st,ln,lm in out:
    print(f'{name}\t{st}\t{ln}\t{lm}\t{u}')

# content checks
def txt(name):
    return open(os.path.join(CACHE,name+'.bin'),'rb').read().decode('utf-8','replace')
atp=txt('atp_elo'); wta=txt('wta_elo')
for label,t in [('atp',atp),('wta',wta)]:
    print(label,'last_update', re.findall(r'Last update: ([0-9-]+)',t)[:1], '100pt64','64%' in t)
for p in ['Sinner','2296.9','Alcaraz','2149.8','Hurkacz','1897.8']:
    print('atp_has',p,p in atp)
for p in ['Siegemund','1762.3','Yastremska','1762.2','Hanna Chang','1355.0','Arseneault','1266.4']:
    print('wta_has',p,p in wta)
print('wta_lacasse_present', 'Lacasse' in wta)
fees=txt('fees'); print('fee_formula', 'fee = C × feeRate × p × (1 - p)' in fees, 'sports','0.05' in fees)

# gamma open examples
ev=json.loads(txt('gamma_open'))
for e in ev[:8]:
    print('open_event',e.get('slug'),'closed',e.get('closed'),'markets',len(e.get('markets',[])))
    for m in e.get('markets',[])[:1]:
        print('  mkt',m.get('slug'),m.get('outcomePrices'),m.get('spread'),m.get('liquidity'),m.get('orderMinSize'),m.get('orderPriceMinTickSize'),m.get('feeSchedule'))

ge=json.loads(txt('gamma_atp_friend'))
if isinstance(ge,list): ge=ge[0]
print('friend',ge.get('slug'),'volume',ge.get('volume'),'endDate',ge.get('endDate'),'nmarkets',len(ge.get('markets',[])))
for m in ge.get('markets',[]):
    if m.get('slug')==ge.get('slug'):
        print('winner_market',m.get('slug'),m.get('outcomePrices'),m.get('resolutionSource'))
print('desc_has_50_50','2026, 11:59 PM ET' in (ge.get('description') or ''))
print('desc_has_walkover','walkover' in (ge.get('description') or ''))
print(ge.get('description'))

# data-api and clob
tr=json.loads(txt('trades')); print('trades_n',len(tr), tr[:1])
cl=json.loads(txt('clob')); print('clob',cl)
print('archive_atp2026_bytes', os.path.getsize(os.path.join(CACHE,'archive_atp2026.bin')))
a=open(os.path.join(CACHE,'archive_atp2026.bin'),'rb').read().decode('utf-8','replace').splitlines()
print('archive_rows',len(a)-1,'first',a[1].split(',')[0],'last_tourney',max(r.split(',')[0] for r in a[1:] if r and r[0].isdigit()))

# September closed pagination
rows=[]
for off in range(0,900,100):
    u=f'https://gamma-api.polymarket.com/events?closed=true&tag_slug=tennis&end_date_min=2026-09-01T00:00:00Z&end_date_max=2026-10-01T00:00:00Z&limit=100&offset={off}'
    try:
        st,ln,b,lm=get(u); js=json.loads(b)
        print('sep_page',off,st,len(js))
        rows+=js
    except Exception as e:
        print('sep_page',off,'ERR',e)
seen={}
for e in rows: seen[e.get('slug')]=e
print('sep_unique_events',len(seen))
pref=Counter()
for s in seen:
    pref['itf' if s.startswith('itf-') else 'atp' if s.startswith('atp-') else 'wta' if s.startswith('wta-') else 'us' if s.startswith('us-') else 'other']+=1
print('prefix',dict(pref))
atpwta=[e for s,e in seen.items() if s.startswith(('atp-','wta-'))]
print('atp_wta_events',len(atpwta))
doubles=[e for e in atpwta if 'double' in ((e.get('title') or '')+' '+(e.get('slug') or '')).lower()]
print('doubles',len(doubles),'non_doubles',len(atpwta)-len(doubles))
qual=[e for e in atpwta if 'qualif' in ((e.get('title') or '')+' '+(e.get('slug') or '')).lower()]
print('qualifying',len(qual))
main=[e for e in atpwta if e not in doubles and e not in qual]
print('main_singles',len(main))
print('qual_examples',[ (e.get('slug'),e.get('title')) for e in qual[:3]])
