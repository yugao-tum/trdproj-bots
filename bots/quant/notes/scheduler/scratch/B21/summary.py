import pandas as pd, numpy as np, json
m=pd.read_pickle('bots/quant/notes/scheduler/scratch/B21/matched.pkl').dropna(subset=['game_id','elo_p_home']).copy()
def oc(x): return json.loads(x) if isinstance(x,str) else x
def get(r,idx):
    try: return r['pm'][oc(r['outcomes'])[int(idx)]]['price']
    except Exception: return np.nan
m['pm_home']=m.apply(lambda r:get(r,r['home_idx']),axis=1)
m['pm_away']=m.apply(lambda r:get(r,1-r['home_idx']),axis=1)
m['y']=np.where(m.home_score>m.away_score,1.0,np.where(m.home_score<m.away_score,0.0,0.5))
m=m.dropna(subset=['pm_home','pm_away']); m['rate']=m['rate'].fillna(0.03)
print('N',len(m))
print('date range',m.date.min(),m.date.max())
print('by season',m.groupby(m.date.str[:4]).size().to_dict())
print('rate values',m.rate.value_counts().to_dict())
print('ties',int((m.y==0.5).sum()))
print('Brier Elo',round(np.mean((m.elo_p_home-m.y)**2),5))
print('Brier PM ',round(np.mean((m.pm_home-m.y)**2),5))
print('Brier VEG',round(np.mean((m.veg_home-m.y)**2),5))
print('MAE Elo-PM',round(np.mean(abs(m.elo_p_home-m.pm_home)),4))
print('MAE Veg-PM',round(np.mean(abs(m.veg_home-m.pm_home)),4))
print('mean PM home',round(m.pm_home.mean(),4),'mean vegas home',round(m.veg_home.mean(),4),'actual home',round(m.y.mean(),4))
# primary rule
def backtest(model, thr, add=0.01, cap=0.95):
    tr=[]
    for _,r in m.iterrows():
        for side in ['home','away']:
            p=float(r[model]) if side=='home' else 1-float(r[model])
            px=float(r['pm_home'] if side=='home' else r['pm_away'])
            if not (0<px<cap): continue
            ask=min(.995,px+add); fee=float(r.rate)*ask*(1-ask)
            if p-ask-fee>=thr:
                win=float(r.y if side=='home' else 1-r.y); cost=ask+fee
                tr.append((r.date,r.slug,side,p,px,ask,fee,p-ask-fee,win,win-cost,(win-cost)/cost))
    t=pd.DataFrame(tr,columns=['date','slug','side','p','pm','ask','fee','edge','win','profit','ret'])
    return t
for name,thr in [('ELO',0.02),('ELO',0.05),('VEG',0.0),('VEG',0.005),('VEG',0.01)]:
    t=backtest('elo_p_home' if name=='ELO' else 'veg_home',thr)
    rng=np.random.default_rng(7); bs=[t.sample(len(t),replace=True,random_state=int(rng.integers(1e9))).profit.mean() for _ in range(4000)] if len(t) else [np.nan]
    print(f'{name} thr={thr}: n={len(t)} win={t.win.mean():.4f} mean_profit={t.profit.mean():.4f} mean_ret={t.ret.mean():.4f} total={t.profit.sum():.2f} CI=({np.percentile(bs,2.5):.4f},{np.percentile(bs,97.5):.4f})')
    print('   by year',t.groupby(t.date.str[:4]).profit.agg(['size','mean']).round(3).to_dict())
# export
m[['slug','date','game_id','home_team','away_team','home_score','away_score','elo_p_home','veg_home','pm_home','pm_away','rate','y']].to_csv('bots/quant/notes/scheduler/scratch/B21/games_638.csv',index=False)
t=backtest('elo_p_home',0.02); t.to_csv('bots/quant/notes/scheduler/scratch/B21/elo_thr2_trades.csv',index=False)
print('saved games_638.csv rows',len(m))
