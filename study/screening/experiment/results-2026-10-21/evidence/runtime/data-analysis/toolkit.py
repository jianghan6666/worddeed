#!/usr/bin/env python3
"""Frozen Step 2 packet/import/export tools. No inference, votes or study dispatch."""
import argparse
import csv
import hashlib
import json
import shutil
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parents[2]
EXPORT = PROJECT / '.local/coauthor-handoff-2026-10-13/checkout'
PROTOCOL = EXPORT / 'step-2-mvp-simple/experiment/expanded-ai-pilot'
INSPECTION = PROJECT / '.local/step2-source-trace-inspection-2026-10-20'
INITIAL = 'initial_descriptor'
REVIEW = 'source_review'
VERSION = 'step2_native_staged_v1'
CHUNK_CHARS = 12000  # transport fragment, not a research/context/time budget
LIMITS = [
 'Exact retained masked/processed component text; not an unmodified or complete call.',
 'All exact-text candidate matches are retained; duplicate text does not identify one speaker.',
 'Delivered CEO-subset membership/flag is attribution, not independently verified role or tenure.',
 'No match in the delivered CEO subset does not independently establish a non-CEO role.',
 'Three saved representatives illustrate each topic; they do not exhaust membership or establish risk preference.',
 'Historical unkeyed density provenance remains separate; no density-based resampling is used.'
]


def now(): return datetime.now(timezone.utc).isoformat()
def loads(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def encoded(v): return (json.dumps(v, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)+'\n').encode('utf-8')
def digest(b): return hashlib.sha256(b).hexdigest()
def sha(p): return digest(Path(p).read_bytes())
def canonical(v): return digest(json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',', ':'),allow_nan=False).encode())
def write(p, v, exclusive=False):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb' if exclusive else 'wb') as f:f.write(encoded(v))
def textwrite(p,t,exclusive=False):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x' if exclusive else 'w',encoding='utf-8',newline='') as f:f.write(t)
def binding(p): return {'path':str(Path(p).resolve()),'sha256':sha(p)}
def verify_binding(b):
 if sha(b['path'])!=b['sha256']:raise ValueError('Binding mismatch: '+b['path'])
def unique_object(pairs):
 d={}
 for k,v in pairs:
  if k in d:raise ValueError('duplicate JSON key: '+k)
  d[k]=v
 return d
def literal_load(p): return json.loads(Path(p).read_text(encoding='utf-8'),object_pairs_hook=unique_object)


def row_schema(review=False):
 fields={
 'topic_id':{'type':'string'},'status':{'enum':['resolved','abstain','failed']},
 'label':{'enum':['relevant','irrelevant',None]},'rationale':{'type':'string','minLength':1},
 'evidence_keywords':{'type':'array','items':{'type':'string'},'uniqueItems':True,'maxItems':5},
 'confidence_level':{'enum':['high','medium','low',None]},'confidence_reason':{'type':'string','minLength':1}}
 if review:fields.update({
 'reviewed_passage_ids':{'type':'array','items':{'type':'string'},'uniqueItems':True},
 'evidence_passages':{'type':'array','items':{'type':'object','required':['passage_id','excerpt'],'properties':{'passage_id':{'type':'string'},'excerpt':{'type':'string','minLength':1}},'additionalProperties':False}},
 'topic_interpretation_assessment':{'enum':['supported','mixed','not_supported','insufficient_evidence']},
 'interpretation_reason':{'type':'string','minLength':1},'review_action':{'enum':['retained','revised','newly_resolved','unresolved']},'change_reason':{'type':'string','minLength':1}})
 return {'type':'object','required':list(fields),'properties':fields,'additionalProperties':False,
 'allOf':[{'if':{'properties':{'status':{'const':'resolved'}}},'then':{'properties':{'label':{'enum':['relevant','irrelevant']},'confidence_level':{'enum':['high','medium','low']},'evidence_keywords':{'minItems':1},**({'evidence_passages':{'minItems':1}} if review else {})}},'else':{'properties':{'label':{'type':'null'},'confidence_level':{'type':'null'}}}}]}

def response_schema(review=False):
 return {'$schema':'https://json-schema.org/draft/2020-12/schema','$id':VERSION+('/review' if review else '/initial'),'type':'object','required':['labels'],'additionalProperties':False,'properties':{'labels':{'type':'array','items':row_schema(review),'minItems':1}},'$comment':'Full stages require exact frozen 354-topic order; page fragments require exact page order. Importer also checks supplied keyword/quotation membership and paired action. Missing confidence is a preserved reporting defect, never a label edit.'}

def make_chunks(path, destination):
 t=Path(path).read_text(encoding='utf-8');destination=Path(destination);destination.mkdir(parents=True,exist_ok=True);out=[]
 for n,start in enumerate(range(0,len(t),CHUNK_CHARS),1):
  part=t[start:start+CHUNK_CHARS];p=destination/f'{n:03}.txt';textwrite(p,part)
  out.append({'index':n,'path':str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p),'start_character':start,'end_character_exclusive':start+len(part),'characters':len(part),'utf8_bytes':len(part.encode()),'sha256':sha(p)})
 assert ''.join((ROOT/r['path']).read_text() for r in out)==t
 return out

def build():
 """Reuse exact v8 scientific packets; replace only ratified administrative bindings."""
 packets=ROOT/'packets';old=ROOT.parent.parent/'step2-expanded-ai-pilot-v8/data-analysis'
 if packets.exists():raise ValueError('Packets already exist; preserve freeze, do not rebuild in place')
 base=loads(ROOT.parent/'cig/baseline-bindings.json')
 for b in base['protocol_files']+base['bound_inputs']:
  if sha(EXPORT/b['path'])!=b['sha256']:raise ValueError('Baseline drift: '+b['path'])
 schedule=loads(PROTOCOL/'SCHEDULE.json');jobs=schedule['jobs'];assign=loads(PROTOCOL/'CMD_ASSIGNMENTS.json')
 assert schedule['design_revision']==9 and len(jobs)==84
 assert [j['dispatch_order'] for j in jobs]==list(range(1,85))
 assert len({j['trial_id'] for j in jobs})==84
 models={'gpt-6.1-sol','gpt-6-astra'};blocks={1,2}
 cells={(m,f'P{p}',e) for m in models for p in range(7) for e in ['medium','high','xhigh']}
 assert len(cells)==42
 for block in blocks:
  rows=[j for j in jobs if j['block']==block]
  assert len(rows)==42 and {(j['model'],j['prompt_id'],j['effort']) for j in rows}==cells
 assert all(j['reader_slots']==['A','B','C'] for j in jobs)
 assert len(assign['commanders'])==4
 for c in assign['commanders']:
  owned=[j for j in jobs if j['cmd_id']==c['cmd_id']]
  assert [j['trial_id'] for j in owned]==c['trial_ids'] and len(owned)==21
 old_schedule=loads(old/'packets/schedule.json')
 retained=[j for j in old_schedule['jobs'] if j['model'] in models and j['block'] in blocks]
 fields=['trial_id','model','prompt_id','effort','block']
 assert [[j[k] for k in fields] for j in jobs]==[[j[k] for k in fields] for j in retained]
 prior=loads(old/'PACKET_MANIFEST.json');admin={'packets/schedule.json','packets/cmd_assignments.json'}
 unchanged=[]
 for rel,h in prior['file_hashes'].items():
  source=old/rel
  if sha(source)!=h:raise ValueError('Frozen v8 packet drift: '+rel)
  target=ROOT/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
  if rel not in admin:unchanged.append(rel)
 # Authoritative merged schedule/assignment bytes replace the two old administrative files.
 shutil.copyfile(PROTOCOL/'SCHEDULE.json',packets/'schedule.json')
 shutil.copyfile(PROTOCOL/'CMD_ASSIGNMENTS.json',packets/'cmd_assignments.json')
 for n in ['initial.schema.json','review.schema.json']:
  assert sha(ROOT/'schemas'/n)==sha(old/'schemas'/n)
 for rel in unchanged:assert sha(ROOT/rel)==prior['file_hashes'][rel]
 copied_catalogue=loads(packets/'catalogue.json')
 source_catalogue=loads(EXPORT/schedule['catalogue_path'])
 assert copied_catalogue['topics']==[{k:r[k] for k in ['topic_id','name','keywords']} for r in source_catalogue['topics']]
 manifest={**prior,'built_utc':now(),'design_revision':9,'input_bindings':base,
 'reused_scientific_packet_manifest':binding(old/'PACKET_MANIFEST.json'),
 'design_counts':{'models':2,'configurations':42,'blocks':2,'trials':84,'readers':252,'stage_records':504,'topic_judgments_per_stage':89208,'topic_judgments_total':178416},
 'file_hashes':{str(p.relative_to(ROOT)):sha(p) for p in sorted(packets.rglob('*')) if p.is_file()}}
 write(ROOT/'PACKET_MANIFEST.json',manifest)
 shutil.copyfile(old/'PACKET_SIZES.json',ROOT/'PACKET_SIZES.json')
 equivalence={'checked_utc':now(),'previous_manifest':binding(old/'PACKET_MANIFEST.json'),
 'scientific_files_unchanged':len(unchanged),'scientific_file_paths':unchanged,
 'schemas_unchanged':{n:sha(ROOT/'schemas'/n) for n in ['initial.schema.json','review.schema.json']},
 'administrative_changes':{rel:{'v8_sha256':prior['file_hashes'][rel],'v9_sha256':sha(ROOT/rel)} for rel in sorted(admin)},
 'source_packet_sha256':sha(packets/'source_packet.private.json'),'source_extraction_rebuilt':False,
 'retained_trial_order_matches_v8_filter':True,'v8_modified':False,'all_scientific_bytes_preserved':True}
 assert equivalence['source_packet_sha256']==prior['source_packet_sha256']
 write(ROOT/'PACKET_EQUIVALENCE.json',equivalence)
 return {'stageA_packets':len(manifest['stageA']),'stageB_pages':len(manifest['stageB']),
 'passages':1062,'scientific_files_unchanged':len(unchanged),'administrative_files_updated':2,
 'trials':84,'readers':252,'stage_records':504,'manifest_sha256':sha(ROOT/'PACKET_MANIFEST.json')}


def cat():return loads(ROOT/'packets/catalogue.json')
def manifest():return loads(ROOT/'PACKET_MANIFEST.json')
def source_map():return {p['passage_id']:p for p in loads(ROOT/'packets/source_packet.private.json')['passages']}
def page_spec(page_id):return next(p for p in manifest()['stageB'] if p['page_id']==page_id)
def job(trial):return next(j for j in loads(ROOT/'packets/schedule.json')['jobs'] if j['trial_id']==trial)

def validate(rows,stage,expected_ids=None,initial=None):
 """Return defects without changing rows. Confidence defects do not remove binary votes."""
 topics={r['topic_id']:r for r in cat()['topics']};expected_ids=expected_ids or list(topics)
 defects=[]
 def defect(t,code,detail):defects.append({'topic_id':t,'code':code,'detail':detail})
 if not isinstance(rows,list):return [{'topic_id':None,'code':'structure','detail':'labels is not an array'}]
 ids=[r.get('topic_id') if isinstance(r,dict) else None for r in rows]
 if ids!=expected_ids:defect(None,'roster','Topic IDs must occur once in exact supplied order')
 sources=source_map() if stage==REVIEW else {}
 initials={r['topic_id']:r for r in (initial or {}).get('labels',[])}
 required=set(row_schema(stage==REVIEW)['required'])
 for r in rows:
  if not isinstance(r,dict):defect(None,'structure','row is not an object');continue
  tid=r.get('topic_id');t=topics.get(tid)
  if t is None:defect(tid,'unknown_topic','Topic ID is not an exact supplied string');continue
  missing=required-set(r);extra=set(r)-required
  for k in sorted(missing):defect(tid,'missing_confidence' if k in ['confidence_level','confidence_reason'] else 'missing_field',k)
  if extra:defect(tid,'unexpected_field',','.join(sorted(extra)))
  status=r.get('status');resolved=status=='resolved';label=r.get('label')
  if status not in ['resolved','abstain','failed']:defect(tid,'status','unknown status')
  if (resolved and label not in ['relevant','irrelevant']) or (not resolved and label is not None):defect(tid,'label','resolved needs binary label; unresolved needs null')
  for k in ['rationale','confidence_reason']:
   if not isinstance(r.get(k),str) or not r[k].strip():defect(tid,'missing_confidence' if k=='confidence_reason' else 'reason',k)
  conf=r.get('confidence_level')
  if (resolved and conf not in ['high','medium','low']) or (not resolved and conf is not None):defect(tid,'missing_confidence' if conf is None else 'confidence','Invalid/null self-reported confidence')
  kw=r.get('evidence_keywords')
  if not isinstance(kw,list) or not all(isinstance(x,str) for x in kw):defect(tid,'keywords','keywords must be string list')
  elif len(kw)!=len(set(kw)) or len(kw)>5 or (resolved and not kw) or any(k not in t['keywords'] for k in kw):defect(tid,'keywords','Need 1–5 distinct exact supplied keywords when resolved')
  if stage==REVIEW:
   expected=[f't{tid}-r{n}' for n in [1,2,3]];checked=r.get('reviewed_passage_ids')
   if not isinstance(checked,list) or len(checked)!=len(set(checked)) or any(x not in expected for x in checked):defect(tid,'passage_ids','Unknown/duplicate checked passage ID')
   elif checked!=expected:defect(tid,'passage_coverage','All three passages in saved order were not reported checked')
   citations=r.get('evidence_passages')
   if not isinstance(citations,list) or (resolved and not citations):defect(tid,'citations','Resolved review requires supporting exact excerpt')
   else:
    for e in citations:
     if not isinstance(e,dict) or set(e)!= {'passage_id','excerpt'}:defect(tid,'citation_shape','Need passage_id and excerpt');continue
     pid=e['passage_id'];quote=e['excerpt']
     if pid not in expected or not isinstance(quote,str) or not quote or quote not in sources.get(pid,{}).get('text',''):defect(tid,'quotation','Not an exact substring of this topic passage')
     if isinstance(checked,list) and pid not in checked:defect(tid,'unchecked_citation','Citation to passage not reported checked')
   if r.get('topic_interpretation_assessment') not in ['supported','mixed','not_supported','insufficient_evidence']:defect(tid,'interpretation','unknown assessment')
   for k in ['interpretation_reason','change_reason']:
    if not isinstance(r.get(k),str) or not r[k].strip():defect(tid,'reason',k)
   old=initials.get(tid);expected_action='unresolved' if not resolved else ('newly_resolved' if not old or vote(old) is None else ('retained' if vote(old)==label else 'revised'))
   if r.get('review_action')!=expected_action:defect(tid,'review_action','Expected '+expected_action)
 # Exact repeats are observable flags only, not semantic rejection.
 reasons=Counter(r.get('rationale') for r in rows if isinstance(r,dict) and isinstance(r.get('rationale'),str))
 for reason,n in reasons.items():
  if n>1:defect(None,'repeated_reason_flag',{'count':n,'rationale':reason,'meaning':'Observable repeat; genericness/support requires semantic inspection'})
 return defects

def vote(row):
 return row.get('label') if isinstance(row,dict) and row.get('status')=='resolved' and row.get('label') in ['relevant','irrelevant'] else None

def majority(rows):
 votes=[vote(r) for r in rows];counts=Counter(votes);label=next((x for x in ['relevant','irrelevant'] if counts[x]>=2),None)
 return {'label':label,'status':'resolved' if label else 'unresolved','votes':votes,'resolved_votes':sum(v is not None for v in votes),'all_three_resolved':all(v is not None for v in votes),'operational_with_missing_third':label is not None and any(v is None for v in votes),'minority_slots':[i for i,v in enumerate(votes) if label and v is not None and v!=label],'missing_slots':[i for i,v in enumerate(votes) if v is None]}

def metadata(trial,reader,chat_id,observations=None):
 j=job(trial)
 if reader not in ['A','B','C']:raise ValueError('reader slot must be A/B/C')
 o=observations or {}
 return {'trial_id':trial,'reader_id':reader,'chat_id':chat_id,'model_requested':j['model'],'effort_requested':j['effort'],'model_observed':o.get('model_observed'),'effort_observed':o.get('effort_observed'),'client_version':o.get('client_version'),'start_utc':o.get('start_utc'),'end_utc':o.get('end_utc'),'usage':o.get('usage'),'backend_version':o.get('backend_version'),'observations':o,'prompt_id':j['prompt_id'],'block':j['block']}

def record(seal):
 s=loads(seal);verify_binding(s['record']);r=loads(s['record']['path'])
 if r['literal_response'] is not None:verify_binding(r['literal_response'])
 for b in r.get('page_seals',[]):
  verify_binding(b);record(b['path'])
 for k in ['initial_seal','release_receipt']:
  if r.get(k):verify_binding(r[k])
 if r.get('recovery'):verify_binding(r['recovery']['original_seal'])
 return r

def recovery_binding(attempt,meta,stage,recovery_of=None,recovery_reason=None):
 if attempt=='first':
  if recovery_of or recovery_reason:raise ValueError('First attempt cannot supersede a prior attempt')
  return None
 if not recovery_of or not recovery_reason:raise ValueError('Named recovery requires original seal and administrative technical reason')
 prior=record(recovery_of)
 if prior['stage']!=stage or any(prior['metadata'][k]!=meta[k] for k in ['trial_id','reader_id','chat_id','model_requested','effort_requested']):raise ValueError('Recovery changes reader identity or stage; preserve as a protocol deviation outside this same-reader recovery helper')
 return {'original_seal':binding(recovery_of),'administrative_technical_reason':recovery_reason,'is_supplementary':True}

def common_bindings(meta,stage,page_id=None):
 m=manifest();pid=meta['prompt_id']
 return {'design_revision':9,'schedule_sha256':sha(ROOT/'packets/schedule.json'),'catalogue_sha256':m['catalogue_sha256'],'topic_model_id':m['topic_model_id'],'prompt_sha256':sha(ROOT/f'packets/prompts/{pid}.md'),'addendum_sha256':sha(ROOT/'packets/initial_addendum.md'),'review_prompt_sha256':sha(ROOT/'packets/review_prompt.md') if stage==REVIEW else None,'schema_sha256':sha(ROOT/('schemas/review.schema.json' if stage==REVIEW else 'schemas/initial.schema.json')),'source_packet_sha256':m['source_packet_sha256'] if stage==REVIEW else None,'page_packet_sha256':page_spec(page_id)['sha256'] if page_id else None}

def seal_literal(literal,out,meta,stage,attempt='first',initial_seal=None,page_id=None,release=None,recovery_of=None,recovery_reason=None):
 if stage==REVIEW and not page_id:raise ValueError('Reviewed literal import requires a logical page ID; use assemble for the final stage')
 if stage==INITIAL and page_id:raise ValueError('Stage A must be the whole 354-topic response')
 out=Path(out)
 if out.exists():raise ValueError('Attempt directory exists; use a new named technical-recovery attempt')
 recovery=recovery_binding(attempt,meta,stage,recovery_of,recovery_reason)
 initial_record=record(initial_seal) if initial_seal else None
 if stage==REVIEW:
  if not release:raise ValueError('Review requires triad release receipt')
  released=loads(release);verify_release(released)
  ib=released['initial_seals'][meta['reader_id']]
  if not initial_seal or sha(initial_seal)!=ib['sha256']:raise ValueError('Initial differs from released initial')
  if any(meta[k]!=initial_record['metadata'][k] for k in ['trial_id','reader_id','chat_id','model_requested','effort_requested']):raise ValueError('Reader identity/model/effort continuity broken')
 parsed=literal_load(literal)
 if not isinstance(parsed,dict) or set(parsed)!= {'labels'}:raise ValueError('literal response must be exactly an object with labels')
 expected=page_spec(page_id)['topic_ids'] if page_id else [r['topic_id'] for r in cat()['topics']]
 defects=validate(parsed['labels'],stage,expected,initial_record)
 # Structural ambiguity cannot be imported as a complete stage. Save literal outside attempts and record a missing attempt if recovery cannot fix it.
 if any(d['code'] in ['structure','roster','unknown_topic','label','status'] for d in defects):raise ValueError('Non-importable structure: '+json.dumps(defects[:10]))
 out.mkdir(parents=True);copy=out/'literal-response.json';shutil.copyfile(literal,copy)
 m=manifest();pid=meta['prompt_id']
 r={'schema_version':VERSION,'stage':stage,'attempt_id':attempt,'missing_attempt':False,'metadata':meta,'page_id':page_id,'labels':parsed['labels'],'literal_response':binding(copy),'initial_seal':binding(initial_seal) if initial_seal else None,'release_receipt':binding(release) if release else None,'catalogue_sha256':m['catalogue_sha256'],'topic_model_id':m['topic_model_id'],'prompt_sha256':sha(ROOT/f'packets/prompts/{pid}.md'),'addendum_sha256':sha(ROOT/'packets/initial_addendum.md'),'review_prompt_sha256':sha(ROOT/'packets/review_prompt.md') if stage==REVIEW else None,'schema_sha256':sha(ROOT/('schemas/review.schema.json' if stage==REVIEW else 'schemas/initial.schema.json')),'source_packet_sha256':m['source_packet_sha256'] if stage==REVIEW else None,'page_packet_sha256':page_spec(page_id)['sha256'] if page_id else None,'defects':defects,'recovery':recovery,'design_revision':9,'schedule_sha256':sha(ROOT/'packets/schedule.json'),'sealed_utc':now()}
 write(out/'record.json',r,True);write(out/'seal.json',{'record':binding(out/'record.json'),'literal':binding(copy),'sealed_utc':now(),'attempt_id':attempt},True)
 return out/'seal.json'

def missing(out,meta,stage,technical_reason,attempt='first',initial_seal=None,release=None,page_id=None,recovery_of=None,recovery_reason=None):
 if not technical_reason:raise ValueError('Administrative technical reason required')
 recovery=recovery_binding(attempt,meta,stage,recovery_of,recovery_reason)
 out=Path(out)
 if out.exists():raise ValueError('Attempt already exists')
 if stage==REVIEW:
  if not release:raise ValueError('Review missing attempt still requires release receipt')
  rr=loads(release);verify_release(rr)
  if sha(initial_seal)!=rr['initial_seals'][meta['reader_id']]['sha256']:raise ValueError('Initial release mismatch')
  ir=record(initial_seal)
  if any(meta[k]!=ir['metadata'][k] for k in ['trial_id','reader_id','chat_id','model_requested','effort_requested']):raise ValueError('Continuity mismatch')
 r={'schema_version':VERSION,'stage':stage,'attempt_id':attempt,'missing_attempt':True,'metadata':meta,'page_id':page_id,'labels':[],'literal_response':None,'administrative_technical_reason':technical_reason,'reader_reason':None,'reader_confidence':None,'initial_seal':binding(initial_seal) if initial_seal else None,'release_receipt':binding(release) if release else None,'catalogue_sha256':manifest()['catalogue_sha256'],'topic_model_id':manifest()['topic_model_id'],'source_packet_sha256':manifest()['source_packet_sha256'] if stage==REVIEW else None,'defects':[],'recovery':recovery,**common_bindings(meta,stage,page_id),'sealed_utc':now()}
 write(out/'record.json',r,True);write(out/'seal.json',{'record':binding(out/'record.json'),'sealed_utc':now(),'attempt_id':attempt},True)
 return out/'seal.json'

def verify_release(r):
 if r['source_packet_sha256']!=manifest()['source_packet_sha256']:raise ValueError('source hash changed')
 for slot,b in r['initial_seals'].items():
  verify_binding(b);rec=record(b['path'])
  if rec['stage']!=INITIAL or rec['metadata']['reader_id']!=slot or rec['metadata']['trial_id']!=r['trial_id']:raise ValueError('Invalid initial triad release')
  if not rec['missing_attempt'] and len(rec['labels'])!=354:raise ValueError('Incomplete initial response')

def release_initial(seals,out):
 if len(seals)!=3:raise ValueError('Need three initial seals')
 rs=[record(p) for p in seals];trial=rs[0]['metadata']['trial_id']
 if {r['metadata']['reader_id'] for r in rs}!= {'A','B','C'} or len({r['metadata']['chat_id'] for r in rs})!=3:raise ValueError('Need three distinct reader slots/chats')
 r={'schema_version':VERSION,'trial_id':trial,'released_utc':now(),'source_packet_sha256':manifest()['source_packet_sha256'],'initial_seals':{rec['metadata']['reader_id']:binding(p) for p,rec in zip(seals,rs)},'peer_evidence_release':False}
 verify_release(r);write(out,r,True);return r

def render_page(release,initial_seal,page_id,out):
 rr=loads(release);verify_release(rr);ir=record(initial_seal);slot=ir['metadata']['reader_id']
 if sha(initial_seal)!=rr['initial_seals'][slot]['sha256']:raise ValueError('Not this released initial')
 page=loads(ROOT/page_spec(page_id)['path']);ids=page_spec(page_id)['topic_ids']
 data={'stage':REVIEW,'page_id':page_id,'reader_metadata':ir['metadata'],'initial_seal':binding(initial_seal),'release_receipt':binding(release),'common_review_prompt':(ROOT/'packets/review_prompt.md').read_text(),'response_schema':response_schema(True),'own_initial_missing_attempt':ir['missing_attempt'],'own_initial_rows':[r for r in ir['labels'] if r['topic_id'] in ids],'source_page':page}
 out=Path(out)
 if out.exists():raise ValueError('Released page exists')
 write(out,data,True);chunks=make_chunks(out,out.parent/(out.stem+'-chunks'))
 write(out.with_suffix('.transport.json'),{'packet':binding(out),'chunks':chunks},True)
 return {'packet':binding(out),'chunks':len(chunks)}

def assemble(page_seals,out,attempt='first',recovery_of=None,recovery_reason=None):
 rs=[record(p) for p in page_seals];expected=[p['page_id'] for p in manifest()['stageB']]
 if [r['page_id'] for r in rs]!=expected:raise ValueError('Need one sealed fragment per logical page in exact order')
 first=rs[0];keys=['initial_seal','source_packet_sha256','release_receipt'];identity=['trial_id','reader_id','chat_id','model_requested','effort_requested']
 if any(r['stage']!=REVIEW or any(r[k]!=first[k] for k in keys) or any(r['metadata'][k]!=first['metadata'][k] for k in identity) for r in rs):raise ValueError('Mixed reader/initial/release/packet')
 if attempt=='first' and any(r['attempt_id']!='first' for r in rs):raise ValueError('Recovered page rows require a supplementary recovered-stage assembly')
 recovery=recovery_binding(attempt,first['metadata'],REVIEW,recovery_of,recovery_reason)
 labels=[r for page in rs for r in page['labels']]
 # Missing pages stay absent; their topics become missing at analysis/export, never fabricated abstentions.
 present=[r['topic_id'] for r in labels];wanted=[tid for p,r in zip(manifest()['stageB'],rs) if not r['missing_attempt'] for tid in p['topic_ids']]
 if present!=wanted:raise ValueError('Page rows do not exactly match supplied pages')
 out=Path(out)
 if out.exists():raise ValueError('Assembly already exists')
 r={**first,'page_id':None,'page_packet_sha256':None,'attempt_id':attempt,'recovery':recovery,'metadata_scope':'First page metadata; full page-specific observations retained in page_seals','labels':labels,'literal_response':None,'missing_attempt':all(p['missing_attempt'] for p in rs),'partial_stage':len(labels)!=354,'missing_page_ids':[p['page_id'] for p in rs if p['missing_attempt']],'page_seals':[binding(p) for p in page_seals],'defects':[d for p in rs for d in p['defects']],'assembly':'literal parsed rows concatenated in frozen order, no regenerated judgments','sealed_utc':now()}
 write(out/'record.json',r,True);write(out/'seal.json',{'record':binding(out/'record.json'),'sealed_utc':now()},True)
 return out/'seal.json'

def emit_slice(p,start,end,label):
 text=Path(p).read_text(encoding='utf-8')
 if start is None or end is None or start<0 or end<=start or end>len(text) or end-start>6000:raise ValueError('Need exact valid start/end offsets, at most 6000 characters')
 part=text[start:end]
 print(f'BEGIN {label} offsets {start}:{end}/{len(text)} packet_sha256 {sha(p)} slice_sha256 {digest(part.encode())}')
 sys.stdout.write(part);print(f'\nEND {label} offsets {start}:{end}/{len(text)}')

def read_chunk(kind,key,index=None,release=None,initial_seal=None,start=None,end=None):
 if kind=='B':
  if not release or not initial_seal:raise ValueError('Source chunks require the release receipt and own sealed initial')
  rr=loads(release);verify_release(rr);ir=record(initial_seal)
  if sha(initial_seal)!=rr['initial_seals'][ir['metadata']['reader_id']]['sha256']:raise ValueError('Wrong released initial')
 m=manifest();item=next(p for p in m['stageA' if kind=='A' else 'stageB'] if p['prompt_id' if kind=='A' else 'page_id']==key)
 if start is not None or end is not None:
  if index is not None:raise ValueError('Use either a frozen fragment index or exact offsets')
  p=ROOT/item['path']
  if sha(p)!=item['sha256']:raise ValueError('Packet binding mismatch')
  emit_slice(p,start,end,f'{kind} {key}');return
 if index is None or index<1 or index>len(item['chunks']):raise ValueError('Valid frozen fragment index required')
 chunk=item['chunks'][index-1];p=ROOT/chunk['path']
 if sha(p)!=chunk['sha256']:raise ValueError('Chunk binding mismatch')
 print(f"BEGIN {kind} {key} chunk {index}/{len(item['chunks'])} characters {chunk['start_character']}:{chunk['end_character_exclusive']} sha256 {chunk['sha256']}")
 sys.stdout.write(p.read_text());print(f'\nEND {kind} {key} chunk {index}')

def export_trial(seals,out):
 if len(seals)!=6:raise ValueError('Need six complete or missing stage seals (A/B/C × two stages)')
 records=[record(p) for p in seals]
 if any(r.get('page_id') is not None for r in records):raise ValueError('Page fragments are not complete stage records')
 if any(r['stage']==REVIEW and not r['missing_attempt'] and not r.get('page_seals') for r in records):raise ValueError('Reviewed final records require literal-page assembly provenance')
 trial=records[0]['metadata']['trial_id']
 if any(r['metadata']['trial_id']!=trial for r in records):raise ValueError('Mixed trials')
 by={(r['stage'],r['metadata']['reader_id']):r for r in records}
 if set(by)!={(s,x) for s in [INITIAL,REVIEW] for x in 'ABC'}:raise ValueError('Need exactly one of each reader/stage')
 for x in 'ABC':
  a,b=by[INITIAL,x],by[REVIEW,x]
  if a['metadata']['chat_id']!=b['metadata']['chat_id']:raise ValueError('Chat continuity mismatch')
  if b['initial_seal']['sha256']!=sha(seals[records.index(a)]):raise ValueError('Reviewed record references different initial')
 out=Path(out)
 if out.exists():raise ValueError('Export exists; use a new output version')
 out.mkdir(parents=True)
 ids=[t['topic_id'] for t in cat()['topics']];maps={k:{r['topic_id']:r for r in v['labels']} for k,v in by.items()};details=[]
 for tid in ids:
  a=[maps[INITIAL,x].get(tid) for x in 'ABC'];b=[maps[REVIEW,x].get(tid) for x in 'ABC']
  details.append({'topic_id':tid,'initial':majority(a),'reviewed':majority(b),'readers':{x:{'initial':a[i],'reviewed':b[i]} for i,x in enumerate('ABC')}})
 src=loads(ROOT/'packets/source_packet.private.json')
 write(out/'topic_details.private.json',{'trial_id':trial,'stage_seals':[binding(p) for p in seals],'topics':details},True)
 shutil.copyfile(ROOT/'packets/source_evidence.private.jsonl',out/'source_evidence.private.jsonl')
 for stage,key,dest in [(INITIAL,'initial',out/'initial'),(REVIEW,'reviewed',out)]:
  dest.mkdir(exist_ok=True)
  selected=[r['topic_id'] for r in details if r[key]['label']=='relevant'];excluded=[r['topic_id'] for r in details if r[key]['label']=='irrelevant'];unresolved=[r['topic_id'] for r in details if r[key]['label'] is None]
  write(dest/'selected_topics.json',{'design_revision':9,'schedule_sha256':sha(ROOT/'packets/schedule.json'),'trial_id':trial,'stage':stage,'topic_model_id':manifest()['topic_model_id'],'catalogue_sha256':manifest()['catalogue_sha256'],'source_packet_sha256':manifest()['source_packet_sha256'] if stage==REVIEW else None,'assignment':job(trial),'selected_topic_ids':selected,'excluded_topic_ids':excluded,'unresolved_topic_ids':unresolved,'rule':'two matching resolved labels out of three, unweighted; no fallback or cross-stage mixing'},True)
  with (dest/'topic_labels.csv').open('x',encoding='utf-8',newline='') as f:
   fields=['topic_id','stage','majority_label','resolved_votes','all_three_resolved','operational_with_missing_third','initial_majority','reviewed_majority','A_initial','A_reviewed','B_initial','B_reviewed','C_initial','C_reviewed','source_links']
   w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
   for r in details:
    row={'topic_id':r['topic_id'],'stage':stage,'majority_label':r[key]['label'],'resolved_votes':r[key]['resolved_votes'],'all_three_resolved':r[key]['all_three_resolved'],'operational_with_missing_third':r[key]['operational_with_missing_third'],'initial_majority':r['initial']['label'],'reviewed_majority':r['reviewed']['label'],'source_links':'../source_evidence.private.jsonl' if stage==INITIAL else 'source_evidence.private.jsonl'}
    for x in 'ABC':
     for s in ['initial','reviewed']:row[x+'_'+s]=json.dumps(r['readers'][x][s],ensure_ascii=False,sort_keys=True)
    w.writerow(row)
  textwrite(dest/'HANDOFF.md',f'# {stage} topic handoff\n\nTrial `{trial}`: {len(selected)} selected, {len(excluded)} excluded, {len(unresolved)} unresolved of 354.\n\n'+('Primary Stage B reviewed majority. ' if stage==REVIEW else 'Separate Stage A baseline; never substitute for a missing review. ')+ 'All votes, reasons, confidence, citations and minorities remain in the CSV and detailed JSON; all candidate source links remain in the source evidence table. Missing/defective records remain explicit. Confidence does not weight voting. Check exact topic-model/density-column binding before Step 3. Agreement and exact citation checks do not establish accuracy, independent CEO attribution or construct validity. Private export includes retained source links; privacy review is required before shared Git integration.\n',True)
 return {'trial_id':trial,'selected':sum(d['reviewed']['label']=='relevant' for d in details),'excluded':sum(d['reviewed']['label']=='irrelevant' for d in details),'unresolved':sum(d['reviewed']['label'] is None for d in details)}


def read_released_chunk(transport,index=None,start=None,end=None):
 tr=loads(transport);verify_binding(tr['packet']);page=loads(tr['packet']['path'])
 verify_binding(page['initial_seal']);verify_binding(page['release_receipt']);verify_release(loads(page['release_receipt']['path']))
 if start is not None or end is not None:
  if index is not None:raise ValueError('Use either frozen fragment index or exact offsets')
  emit_slice(tr['packet']['path'],start,end,f'released {page["page_id"]}');return
 if index is None or index<1 or index>len(tr['chunks']):raise ValueError('Valid frozen fragment index required')
 c=tr['chunks'][index-1];p=ROOT/c['path']
 if sha(p)!=c['sha256']:raise ValueError('Released chunk binding mismatch')
 print(f'BEGIN released {page["page_id"]} chunk {index}/{len(tr["chunks"])} sha256 {c["sha256"]}')
 sys.stdout.write(p.read_text());print(f'\nEND released {page["page_id"]} chunk {index}')

def main():
 p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
 sub.add_parser('build')
 q=sub.add_parser('read-released');q.add_argument('transport');q.add_argument('index',type=int,nargs='?');q.add_argument('--start',type=int);q.add_argument('--end',type=int)
 r=sub.add_parser('read');r.add_argument('kind',choices=['A','B']);r.add_argument('key');r.add_argument('index',type=int,nargs='?');r.add_argument('--start',type=int);r.add_argument('--end',type=int);r.add_argument('--release');r.add_argument('--initial-seal')
 for command in ['import','missing']:
  q=sub.add_parser(command);q.add_argument('--out',required=True);q.add_argument('--trial',required=True);q.add_argument('--reader',choices=list('ABC'),required=True);q.add_argument('--chat-id',required=True);q.add_argument('--stage',choices=[INITIAL,REVIEW],required=True);q.add_argument('--attempt',default='first');q.add_argument('--observations');q.add_argument('--initial-seal');q.add_argument('--release');q.add_argument('--page-id');q.add_argument('--recovery-of');q.add_argument('--recovery-reason')
  q.add_argument('--literal' if command=='import' else '--reason',required=True)
 q=sub.add_parser('release');q.add_argument('--seals',nargs=3,required=True);q.add_argument('--out',required=True)
 q=sub.add_parser('page');q.add_argument('--release',required=True);q.add_argument('--initial-seal',required=True);q.add_argument('--page-id',required=True);q.add_argument('--out',required=True)
 q=sub.add_parser('assemble');q.add_argument('--seals',nargs='+',required=True);q.add_argument('--out',required=True);q.add_argument('--attempt',default='first');q.add_argument('--recovery-of');q.add_argument('--recovery-reason')
 q=sub.add_parser('export');q.add_argument('--seals',nargs=6,required=True);q.add_argument('--out',required=True)
 a=p.parse_args()
 if a.command=='build':result=build()
 elif a.command=='read-released':read_released_chunk(a.transport,a.index,a.start,a.end);return
 elif a.command=='read':read_chunk(a.kind,a.key,a.index,a.release,a.initial_seal,a.start,a.end);return
 elif a.command in ['import','missing']:
  meta=metadata(a.trial,a.reader,a.chat_id,loads(a.observations) if a.observations else None)
  if a.command=='import':result=seal_literal(a.literal,a.out,meta,a.stage,a.attempt,a.initial_seal,a.page_id,a.release,a.recovery_of,a.recovery_reason)
  else:result=missing(a.out,meta,a.stage,a.reason,a.attempt,a.initial_seal,a.release,a.page_id,a.recovery_of,a.recovery_reason)
 elif a.command=='release':result=release_initial(a.seals,a.out)
 elif a.command=='page':result=render_page(a.release,a.initial_seal,a.page_id,a.out)
 elif a.command=='assemble':result=assemble(a.seals,a.out,a.attempt,a.recovery_of,a.recovery_reason)
 else:result=export_trial(a.seals,a.out)
 print(json.dumps(result,ensure_ascii=False,default=str,indent=2))

if __name__=='__main__':main()
