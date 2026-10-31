#!/usr/bin/env python3
"""Replay the ratified cohort from exported saved records; no model calls or dispatch."""
import argparse
import csv
import functools
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
FROZEN = HERE / 'evidence/runtime/data-analysis'
sys.path.insert(0, str(FROZEN))
import toolkit as t
import cohort_analysis as analysis


def resolve(path):
    path = Path(path)
    return path if path.is_absolute() else HERE / path


def raw_load(path):
    return json.loads(resolve(path).read_text(encoding='utf-8'))


def digest(path):
    return hashlib.sha256(resolve(path).read_bytes()).hexdigest()


def package_binding(path):
    path = resolve(path).resolve()
    return {'path': str(path.relative_to(HERE)), 'sha256': digest(path)}


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2)+'\n')


def verify_export():
    provenance = raw_load('PROVENANCE.json')
    for entry in provenance['files']:
        if digest(entry['path']) != entry['sha256']:
            raise ValueError('Export identity mismatch: '+entry['path'])
    schedule = raw_load(HERE.parent / 'SCHEDULE.json')
    index = raw_load('RECORD_INDEX.json')
    trials = {j['trial_id'] for j in schedule['jobs']}
    if len(trials) != 12 or len(index['records']) != 72:
        raise ValueError('Ratified cohort size mismatch')
    expected = {(j['trial_id'], slot, stage) for j in schedule['jobs']
                for slot in 'ABC' for stage in [t.INITIAL, t.REVIEW]}
    actual = {(x['trial_id'], x['reader_id'], x['stage']) for x in index['records']}
    if actual != expected:
        raise ValueError('Record-index assignment mismatch')
    # The frozen scientific schedule stays intact; only analysis iteration uses the
    # current ratified subset. Original record identities still refer to collection.
    original_load = t.loads
    def load_for_cohort(path):
        if resolve(path).resolve() == (FROZEN/'packets/schedule.json').resolve():
            return schedule
        return original_load(resolve(path))
    t.loads = load_for_cohort
    t.sha = digest
    t.binding = package_binding
    t.record = functools.lru_cache(maxsize=None)(t.record)
    return schedule, index


def export_handoffs(out, schedule, index, variant):
    records, _ = analysis.read_index(index, variant)
    index_entries = raw_load(index)['records']
    topics = t.cat()['topics']
    for job in schedule['jobs']:
        trial = job['trial_id']
        folder = out / 'handoffs' / trial
        folder.mkdir(parents=True)
        selected = {}; readers = {}
        for stage in [t.INITIAL, t.REVIEW]:
            rows = {slot: {r['topic_id']:r for r in records[(trial,slot,stage)]['labels']}
                    for slot in 'ABC'}
            decisions = []
            for topic in topics:
                tid = topic['topic_id']
                decision = t.majority([rows[slot].get(tid) for slot in 'ABC'])
                decisions.append({'topic_id':tid, 'name':topic['name'], **decision})
            name = 'topic_labels.csv' if stage == t.REVIEW else 'initial_topic_labels.csv'
            with (folder/name).open('w', newline='', encoding='utf-8') as stream:
                w=csv.DictWriter(stream, fieldnames=['topic_id','name','status','label','vote_A','vote_B','vote_C','all_three_resolved','minority_readers','missing_readers'])
                w.writeheader()
                for d in decisions:
                    w.writerow({k:d[k] for k in ['topic_id','name','status','label','all_three_resolved']} |
                               {'vote_'+s:v for s,v in zip('ABC',d['votes'])} |
                               {'minority_readers':','.join('ABC'[i] for i in d['minority_slots']),
                                'missing_readers':','.join('ABC'[i] for i in d['missing_slots'])})
            selected[stage] = {'relevant':[d['topic_id'] for d in decisions if d['label']=='relevant'],
                               'irrelevant':[d['topic_id'] for d in decisions if d['label']=='irrelevant'],
                               'unresolved':[d['topic_id'] for d in decisions if d['label'] is None]}
            readers[stage] = []
            for entry in index_entries:
                if entry['trial_id'] != trial or entry['stage'] != stage:
                    continue
                seal = (entry['recovered_seals'][-1] if variant=='recovered' and entry['recovered_seals'] else entry['first_seal'])
                readers[stage].append({'reader_id':entry['reader_id'],'seal':seal,
                                       'record':raw_load(seal)['record']['path']})
        write_json(folder/'selected_topics.json', {
            'trial_id':trial, 'variant':variant, 'model_requested':job['model'],
            'effort_requested':job['effort'], 'prompt_id':'P0', 'block':job['block'],
            'topic_model_id':t.cat()['topic_model_id'], 'catalogue_sha256':digest(FROZEN/'packets/catalogue.json'),
            'prompt_sha256':records[(trial,'A',t.REVIEW)]['prompt_sha256'],
            'source_packet_original_sha256':t.manifest()['source_packet_sha256'],
            'final_stage':t.REVIEW, 'rule':'unweighted_two_matching_resolved_votes_out_of_three',
            'final':selected[t.REVIEW], 'initial_separate':selected[t.INITIAL],
            'reader_records_package_relative':readers,
            'reason_location':'Each linked record retains every authored rationale, confidence reason, interpretation/change reason and evidence field, including minority votes. Missing rows remain absent.'})


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args=parser.parse_args()
    if args.out.exists():
        raise ValueError('Use a new output directory; preserve prior results')
    schedule,_=verify_export()
    args.out.mkdir(parents=True)
    for variant in ['first','recovered']:
        out=args.out/variant
        summary=analysis.analyze(HERE/'RECORD_INDEX.json',out,variant)
        summary.update(scope_amendment=3,ratified_schedule_sha256=digest(HERE.parent/'SCHEDULE.json'),
                       scope_note='Twelve completed P0 trials; original 84-trial schedule hash is historical collection provenance. The 72 unadmitted trials are outside current scope, not missing attempts.')
        write_json(out/'SUMMARY.json',summary)
        export_handoffs(out,schedule,HERE/'RECORD_INDEX.json',variant)
        print(json.dumps({k:summary[k] for k in ['variant','planned_trials','saved_stage_records','not_recorded_stage_records','complete_roster_stage_records','mechanical_defect_count']}))


if __name__ == '__main__':
    main()
