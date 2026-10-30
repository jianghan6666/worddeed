"""Verify release file sizes and SHA256 using only the Python standard library."""
from pathlib import Path
import hashlib
import json
import sys

root = Path(__file__).resolve().parents[1]
manifest = json.loads((root / 'manifest.json').read_text(encoding='utf8'))
errors = []
for item in manifest['files']:
    path = root / item['path']
    if not path.is_file():
        errors.append([item['path'], 'missing'])
        continue
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b''):
            digest.update(chunk)
    if path.stat().st_size != item['bytes'] or digest.hexdigest() != item['sha256']:
        errors.append([item['path'], 'size or SHA256 differs'])
print(json.dumps({'passed': not errors, 'checked_files': len(manifest['files']),
                  'errors': errors}, indent=2))
sys.exit(bool(errors))
