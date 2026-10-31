"""Verify static package files without third-party dependencies. Run from any directory."""
import hashlib,json,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
manifest=json.loads((root/'manifest.json').read_text(encoding='utf8'))
errors=[]
for item in manifest['files']:
    p=root/item['path']
    if not p.is_file():errors.append({'path':item['path'],'error':'missing'});continue
    if p.stat().st_size!=item['bytes']:errors.append({'path':item['path'],'error':'size mismatch'})
    if hashlib.sha256(p.read_bytes()).hexdigest()!=item['sha256']:errors.append({'path':item['path'],'error':'SHA256 mismatch'})
print(json.dumps({'status':'passed' if not errors else 'FAILED','files_checked':len(manifest['files']),'errors':errors},indent=2))
sys.exit(bool(errors))
