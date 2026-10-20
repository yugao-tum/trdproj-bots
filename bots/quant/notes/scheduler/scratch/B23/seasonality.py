import csv, datetime as dt
from collections import defaultdict
STATES=['AL','AZ','AR','CA','CO','CT','DE','FL','GA','ID','IL','IN','IA','KS','KY','LA','ME','MD','MA','MI','MN','MS','MO','MT','NE','NV','NH','NJ','NM','NY','NC','ND','OH','OK','OR','PA','RI','SC','SD','TN','TX','UT','VT','VA','WA','WV','WI','WY']
m=defaultdict(lambda:[0,0])
for st in STATES:
    a=[]
    with open(f'_cache/usdm/{st}.csv') as f:
        for r in csv.DictReader(f): a.append((r['MapDate'],float(r['D4'])))
    a.sort()
    for i in range(len(a)-1):
        d0,x=a[i]; d1,y=a[i+1]
        if (dt.date(int(d1[:4]),int(d1[4:6]),int(d1[6:]))-dt.date(int(d0[:4]),int(d0[4:6]),int(d0[6:]))).days!=7: continue
        if x==0:
            m[int(d1[4:6])][0]+=1; m[int(d1[4:6])][1]+= (y>=0.05)
print('month n k rate')
for k in sorted(m): print(k, m[k][0], m[k][1], round(m[k][1]/m[k][0],4))
print('min/max rate', min(m[k][1]/m[k][0] for k in m), max(m[k][1]/m[k][0] for k in m))
