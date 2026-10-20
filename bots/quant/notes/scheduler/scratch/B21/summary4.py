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
m['hi']=m.apply(hidx,axis=1); m['ph']=m.apply(lambda r:get(r,r.hi),axis=1); m['pa']=m.apply(lambda r:get(r,1-r.hi),axis=1)
m['y']=np.where(m.home_score>m.away_score,1.0,np.where(m.home_score<m.away_score,0.0,0.5))
m=m.dropna(subset=['ph','pa']); m['year']=m.date.dt.year
m['fee_rate']=np.where(m.year<=2025,0.0,m['rate'].fillna(0.0))
print('N',len(m),'by year',m.groupby('year').size().to_dict(),'ties',int((m.y==0.5).sum()))
print('Brier Elo',round(np.mean((m.elo_p_home-m.y)**2),5),'PM',round(np.mean((m.ph-m.y)**2),5),'VEG',round(np.mean((m.veg_home-m.y)**2),5))
print('MAE Elo-PM',round(np.mean(abs(m.elo_p_home-m.ph)),4),'MAE Veg-PM',round(np.mean(abs(m.veg_home-m.ph)),4))
print('means Elo/PM/Veg/actual',round(m.elo_p_home.mean(),4),round(m.ph.mean(),4),round(m.veg_home.mean(),4),round(m.y.mean(),4))
print('fee counts',m.fee_rate.value_counts().to_dict())
def bt(model,thr,add=.01,cap=.95,df=None):
    df=m if df is None else df; tr=[]
    for _,r in df.iterrows():
        for side in ['home','away']:
            p=float(r[model]) if side=='home' else 1-float(r[model])
            px=float(r['ph'] if side=='home' else r['pa'])
            if not (0<px<cap): continue
            ask=min(.995,px+add); fee=float(r.fee_rate)*ask*(1-ask)
            if p-ask-fee>=thr:
                win=float(r.y if side=='home' else 1-r.y); cost=ask+fee
                tr.append((r.date,r.slug,side,p,px,ask,fee,p-ask-fee,win,win-cost,(win-cost)/cost))
    return pd.DataFrame(tr,columns=['date','slug','side','p','pm','ask','fee','edge','win','profit','ret'])
def report(name,t,label):
    if len(t)==0: print(label,'none'); return
    rng=np.random.default_rng(11); bs=[t.sample(len(t),replace=True,random_state=int(rng.integers(1e9))).profit.mean() for _ in range(4000)]
    print(f'{label}: n={len(t)} win={t.win.mean():.4f} profit={t.profit.mean():.4f} ret={t.ret.mean():.4f} total={t.profit.sum():.2f} CI=({np.percentile(bs,2.5):.4f},{np.percentile(bs,97.5):.4f})')
    print('  year',t.groupby(t.date.dt.year).agg(n=('profit','size'),profit=('profit','mean'),ret=('ret','mean')).round(3).to_dict())
report('ELO',bt('elo_p_home',.02),'ELO thr2 actualfee')
report('ELO',bt('elo_p_home',.05),'ELO thr5 actualfee')
report('VEG',bt('veg_home',0),'VEG thr0 actualfee')
report('VEG',bt('veg_home',.005),'VEG thr.5c actualfee')
sub=m[m.fee_rate>0]
print('fee-bearing games',len(sub),sub.date.min(),sub.date.max())
report('ELO',bt('elo_p_home',.02,df=sub),'ELO thr2 fee-bearing')
for thr in [.03,.05,.08,.10,.12,.15]: report('ELO',bt('elo_p_home',thr,df=sub),f'ELO thr{thr} fee-bearing')
bt('elo_p_home',.02).to_csv('bots/quant/notes/scheduler/scratch/B21/elo_final_trades.csv',index=False)
m[['slug','date','game_id','home_team','away_team','home_score','away_score','elo_p_home','veg_home','ph','pa','fee_rate','y']].to_csv('bots/quant/notes/scheduler/scratch/B21/games_final.csv',index=False)
# uniform 3%
m['fee_rate']=0.03
report('ELO',bt('elo_p_home',.02),'ELO thr2 uniform3%')
bt('elo_p_home',.02).to_csv('bots/quant/notes/scheduler/scratch/B21/elo_final_trades_uniform3.csv',index=False)
