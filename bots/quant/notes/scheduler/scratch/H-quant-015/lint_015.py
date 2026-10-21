#!/usr/bin/env python3
"""Frontmatter + naming checks for quant-015 only (tools/check.py cannot run
globally in this worktree because bots/muse/entries/muse-700/701 lack fields)."""
import pathlib, re
ROOT=pathlib.Path(__file__).resolve().parents[6]
p=ROOT/'bots/quant/entries/quant-015-global-temp-era5-nowcast.md'
t=p.read_text(encoding='utf-8'); f={}
head=t.split('---',2)[1]
for line in head.splitlines():
    if ':' in line:
        k,_,v=line.partition(':'); f[k.strip()]=v.strip()
REQ=['id','name_zh','name_en','bot','date','market','pm_category','kind','improves','category','return_type','instruments','venues','data','test_2w','status','confidence']
problems=[]
for k in REQ:
    if not f.get(k): problems.append(f'missing {k}')
if f.get('id')!='quant-015' or not p.stem.startswith('quant-015-'): problems.append('id/filename')
if f.get('bot')!='quant': problems.append('bot dir')
if f.get('date')!='2026-10-20': problems.append('date changed')
if f.get('status')!='待核': problems.append('status changed')
if f.get('market') not in {'polymarket','crypto','prediction_other','other'}: problems.append('market')
if f.get('pm_category') not in {'finance','politics','tech','crypto','economics','weather','culture','mentions','sports','geopolitics','other','cross'}: problems.append('pm_category')
if f.get('kind') not in {'new','improvement','supplement'}: problems.append('kind')
if f.get('category') not in set('TRFESCAMVYXB')|{'?'}: problems.append('category')
if f.get('return_type') not in {'direction','convergence','carry','service','insurance','rent','vol_harvest','mixed','unknown'}: problems.append('return_type')
if f.get('confidence') not in {'高','中','低'}: problems.append('confidence')
print(f'quant-015 frontmatter: {"OK" if not problems else problems}')
print(f'date={f.get("date")} status={f.get("status")} (unchanged by this round)')
print(f'file lines={len(t.splitlines())} bytes={len(t.encode())}')
print('NOTE: global `python3 tools/check.py lint` currently fails in bots/muse/entries/muse-700/701 (missing frontmatter); unrelated to quant-015.')
