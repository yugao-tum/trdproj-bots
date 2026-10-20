import json, csv, os, datetime as dt, re
from collections import defaultdict
CACHE='_cache'
ev=json.load(open(f'{CACHE}/events_closed0.json'))
tr=json.load(open(f'{CACHE}/trades_all.json'))['trades']
# USDM data
def load_state(st):
    rows={}
    with open(f'{CACHE}/usdm/{st}.csv') as f:
        for r in csv.DictReader(f):
            rows[r['MapDate']]=r
    return rows
states={}
for fn in os.listdir(f'{CACHE}/usdm'):
    if fn.endswith('.csv'):
        st=fn[:-4]; states[st]=load_state(st)
def d4(st,mapdate):
    r=states.get(st,{}).get(mapdate)
    return None if r is None else float(r['D4'])
# market rows
rows=[]
for e in ev:
    slug=e['slug']; ed=e['endDate']
    end=dt.datetime.fromisoformat(ed.replace('Z','+00:00'))
    cutoff=end-dt.timedelta(hours=13, minutes=1)  # Wed 23:59 UTC
    if slug.startswith('state-d4-drought-'):
        week=slug.split('state-d4-drought-')[1]
        for m in e['markets']:
            st=m['slug'].split('-')[-1].upper()
            md=week.replace('-','')
            prior=(dt.date.fromisoformat(week)-dt.timedelta(days=7)).strftime('%Y%m%d')
            op=m.get('outcomePrices')
            try: op=json.loads(op)
            except: op=[]
            # resolution yes?
            res=None
            if op and len(op)>=2:
                # outcomes ["Yes","No"]
                res = float(op[0])>0.5
            # last trade <= cutoff
            ts=cutoff.timestamp()
            last=None
            for t in tr.get(m['slug'],[]):
                if t.get('timestamp',0)<=ts:
                    if last is None or t['timestamp']>last['timestamp']:
                        last=t
            yes_px=None; age=None
            if last:
                yes_px = last['price'] if last.get('outcome')=='Yes' else 1-last['price']
                age=(ts-last['timestamp'])/3600
            rows.append({'kind':'state','week':week,'state':st,'market':m['slug'],
                'prior_d4':d4(st,prior),'cur_d4':d4(st,md),'resolved_yes':res,
                'yes_px':yes_px,'age_h':age,'n_trades':len(tr.get(m['slug'],[])),
                'cutoff':cutoff.isoformat()})
    else:
        week=slug.split('states-in-d4-drought-')[1]
        md=week.replace('-','')
        for m in e['markets']:
            op=m.get('outcomePrices')
            try: op=json.loads(op)
            except: op=[]
            res=float(op[0])>0.5 if op and len(op)>=2 else None
            ts=cutoff.timestamp(); last=None
            for t in tr.get(m['slug'],[]):
                if t.get('timestamp',0)<=ts:
                    if last is None or t['timestamp']>last['timestamp']: last=t
            yes_px=None; age=None
            if last:
                yes_px=last['price'] if last.get('outcome')=='Yes' else 1-last['price']
                age=(ts-last['timestamp'])/3600
            rows.append({'kind':'bracket','week':week,'state':m.get('groupItemTitle') or m['slug'],
                'market':m['slug'],'prior_d4':None,'cur_d4':None,'resolved_yes':res,
                'yes_px':yes_px,'age_h':age,'n_trades':len(tr.get(m['slug'],[])),'cutoff':cutoff.isoformat()})
with open('dataset.csv','w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
print('rows',len(rows))
# summary
sr=[r for r in rows if r['kind']=='state']
print('state rows',len(sr),'with price',sum(1 for r in sr if r['yes_px'] is not None),
      'price<=72h',sum(1 for r in sr if r['yes_px'] is not None and r['age_h']<=72))
print('resolved yes',sum(1 for r in sr if r['resolved_yes']))
# check USDM vs market resolution mismatches
mis=[r for r in sr if r['resolved_yes'] is not None and r['cur_d4'] is not None and ((r['cur_d4']>=0.05)!=r['resolved_yes'])]
print('mismatch USDM vs market',len(mis))
for r in mis[:10]: print(' MIS',r['week'],r['state'],r['cur_d4'],r['resolved_yes'])
# transitions prior->cur on market weeks
print('\nweek state transitions:')
agg=defaultdict(lambda:[0,0])
for r in sr:
    if r['prior_d4'] is None or r['cur_d4'] is None: continue
    key=(r['prior_d4']>=0.05, r['cur_d4']>=0.05)
    agg[key][0]+=1; agg[key][1]+= (1 if r['resolved_yes'] else 0)
for k,v in sorted(agg.items()): print(k,v)
# price distribution by prior status
print('\nprice stats (age<=72h):')
for prior in [True,False]:
    xs=[r['yes_px'] for r in sr if r['yes_px'] is not None and r['age_h']<=72 and (r['prior_d4']>=0.05)==prior]
    xs=sorted(xs)
    print('prior_d4>=.05',prior,'n',len(xs),'min',xs[:3],'max',xs[-3:] if xs else None)
