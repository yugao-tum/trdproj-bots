#!/usr/bin/env python3
"""H-quant-015 follow-up: out-of-sample split + strict freshness / wider-spread
sensitivity for the 29 closed-month tradable-price backtest.

Reuses the exact model and fill-selection code in backtest_015.py. No parameter
is fitted on the 29 market months; the temporal split below is therefore an
OOS *reporting* split, not a refit.
"""
import csv, json, math, os, random, statistics as st
import backtest_015 as bt

D=os.path.dirname(os.path.abspath(__file__)); os.chdir(D)

def sign_p(k,n):
    k=min(k,n-k)
    return min(1.0,2*sum(math.comb(n,i) for i in range(k+1))/2**n) if n else None

def boot_ci(vals,seed=20261021):
    rng=random.Random(seed); means=[]
    for _ in range(2000):
        s=[vals[rng.randrange(len(vals))] for _ in vals]
        means.append(sum(s)/len(s))
    means.sort(); return means[50],means[1949]

def summarize(rows,title):
    paired=[r for r in rows if r['market_ll'] is not None]
    trades=[tr for r in rows for tr in r['trades']]
    monthly=[]
    for r in rows:
        trs=r['trades']
        if not trs: monthly.append(0.0); continue
        alloc=min(200.0,400.0/len(trs))
        monthly.append(sum(alloc*tr['net']/tr['ask'] for tr in trs))
    mb=sum(r['model_ll']<r['market_ll'] for r in paired)
    mktb=sum(r['market_ll']<r['model_ll'] for r in paired)
    print('='*100); print(title)
    print(f"months={len(rows)} paired={len(paired)} trades={len(trades)} hit={sum(t['won'] for t in trades)}")
    if paired:
        print(f"model_ll={sum(r['model_ll'] for r in paired)/len(paired):.6f} "
              f"market_ll={sum(r['market_ll'] for r in paired)/len(paired):.6f} "
              f"model_better={mb} market_better={mktb} sign_p={sign_p(mb,mb+mktb):.6f}")
    if trades:
        net=sum(t['net'] for t in trades); stake=sum(t['ask'] for t in trades)
        print(f"net/share={net:+.6f} stake={stake:.6f} return_on_stake={net/stake:+.2%} "
              f"median_net={st.median(t['net'] for t in trades):+.6f} "
              f"median_fill_age={st.median(t['age'] for t in trades):.1f}h "
              f"median_ask={st.median(t['ask'] for t in trades):.4f}")
        print(f"$400/mo fixed: total={sum(monthly):+.2f} avg={sum(monthly)/len(monthly):+.2f} "
              f"positive={sum(x>0 for x in monthly)}/{len(monthly)} CI={boot_ci(monthly)[0]:+.2f}..{boot_ci(monthly)[1]:+.2f}")
    return dict(paired=len(paired),mb=mb,mktb=mktb,trades=len(trades),net=sum(t['net'] for t in trades),
                pnl=sum(monthly),monthly=monthly)

def build_strict(max_age_h, spread):
    """Same as backtest_015.build, but a bracket is only tradable/priced if its
    last ask-side print is <= max_age_h old at decision; ask premium = spread."""
    monthly=bt.load_monthly(); rows=[]
    for t,group in sorted(monthly.items()):
        pr=bt.predict(t)
        if pr is None: continue
        e=bt.choose_event(group); rec=bt.trade_file(e['slug'])
        if not rec: continue
        dec=bt.decision_ts(*t)
        prices=bt.price_rows(rec,dec,max_age_h)
        for r in prices:
            if r['age'] is not None and r['age']>max_age_h:
                r['ask']=None
            elif r['ask'] is not None:
                # rebuild ask with requested premium from raw print
                if r['side']=='YES_BUY' or r['side']=='NO_BUY':
                    r['ask']=min(0.999,r['px']+spread)
                else:
                    r['ask']=min(0.999,r['px']+2*spread)
        labels=[r['label'] for r in prices]; bounds=[bt.parse_label(l) for l in labels]
        md=bt.model_dist(pr,labels); mkt=bt.dist_from_prices(prices)
        om={m['label']:json.loads(m['outcomePrices']) for m in rec['markets']}
        settled=[i for i,r in enumerate(prices) if om[r['label']][0] in ('1','1.0')]
        if len(settled)!=1: continue
        si=settled[0]; actual=bt.g.get(t)
        trades=[]
        for i,r in enumerate(prices):
            if r['ask'] is None: continue
            ask=r['ask']; p=md[i]; fee=bt.FEE_RATE*ask*(1-ask)
            if p-ask>fee+0.01+0.02:
                payoff=1.0 if i==si else 0.0
                trades.append(dict(net=payoff-ask-fee,ask=ask,age=r['age'],won=bool(payoff)))
        rows.append(dict(t=t,model_ll=bt.nll(md[si]),market_ll=(bt.nll(mkt[si]) if mkt else None),
                         trades=trades))
    return rows

if __name__=='__main__':
    base=bt.build()
    print('SOURCE: backtest_015.build() replicated in this run')
    s=summarize(base,'PRIMARY (all 29 closed months, last print at/before decision, +1c)')
    # temporal OOS split: first 18 months "dev", last 11 "holdout"
    dev=[r for r in base if r['t']<=(2025,9)]
    hold=[r for r in base if r['t']>=(2025,10)]
    summarize(dev,'TEMPORAL DEV 2024-04..2025-09 (17 available months; 2024-07 missing)')
    summarize(hold,'TEMPORAL HOLDOUT/OOS 2025-10..2026-09 (12 months)')
    for h in (72,24,6,2):
        rows=build_strict(h,0.01)
        summarize(rows,f'STRICT: last ask-side print <= {h}h at decision; stale brackets not priced/traded; +1c')
    for sp in (0.02,0.03):
        rows=build_strict(24,sp)
        summarize(rows,f'STRICT: <=24h; wider half-spread {sp:.2f} (ask=print+{sp:.2f}); fee 5%')
    # model reproduction check: recompute pred from scratch vs primary CSV
    pred={f"{y}-{m:02d}":bt.predict((y,m))['pred'] for y in range(2024,2027) for m in range(1,13) if (y,m) in [r['t'] for r in base]}
    diffs=[]
    for r in csv.DictReader(open('primary_months.csv')):
        diffs.append(abs(float(r['pred'])-pred[r['month']]))
    print('='*100)
    print(f'LOOKAHEAD CHECK: 29 walk-forward preds recomputed from raw CSV; max |diff| vs primary_months.csv = {max(diffs):.3e}')
