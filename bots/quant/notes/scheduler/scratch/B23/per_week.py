import collections
w=collections.defaultdict(lambda:[0,0.0,0.0])
for line in open('actual_pnl.log'):
    p=line.split()
    if not p or p[0] not in ('YES','NO'): continue
    week=p[1]
    cost=float(p[p.index('cost')+1].replace('$',''))
    pnl=float(p[p.index('pnl')+1].replace('$',''))
    w[week][0]+=1; w[week][1]+=cost; w[week][2]+=pnl
print('week n cost pnl roi')
for k in sorted(w):
    print(k,w[k][0],round(w[k][1],4),round(w[k][2],4),round(w[k][2]/w[k][1]*100,2))
print('total',round(sum(v[1] for v in w.values()),4),round(sum(v[2] for v in w.values()),4))
