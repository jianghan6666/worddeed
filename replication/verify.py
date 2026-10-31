"""Verify imported source identities and the locally maintained routing changes."""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from replication.paths import current_path, repository_path
# Current access instructions changed; the original import identity stays recorded.
MAINTAINED_CHANGES = {'step-3-4/README.md': 'Current release routing and connected guide',
                      'step-3-4/verify.py': 'Resolve relocated reading copies; archive identities and checks unchanged',
                      'step-2-twelve-trial-pilot/verify.py': 'Resolve historical source paths through the repository path map',
                      'scripts/restore_review_bundle.py': 'Streaming restore with the same inventory checks'}


def main():
    inventory = json.loads((ROOT/'applications/ceo-risk-preference/replication/IMPORT.json').read_text())
    changed = []
    for item in inventory['files']:
        path = repository_path(item['path'])
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != item['sha256']:
            if item['path'] not in MAINTAINED_CHANGES:
                raise ValueError('Imported scientific source changed: '+item['path'])
            changed.append({'path':current_path(item['path']), 'historical_path':item['path'],
                            'reason':MAINTAINED_CHANGES[item['path']]})
    print(json.dumps({'passed':True,'imported_files':len(inventory['files']),
                      'maintained_changes':changed}, indent=2))


if __name__ == '__main__':
    main()
