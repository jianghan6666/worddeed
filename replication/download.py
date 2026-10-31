"""Download this private repository's frozen reviewer assets with GitHub CLI."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
REPO = 'joyzhzh/ai-microfoundation-proxy'
TAG = 'reviewer-replication-2026-10-30'


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def download(gh, name, directory, transport='gh', refresh_slow=False):
    directory = Path(directory)
    if (directory/name).exists():
        return
    # A failed transfer never leaves an apparently complete asset to reuse.
    with tempfile.TemporaryDirectory(prefix='.transfer-', dir=directory) as tmp:
        if transport == 'curl':
            listing = json.loads(subprocess.check_output(
                [gh, 'release', 'view', TAG, '--repo', REPO, '--json', 'assets'], text=True))
            url = next(x['apiUrl'] for x in listing['assets'] if x['name'] == name)
            if not url.startswith(f'https://api.github.com/repos/{REPO}/releases/assets/'):
                raise ValueError('Unexpected private asset API URL')
            credential = subprocess.check_output([gh, 'auth', 'token'], text=True).strip()
            # Credentials travel on stdin, never in argv, files or printed logs.
            config = f'header = "Authorization: Bearer {credential}"\nheader = "Accept: application/octet-stream"\n'
            while True:
                # A new signed redirect can recover a slow CDN connection. This
                # optional transfer retry never changes scientific worker settings.
                fresh_url = url + '?download=1&fresh=' + str(time.time_ns())
                command = ['curl', '--http1.1', '--fail', '--silent', '--show-error',
                           '--location', '--config', '-', '--output', str(Path(tmp)/name)]
                if refresh_slow:
                    command += ['--speed-limit', '262144', '--speed-time', '15']
                try:
                    subprocess.run([*command, fresh_url], input=config, text=True, check=True)
                    break
                except subprocess.CalledProcessError as exc:
                    if not refresh_slow or exc.returncode != 28:
                        raise
                    print('Refreshing slow asset connection: '+name, flush=True)
        else:
            subprocess.run([gh, 'release', 'download', TAG, '--repo', REPO, '--pattern', name,
                            '--dir', tmp], check=True)
        (Path(tmp)/name).replace(directory/name)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--transport', choices=['gh','curl'], default='gh',
                   help='curl uses authenticated HTTP/1.1 when the default transfer route is unreliable')
    p.add_argument('--refresh-slow', action='store_true',
                   help='For curl only: retry a fresh URL after 15 seconds below 256 KiB/s; no scientific setting changes')
    p.add_argument('--source', action='store_true', help='Also download the original 9.2 GB source/model archive (2.9 GB compressed)')
    args = p.parse_args()
    gh = shutil.which('gh')
    if not gh:
        p.error('Install GitHub CLI and sign in with access to this private repository')
    args.out.mkdir(parents=True, exist_ok=True)
    delivery = json.loads((ROOT/'applications/ceo-risk-preference/replication/manifests/empirical-delivery/DELIVERY.json').read_text())
    evidence = json.loads((ROOT/'applications/ceo-risk-preference/study/screening/experiment/results-2026-10-21/BUNDLE.json').read_text())
    specs = list(delivery['parts'])
    specs.append({'name':'step2-twelve-evidence-2026-10-21.tar.gz', 'sha256':evidence['sha256']})
    if args.source:
        specs += json.loads((ROOT/'applications/ceo-risk-preference/replication/manifests/source-ceo-rd.manifest.json').read_text())['parts']
    names = [x['name'] for x in specs] + ['DELIVERY.json']
    if args.source:
        names.append('source-ceo-rd.manifest.json')
    def fetch(item):
        i, name = item
        print(f'{i}/{len(names)} {name}', flush=True)
        download(gh, name, args.out, args.transport, args.refresh_slow)
        spec = next((x for x in specs if x['name'] == name), None)
        if spec and (digest(args.out/name) != spec['sha256'] or
                     ('bytes' in spec and (args.out/name).stat().st_size != spec['bytes'])):
            raise ValueError('Asset size/hash mismatch: '+name+'; move this file aside and download again')
    # Independent transport requests only; scientific worker settings are unchanged.
    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(fetch, enumerate(names, 1)))
    # The checked-in manifests are the trust anchor, not a mutable downloaded manifest.
    expected = ROOT/'applications/ceo-risk-preference/replication/manifests/empirical-delivery/DELIVERY.json'
    if (args.out/'DELIVERY.json').read_bytes() != expected.read_bytes():
        raise ValueError('Downloaded DELIVERY.json differs from the checked-in inventory')
    if args.source:
        expected = ROOT/'applications/ceo-risk-preference/replication/manifests/source-ceo-rd.manifest.json'
        if (args.out/expected.name).read_bytes() != expected.read_bytes():
            raise ValueError('Downloaded source manifest differs from the checked-in inventory')
    print('Downloaded assets and verified compressed hashes. Reproduction verifies all archive members.')


if __name__ == '__main__':
    main()
