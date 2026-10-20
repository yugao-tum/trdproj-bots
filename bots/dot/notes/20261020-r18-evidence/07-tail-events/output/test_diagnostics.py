import csv,json,math,hashlib
from pathlib import Path
import diagnose as d
root=Path(__file__).resolve().parent
assert d.dd([100,110,88,120]) == -.19999999999999996
assert d.qtile([0,10],.05)==.5
assert d.recovery([{'date':'2023-01-01','x':1},{'date':'2023-01-03','x':1},{'date':'2023-01-04','x':1}],1,'2023-01-01','2023-01-10','x')=={'right_censored':True}
assert d.recovery([{'date':'2023-01-01','x':1},{'date':'2023-01-02','x':1},{'date':'2023-01-03','x':1}],1,'2023-01-01','2023-01-10','x')['confirmed_day']=='2023-01-03'
x=json.loads((root/'diagnostics.json').read_text())
assert x['preregistration_sha256']=='28e32867ddab465daef3bf65092fdf11f79ab2ed6cbb09f963369a4bb3f94013'
path=root.parents[1]/'04-nav-engine/output/nav-panel.LOCAL-ONLY.csv'
assert hashlib.sha256(path.read_bytes()).hexdigest()==x['nav_input_sha256']
rows=list(csv.DictReader(path.open())); unit=[]
for r in rows:
 assert int(r['price_day'])==int(r['timestamp'])//86400*86400-86400
 v=float(r['unit_lp_usdc_zero'])*float(r['usdc_usd'])+float(r['unit_lp_usdt_zero'])*float(r['usdt_usd'])
 assert math.isclose(v,float(r['unit_lp_nav_zero']),rel_tol=1e-12)
 assert math.isclose(v*5/6,float(r['unit_lp_nav_max']),rel_tol=1e-12)
 unit.append(v)
assert math.isclose(d.dd(unit),x['nav']['full_sample_drawdown'],abs_tol=1e-14)
assert len(rows)==x['nav']['rows']
assert x['nav']['daily_adjacent_returns']==x['nav']['days']-1
assert x['nav']['event']['trough']['price_day']=='2023-03-11'
assert x['nav']['event']['recovery']['first_day']>x['nav']['event']['trough']['date']
(root/'tests.json').write_text(json.dumps({'assertion_groups':13,'all_passed':True,'scope':'synthetic quantiles/drawdown/recovery and immutable source hash; all 69798 rows as-of, reconstructed unit NAV and continuous sensitivity; result accounting. Not independent financial outcomes.'},indent=2)+'\n')
print('PASS 13 assertion groups; 69798-row arithmetic/as-of checks')
