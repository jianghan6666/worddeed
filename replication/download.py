"""Download this private repository's frozen reviewer assets with GitHub CLI."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
REPO = 'joyzhzh/ai-microfoundation-proxy'
TAG = 'reviewer-replication-2026-10-30'


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def download(gh, name, directory):
    subprocess.run([gh, 'release', 'download', TAG, '--repo', REPO, '--pattern', name,
                    '--dir', str(directory), '--skip-existing'], check=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--source', action='store_true', help='Also download the original 9.2 GB source/model archive (2.9 GB compressed)')
    args = p.parse_args()
    gh = shutil.which('gh')
    if not gh:
        p.error('Install GitHub CLI and sign in with access to this private repository')
    args.out.mkdir(parents=True, exist_ok=True)
    delivery = json.loads((ROOT/'step-3-4/DELIVERY.json').read_text())
    evidence = json.loads((ROOT/'step-2-mvp-simple/experiment/expanded-ai-pilot/results-2026-10-21/BUNDLE.json').read_text())
    specs = list(delivery['parts'])
    specs.append({'name':'step2-twelve-evidence-2026-10-21.tar.gz', 'sha256':evidence['sha256']})
    if args.source:
        specs += json.loads((ROOT/'replication/manifests/source-ceo-rd.manifest.json').read_text())['parts']
    names = [x['name'] for x in specs] + ['DELIVERY.json']
    if args.source:
        names.append('source-ceo-rd.manifest.json')
    for i, name in enumerate(names, 1):
        print(f'{i}/{len(names)} {name}', flush=True)
        download(gh, name, args.out)
        spec = next((x for x in specs if x['name'] == name), None)
        if spec and (digest(args.out/name) != spec['sha256'] or
                     ('bytes' in spec and (args.out/name).stat().st_size != spec['bytes'])):
            raise ValueError('Asset size/hash mismatch: '+name+'; move this file aside and download again')
    # The checked-in manifests are the trust anchor, not a mutable downloaded manifest.
    expected = ROOT/'step-3-4/DELIVERY.json'
    if (args.out/'DELIVERY.json').read_bytes() != expected.read_bytes():
        raise ValueError('Downloaded DELIVERY.json differs from the checked-in inventory')
    if args.source:
        expected = ROOT/'replication/manifests/source-ceo-rd.manifest.json'
        if (args.out/expected.name).read_bytes() != expected.read_bytes():
            raise ValueError('Downloaded source manifest differs from the checked-in inventory')
    print('Downloaded assets and verified compressed hashes. Reproduction verifies all archive members.')


if __name__ == '__main__':
    main()
