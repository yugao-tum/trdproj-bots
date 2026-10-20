# combine primary YES and NO trades, size at last observed trade size
import json,csv,datetime as dt,math
rows=json.load(open('ask_quotes.json'))
ds=list(csv.DictReader(open('dataset.csv')))
prior={}
for r in ds:
    if r['kind']=='state': prior[(r['week'],r['state'])]=float(r['prior_d4'])
for r in rows: r['prior']=prior.get((r['week'],r['state']))
STATES=['AL','AZ','AR','CA','CO','CT','DE','FL','GA','ID','IL','IN','IA','KS','KY','LA','ME','MD','MA','MI','MN','MS','MO','MT','NE','NV','NH','NJ','NM','NY','NC','ND','OH','OK','OR','PA','RI','SC','SD','TN','TX','UT','VT','VA','WA','WV','WI','WY']
data={}
for st in STATES:
    a=[]
    with open(f'_cache/usdm/{st}.csv') as f:
        for r in csv.DictReader(f): a.append((r['MapDate'],float(r['D4'])))
    a.sort(); data[st]=a
def bucket(x):
    if x==0: return '0'
    if x<0.05: return '(0,.05)'
    if x<0.25: return '[.05,.25)'
    if x<1: return '[.25,1)'
    if x<5: return '[1,5)'
    return '>=5'
trans=[]
for st,a in data.items():
    for i in range(len(a)-1):
        d0,x=a[i]; d1,y=a[i+1]
        if (dt.date(int(d1[:4]),int(d1[4:6]),int(d1[6:]))-dt.date(int(d0[:4]),int(d0[4:6]),int(d0[6:]))).days==7:
            trans.append((d1,bucket(x),y>=0.05))
def pb(b,before):
    sel=[t for t in trans if t[0]<before and t[1]==b]
    return (sum(1 for t in sel if t[2])+1)/(len(sel)+2)
out=[]
for r in rows:
    p=r['prior']
    if p is None: continue
    pd=(dt.date.fromisoformat(r['week'])-dt.timedelta(days=7)).strftime('%Y%m%d')
    if p>=0.05 and r['ask'] is not None and r['ask_age']<=72 and r['ask']<=pb(bucket(p),pd)-0.05:
        fill=r['ask']+0.01; fee=0.05*fill*(1-fill); payoff=1 if r['res'] else 0
        pnl=payoff-fill-fee; shares=r['ask_size']; cost=shares*(fill+fee)
        out.append(('YES',r,shares,cost,shares*pnl,fill,payoff))
    if p==0 and r['bid'] is not None and r['bid_age']<=72:
        noask=1-r['bid']; fill=noask+0.01; fee=0.05*fill*(1-fill)
        if noask<= (1-pb('0',pd))-0.05:
            payoff=0 if r['res'] else 1; pnl=payoff-fill-fee; shares=r['bid_size']; cost=shares*(fill+fee)
            out.append(('NO',r,shares,cost,shares*pnl,fill,payoff))
tot_cost=sum(x[3] for x in out); tot_pnl=sum(x[4] for x in out)
print('n',len(out),'shares',sum(x[2] for x in out),'cost $%.2f'%tot_cost,'pnl $%.2f'%tot_pnl,'ROI %.2f%%'%(100*tot_pnl/tot_cost))
for side,r,sh,cost,pnl,fill,payoff in out:
    print(f'{side} {r["week"]} {r["state"]} shares {sh:.1f} fill {fill:.3f} cost ${cost:.4f} pnl ${pnl:.4f} res {r["res"]}')
