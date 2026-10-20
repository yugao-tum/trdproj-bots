import json,pandas as pd,numpy as np,re
D=pd.read_csv('model_out.csv')
coef=json.load(open('model_coef.json'))['b_elo_form']
P=json.load(open('/tmp/opencode/price_raw.json'))
M=json.load(open('/tmp/opencode/matched.json')); by={m['slug']:m for m in M if m.get('match')}
def norm(s):
    s=str(s).strip().lower();s=re.sub(r'[^a-z0-9 ]','',s);s=re.sub(r'\s+',' ',s)
    if s in ('usa','united states','us'): s='united states of america'
    if s in ('emirates','uae'): s='united arab emirates'
    if s=='new guinea': s='papua new guinea'
    if s=='kong': s='hong kong'
    if s=='lanka': s='sri lanka'
    CITY={'hyderabad':'sunrisers hyderabad','rajasthan':'rajasthan royals','chennai':'chennai super kings','mumbai':'mumbai indians','gujarat':'gujarat titans','punjab':'punjab kings','kolkata':'kolkata knight riders','bangalore':'royal challengers bengaluru','delhi':'delhi capitals','lucknow':'lucknow super giants'}
    FULL={'royal challengers bangalore':'royal challengers bengaluru'}
    return FULL.get(s,CITY.get(s,s))
rows=[]
for p in P:
    if not p.get('last'): continue
    m=by.get(p['slug']); f=p['match_file']
    d=D[D.file==f]
    if d.empty: continue
    d=d.iloc[0]
    pmod=float(d.p_elo)  # placeholder recompute below
    X=np.array([1.0,d.elo_diff,d.form_diff]); pmod=float(1/(1+np.exp(-(X@np.array(coef)))))
    outs=p['outs']; last=p['last']
    win=None
    mm=by[p['slug']]
    prices=mm['prices']
    for o,pr in zip(outs,prices):
        if str(pr)=='1': win=o.strip()
    if win is None:
        continue
    # map outcome0 to team1
    t1=norm(mm['match']['team1'])
    pm=[pmod,1-pmod] if norm(outs[0])==t1 else [1-pmod,pmod]
    for i,o in enumerate(outs):
        t=last.get(o) or last.get(o.strip()) or last.get(o+' ')
        if not t: continue
        p_mkt=float(t['price'])
        y=1.0 if norm(o)==norm(win) else 0.0
        rows.append(dict(slug=p['slug'],date=p['date'],match=f,src='ipl' if f in [x for x in []] else ('ipl' if 'ipl' in f.lower() and False else d.src),
            outcome=o.strip(),p_model=pm[i],p_mkt=p_mkt,y=y,ts=t['ts'],start=p['start'],
            p_model_other=pm[1-i],p_mkt_other=float((last.get(outs[1-i]) or {}).get('price',np.nan)),
            n_pre=p['n_pre'],volume=mm.get('volume')))
df=pd.DataFrame(rows)
df['stale_h']=(df.start-df.ts)/3600
# one row per match-outcome (2 per match)
print('rows',len(df),'matches',df.match.nunique())
print('stale hours',df.stale_h.describe().round(2).to_dict())
def ll(y,p): p=np.clip(p,1e-6,1-1e-6); return float(-np.mean(y*np.log(p)+(1-y)*np.log(1-p)))
def brier(y,p): return float(np.mean((p-y)**2))
# use one row per match (outcome0) for model calibration
a=df.sort_values(['match','outcome']).groupby('match').head(1)
print('model ll',ll(a.y,a.p_model),'brier',brier(a.y,a.p_model))
print('market ll',ll(a.y,a.p_mkt),'brier',brier(a.y,a.p_mkt))
print('const ll',ll(a.y,np.full(len(a),a.y.mean())))
print('market vs model ll by src')
for s,g in a.groupby('src'):
    print(s,len(g),'model',round(ll(g.y,g.p_model),4),'market',round(ll(g.y,g.p_mkt),4),'mean mkt',round(g.p_mkt.mean(),3),'winrate',round(g.y.mean(),3))
# calibration bins
a=a.copy();a['bin']=pd.cut(a.p_mkt,[0,.1,.2,.3,.4,.5,.6,.7,.8,.9,1],include_lowest=True)
print(a.groupby('bin',observed=True).agg(n=('y','size'),pm=('p_mkt','mean'),ym=('y','mean'),model=('p_model','mean')).round(3))
# rule: buy side with edge>=0.05, cost fee 0.05*p*(1-p)+half spread
def run(half=0.01,thr=0.05,fee=0.05,side='both'):
    bets=[]
    for _,r in df.iterrows():
        for sgn in ([0,1] if side=='both' else [0]):
            pm=r.p_model if sgn==0 else 1-r.p_model
            pk=r.p_mkt if sgn==0 else 1-r.p_mkt
            yy=r.y if sgn==0 else 1-r.y
            if pm-pk>=thr:
                entry=min(0.999,pk+half)
                f=fee*entry*(1-entry)
                bets.append(dict(match=r.match,slug=r.slug,edge=pm-pk,p=entry,y=yy,net=yy-entry-f,stale=r.stale_h))
    b=pd.DataFrame(bets)
    if b.empty: return b
    # one bet per match? keep all, but report
    return b
for half in [0.01,0.02,0.05]:
    b=run(half=half)
    print(f'half={half} bets={len(b)} matches={b.match.nunique()} netmean={b.net.mean():.4f} total={b.net.sum():.2f} winrate={b.y.mean():.3f} medstale={b.stale.median():.1f}h')
b=run(half=0.01)
print(b.groupby('match').head(1).describe().round(3).to_string())
b.to_csv('bets_1c.csv',index=False);df.to_csv('priced.csv',index=False)
