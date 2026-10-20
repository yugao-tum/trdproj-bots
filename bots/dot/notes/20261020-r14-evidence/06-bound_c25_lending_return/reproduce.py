"""Offline Decimal bound. Inputs are standalone; no credentials, network or trading."""
import json
from decimal import Decimal as D, getcontext
from pathlib import Path
getcontext().prec = 70
ROOT = Path(__file__).resolve().parent

def calculate(c):
    f = D(c['end_index']) / D(c['start_index'])
    t, cap = D(c['total_capital']), D(c['venue_cap'])
    ci, co = D(c['entry_cost_fraction']), D(c['exit_cost_fraction'])
    # B is the total initial cash allocated to entry, INCLUDING entry friction.
    # D0 = B*(1-ci), terminal gross venue balance D1 = D0*f.
    q = (1-ci)*f*(1-co)-1
    b_endpoint_cap = min(cap, cap / ((1-ci)*f))
    def row(b,g):
        d0=b*(1-ci); d1=d0*f; cash=d1*(1-co); pnl=cash-b-g
        return {'initial_cash_budget':str(b),'entry_cost':str(b*ci),'deposited_units':str(d0),'terminal_venue_units':str(d1),'exit_cost':str(d1*co),'gas_assumption':str(g),'conditional_net_interest_cash':str(pnl),'allocated_cash_return_pct':str(pnl/b*100),'total_capital_return_pct':str(pnl/t*100),'terminal_cap_pass':d1<=cap}
    return {'classification':c['classification'],'gross_index_pct':str((f-1)*100),'zero_cost_total_capital_pct':str(cap/t*(f-1)*100),'net_leg_pct_at_zero_gas':str(q*100),'net_total_pct_loose_cap':str(cap/t*q*100),'endpoint_cap_initial_budget':str(b_endpoint_cap),'endpoint_cap_case':row(b_endpoint_cap,D(0)),'required_gross_pct_for_leg_3':str(((1+D('.03'))/((1-ci)*(1-co))-1)*100),'required_gross_pct_for_total_3_at_half_cap':str(((1+D('.03')*t/cap)/((1-ci)*(1-co))-1)*100),'required_gross_pct_for_total_8_at_half_cap':str(((1+D('.08')*t/cap)/((1-ci)*(1-co))-1)*100),'gas_break_even_loose_cap':str(cap*q),'gas_sensitivity':[row(cap,D(g)) for g in c['gas_scenarios']],'capital_sensitivity':[row(D(b),D(0)) for b in c['capital_scenarios']],'new_mechanisms':0,'real_strategy_backtests':0,'qualifying_results':0}

if __name__ == '__main__':
    print(json.dumps(calculate(json.loads((ROOT/'fixed-inputs.json').read_text())),indent=2))
