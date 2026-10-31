"""Independent unpenalized Table 4 Logit fits; no input data or definitions altered."""
from __future__ import annotations
import os
for _k in ['OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','OMP_NUM_THREADS','NUMEXPR_NUM_THREADS']: os.environ[_k]='1'
import argparse,json,hashlib,time,warnings,sys
from pathlib import Path
from datetime import datetime,timezone
import numpy as np
import pandas as pd
from scipy.special import expit
from scipy.linalg import cho_factor,cho_solve
from scipy.optimize import minimize,linprog
from scipy.stats import norm
ROOT=Path(__file__).resolve().parents[1]
PERIODS=['original_2006_2011','extended_2006_2023','new_2012_2023']
DEFAULT_OUT=ROOT/'results/table4_20261024/python'

def trim_pure_groups(frame,factors=('sic2','fyear')):
    """Remove only observed dummy groups with constant binary outcome; audit each row."""
    out=frame.copy();removed=[];trace=[];iteration=0
    while len(out):
        iteration+=1;drop=pd.Series(False,index=out.index);reason=pd.Series('',index=out.index,dtype=object)
        for factor in factors:
            gr=out.groupby(factor).payer.agg(['size','min','max'])
            for level,row in gr[gr['min'].eq(gr['max'])].iterrows():
                ix=out[factor].eq(level);label=f'pure_{factor}={int(level)}_y={int(row["min"])}'
                reason.loc[ix]=np.where(reason.loc[ix].eq(''),label,reason.loc[ix]+';'+label)
                drop|=ix;trace.append({'iteration':iteration,'factor':factor,'level':int(level),'outcome':int(row['min']),'N':int(row['size'])})
        if not drop.any():break
        gone=out.loc[drop,['event_id','gvkey','fyear']].copy();gone['reason']=reason.loc[drop];gone['iteration']=iteration;removed.append(gone)
        out=out.loc[~drop].copy()
    removed=pd.concat(removed,ignore_index=True) if removed else pd.DataFrame(columns=['event_id','gvkey','fyear','reason','iteration'])
    return out,removed,trace

def design_matrix(frame,regressors):
    """Stable reversible maxabs/L2 scaling; retain all declared columns."""
    data={name:frame[name].to_numpy(float) for name in regressors};bases={}
    for factor in ['sic2','fyear']:
        levels=sorted(frame[factor].unique());bases[factor]=int(levels[0])
        for level in levels[1:]:data[f'{int(level)}.{factor}']=frame[factor].eq(level).to_numpy(float)
    data['_cons']=np.ones(len(frame));names=list(data);X=np.column_stack(list(data.values()))
    if not np.isfinite(X).all():raise ValueError('Nonfinite design; input is not silently dropped')
    means=np.zeros(len(names));scales=np.ones(len(names))
    for j,name in enumerate(names):
        if name in regressors:
            absmax=float(np.max(np.abs(X[:,j])))
            if absmax:
                # No centering: otherwise subtracting an extreme mean erases ordinary values.
                scaled=X[:,j]/absmax;scaled_norm=float(np.linalg.norm(scaled)/np.sqrt(len(X)))
                scales[j]=absmax*scaled_norm if scaled_norm else absmax
    Z=X/scales
    check=Z/np.maximum(np.linalg.norm(Z,axis=0),1e-300)
    singular_values=np.linalg.svd(check,compute_uv=False)
    if singular_values[-1]<1e-12*singular_values[0]:
        raise ValueError('Declared design numerically rank deficient; no regressors silently omitted')
    return X,Z,names,means,scales,bases,[]

def unscale_transform(names,means,scales):
    T=np.diag(1/scales);c=names.index('_cons');T[c,:]=-means/scales;T[c,c]=1.
    return T

def loglike(beta,Z,y,offset=None):
    eta=Z@beta
    if offset is not None:eta=eta+offset
    return float(-np.logaddexp(0,-(2*np.asarray(y)-1)*eta).sum())

def score_information(beta,Z,y,offset=None):
    eta=Z@beta
    if offset is not None:eta=eta+offset
    p=expit(eta);pn=expit(-eta)
    residual=np.where(np.asarray(y)==1,pn,-p)
    weight=p*pn
    score=Z.T@residual;H=(Z.T*weight)@Z
    return eta,p,residual,weight,score,H

def fisher_solve(H,score,return_cov=False):
    diag=np.diag(H)
    if (diag<=0).any() or not np.isfinite(diag).all():raise np.linalg.LinAlgError('nonpositive Fisher diagonal')
    d=1/np.sqrt(diag);Hn=(H*d[:,None])*d[None,:]
    cf=cho_factor(Hn,lower=True,check_finite=False)
    step=d*cho_solve(cf,d*score,check_finite=False)
    if not return_cov:return step
    cov=(cho_solve(cf,np.eye(len(d)),check_finite=False)*d[:,None])*d[None,:]
    eig=np.linalg.eigvalsh(Hn)
    return step,cov,eig

def fit_logit(Z,y,maxiter=500,tol=1e-8,start=None,offset=None):
    """Unpenalized Newton MLE; tail-safe likelihood and dynamically scaled Fisher solve.

    A small ordinary score alone is insufficient for saturated extreme-ratio columns.
    Require a small Newton step AND score; preserve candidates that fail rather than penalizing.
    """
    y=np.asarray(y,float);p0=y.mean();beta=np.zeros(Z.shape[1]) if start is None else np.array(start,float).copy()
    if start is None:beta[-1]=np.log(p0/(1-p0))
    ll=loglike(beta,Z,y,offset);history=[];converged=False;message='iteration_limit';stepmax=np.inf
    for iteration in range(maxiter):
        eta,p,resid,w,score,H=score_information(beta,Z,y,offset)
        grad=float(np.max(np.abs(score)))
        try:step=fisher_solve(H,score)
        except np.linalg.LinAlgError as exc:message='singular_information: '+str(exc);break
        stepmax=float(np.max(np.abs(step)/(1+np.abs(beta))))
        decrement=float(score@step)
        history.append({'iteration':iteration,'ll':ll,'score_inf':grad,'newton_relative_step_inf':stepmax,'newton_decrement':decrement})
        if grad<tol and stepmax<1e-8:
            converged=True;message='score_and_Newton_step_tolerance';break
        alpha=1.;accepted=False
        for j in range(60):
            trial=beta+alpha*step;newll=loglike(trial,Z,y,offset)
            if np.isfinite(newll) and newll>=ll+1e-4*alpha*max(0,decrement)-2e-10:accepted=True;break
            alpha*=.5
        if not accepted:message='line_search_failed';break
        beta=trial;ll=newll
    eta,p,resid,w,score,H=score_information(beta,Z,y,offset)
    try:
        step,cov,eig=fisher_solve(H,score,return_cov=True)
        normalized_condition=float(eig[-1]/eig[0]);information_rank=Z.shape[1]
    except np.linalg.LinAlgError as exc:
        cov=np.full_like(H,np.nan);eig=np.array([np.nan,np.nan]);normalized_condition=np.inf;information_rank=-1;converged=False;message+='; '+str(exc)
    diag=np.diag(H);log_diag=np.log10(diag,where=diag>0,out=np.full_like(diag,-np.inf))
    return {'beta':beta,'cov':cov,'p':p,'eta':eta,'residual':resid,'weight':w,'ll':ll,'history':history,'converged':bool(converged),'message':message,'solver':'tail-safe Newton with dynamic Fisher scaling','iterations':len(history),'score_inf':float(np.max(np.abs(score))),'newton_relative_step_inf':stepmax,'hessian_eigen_min':float(eig[0]),'hessian_eigen_max':float(eig[-1]),'hessian_condition':normalized_condition,'hessian_condition_definition':'condition of diagonal-normalized information','information_rank':information_rank,'information_diag_log10_min':float(np.min(log_diag)),'information_diag_log10_max':float(np.max(log_diag)),'extreme_probability_N':int(((eta<-27.631)|(eta>27.631)).sum())}

def cluster_covariance(Z,y,p,cov,groups,residual=None):
    labels,unique=pd.factorize(np.asarray(groups),sort=True);G=len(unique);N,K=Z.shape
    cluster_score=np.zeros((G,K))
    residual=np.asarray(y)-p if residual is None else residual
    np.add.at(cluster_score,labels,Z*residual[:,None])
    v=cov@(cluster_score.T@cluster_score)@cov;v=(v+v.T)/2
    factor_g=G/(G-1) if G>1 else np.nan
    factor_full=factor_g*(N-1)/(N-K) if N>K else np.nan
    return v,G,factor_g,factor_full

def original_se(cov,names,means,scales):
    # sqrt BEFORE dividing: original variances may underflow although SE is representable.
    se=np.sqrt(np.maximum(np.diag(cov),0))/scales
    c=names.index('_cons');row=-means/scales;row[c]=1.
    se[c]=np.sqrt(max(0,float(row@cov@row)))
    return se

def ratio_diagnostics(Z,y,names,fit,scales,raw_ratio):
    """Independent starts and nuisance-reoptimized finite coefficient profile; no trimmed data."""
    j=names.index('delta_vega');multistart=[];profile=[]
    finite=np.abs(np.asarray(raw_ratio));nonzero=finite[finite>0]
    dyn=float(np.max(finite)/np.median(nonzero)) if len(nonzero) else 1.
    for factor in [.5,2.,0.]:
        start=fit['beta'].copy();requested=float(fit['beta'][j]*factor);start[j]=requested
        effective=float(start[j]);changed=bool(effective!=fit['beta'][j])
        f=fit_logit(Z,y,start=start,maxiter=500)
        multistart.append({'start_rule':'relative_ratio_coefficient','requested_multiplier':factor,'baseline_scaled_coef':float(fit['beta'][j]),'requested_start_scaled_coef':requested,'effective_start_scaled_coef':effective,'effective_changed_from_baseline':changed,'effective_multiplier':float(effective/fit['beta'][j]) if fit['beta'][j] else None,'ll':f['ll'],'coef_scaled':float(f['beta'][j]),'coef_original':float(f['beta'][j]/scales[j]),'converged':f['converged'],'iterations':f['iterations'],'score_inf':f['score_inf'],'newton_relative_step_inf':f['newton_relative_step_inf'],'nuisance_scaledcoef_max_abs_diff':float(np.max(np.abs(np.delete(f['beta']-fit['beta'],j)))),'nuisance_predictor_rms_diff':float(np.linalg.norm(Z[:,[k for k in range(Z.shape[1]) if k!=j]]@np.delete(f['beta']-fit['beta'],j))/np.sqrt(len(y)))})
    keep=[k for k in range(Z.shape[1]) if k!=j];B=Z[:,keep];start=fit['beta'][keep]
    candidate=float(fit['beta'][j])
    values=list(dict.fromkeys([0.,candidate,candidate*.5,candidate*2,candidate-1.,candidate+1.]))
    for value in values:
        f=fit_logit(B,y,start=start,offset=Z[:,j]*value,maxiter=300)
        profile.append({'coef_scaled':value,'coef_original':value/scales[j],'ll':f['ll'],'ll_loss_from_candidate':fit['ll']-f['ll'],'converged_nuisance':f['converged'],'iterations':f['iterations'],'nuisance_scaledcoef_max_abs_diff':float(np.max(np.abs(f['beta']-start)))})
    lls=[f['ll'] for f in multistart if np.isfinite(f['ll'])]+[fit['ll']]
    coefs=[f['coef_scaled'] for f in multistart if f['converged']]+[candidate]
    max_ll_gap=float(max(lls)-min(lls));coef_spread=float(max(coefs)-min(coefs))
    contributions=Z[:,j]*fit['residual'];denom=float(np.sum(np.abs(contributions)));info=float(np.sum(Z[:,j]**2*fit['weight']))
    tail_balance=abs(float(contributions.sum()))/denom if denom else np.nan
    original_info_log10=float(np.log10(info)+2*np.log10(scales[j])) if info>0 else -np.inf
    return {'tail_score_relative_balance':tail_balance,'raw_ratio_information_diag_log10':original_info_log10,'ratio_se_oim_original':float(np.sqrt(max(0,fit['cov'][j,j]))/scales[j]),'profile_zero_ll_loss':next(p['ll_loss_from_candidate'] for p in profile if p['coef_scaled']==0),'multistart_failed_N':sum(not m['converged'] for m in multistart),'raw_max_abs':float(np.max(finite)),'raw_nonzero_median_abs':float(np.median(nonzero)) if len(nonzero) else 0.,'raw_max_to_median':dyn,'extreme_dynamic_range':dyn>1e12,'multistart':multistart,'profile':profile,'multistart_ll_range':max_ll_gap,'multistart_scaled_coef_range':coef_spread,'interpretation_warning':'Extreme dynamic range makes ordinary Wald inference locally fragile; profile, tail scores, and original-unit uncertainty must be reviewed' if dyn>1e12 else None}

def separation_lp(Z,y):
    q=Z*(2*np.asarray(y)-1)[:,None]
    result=linprog(np.zeros(Z.shape[1]),A_ub=np.r_[-q,-q.sum(axis=0)[None,:]],b_ub=np.r_[np.zeros(len(q)),-1.],bounds=[(None,None)]*Z.shape[1],method='highs')
    return {'quasi_or_complete_separation_ray_found':bool(result.success),'lp_status':int(result.status),'lp_message':result.message}

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--out',type=Path,default=DEFAULT_OUT);parser.add_argument('--models',default='1,2,3,4,5,6,7,8,9,10');parser.add_argument('--versions',default='a,b');parser.add_argument('--periods',default=','.join(PERIODS));args=parser.parse_args();out=args.out
    for d in [out,out/'models',out/'samples']:d.mkdir(parents=True,exist_ok=True)
    spec=json.loads((ROOT/'table4_model_columns.json').read_text(encoding='utf-8'));records=[];metas=[];aliases=[]
    model_numbers=[int(s) for s in args.models.split(',')]
    for v in args.versions.split(','):
        for period in args.periods.split(','):
            file=ROOT/f'data/processed/table4_{v}_{period}.parquet';d=pd.read_parquet(file)
            if v=='b':
                assert d.sample_ab.eq(1).all() and (d.sample_log.astype(bool)==d.sample_ab_log.astype(bool)).all()
                aliases.extend({'alias':f'b_{period}_common_m{k:02d}','reuse':f'b_{period}_natural_m{k:02d}','reason':'identical input IDs and columns'} for k in model_numbers)
            for sample in (['natural','common'] if v=='a' else ['natural']):
                for model in model_numbers:
                    model_id=f'{v}_{period}_{sample}_m{model:02d}';started=time.time();base={'model_id':model_id,'version':v,'period':period,'sample':sample,'model':model}
                    logmodel=model in [3,9]
                    choose=d[(d.sample_ab_log if logmodel else d.sample_ab).eq(1)] if sample=='common' else d[d.sample_log.eq(1)] if logmodel else d
                    choose=choose.copy();N_input=len(choose)
                    used,removed,trace=trim_pure_groups(choose)
                    audit=choose[['event_id','gvkey','fyear']].copy();audit['used']=audit.event_id.isin(used.event_id);audit=audit.merge(removed[['event_id','reason']],on='event_id',how='left',validate='one_to_one');audit['reason']=audit.reason.fillna('retained')
                    audit.to_csv(out/'samples'/f'{model_id}_sample.csv.gz',index=False)
                    regressors=spec['models'][str(model)]['ceo_regressors']+spec['controls']
                    meta={**base,'N_input':N_input,'N_used':len(used),'dropped_pure_group_N':len(removed),'pure_group_trace':trace,'source_file':str(file.relative_to(ROOT)),'source_sha256':hashlib.sha256(file.read_bytes()).hexdigest()}
                    try:
                        X,Z,names,means,scales,bases,omitted=design_matrix(used,regressors);y=used.payer.to_numpy(float)
                        if not np.isin(y,[0,1]).all():raise ValueError('Nonbinary outcome')
                        result=fit_logit(Z,y);T=unscale_transform(names,means,scales);beta=T@result['beta'];vo=T@result['cov']@T.T
                        ratio_diag=ratio_diagnostics(Z,y,names,result,scales,used.delta_vega) if 'delta_vega' in names else None
                        cr0,G,fg,ff=cluster_covariance(Z,y,result['p'],result['cov'],used.gvkey,result['residual'])
                        vc0=T@cr0@T.T;vcg=vc0*fg;vcfull=vc0*ff
                        se=original_se(result['cov'],names,means,scales);sec0=original_se(cr0,names,means,scales);secg=sec0*np.sqrt(fg);secfull=sec0*np.sqrt(ff)
                        weak=bool(ratio_diag and ratio_diag['extreme_dynamic_range'])
                        reliable=bool(result['converged'] and not weak)
                        status='weak_ratio_identification' if weak and result['converged'] else 'optimizer_not_converged' if not result['converged'] else 'regular_MLE'
                        for j,term in enumerate(names):
                            z=beta[j]/se[j];zg=beta[j]/secg[j]
                            records.append({**base,'term':term,'coef':beta[j],'se_oim':se[j],'z_oim':z,'p_oim':2*norm.sf(abs(z)),'ci_oim_lo':beta[j]-norm.ppf(.975)*se[j],'ci_oim_hi':beta[j]+norm.ppf(.975)*se[j],'se_cluster':secg[j],'z_cluster':zg,'p_cluster':2*norm.sf(abs(zg)),'se_cluster_cr0':sec0[j],'se_cluster_full':secfull[j],'cluster_factor_g':fg,'cluster_factor_full':ff,'N':len(used),'N_clusters':G,'ll':result['ll'],'converged':result['converged'],'reliable':reliable,'estimation_status':status,'model_weak_ratio':weak,'weak_ratio_term':bool(weak and term=='delta_vega')})
                        fitcols=['converged','message','solver','iterations','score_inf','newton_relative_step_inf','information_diag_log10_min','information_diag_log10_max','hessian_eigen_min','hessian_eigen_max','hessian_condition','information_rank','extreme_probability_N']
                        nullp=y.mean();ll0=float(np.sum(y*np.log(nullp)+(1-y)*np.log1p(-nullp)))
                        meta.update({k:result[k] for k in fitcols});meta.update({'reliable':reliable,'estimation_status':status,'model_weak_ratio':weak,'weak_ratio_terms':['delta_vega'] if weak else [],'ratio_diagnostics':ratio_diag,'N_clusters':G,'K':len(names),'ll':result['ll'],'ll_null':ll0,'pseudo_r2':1-result['ll']/ll0,'base_sic2':bases['sic2'],'base_fyear':bases['fyear'],'design_columns':names,'omitted_columns':omitted,'numerical_means':means.tolist(),'numerical_scales':scales.tolist(),'numerical_scaling':'maxabs then RMS without centering, reversible reparameterization; original SE calculated sqrt before dividing to avoid variance underflow','cluster_factor_primary':fg,'cluster_factor_g':fg,'cluster_factor_full':ff,'cluster_factor_status':'Primary uses G/(G-1); CR0 and full OLS candidate retained for Stata reconciliation','history':result['history']})
                        if not result['converged']:meta['additional_separation_diagnostic']=separation_lp(Z,y)
                        pd.DataFrame({'event_id':used.event_id,'gvkey':used.gvkey,'fyear':used.fyear,'payer':y,'probability':result['p'],'linear_predictor':result['eta']}).to_csv(out/'samples'/f'{model_id}_fitted.csv.gz',index=False,float_format='%.17g')
                        np.savez_compressed(out/'models'/f'{model_id}_covariances.npz',coef=beta,cov_oim=vo,cov_cluster_cr0=vc0,cov_cluster_g=vcg,cov_cluster_full=vcfull,terms=np.array(names),coef_scaled=result['beta'],cov_oim_scaled=result['cov'],cov_cluster_cr0_scaled=cr0,transform=T,scales=scales)
                    except Exception as exc:
                        meta.update({'converged':False,'error_type':type(exc).__name__,'error':str(exc)})
                    meta['elapsed_seconds']=time.time()-started;metas.append(meta)
                    (out/'models'/f'{model_id}.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2,default=str),encoding='utf-8')
                    pd.DataFrame(records).to_csv(out/'coefficients.csv',index=False,float_format='%.17g')
                    pd.DataFrame([{k:z for k,z in m.items() if not isinstance(z,(dict,list))} for m in metas]).to_csv(out/'model_summary.csv',index=False)
                    print(json.dumps({**base,'N_input':N_input,'N_used':len(used),'converged':meta['converged'],'ll':meta.get('ll'),'score':meta.get('score_inf'),'error':meta.get('error'),'seconds':meta['elapsed_seconds']}),flush=True)
    manifest={'created_utc':datetime.now(timezone.utc).isoformat(),'engine':'Independent Python unpenalized exact Logit MLE; scaled Newton with original-unit transformation','models':len(metas),'converged':sum(m.get('converged',False) for m in metas),'reliable':sum(m.get('reliable',False) for m in metas),'weak_ratio_models':[m['model_id'] for m in metas if m.get('model_weak_ratio',False)],'data_unchanged':True,'penalty':'none','fixed_effects':'sic2 and fyear dummies plus intercept','separation_policy':'Only audited constant-outcome dummy groups removed to match Stata standard handling; no arbitrary observations trimmed','cluster_primary_factor':'G/(G-1); retained CR0 and full OLS alternative for exact reconciliation','aliases':aliases,'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'python':sys.version}
    (out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'finished':True,'models':len(metas),'converged':manifest['converged']}),flush=True)
if __name__=='__main__':main()
