# Portable package adaptation: I/O roots and annual-B output scope only; match criteria unchanged.
"""Official WRDS ID verification of frozen synthetic proxy of CEO risk preference, no estimation or retraining."""
from pathlib import Path
from datetime import datetime, timezone
import argparse,hashlib,json
import numpy as np
import pandas as pd
import os
ROOT=Path(os.environ['FULLRAW_INPUT_ROOT']).resolve()
REP=Path(os.environ['FULLRAW_OUTPUT_ROOT']).resolve()/'replications/caliskan_doukas_2015'
OLD=REP/'data/matched/local'
RAW=ROOT/'replications/caliskan_doukas_2015/data/raw/linking_20261025'
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def vals(s):return sorted(set(int(v) for v in s.dropna()))
def strs(s):return sorted(set(str(v) for v in s.dropna()))
def csv(df,p):df.to_csv(p,index=False,encoding='utf-8-sig',float_format='%.17g')
def save(df,p):
 df.to_parquet(p.with_suffix('.parquet'),index=False);csv(df,p.with_suffix('.csv'))
def js(v):return json.dumps(v,ensure_ascii=False)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,default=REP/'data/matched/official');args=ap.parse_args();out=args.out.resolve()
 if out.exists():raise FileExistsError('Output immutable; use a new --out directory: '+str(out))
 for d in ['', 'audit','annual']:(out/d).mkdir(parents=True,exist_ok=True)
 protected=[f for f in OLD.rglob('*') if f.is_file()]+[f for f in RAW.rglob('*') if f.is_file()]
 oldmanifest=json.loads((OLD/'manifest.json').read_text(encoding='utf-8'))
 protected+= [Path(p) for p in oldmanifest['source_sha256']]
 protected+=[ROOT/'data/panel/risk_scores.parquet',ROOT/'data/panel/ceo_firm_year_panel.parquet',ROOT/'data/panel/component_map.parquet',ROOT/'data/replication_sample/transcript_identity.pickle.gz']
 protected=sorted(set(protected));before={str(p):sha(p) for p in protected}
 (out/'audit/protected_inputs_before.json').write_text(json.dumps(before,indent=2),encoding='utf-8')
 print('Protected input hashes recorded',flush=True)
 master=pd.read_parquet(OLD/'master_with_rd_scores.parquet');source=pd.read_parquet(OLD/'audit/source_score_identity.parquet')
 oldcols=master.columns.tolist();assert master.event_id.is_unique and source.score_panel_id.is_unique
 company=pd.read_csv(RAW/'ciq_wrds_gvkey_all.csv.gz',dtype={'gvkey':'string'});people=pd.read_csv(RAW/'people_link_execucomp_boardex_all.csv.gz')
 assert len(company)==145303 and len(people)==44373
 company['gvkey']=company.gvkey.str.zfill(6);company['official_company_row_id']=np.arange(len(company))
 company['link_start']=pd.to_datetime(company.startdate,errors='raise');company['link_end']=pd.to_datetime(company.enddate,errors='raise')
 people['official_person_row_id']=np.arange(len(people));assert people['score'].between(1,13).all()
 # Reconstruct actual company/date requests from every mapped source component, not modal panel IDs.
 comp=pd.read_pickle(ROOT/'data/replication_sample/transcript_identity.pickle.gz')
 comp=comp[['orig_row','companyid','mostimportantdateutc','directorid','transcriptpersonid','proid']].copy();assert comp.orig_row.is_unique
 cmap=pd.read_parquet(ROOT/'data/panel/component_map.parquet',columns=['orig_idx','panel_id']);assert cmap.orig_idx.is_unique
 mapped=cmap.merge(comp,left_on='orig_idx',right_on='orig_row',how='left',validate='1:1',indicator=True)
 assert mapped._merge.eq('both').all() and len(mapped)==1420208
 mapped['request_date']=pd.to_datetime(mapped.mostimportantdateutc,errors='raise',utc=True).dt.tz_localize(None).dt.normalize()
 requests=mapped[['panel_id','companyid','request_date']].drop_duplicates().rename(columns={'panel_id':'score_panel_id'});requests['request_kind']='speech'
 allcids=source[['score_panel_id','companyid_list','source_datadate']].copy();allcids['companyid']=allcids.companyid_list.map(json.loads);allcids=allcids.explode('companyid');allcids['companyid']=allcids.companyid.astype('int64')
 acc=allcids[['score_panel_id','companyid','source_datadate']].rename(columns={'source_datadate':'request_date'});acc['request_kind']='accounting_date'
 requests=pd.concat([requests,acc],ignore_index=True).merge(source[['score_panel_id','gvkey']],on='score_panel_id',validate='m:1').rename(columns={'gvkey':'source_gvkey'});requests['companyid']=requests.companyid.astype('int64');requests['request_id']=np.arange(len(requests))
 evidence=requests.merge(company,on='companyid',how='left',validate='m:m')
 evidence['link_active_under_missing_bound_convention']=evidence.official_company_row_id.notna() & evidence.request_date.notna() & (evidence.link_start.isna()|evidence.request_date.ge(evidence.link_start)) & (evidence.link_end.isna()|evidence.request_date.le(evidence.link_end))
 evidence['expected_pair']=evidence.gvkey.eq(evidence.source_gvkey).fillna(False)
 evidence['link_bounds_both_missing']=evidence.link_start.isna()&evidence.link_end.isna()
 active=evidence[evidence.link_active_under_missing_bound_convention]
 req=requests.copy();agg=active.groupby('request_id').agg(official_active_gvkeys=('gvkey',lambda s:sorted(set(str(x) for x in s.dropna()))),active_row_ids=('official_company_row_id',vals),active_uses_undated_link=('link_bounds_both_missing','any'),active_has_explicit_bound=('link_bounds_both_missing',lambda s:bool((~s).any())))
 req=req.merge(agg,left_on='request_id',right_index=True,how='left',validate='1:1')
 hascompany=set(company.companyid);req['official_company_exists']=req.companyid.isin(hascompany)
 req['official_active_gvkeys']=req.official_active_gvkeys.map(lambda x:x if isinstance(x,list) else [])
 req['active_row_ids']=req.active_row_ids.map(lambda x:x if isinstance(x,list) else [])
 req['official_request_status']=req.apply(lambda r:'no_company_link' if not r.official_company_exists else 'no_active_link_at_date' if not r.official_active_gvkeys else 'multiple_active_gvkeys' if len(r.official_active_gvkeys)>1 else 'consistent' if r.official_active_gvkeys[0]==r.source_gvkey else 'different_gvkey',axis=1)
 req['official_request_verified']=req.official_request_status.eq('consistent')
 for c in ['active_uses_undated_link','active_has_explicit_bound']:req[c]=req[c].fillna(False).astype(bool)
 cs=req.groupby('score_panel_id').agg(official_company_all_requests_consistent=('official_request_verified','all'),official_company_request_n=('request_id','size'),official_company_failed_request_n=('official_request_verified',lambda s:int((~s).sum())),official_company_undated_request_n=('active_uses_undated_link','sum'),official_company_explicit_bound_request_n=('active_has_explicit_bound','sum'),official_company_request_status_list=('official_request_status',strs))
 source=source.merge(cs,on='score_panel_id',validate='1:1')
 def cstatus(r):
  if r.source_companyid_count!=1:return 'multiple_source_companyids'
  v=r.official_company_request_status_list
  for s in ['different_gvkey','multiple_active_gvkeys','no_company_link','no_active_link_at_date']:
   if s in v:return s
  return 'consistent'
 source['official_company_status']=source.apply(cstatus,axis=1)
 source['official_company_verified']=source.official_company_status.eq('consistent')
 source['official_company_temporal_evidence']=np.select([source.official_company_explicit_bound_request_n.eq(0),source.official_company_undated_request_n.eq(0)],['undated_links_only','explicit_bounds_on_all_requests'],default='mixed_or_partial_date_bounds')
 source['official_company_dates_convention']='start/end inclusive when recorded; missing endpoint treated unbounded for ID compatibility, not proof of complete historical validity'
 # Preserve component personnel identifiers, including PROID, without equating separate namespaces.
 mg=mapped.groupby('panel_id');extra=mg.agg(actual_directorids=('directorid',vals),actual_transcriptpersonids=('transcriptpersonid',vals),actual_proids=('proid',vals),n_missing_director_components=('directorid',lambda s:int(s.isna().sum())),n_missing_proid_components=('proid',lambda s:int(s.isna().sum())))
 source=source.merge(extra,left_on='score_panel_id',right_index=True,validate='1:1')
 assert source.directorid_list.map(json.loads).eq(source.actual_directorids).all()
 assert source.transcriptpersonid_list.map(json.loads).eq(source.actual_transcriptpersonids).all()
 source['official_directorid']=source.actual_directorids.map(lambda v:v[0] if len(v)==1 else pd.NA).astype('Int64')
 pg=people.groupby('directorid')
 psummary=pg.agg(official_person_any_execids=('execid',vals),official_person_min_score=('score','min'),official_person_raw_rows=('execid','size'),official_person_matchstyles=('matchStyle',strs))
 for label,mask in [('score1',people.score.eq(1)),('company_backed',people.score.between(1,8)),('existing',people.score.eq(9)),('age',people.score.isin([10,12]))]:
  a=people[mask].groupby('directorid').execid.agg(vals).rename('official_person_'+label+'_execids');psummary=psummary.join(a)
 for c in psummary:
  if c.endswith('_execids') or c.endswith('_matchstyles'):psummary[c]=psummary[c].map(lambda x:x if isinstance(x,list) else [])
 source=source.merge(psummary,left_on='official_directorid',right_index=True,how='left',validate='m:1')
 for c in psummary:
  if c.endswith('_execids') or c.endswith('_matchstyles'):source[c]=source[c].map(lambda x:x if isinstance(x,list) else [])
 source['official_person_score1_unique_execid']=source.official_person_score1_execids.map(lambda x:x[0] if len(x)==1 else pd.NA).astype('Int64')
 def source_person_status(r):
  if not str(r.score_ceo_id).startswith('bx_'):return 'unverified_transcript_namespace'
  if len(r.actual_directorids)!=1 or r.n_missing_director_components:return 'multiple_or_missing_directorid'
  if not r.official_person_any_execids:return 'no_director_link'
  if len(r.official_person_score1_execids)>1:return 'multiple_score1_execids'
  if len(r.official_person_score1_execids)==1:return 'unique_score1_link_available'
  if r.official_person_company_backed_execids:return 'company_backed_link_below_score1'
  if r.official_person_existing_execids:return 'existing_only_or_with_age'
  return 'age_only_candidates_not_confirmation'
 source['official_source_person_status']=source.apply(source_person_status,axis=1)
 # Full raw rows are preserved. No score threshold is presented as an author rule.
 pairs=source[['score_panel_id','official_directorid','score_ceo_id']].merge(people,left_on='official_directorid',right_on='directorid',how='left',validate='m:m')
 for c in req:
  if c in ['official_active_gvkeys','active_row_ids']:req[c]=req[c].map(js)
 save(req,out/'audit/company_date_requests')
 evidence.to_parquet(out/'audit/company_link_row_evidence.parquet',index=False)
 pairs.to_parquet(out/'audit/person_link_row_evidence.parquet',index=False)
 for c in source:
  if c in ['official_company_request_status_list','actual_directorids','actual_transcriptpersonids','actual_proids'] or c in psummary.columns and (c.endswith('_execids') or c.endswith('_matchstyles')):source[c]=source[c].map(js)
 save(source,out/'audit/source_official_identity')
 # Add only official columns to the frozen target; source GVKEY, CEO IDs and scores are never rewritten.
 sourcecols=[c for c in source if c.startswith('official_') or c.startswith('actual_') or c.startswith('n_missing_')]
 new=source[['score_panel_id',*sourcecols]]
 j=master.merge(new,on='score_panel_id',how='left',validate='m:1');pd.testing.assert_frame_equal(j[oldcols],master)
 candidate=j.score_key_match
 for flag in ['official_company_verified','official_company_all_requests_consistent']:j[flag]=j[flag].fillna(False).astype(bool)
 listcols=[c for c in sourcecols if c.endswith('_execids') or c.endswith('_matchstyles') or c.endswith('_list') or c.startswith('actual_')]
 def parse(v):return json.loads(v) if isinstance(v,str) else []
 def target_person_status(r):
  if not r.score_key_match:return 'no_source_score'
  s=r.official_source_person_status
  anyids=parse(r.official_person_any_execids);best=parse(r.official_person_score1_execids);backed=parse(r.official_person_company_backed_execids)
  if s=='unique_score1_link_available':return 'consistent_score1' if best[0]==r.execid else 'different_execid_score1'
  if s=='company_backed_link_below_score1':return 'supported_lower_quality_company_backed' if r.execid in backed else 'different_execid_company_backed'
  if s in ['existing_only_or_with_age','age_only_candidates_not_confirmation']:
   return 'supported_only_existing_or_age' if r.execid in anyids else 'low_quality_disagreement_not_proven_wrong'
  return s
 j['official_person_status']=j.apply(target_person_status,axis=1)
 j['official_person_pair_any_score']=j.apply(lambda r:r.score_key_match and r.execid in parse(r.official_person_any_execids),axis=1)
 j['official_person_pair_company_backed']=j.apply(lambda r:r.score_key_match and r.execid in parse(r.official_person_company_backed_execids),axis=1)
 j['official_person_verified']=j.official_person_status.eq('consistent_score1')
 # All existing mixed-person/family/company quarantines remain in force.
 j['official_local_guards']=candidate & j.score_accounting_date_equal & j.score_name_support & j.source_companyid_count.eq(1) & j.source_execid_count.le(1)
 for c in ['source_ceo_global_conflict','source_tp_conflict','source_companyid_global_conflict']:j['official_local_guards'] &= ~j[c].fillna(True).astype(bool)
 j['official_inherited_execid_compatible']=candidate & (j.resolved_source_execid.isna() | j.resolved_source_execid.eq(j.execid).fillna(False))
 j['official_entity_verified']=j.official_local_guards & j.official_inherited_execid_compatible & j.official_company_verified & j.official_person_verified
 j['official_fiscal_compatible']=j.official_entity_verified & j.score_speeches_within_fiscal & j.score_tenure_dates_support
 j['official_strict_period_match']=j.official_fiscal_compatible & j.score_calendar_equals_fiscal
 j['official_newly_verified']=j.official_entity_verified & ~j.score_entity_match
 j['official_old_accepted_not_verified']=j.score_entity_match & ~j.official_entity_verified
 j['official_primary_person_policy']='score=1 highest quality with unique execid for the one actual BoardEx directorid; researcher conservative policy, not original-study rule'
 j['official_no_upstream_remap']=True
 oof=[c[len('candidate_'):] for c in master if c.startswith('candidate_risk_score_') and '_full' not in c]
 assert len(oof)==8
 for c in oof:
  j['vendor_'+c]=j['candidate_'+c].where(j.official_entity_verified)
  j['vendor_strict_'+c]=j['candidate_'+c].where(j.official_strict_period_match)
 assert len(j)==len(master) and j.event_id.is_unique
 pd.testing.assert_frame_equal(j[oldcols],master)
 assert not j.loc[j.official_entity_verified,'score_ceo_id'].str.startswith('tp_').any()
 assert j.loc[j.official_entity_verified,'execid'].astype('Int64').eq(j.loc[j.official_entity_verified,'official_person_score1_unique_execid']).all()
 assert not (j.official_entity_verified & ~j.official_company_verified).any()
 assert not j.loc[j.official_entity_verified,['source_ceo_global_conflict','source_tp_conflict','source_companyid_global_conflict']].any().any()
 assert not (j.official_newly_verified & j.resolved_source_execid.notna()).any(), 'Only unresolved inherited identities may be recovered'
 newcols=[c for c in j if c not in oldcols]
 save(j,out/'master_with_rd_scores')
 save(j[j.official_entity_verified].reset_index(drop=True),out/'master_official_entity_matched')
 save(j[j.official_strict_period_match].reset_index(drop=True),out/'master_official_strict_period_matched')
 payload=j[['gvkey','fyear',*newcols]];counts=[];tablefiles=[]
 def count(df,branch,version,period):
  counts.append(dict(branch=branch,version=version,period=period,input_n=len(df),candidate_n=int(df.score_key_match.sum()),old_entity_n=int(df.score_entity_match.sum()),official_company_verified_n=int(df.official_company_verified.sum()),official_person_any_score_pair_n=int(df.official_person_pair_any_score.sum()),official_person_verified_n=int(df.official_person_verified.sum()),official_entity_n=int(df.official_entity_verified.sum()),official_fiscal_compatible_n=int(df.official_fiscal_compatible.sum()),official_strict_n=int(df.official_strict_period_match.sum()),newly_verified_n=int(df.official_newly_verified.sum()),old_accepted_not_verified_n=int(df.official_old_accepted_not_verified.sum())))
 count(j,'master','all','2006_2023')
 for branch in ['annual']:
  files=sorted((OLD/branch).glob('*.parquet'));assert len(files)==3
  for p in files:
   df=pd.read_parquet(p);z=df.merge(payload,on=['gvkey','fyear'],how='left',validate='1:1',indicator='payload_join');assert z.payload_join.eq('both').all();z=z.drop(columns='payload_join');pd.testing.assert_frame_equal(z[df.columns],df)
   save(z,out/branch/p.stem);count(z,branch,p.stem.split('_')[1].upper(),p.stem.split('_',2)[2].replace('_rd_scores',''));tablefiles.append(dict(input=str(p),output=str(out/branch/(p.stem+'.parquet')),rows=len(z),all_old_columns_exact=True))
 csv(pd.DataFrame(counts),out/'coverage_summary.csv')
 csv(j.groupby('fyear').agg(input_n=('event_id','size'),candidate_n=('score_key_match','sum'),old_entity_n=('score_entity_match','sum'),official_entity_n=('official_entity_verified','sum'),official_strict_n=('official_strict_period_match','sum'),newly_verified_n=('official_newly_verified','sum'),old_accepted_not_verified_n=('official_old_accepted_not_verified','sum')).reset_index(),out/'coverage_by_year.csv')
 csv(j.groupby(['fyear','official_person_status']).size().rename('n').reset_index(),out/'audit/person_status_by_year.csv')
 csv(j[j.score_key_match].groupby(['official_company_status','official_person_status']).size().rename('n').reset_index(),out/'audit/company_person_status_counts.csv')
 acols=['gvkey','fyear','event_id','conm','execid','exec_fullname','score_panel_id','score_ceo_id','score_ceo_name','companyid_list','directorid_list','resolved_source_execid','source_identity_method','score_key_match','score_entity_match','score_strict_period_match','score_match_reason','score_time_status',*newcols]
 acols=list(dict.fromkeys(acols));audit=j[acols]
 save(audit,out/'audit/all_target_rows')
 csv(audit[audit.official_newly_verified],out/'audit/newly_verified_missing_inherited_execid.csv')
 csv(audit[audit.official_old_accepted_not_verified],out/'audit/old_accepted_not_officially_verified.csv')
 csv(audit[audit.score_key_match & ~audit.official_entity_verified],out/'audit/unverified_candidates.csv')
 csv(audit[audit.official_entity_verified & ~audit.official_strict_period_match],out/'audit/entity_verified_period_review.csv')
 csv(source[source.official_company_status.isin(['different_gvkey','multiple_active_gvkeys','no_company_link','no_active_link_at_date','multiple_source_companyids'])],out/'audit/source_company_problem_queue.csv')
 csv(people.groupby(['score','matchStyle']).size().rename('n').reset_index(),out/'audit/official_person_quality_distribution.csv')
 descriptions={'official_entity_verified':'公司所有实际讲话和源会计日期均唯一对应原GVKEY、人员最高质量score1唯一对应目标execid，且本地歧义/姓名/继承execid守卫通过；不是完全认证每段讲话原始ID赋值','official_strict_period_match':'新官方实体通过并满足原已核讲话包含/任职日期/自然年财年完整区间相等','official_fiscal_compatible':'新官方实体通过且实际讲话位于财年内、无已知任职日期冲突','official_company_verified':'每个实际companyid及讲话/源会计日期仅有一个有效GVKEY且等于原source GVKEY；缺失链接端点按无界约定','official_person_verified':'BoardEx directorid的score1链接唯一execid且等于目标；研究者保守阈值，不是原文设定','official_newly_verified':'旧实体未通过，但缺失的继承execid已由官方BoardEx最高质量唯一链接补证；不改旧列','official_old_accepted_not_verified':'旧本地实体通过，但新官方条件未全部满足；不等于已证实旧CEO错误','official_company_temporal_evidence':'undated_links_only不证明历史有效期，mixed_or_partial_date_bounds保留日期不足','official_person_status':'区分无链接、低质量、年龄型不一致、公司型不一致、最高质量一致、命名空间不可验证等','actual_proids':'实际component的professional实例ID；不等同personid或transcriptpersonid，需要ciqprofessional桥'}
 dictionary=[]
 for c in newcols:
  d=descriptions.get(c,'官方链接证据/诊断，详见脚本和报告；不能单列作身份认证')
  if c.startswith('vendor_strict_risk_score_'):d='原交叉拟合源分数逐值复制，仅official_strict_period_match为真；变换未重算'
  elif c.startswith('vendor_risk_score_'):d='原交叉拟合源分数逐值复制，仅official_entity_verified为真；须另查时间口径'
  dictionary.append(dict(field=c,dtype=str(j[c].dtype),definition=d))
 csv(pd.DataFrame(dictionary),out/'match_variable_dictionary.csv')
 after={str(p):sha(p) for p in protected};assert before==after,'Protected source, old outputs, or Claude document changed during build'
 validation=dict(status='passed',protected_files=len(protected),protected_sha256_unchanged=True,all_old_master_columns_exact=True,all_3_annual_B_tables_prior_columns_exact=True,source_rows=len(source),master_rows=len(j),mapped_components=len(mapped),company_date_requests=len(requests),source_score_values_exact=True,no_regression_or_retraining=True,no_upstream_gvkey_or_speaker_remap=True,no_transcript_to_personid_numeric_comparison=True,unique_highest_quality_person_policy=True)
 (out/'audit/validation.json').write_text(json.dumps(validation,ensure_ascii=False,indent=2),encoding='utf-8')
 manifest=dict(created_utc=datetime.now(timezone.utc).isoformat(),operator='Codex',scope='official_link_matching_only_no_regression',protected_sha256=before,builder_sha256=sha(Path(__file__)),input_old_matching=str(OLD),official_raw_root=str(RAW),company_validity_policy='Check all mapped component companyid/date plus each constituent company source accounting date; inclusive observed bounds; missing endpoints unbounded convention, not historical certification; all requests must have unique active target GVKEY',person_policy='BoardEx only; unique execid among score1 highest quality links. Preserve all other scores and styles as diagnostics. Explicit sourceexecid contradiction never overridden, all old family/mixed-ID quarantine remains.',ciq_person_limit='Transcripts and People Intelligence products denied for current account; E-Cquery11828367 returned0; professional PROID is not personid, required ciqprofessional bridge unavailable',recovery_policy='Recover absent inheritedexecid only when official exact BoardEx-ID pair, same original company/calendarlabel/accountingdate/name and existing guards pass; do not move score to corrected GVKEY or change source aggregates/model',output_tables=tablefiles,coverage=counts,validation=validation)
 (out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
 table=['| 分支 | 版本 | 原输入N | 旧实体N | 官方实体N | 财年内兼容N | 严格同窗口N | 新补证N | 旧接受未获官方通过N |','|---|---|---:|---:|---:|---:|---:|---:|---:|']
 for r in counts:
  if r['branch']=='master' or r['period']=='extended_2006_2023':table.append('| '+str(r['branch'])+' | '+r['version']+' | '+' | '.join(f"{r[k]:,}" for k in ['input_n','old_entity_n','official_entity_n','official_fiscal_compatible_n','official_strict_n','newly_verified_n','old_accepted_not_verified_n'])+' |')
 report=['# WRDS官方连接核验后的synthetic proxy of CEO risk preference匹配','','操作者：Codex。本阶段只补充官方身份核验，未运行回归、重训、生成新分数或修复源训练面板。旧版匹配及所有旧列完整保留，新增vendor_*分数和official_*标记。','','## 覆盖和调用','',*table,'','以上均为匹配输入行数，非回归实际N。现有分数仍仅2013–2023，不能匹配2006–2011原期。','最保守调用：读annual/下相应parquet，筛official_strict_period_match，使用vendor_strict_risk_score_ridge和vendor_strict_risk_score_xgboost。若仅需要官方实体匹配，筛official_entity_verified并用vendor_risk_score_*，同时解释原自然年标签与财年的差异。_clip0/_pct/_z均保持源值；_full未进入vendor主列。','','## 官方公司核验','','CIQ wrds_gvkey全表145303行，6字段，查询11828375；所有实际组成component的companyid/日期，加每个公司对应源会计期末，共逐请求核验；不只看panel众数companyid。记录的startdate/enddate按含端点比较；缺失端点按无界处理是一项兼容性约定，不代表证实全部历史有效期。若同一日期存在多个GVKEY、不同GVKEY、无链接、超出已知日期等，保留原因并不放行。','发现源GVKEY与官方链接不符时不自动把分数搬给另一个公司：源R&D标签、fold/group和CEO选择可能已受上游错配影响，官方ID复核不能替代源面板重建或重训。','','## 官方人员核验','','People Link全表44373行，查询11828366，保留全部16字段和全部质量分数/匹配方式。官方变量说明1为最高质量、13最低。当前主验收用score=1且该directorid只对应一个execid，须等于回归表选定execid。这是研究者为精准匹配设定的保守规则，不是论文或WRDS要求的唯一阈值。','公司支持型score1–8、existing9、年龄型10/12及一对多都保留诊断。只有低质量年龄候选与旧execid不同，不能据此称旧CEO已被证实错误。','仅直接使用BoardEx directorid；源tp_的transcriptpersonid不等于CIQ People Intelligence personid。PROID官方定义是人与公司等机构的professional实例，也不等于personid。需要ciqprofessional(proid,personid,companyid)桥。当前账号明确无ciq_transcripts、ciq_pplintel权限，ExecuComp-CIQ People Link全量查询11828367返回空；这些行继续待核，不按数字相同补配。','官方directorid↔execid只能认证ID对，不能认证每段讲话原始directorid赋值正确。因此原同名家族/多execid/多公司/人员冲突隔离规则仍保留，明确不一致的继承execid不覆盖。','旧缺execid的行若现在获得唯一最高质量BoardEx链接，且公司/姓名/会计日/其他歧义守卫全部通过，可以新增official_entity_verified；旧列和旧拒配原因仍保留以便审计。','','## 验证','','Master全部293个旧列及3张年度B输入的所有旧列、行序、行数和dtype精确保留；新vendor分数逐值复制candidate交叉拟合源值。原自然年/财年、任职日期、讲话区间标记未变。独立源资料和旧结果SHA保护详见manifest.json。原strict标记不是本次新官方标记，调用勿混淆。','有些公司链接没有历史端点；有些CEO任职日期仍缺失；这些未知不是完整历史认证。score_tenure_start_known和score_tenure_left_date_known继续保留。','','## 文件入口','','- master_with_rd_scores.parquet/csv：全部35151目标行和新增官方证据。','- master_official_entity_matched.* / master_official_strict_period_matched.*：明确新口径子集。','- annual/下3张年度B附表，全部旧列不变。','- coverage_summary.csv、coverage_by_year.csv：匹配数和新旧变化。','- audit/source_official_identity.*：全29506源分数的官方公司、人员和组件ID证据。','- audit/company_date_requests.*、company_link_row_evidence.parquet、person_link_row_evidence.parquet：请求、官方原表行号与质量证据。','- audit/newly_verified_missing_inherited_execid.csv、old_accepted_not_officially_verified.csv、unverified_candidates.csv、entity_verified_period_review.csv、source_company_problem_queue.csv：逐行复核清单。','- match_variable_dictionary.csv、manifest.json、audit/validation.json、output_manifest.json：字段、规则、来源和产物SHA。','- 原始来源、查询/权限与原始SQL状态：data/raw/linking_20261025/acquisition_metadata.json（相对replication根）。','','## 可复现命令','','From the package directory run: python code/matching_stage.py --stage all. Financial reconstruction must already be complete. Outputs are written only under the selected run-root; existing matching directories are never overwritten.','']
 (out/'MATCH_REPORT.md').write_text('\n'.join(report),encoding='utf-8')
 outputs=[p for p in out.rglob('*') if p.is_file() and p.name not in ['output_manifest.json','READY.txt']]
 (out/'output_manifest.json').write_text(json.dumps([dict(path=str(p.relative_to(out)),bytes=p.stat().st_size,sha256=sha(p)) for p in outputs],ensure_ascii=False,indent=2),encoding='utf-8')
 (out/'READY.txt').write_text('Official matching build complete; no regressions. Read MATCH_REPORT and validation.\n',encoding='utf-8')
 print(pd.DataFrame(counts).to_string(index=False),flush=True);print(json.dumps(validation,ensure_ascii=False),flush=True)
if __name__=='__main__':main()
