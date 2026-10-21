import json,csv
R=json.load(open('_cache/analysis_rows.json')); D={x['key']:x for x in json.load(open('_cache/diag.json'))}
def fee(p): return 0.05*p*(1-p)
def net(y,p): return y-p-fee(p)-0.01
rows=[]
for r in R:
    d=D[r['key']]
    rows.append({'key':r['key'],'race':r['race'],'season':r['season'],'round':r['round'],'pole':r['pole'],
      'margin':r['margin'],'modelA':r['modelA'],'y':r['y'],'p_hist':r['p_hist'],
      'last_pre_price':d['last_pre_price'],'last_pre_side':d['last_pre_side'],
      'first_buy_price':r['first_buy_price'],'first_buy_size':r['first_buy_size'],'first_buy_dt_h':d['first_buy_dt_h'],
      'exec20':r['exec20'],'exec100':r['exec100'],'q100':r['q100'],
      'buy_shares_pre':d['buy_shares_pre'],'t100_h':d['t100_h'],'race_window_h':d['race_window_h'],
      'triggerA': int(r['p_hist']<=r['modelA']-0.05),
      'net_hist':round(net(r['y'],r['p_hist']),6),
      'net_first':round(net(r['y'],r['first_buy_price']),6),
      'net_exec100':round(net(r['y'],r['exec100']),6)})
with open('exec_rows.csv','w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
print('wrote exec_rows.csv',len(rows))
# compact table for entry: only rule A triggers
for x in rows:
    if x['triggerA']:
        print(f"{x['key']:8s} {x['pole']:16s} y={x['y']:.0f} hist={x['p_hist']:.4f} first={x['first_buy_price']:.4f} e100={x['exec100']:.4f} net_hist={x['net_hist']:+.4f} net_e100={x['net_exec100']:+.4f}")
