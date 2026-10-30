# Portable package adaptation: only I/O roots, source-column projection and annual-B output scope changed.
"""Precisely audit and match existing synthetic proxy of CEO risk preference. No estimation or new predictions."""
from pathlib import Path
import argparse, hashlib, json, re, unicodedata
from datetime import datetime, timezone
import numpy as np
import pandas as pd
import os
ROOT=Path(os.environ['FULLRAW_INPUT_ROOT']).resolve()
REP=Path(os.environ['FULLRAW_OUTPUT_ROOT']).resolve()/'replications/caliskan_doukas_2015'
INPUT_REP=ROOT/'replications/caliskan_doukas_2015'
SCORE=ROOT/'data/panel/risk_scores.parquet'
PANEL=ROOT/'data/panel/ceo_firm_year_panel.parquet'
CMAP=ROOT/'data/panel/component_map.parquet'
TRANS=ROOT/'data/replication_sample/transcript_identity.pickle.gz'
ANN=INPUT_REP/'data/raw/execucomp/anncomp_1992_2023_allfields.csv.gz'
MASTER=REP/'data/processed/panel_master_audit.parquet'
FUNDA=INPUT_REP/'data/raw/compustat/funda_datadate_2003-01_2024-06.csv.gz'
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def norm(v):
 if pd.isna(v):return ''
 return ' '.join(re.findall('[a-z0-9]+',unicodedata.normalize('NFKD',str(v)).encode('ascii','ignore').decode().lower()))
def cnorm(v):
 return ' '.join(t for t in norm(v).split() if t not in {'inc','incorporated','corp','corporation','co','company','ltd','limited','plc','the','llc','sa','nv'})
def intvals(s):return sorted(set(int(x) for x in s.dropna()))
def strvals(s):return sorted(set(str(x) for x in s.dropna()))
def csv(df,p):df.to_csv(p,index=False,encoding='utf-8-sig',float_format='%.17g')
def save(df,p):
 df.to_parquet(p.with_suffix('.parquet'),index=False)
 csv(df,p.with_suffix('.csv'))
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,default=REP/'data/matched/local');args=ap.parse_args();out=args.out.resolve()
 if out.exists():raise FileExistsError('Existing output is never overwritten; select new --out: '+str(out))
 for d in ['', 'audit','annual']:(out/d).mkdir(parents=True,exist_ok=True)
 score=pd.read_parquet(SCORE)
 panel=pd.read_parquet(PANEL,columns=['panel_id','gvkey','year','ceo_id','ceo_name','companyid','tic','datadate','fold','split_group','n_components','n_transcripts','total_words'])
 master=pd.read_parquet(MASTER)
 annual=sorted((REP/'data/processed').glob('table4_b_*.parquet'))
 assert len(annual)==3, 'Expected three annual-B periods from raw reconstruction'
 protected=[SCORE,PANEL,CMAP,TRANS,ANN,MASTER,FUNDA,*annual]
 protected=sorted(set(protected));before={str(f):sha(f) for f in protected}
 assert score.panel_id.is_unique and not score.duplicated(['gvkey','year']).any()
 assert not master.duplicated(['gvkey','fyear']).any()
 pd.testing.assert_frame_equal(score[['panel_id','gvkey','ceo_id','year']],panel[['panel_id','gvkey','ceo_id','year']])
 sc=[c for c in score if c.startswith('risk_score_')];oof=[c for c in sc if '_full' not in c]
 assert len(sc)==16 and len(oof)==8 and score[sc].notna().all().all()
 for m in ['ridge','xgboost']:
  v=score['risk_score_'+m]
  for suffix,expected in [('clip0',v.clip(lower=0)),('pct',v.rank(pct=True)),('z',(v-v.mean())/v.std())]:
   np.testing.assert_array_equal(score['risk_score_'+m+'_'+suffix],expected)
 print('Protected hashes and score keys checked',flush=True)
 comp=pd.read_pickle(TRANS)
 comp=comp[['orig_row','companyid','transcriptid','transcriptpersonid','directorid','transcriptpersonname','execid','exec_fullname','companyname_execucomp','companyname','mostimportantdateutc','year','retained_word_count']].copy()
 assert comp.orig_row.is_unique
 comp['ceo_id']=np.where(comp.directorid.notna(),'bx_'+comp.directorid.astype('Int64').astype(str),'tp_'+comp.transcriptpersonid.astype('Int64').astype(str))
 ceolinks=comp.dropna(subset=['execid']).groupby('ceo_id').execid.agg(intvals)
 tplinks=comp.dropna(subset=['execid','transcriptpersonid']).groupby('transcriptpersonid').execid.agg(intvals)
 comp['tp_global_conflict']=comp.transcriptpersonid.map(tplinks.map(len)).fillna(0).gt(1)
 cmap=pd.read_parquet(CMAP);assert cmap.orig_idx.is_unique
 mapped=cmap.merge(comp,left_on='orig_idx',right_on='orig_row',how='left',validate='1:1',suffixes=('_map',''),indicator=True)
 assert mapped._merge.eq('both').all()
 assert mapped.retained_word_count_map.eq(mapped.retained_word_count).all() and mapped.transcriptid_map.eq(mapped.transcriptid).all()
 mapped['speech_date']=pd.to_datetime(mapped.mostimportantdateutc,errors='raise',utc=True).dt.tz_localize(None).dt.normalize()
 assert mapped.speech_date.notna().all() and mapped.year.eq(mapped.speech_date.dt.year).all()
 mapped=mapped.merge(panel[['panel_id','ceo_id','year']].rename(columns={'ceo_id':'panel_ceo_id','year':'panel_year'}),on='panel_id',validate='m:1')
 assert mapped.ceo_id.eq(mapped.panel_ceo_id).all() and mapped.year.eq(mapped.panel_year).all()
 g=mapped.groupby('panel_id',sort=True)
 ident=g.agg(n_components_audit=('orig_idx','size'),n_transcripts_audit=('transcriptid','nunique'),words_audit=('retained_word_count','sum'),speech_first=('speech_date','min'),speech_last=('speech_date','max'),n_source_execid_nonmissing=('execid','count'),source_tp_conflict=('tp_global_conflict','any'))
 for col in ['execid','companyid','transcriptpersonid','directorid','transcriptpersonname','exec_fullname','companyname_execucomp','companyname']:
  ident[col+'_list']=g[col].agg(intvals if col.endswith('id') else strvals)
 p=panel.merge(ident.reset_index(),on='panel_id',validate='1:1')
 assert p.n_components.eq(p.n_components_audit).all() and p.n_transcripts.eq(p.n_transcripts_audit).all() and p.total_words.eq(p.words_audit).all()
 p['source_execid_count']=p.execid_list.map(len);p['source_companyid_count']=p.companyid_list.map(len)
 p['source_execid']=p.execid_list.map(lambda v:v[0] if len(v)==1 else pd.NA).astype('Int64')
 p['global_execid_list']=p.ceo_id.map(ceolinks).map(lambda v:v if isinstance(v,list) else [])
 p['source_ceo_global_conflict']=p.global_execid_list.map(len).gt(1)
 p['global_inferred_execid']=p.global_execid_list.map(lambda v:v[0] if len(v)==1 else pd.NA).astype('Int64')
 cidlinks=p[['companyid','gvkey']].drop_duplicates().groupby('companyid').gvkey.agg(intvals)
 p['companyid_gvkey_list']=p.companyid.map(cidlinks)
 p['source_companyid_global_conflict']=p.companyid_gvkey_list.map(len).gt(1)
 p['resolved_source_execid']=p.source_execid.where(p.source_execid_count.eq(1),p.global_inferred_execid.where(p.source_execid_count.eq(0)))
 p['source_identity_method']=np.select([p.source_execid_count.eq(1),p.source_execid_count.eq(0)&p.global_inferred_execid.notna(),p.source_execid_count.gt(1)],['direct_inherited_execid','cross_year_unique_source_ceo_id','ambiguous_multiple_execids'],default='no_execid_link')
 print('Component identity evidence built',len(mapped),flush=True)
 ann=pd.read_csv(ANN,usecols=['gvkey','year','execid','exec_fullname','exec_fname','exec_lname','coname','ceoann','pceo','gender'],dtype={'gvkey':'string','ceoann':'string','pceo':'string'})
 ann['gvkey']=ann.gvkey.str.zfill(6);assert not ann.duplicated(['gvkey','year','execid']).any()
 ac=ann.rename(columns={'year':'fyear','exec_fullname':'ann_exec_fullname','coname':'ann_coname','ceoann':'ann_ceoann','pceo':'ann_pceo','gender':'ann_gender'})
 target=master.merge(ac,on=['gvkey','fyear','execid'],how='left',validate='1:1',indicator='ann_join');assert target.ann_join.eq('both').all()
 p=p.merge(score[['panel_id',*sc]].rename(columns={c:'candidate_'+c for c in sc}),on='panel_id',validate='1:1')
 p['source_datadate']=pd.to_datetime(p.datadate,errors='raise');p['gvkey']=p.gvkey.astype(str).str.zfill(6)
 p=p.rename(columns={'panel_id':'score_panel_id','ceo_id':'score_ceo_id','ceo_name':'score_ceo_name','year':'score_year','tic':'score_tic','companyid':'score_companyid','fold':'score_fold','split_group':'score_split_group','datadate':'source_datadate_text'})
 for c in p:
  if c.endswith('_list'):p[c]=p[c].map(lambda v:json.dumps(v,ensure_ascii=False))
 save(p,out/'audit/source_score_identity');p=p.drop(columns=['n_components','n_transcripts','total_words'])
 j=target.merge(p,left_on=['gvkey','fyear'],right_on=['gvkey','score_year'],how='left',validate='1:1',indicator='score_key_join')
 candidate=j.score_key_join.eq('both');j['score_key_match']=candidate
 j['score_accounting_date_equal']=candidate & j.datadate.eq(j.source_datadate)
 j['score_execid_equal']=candidate & j.execid.eq(j.resolved_source_execid).fillna(False)
 def nametokens(value):
  # Vendor last-name fields contain degrees/suffixes and sometimes middle names.
  # A semicolon in CIQ names separates a title; a comma starts suffix/degree text.
  value=str(value).split(';',1)[0].split(',',1)[0]
  return [v for v in norm(value).split() if v not in {'jr','sr','ii','iii','iv','v','phd','mba','cpa','mr','mrs','ms','dr'}]
 def namecheck(row):
  if not row.score_key_match:return False
  names=json.loads(row.transcriptpersonname_list);target=nametokens(row.exec_fullname)
  if len(target)<2:return False
  surname=target[-1]
  def ok(n):
   t=nametokens(n)
   return len(t)>=2 and t[-1]==surname and t[0][0]==target[0][0]
  return all(ok(n) for n in names)
 j['score_name_support']=j.apply(namecheck,axis=1)
 j['score_entity_match']=candidate & j.score_accounting_date_equal & j.score_execid_equal & j.score_name_support
 for flag in ['source_ceo_global_conflict','source_tp_conflict','source_companyid_global_conflict']:j['score_entity_match'] &= ~j[flag].fillna(True).astype(bool)
 j['score_entity_match'] &= j.source_companyid_count.eq(1) & j.source_execid_count.le(1)
 def companycheck(row):
  return row.score_key_match and cnorm(row.ann_coname) in [cnorm(v) for v in json.loads(row.companyname_execucomp_list)]
 j['score_company_name_support']=j.apply(companycheck,axis=1)
 f=pd.read_csv(FUNDA,dtype={'gvkey':'string'},usecols=['gvkey','fyear','datadate','indfmt','datafmt','consol','curcd']);f['gvkey']=f.gvkey.str.zfill(6);f['datadate']=pd.to_datetime(f.datadate,errors='raise')
 f=f[(f.indfmt=='INDL')&(f.datafmt=='STD')&(f.consol=='C')&(f.curcd=='USD')].drop_duplicates(['gvkey','fyear','datadate'])
 u=f.groupby(['gvkey','fyear']).datadate.nunique().eq(1);f=f.merge(u.rename('unique_year'),on=['gvkey','fyear']);f=f[f.unique_year]
 lag=f[['gvkey','fyear','datadate']].copy();lag.fyear+=1;lag=lag.rename(columns={'datadate':'prior_fiscal_end'})
 j=j.merge(lag,on=['gvkey','fyear'],how='left',validate='1:1');j['fiscal_start']=j.prior_fiscal_end+pd.Timedelta(days=1)
 j['score_fiscal_bounds_known']=j.prior_fiscal_end.notna() & j.datadate.notna() & j.datadate.gt(j.prior_fiscal_end)
 j['score_speeches_within_fiscal']=candidate & j.score_fiscal_bounds_known & j.speech_first.ge(j.fiscal_start) & j.speech_last.le(j.datadate)
 j['score_speech_after_fye']=candidate & j.speech_last.gt(j.datadate)
 j['score_speech_before_fiscal_start']=candidate & j.speech_first.lt(j.fiscal_start)
 start=pd.to_datetime(j.score_year.astype('Int64').astype(str)+'-01-01',format='%Y-%m-%d',errors='coerce');end=pd.to_datetime(j.score_year.astype('Int64').astype(str)+'-12-31',format='%Y-%m-%d',errors='coerce')
 j['score_calendar_equals_fiscal']=candidate & j.fiscal_start.eq(start) & j.datadate.eq(end)
 j['score_tenure_dates_support']=candidate & (j.becameceo.isna() | j.speech_first.ge(j.becameceo)) & (j.leftofc.isna() | j.speech_last.lt(j.leftofc))
 j['score_tenure_start_known']=candidate & j.becameceo.notna();j['score_tenure_left_date_known']=candidate & j.leftofc.notna()
 j['score_fiscal_compatible']=j.score_entity_match & j.score_speeches_within_fiscal & j.score_tenure_dates_support
 j['score_strict_period_match']=j.score_fiscal_compatible & j.score_calendar_equals_fiscal
 def reason(row):
  if not row.score_key_match:return 'outside_score_year_coverage' if not 2013<=row.fyear<=2023 else 'no_gvkey_year_score'
  checks=[(not row.score_accounting_date_equal,'accounting_date_mismatch'),(row.source_execid_count>1,'multiple_source_execids'),(bool(row.source_ceo_global_conflict),'global_ceo_id_conflict'),(bool(row.source_tp_conflict),'global_transcript_person_conflict'),(row.source_companyid_count!=1,'multiple_source_companyids'),(bool(row.source_companyid_global_conflict),'global_company_id_conflict'),(pd.isna(row.resolved_source_execid),'no_execid_evidence'),(not row.score_execid_equal,'different_ceo_execid'),(not row.score_name_support,'speaker_name_requires_review')]
  return next((why for bad,why in checks if bad),'entity_link_supported')
 j['score_match_reason']=j.apply(reason,axis=1)
 j['score_time_status']=np.select([~candidate,~j.score_fiscal_bounds_known,j.score_calendar_equals_fiscal & j.score_speeches_within_fiscal,j.score_speeches_within_fiscal],['no_score','unknown_fiscal_bounds','calendar_and_fiscal_period_equal','observed_speeches_inside_fiscal_but_windows_differ'],default='speech_dates_outside_target_fiscal')
 for c in oof:
  j[c]=j['candidate_'+c].where(j.score_entity_match);j['strict_'+c]=j['candidate_'+c].where(j.score_strict_period_match)
 j['score_link_provenance']='inherited_source_execid_plus_firm_year_and_name_checks; official_vendor_bridge_unavailable'
 old=master.columns.tolist();pd.testing.assert_frame_equal(j[old].reset_index(drop=True),master.reset_index(drop=True))
 assert j.event_id.is_unique and len(j)==len(master)
 assert j.loc[j.score_entity_match,'execid'].astype('Int64').eq(j.loc[j.score_entity_match,'resolved_source_execid']).all()
 assert not j.loc[j.score_entity_match,['source_ceo_global_conflict','source_tp_conflict','source_companyid_global_conflict']].any().any()
 assert not j.loc[j.score_strict_period_match,'score_speech_after_fye'].any()
 add=[c for c in j if c not in old and c not in ac.columns and c!='ann_join']+['exec_fname','exec_lname','ann_coname']
 payload=j[['gvkey','fyear',*add]].copy()
 save(j,out/'master_with_rd_scores');save(j[j.score_entity_match].reset_index(drop=True),out/'master_entity_matched');save(j[j.score_strict_period_match].reset_index(drop=True),out/'master_strict_period_matched')
 counts=[];enriched=[]
 def summarize(df,branch,version,period):
  counts.append(dict(branch=branch,version=version,period=period,input_n=len(df),source_year_overlap_n=int(df.fyear.between(2013,2023).sum()),key_candidate_n=int(df.score_key_match.sum()),entity_matched_n=int(df.score_entity_match.sum()),company_name_support_in_entity_n=int((df.score_entity_match&df.score_company_name_support).sum()),fiscal_compatible_n=int(df.score_fiscal_compatible.sum()),strict_equal_period_n=int(df.score_strict_period_match.sum()),entity_speech_after_fye_n=int((df.score_entity_match&df.score_speech_after_fye).sum()),entity_speech_before_start_n=int((df.score_entity_match&df.score_speech_before_fiscal_start).sum())))
 summarize(j,'master','all','2006_2023')
 for branch,files in [('annual',annual)]:
  for src in files:
   df=pd.read_parquet(src);z=df.merge(payload,on=['gvkey','fyear'],how='left',validate='1:1',indicator='payload_join');assert z.payload_join.eq('both').all();z=z.drop(columns='payload_join')
   pd.testing.assert_frame_equal(z[df.columns].reset_index(drop=True),df.reset_index(drop=True))
   path=out/branch/(src.stem+'_rd_scores');save(z,path)
   summarize(z,branch,src.stem.split('_')[1].upper(),src.stem.split('_',2)[2]);enriched.append(dict(source=str(src),output=str(path.with_suffix('.parquet')),n=len(df),all_old_fields_exact=True))
 csv(pd.DataFrame(counts),out/'coverage_summary.csv')
 csv(j.groupby('fyear').agg(input_n=('event_id','size'),key_candidate_n=('score_key_match','sum'),entity_matched_n=('score_entity_match','sum'),fiscal_compatible_n=('score_fiscal_compatible','sum'),strict_equal_period_n=('score_strict_period_match','sum')).reset_index(),out/'coverage_by_year.csv')
 csv(j.groupby(['fyear','score_match_reason']).size().rename('n').reset_index(),out/'audit/match_reason_by_year.csv')
 auditcols=list(dict.fromkeys(['gvkey','fyear','event_id','valuation_id','conm','execid','exec_fullname','becameceo','leftofc','datadate','prior_fiscal_end','fiscal_start',*add]))
 audit=j[auditcols];save(audit,out/'audit/all_target_rows')
 csv(audit[audit.score_key_match & ~audit.score_entity_match],out/'audit/rejected_or_unresolved_candidates.csv')
 csv(audit[audit.score_entity_match & ~audit.score_strict_period_match],out/'audit/entity_matched_period_review.csv')
 csv(audit[~audit.score_key_match],out/'audit/no_score_candidates.csv')
 csv(p[~p.score_panel_id.isin(j.score_panel_id.dropna().astype(int))],out/'audit/source_rows_without_target.csv')
 conflict=ceolinks[ceolinks.map(len)>1].rename('execids').reset_index();conflict.execids=conflict.execids.map(json.dumps);csv(conflict,out/'audit/source_ceo_id_conflicts.csv')
 after={str(f):sha(f) for f in protected};assert before==after,'Protected source/result/Claude file changed during run'
 validation=dict(all_protected_sha256_unchanged=True,protected_file_count=len(before),source_rows=len(score),mapped_components=len(mapped),source_key_equality=True,one_to_one_target=True,all_original_fields_exact=True,oof_transform_values_exact=True,no_regressions_or_retraining=True,no_ticker_or_ceo_year_only_join=True,local_stage_does_not_apply_official_crosswalk=True)
 (out/'audit/validation.json').write_text(json.dumps(validation,ensure_ascii=False,indent=2),encoding='utf-8')
 manifest=dict(created_utc=datetime.now(timezone.utc).isoformat(),operator='Codex',scope='matching_only_no_regression',output_root=str(out),source_sha256=before,source_score_columns=sc,oof_columns=oof,source_year_definition='speech calendar year deliberately equated to Compustat fyear label in source design',target_unit='unique gvkey+fyear plus selected annual/FYE ExecuComp CEO; annual-B only, no PCEO filter',entity_policy='exact gvkey/fyear and datadate; unique inherited source execid (or global singleton ceo_id bridge); selected execid equal; first-initial/surname support; no source ceo/person/company conflicts; one companyid',period_policy='No shifting or reaggregation. Entity score columns preserve source label convention. strict_ columns additionally require actual previous fiscal end+1=Jan1 and fiscal end=Dec31 of speech year, all observed components inside FY, no known CEO tenure date conflict',provenance_limit='Inherited execid creation procedure and official vendor links unavailable; locally supported identity, not independently vendor certified. No name-only matches.',output_tables=enriched,coverage=counts,validation=validation)
 (out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
 report=['# Local source-identity matching replay','','This is the first matching stage. It reconstructs inherited-ID, name, company and period guards from the frozen score-source records. It does not certify official identity; the following official stage applies the supplied raw WRDS company and person bridges.','','All 1,775,355 raw identity rows are retained before global conflict detection. component_map then selects 1,420,208 actual score components. Frozen OOF scores are never retrained or relabeled.','','Only the three annual-B period tables are enriched. No PCEO or A branch is run.','','## Coverage','',pd.DataFrame(counts).to_string(index=False),'','## Reproduction','','From the package directory run: python code/matching_stage.py --stage all. The raw financial/CEO reconstruction must be completed first.','Source data and hashes are listed in manifest.json; per-row guards and unresolved candidates are under audit/.','']
 (out/'MATCH_REPORT.md').write_text('\n'.join(report),encoding='utf-8')
 outputs=[f for f in out.rglob('*') if f.is_file() and f.name not in {'output_manifest.json','READY.txt'}]
 (out/'output_manifest.json').write_text(json.dumps([dict(path=str(f.relative_to(out)),bytes=f.stat().st_size,sha256=sha(f)) for f in outputs],ensure_ascii=False,indent=2),encoding='utf-8')
 (out/'READY.txt').write_text('Matching complete. No regressions. Read MATCH_REPORT.md and audit/validation.json.\n',encoding='utf-8')
 print(pd.DataFrame(counts).to_string(index=False),flush=True);print(json.dumps(validation,ensure_ascii=False),flush=True)
if __name__=='__main__':main()
