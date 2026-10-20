import pandas as pd,numpy as np,json,collections
R=pd.read_csv('ratings.csv'); B=pd.read_csv('ballstats.csv')
df=R.merge(B[['file','rr1','rr2']],on='file',how='left')
df=df.sort_values(['date','file']).reset_index(drop=True)
HL=365.0
state={}  # team -> [ewm value, last_date_ord]
forms=[]
for i,r in df.iterrows():
    d=pd.Timestamp(r['date']).toordinal()
    f1=state.get(r.team1,[0.0,None]); f2=state.get(r.team2,[0.0,None])
    def decay(f):
        if f[1] is None: return 0.0
        return f[0]*(0.5**((d-f[1])/HL))
    forms.append((decay(f1),decay(f2)))
    if pd.notna(r['rr1']) and pd.notna(r['rr2']):
        diff=float(r['rr1'])-float(r['rr2'])
        for team,own,opp,cur in [(r.team1,r['rr1'],r['rr2'],f1),(r.team2,r['rr2'],r['rr1'],f2)]:
            v=decay(cur)*0.5**(1/HL)*0  # placeholder not used
    # update with decayed values toward current match diff
    if pd.notna(r['rr1']) and pd.notna(r['rr2']):
        for team,diff in [(r.team1,float(r['rr1'])-float(r['rr2'])),(r.team2,float(r['rr2'])-float(r['rr1']))]:
            old=state.get(team,[0.0,None]); od=decay(old)
            state[team]=[od+ (1-0.5**(1/HL))*diff, d]
df['form1']=[x[0] for x in forms]; df['form2']=[x[1] for x in forms]
df['elo_diff']=(df.r1-df.r2)/400.0
df['form_diff']=df.form1-df.form2
df=df[df.winner.isin([df.team1.iloc[0],df.team2.iloc[0]])] if False else df
df=df[df.apply(lambda x:x.winner in (x.team1,x.team2),axis=1)].copy()
df['y']=(df.winner==df.team1).astype(int)
train=df[df.date<'2024-06-01']; test=df[(df.date>='2024-06-01')&(df.date<'2026-06-01')]
def fit(cols,tr):
    X=np.column_stack([np.ones(len(tr))]+[tr[c].values for c in cols]); y=tr.y.values; b=np.zeros(X.shape[1])
    for _ in range(60):
        p=1/(1+np.exp(-X@b)); W=p*(1-p)+1e-9; z=X@b+(y-p)/W
        b=np.linalg.solve(X.T@(X*W[:,None]),X.T@(W*z))
    return b
def ev(b,cols,te):
    X=np.column_stack([np.ones(len(te))]+[te[c].values for c in cols]); p=1/(1+np.exp(-X@b)); y=te.y.values
    p=np.clip(p,1e-6,1-1e-6)
    ll=-np.mean(y*np.log(p)+(1-y)*np.log(1-p)); br=np.mean((p-y)**2)
    return ll,br,p
print('train',len(train),'test',len(test))
for cols in [['elo_diff'],['elo_diff','form_diff']]:
    b=fit(cols,train); ll,br,_=ev(b,cols,test)
    print(cols,'coef',np.round(b,4),'test ll',round(ll,4),'brier',round(br,4))
# constant
p0=train.y.mean(); ll=-np.mean(test.y*np.log(p0)+(1-test.y)*np.log(1-p0));print('const',p0,ll)
# elo-only out of sample by source
b=fit(['elo_diff'],train); _,_,p=ev(b,['elo_diff'],test)
test=test.copy(); test['p_elo']=p
print(test.groupby('src').apply(lambda g: pd.Series({'n':len(g),'ll':-np.mean(g.y*np.log(g.p_elo)+(1-g.y)*np.log(1-g.p_elo))})))
df['p_elo']=1/(1+np.exp(-(fit(['elo_diff'],train)[0]+fit(['elo_diff'],train)[1]*df.elo_diff)))
df[['file','date','src','team1','team2','winner','r1','r2','elo_diff','form1','form2','form_diff','y','p_elo']].to_csv('model_out.csv',index=False)
json.dump({'b_elo_form':list(fit(['elo_diff','form_diff'],train)),'b_elo':list(fit(['elo_diff'],train))},open('model_coef.json','w'))
print('coef elo',fit(['elo_diff'],train),'elo+form',fit(['elo_diff','form_diff'],train))
