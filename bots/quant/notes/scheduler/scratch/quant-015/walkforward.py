#!/usr/bin/env python3
import csv, math, re, statistics as st
from datetime import date

# ---------- parse GISTEMP monthly table (current, revised values) ----------
g = {}
for line in open('_cache/gistemp.txt', errors='ignore'):
    m = re.match(r'^\s*(\d{4})\s+(.*)$', line)
    if not m:
        continue
    yr = int(m.group(1)); toks = m.group(2).split()
    if len(toks) < 12:
        continue
    for mo in range(1, 13):
        v = toks[mo-1]
        if v.startswith('*'):
            continue
        try:
            g[(yr, mo)] = int(v)/100.0
        except ValueError:
            pass

# ---------- parse ERA5 daily CSV, monthly mean of ano_91-20 ----------
days = {}; stat = {}
with open('_cache/era5.csv', errors='ignore') as f:
    rows = (ln for ln in f if not ln.startswith('#'))
    rd = csv.DictReader(rows)
    for r in rd:
        try:
            y, mo, d = map(int, r['date'].split('-')); a = float(r['ano_91-20'])
        except Exception:
            continue
        days.setdefault((y, mo), []).append(a)
        stat[(y, mo)] = r['status']

def ndays(y, m):
    return (date(y+(m == 12), (m % 12)+1, 1)-date(y, m, 1)).days

era = {k: sum(v)/len(v) for k, v in days.items() if len(v) >= 28}
full = {k for k, v in days.items() if len(v) == ndays(*k)}

def ols(xs, ys):
    n = len(xs); mx = sum(xs)/n; my = sum(ys)/n
    sxx = sum((x-mx)**2 for x in xs); sxy = sum((x-mx)*(y-my) for x, y in zip(xs, ys))
    b = sxy/sxx; a = my-b*mx
    resid = [y-(a+b*x) for x, y in zip(xs, ys)]
    sig = math.sqrt(sum(r*r for r in resid)/(n-2))
    return a, b, sig, resid

def ncdf(z):
    return 0.5*(1+math.erf(z/math.sqrt(2)))

def nll(p):
    return -math.log(max(p, 1e-12))

def bracket_idx(x):
    return math.floor((x+0.005)/0.05)

targets = []
y, m = 2000, 1
while (y, m) <= (2026, 9):
    if (y, m) in g and (y, m) in full:
        targets.append((y, m))
    m += 1
    if m == 13:
        y += 1; m = 1
allmonths = sorted(k for k in g if k in full and k <= (2026, 9))

def run(mode, win):
    out = []; skipped = 0
    for t in targets:
        prior = []
        if mode == 'rolling':
            yy, mm = t[0], t[1]; k = 0
            while len(prior) < win and k < win*3:
                k += 1; mm -= 1
                if mm == 0:
                    mm = 12; yy -= 1
                if (yy, mm) in g and (yy, mm) in full:
                    prior.append((yy, mm))
                else:
                    prior = []; break
            prior = list(reversed(prior))
        else:
            prior = [p for p in allmonths if p < t]
        if mode == 'rolling' and len(prior) < win:
            skipped += 1; continue
        if len(prior) < 24:
            skipped += 1; continue
        xs = [era[p] for p in prior]; ys = [g[p] for p in prior]
        a, b, sig, _ = ols(xs, ys)
        pred = a+b*era[t]; actual = g[t]
        yy, mm = t[0], t[1]-1
        if mm == 0:
            mm = 12; yy -= 1
        while (yy, mm) not in g and (yy, mm) >= (1880, 1):
            mm -= 1
            if mm == 0:
                mm = 12; yy -= 1
        pprev = g[(yy, mm)]
        pr = []
        for p in prior:
            yy2, mm2 = p[0], p[1]-1
            if mm2 == 0:
                mm2 = 12; yy2 -= 1
            if (yy2, mm2) in g:
                pr.append(g[p]-g[(yy2, mm2)])
        psig = st.stdev(pr) if len(pr) > 2 else sig
        edges = [pprev-0.15+i*0.05 for i in range(7)]
        def probs(mu, s):
            ps = [ncdf((edges[0]-mu)/s)]
            for i in range(6):
                ps.append(ncdf((edges[i+1]-mu)/s)-ncdf((edges[i]-mu)/s))
            ps.append(1-ncdf((edges[-1]-mu)/s))
            return ps
        pm = probs(pred, sig); pp = probs(pprev, psig); pu = [1/8]*8
        if actual < edges[0]:
            oi = 0
        elif actual >= edges[-1]:
            oi = 7
        else:
            oi = 1+next(i for i in range(6) if edges[i] <= actual < edges[i+1])
        out.append(dict(t=t, a=a, b=b, sig=sig, pred=pred, actual=actual, pprev=pprev, psig=psig,
                        llm=nll(pm[oi]), llp=nll(pp[oi]), llu=nll(pu[oi]),
                        hit=int(bracket_idx(pred) == bracket_idx(actual)),
                        phit=int(bracket_idx(pprev) == bracket_idx(actual)),
                        pit=ncdf((actual-pred)/sig), z=(actual-pred)/sig, oi=oi,
                        pm=pm, edges=edges, era=era[t], status=stat[t]))
    return out, skipped

def block(lbl, out):
    n = len(out); pits = sorted(r['pit'] for r in out)
    ks = max(abs(pits[i]-(i+1)/n) for i in range(n))
    print(f' {lbl}: n={n} hit={sum(r["hit"] for r in out)}/{n}={sum(r["hit"] for r in out)/n:.4f} '
          f'persist_hit={sum(r["phit"] for r in out)}/{n}={sum(r["phit"] for r in out)/n:.4f} '
          f'LL_model={sum(r["llm"] for r in out)/n:.4f} LL_persist={sum(r["llp"] for r in out)/n:.4f} '
          f'LL_uniform={sum(r["llu"] for r in out)/n:.4f} '
          f'cov50={sum(abs(r["z"]) <= 0.67449 for r in out)/n:.4f} '
          f'cov80={sum(abs(r["z"]) <= 1.28155 for r in out)/n:.4f} '
          f'cov90={sum(abs(r["z"]) <= 1.64485 for r in out)/n:.4f} KS={ks:.4f}')

def summarize(name, out, skipped):
    print(f'=== {name}: n={len(out)}, skipped={skipped}, span={out[0]["t"]}..{out[-1]["t"]} ===')
    n = len(out); pits = sorted(r['pit'] for r in out)
    mean = sum(pits)/n; sd = math.sqrt(sum((x-mean)**2 for x in pits)/(n-1))
    ks = max(abs(pits[i]-(i+1)/n) for i in range(n))
    print(f' PIT: mean={mean:.4f} sd={sd:.4f} KS_vs_U(0,1)={ks:.4f}')
    dec = [0]*10
    for r in out:
        dec[min(9, int(r['pit']*10))] += 1
    print(' PIT deciles:', dec)
    for lbl, sel in [('ALL', out), ('2000-2012', [r for r in out if r['t'][0] <= 2012]),
                     ('2013-2026', [r for r in out if r['t'][0] >= 2013]),
                     ('2020-2026', [r for r in out if r['t'][0] >= 2020]),
                     ('2024-2026', [r for r in out if r['t'] >= (2024, 1)]),
                     ('2024-04..2026-09', [r for r in out if r['t'] >= (2024, 4)])]:
        if sel:
            block(lbl, sel)
    print(' tail outcomes (outside +/-0.15 of persistence):', sum(1 for r in out if r['oi'] in (0, 7)))

out120, sk120 = run('rolling', 120)
outexp, ske = run('expanding', 0)
out60, sk60 = run('rolling', 60)
summarize('MAIN rolling 120 months', out120, sk120)
summarize('ROBUSTNESS expanding (all prior from 1940)', outexp, ske)
summarize('ROBUSTNESS rolling 60 months', out60, sk60)

r = out120[-1]; mi = bracket_idx(r['pred'])
print('=== latest target', r['t'], 'ERA5', round(r['era'], 4), 'pred', round(r['pred'], 4),
      'actual', r['actual'], 'sigma', round(r['sig'], 4))
print(' latest OLS a,b,sigma', round(r['a'], 6), round(r['b'], 6), round(r['sig'], 6))
for j in range(mi-2, mi+4):
    lo = j*0.05-0.005; hi = lo+0.05
    p = ncdf((hi-r['pred'])/r['sig'])-ncdf((lo-r['pred'])/r['sig'])
    print(f'  [{lo:.2f},{hi:.2f}) p={p:.4f} market-style label {lo+.005:.2f}-{hi-.005:.2f}')
