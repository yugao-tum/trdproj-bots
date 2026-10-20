import csv, os, datetime as dt
from collections import defaultdict, Counter
FIPS_STATES=['AL','AZ','AR','CA','CO','CT','DE','FL','GA','ID','IL','IN','IA','KS','KY','LA','ME','MD','MA','MI','MN','MS','MO','MT','NE','NV','NH','NJ','NM','NY','NC','ND','OH','OK','OR','PA','RI','SC','SD','TN','TX','UT','VT','VA','WA','WV','WI','WY']
data={}
for st in FIPS_STATES:
    rows=[]
    with open(f'_cache/usdm/{st}.csv') as f:
        for r in csv.DictReader(f):
            rows.append((r['MapDate'],float(r['D4'])))
    rows.sort()
    data[st]=rows
def bucket(x):
    if x==0: return '0'
    if x<0.05: return '(0,.05)'
    if x<0.25: return '[.05,.25)'
    if x<1: return '[.25,1)'
    if x<5: return '[1,5)'
    return '>=5'
trans=defaultdict(Counter)
n_weeks=Counter()
for st,rows in data.items():
    for i in range(len(rows)-1):
        d0,x=rows[i]; d1,y=rows[i+1]
        # consecutive weekly maps only
        if (dt.date(int(d1[:4]),int(d1[4:6]),int(d1[6:]))-dt.date(int(d0[:4]),int(d0[4:6]),int(d0[6:]))).days!=7:
            continue
        b=bucket(x)
        trans[b][y>=0.05]+=1
        if x>=0.05: trans['ALL'][y>=0.05]+=1
        n_weeks[d0[:4]]+=1
print('week-state transitions',sum(sum(v.values()) for k,v in trans.items() if k!='ALL'))
print('ALL persist if prior>=.05', trans['ALL'][True], trans['ALL'][True]+trans['ALL'][False], trans['ALL'][True]/(trans['ALL'][True]+trans['ALL'][False]))
for b in ['0','(0,.05)','[.05,.25)','[.25,1)','[1,5)','>=5']:
    c=trans[b]; tot=c[True]+c[False]
    if tot: print(f'{b:12s} n {tot:7d} next_D4>=.05 {c[True]:6d} rate {c[True]/tot:.4f}')
# market weeks only
print('\nMarket weeks (2026-08-18..2026-10-13):')
te=defaultdict(Counter)
for st,rows in data.items():
    for i in range(len(rows)-1):
        d0,x=rows[i]; d1,y=rows[i+1]
        if not ('20260818'<=d0<='20261006'): continue
        b=bucket(x); te[b][y>=0.05]+=1
for b in ['0','(0,.05)','[.05,.25)','[.25,1)','[1,5)','>=5']:
    c=te[b]; tot=c[True]+c[False]
    if tot: print(f'{b:12s} n {tot:4d} rate {c[True]/tot:.4f}')
