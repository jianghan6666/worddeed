#!/usr/bin/env python3
"""Prespecified descriptive analysis from an explicit index of sealed saved records.
No inference; no hidden discovery of reader files; absent indexed stages stay missing.
"""
import argparse
import csv
import itertools
import json
from collections import Counter, defaultdict
from pathlib import Path
import toolkit as t


def ratio(n,d):return n/d if d else None

def agreement(left,right,eligible=None):
 a=b=c=d=0;eligible=eligible if eligible is not None else [True]*len(left)
 for x,y,e in zip(left,right,eligible):
  if not e or x is None or y is None:continue
  if x=='relevant' and y=='relevant':a+=1
  elif x=='relevant':b+=1
  elif y=='relevant':c+=1
  else:d+=1
 n=a+b+c+d
 return {'catalogue_N':len(left),'jointly_resolved_N':n,'excluded_from_pair_N':len(left)-n,'a_both_relevant':a,'b_left_relevant_right_irrelevant':b,'c_left_irrelevant_right_relevant':c,'d_both_irrelevant':d,'discordant_N':b+c,'raw_agreement':ratio(a+d,n),'positive_agreement':ratio(2*a,2*a+b+c),'negative_agreement':ratio(2*d,2*d+b+c),'selected_set_jaccard':ratio(a,a+b+c)}


def csvwrite(path,rows,fields=None):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
 if fields is None:fields=list(dict.fromkeys(k for row in rows for k in row))
 with path.open('x',encoding='utf-8',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields or ['no_records']);w.writeheader()
  for r in rows:w.writerow({k:json.dumps(v,ensure_ascii=False,sort_keys=True) if isinstance(v,(dict,list,tuple)) else v for k,v in r.items()})


def read_index(path,variant):
 index=t.loads(path)
 if not isinstance(index,dict) or set(index)!= {'schema_version','records'}:raise ValueError('Index requires schema_version and records only')
 entries=index['records'];seen=set();out={};ledger=[]
 for e in entries:
  if set(e)-{'trial_id','reader_id','stage','first_seal','recovered_seals'}:raise ValueError('Unknown index entry field')
  k=(e['trial_id'],e['reader_id'],e['stage'])
  if k in seen:raise ValueError('Duplicate indexed reader stage')
  seen.add(k);t.job(k[0])
  if k[1] not in 'ABC' or len(k[1])!=1 or k[2] not in [t.INITIAL,t.REVIEW]:raise ValueError('Invalid stage/slot')
  paths=([e['first_seal']] if e.get('first_seal') else [])+e.get('recovered_seals',[])
  allr=[]
  for i,p in enumerate(paths):
   r=t.record(p)
   if (r['metadata']['trial_id'],r['metadata']['reader_id'],r['stage'])!=k or r.get('page_id') is not None:raise ValueError('Index/seal identity or whole-stage mismatch')
   if r['stage']==t.REVIEW and not r['missing_attempt'] and not r.get('page_seals'):raise ValueError('Review lacks literal-page assembly provenance')
   if i==0 and e.get('first_seal') and r['attempt_id']!='first':raise ValueError('First-attempt record must be explicitly first')
   if i>0 and r['attempt_id']=='first':raise ValueError('Recovery must use new attempt ID')
   allr.append((p,r))
  selected=None
  if variant=='first':selected=next((r for p,r in allr if p==e.get('first_seal')),None)
  else:
   # Explicit latest named recovery is supplementary; order is supplied, never label-driven.
   selected=allr[-1][1] if allr else None
  if selected:out[k]=selected
  for p,r in allr:
   ledger.append({'trial_id':k[0],'reader_id':k[1],'stage':k[2],'seal_path':str(p),'seal_sha256':t.sha(p),'attempt_id':r['attempt_id'],'missing_attempt':r['missing_attempt'],'is_first':p==e.get('first_seal'),'selected_for_variant':r is selected})
 # Source review must bind the actual sealed initial. Recovery variants may bind an earlier
 # initial; mark this pairing explicitly, never silently compare to a replacement initial.
 for (trial,slot,stage),r in out.items():
  if stage==t.REVIEW:
   if not r.get('initial_seal'):raise ValueError('Review lacks sealed initial reference')
   t.verify_binding(r['initial_seal'])
   a=t.record(r['initial_seal']['path'])
   if a['stage']!=t.INITIAL:raise ValueError('Review-bound record is not Stage A')
   if any(a['metadata'][k]!=r['metadata'][k] for k in ['trial_id','reader_id','chat_id','model_requested','effort_requested']):raise ValueError('Stage continuity mismatch')
 return out,ledger


def analyze(index_path,out,variant='first'):
 out=Path(out)
 if out.exists():raise ValueError('Analysis output exists; use new version')
 out.mkdir(parents=True)
 records,attempts=read_index(index_path,variant)
 schedule=t.loads(t.ROOT/'packets/schedule.json');jobs=schedule['jobs'];blocks=sorted({j['block'] for j in jobs});planned_readers=sum(len(j['reader_slots']) for j in jobs);planned_stages=2*planned_readers;ids=[r['topic_id'] for r in t.cat()['topics']];N=len(ids)
 rm={k:{x['topic_id']:x for x in r['labels']} for k,r in records.items()}
 selected_seals={(r['trial_id'],r['reader_id'],r['stage']):{'path':r['seal_path'],'sha256':r['seal_sha256']} for r in attempts if r['selected_for_variant']}
 # Variant selection defines the standalone Stage A baseline. Paired changes instead
 # use the exact initial the selected review actually saw, even after a recovery.
 bound_initials={k:t.record(r['initial_seal']['path']) for k,r in records.items() if k[2]==t.REVIEW}
 bound_rows={k:{row['topic_id']:row for row in r['labels']} for k,r in bound_initials.items()}
 pair_lineage=[]
 sources=t.source_map();coverage=[];confidence=Counter();confidence_assoc=Counter();support=Counter();defects=[];transitions=Counter();conftrans=Counter();actions=Counter();stagecombos=Counter();reader_changes=[];ens={};cella=defaultdict(list);reader_counts=[]
 for j in jobs:
  trial=j['trial_id'];cell=(j['model'],j['prompt_id'],j['effort']);cella[cell].append(j)
  for stage in [t.INITIAL,t.REVIEW]:
   for slot in 'ABC':
    key=(trial,slot,stage);r=records.get(key);rows=rm.get(key,{})
    ir=None
    if stage==t.REVIEW and r:ir=bound_initials[key]
    checked=t.validate(list(rows.values()),stage,initial=ir) if rows else []
    # Partial stages already carry whole missing pages; avoid treating absent rows as abstentions.
    for d in checked:defects.append({'trial_id':trial,'reader_id':slot,'stage':stage,**d})
    states=Counter(x.get('status') for x in rows.values());votes=[t.vote(rows.get(tid)) for tid in ids]
    coverage.append({'trial_id':trial,'block':j['block'],'model':j['model'],'prompt_id':j['prompt_id'],'effort':j['effort'],'reader_id':slot,'stage':stage,'scheduled_reader_stage':1,'attempt_disposition':'not_recorded' if r is None else ('explicit_missing_attempt' if r['missing_attempt'] else 'response_saved'),'attempted_observed':(True if r and not r['missing_attempt'] and (r.get('literal_response') or r.get('page_seals')) else (r['metadata'].get('observations',{}).get('attempted') if r else None)),'literal_response_saved':bool(r and not r['missing_attempt'] and (r['literal_response'] or r.get('page_seals'))),'complete_roster':len(rows)==N,'resolved_N':sum(x is not None for x in votes),'abstain_N':states['abstain'],'failed_row_N':states['failed'],'absent_topic_N':N-len(rows),'selected_N':votes.count('relevant'),'excluded_N':votes.count('irrelevant'),'confidence_defect_N':sum(d['code'] in ['confidence','missing_confidence'] for d in checked),'citation_defect_N':sum(d['code'] in ['citations','quotation','unchecked_citation','citation_shape','passage_ids'] for d in checked),'passage_coverage_defect_N':sum(d['code']=='passage_coverage' for d in checked),'repeated_reason_flags':sum(d['code']=='repeated_reason_flag' for d in checked),'all_reported_defects_N':len(checked),'protocol_compliant_complete_stage':len(rows)==N and not any(d['code']!='repeated_reason_flag' for d in checked),'attempt_id':r.get('attempt_id') if r else None})
    reader_counts.append({'trial_id':trial,'reader_id':slot,'stage':stage,'selected_N':votes.count('relevant'),'resolved_N':sum(v is not None for v in votes),'missing_N':sum(v is None for v in votes)})
    for tid in ids:
     row=rows.get(tid);label=t.vote(row);conf=row.get('confidence_level') if row else None
     confidence[(stage,*cell,j['block'],label,conf)]+=1
     if stage==t.REVIEW:
      support[(*cell,j['block'],row.get('topic_interpretation_assessment') if row else None)]+=1
   decisions=[]
   for tid in ids:
    rows=[rm.get((trial,x,stage),{}).get(tid) for x in 'ABC'];m=t.majority(rows);decisions.append(m)
    distinct={t.vote(r) for r in rows if t.vote(r) is not None};disagree=len(distinct)>1
    for row in rows:
     confidence_assoc[(stage,*cell,t.vote(row),row.get('confidence_level') if row else None,disagree,any(t.vote(z) is None for z in rows))]+=1
   ens[trial,stage]=decisions
  for slot in 'ABC':
   ak=(trial,slot,t.INITIAL);bk=(trial,slot,t.REVIEW)
   selected_initial=selected_seals.get(ak);bound_initial=records[bk]['initial_seal'] if bk in records else None
   lineage_matches=(selected_initial['sha256']==bound_initial['sha256']) if selected_initial and bound_initial else None
   pairing_basis='review_bound_initial' if bk in records else 'selected_initial_without_review'
   pair_lineage.append({'trial_id':trial,'reader_id':slot,'variant':variant,'pairing_basis':pairing_basis,'selected_initial_seal':selected_initial,'review_bound_initial_seal':bound_initial,'selected_initial_matches_review_bound':lineage_matches})
   for tid in ids:
    selected_a=rm.get(ak,{}).get(tid)
    a=bound_rows[bk].get(tid) if bk in bound_rows else selected_a
    b=rm.get(bk,{}).get(tid);av=t.vote(a);bv=t.vote(b)
    astate='absent_topic' if a is None else a.get('status');bstate='absent_topic' if b is None else b.get('status')
    stagecombos[(*cell,j['block'],astate,bstate)]+=1
    transitions[(*cell,j['block'],av,bv)]+=1
    conftrans[(*cell,j['block'],a.get('confidence_level') if a else None,b.get('confidence_level') if b else None,av,bv)]+=1
    action=b.get('review_action') if b else None;actions[(*cell,j['block'],action)]+=1
    # Full reasons and source links retained by immutable stage seals; this table points to them.
    reader_changes.append({'trial_id':trial,'reader_id':slot,'topic_id':tid,'pairing_basis':pairing_basis,'selected_initial_matches_review_bound':lineage_matches,'selected_initial_label':t.vote(selected_a),'selected_initial_confidence':selected_a.get('confidence_level') if selected_a else None,'initial_label':av,'reviewed_label':bv,'initial_status':astate,'reviewed_status':bstate,'jointly_resolved':av is not None and bv is not None,'changed_resolved_label':av!=bv if av is not None and bv is not None else None,'review_action':action,'initial_confidence':a.get('confidence_level') if a else None,'reviewed_confidence':b.get('confidence_level') if b else None,'confidence_changed':(a.get('confidence_level')!=b.get('confidence_level')) if a and b else None,'reviewed_interpretation':b.get('topic_interpretation_assessment') if b else None,'rationale':b.get('rationale') if b else None,'confidence_reason':b.get('confidence_reason') if b else None,'interpretation_reason':b.get('interpretation_reason') if b else None,'change_reason':b.get('change_reason') if b else None,'reviewed_passage_ids':b.get('reviewed_passage_ids') if b else None,'evidence_passages':b.get('evidence_passages') if b else None,'initial_seal_reference':bound_initial})
 csvwrite(out/'coverage_by_reader_stage.csv',coverage);csvwrite(out/'attempt_ledger.csv',attempts);csvwrite(out/'reader_selection_counts.csv',reader_counts);csvwrite(out/'reader_stage_changes.private.csv',reader_changes)
 csvwrite(out/'paired_initial_lineage.private.csv',pair_lineage)
 t.write(out/'mechanical_defects.private.json',defects,True)
 def counter_table(counter,names,path):csvwrite(out/path,[dict(zip(names,k),N=v) for k,v in sorted(counter.items(),key=lambda x:str(x[0]))])
 counter_table(confidence,['stage','model','prompt_id','effort','block','label','confidence_level'],'confidence_distribution.csv')
 counter_table(confidence_assoc,['stage','model','prompt_id','effort','label','confidence_level','within_trial_disagreement','any_missing_vote'],'confidence_disagreement_association.csv')
 counter_table(support,['model','prompt_id','effort','block','interpretation_assessment'],'review_evidence_support.csv')
 counter_table(transitions,['model','prompt_id','effort','block','initial_label','reviewed_label'],'label_transitions.csv')
 counter_table(conftrans,['model','prompt_id','effort','block','initial_confidence','reviewed_confidence','initial_label','reviewed_label'],'confidence_transitions.csv')
 counter_table(actions,['model','prompt_id','effort','block','review_action'],'review_actions.csv')
 counter_table(stagecombos,['model','prompt_id','effort','block','initial_status','reviewed_status'],'stage_missingness_combinations.csv')
 # Cell/block coverage includes scheduled attempts even if the whole run is absent.
 aggregated=defaultdict(Counter)
 for r in coverage:
  k=tuple(r[x] for x in ['stage','model','prompt_id','effort','block'])
  for f in ['scheduled_reader_stage','resolved_N','abstain_N','failed_row_N','absent_topic_N','selected_N','excluded_N','confidence_defect_N','citation_defect_N','passage_coverage_defect_N']:aggregated[k][f]+=r[f]
  aggregated[k]['attempted_observed_true_stages']+=r['attempted_observed'] is True;aggregated[k]['attempted_observed_false_stages']+=r['attempted_observed'] is False;aggregated[k]['attempted_unknown_stages']+=r['attempted_observed'] is None;aggregated[k]['protocol_compliant_complete_stages']+=r['protocol_compliant_complete_stage']
  aggregated[k]['not_recorded_stages']+=r['attempt_disposition']=='not_recorded';aggregated[k]['explicit_missing_attempts']+=r['attempt_disposition']=='explicit_missing_attempt';aggregated[k]['complete_roster_stages']+=r['complete_roster']
 csvwrite(out/'coverage_by_cell_block.csv',[dict(zip(['stage','model','prompt_id','effort','block'],k),**v) for k,v in sorted(aggregated.items())])
 comparisons=[]
 def compare(kind,left,right,stage,extra=None):
  l=ens[left,stage];r=ens[right,stage]
  for mode in ['all_three_resolved','operational_majority']:
   eligible=[a['all_three_resolved'] and b['all_three_resolved'] for a,b in zip(l,r)] if mode=='all_three_resolved' else None
   comparisons.append({'contrast':kind,'stage':stage,'left_trial':left,'right_trial':right,'comparison_population':mode,**(extra or {}),**agreement([d['label'] for d in l],[d['label'] for d in r],eligible)})
 cell_topics=[];trial_summary=[];ensemble_changes=[];constituents=[];repeat_conf=Counter()
 for cell,js in sorted(cella.items()):
  js=sorted(js,key=lambda j:j['block'])
  for stage in [t.INITIAL,t.REVIEW]:
   for l,r in itertools.combinations(js,2):compare('within_cell_repeatability',l['trial_id'],r['trial_id'],stage,{'model':cell[0],'prompt_id':cell[1],'effort':cell[2]})
   for tidx,tid in enumerate(ids):
    six=[t.vote(rm.get((j['trial_id'],slot,stage),{}).get(tid)) for j in js for slot in 'ABC'];two=[ens[j['trial_id'],stage][tidx]['label'] for j in js]
    cell_topics.append({'stage':stage,'model':cell[0],'prompt_id':cell[1],'effort':cell[2],'topic_id':tid,'reader_attempts':len(js)*3,'trial_attempts':len(js),'reader_selected_out_of_6':six.count('relevant'),'reader_excluded_out_of_6':six.count('irrelevant'),'reader_missing_out_of_6':six.count(None),'trial_selected_out_of_2':two.count('relevant'),'trial_excluded_out_of_2':two.count('irrelevant'),'trial_unresolved_out_of_2':two.count(None)})
   for slot in 'ABC':
    for left,right in itertools.combinations(js,2):
     for tid in ids:
      a=rm.get((left['trial_id'],slot,stage),{}).get(tid);b=rm.get((right['trial_id'],slot,stage),{}).get(tid);av=t.vote(a);bv=t.vote(b)
      repeat_conf[(stage,*cell,a.get('confidence_level') if a else None,b.get('confidence_level') if b else None,av!=bv if av is not None and bv is not None else None,av is None or bv is None)]+=1
  for j in js:
   trial=j['trial_id']
   for stage in [t.INITIAL,t.REVIEW]:
    ds=ens[trial,stage];labs=[d['label'] for d in ds]
    trial_summary.append({'trial_id':trial,'stage':stage,'block':j['block'],'model':cell[0],'prompt_id':cell[1],'effort':cell[2],'selected_N':labs.count('relevant'),'excluded_N':labs.count('irrelevant'),'unresolved_N':labs.count(None),'all_three_resolved_N':sum(d['all_three_resolved'] for d in ds),'operational_majority_missing_third_N':sum(d['operational_with_missing_third'] for d in ds)})
    for slot in 'ABC':
     constituent=[t.vote(rm.get((trial,slot,stage),{}).get(tid)) for tid in ids]
     constituents.append({'trial_id':trial,'reader_id':slot,'stage':stage,**agreement(labs,constituent)})
   paired_initial=[t.majority([bound_rows.get((trial,slot,t.REVIEW),{}).get(tid) for slot in 'ABC']) for tid in ids]
   for tid,a,b,selected_a in zip(ids,paired_initial,ens[trial,t.REVIEW],ens[trial,t.INITIAL]):ensemble_changes.append({'trial_id':trial,'topic_id':tid,'pairing_basis':'review_bound_initials_only','selected_initial_label':selected_a['label'],'selected_initial_votes':selected_a['votes'],'initial_label':a['label'],'reviewed_label':b['label'],'initial_all_three_resolved':a['all_three_resolved'],'reviewed_all_three_resolved':b['all_three_resolved'],'changed_resolved_label':a['label']!=b['label'] if a['label'] is not None and b['label'] is not None else None,'initial_votes':a['votes'],'reviewed_votes':b['votes'],'initial_minority_slots':a['minority_slots'],'reviewed_minority_slots':b['minority_slots']})
 counter_table(repeat_conf,['stage','model','prompt_id','effort','left_confidence','right_confidence','changed_label_same_slot_across_blocks','any_missing_label'],'confidence_repeat_change_association.csv')
 csvwrite(out/'cell_topic_frequencies.csv',cell_topics);csvwrite(out/'trial_selection_counts.csv',trial_summary);csvwrite(out/'ensemble_stage_changes.csv',ensemble_changes);csvwrite(out/'homogeneous_vs_constituents.csv',constituents)
 # Retain every matched block contrast; no pooled averaging masks reversals.
 lookup={(j['model'],j['prompt_id'],j['effort'],j['block']):j['trial_id'] for j in jobs};models=sorted({j['model'] for j in jobs});efforts=['medium','high','xhigh']
 for stage in [t.INITIAL,t.REVIEW]:
  for block in blocks:
   for model in models:
    for effort in efforts:
     for pid in [f'P{i}' for i in range(1,7)]:compare('prompt_vs_P0',lookup[model,'P0',effort,block],lookup[model,pid,effort,block],stage,{'block':block})
   for pid in [f'P{i}' for i in range(7)]:
    for effort in efforts:
     for lm,rm_model in itertools.combinations(models,2):compare('model_contrast',lookup[lm,pid,effort,block],lookup[rm_model,pid,effort,block],stage,{'block':block})
    for model in models:
     for le,re in [('medium','high'),('high','xhigh'),('medium','xhigh')]:compare('effort_contrast',lookup[model,pid,le,block],lookup[model,pid,re,block],stage,{'block':block})
 csvwrite(out/'paired_comparisons.csv',comparisons)
 maps=[]
 for stage in [t.INITIAL,t.REVIEW]:
  for effort in [None]+efforts:
   subset=[j for j in jobs if effort is None or j['effort']==effort]
   for idx,tid in enumerate(ids):
    labels=[ens[j['trial_id'],stage][idx]['label'] for j in subset];c=Counter(labels)
    state='changing' if c['relevant'] and c['irrelevant'] else ('consistently_selected_complete' if c['relevant']==len(subset) else ('consistently_excluded_complete' if c['irrelevant']==len(subset) else ('only_relevant_observed_with_missing' if c['relevant'] else ('only_irrelevant_observed_with_missing' if c['irrelevant'] else 'all_missing'))))
    maps.append({'stage':stage,'effort':effort or 'complete_grid','topic_id':tid,'scheduled_trials':len(subset),'selected_N':c['relevant'],'excluded_N':c['irrelevant'],'unresolved_N':c[None],'sensitivity_status':state})
 csvwrite(out/'topic_sensitivity_maps.csv',maps)
 # No three-distinct-model recombination or optional AI audit in the two-model plan.
 t.write(out/'NOT_APPLICABLE.json',{'derived_mixed_model_ensembles':{'status':'not_applicable','reason':'Revision 9 selects two models; no three-distinct-model triples or replacement ensembles.'},'optional_extra_AI_audit':{'status':'outside_revision9_design','reason':'No extra audit seats or audit votes are scheduled.'}},True)
 # Descriptive ranges retain the underlying trial rows and denominators.
 ranges=[]
 for cell in sorted(cella):
  for stage in [t.INITIAL,t.REVIEW]:
   rs=[r for r in trial_summary if (r['model'],r['prompt_id'],r['effort'])==cell and r['stage']==stage]
   ranges.append({'model':cell[0],'prompt_id':cell[1],'effort':cell[2],'stage':stage,'selected_counts_by_block':[r['selected_N'] for r in rs],'selected_count_range':[min(r['selected_N'] for r in rs),max(r['selected_N'] for r in rs)],'unresolved_counts_by_block':[r['unresolved_N'] for r in rs],'completely_resolved_trials':sum(r['unresolved_N']==0 for r in rs),'note':'Selections with missingness are observed counts, not a complete-list estimate.'})
 t.write(out/'descriptive_ranges.json',ranges,True)
 summary={'variant':variant,'index':t.binding(index_path),'schedule_sha256':t.sha(t.ROOT/'packets/schedule.json'),'packet_manifest_sha256':t.sha(t.ROOT/'PACKET_MANIFEST.json'),'source_packet_sha256':t.manifest()['source_packet_sha256'],'catalogue_N':N,'design_revision':9,'planned_configurations':len(cella),'planned_blocks':len(blocks),'planned_trials':len(jobs),'planned_readers':planned_readers,'planned_stages':planned_stages,'planned_topic_judgments_per_stage':planned_readers*schedule['topic_count'],'planned_topic_judgments_total':planned_stages*schedule['topic_count'],'saved_stage_records':len(records),'not_recorded_stage_records':planned_stages-len(records),'explicit_missing_attempt_records':sum(r['missing_attempt'] for r in records.values()),'complete_roster_stage_records':sum(len(r['labels'])==N for r in records.values()),'paired_changes_initial_basis':'exact Stage B-bound initial seal; selected Stage A baseline remains separate','selected_initial_mismatch_reader_stages':sum(r['selected_initial_matches_review_bound'] is False for r in pair_lineage),'review_bound_initial_reader_stages':len(bound_initials),'primary_stage':t.REVIEW,'initial_stage_reported_separately':True,'derived_mixed_outputs':0,'derived_mixed_status':'not_applicable_two_selected_models','optional_extra_AI_audit_status':'outside_revision9_design','mechanical_defect_count':len(defects),'completed_utc':t.now(),'limitations':['Fixed catalogue and three saved representatives; no human-consensus reference or accuracy estimate.','Jointly resolved comparison denominators are reported; principal repeatability also requires all three votes resolved.','Initial-to-review differences combine text access, re-examination and anchoring; no isolated causal passage effect.','Confidence is ordinal self-report, not calibrated probability or vote weight.','Shared-context topic rows are not independent experiments.','Two repetitions have limited precision; no best classifier or preferred count is selected.','Missing full attempts are not converted into 354 abstentions or irrelevant labels.','Exact quotations and repeated-reason flags are mechanical diagnostics, not semantic validation.','First-attempt analysis is primary; latest explicitly indexed recovery is supplementary.']}
 t.write(out/'SUMMARY.json',summary,True)
 t.textwrite(out/'REPORT.md',f'# Saved-record descriptive analysis\n\nVariant: `{variant}`. {len(records)}/{planned_stages:,} scheduled stage records indexed; {summary["complete_roster_stage_records"]} have a full roster. Stage B is the primary endpoint; Stage A remains separate.\n\nCoverage, missingness, all block-matched contrasts, the one repeat pair per cell, prevalence-visible agreement, confidence, review transitions, source support, and constituent comparisons are preserved in named tables. Three-model derived outputs and optional extra AI audits are not applicable to this reduced design, as recorded in NOT_APPLICABLE.json. Blank numerical cells represent undefined denominators. See SUMMARY.json and immutable stage seals for limits and evidence. These are descriptive results; no human-reference accuracy, causal improvement or construct-validity claim is made.\n',True)
 return summary


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--index',required=True);p.add_argument('--out',required=True);p.add_argument('--variant',choices=['first','recovered'],default='first');a=p.parse_args();print(json.dumps(analyze(a.index,a.out,a.variant),indent=2))
if __name__=='__main__':main()
