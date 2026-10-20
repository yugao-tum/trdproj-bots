"""r17 preregistered continuous SMA50 signals. No returns or ledger results read."""
from pathlib import Path
import hashlib,json,ast
import numpy as np
import pandas as pd
O=Path(__file__).resolve().parent
R16=O.parents[2]/'r16-proposal'
P=R16/'01-freeze-inputs/output/panel_utc.csv'
S=R16/'02-frozen-signals/reproduce_frozen.py'
SYMS=['BTC','ETH','SOL']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def held(x):return x.iloc[np.arange(len(x))//5*5].set_axis(x.index)
def compute(px):
    mom=px.shift(1).div(px.shift(31))-1
    pos=mom.gt(0).astype(float)
    raw=pos.div(pos.sum(axis=1).replace(0,np.nan),axis=0).fillna(0)
    ret=px.pct_change().fillna(0)
    sleeve=(held(raw).shift(1).fillna(0)*ret).sum(axis=1)
    weekly=sleeve.resample('W-FRI').sum()
    vol=weekly.rolling(4).std(ddof=1).mul(np.sqrt(52)).shift(1)
    scale=(.15/vol.reindex(px.index,method='ffill').replace(0,np.nan)).clip(0,1).fillna(0)
    base=held(raw.mul(scale,axis=0)).shift(1).fillna(0)
    gate=px.BTC.ge(px.BTC.rolling(50).mean()).astype(float).shift(1).fillna(1.)
    f=pd.DataFrame(index=px.index)
    for s in SYMS:f['base_'+s+'_weight']=base[s]
    for s in SYMS:f[s+'_weight']=base[s]*gate
    f['gate_lagged']=gate
    f['base_rebalance_day']=(np.arange(len(px))>=1)&((np.arange(len(px))-1)%5==0)
    return f

def main():
    assert sha(P)=='a3b601644697f778990fcfdcc2ff1143140d5373c33d871ff81536d493891f79'
    p=pd.read_csv(P,index_col='date_utc');p.index=pd.to_datetime(p.index,utc=True)
    px=p.loc['2023-04-26':'2026-09-30',[s+'_close' for s in SYMS]].rename(columns={s+'_close':s for s in SYMS})
    assert len(px)==1254 and px.notna().all().all()
    assert (px.index.to_series().diff().dropna()==pd.Timedelta(days=1)).all()
    f=compute(px);cols=[c for c in f if c!='base_rebalance_day']
    # r16 computational parity; no execution of source imports, main, network or reporting.
    nodes=[n for n in ast.parse(S.read_text()).body if isinstance(n,ast.FunctionDef) and n.name in ['held','independent']]
    env={'np':np,'pd':pd};exec(compile(ast.Module(body=nodes,type_ignores=[]),str(S),'exec'),env)
    ref,_=env['independent'](px)
    parity=float(np.max(np.abs(ref.to_numpy()-f[['base_'+s+'_weight' for s in SYMS]].to_numpy())))
    assert parity==0
    checks=[]
    # Every execution d: no actual d close is supplied, only <=d-1 history plus a dummy row.
    for i in range(1,len(px)):
        prefix=px.iloc[:i+1].copy();prefix.iloc[-1]=px.iloc[i-1]*1.731
        g=compute(prefix)
        error=float(np.abs(g.iloc[-1][cols].astype(float)-f.iloc[i][cols].astype(float)).max())
        assert error<1e-12,(str(px.index[i]),error)
        checks.append({'execution_date_utc':px.index[i].strftime('%Y-%m-%d'),'max_abs_error':error})
    perturb=[]
    for date in ['2023-12-29','2024-01-01','2024-12-31','2025-01-03','2025-12-31','2026-09-30']:
        d=pd.Timestamp(date,tz='UTC');mut=px.copy();mask=mut.index>=d
        mut.loc[mask]=mut.loc[mask].mul(np.array([2.1,.41,3.7]),axis=1)
        g=compute(mut);error=float(np.abs(g.loc[:d,cols].to_numpy(dtype=float)-f.loc[:d,cols].to_numpy(dtype=float)).max())
        assert error<1e-12
        perturb.append({'execution_date_utc':date,'mutated_from_execution_close_onward':True,'max_historical_abs_error':error})
    f.insert(0,'is_test',f.index>=pd.Timestamp('2024-01-01',tz='UTC'))
    f.insert(0,'variant','VM_BTC_SMA50')
    f.insert(0,'execution_date_utc',f.index.strftime('%Y-%m-%dT00:00:00Z'))
    f.insert(0,'decision_date_utc',(f.index-pd.Timedelta(days=1)).strftime('%Y-%m-%dT00:00:00Z'))
    f.insert(0,'date_utc',f.index.strftime('%Y-%m-%dT00:00:00Z'))
    assert f.is_test.sum()==1004
    assert f[['BTC_weight','ETH_weight','SOL_weight']].sum(axis=1).le(1+1e-12).all()
    f.to_csv(O/'signals.csv',index=False,float_format='%.17g')
    f.loc[f.base_rebalance_day,['date_utc','decision_date_utc','is_test']].to_csv(O/'phase_sequence.csv',index=False)
    test={'status':'PASS','daily_prefix_tests':len(checks),'max_prefix_error':max(x['max_abs_error'] for x in checks),'r16_base_parity_max_abs_error':parity,'future_perturbations':perturb,'daily_checks':checks}
    (O/'causal-tests.json').write_text(json.dumps(test,indent=2)+'\n')
    boundary=f.loc[['2023-04-26','2024-01-01','2026-09-30']].reset_index(drop=True).to_dict(orient='records')
    (O/'boundaries.json').write_text(json.dumps(boundary,indent=2)+'\n')
    schema={'columns':list(f.columns),'rows':len(f),'warmup_rows':250,'test_rows':1004,'timezone':'UTC','booleans':['is_test','base_rebalance_day'],'date_label_note':'decision_date labels prior daily candle; decision becomes available after its close, execution references next daily first trade, not a proven fill','phase_anchor':'2023-04-26','effective_base_phase':'i >= 1 and (i-1) modulo 5 = 0','extra_shift_allowed':False}
    (O/'schema.json').write_text(json.dumps(schema,indent=2)+'\n')
    manifest={'model':'unknown','agent_provider':'native OpenAI','new_mechanisms':0,'mechanism':'quant-001 / T-T2-vm supplement','classification':'conditional_simulation inputs only; no returns evaluated','inputs':{str(P):sha(P),str(S):sha(S),str(O.parents[1]/'INTERFACES.md'):sha(O.parents[1]/'INTERFACES.md')},'code_sha256':sha(Path(__file__)),'outputs':{n:sha(O/n) for n in ['signals.csv','phase_sequence.csv','causal-tests.json','boundaries.json','schema.json','RESULT.md']},'local_only':['signals.csv','phase_sequence.csv'],'publication_allowlist':['generate_signals.py','manifest.json','schema.json','causal-tests.json','boundaries.json','RESULT.md']}
    (O/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({'signals_sha256':manifest['outputs']['signals.csv'],'rows':len(f),'daily_tests':len(checks),'boundaries':boundary},indent=2))
if __name__=='__main__':main()
