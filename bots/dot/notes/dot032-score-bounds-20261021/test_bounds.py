"""Offline exact-rational synthetic checks. No network, market data or strategy."""
from fractions import Fraction as F
from itertools import product
import json
from pathlib import Path
import random

def f(a,b): return max(min(a,b),a/F(3),b/F(3))
def bounds(a,b): return max(a/F(3),b/F(3),(a+b)/F(4)), min(a,b)+abs(a-b)/F(3)
def lo_partition(a,b):
    if a>=3*b or b>=3*a: return [(a,b)]
    t,z=(3*a-b)/F(8),(3*b-a)/F(8)
    return [(3*t,t),(z,3*z)]
def hi_partition(a,b):
    return [(min(a,b),min(a,b)),(max(a-b,0),max(b-a,0))]
def check_partition(p):
    a,b=map(sum,zip(*p)); d=sum(f(x,y) for x,y in p)
    lo,hi=bounds(a,b)
    assert lo<=d<=hi,(p,lo,d,hi)
    assert 0<=sum(min(x,y) for x,y in p)<=min(a,b)
    return a,b,d

pointwise=0
for a,b in product(map(F,range(101)),repeat=2):
    lo,hi=bounds(a,b)
    for part,target in [(lo_partition(a,b),lo),(hi_partition(a,b),hi)]:
        aa,bb,dd=check_partition(part)
        assert (aa,bb)==(a,b) and dd==target
    pointwise+=1
random.seed(320032)
for _ in range(20000):
    p=[(F(random.randrange(1001),random.randrange(1,21)),F(random.randrange(1001),random.randrange(1,21))) for __ in range(random.randrange(1,16))]
    check_partition(p)

# Exhaust all two-maker integer score tuples in a small box.
for tup in product(range(11),repeat=4):
    check_partition([(F(tup[0]),F(tup[1])),(F(tup[2]),F(tup[3]))])

# Fixed eligible order atoms: scores 75,25 on each side; threshold 100 shares,
# weight 1/4 corresponds to sizes 300,100, both eligible. Same atoms, two groupings.
a=b=F(100)
assert sum(f(x,y) for x,y in [(F(75),F(25)),(F(25),F(75))])==50
assert f(a,b)==100
assert bounds(F(300),F(100))==(F(100),F(500,3))
q=f(F(30),F(30)); lo,hi=bounds(a,b)
assert (q/(q+hi),q/(q+lo))==(F(3,13),F(3,8))
q=f(F(30),F(0))
assert (q/(q+hi),q/(q+lo))==(F(1,11),F(1,6))
# Raw level score 100 cannot certify positive eligible lower denominator.
assert bounds(a,b)[0]>0 and sum(f(x,y) for x,y in [(F(0),F(0))])==0
# Mean-of-ratios != ratio-of-sums.
assert (F(1,2)+F(1,10))/2==F(3,10)
assert F(1+1,2+10)==F(1,6)
result={"status":"PASS","arithmetic":"exact fractions","endpoint_total_pairs":pointwise,
        "random_partitions":20000,"exhaustive_two_maker_tuples":11**4,
        "seed":320032,"market_data":False,"network_calls":0,
        "balanced_denominator_bounds":["50","100"],
        "balanced_own30_share_bounds":["3/13","3/8"],
        "interpretation":"Tests check arithmetic/constructions; analytic proof establishes universal result. No live eligibility, sample, cash or profit assertion."}
Path(__file__).with_name('TEST-RESULTS.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
