"""Proportional synthetic fixtures. No experimental labels are authored here."""
import copy
import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import toolkit as t
import analyze


class StudyToolTests(unittest.TestCase):
 def test_arithmetic_confidence_independent_and_missing(self):
  def row(label,confidence):return {'status':'resolved','label':label,'confidence_level':confidence}
  d=t.majority([row('relevant','low'),row('relevant','low'),row('irrelevant','high')])
  self.assertEqual(d['label'],'relevant');self.assertEqual(d['minority_slots'],[2])
  d=t.majority([row('irrelevant','low'),row('irrelevant','low'),None]);self.assertEqual(d['label'],'irrelevant');self.assertTrue(d['operational_with_missing_third']);self.assertFalse(d['all_three_resolved'])
  self.assertIsNone(t.majority([row('irrelevant','high'),row('relevant','low'),None])['label'])
  # Stage A would choose irrelevant; only reviewed rows choose relevant.
  initial=[row('irrelevant','high')]*3;review=[row('relevant','low')]*2+[None]
  self.assertEqual(t.majority(initial)['label'],'irrelevant');self.assertEqual(t.majority(review)['label'],'relevant')

 def test_pair_metrics_prevalence_and_undefined(self):
  r=analyze.agreement(['relevant','relevant','irrelevant','irrelevant',None],['relevant','irrelevant','relevant','irrelevant','relevant'])
  self.assertEqual([r[k] for k in ['a_both_relevant','b_left_relevant_right_irrelevant','c_left_irrelevant_right_relevant','d_both_irrelevant']],[1,1,1,1]);self.assertEqual(r['jointly_resolved_N'],4);self.assertEqual(r['positive_agreement'],.5);self.assertEqual(r['selected_set_jaccard'],1/3)
  r=analyze.agreement(['irrelevant'],['irrelevant']);self.assertIsNone(r['positive_agreement']);self.assertIsNone(r['selected_set_jaccard']);self.assertEqual(r['negative_agreement'],1)
  self.assertIsNone(analyze.agreement([None],[None])['raw_agreement'])

 def test_packet_exactness_order_and_duplicates(self):
  m=t.manifest();original=t.loads(t.INSPECTION/'representative-source-links.private.json');source=t.loads(t.ROOT/'packets/source_packet.private.json')['passages']
  self.assertEqual(len(source),1062);self.assertEqual(len(m['stageB']),18);self.assertEqual([r['topic_count'] for r in m['stageB']],[20]*17+[14])
  for a,b in zip(original,source):
   for field in original[0]:self.assertEqual(a[field],b[field])
  self.assertEqual(sum(len(p['exact_source_matches'])>1 for p in source),68)
  allids=[]
  for p in m['stageB']:
   allids+=p['topic_ids'];self.assertEqual(t.sha(t.ROOT/p['path']),p['sha256'])
   reassembled=''.join((t.ROOT/chunk['path']).read_text() for chunk in p['chunks'])
   self.assertEqual(reassembled,(t.ROOT/p['path']).read_text());self.assertTrue(all(c['characters']<=12000 for c in p['chunks']))
  self.assertEqual(allids,[str(i) for i in range(354)])
  for a in m['stageA']:
   packet=t.loads(t.ROOT/a['path']);self.assertEqual(len(packet['topics']),354);self.assertTrue(all(set(x)=={'topic_id','name','keywords'} for x in packet['topics']))
   self.assertNotIn('passages',packet);self.assertEqual(packet['prompt'],(t.ROOT/f'packets/prompts/{a["prompt_id"]}.md').read_text());self.assertEqual(packet['initial_output_addendum'],(t.PROTOCOL/'READER_OUTPUT_ADDENDUM.md').read_text())

 def test_changed_retained_newly_resolved_missing_and_exact_citations(self):
  # Tiny fictional packet, never the 354-topic catalogue's judgments.
  cats={'topics':[{'topic_id':str(i),'keywords':['fictional'], 'name':'fictional fixture'} for i in range(4)]}
  sources={f't{i}-r{r}':{'text':'Fictional uncertainty passage.'} for i in range(4) for r in [1,2,3]}
  initial={'labels':[{'topic_id':'0','status':'resolved','label':'irrelevant'},{'topic_id':'1','status':'resolved','label':'relevant'},{'topic_id':'2','status':'abstain','label':None}]}
  rows=[]
  for i,act in enumerate(['revised','retained','newly_resolved','unresolved']):
   resolved=i<3
   rows.append({'topic_id':str(i),'status':'resolved' if resolved else 'abstain','label':'relevant' if resolved else None,'rationale':f'Fictional topic {i}.','evidence_keywords':['fictional'] if resolved else [],'confidence_level':'low' if resolved else None,'confidence_reason':f'Fixture confidence {i}.','reviewed_passage_ids':[f't{i}-r{r}' for r in [1,2,3]],'evidence_passages':[{'passage_id':f't{i}-r1','excerpt':'uncertainty'}] if resolved else [],'topic_interpretation_assessment':'supported' if resolved else 'insufficient_evidence','interpretation_reason':f'Fixture interpretation {i}.','review_action':act,'change_reason':f'Fixture action {i}.'})
  with patch.object(t,'cat',return_value=cats),patch.object(t,'source_map',return_value=sources):
   self.assertEqual(t.validate(rows,t.REVIEW,initial=initial),[])
   bad=copy.deepcopy(rows);bad[0]['evidence_passages'][0]['excerpt']='not in passage'
   self.assertTrue(any(d['code']=='quotation' for d in t.validate(bad,t.REVIEW,initial=initial)))
   bad=copy.deepcopy(rows);bad[0].pop('confidence_level')
   self.assertTrue(any(d['code']=='missing_confidence' for d in t.validate(bad,t.REVIEW,initial=initial)));self.assertEqual(t.vote(bad[0]),'relevant')
   bad=copy.deepcopy(rows);bad[0]['reviewed_passage_ids'].pop()
   self.assertTrue(any(d['code']=='passage_coverage' for d in t.validate(bad,t.REVIEW,initial=initial)))
   bad=copy.deepcopy(rows);bad[0]['review_action']='retained'
   self.assertTrue(any(d['code']=='review_action' for d in t.validate(bad,t.REVIEW,initial=initial)))

 def test_release_missing_assembly_literal_preservation_and_no_overwrite(self):
  # Technical lifecycle fixture has 354 explicitly administrative missing initial rows,
  # then 18 explicit missing reviewed pages. It contains no authored experimental votes.
  with tempfile.TemporaryDirectory(dir=t.ROOT/'fixtures',prefix='lifecycle-') as tmp:
   root=Path(tmp);trial=t.loads(t.ROOT/'packets/schedule.json')['jobs'][0]['trial_id'];seals=[]
   for slot in 'ABC':
    meta=t.metadata(trial,slot,'synthetic-'+slot);seals.append(t.missing(root/slot/'initial',meta,t.INITIAL,'SYNTHETIC fixture: no reader attempt'))
   with self.assertRaises(ValueError):t.release_initial(seals[:2],root/'invalid-release.json')
   t.release_initial(seals,root/'release.json');release=root/'release.json'
   t.render_page(release,seals[0],'B01',root/'released/B01.json')
   buf=io.StringIO()
   with contextlib.redirect_stdout(buf):t.read_released_chunk(root/'released/B01.transport.json',start=0,end=6000)
   full=(root/'released/B01.json').read_text();self.assertIn(full[:6000],buf.getvalue());self.assertIn('END released B01 offsets 0:6000/',buf.getvalue())
   with self.assertRaises(ValueError):t.read_released_chunk(root/'released/B01.transport.json',start=0,end=6001)
   with self.assertRaises(FileExistsError):t.release_initial(seals,release)
   pages=[];meta=t.metadata(trial,'A','synthetic-A')
   for page in t.manifest()['stageB']:
    pages.append(t.missing(root/'A'/page['page_id'],meta,t.REVIEW,'SYNTHETIC missing page',initial_seal=seals[0],release=release,page_id=page['page_id']))
   assembled=t.assemble(pages,root/'A'/'assembled');r=t.record(assembled)
   self.assertEqual(r['labels'],[]);self.assertTrue(r['partial_stage']);self.assertEqual(len(r['missing_page_ids']),18)
   with self.assertRaises(ValueError):t.assemble(pages,root/'A'/'assembled')
   reviewed=[assembled]
   for slot,initial in zip('BC',seals[1:]):
    reviewed.append(t.missing(root/slot/'review',t.metadata(trial,slot,'synthetic-'+slot),t.REVIEW,'SYNTHETIC missing whole review',initial_seal=initial,release=release))
   # Changed administrative bindings survive deterministic exports; no votes are invented.
   for name in ['export-first','export-repeat']:t.export_trial(seals+reviewed,root/name)
   selected=t.loads(root/'export-first/selected_topics.json')
   self.assertEqual(selected['design_revision'],9);self.assertEqual(selected['schedule_sha256'],t.sha(t.ROOT/'packets/schedule.json'));self.assertEqual(selected['unresolved_topic_ids'],[str(i) for i in range(354)])
   self.assertEqual(selected['selected_topic_ids'],[]);self.assertEqual(selected['excluded_topic_ids'],[])
   for name in ['selected_topics.json','topic_labels.csv','HANDOFF.md','topic_details.private.json','source_evidence.private.jsonl','initial/selected_topics.json']:
    self.assertEqual((root/'export-first'/name).read_bytes(),(root/'export-repeat'/name).read_bytes())
   self.assertEqual(t.sha(root/'export-first/source_evidence.private.jsonl'),t.sha(t.ROOT/'packets/source_evidence.private.jsonl'))
   changed_meta=t.metadata(trial,'A','different-chat')
   with self.assertRaises(ValueError):t.missing(root/'bad-chat',changed_meta,t.REVIEW,'fixture',initial_seal=seals[0],release=release)
   # Literal importer preserves JSON bytes including whitespace, schema-defective confidence
   # and all reasons. Fictional small catalogue avoids authoring any study vote.
   cats={'topics':[{'topic_id':'fixture','keywords':['invented'],'name':'synthetic'}]}
   payload={'labels':[{'topic_id':'fixture','status':'resolved','label':'relevant','rationale':'Fictional fixture only','evidence_keywords':['invented'],'confidence_reason':'Fictional reporting defect'}]}
   literal=root/'literal.json';literal.write_text(json.dumps(payload,indent=3)+'\n\n')
   with patch.object(t,'cat',return_value=cats):
    sealed=t.seal_literal(literal,root/'literal-sealed',meta,t.INITIAL)
   rec=t.record(sealed);self.assertEqual(Path(rec['literal_response']['path']).read_bytes(),literal.read_bytes());self.assertTrue(any(d['code']=='missing_confidence' for d in rec['defects']))
   with patch.object(t,'cat',return_value=cats):
    with self.assertRaises(ValueError):t.seal_literal(literal,root/'literal-sealed',meta,t.INITIAL)
   Path(rec['literal_response']['path']).write_text('tampered fixture')
   with self.assertRaises(ValueError):t.record(sealed)

 def test_unsupported_raw_source_and_whole_review_import_rejected(self):
  with self.assertRaises(ValueError):t.read_chunk('B','B01',1)
  with tempfile.TemporaryDirectory(dir=t.ROOT/'fixtures') as tmp:
   with self.assertRaises(ValueError):t.seal_literal(Path(tmp)/'unused.json',Path(tmp)/'out',{},t.REVIEW)

 def test_analysis_grid_and_missingness_without_study_votes(self):
  # Four fictional IDs shrink only the fixture's table size; all 84 stored assignments
  # are traversed, with no reader records or study labels invented.
  fictional={'topics':[{'topic_id':'fixture-'+str(i),'keywords':['fictional'],'name':'fictional'} for i in range(4)]}
  with tempfile.TemporaryDirectory(dir=t.ROOT/'fixtures') as tmp:
   root=Path(tmp);index=root/'index.json';t.write(index,{'schema_version':t.VERSION,'records':[]})
   with patch.object(t,'cat',return_value=fictional):summary=analyze.analyze(index,root/'analysis')
   self.assertEqual(summary['saved_stage_records'],0);self.assertEqual(summary['not_recorded_stage_records'],504);self.assertEqual(summary['derived_mixed_outputs'],0);self.assertEqual(summary['derived_mixed_status'],'not_applicable_two_selected_models');self.assertEqual(summary['planned_topic_judgments_per_stage'],89208);self.assertEqual(summary['planned_topic_judgments_total'],178416)
   import csv
   with (root/'analysis/paired_comparisons.csv').open() as f:comparisons=list(csv.DictReader(f))
   self.assertEqual(len(comparisons),960);self.assertTrue(all(r['jointly_resolved_N']=='0' and r['raw_agreement']=='' for r in comparisons))
   with (root/'analysis/topic_sensitivity_maps.csv').open() as f:maps=list(csv.DictReader(f))
   self.assertTrue(all(r['sensitivity_status']=='all_missing' for r in maps))
   from collections import Counter
   self.assertEqual(Counter(r['contrast'] for r in comparisons),{'within_cell_repeatability':168,'prompt_vs_P0':288,'model_contrast':168,'effort_contrast':336})
   with (root/'analysis/cell_topic_frequencies.csv').open() as f:frequencies=list(csv.DictReader(f))
   self.assertTrue(all(r['reader_missing_out_of_6']=='6' and r['trial_unresolved_out_of_2']=='2' for r in frequencies))
   self.assertFalse(list((root/'analysis').glob('derived_mixed*')))
   self.assertEqual(t.loads(root/'analysis/NOT_APPLICABLE.json')['derived_mixed_model_ensembles']['status'],'not_applicable')

 def test_revision9_schedule_and_packet_equivalence(self):
  from collections import Counter
  schedule=t.loads(t.ROOT/'packets/schedule.json');jobs=schedule['jobs'];assign=t.loads(t.ROOT/'packets/cmd_assignments.json')
  self.assertEqual(schedule['design_revision'],9);self.assertEqual(len(jobs),84)
  self.assertEqual([j['dispatch_order'] for j in jobs],list(range(1,85)))
  self.assertEqual({j['model'] for j in jobs},{'gpt-6.1-sol','gpt-6-astra'})
  self.assertEqual(Counter(j['block'] for j in jobs),{1:42,2:42})
  self.assertEqual(set(Counter((j['model'],j['prompt_id'],j['effort']) for j in jobs).values()),{2})
  self.assertEqual(len(assign['commanders']),4);self.assertTrue(all(len(c['trial_ids'])==21 for c in assign['commanders']))
  eq=t.loads(t.ROOT/'PACKET_EQUIVALENCE.json');self.assertEqual(eq['scientific_files_unchanged'],654);self.assertTrue(eq['all_scientific_bytes_preserved']);self.assertTrue(eq['retained_trial_order_matches_v8_filter'])
  old=t.ROOT.parent.parent/'step2-expanded-ai-pilot-v8/data-analysis'
  old_schedule=t.loads(old/'packets/schedule.json')
  retained=[j['trial_id'] for j in old_schedule['jobs'] if j['model'] in {'gpt-6.1-sol','gpt-6-astra'} and j['block'] in {1,2}]
  self.assertEqual([j['trial_id'] for j in jobs],retained)
  for rel in eq['scientific_file_paths']:self.assertEqual(t.sha(t.ROOT/rel),t.sha(old/rel))
  for name in eq['schemas_unchanged']:self.assertEqual(t.sha(t.ROOT/'schemas'/name),t.sha(old/'schemas'/name))

 def test_strict_json_duplicate_key_rejected(self):
  with tempfile.NamedTemporaryFile(dir=t.ROOT/'fixtures',mode='w',suffix='.json') as f:
   f.write('{"labels": [], "labels": []}');f.flush()
   with self.assertRaises(ValueError):t.literal_load(f.name)

 def test_recovered_baseline_does_not_replace_review_bound_initial(self):
  # Simulated sealed analysis records for one fictional topic. This tests analysis
  # lineage, not the 354-topic/18-page collection procedure or study judgments.
  import csv
  fictional={'topics':[{'topic_id':'fixture-lineage','name':'fictional','keywords':['fictional']}]}
  sources={f'tfixture-lineage-r{i}':{'text':'Fictional passage'} for i in [1,2,3]}
  with tempfile.TemporaryDirectory(dir=t.ROOT/'fixtures',prefix='lineage-') as tmp:
   root=Path(tmp);trial=t.loads(t.ROOT/'packets/schedule.json')['jobs'][0]['trial_id'];entries=[]
   def saved(directory,meta,stage,row,attempt='first',**extra):
    directory.mkdir(parents=True);literal=directory/'literal.json';t.write(literal,{'labels':[row]})
    rec={'stage':stage,'metadata':meta,'labels':[row],'attempt_id':attempt,'missing_attempt':False,'page_id':None,'literal_response':t.binding(literal),**extra}
    t.write(directory/'record.json',rec);t.write(directory/'seal.json',{'record':t.binding(directory/'record.json')})
    return directory/'seal.json'
   for slot in 'ABC':
    meta=t.metadata(trial,slot,'synthetic-lineage-'+slot)
    original={'topic_id':'fixture-lineage','status':'resolved','label':'relevant','rationale':'Fictional original','evidence_keywords':['fictional'],'confidence_level':'high','confidence_reason':'Fictional original confidence'}
    orig=saved(root/slot/'original',meta,t.INITIAL,original)
    replacement={**original,'label':'irrelevant','confidence_level':'low'}
    recovered=saved(root/slot/'recovered',meta,t.INITIAL,replacement,'technical-2',recovery={'original_seal':t.binding(orig),'administrative_technical_reason':'Synthetic reporting recovery'})
    reviewed={**replacement,'reviewed_passage_ids':list(sources),'evidence_passages':[{'passage_id':'tfixture-lineage-r1','excerpt':'Fictional'}],'topic_interpretation_assessment':'mixed','interpretation_reason':'Fictional interpretation','review_action':'revised','change_reason':'Fictional change from original'}
    page=saved(root/slot/'page',meta,t.REVIEW,reviewed,initial_seal=t.binding(orig))
    review=saved(root/slot/'review',meta,t.REVIEW,reviewed,initial_seal=t.binding(orig),page_seals=[t.binding(page)])
    entries.extend([{'trial_id':trial,'reader_id':slot,'stage':t.INITIAL,'first_seal':str(orig),'recovered_seals':[str(recovered)]},{'trial_id':trial,'reader_id':slot,'stage':t.REVIEW,'first_seal':str(review),'recovered_seals':[]}])
   index=root/'index.json';t.write(index,{'schema_version':t.VERSION,'records':entries})
   with patch.object(t,'cat',return_value=fictional),patch.object(t,'source_map',return_value=sources):
    summary=analyze.analyze(index,root/'analysis','recovered')
   def rows(name):
    with (root/'analysis'/name).open() as f:return list(csv.DictReader(f))
   changes=[r for r in rows('reader_stage_changes.private.csv') if r['trial_id']==trial]
   self.assertEqual(len(changes),3)
   for row in changes:
    self.assertEqual(row['selected_initial_label'],'irrelevant');self.assertEqual(row['initial_label'],'relevant');self.assertEqual(row['reviewed_label'],'irrelevant');self.assertEqual(row['changed_resolved_label'],'True')
    self.assertEqual(row['selected_initial_confidence'],'low');self.assertEqual(row['initial_confidence'],'high');self.assertEqual(row['reviewed_confidence'],'low');self.assertEqual(row['confidence_changed'],'True');self.assertEqual(row['review_action'],'revised');self.assertEqual(row['selected_initial_matches_review_bound'],'False')
   label=[r for r in rows('label_transitions.csv') if r['model']==t.job(trial)['model'] and r['prompt_id']==t.job(trial)['prompt_id'] and r['effort']==t.job(trial)['effort'] and r['block']=='1' and r['initial_label']=='relevant' and r['reviewed_label']=='irrelevant']
   self.assertEqual(label[0]['N'],'3')
   conf=[r for r in rows('confidence_transitions.csv') if r['initial_confidence']=='high' and r['reviewed_confidence']=='low']
   self.assertEqual(sum(int(r['N']) for r in conf),3)
   ensemble=next(r for r in rows('ensemble_stage_changes.csv') if r['trial_id']==trial)
   self.assertEqual(ensemble['selected_initial_label'],'irrelevant');self.assertEqual(ensemble['initial_label'],'relevant');self.assertEqual(ensemble['reviewed_label'],'irrelevant');self.assertEqual(ensemble['changed_resolved_label'],'True')
   baseline=next(r for r in rows('trial_selection_counts.csv') if r['trial_id']==trial and r['stage']==t.INITIAL)
   self.assertEqual(baseline['excluded_N'],'1');self.assertEqual(summary['selected_initial_mismatch_reader_stages'],3)
   lineages=[r for r in rows('paired_initial_lineage.private.csv') if r['trial_id']==trial]
   self.assertTrue(all(r['selected_initial_matches_review_bound']=='False' for r in lineages))

if __name__=='__main__':
 (t.ROOT/'fixtures').mkdir(exist_ok=True)
 unittest.main()
