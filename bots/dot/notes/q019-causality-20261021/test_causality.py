"""Offline synthetic diagnostic; no markets, downloads, or strategy replay."""
import ast, json, sys, hashlib
from datetime import datetime, timezone, timedelta
from pathlib import Path
p=Path(__file__).parent
# Pass the quant-authored replay.py from the pinned commit. No network or main execution.
raw=Path(sys.argv[1]).read_bytes()
assert hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest() == 'e604d19a0f3f14e4e119220bd6a5843e7b163039', 'Source must match pinned Git blob'
src=raw.decode('utf-8')
ns={'datetime':datetime,'timezone':timezone,'CAP_USDT':300,'FEE_RATE':.04}
mod=ast.Module(body=[n for n in ast.parse(src).body if isinstance(n,ast.FunctionDef) and n.name in ['fills_for','pick_adjacent']],type_ignores=[])
exec(compile(mod,'isolated-pure-functions','exec'),ns)
t=datetime(2026,1,1,tzinfo=timezone.utc)
def pick(extra):
    c=[]
    for k,px in [(100,.2),(200,.3),(300,.4)]:
        rows=[dict(timestamp=int(t.timestamp()),side='BUY',outcome='Yes',price=px,size=1)]
        if extra and k==300:
            rows.append(dict(timestamp=int((t+timedelta(days=1)).timestamp()),side='BUY',outcome='Yes',price=.01,size=10000))
        f=ns['fills_for']('YES',rows,t,t+timedelta(days=2),.5,False)
        c.append((k,f,.5-f['avg_price']))
    return [a[0] for a in ns['pick_adjacent'](c,2)]
r={'test':'same decision-time prefix, future print only in strike 300','synthetic_only':True,'prefix_selection':pick(False),'full_window_selection':pick(True),'selection_changed':pick(False)!=pick(True),'external_requests':0,'strategy_replays':0}
assert r['selection_changed']
(p/'q019-synthetic-causality.json').write_text(json.dumps(r,indent=2)+'\n')
print(json.dumps(r))
