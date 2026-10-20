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
print('mean PM',round(m.pm_home.mean(),4),'mean Vegas',round(m.veg_home.mean(),4),'actual',round(m.y.mean(),4))
# bias by price bucket
m['bucket']=pd.cut(m.pm_home,[0,.2,.35,.5,.65,.8,1.0])
print(m.groupby('bucket',observed=True).agg(n=('y','size'),pm=('pm_home','mean'),veg=('veg_home','mean'),actual=('y','mean')).round(4).to_string())
# favorite-longshot: home price bins
print('\nPM-Vegas by bucket:', (m.groupby('bucket',observed=True).apply(lambda d: (d.pm_home-d.veg_home).mean(),include_groups=False)).round(4).to_string())
def run(px_col='pm_home', add=0.0, thr=0.0, lo=0.0, hi=1.0, model='veg_home', fee_on=True):
    tr=[]
    for _,r in m.iterrows():
        for side in ['home','away']:
            p=float(r[model]) if side=='home' else 1-float(r[model])
            px=float(r['pm_home'] if side=='home' else r['pm_away'])
            if not np.isfinite(px) or not (lo<=px<=hi): continue
            ask=min(0.995,px+add); fee=float(r['rate'])*ask*(1-ask) if fee_on else 0
            edge=p-ask-fee
            if edge>thr:
                win=float(r.y if side=='home' else 1-r.y); cost=ask+fee
                tr.append((r.slug,side,p,px,ask,fee,edge,win,(win-cost)/cost))
    t=pd.DataFrame(tr,columns=['slug','side','p','pm','ask','fee','edge','win','ret'])
    if len(t)==0: return None
    return dict(n=len(t),win=round(t.win.mean(),3),edge=round(t.edge.mean(),4),profit=round((t.win-t.ask-t.fee).mean(),4),
                ret=round(t.ret.mean(),4),medret=round(t.ret.median(),4),total=round((t.win-t.ask-t.fee).sum(),2))
print('\nVEGAS threshold sweep add=0.01')
for lo,hi in [(0,1),(0.1,0.9),(0.2,0.8),(0.35,0.65)]:
  for thr in [0.0,0.005,0.01,0.015,0.02]:
    print(f'p[{lo},{hi}] thr{thr}',run(add=.01,thr=thr,lo=lo,hi=hi))
print('\nVEGAS add=0')
for thr in [0.0,0.005,0.01,0.015,0.02]: print('thr',thr,run(add=0,thr=thr))
print('\nELO add=.01')
for thr in [0.0,0.02,0.05,0.08]: print('thr',thr,run(add=.01,thr=thr,model='elo_p_home'))
