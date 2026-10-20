import json,re
import pandas as pd, numpy as np

MAP={'was':'WAS','wsh':'WAS','la':'LA','lar':'LA','las':'LV','lv':'LV','lac':'LAC','jax':'JAX','sf':'SF','tb':'TB','ne':'NE','no':'NO','nyg':'NYG','nyj':'NYJ','gb':'GB','kc':'KC'}
def T(x): return MAP.get(x.lower(),x.upper())

# ---- Elo from nflverse games.csv (free, keyless) ----
g=pd.read_csv('bots/quant/notes/scheduler/scratch/B21/_cache/games.csv',low_memory=False)
g=g[(g.season>=2010)&g.away_score.notna()&g.home_score.notna()].copy()
g['dt']=pd.to_datetime(g.gameday)
g=g.sort_values(['dt','game_id']).reset_index(drop=True)
ELO={}; last_season=None; HFA=55.0; K=20.0
pre_h=[]; pre_a=[]
for r in g.itertuples():
    if last_season is not None and r.season!=last_season:
        for k in ELO: ELO[k]=1500+(ELO[k]-1500)*2/3
    last_season=r.season
    h=r.home_team; a=r.away_team
    eh=ELO.get(h,1500.0); ea=ELO.get(a,1500.0)
    pre_h.append(eh); pre_a.append(ea)
    ph=1/(1+10**(-((eh+HFA)-ea)/400))
    ah=1.0 if r.home_score>r.away_score else (0.5 if r.home_score==r.away_score else 0.0)
    mov=abs(r.home_score-r.away_score)
    mult=1.0 if mov<=1 else 1.0+np.log(mov)
    d=K*mult*(ah-ph)
    ELO[h]=eh+d; ELO[a]=ea-d
g['elo_home_pre']=pre_h; g['elo_away_pre']=pre_a
g['elo_p_home']=1/(1+10**(-((g.elo_home_pre+HFA)-g.elo_away_pre)/400))
g['elo_p_away']=1-g.elo_p_home

def am2p(x):
    try: x=float(x)
    except: return np.nan
    if np.isnan(x): return np.nan
    return 100/(x+100) if x>0 else -x/(-x+100)
g['mkt_home']=g.home_moneyline.map(am2p); g['mkt_away']=g.away_moneyline.map(am2p)
g['veg_home']=g.mkt_home/(g.mkt_home+g.mkt_away)
g['date']=g.gameday.astype(str)
g['pair']=g.apply(lambda r:'-'.join(sorted([r.away_team,r.home_team])),axis=1)

# ---- Polymarket T-60 quotes ----
pq=json.load(open('bots/quant/notes/scheduler/scratch/B21/pregame_quotes.json'))
rows=[]
for x in pq:
    if 'last' not in x or len(x['last'])<2: continue
    parts=x['slug'].split('-'); away,home=T(parts[1]),T(parts[2])
    rows.append({'slug':x['slug'],'date':'-'.join(parts[3:6]),'pair':'-'.join(sorted([away,home])),
                 'tok_away':away,'tok_home':home,'cid':x['cid'],'outcomes':x['outcomes'],
                 'resolved':x['prices'],'rate':x['rate'],'pm':x['last']})
p=pd.DataFrame(rows)
m=p.merge(g,on=['date','pair'],how='left',suffixes=('','_n'))
print('polymarket games',len(p),'matched',m.game_id.notna().sum())
print('unmatched',len(m[m.game_id.isna()]),m[m.game_id.isna()][['slug','date','pair']].head(8).to_string())
# determine home outcome label = nflverse home team token, which equals outcome index 1 or 0
def home_side(r):
    if pd.isna(r.home_team): return np.nan
    # slug token order == outcomes order
    if r.tok_home==r.home_team: return 1
    if r.tok_away==r.home_team: return 0
    return np.nan
m['home_idx']=m.apply(home_side,axis=1)
def oc(r):
    o=r.outcomes
    return json.loads(o) if isinstance(o,str) else o
def oprice(r,i):
    try:
        o=oc(r)[i]; return r.pm[o]['price']
    except Exception: return np.nan
m['pm_home']=[oprice(r,r.home_idx) if not pd.isna(r.home_idx) else np.nan for r in m.itertuples()]
m['pm_away']=[oprice(r,1-r.home_idx) if not pd.isna(r.home_idx) else np.nan for r in m.itertuples()]
def oside(r,i):
    try: return r.pm[oc(r)[i]]['side']
    except Exception: return None
m['pm_home_side']=[oside(r,r.home_idx) if not pd.isna(r.home_idx) else None for r in m.itertuples()]
m['home_win']=np.where(m.home_score>m.away_score,1.0,np.where(m.home_score<m.away_score,0.0,0.5))
m.to_pickle('bots/quant/notes/scheduler/scratch/B21/matched.pkl')
print('usable',m.pm_home.notna().sum(),'date range',m.date.min(),m.date.max())
print(m[['slug','game_id','home_team','away_team','elo_p_home','veg_home','pm_home','pm_away','home_win']].dropna().head(8).to_string())
