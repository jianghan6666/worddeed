"""Check all25 reconstructed-data Stata models against frozen published outputs.

Python standard library only. No data or regression changes are made.
"""
from pathlib import Path
import argparse
import csv
import json
import math
import sys

def read_csv(path):
    with Path(path).open(encoding='utf-8-sig',newline='') as stream:
        return list(csv.DictReader(stream))

def number(value):
    return float(value) if value not in ('','.') else float('nan')

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reference',type=Path,required=True)
    parser.add_argument('--generated',type=Path,required=True,
                        help='Generated regression directory containing stata/')
    parser.add_argument('--tolerance',type=float,default=1e-5)
    args=parser.parse_args()
    refdir=args.reference;gotdir=args.generated/'stata'
    if not (gotdir/'run_finished.txt').exists():
        raise ValueError('No run_finished marker; Stata replay did not complete')
    checks=[];maxima={}
    refrows=read_csv(refdir/'coefficients.csv')
    gotrows=read_csv(gotdir/'coefficients.csv')
    ref={(r['model_id'],r['term']):r for r in refrows}
    got={(r['model_id'],r['term']):r for r in gotrows}
    checks.append({'name':'unique_coefficient_keys',
                   'passed':len(refrows)==len(ref) and len(gotrows)==len(got)})
    checks.append({'name':'coefficient_keys','passed':set(ref)==set(got),
                   'expected_rows':len(ref),'actual_rows':len(got)})
    keys=set(ref)&set(got)
    for field in ['coef','se_oim','se_cluster','p_oim','p_cluster']:
        okay=True;maximum=0.0
        for key in keys:
            expected=number(ref[key][field]);actual=number(got[key][field])
            if math.isnan(expected) and math.isnan(actual):
                continue
            if not math.isfinite(expected) or not math.isfinite(actual):
                okay=False;continue
            error=abs(actual-expected)/max(1.0,abs(expected))
            maximum=max(maximum,error)
        maxima[field]=maximum
        checks.append({'name':field,'passed':okay and maximum<=args.tolerance,
                       'max_scaled_error':maximum})
    for field in ['omitted_oim','omitted_cluster']:
        checks.append({'name':field,'passed':all(number(ref[k][field])==
                            number(got[k][field]) for k in keys)})
    refr=read_csv(refdir/'model_summary.csv');gotr=read_csv(gotdir/'model_summary.csv')
    refmeta={r['model_id']:r for r in refr};gotmeta={r['model_id']:r for r in gotr}
    checks.append({'name':'25_model_ids','passed':len(refmeta)==25
                   and len(refmeta)==len(refr) and len(gotmeta)==len(gotr)
                   and set(refmeta)==set(gotmeta)})
    for mid in sorted(set(refmeta)&set(gotmeta)):
        expected=refmeta[mid];actual=gotmeta[mid]
        for field in ['N_input','N_after_pure','N_oim','N_cluster','N_clusters',
                      'converged_oim','converged_cluster','rc','base_sic2',
                      'base_fyear','core_omitted']:
            checks.append({'name':mid+':'+field,'passed':number(expected[field])==
                           number(actual[field])})
        checks.append({'name':mid+':status','passed':expected['status']==
                       actual['status']=='success'})
        for field in ['ll_oim','ll_cluster']:
            error=abs(number(expected[field])-number(actual[field]))
            maxima[field]=max(maxima.get(field,0.0),error)
            checks.append({'name':mid+':'+field,'passed':error<=args.tolerance,
                           'absolute_error':error})
        erows=read_csv(refdir/f'samples/{mid}_used.csv')
        arows=read_csv(gotdir/f'samples/{mid}_used.csv')
        for field in ['esample_oim','esample_cluster']:
            eids={r['event_id'] for r in erows if number(r[field])==1}
            aids={r['event_id'] for r in arows if number(r[field])==1}
            checks.append({'name':mid+':'+field+':IDs','passed':eids==aids
                           and len(eids)==number(expected['N_oim']),
                           'expected_N':len(eids),'actual_N':len(aids)})
    passed=all(c['passed'] for c in checks)
    report={'passed':passed,'checks_count':len(checks),'tolerance':args.tolerance,
            'max_errors':maxima,'checks':checks,
            'scope':'25models:9annual-B Replication +16Ridge/XGBoost score models',
            'input_origin':'DTA regenerated from reconstructed data; no frozen DTA used'}
    dest=args.generated/'audit/REGRESSION_REPLAY_QA.json';dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(report,indent=2),encoding='utf8')
    print(json.dumps({'passed':passed,'checks_count':len(checks),
                      'max_errors':maxima,'report':str(dest)},indent=2))
    return 0 if passed else 1

if __name__=='__main__':
    try:
        sys.exit(main())
    except Exception as exc:
        print('Regression validation failed: '+str(exc),file=sys.stderr)
        sys.exit(1)
