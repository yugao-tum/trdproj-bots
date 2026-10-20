import json,csv,math,datetime,collections
import numpy as np, pandas as pd
rows=list(csv.DictReader(open('matches.csv')))
rows=[r for r in rows if r['gender']=='male']
for r in rows:
    r['date']=r['date'][:10]
rows.sort(key=lambda r:(r['date'],r['file']))
def margin_factor(r):
    if r['by_runs']:
        m=int(r['by_runs']); return 1+0.05*min(m,100)/10.0
    if r['by_wkts']:
        m=int(r['by_wkts']); return 1+0.05*min(m,10)/2.0
    return 1.0
K=20.0
R=collections.defaultdict(lambda:1500.0)
hist=[]
for r in rows:
    t1,t2=r['team1'],r['team2']
    r1,r2=R[t1],R[t2]
    e1=1/(1+10**(-(r1-r2)/400))
    w=r['winner']
    hist.append(dict(file=r['file'],date=r['date'],src=r['src'],team1=t1,team2=t2,winner=w,r1=r1,r2=r2,e1=e1,
                     neutral=r['neutral'],event=r['event'],venue=r['venue'],by_runs=r['by_runs'],by_wkts=r['by_wkts']))
    if w in (t1,t2):
        s=1.0 if w==t1 else 0.0
        R[t1]=r1+K*margin_factor(r)*(s-e1)
        R[t2]=r2-K*margin_factor(r)*(s-e1)
pd.DataFrame(hist).to_csv('ratings.csv',index=False)
print(len(hist))
# pre-2024 calibration of scale
H=pd.DataFrame(hist)
pre=H[H.date<'2024-06-01'].dropna(subset=['winner'])
pre=pre[pre.winner.isin([pre.team1,pre.team2])] if False else pre
pre=pre[pre.apply(lambda x:x.winner in (x.team1,x.team2),axis=1)]
y=(pre.winner==pre.team1).astype(int).values
x=((pre.r1-pre.r2)/400.0).values
# fit logistic a*x+b via IRLS
X=np.column_stack([np.ones(len(x)),x]); b=np.zeros(2)
for _ in range(50):
    p=1/(1+np.exp(-X@b)); W=p*(1-p)+1e-9
    z=X@b+(y-p)/W
    b=np.linalg.solve(X.T@(X*W[:,None]),X.T@(W*z))
print('pre2024 n',len(pre),'coef',b)
# logloss pre
p=1/(1+np.exp(-X@b)); ll=-np.mean(y*np.log(p)+(1-y)*np.log(1-p)); print('pre ll',ll)
json.dump({'b':list(b)},open('calib.json','w'))
