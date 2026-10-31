"""Fresh-download and verify every source/model archive byte with bounded disk use.

Downloads each transport part into a new temporary directory, verifies the entire
compressed archive and all expanded members, then discards only these temporary
downloads. It does not extract files or fit a topic model.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from replication.download import REPO, TAG, digest, download
from replication.restore import restore


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True, help='Verification receipt JSON')
    parser.add_argument('--transport', choices=['gh','curl'], default='gh')
    parser.add_argument('--refresh-slow', action='store_true')
    parser.add_argument('--temp-parent', type=Path, help='Filesystem for disposable download parts')
    args = parser.parse_args()
    gh = shutil.which('gh')
    if not gh:
        parser.error('Install GitHub CLI and sign in with private repository access')
    manifest = ROOT/'applications/ceo-risk-preference/replication/manifests/source-ceo-rd.manifest.json'
    spec = json.loads(manifest.read_text())
    assets = []
    with tempfile.TemporaryDirectory(prefix='nbm-source-verify-', dir=args.temp_parent) as tmp, \
            ThreadPoolExecutor(max_workers=4) as pool:
        directory = Path(tmp)
        download(gh, manifest.name, directory, args.transport, args.refresh_slow)
        if (directory/manifest.name).read_bytes() != manifest.read_bytes():
            raise ValueError('Downloaded manifest differs from the checked-in trust anchor')
        pending = {}
        next_index = 0
        def prefetch():
            nonlocal next_index
            while len(pending) < 4 and next_index < len(spec['parts']):
                part = spec['parts'][next_index]
                pending[part['name']] = pool.submit(download, gh, part['name'], directory, args.transport, args.refresh_slow)
                next_index += 1
        prefetch()
        def acquire(part):
            print(f"{len(assets)+1}/{len(spec['parts'])} {part['name']}", flush=True)
            pending.pop(part['name']).result()
            prefetch()
            assets.append(part)
            return directory/part['name']
        report = restore(manifest, acquire=acquire, release=lambda path: Path(path).unlink())
    report.update(completed_utc=datetime.now(timezone.utc).isoformat(), repository=REPO,
                  release=TAG, manifest_sha256=digest(manifest), downloaded_parts=assets,
                  compressed_bytes=sum(p['bytes'] for p in assets),
                  expanded_bytes=sum(p['export_bytes'] for p in spec['files']),
                  method='Fresh GitHub download; stream all archive members without extraction',
                  limitations='Archive integrity only; no new topic fitting, sentiment generation or historical alignment authentication')
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k != 'downloaded_parts'}, indent=2))


if __name__ == '__main__':
    main()
