"""Verify the Git reading copy and its exact Step 2 handoff, without dependencies."""
import ast
import hashlib
import json
from pathlib import Path, PurePosixPath
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from replication.paths import repository_path


def delivery_path(name):
    return repository_path('step-3-4/' + name)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    delivery = json.loads(delivery_path('DELIVERY.json').read_text())
    rows = {row['path']: row for row in delivery['files']}
    assert len(rows) == len(delivery['files']), 'Duplicate inventory entries'
    assert len(set(delivery['git_paths'])) == len(delivery['git_paths'])
    for name in delivery['git_paths']:
        path = delivery_path(name)
        row = rows[name]
        assert path.stat().st_size == row['export_bytes'], name
        assert digest(path) == row['export_sha256'], name
        if path.suffix == '.py':
            ast.parse(path.read_text(encoding='utf-8-sig'), filename=name)
    for manifest_name in delivery['git_paths']:
        if PurePosixPath(manifest_name).name.lower() != 'manifest.json':
            continue
        path = delivery_path(manifest_name)
        manifest = json.loads(path.read_text())
        for item in manifest['files']:
            name = str(PurePosixPath(manifest_name).parent / item['path'])
            assert rows[name]['export_bytes'] == item['bytes'], name
            assert rows[name]['export_sha256'] == item['sha256'], name
    trial = 'b1-gpt-6-astra-P0-xhigh'
    selected = ROOT / 'applications/ceo-risk-preference/study/prediction/data/topic_selection' / (trial + '.json')
    source = ROOT / 'applications/ceo-risk-preference/study/screening/review/results/primary/handoffs' / trial / 'selected_topics.json'
    assert selected.read_bytes() == source.read_bytes(), 'Step 2 selection mismatch'
    selection = json.loads(selected.read_text())
    assert (len(selection['final']['relevant']), len(selection['final']['irrelevant']), len(selection['final']['unresolved'])) == (321, 33, 0)
    print(f"Verified {len(delivery['git_paths'])} browsable files, {len(rows)} inventoried archive files, export manifest consistency and exact Step 2 linkage.")


if __name__ == '__main__':
    main()
