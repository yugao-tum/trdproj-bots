import json,re
import pandas as pd, numpy as np
MAP={'was':'WAS','wsh':'WAS','la':'LA','lar':'LA','las':'LV','lv':'LV','lac':'LAC','jax':'JAX','sf':'SF','tb':'TB','ne':'NE','no':'NO','nyg':'NYG','nyj':'NYJ','gb':'GB','kc':'KC'}
def T(x): return MAP.get(x.lower(),x.upper())
g=pd.read_csv('bots/quant/notes/scheduler/scratch/B21/_cache/games.csv',low_memory=False)
g=g[(g.season>=2010)&g.away_score.notna()&g.home_score.notna()].copy()
g['dt']=pd.to_datetime(g.gameday); g=g.sort_values(['dt','game_id']).reset_index(drop=True)
ELO={}; last_season=None; HFA=55.0; K=20.0; pre_h=[]; pre_a=[]
for r in g.itertuples():
    if last_season is not None and r.season!=last_season:
        for k in ELO: ELO[k]=1500+(ELO[k]-1500)*2/3
    last_season=r.season; h=r.home_team; a=r.away_team
    eh=ELO.get(h,1500.0); ea=ELO.get(a,1500.0); pre_h.append(eh); pre_a.append(ea)
    ph=1/(1+10**(-((eh+HFA)-ea)/400)); ah=1.0 if r.home_score>r.away_score else (0.5 if r.home_score==r.away_score else 0.0)
    mov=abs(r.home_score-r.away_score); mult=1.0 if mov<=1 else 1.0+np.log(mov); d=K*mult*(ah-ph)
    ELO[h]=eh+d; ELO[a]=ea-d
g['elo_home_pre']=pre_h; g['elo_away_pre']=pre_a; g['elo_p_home']=1/(1+10**(-((g.elo_home_pre+HFA)-g.elo_away_pre)/400))
def am2p(x):
    try: x=float(x)
    except: return np.nan
    return 100/(x+100) if x>0 else (-x/(-x+100) if x<0 else np.nan)
g['mkt_home']=g.home_moneyline.map(am2p); g['mkt_away']=g.away_moneyline.map(am2p); g['veg_home']=g.mkt_home/(g.mkt_home+g.mkt_away)
g['date']=pd.to_datetime(g.gameday); g['pair']=g.apply(lambda r:'-'.join(sorted([r.away_team,r.home_team])),axis=1)
pq=json.load(open('bots/quant/notes/scheduler/scratch/B21/pregame_quotes.json')); rows=[]
for x in pq:
    if 'last' not in x or len(x['last'])<2: continue
    parts=x['slug'].split('-'); away,home=T(parts[1]),T(parts[2])
    rows.append({'slug':x['slug'],'date':pd.to_datetime('-'.join(parts[3:6])),'pair':'-'.join(sorted([away,home])),
                 'tok_away':away,'tok_home':home,'cid':x['cid'],'outcomes':x['outcomes'],'resolved':x['prices'],'rate':x['rate'],'pm':x['last']})
p=pd.DataFrame(rows); p['date']=pd.to_datetime(p['date'])
# merge on pair, then date within 1 day
m=p.merge(g,on='pair',how='left',suffixes=('','_n'))
m['dd']=(m.date-m.date_n).abs().dt.days
m=m[(m.dd<=1)|m.game_id.isna()].drop_duplicates(subset=['slug','game_id'])
# if multiple within 1 day keep closest
m['_rank']=m.groupby('slug')['dd'].rank(method='first')
m=m[(m._rank==1)|m.game_id.isna()].drop(columns=['_rank'])
print('pm',len(p),'matched',m.game_id.notna().sum(),'unique',m[m.game_id.notna()].slug.nunique())
print('unmatched',m.game_id.isna().sum(),m[m.game_id.isna()].groupby(m.date.dt.year).size().to_dict())
m.to_pickle('bots/quant/notes/scheduler/scratch/B21/matched2.pkl')
