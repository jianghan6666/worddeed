"""Export a verified Windows Step 1–3 run and supplementary checks for Stata continuation."""
import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import shutil
import sys

ROOT=Path(__file__).resolve().parents[1]


def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):h.update(block)
    return h.hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    run=args.run.resolve();out=args.out.resolve()
    if out.exists():raise FileExistsError('Use a new handoff directory')
    out.mkdir(parents=True)
    def read(relative):
        path=run/relative
        return json.loads(path.read_text()) if path.is_file() else {}
    state=read('workflow/state.json');supplementary=read('supplementary/VERIFICATION.json')
    metrics=read('workflow/step3/results/metrics.json')
    passed=(all(state.get('stages',{}).get(s,{}).get('status')=='complete' for s in ['step1','step2','step3','step4_prepare'])
            and metrics.get('adapter_validation',{}).get('reproduction',{}).get('passed',False)
            and supplementary.get('passed',False))
    replacements={str(run):'REPRODUCTION_ROOT',str(ROOT):'REPOSITORY_ROOT',
                  str(Path(sys.prefix)):'ANALYSIS_ENVIRONMENT',str(Path(sys.base_prefix)):'PYTHON_BASE_ENVIRONMENT'}
    pairs=[]
    for source,target in sorted(replacements.items(),key=lambda x:len(x[0]),reverse=True):
        for value in {source,source.replace('\\','/'),json.dumps(source)[1:-1]}:
            pairs.append((value.encode(),target.encode()))
    paths=[p for p in run.glob('*.json') if p.is_file()]
    for folder in ['workflow','screening','supplementary','logs']:
        paths += [p for p in (run/folder).rglob('*') if p.is_file()]
    files=[]
    for path in sorted(paths):
        relative=path.relative_to(run).as_posix();target=out/relative;target.parent.mkdir(parents=True,exist_ok=True)
        original=digest(path)
        if path.suffix.lower() in {'.json','.jsonl','.log','.txt','.csv','.md','.html'}:
            data=path.read_bytes()
            for source,replacement in pairs:data=data.replace(source,replacement)
            target.write_bytes(data)
        else:shutil.copyfile(path,target)
        files.append({'path':relative,'bytes':target.stat().st_size,'sha256':digest(target),
                      'original_sha256':original,'portable_paths':digest(target)!=original})
    report={'passed':bool(passed),'scope':'New Windows fits, saved-record replay and full raw-data regression preparation; Stata has not run in this job',
            'repository':os.environ.get('GITHUB_REPOSITORY'),'commit':os.environ.get('GITHUB_SHA'),
            'workflow_run':os.environ.get('GITHUB_RUN_ID'),'workflow_attempt':os.environ.get('GITHUB_RUN_ATTEMPT'),
            'python':sys.version,'platform':sys.platform,'step3_rows':metrics.get('n_firm_years'),
            'stage_status':{s:r['status'] for s,r in state.get('stages',{}).items()},
            'supplementary_passed':supplementary.get('passed',False),
            'selection_sha256':digest(run/'workflow/step2/selected_topics.json') if (run/'workflow/step2/selected_topics.json').is_file() else None,
            'package_manifests':{},'files':files}
    for package,name in [('step3_risk_score_collaborator_20261027','MANIFEST.json'),('step4_full_from_raw_20261027','manifest.json')]:
        p=run/'inputs/packages'/package/name
        if p.exists():report['package_manifests'][package]=digest(p)
    (out/'HANDOFF.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='files'},indent=2))


if __name__=='__main__':main()
