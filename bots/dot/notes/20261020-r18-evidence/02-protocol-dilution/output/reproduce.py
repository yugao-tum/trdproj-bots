#!/usr/bin/env python3
"""Offline integer formula checks, not EVM execution or historical backtest."""
import json, math, random
from pathlib import Path

def pending(S,R0,R1,k,fee_on):
    assert S>0 and min(R0,R1,k)>=0
    r,rl=math.isqrt(R0*R1),math.isqrt(k)
    return S*(r-rl)//(5*r+rl) if fee_on and k and r>rl else 0

def mint_existing(S,R0,R1,B0,B1,k,on):
    assert R0>0 and R1>0 and B0>=R0 and B1>=R1
    m=pending(S,R0,R1,k,on)
    L=min((B0-R0)*(S+m)//R0,(B1-R1)*(S+m)//R1)
    if L<=0: raise ValueError('zero mint reverts')
    return L,S+m+L,(B0*B1 if on else 0),m

def burn(S,R0,R1,B0,B1,L,k,on):
    assert 0<L<=S and min(B0,B1)>=0
    m=pending(S,R0,R1,k,on)
    a,b=L*B0//(S+m),L*B1//(S+m)
    if min(a,b)<=0: raise ValueError('zero burn reverts')
    return a,b,S+m-L,((B0-a)*(B1-b) if on else 0),m

def initial(a,b):
    L=math.isqrt(a*b)-1000
    if L<=0: raise ValueError('initial mint reverts')
    return L,L+1000

def main():
    results=[]
    def ok(name,cond):
        assert cond,name
        results.append({'name':name,'pass':True})
    ok('fee_off_and_zero_kLast_no_pending',pending(10000,2000,2000,1000000,False)==pending(10000,2000,2000,0,True)==0)
    ok('no_root_growth_no_pending',pending(10000,1000,1000,1000000,True)==pending(10000,999,999,1000000,True)==0)
    ok('fee_mint_rounds_down',pending(10000,2000,2000,1000000,True)==909)
    ok('initial_minimum_locked',initial(2000,2000)==(1000,2000))
    try: initial(1000,1000)
    except ValueError: ok('initial_zero_reverts',True)
    else: raise AssertionError('initial zero')
    v=mint_existing(10000,2000,2000,2200,2200,1000000,True)
    ok('entry_uses_post_fee_supply',v==(1090,11999,4840000,909))
    v=burn(10000,2000,2000,2200,2000,1000,1000000,True)
    ok('burn_actual_balances_post_fee_supply',v==(201,183,9909,3632183,909))
    w=burn(10000,2000,2000,2000,2000,1000,1000000,True)
    ok('skim_excess_changes_redemption',v[0]>w[0] and v[1]==w[1])
    off=burn(10000,2000,2000,2000,2000,1000,1000000,False)
    ok('fee_off_clears_kLast_after_burn',off[3]==0)
    # Rational 5/6 bound does not survive floors as a proportional bound on integer payout.
    no_pending=1000*10//10000
    diluted=1000*10//10909
    ok('floor_dust_can_revert_not_5_6_integer_payout',no_pending==1 and diluted==0)
    try: burn(10000,2000,2000,10,10,1000,1000000,True)
    except ValueError: ok('zero_burn_reverts_atomically',True)
    else: raise AssertionError('zero burn')
    rng=random.Random(1802)
    cases=20000
    for _ in range(cases):
        S=rng.randrange(1,10**24); R0=rng.randrange(1,10**18); R1=rng.randrange(1,10**18)
        k=rng.randrange(0,4*R0*R1); on=bool(rng.randrange(2)); L=rng.randrange(1,S+1)
        m=pending(S,R0,R1,k,on); M=(S-1)//5
        assert 5*m<S and m<=M
        for B in (rng.randrange(0,10**20),rng.randrange(0,10**20)):
            A=L*B//(S+m)
            assert L*B//(S+M)<=A<=L*B//S
            assert 5*L*B//(6*S)<=A
    ok('20000_seeded_single_event_integer_bound_cases',True)
    # Two separate triggers compound; one-event bound cannot cap an entire history.
    m1=pending(10**9,10**6,10**6,1,True)
    # A positive tiny mint updates kLast; later reserve growth creates another trigger.
    entry_units=(10**9+m1)//10**6
    after_first=10**9+m1+entry_units
    m2=pending(after_first,10**12,10**12,(10**6+1)**2,True)
    ok('two_trigger_bound_is_not_global',5*(m1+m2)>10**9)
    result={'classification':'synthetic_offline_integer_formula_tests','historical_backtest':False,'evm_execution':False,'model':'OpenAI native agent; exact model ID not exposed','seed':1802,'random_cases':cases,'tests':results,'passed':len(results)}
    Path(__file__).with_name('synthetic-tests.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'passed':len(results),'random_cases':cases}))
if __name__=='__main__': main()
