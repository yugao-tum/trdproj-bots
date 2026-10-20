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
m['home_idx']=m.apply(hidx,axis=1)
m['pm_home']=m.apply(lambda r:get(r,r['home_idx']),axis=1); m['pm_away']=m.apply(lambda r:get(r,1-r['home_idx']),axis=1)
m['y']=np.where(m.home_score>m.away_score,1.0,np.where(m.home_score<m.away_score,0.0,0.5))
m=m.dropna(subset=['pm_home','pm_away']); m['year']=m.date.dt.year
# actual fee: 2024-2025 feesEnabled=false -> 0; 2026 use field; missing -> 0
m['fee_rate']=np.where(m.year<=2025,0.0,m['rate'].fillna(0.0))
print('N',len(m),'by year',m.groupby('year').size().to_dict())
print('fee_rate counts',m.fee_rate.value_counts().to_dict())
print('Brier Elo',round(np.mean((m.elo_p_home-m.y)**2),5),'PM',round(np.mean((m.pm_home-m.y)**2),5),'VEG',round(np.mean((m.veg_home-m.y)**2),5))
def bt(model,thr,add=.01,cap=.95):
    tr=[]
    for _,r in m.iterrows():
        for side in ['home','away']:
            p=float(r[model]) if side=='home' else 1-float(r[model])
            px=float(r['pm_home'] if side=='home' else r['pm_away'])
            if not (0<px<cap): continue
            ask=min(.995,px+add); fee=float(r.fee_rate)*ask*(1-ask)
            if p-ask-fee>=thr:
                win=float(r.y if side=='home' else 1-r.y); cost=ask+fee
                tr.append((r.date,r.slug,side,p,px,ask,fee,p-ask-fee,win,win-cost,(win-cost)/cost))
    return pd.DataFrame(tr,columns=['date','slug','side','p','pm','ask','fee','edge','win','profit','ret'])
for name,thr in [('ELO',.02),('ELO',.05),('VEG',.0),('VEG',.005)]:
    t=bt('elo_p_home' if name=='ELO' else 'veg_home',thr)
    rng=np.random.default_rng(11); bs=[t.sample(len(t),replace=True,random_state=int(rng.integers(1e9))).profit.mean() for _ in range(4000)]
    print(f'{name} {thr}: n={len(t)} win={t.win.mean():.4f} profit={t.profit.mean():.4f} ret={t.ret.mean():.4f} total={t.profit.sum():.2f} CI=({np.percentile(bs,2.5):.4f},{np.percentile(bs,97.5):.4f})')
    print('  year',t.groupby(t.date.dt.year).profit.agg(['size','mean']).round(3).to_dict())
    print('  fee paid total',round(t.fee.sum(),2))
t=bt('elo_p_home',.02); t.to_csv('bots/quant/notes/scheduler/scratch/B21/elo_thr2_trades_actualfees.csv',index=False)
m[['slug','date','game_id','home_team','away_team','home_score','away_score','elo_p_home','veg_home','pm_home','pm_away','fee_rate','y']].to_csv('bots/quant/notes/scheduler/scratch/B21/games_657.csv',index=False)
