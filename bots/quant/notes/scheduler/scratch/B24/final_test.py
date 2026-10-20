import pandas as pd,numpy as np,json
P=pd.read_csv('priced.csv')
# one row per match, outcome0/1 aligned
rows=[]
for f,g in P.groupby('match'):
    if len(g)!=2: continue
    g=g.sort_values('outcome')
    a,b=g.iloc[0],g.iloc[1]
    if abs(a.p_mkt+b.p_mkt-1)>0.10: continue
    if a.y==b.y: continue  # 50-50 / non-decisive
    rows.append(dict(match=f,date=a.date,src=a.src,slug=a.slug,
        m0=a.p_model,m1=b.p_model,p0=a.p_mkt,p1=b.p_mkt,y0=a.y,y1=b.y,
        stale=max(a.stale_h,b.stale_h),n_pre=a.n_pre))
M=pd.DataFrame(rows)
print('clean matches',len(M),'of',P.match.nunique())
print('by src',M.groupby('src').size().to_dict(),'by year',M.date.str[:4].value_counts().sort_index().to_dict())
def ll(y,p):
    p=np.clip(p,1e-6,1-1e-6); return float(-np.mean(y*np.log(p)+(1-y)*np.log(1-p)))
def br(y,p): return float(np.mean((p-y)**2))
print('MODEL  ll %.4f brier %.4f'%(ll(M.y0,M.m0),br(M.y0,M.m0)))
print('MARKET ll %.4f brier %.4f'%(ll(M.y0,M.p0),br(M.y0,M.p0)))
print('CONST  ll %.4f'%ll(M.y0,np.full(len(M),M.y0.mean())))
for half in [0.0,0.01,0.02,0.05]:
    bets=[]
    for _,r in M.iterrows():
        best=None
        for i in [0,1]:
            pm=r[f'm{i}'];pk=r[f'p{i}'];yy=r[f'y{i}']
            edge=pm-pk
            if edge>=0.05 and 0.02<=pk<=0.98:
                if best is None or edge>best[0]: best=(edge,i,pk,yy)
        if best:
            edge,i,pk,yy=best
            entry=min(0.999,pk+half); fee=0.05*entry*(1-entry)
            bets.append(dict(match=r.match,date=r.date,src=r.src,slug=r.slug,edge=edge,p=pk,y=yy,net=yy-entry-fee))
    b=pd.DataFrame(bets)
    print('half %.2f bets %d matches %d net/bet %+.4f net/match %+.4f total %+.2f win %.3f'%(half,len(b),b.match.nunique(),b.net.mean(),b.groupby('match').net.sum().mean(),b.net.sum(),b.y.mean()))
    if half==0.01: b.to_csv('bets_final_1c.csv',index=False); print('  by src',b.groupby('src').net.agg(['size','mean']).round(3).to_dict()); print('  by year',b.groupby(b.date.str[:4]).net.agg(['size','mean']).round(3).to_dict())
# post-hoc balanced subset (same rule, only p_mkt in .35-.65)
b=[]
for _,r in M.iterrows():
    best=None
    for i in [0,1]:
        pm=r[f'm{i}'];pk=r[f'p{i}'];yy=r[f'y{i}'];edge=pm-pk
        if edge>=0.05 and 0.35<=pk<=0.65:
            if best is None or edge>best[0]: best=(edge,pk,yy)
    if best:
        edge,pk,yy=best; entry=pk+0.01; fee=0.05*entry*(1-entry)
        b.append(dict(match=r.match,date=r.date,src=r.src,slug=r.slug,edge=edge,p=pk,y=yy,net=yy-entry-fee))
b=pd.DataFrame(b)
print('POSTHOC 0.35-0.65: bets %d matches %d net/bet %+.4f net/match %+.4f total %+.2f win %.3f'%(len(b),b.match.nunique(),b.net.mean(),b.groupby('match').net.sum().mean(),b.net.sum(),b.y.mean()))
print('  by year',b.groupby(b.date.str[:4]).net.agg(['size','mean']).round(3).to_dict())
print('  by src',b.groupby('src').net.agg(['size','mean']).round(3).to_dict())
b.to_csv('bets_posthoc_balanced.csv',index=False)
M.to_csv('clean_matches.csv',index=False)
json.dump({'n_matches':int(len(M)),'model_ll':ll(M.y0,M.m0),'market_ll':ll(M.y0,M.p0),'const_ll':ll(M.y0,np.full(len(M),M.y0.mean())),
  'model_brier':br(M.y0,M.m0),'market_brier':br(M.y0,M.p0)},open('summary.json','w'),indent=1)
