"""Rebuild local and official CEO/company/time matching from raw identity inputs.

Frozen Ridge/XGBoost scores are read unchanged; this entry never trains a model.
"""
from pathlib import Path
import argparse, importlib.util, json, os, sys
sys.dont_write_bytecode = True

def load(path, name):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def run_matching(package_root,run_root=None,stage='all'):
    package=Path(package_root).resolve()
    run=Path(run_root) if run_root else package/'rerun'
    run=(run if run.is_absolute() else package/run).resolve()
    project=run/'project'
    rep=project/'replications/caliskan_doukas_2015'
    if not (rep/'data/processed/panel_master_audit.parquet').exists():
        raise FileNotFoundError('Run the raw financial/CEO/market reconstruction first: '+str(rep/'data/processed/panel_master_audit.parquet'))
    os.environ['FULLRAW_INPUT_ROOT']=str(package/'project')
    os.environ['FULLRAW_OUTPUT_ROOT']=str(project)
    savedargv=sys.argv[:]
    results=[]
    try:
        for label in (['local','official'] if stage=='all' else [stage]):
            output=rep/'data/matched'/label
            script=package/'code/matching'/('local_match.py' if label=='local' else 'official_match.py')
            module=load(script,'fullraw_'+label+'_matching')
            sys.argv=[str(script),'--out',str(output)]
            module.main()
            report=json.loads((output/'audit/validation.json').read_text(encoding='utf8'))
            results.append({'stage':label,'output_relative_to_run':output.relative_to(run).as_posix(),'validation':report})
    finally:
        sys.argv=savedargv
    summary={'status':'passed','stages':results,'score_retrained':False}
    (run/'matching_stage_summary.json').write_text(json.dumps(summary,indent=2),encoding='utf8')
    print(json.dumps({'status':'passed','stages':[r['stage'] for r in results]},indent=2),flush=True)
    return summary

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--package-root',type=Path,default=Path(__file__).resolve().parents[1])
    ap.add_argument('--run-root',type=Path)
    ap.add_argument('--stage',choices=['all','local','official'],default='all')
    args=ap.parse_args()
    run_matching(args.package_root,args.run_root,args.stage)

if __name__=='__main__':main()
