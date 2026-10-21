#!/usr/bin/env python3
import csv, re, os
D=os.path.dirname(os.path.abspath(__file__)); os.chdir(D)
rows=list(csv.DictReader(open('primary_months.csv')))
changed=[r for r in rows if r['first_in_current']=='0']
print('months:',len(rows))
print('first-release settled bracket still contains current GISTEMP:',sum(r['first_in_current']=='1' for r in rows),'/',len(rows))
print('bracket changed:',len(changed),'/',len(rows))
for r in changed:
    print(' ',r['month'],'settled(first)=',r['settled_label'],'current=',r['current_gistemp'],'pred=',r['pred'])
print('model hit settled first-release:',sum(r['model_hit_settled']=='1' for r in rows),'/',len(rows))
print('model hit current bracket (not in CSV; from backtest object): see backtest_015.out')
# compare with merged Wayback proxy notes
print('\nWayback proxy (quoted from bots/quant/notes/scheduler/scratch/quant-015/firstrelease_local.out):')
for line in open('../quant-015/firstrelease_local.out'):
    if 'BRACKET CHANGE' in line: print(' ',line.strip())
