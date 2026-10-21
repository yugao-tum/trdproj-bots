import pathlib,re,sys
root=pathlib.Path(__file__).resolve().parents[6]
p=root/'bots/quant/entries/quant-021-f1-pole-winner-base-rate.md'
t=p.read_text(); head=t.split('---',2)[1]; f={}
for line in head.splitlines():
    if ':' in line:
        k,_,v=line.partition(':'); f[k.strip()]=v.strip()
REQ=["id","name_zh","name_en","bot","date","market","pm_category","kind","improves","category","return_type","instruments","venues","data","test_2w","status","confidence"]
ok=True
def chk(cond,msg):
    global ok
    print(('PASS' if cond else 'FAIL'),msg)
    ok=ok and cond
chk(not [k for k in REQ if not f.get(k)],'all required fields present')
chk(f['bot']=='quant' and p.parent.parent.name=='quant','bot matches directory')
chk(p.stem.startswith(f['id']+'-'),'filename starts with id')
chk(re.fullmatch(r'quant-\d{3}',f['id']) is not None,'id format')
chk(f['market']=='polymarket','market')
chk(f['pm_category']=='sports','pm_category')
chk(f['kind']=='new' and f['improves']=='-','kind/improves')
chk(f['category']=='S' and f['return_type']=='direction','category/return_type')
chk(f['status'] in ('草稿','待核'),'status allowed: '+f['status'])
chk(f['date']=='2026-10-20','date unchanged')
chk(f['confidence'] in ('高','中','低'),'confidence')
chk(('### 1）' in t and '### 8）' in t),'evidence sections present')
chk('门槛自查' in t and '出处' in t,'gate/self-check + sources sections present')
print('\nentry lines',len(t.splitlines()),'chars',len(t))
sys.exit(0 if ok else 1)
