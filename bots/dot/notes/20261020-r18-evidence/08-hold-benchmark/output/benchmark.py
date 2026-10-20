"""Independent fixed-token hold comparator, stdlib only; never requests network."""
import csv, hashlib, json, math
from pathlib import Path
from datetime import datetime, timezone
from decimal import Decimal, getcontext
getcontext().prec=40
D=Decimal
OUT=Path(__file__).resolve().parent
BASE=OUT.parents[3]
CONFIG=BASE/'workers/r18-proposal/04-nav-engine/output/frozen-config.json'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def utc(t): return datetime.fromtimestamp(t,timezone.utc).isoformat()
def drawdown(seq):
    peak=seq[0]; worst=0.
    for v in seq:
        peak=max(peak,v); worst=min(worst,v/peak-1)
    return worst

def run():
    cfg=json.loads(CONFIG.read_text())
    paths=[Path(i['path']) for i in cfg['inputs']]
    for p,i in zip(paths,cfg['inputs']): assert sha(p)==i['sha256']
    prices=[]
    for p in paths[1:]:
        rows=list(csv.DictReader(p.open()))
        prices.append({int(r['timestamp']):D(r['close']) for r in rows if D(r['volume'])>0})
    start=int(datetime(2021,6,16,tzinfo=timezone.utc).timestamp())
    rows=[]
    for r in csv.DictReader(paths[0].open()):
        t=int(r['ts'])
        if t<start: continue
        day=t//86400*86400-86400
        assert day+86400<=t
        p=[a[day] for a in prices] # missing candles fail closed
        b=[D(r['token0_bal']),D(r['token1_bal'])]
        assert r['token0_symbol']=='USDC' and r['token1_symbol']=='USDT'
        rows.append((t,b,D(r['lp_supply']),p))
    first,last=rows[0],rows[-1]
    v0=sum(b*p for b,p in zip(first[1],first[3]))
    years=(last[0]-first[0])/(365.25*86400)
    scenarios=[]
    for c_float in cfg['cost_per_side']:
        c=D(str(c_float)); invest=D(2500)*(1-c)
        q=[invest*b/v0 for b in first[1]]
        assert abs(sum(a*b for a,b in zip(q,first[3]))-invest)<D('1e-30')
        values=[sum(a*b for a,b in zip(q,r[3])) for r in rows]
        terminal=values[-1]*(1-c)
        # Same initial coin composition and capital; fixed coin units, not LP units.
        lp_unadjusted=[invest*(sum(b*p for b,p in zip(r[1],r[3]))/r[2])/(v0/first[2]) for r in rows]
        comparisons=[]
        for de_float in cfg['pending_supply_fraction_entry']:
            for dx_float in cfg['pending_supply_fraction_exit']:
                de,dx=D(str(de_float)),D(str(dx_float))
                lp_terminal=lp_unadjusted[-1]*(1+de)/(1+dx)*(1-c)
                comparisons.append({'entry_pending_fraction':float(de),'exit_pending_fraction':float(dx),'lp_terminal_before_unknown_gas':float(lp_terminal),'lp_minus_hold_usd_before_differential_gas':float(lp_terminal-terminal),'lp_minus_hold_total_capital_return_percentage_points':float((lp_terminal-terminal)/D(5000)*100),'lp_leg_cagr':float(lp_terminal/D(2500))**(1/years)-1,'lp_total_capital_cagr':float((D(2500)+lp_terminal)/D(5000))**(1/years)-1})
        scenarios.append({'cost_per_side':float(c),'initial_token_quantities':{'USDC':str(q[0]),'USDT':str(q[1])},'initial_usd_weights':{'USDC':float(q[0]*first[3][0]/invest),'USDT':float(q[1]*first[3][1]/invest)},'hold_terminal_before_unknown_gas':float(terminal),'hold_leg_return':float(terminal/D(2500)-1),'hold_leg_cagr':float(terminal/D(2500))**(1/years)-1,'hold_total_terminal':float(D(2500)+terminal),'hold_total_capital_cagr':float((D(2500)+terminal)/D(5000))**(1/years)-1,'hold_marked_drawdown_excludes_terminal_costs':drawdown([float(v) for v in values]),'hold_total_capital_marked_drawdown':drawdown([2500+float(v) for v in values]),'lp_zero_pending_marked_drawdown':drawdown([float(v) for v in lp_unadjusted]),'comparisons':comparisons})
    result={'status':'CONDITIONAL historical external-close valuation, not executable backtest or fee alpha','source_hashes':cfg['inputs'],'frozen_engine_config_sha256':sha(CONFIG),'window':{'first_utc':utc(first[0]),'last_utc':utc(last[0]),'years_365_25':years,'pool_observations':len(rows),'usd_candles_used':len(set(r[0]//86400*86400-86400 for r in rows))},'initial_external_usd_prices':list(map(str,first[3])),'terminal_external_usd_prices':list(map(str,last[3])),'scenarios':scenarios,'limitations':['Same initial proportional token holdings, not 50/50 quantities or 50/50 USD invented after results.','No LP dilution applies to passive token holder. Entry/exit pending LP sensitivities are unverified endpoint hypotheses, not a joint historical bound.','LP reference uses balance=reserve entry assumption and unchanged historical price-taker path; not exact funded mint/burn.','Uniform proportional execution cost per side is matched assumption, not observed cash spend. LP-specific vs holding-specific gas unresolved; subtract differential gas from incremental USD.','External daily USD marks use completed prior UTC day only; non-synchronous and not executable same-block quotes.','Donations, swap fees, reserve imbalance and supply effects cannot be separated; incremental rights result is not pure fee alpha.','MDD uses marked values before unknown gas and exit cost; excludes intraday path and actual redemption hazards.','2500 idle cash assumes zero yield and no operational cost. No causal performance claim, independent events or low correlation proof.']}
    (OUT/'benchmark-results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    return result

def tests():
    assert drawdown([100,120,90,130]) == -.25
    # Fixed holdings cannot accrue LP quantity growth; proportional USD allocation preserves budget.
    b=[D(2),D(1)];p=[D('0.8'),D('1.1')];budget=D(2492.5)
    q=[budget*x/sum(x*y for x,y in zip(b,p)) for x in b]
    assert abs(sum(x*y for x,y in zip(q,p))-budget)<D('1e-30')
    assert q[0]/q[1]==2
    assert sum(x*y for x,y in zip(q,[2*z for z in p])) == 2*budget
    assert D(2500)*(1-D('.003'))**2==D('2485.022500')
    assert int(datetime(2021,6,16,tzinfo=timezone.utc).timestamp())//86400*86400-86400==1623715200
    return 5
if __name__=='__main__':
    n=tests(); result=run(); print(json.dumps({'tests':n,'window':result['window'],'scenarios':result['scenarios']},ensure_ascii=False,indent=2))
