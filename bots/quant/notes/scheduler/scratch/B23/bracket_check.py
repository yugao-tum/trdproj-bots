import json,csv,os
EV=json.load(open('_cache/events_closed0.json'))
tr=json.load(open('_cache/trades_all.json'))['trades']
def d4(st,md):
    with open(f'_cache/usdm/{st}.csv') as f:
        for r in csv.DictReader(f):
            if r['MapDate']==md: return float(r['D4'])
    return None
STATES=['AL','AZ','AR','CA','CO','CT','DE','FL','GA','ID','IL','IN','IA','KS','KY','LA','ME','MD','MA','MI','MN','MS','MO','MT','NE','NV','NH','NJ','NM','NY','NC','ND','OH','OK','OR','PA','RI','SC','SD','TN','TX','UT','VT','VA','WA','WV','WI','WY']
def bracket(n):
    if n==0: return '0'
    if n<=2: return '1-2'
    if n<=4: return '3-4'
    if n<=6: return '5-6'
    if n<=9: return '7-9'
    return '10+'
for e in EV:
    if not e['slug'].startswith('states-in-d4-drought-'): continue
    week=e['slug'].split('states-in-d4-drought-')[1]; md=week.replace('-','')
    cnt=sum(1 for st in STATES if (d4(st,md) or 0)>=0.05)
    res=[m for m in e['markets'] if json.loads(m['outcomePrices'])[0]=='1']
    print(week,'count',cnt,'bracket',bracket(cnt),'market',[m.get('groupItemTitle') for m in res])
