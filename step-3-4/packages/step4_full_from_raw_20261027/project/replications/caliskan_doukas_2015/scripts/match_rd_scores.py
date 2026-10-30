"""Precisely audit and match existing R&D scores. No estimation or new predictions."""
from pathlib import Path
import argparse, hashlib, json, re, unicodedata
from datetime import datetime, timezone
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[3]
REP=Path(__file__).resolve().parents[1]
SCORE=ROOT/'data/panel/risk_scores.parquet'
PANEL=ROOT/'data/panel/ceo_firm_year_panel.parquet'
CMAP=ROOT/'data/panel/component_map.parquet'
TRANS=ROOT/'data/replication_sample/transcripts_is_ceo.pickle'
ANN=REP/'data/raw/execucomp/anncomp_1992_2023_allfields.csv.gz'
MASTER=REP/'data/processed/panel_master_audit.parquet'
FUNDA=REP/'data/raw/compustat/funda_datadate_2003-01_2024-06.csv.gz'
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
 ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,default=REP/'data/matched/rd_scores_20261025');args=ap.parse_args();out=args.out.resolve()
 if out.exists():raise FileExistsError('Existing output is never overwritten; select new --out: '+str(out))
 for d in ['', 'audit','annual','pceo']:(out/d).mkdir(parents=True,exist_ok=True)
 score=pd.read_parquet(SCORE)
 panel=pd.read_parquet(PANEL,columns=['panel_id','gvkey','year','ceo_id','ceo_name','companyid','tic','datadate','fold','split_group','n_components','n_transcripts','total_words'])
 master=pd.read_parquet(MASTER)
 annual=sorted((REP/'data/processed').glob('table4_*.parquet'))
 pceo=sorted((REP/'results/table4_pceo_20261024/input/data/processed').glob('table4_*.parquet'))
 assert len(annual)==len(pceo)==6
 protected=[SCORE,PANEL,CMAP,TRANS,ANN,MASTER,FUNDA,ROOT/'data/panel/risk_scores.json',ROOT/'scripts/risk_score.py',ROOT/'agents_coop/claude.md',*annual,*pceo]
 for branch in ['table4_20261024','table4_pceo_20261024']:
  protected+=list((REP/'results'/branch).rglob('*.csv'))+list((REP/'results'/branch).glob('*manifest.json'))
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
 for branch,files in [('annual',annual),('pceo',pceo)]:
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
 validation=dict(all_protected_sha256_unchanged=True,protected_file_count=len(before),source_rows=len(score),mapped_components=len(mapped),source_key_equality=True,one_to_one_target=True,all_original_fields_exact=True,oof_transform_values_exact=True,no_regressions_or_retraining=True,no_ticker_or_ceo_year_only_join=True,no_official_vendor_crosswalk_downloaded=True,source_claude_sha256=after[str(ROOT/'agents_coop/claude.md')])
 (out/'audit/validation.json').write_text(json.dumps(validation,ensure_ascii=False,indent=2),encoding='utf-8')
 manifest=dict(created_utc=datetime.now(timezone.utc).isoformat(),operator='Codex',scope='matching_only_no_regression',output_root=str(out),source_sha256=before,source_score_columns=sc,oof_columns=oof,source_year_definition='speech calendar year deliberately equated to Compustat fyear label in source design',target_unit='unique gvkey+fyear plus selected annual/FYE ExecuComp CEO; PCEO adds frozen filter',entity_policy='exact gvkey/fyear and datadate; unique inherited source execid (or global singleton ceo_id bridge); selected execid equal; first-initial/surname support; no source ceo/person/company conflicts; one companyid',period_policy='No shifting or reaggregation. Entity score columns preserve source label convention. strict_ columns additionally require actual previous fiscal end+1=Jan1 and fiscal end=Dec31 of speech year, all observed components inside FY, no known CEO tenure date conflict',provenance_limit='Inherited execid creation procedure and official vendor links unavailable; locally supported identity, not independently vendor certified. No name-only matches.',output_tables=enriched,coverage=counts,validation=validation)
 (out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
 report=['# R&D score 匹配报告','','日期：2026-10-24（America/New_York；输出目录日期为UTC）。操作者：Codex。本步仅匹配，没有回归、重训或新分数推断。','','## 单位与分数','','源为公司×讲话自然年（2013–2023），选择发言词数最多的讲话者；目标为公司财政年及所选年度/FYE CEO。不能为2006–2011原期提供现有分数，也不跨公司搬用CEO分数。','risk_score_ridge、risk_score_xgboost及clip0/pct/z为原交叉拟合值；百分位和z保留全源29,506行的尺度。candidate_*保留源值，包括_full供审计；_full不作为后续主回归指标。','','## 标记','','- score_key_match：同公司/年份标签候选，不足以证明CEO相同。','- score_entity_match：本地实体证据通过，risk_score_*仅在这些行填值；必须同时查时间口径。','- score_fiscal_compatible：所有构成分数的实际讲话日期在目标实际财年内，且无已知任职日期冲突；年度窗口仍可能不同。','- score_strict_period_match：再要求源自然年与实际财年区间完全相等，strict_risk_score_*只在这些行填值。','- 任职开始/离职日期缺失各有标记；不触发已知冲突不等于证明全年连续任职。','','## 覆盖（输入行数，不是回归实际N）','',pd.DataFrame(counts).to_string(index=False),'','## 核验和局限','','1. 逐条核对1,420,208条component，orig_idx到orig_row一对一；源CEO、年份、component数、transcript数和词数一致。','2. 不用ticker连接、不用CEO-year单独连接、不做模糊姓名补配；同一人员ID混入不同人或同一分数混入多家公司时隔离。','3. 源execid为原始pickle携带字段，其创建程序和官方vendor桥未取得，因此实体匹配是本地证据支持，不称官方独立认证。公司名辅助检查保留；不能把子公司名称机械当发行人ID。','4. 已查官方WRDS说明：WRDS_GVKEY连接companyid/gvkey；本次CDP读取两次超时、原生App授权超时，未能取已登录连接表。需后续独立复核官方公司与People Link桥。','5. 没有静默平移年份或重聚合源分数；非同窗口行保留。要构造真正财年分数须另做方法决定和重聚合/交叉拟合，不在本步执行。','6. 分数是用R&D监督训练的预测指标；匹配不证明其独立识别CEO风险偏好。','','## 文件入口','','- master_with_rd_scores.*：保留全部35,151目标行；master_entity_matched.*和master_strict_period_matched.*为两种明确子集。','- annual/、pceo/各6张原Table4表的新增列版本，所有原字段和行数精确保留。','- coverage_summary.csv、coverage_by_year.csv：覆盖统计。','- audit/all_target_rows.*：逐行证据；rejected_or_unresolved_candidates.csv、entity_matched_period_review.csv、no_score_candidates.csv、source_rows_without_target.csv为待核清单。','- audit/source_score_identity.*与source_ceo_id_conflicts.csv：源歧义。','- audit/validation.json、manifest.json、output_manifest.json：规则、源和产物SHA、核验。','','用法：读master_with_rd_scores.parquet，最保守子样本筛score_strict_period_match，使用strict_risk_score_ridge/strict_risk_score_xgboost。若沿用源自然年=财年标签设计，可筛score_entity_match并使用risk_score_*，但须明确其时间定义，不能称为财年内全部讲话重构分数。','']
 (out/'MATCH_REPORT.md').write_text('\n'.join(report),encoding='utf-8')
 outputs=[f for f in out.rglob('*') if f.is_file() and f.name not in {'output_manifest.json','READY.txt'}]
 (out/'output_manifest.json').write_text(json.dumps([dict(path=str(f.relative_to(out)),bytes=f.stat().st_size,sha256=sha(f)) for f in outputs],ensure_ascii=False,indent=2),encoding='utf-8')
 (out/'READY.txt').write_text('Matching complete. No regressions. Read MATCH_REPORT.md and audit/validation.json.\n',encoding='utf-8')
 print(pd.DataFrame(counts).to_string(index=False),flush=True);print(json.dumps(validation,ensure_ascii=False),flush=True)
if __name__=='__main__':main()
