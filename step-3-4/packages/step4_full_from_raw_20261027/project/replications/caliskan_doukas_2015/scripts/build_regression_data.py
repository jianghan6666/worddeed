"""Build Table 4 data. Stages prepare/finalize/all; never estimate regressions."""
from __future__ import annotations
import argparse,json,hashlib,sys
from datetime import datetime,timezone
from importlib.metadata import version
from pathlib import Path
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'data/raw'; INT=ROOT/'data/interim'; OUT=ROOT/'data/processed'; AUD=ROOT/'audits'; REPORT=ROOT/'reports'
CONFIG=json.loads((ROOT/'build_config.json').read_text(encoding='utf-8'))

# These fields document a frozen research specification, not silent toggles.
_FIXED_SPEC={'original_years':[2006,2011],'extended_years':[2006,2023],'new_years':[2012,2023],
 'industry_exclusions':[[4900,4999],[6000,6999]],'fiscal_end_ceo':True,
 'duplicate_funda_policy':'exclude_all_ambiguous_gvkey_fyear','ambiguous_link_policy':'exclude_distinct_permno_conflicts',
 'industry_source':'sich_only','winsorization':'none','high_leverage_threshold':1,
 'size_reference':'eligible_ExecuComp_Compustat_CRSP_universe_before_complete_case',
 'profitability':'ib-dvp+txditc in Compustat USD millions',
 'tenure':'1+floor((datadate-becameceo).days/365.25)',
 'rd_missing':'indicator before ratio fill0; no other automatic fill0',
 'options_count_tolerance_thousands':0.01,'formula_versions':['paper_literal_diagnostic','standard_finance'],
 'ccm_source':'ccmxpf_lnkhist_postgres_all.csv.gz','popsrc_status':'exact_supplement_join_then_filter_D','regressions':False}
for _key,_expected in _FIXED_SPEC.items():
    if CONFIG.get(_key)!=_expected:
        raise ValueError(f'Frozen specification {_key} changed; update implementation and tests explicitly.')


def write_json(path,obj):
    path.write_text(json.dumps(obj,ensure_ascii=False,indent=2,default=str)+'\n',encoding='utf-8')

def numeric(frame,cols):
    for col in cols:
        frame[col]=pd.to_numeric(frame[col],errors='coerce')
    return frame

def safe_ratio(a,b,positive=False):
    ok=np.isfinite(a)&np.isfinite(b)&(b.gt(0) if positive else b.ne(0))
    return a.div(b).where(ok)

def prepare():
    for d in [INT,OUT,AUD,REPORT]: d.mkdir(parents=True,exist_ok=True)
    f=pd.read_csv(RAW/'compustat/funda_datadate_2003-01_2024-06.csv.gz',dtype={'gvkey':str},low_memory=False)
    f['datadate']=pd.to_datetime(f.datadate,errors='coerce'); f['fyear']=pd.to_numeric(f.fyear,errors='coerce')
    pop=pd.read_csv(RAW/'compustat/funda_population_keys_all.csv.gz',dtype={'gvkey':str},low_memory=False)
    pop['datadate']=pd.to_datetime(pop.datadate,errors='coerce')
    popkeys=['gvkey','datadate','indfmt','consol','datafmt','curcd']
    assert not pop.duplicated(popkeys).any(), 'Ambiguous population-source keys'
    f=f.merge(pop[popkeys+['popsrc']],on=popkeys,how='left',validate='one_to_one')
    write_json(AUD/'funda_population_match.json',{'raw_financial_rows':len(f),'matched_rows':int(f.popsrc.notna().sum()),'population_counts':f.popsrc.fillna('MISSING').value_counts().to_dict(),'supplement_file':'funda_population_keys_all.csv.gz','join_keys':popkeys})
    if f.popsrc.isna().any(): raise ValueError('Unmatched population-source rows; audit before proceeding')
    f=f[f.popsrc.eq('D')].copy()
    dup=f.duplicated(['gvkey','fyear'],keep=False)
    f.loc[dup].to_csv(AUD/'ambiguous_funda_fiscal_years.csv',index=False)
    bad_funda_keys=set(zip(f.loc[dup,'gvkey'],f.loc[dup,'fyear']))
    f=f.loc[~dup & f.fyear.notna()].copy(); f['fyear']=f.fyear.astype(int)
    assert not f.duplicated(['gvkey','fyear']).any()
    # No missing-to-zero substitutions in book equity or profitability.
    f['market_equity_m']=f.prcc_f*f.csho
    f['shareholder_equity_m']=f.seq.combine_first(f.ceq+f.pstk).combine_first(f['at']-f['lt'])
    f['preferred_equity_m']=f.pstkl.combine_first(f.pstkrv).combine_first(f.pstk)
    f['book_equity_m']=f.shareholder_equity_m-f.preferred_equity_m+f.txditc
    f['mb']=safe_ratio(f.market_equity_m,f.book_equity_m)
    f['profitability_m']=f.ib-f.dvp+f.txditc
    f['profitability_txdi_m']=f.ib-f.dvp+f.txdi
    f['rd_missing']=f.xrd.isna().astype('int8')
    f['rd_at_pct']=100*safe_ratio(f.xrd.fillna(0),f['at'],positive=True)
    f['capx_at_pct']=100*safe_ratio(f.capx,f['at'],positive=True)
    f['re_at']=safe_ratio(f.re,f['at'],positive=True)
    f['firm_leverage']=safe_ratio(f['lt'],f.market_equity_m,positive=True)
    f['dvy']=safe_ratio(f.dvpsx_f,f.prcc_f,positive=True).where(f.dvpsx_f.ge(0))
    f['payer']=np.where(f.dvpsx_f.notna(),f.dvpsx_f.gt(0).astype(float),np.nan)
    for k in [1,2,3]:
        lag=f[['gvkey','fyear','dvy','datadate']].copy(); lag['fyear']+=k
        lag=lag.rename(columns={'dvy':f'dvy_lag{k}','datadate':f'dvy_date_lag{k}'})
        f=f.merge(lag,on=['gvkey','fyear'],how='left',validate='one_to_one')
        f.loc[f[f'dvy_date_lag{k}'].ge(f.datadate),f'dvy_lag{k}']=np.nan
    prev=f[['gvkey','fyear','at','datadate']].copy();prev['fyear']+=1
    prev=prev.rename(columns={'at':'lag_at','datadate':'lag_at_date'})
    f=f.merge(prev,on=['gvkey','fyear'],how='left',validate='one_to_one')
    f['asset_growth']=safe_ratio(f['at']-f.lag_at,f.lag_at,positive=True).where(f.lag_at_date.lt(f.datadate))
    f['dividend_history_complete']=f[['dvy_lag1','dvy_lag2','dvy_lag3']].notna().all(axis=1)
    f['d']=np.log1p(f[['dvy_lag1','dvy_lag2','dvy_lag3']].mean(axis=1)).where(f.dividend_history_complete)
    cols=['gvkey','year','execid','co_per_rol','exec_fullname','ceoann','age','becameceo','leftofc','joined_co','salary','bonus','shrown_excl_opts','stock_unvest_num','defer_balance_tot','pension_value_tot','opt_unex_exer_num','opt_unex_unexer_num']
    a=pd.read_csv(RAW/'execucomp/anncomp_1992_2023_allfields.csv.gz',usecols=cols,dtype={'gvkey':str},low_memory=False)
    badflags=a[a.ceoann.notna() & ~a.ceoann.eq('CEO')];badflags.to_csv(AUD/'unexpected_ceoann_codes.csv',index=False)
    a=a[a.ceoann.eq('CEO') & a.year.between(*CONFIG['extended_years'])].copy().rename(columns={'year':'fyear'})
    for c in ['becameceo','leftofc','joined_co']:a[c]=pd.to_datetime(a[c],errors='coerce')
    a['anncomp_row_id']=np.arange(len(a));a['annual_ceo_count']=a.groupby(['gvkey','fyear']).gvkey.transform('size')
    a=a.merge(f,on=['gvkey','fyear'],how='left',validate='many_to_one',indicator='funda_merge')
    a['funda_key_ambiguous']=[(g,y) in bad_funda_keys for g,y in zip(a.gvkey,a.fyear)]
    a['ceo_start_after_fye']=a.becameceo.gt(a.datadate)
    a['ceo_left_by_fye']=a.leftofc.le(a.datadate)
    a['ceo_at_fye_candidate']=a.datadate.notna() & ~a.ceo_start_after_fye & ~a.ceo_left_by_fye
    a['active_ceo_count']=a.groupby(['gvkey','fyear']).ceo_at_fye_candidate.transform('sum')
    # Missing financial date: retain unique annual CEO for exclusion accounting, not analysis.
    a['selected_ceo']=(a.ceo_at_fye_candidate & a.active_ceo_count.eq(1)) | (a.datadate.isna() & a.annual_ceo_count.eq(1))
    a[['anncomp_row_id','gvkey','fyear','execid','co_per_rol','exec_fullname','ceoann','datadate','becameceo','leftofc','annual_ceo_count','active_ceo_count','ceo_start_after_fye','ceo_left_by_fye','selected_ceo','funda_key_ambiguous']].to_parquet(AUD/'ceo_selection_audit.parquet',index=False)
    b=a[a.selected_ceo].copy();assert not b.duplicated(['gvkey','fyear']).any()
    b['event_id']=b.gvkey+':'+b.fyear.astype(str)
    b['valuation_id']=b.event_id+':'+b.execid.astype(str)
    b['sic2']=np.floor(b.sich/100)
    b['flag_funda']=b.datadate.notna() & ~b.funda_key_ambiguous
    b['flag_industry']=b.sich.notna() & b.sich.between(100,9999) & ~b.sich.between(4900,4999) & ~b.sich.between(6000,6999)
    b['flag_positive_assets_me']=b['at'].gt(0) & b.market_equity_m.gt(0)
    b['tenure_years']=1+np.floor((b.datadate-b.becameceo).dt.days/365.25)
    b['ln_tenure']=np.log(b.tenure_years.where(b.tenure_years.gt(0)))
    # Open E sentinel is retained in raw and treated as open-ended for valid-date matching.
    links=pd.read_csv(RAW/'crsp/ccmxpf_lnkhist_postgres_all.csv.gz',dtype={'gvkey':str},low_memory=False).rename(columns=str.lower)
    links['linkdt']=pd.to_datetime(links.linkdt,errors='coerce')
    links['linkend_open']=links.linkenddt.eq('E') | links.linkenddt.isna()
    links['linkenddt']=pd.to_datetime(links.linkenddt.where(~links.linkend_open),errors='coerce')
    links['lpermno']=pd.to_numeric(links.lpermno,errors='coerce')
    links=links[links.linktype.isin(CONFIG['ccm_linktypes']) & links.linkprim.isin(CONFIG['ccm_linkprim']) & links.lpermno.gt(0)].copy()
    ll=b[['event_id','gvkey','datadate']].merge(links,on='gvkey',how='left')
    valid=ll.linkdt.le(ll.datadate) & (ll.linkend_open | ll.linkenddt.ge(ll.datadate))
    ll=ll[valid].copy();nlinks=ll.groupby('event_id').lpermno.nunique()
    b['ccm_n_distinct_permno']=b.event_id.map(nlinks).fillna(0).astype(int)
    ll.to_parquet(AUD/'ccm_valid_link_candidates.parquet',index=False)
    selected=ll[ll.event_id.map(nlinks).eq(1)].drop_duplicates('event_id')[['event_id','lpermno']].rename(columns={'lpermno':'permno'})
    b=b.merge(selected,on='event_id',how='left',validate='one_to_one')
    b['flag_ccm_unique']=b.ccm_n_distinct_permno.eq(1)
    # Exact backward-only rate lookup; holiday/missing observations never filled with future rates.
    rf=pd.read_csv(RAW/'fred/DTB3_2005-01-01_2024-06-30.csv',parse_dates=['observation_date'])
    rf['DTB3']=pd.to_numeric(rf.DTB3,errors='coerce');rf=rf.dropna(subset=['DTB3']).sort_values('observation_date')
    rr=pd.merge_asof(b.loc[b.datadate.notna(),['event_id','datadate']].sort_values('datadate'),rf,left_on='datadate',right_on='observation_date',direction='backward')
    rr=rr.rename(columns={'observation_date':'rf_date','DTB3':'rf_pct'}).drop(columns='datadate')
    b=b.merge(rr,on='event_id',how='left',validate='one_to_one')
    b['rf_gap_days']=(b.datadate-b.rf_date).dt.days
    b['r']=np.log1p(b.rf_pct/100);b['S']=b.prcc_f
    b.to_parquet(INT/'base_panel.parquet',index=False)
    requests=b.loc[b.flag_funda & b.flag_ccm_unique,['event_id','gvkey','fyear','datadate','permno']].copy();requests['permno']=requests.permno.astype('int64')
    requests.to_parquet(INT/'market_requests_latest.parquet',index=False)
    summary={'annual_ceo_rows':len(a),'selected_firm_years':len(b),'annual_ceo_unique_firmyears':a.groupby(['gvkey','fyear']).ngroups,'selected_with_funda':int(b.flag_funda.sum()),'funda_ambiguous_rows':int(dup.sum()),'market_requests':len(requests),'ccm_ambiguous_event_count':int(b.ccm_n_distinct_permno.gt(1).sum()),'ccm_missing_event_count':int(b.ccm_n_distinct_permno.eq(0).sum()),'ceo_rule':'CEOANN plus start<=fye and leftofc>fye when known; unresolved multiple candidates excluded; missing start allowed selection but yields missing tenure','regressions_run':False}
    write_json(AUD/'prepare_summary.json',summary);print(json.dumps(summary,indent=2),flush=True)


CONTROLS=['age','ln_tenure','rd_at_pct','rd_missing','capx_at_pct','asset_growth','mb','profitability_m','size_pct','re_at','retvol255']
CEO_COMMON=['cash_m','inside_debt_m','delta_vega','equity_m','vega_k']
IDENTIFIERS=['gvkey','fyear','datadate','permno','execid','co_per_rol','event_id','valuation_id','conm','exec_fullname','sich','sic2']
PERIODS={'original_2006_2011':[2006,2011],'extended_2006_2023':[2006,2023],'new_2012_2023':[2012,2023]}

def size_percentile(values):
    return 100*(values.rank(method='min')-1)/len(values)

def leverage_features(debt_m,equity_m,firm_leverage):
    ceo_leverage=safe_ratio(debt_m,equity_m,positive=True).where(debt_m.ge(0))
    relative=safe_ratio(ceo_leverage,firm_leverage,positive=True)
    return relative,np.log(relative.where(relative.gt(0))),relative.gt(1).astype(float).where(relative.notna())

def make_valuation_inputs():
    b=pd.read_parquet(INT/'base_panel.parquet');m=pd.read_parquet(INT/'market_inputs.parquet')
    x=b.merge(m[['event_id','sigma60']],on='event_id',how='left',validate='one_to_one')
    cols=['valuation_id','event_id','gvkey','fyear','execid','co_per_rol','datadate','S','sigma60','d','r','salary','bonus','shrown_excl_opts','stock_unvest_num','defer_balance_tot','pension_value_tot','opt_unex_exer_num','opt_unex_unexer_num']
    assert not x.duplicated(['co_per_rol','fyear']).any()
    x[cols].to_parquet(INT/'ceo_valuation_inputs.parquet',index=False)

def all_finite(df,cols):
    return pd.Series(np.isfinite(df[cols].to_numpy(dtype=float)).all(axis=1),index=df.index)

def export_table(df,pathbase):
    df=df.sort_values(['gvkey','fyear']).reset_index(drop=True).copy()
    for c in df.select_dtypes(include=['bool','boolean']).columns: df[c]=df[c].astype('int8')
    # All included identifiers are explicitly typed; strings retain GVKEY leading zeros.
    for c in ['gvkey','event_id','valuation_id','conm','exec_fullname']:
        if c in df:df[c]=df[c].fillna('').astype(str)
    for c in ['fyear','permno','execid','co_per_rol','sic2']:
        if c in df:df[c]=df[c].astype('int64')
    if any(len(c)>32 for c in df):raise ValueError('Stata field name too long')
    df.to_parquet(pathbase.with_suffix('.parquet'),index=False)
    df.to_csv(pathbase.with_suffix('.csv'),index=False,encoding='utf-8-sig',float_format='%.17g')
    labels={'payer':'Dividend per share ex-date fiscal > 0','cash_m':'CEO salary plus bonus, USD millions','inside_debt_m':'Annual pension plus deferred balance, USD millions','ln_rellev':'Natural log of CEO relative leverage; positive only','high_rellev':'CEO relative leverage > 1','delta_vega':'Total delta / total vega; see formula_version warning','equity_m':'CEO equity portfolio value, USD millions','vega_k':'CEO portfolio sensitivity to 1pp volatility, USD thousands','size_pct':'Percent of reference eligible firm-years with smaller market equity','rd_at_pct':'100 * XRD / AT; missing XRD zero with separate indicator','capx_at_pct':'100 * CAPX / AT','asset_growth':'(AT - prior consecutive FY AT) / prior AT','profitability_m':'IB - DVP + TXDITC, raw Compustat USD millions','retvol255':'100 * sd(RETX) in previous 255 market days, ddof=1','sample_log':'Eligible for Table 4 columns 3 and 9','sample_ab':'Eligible for both formula versions on identical firm-years','sample_ab_log':'Eligible for both versions log-leverage models'}
    df.to_stata(pathbase.with_suffix('.dta'),write_index=False,version=118,data_label=('A mixed-unit literal diagnostic; see codebook' if df.formula_version.iloc[0].startswith('A') else 'B standard finance; regression data only'),convert_dates={'datadate':'td'},variable_labels={c:v for c,v in labels.items() if c in df})
    back=pd.read_stata(pathbase.with_suffix('.dta'),convert_categoricals=False)
    assert len(back)==len(df) and not back.duplicated(['gvkey','fyear']).any()
    assert back.gvkey.tolist()==df.gvkey.tolist()
    number_cols=df.select_dtypes(include=np.number).columns
    for c in number_cols:
        np.testing.assert_allclose(back[c].to_numpy(float),df[c].to_numpy(float),rtol=1e-12,atol=1e-12,equal_nan=True,err_msg='Stata roundtrip '+c)
    assert pd.to_datetime(back.datadate).equals(pd.to_datetime(df.datadate))
    return {'file_base':str(pathbase.relative_to(ROOT)),'rows':len(df),'columns':len(df.columns),'stata_roundtrip_passed':True}

def finalize():
    b=pd.read_parquet(INT/'base_panel.parquet');m=pd.read_parquet(INT/'market_inputs.parquet');op=pd.read_parquet(INT/'option_portfolios.parquet')
    assert b.event_id.is_unique and m.event_id.is_unique and op.valuation_id.is_unique
    old=pd.read_parquet(INT/'market_requests.parquet') if (INT/'market_requests.parquet').exists() else pd.read_parquet(INT/'market_requests_latest.parquet')
    latest=pd.read_parquet(INT/'market_requests_latest.parquet')
    cmp=['event_id','gvkey','fyear','datadate','permno']
    pd.testing.assert_frame_equal(old[cmp].sort_values('event_id').reset_index(drop=True),latest[cmp].sort_values('event_id').reset_index(drop=True),check_dtype=False)
    if set(latest.event_id)!=set(m.event_id):raise ValueError('Market request/output IDs differ')
    pd.testing.assert_frame_equal(m[cmp].sort_values('event_id').reset_index(drop=True),latest[cmp].sort_values('event_id').reset_index(drop=True),check_dtype=False)
    market_new=[c for c in m if c not in b or c=='event_id']
    b=b.merge(m[market_new],on='event_id',how='left',validate='one_to_one')
    sig=op[['valuation_id','sigma60']].merge(b[['valuation_id','sigma60']],on='valuation_id',suffixes=('_option','_market'),validate='one_to_one')
    np.testing.assert_allclose(sig.sigma60_option,sig.sigma60_market,equal_nan=True)
    newcols=[c for c in op if c not in b or c=='valuation_id']
    b=b.merge(op[newcols],on='valuation_id',how='left',validate='one_to_one')
    if b.portfolio_complete.isna().any():raise ValueError('Missing portfolio audit rows')
    b['portfolio_complete']=b.portfolio_complete.astype(bool)
    b['flag_current_security']=b.last_trade_date.ge(b.last_market_date_le_fye) & b.last_trade_date.le(b.datadate)
    b['flag_common_us_listing']=b.last_shrcd.isin(CONFIG['share_codes']) & b.last_exchcd.isin(CONFIG['exchange_codes']) & b.flag_current_security
    b['flag_base_eligible']=b[['flag_funda','flag_industry','flag_positive_assets_me','flag_ccm_unique','flag_common_us_listing']].all(axis=1)
    b['size_pct']=np.nan;b['size_ref_n']=np.nan
    base=b[b.flag_base_eligible]
    b.loc[base.index,'size_pct']=base.groupby('fyear').market_equity_m.transform(size_percentile)
    b.loc[base.index,'size_ref_n']=base.groupby('fyear').gvkey.transform('size')
    b['payer_calendar']=np.where(b.dvpsx_c.notna(),b.dvpsx_c.gt(0).astype(float),np.nan)
    for v in ['a','b']:
        relative,log,high=leverage_features(b.inside_debt_m,b[f'equity_{v}_m'],b.firm_leverage)
        b[f'rellev_{v}'],b[f'ln_rellev_{v}'],b[f'high_rellev_{v}']=relative,log,high
        b[f'high_appendix_{v}']=relative.gt(b.firm_leverage).astype(float).where(relative.notna() & b.firm_leverage.notna())
    b['flag_controls_complete']=all_finite(b,['payer','sic2','fyear']+CONTROLS)
    b['flag_cash_debt_complete']=all_finite(b,['cash_m','inside_debt_m']) & b.inside_debt_m.ge(0)
    for v in ['a','b']:
        measures=[f'equity_{v}_m',f'vega_{v}_k',f'dv_ratio_{v}',f'rellev_{v}',f'high_rellev_{v}']
        b[f'flag_measures_{v}']=all_finite(b,measures) & b[f'equity_{v}_m'].gt(0) & b[f'vega_{v}_k'].gt(0)
        b[f'sample_{v}']=b.flag_base_eligible & b.flag_controls_complete & b.flag_cash_debt_complete & b.portfolio_complete & b[f'flag_measures_{v}']
        b[f'sample_log_{v}']=b[f'sample_{v}'] & b[f'ln_rellev_{v}'].notna() & np.isfinite(b[f'ln_rellev_{v}'])
    b['sample_ab']=b.sample_a & b.sample_b
    b['sample_ab_log']=b.sample_log_a & b.sample_log_b
    b['period_original']=b.fyear.between(2006,2011);b['period_new']=b.fyear.between(2012,2023)
    # Preserve every selected CEO-year including excluded observations and flags.
    b=b.sort_values(['gvkey','fyear']).reset_index(drop=True)
    b.to_parquet(OUT/'panel_master_audit.parquet',index=False)
    failures=['flag_funda','flag_industry','flag_positive_assets_me','flag_ccm_unique','flag_common_us_listing','flag_controls_complete','flag_cash_debt_complete','portfolio_complete']
    for v in ['a','b']:
        stages=failures+[f'flag_measures_{v}']
        conditions=[~b[s].fillna(False).astype(bool).to_numpy() for s in stages]
        b[f'first_exclusion_{v}']=np.select(conditions,stages,default='included')
    auditcols=IDENTIFIERS+failures+['flag_measures_a','flag_measures_b','sample_a','sample_b','sample_log_a','sample_log_b','sample_ab','sample_ab_log','first_exclusion_a','first_exclusion_b','portfolio_reason','n_option_tranches','n_valid_tranches','zero_options_explicit','sigma60_failure','retvol255_failure']
    b[auditcols].to_parquet(AUD/'sample_selection_audit.parquet',index=False)
    counts=[];attrition=[];exports=[]
    outputcols=IDENTIFIERS+['formula_version','payer','cash_m','inside_debt_m','ln_rellev','high_rellev','delta_vega','equity_m','vega_k','rellev']+CONTROLS+['sample_log','sample_ab','sample_ab_log','period_original','period_new','sigma60','d','r','size_ref_n','high_appendix','profitability_txdi_m','payer_calendar']
    for v in ['a','b']:
        x=b.rename(columns={f'equity_{v}_m':'equity_m',f'vega_{v}_k':'vega_k',f'dv_ratio_{v}':'delta_vega',f'rellev_{v}':'rellev',f'ln_rellev_{v}':'ln_rellev',f'high_rellev_{v}':'high_rellev',f'high_appendix_{v}':'high_appendix'}).copy()
        x['formula_version']='A_paper_literal_diagnostic' if v=='a' else 'B_standard_finance'
        x['sample_log']=x[f'sample_log_{v}']
        for period,(lo,hi) in PERIODS.items():
            yy=x.fyear.between(lo,hi);ss=x[f'sample_{v}'] & yy;ls=x.sample_log & yy
            counts.append({'version':v,'period':period,'N_nonlog':int(ss.sum()),'N_log':int(ls.sum()),'payers_nonlog':int(x.loc[ss,'payer'].sum()),'nonpayers_nonlog':int(ss.sum()-x.loc[ss,'payer'].sum()),'N_ab_common':int((x.sample_ab & yy).sum()),'N_ab_log_common':int((x.sample_ab_log & yy).sum())})
            current=yy.copy()
            attrition.append({'version':v,'period':period,'stage':'selected_annual_CEO_firmyears','N':int(current.sum())})
            for stage in failures+[f'flag_measures_{v}']:
                current &= x[stage].fillna(False).astype(bool)
                attrition.append({'version':v,'period':period,'stage':stage,'N':int(current.sum())})
            np.testing.assert_array_equal(current.to_numpy(bool),ss.to_numpy(bool))
            exports.append(export_table(x.loc[ss,outputcols],OUT/f'table4_{v}_{period}'))
        x.loc[x[f'sample_{v}']].groupby(['fyear','payer']).size().rename('N').reset_index().assign(version=v).to_csv(REPORT/f'yearly_sample_{v}.csv',index=False)
    pd.DataFrame(counts).to_csv(REPORT/'sample_counts.csv',index=False)
    pd.DataFrame(attrition).to_csv(REPORT/'sample_attrition.csv',index=False)
    pd.DataFrame(exports).to_csv(REPORT/'export_checks.csv',index=False)
    # Actual selected annual CEO rows are upstream of the one-row-per-firm-year panel.
    cs=pd.read_parquet(AUD/'ceo_selection_audit.parquet')
    cs.assign(period=np.where(cs.fyear.le(2011),'original','new')).groupby(['period','selected_ceo']).size().rename('N').reset_index().to_csv(REPORT/'ceo_selection_counts.csv',index=False)
    models={1:['cash_m'],2:['inside_debt_m'],3:['ln_rellev'],4:['high_rellev'],5:['delta_vega'],6:['equity_m'],7:['vega_k'],8:['cash_m','inside_debt_m','delta_vega','equity_m','vega_k'],9:['cash_m','ln_rellev','delta_vega','equity_m','vega_k'],10:['cash_m','high_rellev','delta_vega','equity_m','vega_k']}
    write_json(ROOT/'table4_model_columns.json',{'dependent':'payer','controls':CONTROLS,'industry_dummies':'sic2','year_dummies':'fyear','models':{str(k):{'ceo_regressors':v,'sample_flag':'sample_log' if k in [3,9] else 'all rows of each version dataset'} for k,v in models.items()},'estimation_run':False,'note':'This file declares future model columns only; no model was estimated.'})
    # Descriptive quality checks, not an empirical test of the article's findings.
    validation={'unique_master_keys':not b.duplicated(['gvkey','fyear']).any(),'master_rows':len(b),'market_requests_equivalent_after_source_supplement':True,'market_output_request_match':True,'sigma_inputs_match_final_market_output':True,'gvkey_six_digit_strings':bool(b.gvkey.str.fullmatch(r'\d{6}').all()),'no_forward_rf_date':bool((b.rf_date.le(b.datadate)|b.rf_date.isna()).all()),'no_forward_asset_lag':bool((b.lag_at_date.lt(b.datadate)|b.lag_at_date.isna()).all()),'log_is_positive_relative_only':bool((b.loc[b.sample_log_a,'rellev_a']>0).all() and (b.loc[b.sample_log_b,'rellev_b']>0).all()),'common_mask_intersection':bool((b.sample_ab==(b.sample_a & b.sample_b)).all()),'zero_debt_retained_nonlog_a':int((b.sample_a & b.inside_debt_m.eq(0)).sum()),'zero_debt_retained_nonlog_b':int((b.sample_b & b.inside_debt_m.eq(0)).sum()),'infinite_values_in_export':False,'winsorization':'none','stata_export_roundtrip':all(e['stata_roundtrip_passed'] for e in exports),'regressions_run':False,'exports':exports}
    for flag in ['unique_master_keys','gvkey_six_digit_strings','no_forward_rf_date','no_forward_asset_lag','log_is_positive_relative_only','common_mask_intersection','stata_export_roundtrip']:
        if not validation[flag]:raise AssertionError(flag)
    write_json(AUD/'panel_validation.json',validation)
    hashes=[]
    for path in sorted(RAW.rglob('*')):
        if path.name.endswith(('.csv.gz','.csv')):
            h=hashlib.sha256()
            with path.open('rb') as fh:
                for block in iter(lambda:fh.read(1<<20),b''):h.update(block)
            hashes.append({'path':str(path.relative_to(ROOT)),'bytes':path.stat().st_size,'sha256':h.hexdigest()})
    script_hashes=[{'path':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted((ROOT/'scripts').glob('*.py'))]
    write_json(ROOT/'build_manifest.json',{'schema_version':1,'built_at_utc':datetime.now(timezone.utc).isoformat(),'stage':'regression data construction only','environment':{'python':sys.version,'pandas':pd.__version__,'numpy':np.__version__,'scipy':version('scipy'),'pyarrow':version('pyarrow'),'stata_file_version':118},'config':CONFIG,'source_files':hashes,'scripts':script_hashes,'sample_counts':counts,'validation':'audits/panel_validation.json','source_audit':'metadata/source_audit_20261024.json','formula_a_warning':'Mechanical diagnostic mixes stock $1-delta and option 1%-delta; stock vega not standard; not confirmed author code.','regressions_run':False})
    print(json.dumps({'master_rows':len(b),'sample_counts':counts,'exports':len(exports),'regressions_run':False},indent=2),flush=True)

def run_all():
    prepare()
    from market_inputs import build_market_inputs
    from option_portfolios import build_option_portfolios
    build_market_inputs(INT/'market_requests_latest.parquet',RAW/'crsp',INT/'market_inputs.parquet',AUD/'market')
    make_valuation_inputs()
    build_option_portfolios(INT/'ceo_valuation_inputs.parquet',RAW/'execucomp/outstandingawards_2006_2023_allfields.csv.gz',RAW/'execucomp/pension_2006_2023_allfields.csv.gz',RAW/'execucomp/deferredcomp_2006_2023_allfields.csv.gz',INT/'option_portfolios.parquet',AUD/'options')
    finalize()

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--stage',choices=['prepare','valuations','finalize','all'],default='all');args=p.parse_args()
    if args.stage=='prepare':prepare()
    elif args.stage=='valuations':make_valuation_inputs()
    elif args.stage=='finalize':finalize()
    else:run_all()
