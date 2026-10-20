import pandas as pd, numpy as np, json

m=pd.read_pickle('bots/quant/notes/scheduler/scratch/B21/matched.pkl')
m=m.dropna(subset=['game_id','elo_p_home']).copy()
def oc(x): return json.loads(x) if isinstance(x,str) else x
def get(r,idx):
    try:
        o=oc(r['outcomes'])[int(idx)]
        return r['pm'][o]['price'], r['pm'][o]['side'], r['pm'][o]['ts']
    except Exception: return np.nan,None,np.nan
h=[get(r,r['home_idx']) for _,r in m.iterrows()]
a=[get(r,1-r['home_idx']) for _,r in m.iterrows()]
m['pm_home']=[x[0] for x in h]; m['pm_away']=[x[0] for x in a]
m['home_win']=np.where(m.home_score>m.away_score,1.0,np.where(m.home_score<m.away_score,0.0,0.5))
m=m.dropna(subset=['pm_home','pm_away'])
m['y']=m.home_win
m['rate']=m['rate'].fillna(0.03)
print('N games',len(m),'dates',m.date.min(),m.date.max())

# metrics
def brier(p,y): return float(np.mean((p-y)**2))
print('Brier Elo     ',round(brier(m.elo_p_home,m.y),5))
print('Brier PM      ',round(brier(m.pm_home,m.y),5))
print('Brier Vega    ',round(brier(m.veg_home,m.y),5))
print('corr Elo/PM   ',round(np.corrcoef(m.elo_p_home,m.pm_home)[0,1],4))
print('mean |Elo-PM| ',round(np.mean(abs(m.elo_p_home-m.pm_home)),4))
print('mean |Vegas-PM|',round(np.mean(abs(m.veg_home-m.pm_home)),4))
print('PM home mean  ',round(m.pm_home.mean(),4),'home win rate',round(m.y.mean(),4))

# pre-registered rule: at T-60, buy side if model p - (last trade + 0.01) - fee >= 0.02
def run(model_col, edge_min=0.02, price_cap=0.95):
    trades=[]
    for _,r in m.iterrows():
        for side in ['home','away']:
            p=float(r[model_col]) if side=='home' else 1-float(r[model_col]); px=float(r['pm_home'] if side=='home' else r['pm_away'])
            if not np.isfinite(px) or px<=0 or px>=price_cap: continue
            ask=min(0.99,px+0.01)
            fee=float(r['rate'])*ask*(1-ask)
            edge=p-ask-fee
            if edge>=edge_min:
                win=float(r.y if side=='home' else 1-r.y)
                cost=ask+fee
                trades.append({'slug':r.slug,'side':side,'p':p,'pm':px,'ask':ask,'fee':fee,
                               'edge':edge,'win':win,'profit':win-cost,'ret':(win-cost)/cost,
                               'date':r.date})
    t=pd.DataFrame(trades)
    if len(t)==0: return {'n':0}
    return {'n':len(t),'winrate':round(t.win.mean(),4),'mean_edge':round(t.edge.mean(),4),
            'mean_profit_per_share':round(t.profit.mean(),4),'mean_ret':round(t.ret.mean(),4),
            'total_profit_per_unit':round(t.profit.sum(),2),'median_ret':round(t.ret.median(),4),
            'pos_share':round((t.profit>0).mean(),4),
            'home_share':round((t.side=='home').mean(),4),'trades':t}

for name,col in [('ELO','elo_p_home'),('VEGAS','veg_home')]:
    for e in [0.01,0.02,0.03,0.05]:
        r=run(col,e)
        print(name,'edge>=',e,r if r['n']==0 else {k:v for k,v in r.items() if k!='trades'})
    r=run(col,0.02)
    if r['n']:
        r['trades'].to_csv(f'bots/quant/notes/scheduler/scratch/B21/trades_{name.lower()}.csv',index=False)

# combined veto: bet only if Elo and Vegas on same side and each edge vs PM positive
trades=[]
for _,r in m.iterrows():
    for side,pcol in [('home','elo_p_home'),('away','elo_p_away')]:
        p=float(r[pcol]); v=float(r['veg_home'] if side=='home' else 1-r['veg_home'])
        px=float(r['pm_home'] if side=='home' else r['pm_away'])
        if not np.isfinite(px) or px<=0 or px>=0.95: continue
        ask=min(0.99,px+0.01); fee=float(r['rate'])*ask*(1-ask)
        if p-ask-fee>=0.02 and v-ask-fee>=0.02:
            win=float(r.y if side=='home' else 1-r.y); cost=ask+fee
            trades.append({'slug':r.slug,'side':side,'p':p,'v':v,'pm':px,'ask':ask,'fee':fee,
                           'edge':p-ask-fee,'win':win,'profit':win-cost,'ret':(win-cost)/cost,'date':r.date})
t=pd.DataFrame(trades)
print('COMBO n',len(t), '' if len(t)==0 else {'winrate':round(t.win.mean(),4),'mean_profit':round(t.profit.mean(),4),'mean_ret':round(t.ret.mean(),4),'total_profit':round(t.profit.sum(),2)})
if len(t): t.to_csv('bots/quant/notes/scheduler/scratch/B21/trades_combo.csv',index=False)
