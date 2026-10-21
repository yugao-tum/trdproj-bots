import json,datetime as dt
M=json.load(open('_cache/winner_map.json')); S=json.load(open('_cache/schedule.json'))
def ts(date,t):
    if not date: return None
    return int(dt.datetime.fromisoformat(date+'T'+(t or '00:00:00').replace('Z','+00:00')).timestamp())
rows=[];leak=[]
for k,x in sorted(M.items()):
    r=x['race']; s=S[k]
    rd=r['date']; rstart=ts(rd,r.get('time') or '00:00:00Z')
    cut_race=ts(rd,'00:00:00Z')
    qs=ts(s.get('qual_date'),s.get('qual_time'))
    # qualifying session ends roughly 1h after start; require data published 2h after start
    cut_q=qs+2*3600 if qs else None
    cut=max(cut_race,cut_q) if cut_q else cut_race
    rows.append((k,r['name'],rd,s.get('qual_date'),s.get('qual_time'),cut_race,cut_q,cut,rstart))
    if cut_q and cut_q>cut_race: leak.append(rows[-1])
print('events',len(rows),'race_start<=qual_cut?',sum(1 for z in rows if z[8]<=z[7]))
print('cutoff moved later by qualifying time:',len(leak))
for z in leak: print('  ',z[0],z[1],'race',z[2],'qual',z[3],z[4],'cut_race',dt.datetime.utcfromtimestamp(z[5]),'cut_q',dt.datetime.utcfromtimestamp(z[6]),'start',dt.datetime.utcfromtimestamp(z[8]))
print('\nall events cut_q>cut_race or race start check:')
for z in rows:
    tag='LEAK' if z[6] and z[6]>z[5] else ''
    print(f'{z[0]:>8} {z[1][:28]:28} qual={z[4] or "-":>9} d={z[3] or "-"} cut_race={dt.datetime.utcfromtimestamp(z[5]):%m-%d %H:%M} cut_q={dt.datetime.utcfromtimestamp(z[6]) if z[6] else None!s:>16} start={dt.datetime.utcfromtimestamp(z[8]):%m-%d %H:%M} {tag}')
json.dump([{'key':z[0],'cut':z[7],'cut_race':z[5],'cut_q':z[6],'start':z[8]} for z in rows],open('_cache/v3_cuts.json','w'),indent=0)
