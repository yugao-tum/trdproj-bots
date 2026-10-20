import json,glob,os,csv,collections,math
def balls(d):
    ex=d.get('extras',{})
    return 0 if ('wides' in ex or 'noballs' in ex) else 1
out=[]
for src,base in [('t20i','/tmp/opencode/cricsheet/t20m'),('ipl','/tmp/opencode/cricsheet/ipl')]:
    for f in glob.glob(base+'/*.json'):
        d=json.load(open(f)); info=d.get('info',{})
        if info.get('gender')!='male': continue
        teams=info.get('teams',[])
        if len(teams)!=2 or not info.get('dates'): continue
        per=collections.defaultdict(lambda:[0,0,0])  # runs, balls, wickets
        for inn in d.get('innings',[]):
            bat=inn.get('team')
            for ov in inn.get('overs',[]):
                for dl in ov.get('deliveries',[]):
                    r=dl.get('runs',{})
                    per[bat][0]+=r.get('total',0)
                    per[bat][1]+=balls(dl)
                    if 'wickets' in dl: per[bat][2]+=len(dl['wickets'])
        t1,t2=teams
        a=per.get(t1,[0,0,0]); b=per.get(t2,[0,0,0])
        rr1=a[0]/(a[1]/6) if a[1] else None
        rr2=b[0]/(b[1]/6) if b[1] else None
        out.append(dict(file=os.path.basename(f),date=info['dates'][0][:10],src=src,team1=t1,team2=t2,
            runs1=a[0],balls1=a[1],wkts1=a[2],runs2=b[0],balls2=b[1],wkts2=b[2],rr1=rr1,rr2=rr2))
out.sort(key=lambda r:(r['date'],r['file']))
with open('ballstats.csv','w',newline='') as fh:
    w=csv.DictWriter(fh,fieldnames=list(out[0].keys()));w.writeheader();w.writerows(out)
print(len(out),sum(1 for r in out if r['rr1'] is None or r['rr2'] is None))
