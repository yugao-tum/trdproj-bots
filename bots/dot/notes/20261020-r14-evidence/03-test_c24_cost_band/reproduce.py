#!/usr/bin/env python3
"""Offline paired C24 experiment. No network or trades. Read only frozen inputs."""
import argparse,csv,dataclasses,hashlib,importlib.util,json,sys
from pathlib import Path
from datetime import date
HERE=Path(__file__).resolve().parent

def load_engine(path):
    spec=importlib.util.spec_from_file_location('c24_frozen_engine',path)
    e=importlib.util.module_from_spec(spec);sys.modules[spec.name]=e;spec.loader.exec_module(e)
    return e

def decision(qty,cash,prices,e):
    values={s:qty[s]*prices[s] for s in e.SYMBOLS}
    total=sum(values.values()); assets=cash+total
    target=min(e.POSITION_CAP_USDT,e.TARGET_FRACTION*assets)
    if not any(qty[s]>e.EPS for s in e.SYMBOLS):return 'initial'
    if total>target+e.EPS:return 'position_cap'
    if any(abs(values[s]/assets-target/(3*assets))>0.05+1e-12 for s in e.SYMBOLS):return 'weight_band'
    return 'skip'

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--manifest',default=HERE/'source-manifest.json');args=ap.parse_args()
    manifest=json.loads(Path(args.manifest).read_text()); ins=manifest['inputs']
    for p in ins:
        assert hashlib.sha256(Path(p['path']).read_bytes()).hexdigest()==p['sha256'],p['path']
    e=load_engine(ins[0]['path']); original=e.Portfolio
    bars,dates,quality=e.load_and_precheck(ins[1]['path'])
    frozen=json.loads(Path(ins[2]['path']).read_text())
    comparisons=[];details={};baseline_checks=[]
    for cost in e.COST_RATES:
        variants={}
        for mode in ['baseline','band_5pp']:
            triggers=[]
            class BandPortfolio(original):
                def rebalance(self,day,prices,selected,reason):
                    why=decision(self.qty,self.cash,prices,e)
                    triggers.append({'date':str(day),'decision':why})
                    if why!='skip':super().rebalance(day,prices,selected,reason)
            e.Portfolio=original if mode=='baseline' else BandPortfolio
            sim=e.simulate('C24',bars,dates,cost); daily=sim['daily']; trades=sim['trades']
            snaps,base=e.oos_start_snapshot(daily)
            periods={}
            for name,start,end,nav,state in [('2024',e.SIM_START,date(2024,12,31),5000,e._initial_state()),('oos_2025',e.OOS_START,e.SIM_END,base,snaps),('full',e.SIM_START,e.SIM_END,5000,e._initial_state())]:
                rows=[r for r in daily if start<=r['date']<=end]
                p=e._period_metrics(name,rows,nav,state,trades,sim['episodes'],start,end)
                p['average_risky_holdings_usdt']=sum(r['holdings_close'] for r in rows)/len(rows)
                p['turnover_over_initial_5000']=p['notional_traded_usdt']/5000
                p['gross_mark_pnl_before_costs_usdt']=p['net_pnl_usdt']+p['fees_usdt']
                periods[name]=p
                if mode=='baseline':
                    old=frozen['strategies']['C24']['scenarios'][f'{cost:.3f}']['periods'][name]
                    keys=['net_pnl_usdt','fees_usdt','max_drawdown','notional_traded_usdt','trade_count','start_equity','end_equity']
                    for k in keys:
                        assert abs(old[k]-p[k])<1e-9,(cost,name,k,old[k],p[k])
                    baseline_checks.append({'cost':cost,'period':name,'matched_fields':keys})
            prefix=f'{mode}-{cost:.3f}'
            with (HERE/(prefix+'-daily.csv')).open('w') as f:
                w=csv.DictWriter(f,fieldnames=daily[0].keys());w.writeheader();w.writerows(daily)
            with (HERE/(prefix+'-trades.csv')).open('w') as f:
                tr=[dataclasses.asdict(t) for t in trades];w=csv.DictWriter(f,fieldnames=tr[0].keys());w.writeheader();w.writerows(tr)
            variants[mode]=periods
            details[prefix]={'periods':periods,'triggers':triggers,'episodes':sim['episodes'],'negative_cash':sim['negative_cash_seen'],'negative_qty':sim['negative_qty_seen']}
        for period in ['2024','oos_2025','full']:
            a,b=variants['baseline'][period],variants['band_5pp'][period]
            row={'cost':cost,'period':period}
            for key in ['net_pnl_usdt','fees_usdt','notional_traded_usdt','max_drawdown','average_risky_holdings_usdt','gross_mark_pnl_before_costs_usdt','turnover_over_initial_5000','trade_count']:
                row[key]={'baseline':a[key],'variant':b[key],'delta':b[key]-a[key]}
            row['capital']={'baseline':a['capital_bound_diagnostics'],'variant':b['capital_bound_diagnostics']}
            comparisons.append(row)
    e.Portfolio=original
    out={'stage':'real historical price simulation / retrospective holdout, not real execution','variant_count':1,'cost_cases':2,'genuine_oos':False,'comparisons':comparisons,'details':details,'baseline_exact_field_checks':baseline_checks,'input_quality':quality,'independent_episodes_per_run':1,'recommend_improvement':False}
    (HERE/'results.json').write_text(json.dumps(out,indent=2,default=str))
    for r in comparisons: print(r['cost'],r['period'],'PnL',r['net_pnl_usdt'],'fee',r['fees_usdt'],'MDD',r['max_drawdown'])
if __name__=='__main__':main()
