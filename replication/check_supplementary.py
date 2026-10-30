"""Run the supplied saved-model and seed checks against a completed core replay."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, required=True)
    args = parser.parse_args()
    run = args.run.resolve()
    package = run/'inputs/packages/step3_risk_score_collaborator_20261027'
    generated = run/'workflow/step3'
    out = run/'supplementary'
    out.mkdir(exist_ok=True)
    report = {'completed_utc':None, 'passed':False, 'checks':[],
              'scope':'Saved fits and portable scoring; rebuilt panel; three original seed robustness analyses',
              'tolerance_origin':'1e-9 from supplied code/04_verify.py; no widened threshold'}
    def record(name, passed, **detail):
        report['checks'].append({'name':name,'passed':bool(passed),**detail})
        (out/'VERIFICATION.json').write_text(json.dumps(report,indent=2)+'\n')
        if not passed:
            raise ValueError('Supplementary verification failed: '+name)
    with (out/'saved-models.log').open('w') as log:
        result = subprocess.run([sys.executable, str(package/'code/04_verify.py')],
                                cwd=package,stdout=log,stderr=subprocess.STDOUT)
    record('supplied_saved_model_checks', result.returncode == 0)
    import numpy as np
    import pandas as pd
    original = pd.read_parquet(package/'data/firm_year_inputs.parquet')
    rebuilt = pd.read_parquet(generated/'firm_year_inputs.parquet')
    pd.testing.assert_frame_equal(rebuilt, original, check_exact=True)
    record('rebuilt_panel_exact',True,rows=len(rebuilt),columns=len(rebuilt.columns))
    if not (out/'results/seed_robustness_metrics.csv').exists():
        with (out/'seed-robustness.log').open('w') as log:
            subprocess.run([sys.executable,str(package/'code/03_seed_robustness.py'),
                            '--inputs',str(generated/'firm_year_inputs.parquet'),
                            '--scores',str(generated/'results/risk_scores.parquet'),
                            '--out',str(out)],cwd=package,stdout=log,stderr=subprocess.STDOUT,check=True)
    actual = pd.read_csv(out/'results/seed_robustness_metrics.csv')
    expected = pd.read_csv(package/'results/seed_robustness_metrics.csv')
    record('seed_metric_columns',list(actual.columns)==list(expected.columns))
    actual=actual.sort_values(['seed','model']).reset_index(drop=True)
    expected=expected.sort_values(['seed','model']).reset_index(drop=True)
    record('seed_model_keys',actual[['seed','model']].equals(expected[['seed','model']]) and len(actual)==6)
    for col in expected:
        if pd.api.types.is_float_dtype(expected[col]):
            a,b=actual[col].to_numpy(float),expected[col].to_numpy(float)
            maximum=float(np.max(np.abs(a-b)))
            record('seed_metric:'+col,np.isfinite(a).all() and np.isfinite(b).all() and maximum<=1e-9,
                   max_absolute_error=maximum,atol=1e-9)
        else:
            record('seed_exact:'+col,actual[col].equals(expected[col]))
    report.update(passed=True,completed_utc=datetime.now(timezone.utc).isoformat())
    (out/'VERIFICATION.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__ == '__main__':
    main()
