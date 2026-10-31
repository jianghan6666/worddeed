"""Rebuild the complete workbook analysis from raw inputs and fixed OOF scores.

No original project directory, network login, or score training is used.
All generated files are written below --run-root (default PACKAGE/rerun).
"""
from pathlib import Path
import argparse,json,os,shutil,subprocess,sys,time,traceback
sys.dont_write_bytecode = True

def find_stata(value):
 if value:return shutil.which(value) or str(Path(value).expanduser())
 if os.environ.get('STATA_EXE'):return find_stata(os.environ['STATA_EXE'])
 for name in ['stata-se','stata-mp','stata','StataSE-64.exe','StataMP-64.exe']:
  found=shutil.which(name)
  if found:return found
 if os.name=='nt':
  for folder in ['StataNow19','Stata19']:
   for exe in ['StataSE-64.exe','StataMP-64.exe','Stata-64.exe']:
    p=Path(os.environ.get('ProgramFiles','C:/Program Files'))/folder/exe
    if p.exists():return str(p)
 return None

def main():
 ap=argparse.ArgumentParser(description=__doc__)
 ap.add_argument('--package-root',type=Path,default=Path(__file__).resolve().parents[1])
 ap.add_argument('--run-root',type=Path,help='Fresh output directory, default PACKAGE/rerun; relative to package')
 ap.add_argument('--stage',choices=['all','data','finance','matching','models','estimate','verify','report'],default='all')
 ap.add_argument('--stata-exe',help='Stata executable; may instead set STATA_EXE')
 args=ap.parse_args();pkg=args.package_root.resolve();run=args.run_root or Path('rerun');run=run.resolve() if run.is_absolute() else (pkg/run).resolve()
 if run==pkg or run==pkg/'project' or pkg/'project' in run.parents:raise ValueError('Output must be separate from immutable project inputs')
 plans={'all':['finance','matching','verify_data','models','estimate','check','report'],'data':['finance','matching','verify_data','models'],'finance':['finance'],'matching':['matching'],'models':['models'],'estimate':['estimate','check','report'],'verify':['verify_data','check'],'report':['report']}
 stages=plans[args.stage]
 if args.stage in ['all','data'] and run.exists() and any(run.iterdir()):raise FileExistsError('A full rebuild requires a fresh output directory. Supply --run-root rerun_2, or use a specific --stage to continue.')
 stata=find_stata(args.stata_exe) if 'estimate' in stages else None
 if 'estimate' in stages and (not stata or not Path(stata).exists()):raise FileNotFoundError('Stata not found. Supply --stata-exe or STATA_EXE. Use --stage data to build inputs without estimating.')
 run.mkdir(parents=True,exist_ok=True);logs=run/'logs';logs.mkdir(exist_ok=True)
 fin=run/'project/replications/caliskan_doukas_2015';reg=run/'regression';ref=pkg/'reference/regression'
 state={'status':'running','stage_requested':args.stage,'package_root':str(pkg),'run_root':str(run),'score_retraining':False,'network_access_required':False,'steps':[],'stata_executable':stata}
 status=run/'FULL_PIPELINE_STATUS.json'
 def save():status.write_text(json.dumps(state,indent=2),encoding='utf8')
 def command(label,cmd,cwd=None):
  print('Running '+label,flush=True);begin=time.monotonic();log=logs/(label+'.log')
  with log.open('w',encoding='utf8') as stream:
   flags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0
   result=subprocess.run([str(c) for c in cmd],cwd=cwd or pkg,stdout=stream,stderr=subprocess.STDOUT,creationflags=flags)
  state['steps'].append({'stage':label,'returncode':result.returncode,'seconds':time.monotonic()-begin,'log':str(log.relative_to(run))});save()
  if result.returncode:raise RuntimeError(label+' failed; inspect '+str(log))
  print('Completed '+label,flush=True)
 save();start=time.monotonic()
 try:
  for step in stages:
   common=['--package-root',pkg,'--run-root',run]
   if step=='finance':command(step,[sys.executable,'-X','utf8',pkg/'code/finance_stage.py',*common,'--stage','all'])
   elif step=='matching':command(step,[sys.executable,'-X','utf8',pkg/'code/matching_stage.py',*common,'--stage','all'])
   elif step=='verify_data':
    command('verify_finance',[sys.executable,'-X','utf8',pkg/'code/verify_finance.py',*common]);command('verify_matching',[sys.executable,'-X','utf8',pkg/'code/verify_matching.py',*common])
   elif step=='models':command(step,[sys.executable,'-X','utf8',pkg/'code/prepare_models.py','--annual-b',fin/'data/processed/table4_b_extended_2006_2023.parquet','--matched',fin/'data/matched/official/annual/table4_b_extended_2006_2023_rd_scores.parquet','--output',reg,'--reference',ref/'model_reference.json'])
   elif step=='estimate':
    script=reg/'stata/RUN_MODELS.do'
    if not script.exists():raise FileNotFoundError('Run models stage first: '+str(script))
    cmd=[stata,'/e','do',script.name] if os.name=='nt' else [stata,'-b','do',script.name]
    command(step,cmd,cwd=script.parent)
    if not (script.parent/'run_finished.txt').exists():raise RuntimeError('Stata exited without the completion marker; inspect regression/stata/regression.log')
   elif step=='check':command(step,[sys.executable,'-X','utf8',pkg/'code/check_models.py','--reference',ref,'--generated',reg])
   elif step=='report':
    command(step,[sys.executable,'-X','utf8',pkg/'code/render_replayed_tables.py','--generated',reg])
    command('presentation',[sys.executable,'-X','utf8',pkg/'code/check_presentation.py','--workbook',pkg/'results/table4_annual_b_tables.xlsx','--payload',ref/'table_payload.json','--generated',reg,'--output',run/'qa/PRESENTATION_QA.json'])
  state['status']='passed';state['seconds']=time.monotonic()-start;save();print(json.dumps({'status':'passed','run_root':str(run),'seconds':state['seconds'],'steps':len(state['steps'])},indent=2))
 except Exception:
  state['status']='failed';state['seconds']=time.monotonic()-start;state['error']=traceback.format_exc();save();raise
if __name__=='__main__':main()
