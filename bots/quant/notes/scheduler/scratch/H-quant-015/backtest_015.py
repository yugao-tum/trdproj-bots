#!/usr/bin/env python3
# Historical tradable-price backtest for quant-015 using data-api fills.
# Decision: 5th of month after target month, 00:00 UTC (after month-end ERA5 is complete).
# Price: last YES fill at/before decision within 24h (primary), ask = fill + 1c half-spread.
# Settlement: Gamma outcomePrices = market's own first-release settlement (NOT current GISTEMP).
import csv, json, math, os, re, random, statistics as st
from datetime import date, datetime, timezone

D=os.path.dirname(os.path.abspath(__file__)); os.chdir(D)
CACHE='_cache'; FEE_RATE=0.05
MONTHS=['January','February','March','April','May','June','July','August','September','October','November','December']

# ---------- GISTEMP current revised table ----------
g={}
for line in open(os.path.join(CACHE,'gistemp.txt'),errors='ignore'):
    m=re.match(r'^\s*(\d{4})\s+(.*)$',line)
    if not m: continue
    yr=int(m.group(1)); toks=m.group(2).split()
    if len(toks)<12: continue
    for mo in range(1,13):
        v=toks[mo-1]
        if v.startswith('*'): continue
        try: g[(yr,mo)]=int(v)/100.0
        except ValueError: pass

# ---------- ERA5 monthly mean ----------
days={}; stat={}
with open(os.path.join(CACHE,'era5.csv'),errors='ignore') as f:
    rows=(ln for ln in f if not ln.startswith('#'))
    for r in csv.DictReader(rows):
        try:
            y,mo,d=map(int,r['date'].split('-')); a=float(r['ano_91-20'])
        except Exception: continue
        days.setdefault((y,mo),[]).append(a); stat[(y,mo)]=r['status']
def ndays(y,m): return (date(y+(m==12),(m%12)+1,1)-date(y,m,1)).days
era={k:sum(v)/len(v) for k,v in days.items() if len(v)>=28}
full={k for k,v in days.items() if len(v)==ndays(*k)}

def ols(xs,ys):
    n=len(xs); mx=sum(xs)/n; my=sum(ys)/n
    sxx=sum((x-mx)**2 for x in xs); sxy=sum((x-mx)*(y-my) for x,y in zip(xs,ys))
    b=sxy/sxx; a=my-b*mx
    resid=[y-(a+b*x) for x,y in zip(xs,ys)]
    return a,b,math.sqrt(sum(r*r for r in resid)/(n-2))
def ncdf(z): return 0.5*(1+math.erf(z/math.sqrt(2)))
def nll(p): return -math.log(max(p,1e-12))

def predict(t,win=120):
    prior=[]; yy,mm=t; k=0
    while len(prior)<win and k<win*3:
        k+=1; mm-=1
        if mm==0: mm=12; yy-=1
        if (yy,mm) in g and (yy,mm) in full: prior.append((yy,mm))
        else: return None
    prior=list(reversed(prior))
    a,b,sig=ols([era[p] for p in prior],[g[p] for p in prior])
    return dict(a=a,b=b,sig=sig,pred=a+b*era[t],era=era[t])

def parse_label(lab):
    s=lab.replace('ºC','').replace('°C','').replace('–','-').replace('—','-').strip()
    s=re.sub(r'\s+',' ',s)
    if s.startswith('<'): return (-math.inf,float(s[1:].strip())-0.005)
    if s.startswith('>'): return (float(s[1:].strip())+0.005,math.inf)
    mm=re.match(r'^(-?\d+(?:\.\d+)?)\s*-\s*(-?\d+(?:\.\d+)?)$',s)
    if mm: return (float(mm.group(1))-0.005,float(mm.group(2))+0.005)
    raise ValueError('bad label '+repr(lab))
def in_bracket(x,b): return b[0] <= x < b[1]
def bracket_of(x,bounds):
    for i,b in enumerate(bounds):
        if in_bracket(x,b): return i
    return None

def month_of(e):
    t=e.get('title','')
    for i,mn in enumerate(MONTHS):
        if mn in t:
            parts=t.split()
            for j,p in enumerate(parts):
                if p==mn and j+1<len(parts):
                    try: return int(parts[j+1]), i+1
                    except ValueError: pass
    raise ValueError(t)
def decision_ts(y,m):
    yy,mm=(y+1,1) if m==12 else (y,m+1)
    return int(datetime(yy,mm,5,tzinfo=timezone.utc).timestamp())

def load_monthly():
    monthly={}
    for fn in sorted(os.listdir(CACHE)):
        if fn.startswith('ev_') and fn.endswith('.json'):
            e=json.load(open(os.path.join(CACHE,fn)))[0]
            if not e.get('closed'): continue
            y,m=month_of(e); monthly.setdefault((y,m),[]).append(e)
    return monthly
def trade_file(slug):
    p=os.path.join(CACHE,'tr_'+slug+'.json')
    return json.load(open(p)) if os.path.exists(p) else None

def clean_trades(trs):
    """Drop obvious same-wallet round trips: BUY and SELL of the same outcome
    within 180 min at prices >0.15 apart. Example: Sept-2026 <1.30 wallet
    0xf769... bought YES 0.707 then sold YES 0.015 within 1h."""
    out=[]; by={}
    for t in trs: by.setdefault((t.get('proxyWallet'),t.get('outcome')),[]).append(t)
    bad=set()
    for key,xs in by.items():
        xs.sort(key=lambda t:t['timestamp'])
        for i in range(len(xs)):
            for j in range(i+1,len(xs)):
                if xs[j]['timestamp']-xs[i]['timestamp']>180*60: break
                if xs[i]['side']!=xs[j]['side'] and abs(float(xs[i]['price'])-float(xs[j]['price']))>0.15:
                    bad.add(id(xs[i])); bad.add(id(xs[j]))
    return [t for t in trs if id(t) not in bad]

def price_rows(rec,dec,max_age_h=24.0, wash=False):
    # Ask-side proxy priority: actual taker YES BUY > taker NO BUY (complement)
    # > taker YES SELL (bid + full spread) > taker NO SELL. No SELL print is
    # ever treated as an ask directly (the Sept 0.24 SELL vs CLOB 0.635 shows why).
    out=[]
    for mk in rec['markets']:
        trs=clean_trades(mk['trades']) if wash else mk['trades']
        def last(outcome,side):
            xs=[t for t in trs if t.get('outcome')==outcome and t.get('side')==side and t.get('timestamp',0)<=dec]
            xs.sort(key=lambda t:t['timestamp'])
            return xs[-1] if xs else None
        t=last('Yes','BUY'); kind='YES_BUY'; px=None; ask=None
        if t: px=float(t['price']); ask=min(0.999,px+0.01)
        if t is None:
            t=last('No','BUY'); kind='NO_BUY'
            if t: px=1-float(t['price']); ask=min(0.999,px+0.01)
        if t is None:
            t=last('Yes','SELL'); kind='YES_SELL'
            if t: px=float(t['price']); ask=min(0.999,px+0.02)
        if t is None:
            t=last('No','SELL'); kind='NO_SELL'
            if t: px=1-float(t['price']); ask=min(0.999,px+0.02)
        if t:
            age=(dec-t['timestamp'])/3600.0
            out.append(dict(label=mk['label'],px=px,ask=ask,age=age,ts=t['timestamp'],side=kind,fresh=age<=max_age_h))
        else:
            out.append(dict(label=mk['label'],px=None,ask=None,age=None,ts=None,side=None,fresh=False))
    return out
def dist_from_prices(rows):
    vals=[r['px'] for r in rows]
    if any(v is None for v in vals): return None
    vals=[min(max(v,1e-6),1-1e-6) for v in vals]; s=sum(vals)
    return [v/s for v in vals]
def model_dist(pr,labels):
    ps=[]
    for lo,hi in [parse_label(l) for l in labels]:
        a=ncdf((lo-pr['pred'])/pr['sig']) if lo!=-math.inf else 0.0
        b=ncdf((hi-pr['pred'])/pr['sig']) if hi!=math.inf else 1.0
        ps.append(max(b-a,0.0))
    s=sum(ps); return [p/s for p in ps]
def choose_event(group):
    def key(e):
        rec=trade_file(e['slug'])
        return (-len(e['markets']),-(sum(len(m.get('trades',[])) for m in rec['markets']) if rec else 0),e['slug'])
    return sorted(group,key=key)[0]

def build(max_age_h=24.0,shift=0,fee_rate=FEE_RATE,wash=False):
    monthly=load_monthly(); rows=[]
    for t,group in sorted(monthly.items()):
        pr=predict(t)
        if pr is None: continue
        e=choose_event(group); rec=trade_file(e['slug'])
        if not rec: continue
        dec=decision_ts(*t)+int(shift*86400)
        prices=price_rows(rec,dec,max_age_h,wash)
        labels=[r['label'] for r in prices]; bounds=[parse_label(l) for l in labels]
        md=model_dist(pr,labels); mkt=dist_from_prices(prices)
        om={m['label']:json.loads(m['outcomePrices']) for m in rec['markets']}
        settled=[i for i,r in enumerate(prices) if om[r['label']][0] in ('1','1.0')]
        if len(settled)!=1: continue
        si=settled[0]; actual=g.get(t)
        current_bi=bracket_of(actual,bounds) if actual is not None else None
        trades=[]
        for i,r in enumerate(prices):
            if r['ask'] is None: continue
            ask=r['ask']; p=md[i]; fee=fee_rate*ask*(1-ask)
            if p-ask > fee+0.01+0.02:
                payoff=1.0 if i==si else 0.0; net=payoff-ask-fee
                trades.append(dict(t=t,slug=e['slug'],label=r['label'],ask=ask,p=p,fee=fee,payoff=payoff,net=net,age=r['age'],won=bool(payoff)))
        rows.append(dict(t=t,slug=e['slug'],pred=pr['pred'],sig=pr['sig'],era=pr['era'],
                         actual_current=actual,settled_label=prices[si]['label'],
                         settled_first_in_current=bool(actual is not None and in_bracket(actual,bounds[si])),
                         model_hit_settled=(max(range(len(md)),key=lambda i:md[i])==si),
                         model_hit_current=(current_bi is not None and max(range(len(md)),key=lambda i:md[i])==current_bi),
                         model_ll=nll(md[si]),market_ll=(nll(mkt[si]) if mkt else None),
                         all_priced=(mkt is not None),md=md,mkt=mkt,prices=prices,trades=trades,
                         model_p_settled=md[si],market_p_settled=(mkt[si] if mkt else None),dec=dec))
    return rows

def stats(rows):
    out={}
    paired=[r for r in rows if r['market_ll'] is not None]
    out['n']=len(rows); out['paired']=len(paired)
    out['model_ll']=sum(r['model_ll'] for r in paired)/len(paired) if paired else None
    out['market_ll']=sum(r['market_ll'] for r in paired)/len(paired) if paired else None
    out['model_better']=sum(r['model_ll']<r['market_ll'] for r in paired)
    out['market_better']=sum(r['market_ll']<r['model_ll'] for r in paired)
    diffs=[r['market_ll']-r['model_ll'] for r in paired]
    out['median_diff']=st.median(diffs) if diffs else None
    n=out['model_better']+out['market_better']; k=min(out['model_better'],out['market_better'])
    out['sign_p']=min(1.0,2*sum(math.comb(n,i) for i in range(k+1))/2**n) if n else None
    trades=[tr for r in rows for tr in r['trades']]
    out['trades']=len(trades); out['hit']=sum(tr['won'] for tr in trades)
    out['staked']=sum(tr['ask'] for tr in trades); out['net']=sum(tr['net'] for tr in trades)
    out['median_net']=st.median([tr['net'] for tr in trades]) if trades else None
    out['median_age']=st.median([tr['age'] for tr in trades]) if trades else None
    out['median_ask']=st.median([tr['ask'] for tr in trades]) if trades else None
    out['mean_net']=out['net']/len(trades) if trades else None
    out['return_on_stake']=out['net']/out['staked'] if out['staked'] else None
    # equal capital per month: 400 USDT budget, max 200 per bracket
    monthly=[]
    for r in rows:
        trs=r['trades']
        if not trs: monthly.append(0.0); continue
        alloc=min(200.0,400.0/len(trs))
        pnl=sum(alloc*tr['net']/tr['ask'] for tr in trs)
        monthly.append(pnl)
    out['monthly_pnl']=monthly
    out['total_monthly_pnl']=sum(monthly)
    out['avg_monthly_pnl']=sum(monthly)/len(monthly) if monthly else None
    out['positive_months']=sum(x>0 for x in monthly)
    # bootstrap mean monthly pnl, 2000 draws
    rng=random.Random(20261021); means=[]
    for _ in range(2000):
        s=[monthly[rng.randrange(len(monthly))] for _ in monthly]
        means.append(sum(s)/len(s))
    means.sort(); out['boot_lo']=means[50]; out['boot_hi']=means[1949]
    # undo top wins
    nets=sorted([tr['net'] for tr in trades],reverse=True)
    out['top_wins']=nets[:3]
    out['net_ex_top1']=out['net']-(nets[0] if nets else 0)
    out['net_ex_top3']=out['net']-sum(nets[:3])
    out['model_hit_settled']=sum(r['model_hit_settled'] for r in rows)
    out['model_hit_current']=sum(r['model_hit_current'] for r in rows)
    out['first_matches_current']=sum(r['settled_first_in_current'] for r in rows)
    return out

def show(rows,title):
    s=stats(rows)
    print('='*110); print(title)
    print(f"months={s['n']} paired={s['paired']} full_price_coverage={sum(r['all_priced'] for r in rows)}")
    print(f"log loss: model={s['model_ll']:.6f} market={s['market_ll']:.6f} "
          f"diff(market-model)={s['market_ll']-s['model_ll']:+.6f} median_paired_diff={s['median_diff']:+.6f}")
    print(f"  model better {s['model_better']}, market better {s['market_better']}, sign_test_p={s['sign_p']:.6f}")
    print(f"model point hit vs first-release settled bracket: {s['model_hit_settled']}/{s['n']}={s['model_hit_settled']/s['n']:.4f}; vs current revised bracket: {s['model_hit_current']}/{s['n']}={s['model_hit_current']/s['n']:.4f}")
    print(f"first-release settled bracket still contains current revised GISTEMP: {s['first_matches_current']}/{s['n']}={s['first_matches_current']/s['n']:.4f}")
    print(f"trades={s['trades']} hit={s['hit']}/{s['trades']} staked={s['staked']:.6f} net={s['net']:+.6f} "
          f"median_net/share={s['median_net']:+.6f} mean_net/share={s['mean_net']:+.6f} return_on_stake={s['return_on_stake']:+.2%}, "
          f"median_fill_age={s['median_age']:.1f}h, median_ask={s['median_ask']:.4f}")
    print(f"equal-capital ($400/mo, max $200/bracket): total={s['total_monthly_pnl']:+.2f} USDT, "
          f"avg={s['avg_monthly_pnl']:+.2f}/mo, positive months {s['positive_months']}/{s['n']}, "
          f"bootstrap 95% CI of mean={s['boot_lo']:+.2f}..{s['boot_hi']:+.2f} USDT/mo")
    print(f"top 3 winning trades net/share={['%+.3f'%x for x in s['top_wins']]}; "
          f"net excluding top1={s['net_ex_top1']:+.6f}, excluding top3={s['net_ex_top3']:+.6f}")
    print('month  slug                          pred   settled(first)   curr   modelP mktP   modelLL mktLL   trades net')
    for r in rows:
        print(f"{r['t'][0]}-{r['t'][1]:02d} {r['slug'][:29]:29s} {r['pred']:.4f} {r['settled_label']:14s} "
              f"{r['actual_current']:.2f}  {r['model_p_settled']:.4f} {r['market_p_settled']:.4f}  "
              f"{r['model_ll']:.4f} {r['market_ll']:.4f}  {len(r['trades']):2d} {sum(x['net'] for x in r['trades']):+.4f}")
    return s

def write_csv(rows,base):
    with open(base+'_months.csv','w',newline='') as f:
        w=csv.writer(f); w.writerow(['month','slug','pred','sigma','settled_label','current_gistemp',
            'first_in_current','model_hit_settled','model_p_settled','market_p_settled','model_ll','market_ll','n_trades','staked','net'])
        for r in rows:
            w.writerow([f"{r['t'][0]}-{r['t'][1]:02d}",r['slug'],f"{r['pred']:.6f}",f"{r['sig']:.6f}",
                r['settled_label'],r['actual_current'],int(r['settled_first_in_current']),
                int(r['model_hit_settled']),f"{r['model_p_settled']:.6f}",
                (f"{r['market_p_settled']:.6f}" if r['market_p_settled'] is not None else ''),
                f"{r['model_ll']:.6f}",(f"{r['market_ll']:.6f}" if r['market_ll'] is not None else ''),
                len(r['trades']),f"{sum(x['ask'] for x in r['trades']):.6f}",f"{sum(x['net'] for x in r['trades']):.6f}"])
    with open(base+'_trades.csv','w',newline='') as f:
        w=csv.writer(f); w.writerow(['month','slug','label','ask','model_p','fee','payoff','net','age_h','won'])
        for r in rows:
            for tr in r['trades']:
                w.writerow([f"{r['t'][0]}-{r['t'][1]:02d}",r['slug'],tr['label'],f"{tr['ask']:.6f}",
                    f"{tr['p']:.6f}",f"{tr['fee']:.6f}",tr['payoff'],f"{tr['net']:.6f}",f"{tr['age']:.2f}",int(tr['won'])])

if __name__=='__main__':
    base=build(); s=show(base,'PRIMARY: decision=5th next month 00:00Z; last ask-side print at/before decision; ask=print+1c; fee 5%; trigger p-ask>fee+1c+2c')
    write_csv(base,'primary')
    print('\nINDEPENDENT MONTHS:',len(base))
    for shift,label in [(0,'decision +2d (7th)'),(0,'')]:
        pass
    show(build(max_age_h=24,shift=2),'SENS: decision +2 days (7th); last ask-side print before that')
    show(build(max_age_h=24,shift=7),'SENS: decision +7 days (12th); last ask-side print before that')
    show(build(max_age_h=24,shift=0,fee_rate=0.0),'SENS: zero fee (reference only, not tradable)')
    show(build(wash=True),'SENS: drop same-wallet round-trip wash prints (see clean_trades)')
