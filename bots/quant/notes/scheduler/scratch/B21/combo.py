import pandas as pd, numpy as np, json
m=pd.read_pickle('bots/quant/notes/scheduler/scratch/B21/matched2.pkl').dropna(subset=['game_id','elo_p_home']).copy()
def oc(x): return json.loads(x) if isinstance(x,str) else x
def get(r,idx):
    try: return r['pm'][oc(r['outcomes'])[int(idx)]]['price']
    except Exception: return np.nan
def hidx(r):
    if r['tok_home']==r['home_team']: return 1
    if r['tok_away']==r['home_team']: return 0
    return np.nan
m['home_idx']=m.apply(hidx,axis=1); m['pm_home']=m.apply(lambda r:get(r,r['home_idx']),axis=1); m['pm_away']=m.apply(lambda r:get(r,1-r['home_idx']),axis=1)
m['y']=np.where(m.home_score>m.away_score,1.0,np.where(m.home_score<m.away_score,0.0,0.5)); m=m.dropna(subset=['pm_home','pm_away'])
m['year']=m.date.dt.year; m['fee_rate']=np.where(m.year<=2025,0.0,m['rate'].fillna(0.0))
def bt(thr,add=.01):
    tr=[]
    for _,r in m.iterrows():
        for side in ['home','away']:
            pe=float(r.elo_p_home) if side=='home' else 1-float(r.elo_p_home)
            pv=float(r.veg_home) if side=='home' else 1-float(r.veg_home)
            px=float(r['pm_home'] if side=='home' else r['pm_away'])
            if not (0<px<.95): continue
            ask=min(.995,px+add); fee=float(r.fee_rate)*ask*(1-ask)
            if min(pe,pv)-ask-fee>=thr:
                win=float(r.y if side=='home' else 1-r.y); cost=ask+fee
                tr.append((r.date,r.slug,side,pe,pv,px,ask,fee,win,win-cost,(win-cost)/cost))
    return pd.DataFrame(tr,columns=['date','slug','side','pe','pv','pm','ask','fee','win','profit','ret'])
for thr in [0,.005,.01,.02,.03]:
    t=bt(thr)
    if len(t)==0: print(thr,'none'); continue
    rng=np.random.default_rng(3); bs=[t.sample(len(t),replace=True,random_state=int(rng.integers(1e9))).profit.mean() for _ in range(4000)]
    print(f'combo thr{thr}: n={len(t)} win={t.win.mean():.3f} profit={t.profit.mean():.4f} ret={t.ret.mean():.4f} total={t.profit.sum():.2f} CI=({np.percentile(bs,2.5):.4f},{np.percentile(bs,97.5):.4f})')
    print('  year',t.groupby(t.date.dt.year).profit.agg(['size','mean']).round(3).to_dict())
