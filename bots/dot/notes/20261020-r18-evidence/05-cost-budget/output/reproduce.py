#!/usr/bin/env python3
"""Self-authored cost sensitivity, no network/execution integration."""
import json, math
from pathlib import Path
B, IDLE = 2500.0, 2500.0

def evaluate(R, years, c, entry_gas=0., exit_gas=0.):
    assert R > 0 and years > 0 and 0 <= c < 1
    assert 0 <= entry_gas <= B and exit_gas >= 0
    k=(1-c)*R*(1-c)
    end=(B-entry_gas)*k-exit_gas
    return {'gross_factor_R':R, 'years':years, 'each_side_haircut':c,
            'net_factor_before_gas_k':k, 'entry_gas_USD':entry_gas,
            'exit_gas_USD':exit_gas, 'investment_end_USD':end,
            'total_end_USD':IDLE+end,
            'investment_CAGR':(end/B)**(1/years)-1 if end>=0 else None,
            'total_CAGR':((IDLE+end)/(B+IDLE))**(1/years)-1 if IDLE+end>=0 else None}

def budgets(R, years, c):
    k=(1-c)*R*(1-c)
    targets={'break_even':B, 'investment_3pct':B*1.03**years,
             'total_3pct':(B+IDLE)*1.03**years-IDLE,
             'total_8pct':(B+IDLE)*1.08**years-IDLE}
    out={}
    for label,target in targets.items():
        h=B*k-target
        out[label]={'target_investment_terminal_USD':target,
          'signed_terminal_headroom_USD':h,
          'zero_gas_meets_equality_hurdle':h>=0,
          'inequality':'k*G_entry + G_exit <= signed_terminal_headroom_USD',
          'entry_only_max_USD':min(B,h/k) if h>=0 else None,
          'exit_only_max_USD':h if h>=0 else None,
          'allocation_unknown_guaranteed_total_budget_USD':min(B,h/max(k,1)) if h>=0 else None}
    return out

def tests():
    assert evaluate(1,1,0)['total_end_USD']==5000
    x=evaluate(1.1,2,.003,10,20)
    assert abs(x['investment_end_USD']-(2490*.997*1.1*.997-20))<1e-9
    assert abs(x['total_end_USD']-x['investment_end_USD']-2500)<1e-9
    assert budgets(.9,1,0)['break_even']['exit_only_max_USD'] is None
    assert budgets(1,1,0)['break_even']['exit_only_max_USD']==0
    for R in [.9,1,1.1,1.4]:
      for y in [1.,2.8]:
       for c in [0.,.003,.006]:
        z=budgets(R,y,c)
        for item in z.values():
         h=item['signed_terminal_headroom_USD']
         if h>=0:
          ge=item['entry_only_max_USD']
          if ge<B: assert abs(evaluate(R,y,c,ge,0)['investment_end_USD']-item['target_investment_terminal_USD'])<1e-8
          gx=item['exit_only_max_USD']
          assert abs(evaluate(R,y,c,0,gx)['investment_end_USD']-item['target_investment_terminal_USD'])<1e-8
    assert evaluate(1.1,1,.006)['total_end_USD']<evaluate(1.1,1,.003)['total_end_USD']
    return {'status':'PASS','test_scope':'synthetic arithmetic only; no transactions or historical gas verified','grids':24}

if __name__=='__main__':
    p=Path(__file__).parent
    (p/'synthetic-tests.json').write_text(json.dumps(tests(),indent=2)+'\n')
    f=p/'capital-input.json'
    if f.exists():
      inp=json.loads(f.read_text())
      rows=[]
      for s in inp['scenarios']:
        for c in [0.,.003,.006]:
          rows.append({'scenario':s['scenario'],**evaluate(s['R'],inp['years'],c),
                       'budgets':budgets(s['R'],inp['years'],c)})
      (p/'cost-results.json').write_text(json.dumps({'classification':'CONDITIONAL_PRICE_TAKER_SENSITIVITY_NOT_ACTUAL_NET_RETURN','source':inp,'rows':rows},indent=2)+'\n')
