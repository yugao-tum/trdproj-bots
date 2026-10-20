import pandas as pd, numpy as np, json
m=pd.read_pickle('bots/quant/notes/scheduler/scratch/B21/matched.pkl').dropna(subset=['game_id','elo_p_home']).copy()
def oc(x): return json.loads(x) if isinstance(x,str) else x
def get(r,idx):
    try: return r['pm'][oc(r['outcomes'])[int(idx)]]['price']
    except Exception: return np.nan
m['pm_home']=m.apply(lambda r:get(r,r['home_idx']),axis=1); m['pm_away']=m.apply(lambda r:get(r,1-r['home_idx']),axis=1)
m['y']=np.where(m.home_score>m.away_score,1.0,np.where(m.home_score<m.away_score,0.0,0.5))
m=m.dropna(subset=['pm_home','pm_away']); m['rate']=m['rate'].fillna(0.03)
def signals(thr=0.005, add=0.01, lo=0.1, hi=0.9):
    tr=[]
    for _,r in m.iterrows():
        for side in ['home','away']:
            p=float(r['veg_home']) if side=='home' else 1-float(r['veg_home'])
            px=float(r['pm_home'] if side=='home' else r['pm_away'])
            if not (lo<=px<=hi): continue
            ask=min(.995,px+add); fee=float(r['rate'])*ask*(1-ask)
            if p-ask-fee>thr:
                win=float(r.y if side=='home' else 1-r.y); cost=ask+fee
                tr.append(dict(slug=r.slug,date=r.date,side=side,p=p,pm=px,ask=ask,edge=p-ask-fee,win=win,profit=win-cost,ret=(win-cost)/cost))
    return pd.DataFrame(tr)
for thr in [0.005,0.01]:
    t=signals(thr)
    print('\nthr',thr,'n',len(t),'mean profit',round(t.profit.mean(),4),'mean ret',round(t.ret.mean(),4))
    print(t.groupby(t.date.str[:4]).agg(n=('profit','size'),profit=('profit','mean'),ret=('ret','mean'),wr=('win','mean')).round(3).to_string())
    rng=np.random.default_rng(1); bs=[t.sample(len(t),replace=True,random_state=int(rng.integers(1e9))).profit.mean() for _ in range(5000)]
    print('profit 95% CI',round(np.percentile(bs,2.5),4),round(np.percentile(bs,97.5),4))
    print('side counts',t.side.value_counts().to_dict())
    t.to_csv(f'bots/quant/notes/scheduler/scratch/B21/vegas_thr{int(thr*1000)}.csv',index=False)
