#!/usr/bin/env python3
# Cross-check data-api ask proxy vs CLOB midpoint for the one closed event with CLOB history.
import json, os, urllib.request
from datetime import datetime, timezone
D=os.path.dirname(os.path.abspath(__file__)); os.chdir(D); CACHE='_cache'
e=json.load(open(os.path.join(CACHE,'ev_september-2026-temperature-increase-c.json')))[0]
rec=json.load(open(os.path.join(CACHE,'tr_september-2026-temperature-increase-c.json')))
dec=rec['decision_ts']; print('decision',datetime.fromtimestamp(dec,timezone.utc).isoformat())
def last_clob(tok):
    u=f'https://clob.polymarket.com/prices-history?market={tok}&interval=max&fidelity=60'
    h=json.load(urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0'}),timeout=30))['history']
    h=[x for x in h if x['t']<=dec]
    return (h[-1]['t'],h[-1]['p']) if h else (None,None)
def api_ask(rec,label):
    mk=next(m for m in rec['markets'] if m['label']==label)
    for outcome,side,conv in [('Yes','BUY',1),('No','BUY',-1),('Yes','SELL',1),('No','SELL',-1)]:
        xs=sorted([t for t in mk['trades'] if t['outcome']==outcome and t['side']==side and t['timestamp']<=dec],key=lambda t:t['timestamp'])
        if xs:
            t=xs[-1]; px=float(t['price']) if conv==1 else 1-float(t['price'])
            add=0.01 if side=='BUY' else 0.02
            return outcome+'_'+side,px,min(0.999,px+add),(dec-t['timestamp'])/3600
    return None,None,None,None
rows=[]
for m in e['markets']:
    lab=m['groupItemTitle']; toks=json.loads(m['clobTokenIds']); tok=toks[0]
    ct,cp=last_clob(tok); kind,px,ask,age=api_ask(rec,lab)
    rows.append((lab,cp,ask,kind,age,ct))
print('label             CLOB_mid  dataapi_ask  source        age_h')
for lab,cp,ask,kind,age,ct in rows:
    print(f'{lab:16s} {cp:.4f}    {ask:.4f}       {kind:10s} {age:6.1f}' if cp is not None else f'{lab:16s} None      {ask} {kind}')
sc=sum(x[1] for x in rows); sa=sum(x[2] for x in rows)
print('CLOB raw sum',round(sc,4),'normalized settled bracket',round(rows[2][1]/sc,4))
print('data-api ask sum',round(sa,4),'normalized settled bracket',round(rows[2][2]/sa,4))
