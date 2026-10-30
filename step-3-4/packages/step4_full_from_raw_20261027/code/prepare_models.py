"""Prepare all 25 Table 4 models from reconstructed annual-B and matched data.

No saved per-model DTA, score training, fitted coefficient, or saved e(sample)
is used to construct a regression input. Frozen references are assertions only.
Run with --help for paths. Requires numpy, pandas and pyarrow; Stata is optional
for preparation and required for --run-stata.
"""
from __future__ import annotations
import os
for name in ['OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','OMP_NUM_THREADS','NUMEXPR_NUM_THREADS']:
    os.environ[name] = '1'
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
from datetime import datetime, timezone
import numpy as np
import pandas as pd

CONTROLS = ['age','ln_tenure','rd_at_pct','rd_missing','capx_at_pct',
            'asset_growth','mb','profitability_m','size_pct','re_at','retvol255']
SETTINGS = {'m08':['cash_m','inside_debt_m','equity_m','vega_k'],
            'm09':['cash_m','ln_rellev','equity_m','vega_k'],
            'm10':['cash_m','high_rellev','equity_m','vega_k'],
            'm00':['cash_m','equity_m']}

def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(8*1024*1024), b''):
            h.update(block)
    return h.hexdigest()

def write_json(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2,
                                    default=str), encoding='utf8')

def trim_pure_groups(frame, factors=('sic2','fyear')):
    """Original simultaneous-factor iterative pure-group deletion, with audit."""
    out=frame.copy();removed=[];trace=[];iteration=0
    while len(out):
        iteration+=1
        drop=pd.Series(False,index=out.index)
        reason=pd.Series('',index=out.index,dtype=object)
        for factor in factors:
            gr=out.groupby(factor).payer.agg(['size','min','max'])
            for level,row in gr[gr['min'].eq(gr['max'])].iterrows():
                ix=out[factor].eq(level)
                label=f'pure_{factor}={int(level)}_y={int(row["min"])}'
                reason.loc[ix]=np.where(reason.loc[ix].eq(''),label,
                                         reason.loc[ix]+';'+label)
                drop|=ix
                trace.append({'iteration':iteration,'factor':factor,
                              'level':int(level),'outcome':int(row['min']),
                              'N':int(row['size'])})
        if not drop.any():
            break
        gone=out.loc[drop,['event_id','gvkey','fyear']].copy()
        gone['reason']=reason.loc[drop];gone['iteration']=iteration
        removed.append(gone)
        out=out.loc[~drop].copy()
    removed=pd.concat(removed,ignore_index=True) if removed else pd.DataFrame(
        columns=['event_id','gvkey','fyear','reason','iteration'])
    return out,removed,trace

def design(frame, regressors):
    """Original reversible maxabs/L2 RMS reparameterization; no centering."""
    data={name:frame[name].to_numpy(float) for name in regressors};bases={}
    for factor in ['sic2','fyear']:
        levels=sorted(frame[factor].unique());bases[factor]=int(levels[0])
        for level in levels[1:]:
            data[f'{int(level)}.{factor}']=frame[factor].eq(level).to_numpy(float)
    data['_cons']=np.ones(len(frame));names=list(data)
    X=np.column_stack(list(data.values()))
    if not np.isfinite(X).all():
        raise ValueError('Nonfinite design; required values are never silently dropped')
    scales=np.ones(len(names))
    for j,name in enumerate(names):
        if name in regressors:
            absmax=float(np.max(np.abs(X[:,j])))
            if absmax:
                scaled=X[:,j]/absmax
                scaled_norm=float(np.linalg.norm(scaled)/np.sqrt(len(X)))
                scales[j]=absmax*scaled_norm if scaled_norm else absmax
    Z=X/scales
    check=Z/np.maximum(np.linalg.norm(Z,axis=0),1e-300)
    singular=np.linalg.svd(check,compute_uv=False)
    if singular[-1]<1e-12*singular[0]:
        raise ValueError('Declared design rank deficient; no regressor silently omitted')
    return names,scales,bases

def jobs_from_data(annual, matched):
    assert annual.event_id.is_unique and matched.event_id.is_unique
    assert annual.formula_version.eq('B_standard_finance').all()
    assert annual.fyear.between(2006,2023).all()
    if 'sample_log' not in annual or 'sample_log' not in matched:
        raise ValueError('Required upstream sample_log selection flag absent')
    cohorts={
        'original_2006_2011':annual.loc[annual.fyear.between(2006,2011)].copy(),
        'extended_2006_2023':annual.copy(),
        'new_2013_2023':annual.loc[annual.fyear.between(2013,2023)].copy()}
    strict=matched.loc[matched.official_strict_period_match.fillna(False)
                       &matched.fyear.between(2013,2023)].copy()
    for model in ['ridge','xgboost']:
        raw=strict['vendor_strict_risk_score_'+model].to_numpy(float)
        if not np.isfinite(raw).all():
            raise ValueError('Accepted score missing; never impute score zero')
        strict[model+'_clip0_pp']=100*np.maximum(raw,0)
    cohorts['scores_2013_2023']=strict
    jobs=[]
    for period,prefix in [('original_2006_2011','rep_original_2006_2011'),
                          ('extended_2006_2023','rep_extended_2006_2023'),
                          ('new_2013_2023','rep_2013_2023')]:
        for setting in ['m08','m09','m10']:
            jobs.append(dict(model_id=prefix+'_'+setting,table_group='replication',
                             version='b',period=period,score_model=None,
                             setting=setting,score_column=None,
                             regressors=SETTINGS[setting]+CONTROLS,
                             cohort=period))
    for group in ['no_rd','with_rd']:
        controls=[c for c in CONTROLS if group=='with_rd'
                  or c not in ['rd_at_pct','rd_missing']]
        for model in ['xgboost','ridge']:
            for setting in ['m08','m09','m10','m00']:
                jobs.append(dict(model_id=f'score_{model}_{group}_{setting}',
                                 table_group=group,version='b',period='2013_2023',
                                 score_model=model,setting=setting,
                                 score_column=model+'_clip0_pp',
                                 regressors=['rd_score']+SETTINGS[setting]+controls,
                                 cohort='scores_2013_2023'))
    return cohorts,jobs

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--annual-b',type=Path,required=True,
                        help='Reconstructed full annual-B 2006-2023 parquet')
    parser.add_argument('--matched',type=Path,required=True,
                        help='Reconstructed matched annual-B parquet (all base rows)')
    parser.add_argument('--output',type=Path,required=True,
                        help='Fresh generated regression output directory')
    parser.add_argument('--reference',type=Path,default=Path(__file__).parent/'model_reference.json',
                        help='Frozen declarations for assertions only')
    parser.add_argument('--run-stata',action='store_true')
    parser.add_argument('--stata',default=os.environ.get('STATA_EXE'),
                        help='Stata executable; needed when --run-stata')
    args=parser.parse_args()
    output=args.output.resolve()
    if output.exists() and any(output.iterdir()):
        raise FileExistsError('Use a fresh --output directory: '+str(output))
    for sub in ['input','audit','stata/inputs','stata/samples','stata/estimates',
                'stata/covariances']:
        (output/sub).mkdir(parents=True,exist_ok=True)
    annual=pd.read_parquet(args.annual_b)
    matched=pd.read_parquet(args.matched)
    cohorts,jobs=jobs_from_data(annual,matched)
    frozen=json.loads(args.reference.read_text(encoding='utf-8-sig'))
    refs={m['model_id']:m for m in frozen['models']}
    if set(refs)!={j['model_id'] for j in jobs}:
        raise ValueError('Reference does not describe the same 25 declared models')
    for name,frame in cohorts.items():
        frame.reset_index(drop=True).to_parquet(output/'input'/f'{name}.parquet',index=False)
    blocks=[];checks=[];models=[]
    for job in jobs:
        mid=job['model_id'];ref=refs[mid]
        frame=cohorts[job['cohort']].copy()
        if job['setting']=='m09':
            frame=frame.loc[frame.sample_log.eq(1)].copy()
        if job['score_model']:
            frame['rd_score']=frame[job['score_column']].to_numpy(copy=True)
        used,removed,trace=trim_pure_groups(frame)
        names,scales,bases=design(used,job['regressors'])
        core_scales=scales[:len(job['regressors'])]
        assert job['regressors']==ref['regressors'],mid
        assert len(frame)==ref['N_input'] and len(used)==ref['N_used'],mid
        assert bases['sic2']==ref['base_sic2'] and bases['fyear']==ref['base_fyear'],mid
        assert names==ref['design_columns'],mid
        np.testing.assert_allclose(scales,ref['numerical_scales'],rtol=2e-12,atol=1e-14,
                                   err_msg=mid+': reconstructed scales differ')
        expected_ids_hash=hashlib.sha256('\n'.join(sorted(used.event_id)).encode()).hexdigest()
        assert expected_ids_hash==ref['used_ids_sha256'],mid+': different e(sample) IDs'
        dta=frame[['event_id','gvkey','fyear','sic2','payer','sample_log']
                  +job['regressors']].copy().reset_index(drop=True)
        # Inputs are pre-pure-group; m09 is already positive-relative-leverage.
        dta.to_stata(output/'stata/inputs'/f'{mid}.dta',write_index=False,version=118)
        sample=frame[['event_id','gvkey','fyear','payer']].copy()
        sample['used']=sample.event_id.isin(used.event_id)
        sample=sample.merge(removed[['event_id','reason']],on='event_id',how='left',validate='1:1')
        sample['reason']=sample.reason.fillna('retained')
        sample.to_csv(output/'audit'/f'{mid}_selection.csv',index=False,float_format='%.17g')
        item={**job,'N_input':len(frame),'N_used':len(used),
              'N_clusters':int(used.gvkey.nunique()),'base_sic2':bases['sic2'],
              'base_fyear':bases['fyear'],'design_columns':names,
              'numerical_scales':scales.tolist(),'pure_group_trace':trace,
              'input_file':f'inputs/{mid}.dta','used_ids_sha256':expected_ids_hash}
        y=used.payer.to_numpy(float);ym=float(y.mean())
        item['ll_null']=float(np.sum(y*np.log(ym)+(1-y)*np.log1p(-ym)))
        models.append(item)
        checks.append({'model_id':mid,'input_N':len(frame),'used_N':len(used),
                       'N_clusters':item['N_clusters'],'declarations_match':True,
                       'used_ids_match':True,'max_scale_relative_error':float(np.max(
                           np.abs(scales-np.asarray(ref['numerical_scales']))/
                           np.maximum(1,np.abs(ref['numerical_scales']))))})
        values={'MID':mid,'V':'b','PER':job['period'],'SM':'natural',
                'M':str(int(job['setting'][1:])),
                'SOURCE':f'./inputs/{mid}.dta','XVARS':' '.join(job['regressors']),
                'SCALES':' '.join(format(x,'.17g') for x in core_scales),
                'NINPUT':str(len(frame)),'NUSED':str(len(used)),
                'BSIC':str(bases['sic2']),'BYEAR':str(bases['fyear'])}
        block='\n'.join('global '+key+' "'+val+'"' for key,val in values.items())
        block+='\ncapture noisily table4fit\nlocal modelrc=_rc\nif `modelrc\'!=0 {\n'
        block+='    global REPLAY_FAILURES = $REPLAY_FAILURES + 1\n'
        block+='    post PCEOT4META ("$MID") ("$V") ("$PER") ("$SM") ($M) ("stata_command_error") ($NINPUT) ($NUSED) (.) (.) (.) (.) (.) (.) (.) (`modelrc\') ($BSIC) ($BYEAR) (.) (.)\n}\n'
        blocks.append(block)
    template=(Path(__file__).parent/'stata_engine_template.do').read_text(encoding='utf8')
    assert template.count('@@MODEL_BLOCKS@@')==1
    (output/'stata/RUN_MODELS.do').write_text(template.replace('@@MODEL_BLOCKS@@',
                                                             '\n\n'.join(blocks)),encoding='utf8')
    write_json(output/'model_specifications.json',{'models':models,
        'input_sources':{'annual_b_sha256':sha(args.annual_b),'matched_sha256':sha(args.matched)},
        'created_utc':datetime.now(timezone.utc).isoformat(),
        'score_retraining':False,'origin':'New DTA constructed from rebuilt data, no frozen model DTA read'})
    write_json(output/'audit/PREPARATION_QA.json',{'passed':True,'models':len(models),
        'checks':checks,'annual_B_rows':len(annual),'strict_score_rows':len(cohorts['scores_2013_2023'])})
    if args.run_stata:
        if not args.stata:
            raise ValueError('Provide --stata or STATA_EXE to run Stata')
        exe=shutil.which(args.stata) or args.stata
        command=[exe,'/e','do','RUN_MODELS.do'] if os.name=='nt' else [exe,'-b','do','RUN_MODELS.do']
        flags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0
        result=subprocess.run(command,cwd=output/'stata',creationflags=flags)
        if result.returncode!=0 or not (output/'stata/run_finished.txt').exists():
            raise RuntimeError('Stata replay failed; inspect '+str(output/'stata/regression.log'))
    print(json.dumps({'passed':True,'models':len(models),'output':str(output),
                      'run_stata':args.run_stata},indent=2))

if __name__=='__main__':
    main()
