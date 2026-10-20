import pandas as pd, numpy as np, json
m=pd.read_pickle('bots/quant/notes/scheduler/scratch/B21/matched.pkl').dropna(subset=['game_id','elo_p_home']).copy()
def oc(x): return json.loads(x) if isinstance(x,str) else x
def get(r,idx):
    try:
        o=oc(r['outcomes'])[int(idx)]; return r['pm'][o]['price']
    except Exception: return np.nan
m['pm_home']=m.apply(lambda r:get(r,r['home_idx']),axis=1)
m['pm_away']=m.apply(lambda r:get(r,1-r['home_idx']),axis=1)
m['y']=np.where(m.home_score>m.away_score,1.0,np.where(m.home_score<m.away_score,0.0,0.5))
m=m.dropna(subset=['pm_home','pm_away']); m['rate']=m['rate'].fillna(0.03)
print('N',len(m))
def ev(rows, side='away', add=0.01):
    out=[]
    for _,r in rows.iterrows():
        px=float(r['pm_away'] if side=='away' else r['pm_home'])
        ask=min(.995,px+add); fee=float(r['rate'])*ask*(1-ask)
        win=float(1-r.y if side=='away' else r.y)
        out.append((win-ask-fee, (win-ask-fee)/(ask+fee), ask, win))
    o=np.array(out)
    return dict(n=len(o),win=round(o[:,3].mean(),3),profit=round(o[:,0].mean(),4),ret=round(o[:,1].mean(),4),total=round(o[:,0].sum(),2),med=round(np.median(o[:,1]),3))
for lo,hi in [(0.2,.35),(.35,.5),(.5,.65),(.65,.8),(.2,.8),(.35,.8),(.3,.7)]:
    sub=m[(m.pm_home>lo)&(m.pm_home<=hi)]
    print(f'PMhome({lo},{hi}] n={len(sub)} buy AWAY',ev(sub,'away'))
    print(f'                buy HOME',ev(sub,'home'))
# year split for away in 0.35-0.8
for y in ['2024','2025','2026']:
    sub=m[(m.pm_home>0.35)&(m.pm_home<=0.8)&(m.date.str[:4]==y)]
    print(y,len(sub),ev(sub,'away'))
# bootstrap CI for away 0.35-0.8
sub=m[(m.pm_home>0.35)&(m.pm_home<=0.8)]
rng=np.random.default_rng(0); vals=[]
for _ in range(5000):
    s=sub.sample(len(sub),replace=True,random_state=int(rng.integers(1e9)))
    vals.append((1-s.y-(s.pm_away+0.01)-s.rate*(s.pm_away+0.01)*(1-s.pm_away-0.01)).mean())
print('away 0.35-0.8 profit bootstrap 95%',round(np.percentile(vals,2.5),4),round(np.percentile(vals,97.5),4))
