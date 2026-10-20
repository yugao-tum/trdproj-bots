import json,csv,re,datetime,collections
C=list(csv.DictReader(open('matches.csv')))
C=[r for r in C if r['gender']=='male']
M={}
for r in C: M.setdefault(r['date'],[]).append(r)
cand=json.load(open('/tmp/opencode/cand2.json'))
IPL_FULL={'royal challengers bangalore':'royal challengers bengaluru','kings xi punjab':'punjab kings',
 'delhi daredevils':'delhi capitals','rising pune supergiant':'rising pune supergiant','gujarat lions':'gujarat lions',
 'deccan chargers':'deccan chargers','pune warriors':'pune warriors','kochi tuskers kerala':'kochi tuskers kerala'}
CITY={'hyderabad':'sunrisers hyderabad','rajasthan':'rajasthan royals','chennai':'chennai super kings','mumbai':'mumbai indians',
 'gujarat':'gujarat titans','punjab':'punjab kings','kolkata':'kolkata knight riders','bangalore':'royal challengers bengaluru',
 'delhi':'delhi capitals','lucknow':'lucknow super giants'}
def norm(s):
    s=str(s).strip().lower()
    s=re.sub(r'[^a-z0-9 ]','',s)
    s=re.sub(r'\s+',' ',s)
    if s in ('usa','united states','us'): s='united states of america'
    if s in ('emirates','uae'): s='united arab emirates'
    if s=='new guinea': s='papua new guinea'
    if s=='kong': s='hong kong'
    if s=='lanka': s='sri lanka'
    return IPL_FULL.get(s,CITY.get(s,s))
def dparse(s): return datetime.date.fromisoformat(s[:10])
out=[]
for c in cand:
    d=dparse(c['date'])
    pmset={norm(x) for x in c['outs']}
    best=None
    for delta in (0,-1,1,-2,2):
        dd=str(d+datetime.timedelta(days=delta))
        for r in M.get(dd,[]):
            cs={norm(r['team1']),norm(r['team2'])}
            if cs==pmset:
                best=(r,delta);break
        if best: break
    c=dict(c); c['match']=best[0] if best else None; c['delta']=best[1] if best else None
    out.append(c)
matched=[c for c in out if c['match']]
print('matched',len(matched),'of',len(out))
print(collections.Counter((c['match']['src'],c['match']['date'][:4]) for c in matched).most_common(20))
print('unmatched groups',collections.Counter(c['slug'].split('-')[0] for c in out if not c['match']).most_common(20))
json.dump(out,open('/tmp/opencode/matched.json','w'))
for c in matched[:5]: print(c['slug'],c['date'],c['outs'],'->',c['match']['date'],c['match']['team1'],c['match']['team2'],c['delta'])
