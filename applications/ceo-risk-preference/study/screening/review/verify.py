#!/usr/bin/env python3
"""Verify the coauthor delivery and Step 3 selections without model calls."""
import csv
import hashlib
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = next(parent for parent in HERE.parents if (parent / 'replication/paths.json').is_file())
sys.path.insert(0, str(ROOT))
from replication.paths import repository_path


def main():
    manifest = json.loads((HERE / 'MANIFEST.json').read_text())
    index = json.loads((HERE / 'TRIAL_INDEX.json').read_text())
    package = repository_path(index['evidence_package_root_repository_relative'])
    bundle = json.loads((package / 'BUNDLE.json').read_text())
    bundle_hashes = {item['path']: item['sha256'] for item in bundle['files']}
    for item in manifest['copies']:
        destination = HERE / item['path']
        original = repository_path(item['source_repository_relative'])
        payload = destination.read_bytes()
        assert hashlib.sha256(payload).hexdigest() == item['sha256'], destination
        if original.exists():
            assert payload == original.read_bytes(), original
        else:
            # A fresh clone can verify the catalogue against the release inventory.
            archive_path = original.relative_to(package).as_posix()
            assert bundle_hashes[archive_path] == item['sha256'], original

    catalogue_path = HERE / 'inputs/catalogue.json'
    catalogue = json.loads(catalogue_path.read_text())
    catalogue_hash = hashlib.sha256(catalogue_path.read_bytes()).hexdigest()
    topic_ids = {str(topic['topic_id']) for topic in catalogue['topics']}
    assert len(topic_ids) == 354
    assert len(index['trials']) == len({t['trial_id'] for t in index['trials']}) == 12
    totals = {variant: dict.fromkeys(['relevant', 'irrelevant', 'unresolved'], 0)
              for variant in ['primary', 'supplementary']}
    for trial in index['trials']:
        for variant, item in trial['variants'].items():
            selection = json.loads((HERE / item['selected_topics']).read_text())
            rows = list(csv.DictReader((HERE / item['topic_labels']).open()))
            assert len(rows) == 354 and {r['topic_id'] for r in rows} == topic_ids
            assert selection['trial_id'] == trial['trial_id']
            assert selection['variant'] == index['variant_mapping'][variant]
            assert selection['topic_model_id'] == catalogue['topic_model_id']
            assert selection['catalogue_sha256'] == catalogue_hash
            assert selection['final_stage'] == 'source_review'
            final = selection['final']
            sets = [set(final[key]) for key in totals[variant]]
            assert set.union(*sets) == topic_ids and sum(map(len, sets)) == 354
            for label in totals[variant]:
                from_csv = {row['topic_id'] for row in rows
                            if (row['label'] if row['status'] == 'resolved' else 'unresolved') == label}
                assert from_csv == set(final[label]), (trial['trial_id'], variant, label)
                assert item['counts'][label] == len(final[label])
                totals[variant][label] += len(final[label])
    assert totals['primary'] == {'relevant': 3795, 'irrelevant': 452, 'unresolved': 1}
    assert totals['supplementary'] == {'relevant': 3796, 'irrelevant': 452, 'unresolved': 0}
    prompt_blocks = re.findall(r'```markdown\n(.*?)```', (HERE / 'MEMO.md').read_text(), re.S)
    assert prompt_blocks == [(HERE / 'protocol/prompts/P0-direct.md').read_text(),
                             (HERE / 'protocol/SOURCE_REVIEW_PROMPT.md').read_text()]
    print(f"Verified {len(manifest['copies'])} frozen copies, 12 trials, 24 selections, "
          f"354 topics per selection and two exact memo prompts. Totals: {totals}")


if __name__ == '__main__':
    main()
