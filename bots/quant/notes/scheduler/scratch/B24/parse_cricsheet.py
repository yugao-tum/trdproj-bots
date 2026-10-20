import json,glob,os,csv,re
rows=[]
for src,pat in [('t20i','/tmp/opencode/cricsheet/t20m/*.json'),('ipl','/tmp/opencode/cricsheet/ipl/*.json')]:
    for f in glob.glob(pat):
        try: d=json.load(open(f))
        except Exception: continue
        info=d.get('info',{})
        teams=info.get('teams',[])
        if len(teams)!=2: continue
        dates=info.get('dates',[])
        if not dates: continue
        out=info.get('outcome',{})
        winner=out.get('winner','') or out.get('eliminator','')
        rows.append(dict(src=src,file=os.path.basename(f),date=dates[0],team1=teams[0],team2=teams[1],
            winner=winner,result=out.get('result',''),eliminator=out.get('eliminator',''),by_runs=out.get('by',{}).get('runs',''),by_wkts=out.get('by',{}).get('wickets',''),
            method=out.get('method',''),event=info.get('event',{}).get('name',''),match_number=info.get('event',{}).get('match_number',''),
            venue=info.get('venue',''),city=info.get('city',''),neutral=info.get('neutral',''),gender=info.get('gender',''),overs=info.get('overs','')))
rows.sort(key=lambda r:(r['date'],r['src']))
with open('matches.csv','w',newline='') as fh:
    w=csv.DictWriter(fh,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
print(len(rows))
from collections import Counter
print(Counter((r['src'],r['date'][:4]) for r in rows).most_common(10))
print(min(r['date'] for r in rows),max(r['date'] for r in rows))
i26=[r for r in rows if r['src']=='ipl' and r['date']>='2026-01-01']
print('IPL2026',len(i26),i26[0]['date'] if i26 else '',i26[-1]['date'] if i26 else '')
