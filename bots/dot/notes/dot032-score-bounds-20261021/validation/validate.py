#!/usr/bin/env python3
"""Synthetic offline checks only; no live inputs, network, installs, or trading."""
from fractions import Fraction as F
from itertools import product
from pathlib import Path
import json, random
import numpy as np
from scipy.optimize import linprog

def f(a,b): return max(min(a,b),max(a,b)/3)
def bounds(a,b): return max(a/3,b/3,(a+b)/4),min(a,b)+abs(a-b)/3

def witnesses(a,b):
    if a>=3*b or b>=3*a: low=[(a,b)]
    else:
        x,y=(3*a-b)/8,(3*b-a)/8
        low=[(3*x,x),(y,3*y)]
    m=min(a,b)
    return low,[(m,m),(a-m,b-m)]

endpoint_checks=0
for ai,bi in product(range(51),repeat=2):
    a,b=F(ai,7),F(bi,11)
    for groups,target in zip(witnesses(a,b),bounds(a,b)):
        assert all(x>=0 and y>=0 for x,y in groups)
        assert sum(x for x,y in groups)==a and sum(y for x,y in groups)==b
        assert sum(f(x,y) for x,y in groups)==target
        endpoint_checks+=1
rays=[(a,b) for a,b in product(range(7),repeat=2) if a+b]
mat=np.array(rays,dtype=float).T
cost=np.array([float(f(F(a),F(b))) for a,b in rays])
lp_checks=0
for a,b in product(range(11),repeat=2):
    lo,hi=map(float,bounds(F(a),F(b)))
    for sign,target in ((1,lo),(-1,hi)):
        r=linprog(sign*cost,A_eq=mat,b_eq=[a,b],bounds=(0,None),method='highs')
        assert r.success and abs(sign*r.fun-target)<1e-8,(a,b,r,target)
        lp_checks+=1
rng=random.Random(32021)
random_checks=0
for _ in range(20000):
    groups=[(F(rng.randrange(101),13),F(rng.randrange(101),17)) for _ in range(rng.randrange(1,12))]
    a,b=sum(x for x,y in groups),sum(y for x,y in groups)
    lo,hi=bounds(a,b)
    assert lo<=sum(f(x,y) for x,y in groups)<=hi
    random_checks+=1
discrete=sorted({f(F(1),F(1)),f(F(1),F(0))+f(F(0),F(1))})
assert discrete==[F(2,3),F(1)] and bounds(F(1),F(1))[0]==F(1,2)
q=F(5);lo,hi=bounds(F(0),F(0))
assert q/(q+hi)==q/(q+lo)==1
samples=[(F(1),F(1)),(F(1),F(9))]
mean=sum(q/(q+r) for q,r in samples)/2
pooled=sum(q for q,r in samples)/sum(q+r for q,r in samples)
assert mean==F(3,10) and pooled==F(1,6)
result={'status':'PASS_WITH_SCOPE_RESTRICTIONS','exact_endpoint_checks':endpoint_checks,'lp_extremum_checks':lp_checks,'random_exact_partition_checks':random_checks,'indivisible_atom_counterexample':{'A':1,'B':1,'relaxed_lower':'1/2','attainable':['2/3','1']},'epoch_counterexample':{'samples_q_r':[[1,1],[1,9]],'mean_share':str(mean),'pooled_score_ratio':str(pooled)},'methods':'Fraction arithmetic; scipy linprog HiGHS already installed; seed 32021','inputs':'Synthetic only; official formula independently read from cached official documentation.'}
Path(__file__).with_name('results.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
