"""Build audited CEO option portfolios; no regressions are estimated.

All ExecuComp quantities and monetary amounts used here are originally in
thousands (EXPRIC and fiscal-end S are actual dollars). Internal valuation is
in actual shares and dollars. A is a mechanical paper-literal diagnostic with
mixed stock/option delta units; B has coherent 1%-price delta and stock vega=0.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.special import ndtr

COUNT_TOLERANCE_THOUSANDS = 0.01
OPTION_COUNT_FIELDS = ['opts_unex_exer', 'opts_unex_unexer', 'opts_unex_unearn']


def _id(s: pd.Series, width: int | None = None) -> pd.Series:
    out = s.astype('string').str.strip().str.replace(r'\.0$', '', regex=True)
    return out.str.zfill(width) if width else out


def bsm_value_delta_vega(S, X, T, r, d, sigma):
    """Vectorized per-option value, 1%-price delta, 1pp-volatility vega.

    Expiry T=0 uses the payoff limit, with symmetric half-delta at the kink.
    Zero volatility uses the deterministic-forward limit, including the
    one-sided volatility derivative at forward ATM. A zero strike uses its
    exact stock-like limit. Negative T/strike/sigma or S<=0 is invalid.
    """
    S, X, T, r, d, sigma = np.broadcast_arrays(*[
        np.asarray(a, dtype=float) for a in (S, X, T, r, d, sigma)])
    value, delta, vega = [np.full(S.shape, np.nan) for _ in range(3)]
    valid = np.isfinite(S+X+T+r+d+sigma) & (S>0) & (X>=0) & (T>=0) & (sigma>=0)
    expiry = valid & (T==0)
    value[expiry] = np.maximum(S[expiry]-X[expiry], 0)
    delta[expiry] = S[expiry]*.01*np.where(S[expiry]>X[expiry], 1., np.where(S[expiry]<X[expiry], 0., .5))
    vega[expiry] = 0.
    alive = valid & (T>0)
    ds = S*np.exp(-d*T)
    dx = X*np.exp(-r*T)
    zero_strike = alive & (X==0)
    value[zero_strike], delta[zero_strike], vega[zero_strike] = ds[zero_strike], ds[zero_strike]*.01, 0.
    deterministic = alive & (X>0) & (sigma==0)
    forward_atm = np.isclose(ds, dx, rtol=1e-12, atol=1e-12)
    prob = np.where(forward_atm, .5, (ds>dx).astype(float))
    value[deterministic] = np.maximum(ds[deterministic]-dx[deterministic], 0.)
    delta[deterministic] = ds[deterministic]*.01*prob[deterministic]
    vega[deterministic] = np.where(forward_atm[deterministic], ds[deterministic]*np.sqrt(T[deterministic])*.01/np.sqrt(2*np.pi), 0.)
    regular = alive & (X>0) & (sigma>0)
    ix = regular
    z = (np.log(S[ix]/X[ix])+(r[ix]-d[ix]+sigma[ix]**2/2)*T[ix])/(sigma[ix]*np.sqrt(T[ix]))
    value[ix] = ds[ix]*ndtr(z)-dx[ix]*ndtr(z-sigma[ix]*np.sqrt(T[ix]))
    delta[ix] = ds[ix]*ndtr(z)*.01
    vega[ix] = ds[ix]*np.exp(-z*z/2)/np.sqrt(2*np.pi)*np.sqrt(T[ix])*.01
    # Roundoff can only make an otherwise nonnegative call value tiny-negative.
    value[valid] = np.maximum(value[valid], 0.)
    return value, delta, vega


def _detail_totals(path, value_name, id_name, prefix):
    frame = pd.read_csv(path, dtype='string', usecols=lambda c: c in {'co_per_rol','year',value_name,id_name})
    frame['_role'] = _id(frame.co_per_rol)
    frame['_year'] = pd.to_numeric(frame.year, errors='coerce')
    frame[value_name] = pd.to_numeric(frame[value_name], errors='coerce')
    keys = ['_role', '_year']
    grouped = frame.groupby(keys, dropna=False)[value_name].agg(['size','count'])
    grouped[prefix+'_detail_total_k'] = frame.groupby(keys, dropna=False)[value_name].sum(min_count=1)
    grouped[prefix+'_detail_rows'] = grouped.pop('size')
    grouped[prefix+'_detail_values_present'] = grouped.pop('count')
    grouped[prefix+'_detail_duplicate_ids'] = frame.duplicated(keys+[id_name], keep=False).groupby([frame[k] for k in keys], dropna=False).any()
    return grouped.reset_index()


def build_option_portfolios(ceo_inputs_path, awards_path, pension_path,
                            deferred_path, output_path, audit_dir):
    """Write one CEO-valuation row and tranche/debt audits; return that frame.

    Inputs: valuation_id, gvkey, execid, co_per_rol, fyear, datadate, S,
    sigma60,d,r, plus the original anncomp amounts and quantities.
    Pension/deferred detail tables audit annual totals only: no fallback or
    zero imputation changes the strict annual baseline.
    """
    audit_dir = Path(audit_dir)
    audit_dir.mkdir(parents=True, exist_ok=True)
    inputs = pd.read_parquet(ceo_inputs_path).copy()
    required = {'valuation_id','gvkey','execid','co_per_rol','fyear','datadate','S','sigma60','d','r',
                'salary','bonus','shrown_excl_opts','stock_unvest_num','defer_balance_tot',
                'pension_value_tot','opt_unex_exer_num','opt_unex_unexer_num'}
    if required-set(inputs):
        raise ValueError('Missing CEO inputs: '+str(sorted(required-set(inputs))))
    if inputs.valuation_id.isna().any() or inputs.valuation_id.duplicated().any():
        raise ValueError('valuation_id must be unique and nonmissing')
    inputs['_role'] = _id(inputs.co_per_rol)
    inputs['_year'] = pd.to_numeric(inputs.fyear, errors='coerce')
    inputs['gvkey'] = _id(inputs.gvkey, 6)
    inputs['execid'] = _id(inputs.execid, 6)
    inputs['datadate'] = pd.to_datetime(inputs.datadate, errors='coerce')
    numeric = list(required-{'valuation_id','gvkey','execid','co_per_rol','fyear','datadate'})
    for col in numeric:
        inputs[col] = pd.to_numeric(inputs[col], errors='coerce').astype(float)
    keys = ['_role','_year']
    acols = {'co_per_rol','year','gvkey','execid','outawdnum','exdate','expric',*OPTION_COUNT_FIELDS}
    awards = pd.read_csv(awards_path, dtype='string', usecols=lambda c: c in acols)
    awards['_role'] = _id(awards.co_per_rol)
    awards['_year'] = pd.to_numeric(awards.year, errors='coerce')
    awards = awards.merge(inputs[keys].drop_duplicates(), on=keys, how='inner', validate='many_to_one')
    awards.rename(columns={'gvkey':'award_gvkey','execid':'award_execid'}, inplace=True)
    awards['award_gvkey'] = _id(awards.award_gvkey,6)
    awards['award_execid'] = _id(awards.award_execid,6)
    awards['outawdnum'] = _id(awards.outawdnum)
    awards['award_duplicate_key'] = awards.duplicated(keys+['outawdnum'], keep=False)
    awards['award_number_missing'] = awards.outawdnum.isna()
    awards['expiry'] = pd.to_datetime(awards.exdate, errors='coerce')
    for col in OPTION_COUNT_FIELDS+['expric']:
        awards[col] = pd.to_numeric(awards[col], errors='coerce').astype(float)
    awards['quantity_category_missing'] = awards[OPTION_COUNT_FIELDS].isna().any(axis=1)
    awards['quantity_negative'] = awards[OPTION_COUNT_FIELDS].lt(0).any(axis=1)
    awards['is_option_row'] = awards[OPTION_COUNT_FIELDS].gt(0).any(axis=1)
    # Category absence inside the detailed award table is zero; absence of an
    # entire annual portfolio is separately tested using annual disclosed totals.
    awards['total_quantity_k'] = awards[OPTION_COUNT_FIELDS].fillna(0).sum(axis=1)
    awards['quantity_shares'] = awards.total_quantity_k*1000.
    m = inputs.merge(awards.drop(columns=['co_per_rol','year']), on=keys, how='left', validate='many_to_many')
    m['identity_mismatch'] = ((m.award_gvkey.notna() & m.award_gvkey.ne(m.gvkey)) |
                              (m.award_execid.notna() & m.award_execid.ne(m.execid))).fillna(False)
    m['identity_missing'] = (m.award_gvkey.isna() | m.award_execid.isna()) & m.is_option_row.fillna(False)
    m['T'] = (m.expiry-m.datadate).dt.days/365.25
    mask = m.is_option_row.fillna(False)
    option_rows = m.loc[mask].copy()
    v, de, ve = bsm_value_delta_vega(option_rows.S,option_rows.expric,option_rows['T'],
                                   option_rows.r,option_rows.d,option_rows.sigma60)
    option_rows['unit_value_usd'], option_rows['unit_delta_usd'], option_rows['unit_vega_usd'] = v,de,ve
    option_rows['tranche_value_usd'] = v*option_rows.quantity_shares
    option_rows['tranche_delta_usd'] = de*option_rows.quantity_shares
    option_rows['tranche_vega_usd'] = ve*option_rows.quantity_shares
    option_rows['valid_tranche'] = np.isfinite(v+de+ve) & ~option_rows.quantity_negative.fillna(True) & ~option_rows.identity_mismatch & ~option_rows.award_duplicate_key.fillna(True) & ~option_rows.award_number_missing.fillna(True) & ~option_rows.identity_missing & np.isfinite(option_rows.quantity_shares)
    option_rows['invalid_reason'] = np.select([
        option_rows.identity_mismatch.to_numpy(dtype=bool),
        option_rows.identity_missing.to_numpy(dtype=bool),
        option_rows.award_number_missing.fillna(False).to_numpy(dtype=bool),
        option_rows.award_duplicate_key.fillna(False).to_numpy(dtype=bool),
        option_rows.quantity_negative.fillna(False).to_numpy(dtype=bool),
        option_rows['T'].lt(0).to_numpy(dtype=bool),
        option_rows.expiry.isna().to_numpy(dtype=bool),
        option_rows.expric.lt(0).to_numpy(dtype=bool),
        ~np.isfinite(v+de+ve)],
        ['identity_mismatch','identity_missing','missing_award_number','duplicate_award_key','negative_quantity','expired_before_fiscal_end','missing_expiry','negative_strike','missing_or_invalid_valuation_inputs'], default='')
    g = option_rows.groupby('valuation_id')
    agg = g.agg(n_option_tranches=('is_option_row','size'),
                n_valid_tranches=('valid_tranche','sum'),
                exer_quantity_k=('opts_unex_exer','sum'),
                unexer_quantity_k=('opts_unex_unexer','sum'),
                unearned_quantity_k=('opts_unex_unearn','sum'),
                option_value_partial_usd=('tranche_value_usd','sum'),
                option_delta_partial_usd=('tranche_delta_usd','sum'),
                option_vega_partial_usd=('tranche_vega_usd','sum'))
    out = inputs.merge(agg, on='valuation_id', how='left', validate='one_to_one')
    aggregate_columns = list(agg.columns)
    out[aggregate_columns] = out[aggregate_columns].fillna(0.)
    rawflags = m.groupby('valuation_id').agg(
        any_award_identity_mismatch=('identity_mismatch','any'),
        any_award_identity_missing=('identity_missing','any'),
        any_missing_award_number=('award_number_missing','any'),
        any_negative_award_quantity=('quantity_negative','any'),
        any_duplicate_award_key=('award_duplicate_key','any'),
        any_award_category_missing=('quantity_category_missing','any'))
    out = out.merge(rawflags,on='valuation_id',how='left',validate='one_to_one')
    out['exer_quantity_difference_k'] = out.exer_quantity_k-out.opt_unex_exer_num
    out['unexer_quantity_difference_k'] = out.unexer_quantity_k-out.opt_unex_unexer_num
    out['annual_counts_disclosed'] = out[['opt_unex_exer_num','opt_unex_unexer_num']].notna().all(axis=1) & out[['opt_unex_exer_num','opt_unex_unexer_num']].ge(0).all(axis=1)
    out['annual_counts_reconciled'] = out.annual_counts_disclosed & out.exer_quantity_difference_k.abs().le(COUNT_TOLERANCE_THOUSANDS) & out.unexer_quantity_difference_k.abs().le(COUNT_TOLERANCE_THOUSANDS)
    out['zero_options_explicit'] = out.annual_counts_disclosed & out[['opt_unex_exer_num','opt_unex_unexer_num']].eq(0).all(axis=1) & out.n_option_tranches.eq(0)
    out['portfolio_complete'] = (out.annual_counts_reconciled & out.n_valid_tranches.eq(out.n_option_tranches) & ~out.any_award_identity_mismatch & ~out.any_award_identity_missing & ~out.any_missing_award_number & ~out.any_negative_award_quantity & ~out.any_duplicate_award_key)
    out['portfolio_reason'] = np.select([condition.fillna(False).to_numpy(dtype=bool) for condition in [
        ~out.annual_counts_disclosed,
        out.any_award_identity_mismatch,
        out.any_award_identity_missing,
        out.any_missing_award_number,
        out.any_duplicate_award_key,
        out.any_negative_award_quantity,
        ~out.annual_counts_reconciled,
        out.n_valid_tranches.ne(out.n_option_tranches)]],
        ['annual_option_counts_missing_or_negative','identity_mismatch','identity_missing','missing_award_number','duplicate_award_key','negative_award_quantity','annual_count_mismatch','invalid_or_missing_tranche_inputs'],default='complete')
    for component in ['value','delta','vega']:
        out['option_'+component+'_usd'] = out['option_'+component+'_partial_usd'].where(out.portfolio_complete)
    common_shares = (out.shrown_excl_opts*1000.).where(out.shrown_excl_opts.ge(0))
    unvested_shares = (out.stock_unvest_num*1000.).where(out.stock_unvest_num.ge(0))
    shares_a = common_shares+unvested_shares
    out['stock_shares_a'],out['stock_shares_b'] = shares_a,common_shares
    positive_S = out.S.where(out.S.gt(0))
    out['equity_a_m'] = (shares_a*positive_S+out.option_value_usd)/1e6
    out['equity_b_m'] = (common_shares*positive_S+out.option_value_usd)/1e6
    out['delta_a_k'] = (shares_a+out.option_delta_usd)/1000.
    out['delta_b_k'] = (common_shares*positive_S*.01+out.option_delta_usd)/1000.
    out['vega_a_k'] = (shares_a*.01+out.option_vega_usd)/1000.
    out['vega_b_k'] = out.option_vega_usd/1000.
    out['dv_ratio_a'] = (out.delta_a_k/out.vega_a_k).where(out.vega_a_k.gt(0))
    out['dv_ratio_b'] = (out.delta_b_k/out.vega_b_k).where(out.vega_b_k.gt(0))
    out['cash_m'] = (out.salary+out.bonus)/1000.
    out['inside_debt_m'] = (out.defer_balance_tot+out.pension_value_tot)/1000.
    for path,value,idname,prefix,annual in [
        (pension_path,'pension_value','penid','pension','pension_value_tot'),
        (deferred_path,'defer_balance','defer_id','deferred','defer_balance_tot')]:
        details = _detail_totals(path,value,idname,prefix)
        out = out.merge(details,on=keys,how='left',validate='many_to_one')
        out[prefix+'_detail_difference_k'] = out[prefix+'_detail_total_k']-out[annual]
        out[prefix+'_detail_reconciled'] = out[prefix+'_detail_difference_k'].abs().le(.01).where(out[prefix+'_detail_total_k'].notna() & out[annual].notna()).astype('boolean')
    option_rows.to_parquet(audit_dir/'option_tranches.parquet', index=False)
    out.drop(columns=keys).to_parquet(audit_dir/'ceo_portfolio_audit.parquet', index=False)
    summary = {'valuation_rows':len(out),'positive_option_tranche_rows':len(option_rows),
               'matched_raw_award_rows':len(awards),'pure_stock_or_zero_option_raw_award_rows':int((~awards.is_option_row).sum()),
               'portfolio_complete':int(out.portfolio_complete.sum()),
               'zero_options_explicit':int(out.zero_options_explicit.sum()),
               'portfolio_reason_counts':out.portfolio_reason.value_counts().to_dict(),
               'quantity_tolerance_thousands':COUNT_TOLERANCE_THOUSANDS,
               'quantity_reconciliation':'annual exer vs detailed exer; annual unexer vs detailed unexer; unearned options included independently in full portfolio',
               'quantity_rule_evidence':'Supplier definitions plus raw category quantity audit, fixed before regression estimation',
               'original_units':'option/share quantities thousands; compensation/debt thousands USD; strike and share price actual USD',
               'a_warning':'Mechanical literal diagnostic only: stock $1 delta mixed with option 1%-price delta; stock vega nonstandard; restricted shares may double count',
               'debt_policy':'Use anncomp components only; missing annual debt not replaced by detail sum or zero',
               'regressions_run':False}
    (audit_dir/'option_summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    keep = [c for c in out.columns if c not in keys]
    out = out[keep]
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    out.to_parquet(output_path,index=False)
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs',required=True)
    parser.add_argument('--awards',required=True)
    parser.add_argument('--pension',required=True)
    parser.add_argument('--deferred',required=True)
    parser.add_argument('--output',required=True)
    parser.add_argument('--audit-dir',required=True)
    args=parser.parse_args()
    result=build_option_portfolios(args.inputs,args.awards,args.pension,args.deferred,args.output,args.audit_dir)
    print(json.dumps({'rows':len(result),'complete':int(result.portfolio_complete.sum())}),flush=True)

if __name__=='__main__':
    main()
