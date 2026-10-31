"""Compare the STEP 4 Stata replay to frozen references, using Python stdlib only.

Run from any directory: python path/to/package/code/02_check_stata.py
Exit code 0 = passed; exit code 1 = discrepancies or incomplete replay.
All comparisons use unrounded numeric CSVs, including omitted base FE terms.
"""
from pathlib import Path
import csv
import json
import math
import sys

ROOT = Path(__file__).resolve().parents[1]
REF = ROOT / 'reference'
GOT = ROOT / 'rerun/stata'
TOL = 1e-5  # abs(a-b)/max(1,abs(reference)) for b/SE; absolute for log likelihood.


def rows(path):
    with path.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def value(x):
    return float(x) if x not in ('', '.') else float('nan')


def main():
    checks = []
    maxima = {}
    if not (GOT/'run_finished.txt').exists():
        raise ValueError('Missing rerun/stata/run_finished.txt; replay did not finish.')
    refrows, gotrows = rows(REF/'coefficients.csv'), rows(GOT/'coefficients.csv')
    ref = {(r['model_id'], r['term']): r for r in refrows}
    got = {(r['model_id'], r['term']): r for r in gotrows}
    checks.append({'name':'unique_coefficient_keys','passed':len(refrows)==len(ref) and len(gotrows)==len(got)})
    checks.append({'name': 'coefficient_keys', 'passed': set(ref)==set(got),
                   'expected_rows':len(ref),'actual_rows':len(got)})
    for field in ['coef', 'se_oim', 'se_cluster', 'p_oim', 'p_cluster']:
        maxerr = 0.0
        okay = True
        for key in set(ref)&set(got):
            a, b = value(ref[key][field]), value(got[key][field])
            if math.isnan(a) and math.isnan(b):
                continue
            if not math.isfinite(a) or not math.isfinite(b):
                okay = False
                continue
            err = abs(a-b)/max(1.0,abs(a))
            maxerr = max(maxerr,err)
        maxima[field]=maxerr
        checks.append({'name':field,'passed':okay and maxerr<=TOL,'max_scaled_error':maxerr})
    for field in ['omitted_oim','omitted_cluster']:
        checks.append({'name':field,'passed':all(value(ref[k][field])==value(got[k][field]) for k in set(ref)&set(got))})
    refmeta={r['model_id']:r for r in rows(REF/'model_summary.csv')}
    gotmeta={r['model_id']:r for r in rows(GOT/'model_summary.csv')}
    checks.append({'name':'16_model_ids','passed':len(refmeta)==16 and set(refmeta)==set(gotmeta)})
    for mid in set(refmeta)&set(gotmeta):
        a,b=refmeta[mid],gotmeta[mid]
        for field in ['N_input','N_after_pure','N_oim','N_cluster','N_clusters','converged_oim','converged_cluster','rc','base_sic2','base_fyear','core_omitted']:
            checks.append({'name':mid+':'+field,'passed':value(a[field])==value(b[field])})
        checks.append({'name':mid+':status','passed':a['status']==b['status']=='success'})
        for field in ['ll_oim','ll_cluster']:
            err=abs(value(a[field])-value(b[field]))
            maxima[field]=max(maxima.get(field,0.0),err)
            checks.append({'name':mid+':'+field,'passed':err<=TOL,'absolute_error':err})
        expected=rows(REF/f'samples/{mid}_used.csv')
        actual=rows(GOT/f'samples/{mid}_used.csv')
        for field in ['esample_oim','esample_cluster']:
            rid={r['event_id'] for r in expected if value(r[field])==1}
            gid={r['event_id'] for r in actual if value(r[field])==1}
            checks.append({'name':mid+':'+field+':IDs','passed':rid==gid and len(rid)==value(a['N_oim']),
                           'expected_N':len(rid),'actual_N':len(gid)})
    passed=all(c['passed'] for c in checks)
    report={'passed':passed,'checks_count':len(checks),'tolerance':TOL,'max_errors':maxima,
            'checks':checks,'scope':'16 annual-B score models; no original-study Replication models'}
    (GOT/'REPLAY_CHECK.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    print(json.dumps({'passed':passed,'checks':len(checks),'max_errors':maxima,
                      'report':'rerun/stata/REPLAY_CHECK.json'},indent=2))
    return 0 if passed else 1


if __name__=='__main__':
    try:
        sys.exit(main())
    except Exception as exc:
        print('STEP 4 comparison failed: '+str(exc), file=sys.stderr)
        sys.exit(1)
