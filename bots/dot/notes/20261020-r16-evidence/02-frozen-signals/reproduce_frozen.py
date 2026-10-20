"""Independent deterministic VM signal reproduction; local frozen inputs only."""
from pathlib import Path
import json, hashlib, ast
import numpy as np
import pandas as pd
HERE=Path(__file__).resolve().parent
INPUT=HERE.parent/'01-freeze-inputs/output/panel_utc.csv'
SOURCE=Path('retained-inputs/competition-retrospective-20261020/quant-reproduce-readonly.py')
OUT=HERE/'output'
SYMS=['BTC','ETH','SOL']
FOLDS=[('fold2','2023-12-31','2024-12-29'),('fold3','2024-12-30','2025-12-29'),('fold4_truncated','2025-12-30','2026-09-30')]

def held(x):
    # Reset five-row anchor on each fold's own 250-day warm-up.
    return x.iloc[np.arange(len(x))//5*5].set_axis(x.index)

def independent(px):
    momentum=px.shift(1).div(px.shift(31))-1
    positive=momentum.gt(0).astype(float)
    raw=positive.div(positive.sum(axis=1).replace(0,np.nan),axis=0).fillna(0)
    ret=px.pct_change().fillna(0)
    sleeve=(held(raw).shift(1).fillna(0)*ret).sum(axis=1)
    weekly=sleeve.resample('W-FRI').sum()
    vol=weekly.rolling(4).std(ddof=1).mul(np.sqrt(52)).shift(1)
    scale=(.15/vol.reindex(px.index,method='ffill').replace(0,np.nan)).clip(0,1).fillna(0)
    base=held(raw.mul(scale,axis=0)).shift(1).fillna(0)
    return base,ret

def reference_namespace():
    # Audited computational functions only. Never execute module imports, downloader or main.
    tree=ast.parse(SOURCE.read_text())
    nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in {'freeze','apply','vm_weights'}]
    assert len(nodes)==3
    env={'np':np,'pd':pd,'REBAL':5}
    exec(compile(ast.Module(body=nodes,type_ignores=[]),str(SOURCE),'exec'),env)
    return env

def main():
    panel=pd.read_csv(INPUT)
    panel.index=pd.to_datetime(panel.pop('date_utc'),utc=True)
    assert panel.index.is_unique and panel.index.is_monotonic_increasing
    assert (panel.index.to_series().diff().dropna()==pd.Timedelta(days=1)).all()
    assert panel.notna().all().all()
    ref=reference_namespace(); signals=[]; returns=[]; metrics=[]; checks=[]
    for fid,start,end in FOLDS:
        start=pd.Timestamp(start,tz='UTC'); end=pd.Timestamp(end,tz='UTC'); warm=start-pd.Timedelta(days=250)
        px=panel.loc[warm:end,[s+'_close' for s in SYMS]].rename(columns={s+'_close':s for s in SYMS})
        assert px.index[0]==warm and px.index[-1]==end
        base,ret=independent(px)
        delta=float((base-ref['vm_weights'](px)).abs().to_numpy().max()); assert delta<1e-12
        for variant,n in [('VM_base',None),('VM_BTC_SMA50',50),('VM_BTC_SMA100_control',100),('VM_BTC_SMA200_control',200)]:
            gate=pd.Series(1.,index=px.index) if n is None else px.BTC.ge(px.BTC.rolling(n).mean()).astype(float).shift(1).fillna(1.)
            w=base.mul(gate,axis=0)
            assert (w>=0).all().all() and (w.sum(axis=1)<=1+1e-12).all()
            gross=(w*ret).sum(axis=1)
            turn=w.diff().abs().sum(axis=1).fillna(w.abs().sum(axis=1))
            f=pd.DataFrame({'fold_id':fid,'date_utc':px.index.strftime('%Y-%m-%dT00:00:00Z'),'variant':variant,'is_test':px.index>=start},index=px.index)
            for s in SYMS: f[s+'_weight']=w[s]; f['base_'+s+'_weight']=base[s]; f[s+'_asset_return']=ret[s]
            f['gate_lagged']=gate; f['base_rebalance_day']=(np.arange(len(px))>=1)&((np.arange(len(px))-1)%5==0)
            f['gross_return']=gross; f['original_turnover']=turn
            signals.append(f.reset_index(drop=True))
            for fee in [.001,.003,.006]:
                net=gross-turn*fee
                err=float((net-ref['apply'](w,px,fee)).abs().max()); assert err<1e-12
                test=net.loc[start:end]; nav=(1+test).cumprod(); dd=(nav/nav.cummax()-1).min()
                r=f[['fold_id','date_utc','variant','is_test','gross_return','original_turnover']].copy()
                r['fee_per_side']=fee; r['net_return']=net; r['test_nav']=nav.reindex(px.index)
                returns.append(r.reset_index(drop=True))
                metrics.append({'fold_id':fid,'variant':variant,'fee_per_side':fee,'days':len(test),'start':str(start.date()),'end':str(end.date()),'compound_return':nav.iloc[-1]-1,'cagr':nav.iloc[-1]**(365/len(test))-1,'original_dd_excludes_initial_nav':dd,'turnover_sum':float(turn.loc[start:end].sum()),'avg_exposure':float(w.loc[start:end].sum(axis=1).mean())})
            checks.append({'fold_id':fid,'variant':variant,'base_reference_max_abs_error':delta,'daily_gate_changes':int(gate.loc[start:end].diff().fillna(0).ne(0).sum()),'effective_weight_change_days':int(w.loc[start:end].diff().abs().sum(axis=1).gt(1e-12).sum())})
    sig=pd.concat(signals,ignore_index=True); sig.to_csv(OUT/'signals.csv',index=False,float_format='%.17g')
    sig[['fold_id','date_utc','variant','is_test']+[s+'_weight' for s in SYMS]].to_csv(OUT/'weights.csv',index=False,float_format='%.17g')
    pd.concat(returns,ignore_index=True).to_csv(OUT/'original_returns.csv',index=False,float_format='%.17g')
    pd.DataFrame(metrics).to_csv(OUT/'original_metrics.csv',index=False,float_format='%.17g')
    manifest={'input_sha256':hashlib.sha256(INPUT.read_bytes()).hexdigest(),'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'checks':checks,'scope':'fold2/fold3 complete; fold4 truncated at 2026-09-30; fold1 unavailable; no four-fold replication claim','fee_note':'0.001/0.003 opponent original; 0.006 preregistered stress, not original reported fee','accounting':'original constant-target weight return minus |delta target| fee; NOT a conserved-share/cash ledger','signals_sha256':hashlib.sha256((OUT/'signals.csv').read_bytes()).hexdigest()}
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({'rows':len(sig),'signals_sha256':manifest['signals_sha256'],'checks':checks},indent=2))
if __name__=='__main__':main()
