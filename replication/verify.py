"""Verify imported source identities and the locally maintained routing changes."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# Current access instructions changed; the original import identity stays recorded.
MAINTAINED_CHANGES = {'step-3-4/README.md': 'Current release routing and connected guide',
                      'scripts/restore_review_bundle.py': 'Streaming restore with the same inventory checks'}


def main():
    inventory = json.loads((ROOT/'replication/IMPORT.json').read_text())
    changed = []
    for item in inventory['files']:
        path = ROOT/item['path']
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != item['sha256']:
            if item['path'] not in MAINTAINED_CHANGES:
                raise ValueError('Imported scientific source changed: '+item['path'])
            changed.append({'path':item['path'], 'reason':MAINTAINED_CHANGES[item['path']]})
    print(json.dumps({'passed':True,'imported_files':len(inventory['files']),
                      'maintained_changes':changed}, indent=2))


if __name__ == '__main__':
    main()
