"""Compare rebuilt CEO/company/time matching with frozen reference, without using references for matching."""
from pathlib import Path
import argparse,json
import numpy as np
import pandas as pd

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--package-root',type=Path,default=Path(__file__).resolve().parents[1]);ap.add_argument('--run-root',type=Path);args=ap.parse_args()
 pkg=args.package_root.resolve();run=args.run_root or pkg/'rerun';run=run if run.is_absolute() else pkg/run
 base=run/'project/replications/caliskan_doukas_2015/data/matched';ref=pkg/'reference/matching'
 pairs=[('local source identity',base/'local/audit/source_score_identity.parquet',ref/'source_score_identity_local.parquet','score_panel_id'),('official source identity',base/'official/audit/source_official_identity.parquet',ref/'source_official_identity.parquet','score_panel_id'),('full master official flags',base/'official/master_with_rd_scores.parquet',ref/'master_with_rd_scores.parquet','event_id'),('annualB official matches',base/'official/annual/table4_b_extended_2006_2023_rd_scores.parquet',ref/'table4_b_extended_2006_2023_rd_scores.parquet','event_id')]
 checks=[]
 for label,gp,rp,key in pairs:
  g=pd.read_parquet(gp);r=pd.read_parquet(rp);assert g[key].is_unique and r[key].is_unique,label
  assert set(g[key])==set(r[key]),label+': IDs differ'
  missing=set(r)-set(g);assert not missing,(label,missing)
  g=g.set_index(key,drop=False).loc[r[key]].reset_index(drop=True);r=r.reset_index(drop=True)
  diffs=[];maxerr=0.0;numeric_exact=True
  for c in r:
   if pd.api.types.is_numeric_dtype(r[c]) and not pd.api.types.is_bool_dtype(r[c]):
    x=g[c].to_numpy(dtype=float,na_value=np.nan);y=r[c].to_numpy(dtype=float,na_value=np.nan)
    assert np.array_equal(np.isnan(x),np.isnan(y)),(label,c,'NaN mask')
    assert np.array_equal(np.isposinf(x),np.isposinf(y)) and np.array_equal(np.isneginf(x),np.isneginf(y)),(label,c,'inf mask')
    finite=np.isfinite(x)&np.isfinite(y)
    err=float(np.max(np.abs(x[finite]-y[finite])/np.maximum(1,np.abs(y[finite])))) if finite.any() else 0.
    maxerr=max(maxerr,err);numeric_exact &= np.array_equal(x,y,equal_nan=True)
    assert err<1e-11,(label,c,err)
   else:
    pd.testing.assert_series_equal(g[c],r[c],check_names=False,check_dtype=False,check_exact=True)
  checks.append({'table':label,'rows':len(g),'reference_columns_checked':len(r.columns),'extra_generated_columns':sorted(set(g)-set(r)),'all_IDs_exact':True,'nonnumeric_exact':True,'numeric_exact':bool(numeric_exact),'max_scaled_numeric_error':maxerr})
 b=pd.read_parquet(base/'official/annual/table4_b_extended_2006_2023_rd_scores.parquet');d=b[b.fyear.between(2013,2023)]
 strict=d[d.official_strict_period_match.fillna(False)];assert len(d)==7086 and len(strict)==2967
 report={'passed':True,'checks':checks,'annual_B_2013_2023_rows':len(d),'strict_2013_2023_rows':len(strict),'company_firms':int(strict.gvkey.nunique()),'CEOs':int(strict.execid.nunique()),'original_scores_retrained':False,'reference_frames_used_for_construction':False}
 dest=run/'matching_reproduction_check.json';dest.write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
