import ast, datetime, json, random, hashlib, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
# Pass a local copy of replay.py from the pinned source commit. No network.
raw=Path(sys.argv[1]).read_bytes()
assert hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest() == 'c7e0dc2fbcef98b9665517e79b56416a474994d0', 'Wrong source blob'
source=raw.decode('utf-8')
tree=ast.parse(source)
names={'simulate_ladder','settle'}
pure=ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[])
ns={'CAP_USDT':300.0,'FEE_RATE':0.04}
exec(compile(pure,'fixed-source-pure-functions','exec'),ns)
T=datetime.datetime(2026,1,1,tzinfo=datetime.timezone.utc)
D=datetime.timedelta
def pick(extra):
    books={k:[(T,p,1.)] for k,p in [(100,.2),(200,.3),(300,.4)]}
    if extra: books[300].append((T+D(days=1),.01,10000.))
    log=[]
    ns['simulate_ladder']('YES',books,{k:.5 for k in books},T,T+D(days=2),log)
    return sorted(k for ts,a,k,p in log if a=='decide' and ts<=T)
out={'synthetic_prefix':pick(False),'synthetic_appended_future':pick(True)}
assert out['synthetic_prefix']==out['synthetic_appended_future']==[100,200]
rng=random.Random(19); checks=0
for case in range(100):
    books={k:sorted([(T+D(seconds=rng.randrange(40)),rng.uniform(.05,.95),rng.uniform(1,10)) for _ in range(20)]) for k in [100,200,300,400]}
    limits={k:rng.uniform(.1,.9) for k in books}
    log=[]
    ns['simulate_ladder']('YES',books,limits,T,T+D(seconds=50),log)
    for cut in range(0,41,4):
        tr={k:[p for p in b if p[0]<=T+D(seconds=cut)] for k,b in books.items()}
        l=[]
        ns['simulate_ladder']('YES',tr,limits,T,T+D(seconds=50),l)
        assert [x for x in log if x[0]<=T+D(seconds=cut)]==[x for x in l if x[0]<=T+D(seconds=cut)]
        checks+=1
out['independent_synthetic_prefix_checks']=checks
# Execute only the exact output-construction loop from main with synthetic positions.
main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
loop=next(n for n in ast.walk(main) if isinstance(n,ast.For) and isinstance(n.target,ast.Name) and n.target.id=='k' and isinstance(n.iter,ast.Call) and isinstance(n.iter.func,ast.Name) and n.iter.func.id=='sorted' and any(isinstance(a,ast.Name) and a.id=='chosen' for a in n.iter.args))
code=compile(ast.Module(body=[loop],type_ignores=[]),'fixed-source-identity-loop','exec')
records=[]
for kind in ('YES','NO'):
    pos={'decision_ts':T,'decision_px':.2,'first_fill':T+D(seconds=1),'first_px':.3,'first_sz':1.,'cost':.3,'shares':1.,'n_prints':1}
    scope=dict(ns,chosen={100:pos.copy(),200:pos.copy()},mk={k:({'slug':f'synthetic-market-{k}','conditionId':f'synthetic-condition-{k}'},[],True) for k in [100,200]},m={'slug':'STALE_WRONG','conditionId':'STALE_WRONG'},kind=kind,limits={100:.5,200:.5},ev={'slug':'synthetic-event'},ev_fills=[],all_fills=[],print=lambda *a,**k:None)
    exec(code,scope)
    for r in scope['all_fills']:
        assert r['market']==f"synthetic-market-{r['strike']}"
        assert r['condition_id']==f"synthetic-condition-{r['strike']}"
        assert r['kind']==kind
        records.append({k:r[k] for k in ['market','condition_id','strike','kind']})
out['synthetic_identity_records']=records
out['scope']='Pure AST-extracted functions and output loop only; no imports of repository code, network, cached market data, or full replay.'
# Print only; do not overwrite frozen evidence.
print(json.dumps(out,indent=2))
