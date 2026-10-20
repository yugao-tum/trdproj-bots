import json,statistics as st
R=json.load(open('_cache/analysis_rows.json'))
def fee(p): return 0.05*p*(1-p) if 0<=p<=1 else 0
def net(y,p): return y-p-fee(p)-0.01
def run(name,pricekey,trig='hist',model='A',verbose=False):
    tr=[]
    for r in R:
        m=r['modelA'] if model=='A' else 0.4903
        base=r['p_hist'] if trig=='hist' else r[pricekey]
        if base is None: continue
        if base<=m-0.05:
            p=r[pricekey]
            if p is None: continue
            tr.append((r['key'],r['season'],r['pole'],r['y'],r['p_hist'],p,net(r['y'],p)))
    tot=sum(x[6] for x in tr); n=len(tr); w=sum(1 for x in tr if x[3]==1)
    print(f"{name:38s} n={n:2d} wins={w:2d} sum={tot:+.4f} mean={tot/n if n else 0:+.4f}")
    if verbose:
        for x in tr: print('   ',x[0],x[2],'y',x[3],'hist',round(x[4],4),'fill',round(x[5],4),'net',round(x[6],4))
    return tr
print('--- rule A (margin bins; trigger uses prices-history last price at cutoff) ---')
for k in ['p_hist','first_buy_price','exec20','exec100']:
    run('A fill='+k,k)
print('--- rule B (const 0.4903) ---')
for k in ['p_hist','first_buy_price','exec20','exec100']:
    run('B fill='+k,k,model='B')
print('--- unconditional buy every pole sitter ---')
for k in ['p_hist','first_buy_price','exec20','exec100']:
    tr=[]
    for r in R:
        p=r[k]
        if p is None: continue
        tr.append((r['key'],r['y'],net(r['y'],p)))
    tot=sum(x[2] for x in tr)
    print(f"all fill={k:18s} n={len(tr):2d} wins={sum(1 for x in tr if x[1]==1):2d} sum={tot:+.4f} mean={tot/len(tr):+.4f}")
print('--- trigger if executable price itself <= model-0.05 (limit order at fill) ---')
for k in ['first_buy_price','exec20','exec100']:
    run('A trigger&fill='+k,k,trig=k)
print('--- per-trade detail, rule A with exec100 ---')
run('A exec100 detail','exec100',verbose=True)
print('--- uplift distribution ---')
up=[r['exec100']-r['p_hist'] for r in R if r['exec100'] is not None and r['p_hist'] is not None]
print('n',len(up),'mean',round(st.mean(up),4),'median',round(st.median(up),4),'p10',round(sorted(up)[4],4),'p90',round(sorted(up)[44],4))
up1=[r['first_buy_price']-r['p_hist'] for r in R if r['first_buy_price'] is not None]
print('first_buy-p_hist mean',round(st.mean(up1),4),'median',round(st.median(up1),4),'min',round(min(up1),4),'max',round(max(up1),4))
print('--- 2026 dust cases ---')
for r in R:
    if r['key'] in ('2026-5','2026-14','2026-13','2026-10'):
        print(r['key'],'hist',r['p_hist'],'first',r['first_buy_price'],r['first_buy_size'],'exec100',r['exec100'],'bought_shares',r['buy_shares_pre'],'y',r['y'])
