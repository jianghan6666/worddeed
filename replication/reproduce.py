"""Restore frozen evidence and reproduce the four-step study in a new run directory."""
import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from replication.restore import restore

EVIDENCE = ROOT/'applications/ceo-risk-preference/study/screening/experiment/results-2026-10-21'
TRIAL = 'b1-gpt-6-astra-P0-xhigh'


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda: f.read(1024*1024), b''):
            h.update(b)
    return h.hexdigest()


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False)+'\n')


def call(command, log):
    print('Running:', ' '.join(map(str, command)), flush=True)
    with log.open('a') as f:
        subprocess.run(list(map(str, command)), cwd=ROOT, check=True, stdout=f,
                       stderr=subprocess.STDOUT, env={**os.environ, 'PYTHONDONTWRITEBYTECODE':'1',
                       'PYTHONUNBUFFERED':'1'})


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--downloads', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--stata')
    p.add_argument('--stata-version', type=int, choices=[18,19], default=19)
    p.add_argument('--through', choices=['step1','step2','step3','step4_prepare','step4'], default='step4')
    args = p.parse_args()
    out, downloads = args.out.resolve(), args.downloads.resolve()
    out.mkdir(parents=True, exist_ok=True)
    logs = out/'logs'; logs.mkdir(exist_ok=True)
    manifest = ROOT/'applications/ceo-risk-preference/replication/manifests/empirical-delivery/DELIVERY.json'
    if (downloads/'DELIVERY.json').read_bytes() != manifest.read_bytes():
        raise ValueError('Download manifest differs from the checked-in frozen inventory')
    stamp = out/'RESTORE.json'
    if not stamp.exists():
        receipt = restore(downloads/'DELIVERY.json', out/'inputs')
        receipt['manifest_sha256'] = digest(manifest)
        write(stamp, receipt)
    else:
        if json.loads(stamp.read_text())['manifest_sha256'] != digest(manifest):
            raise ValueError('Restored input inventory changed')
        for row in json.loads(manifest.read_text())['files']:
            f = out/'inputs'/row['path']
            if f.stat().st_size != row['export_bytes'] or digest(f) != row['export_sha256']:
                raise ValueError('Restored input changed: '+row['path'])
    call([sys.executable,EVIDENCE/'restore.py','--archive',downloads/'step2-twelve-evidence-2026-10-21.tar.gz'],logs/'screening-restore.log')
    call([sys.executable,ROOT/'applications/ceo-risk-preference/study/screening/review/verify.py'],logs/'screening-delivery.log')
    call([sys.executable,ROOT/'replication/verify_delivery.py'],logs/'prediction-delivery.log')
    if not (out/'screening').exists():
        call([sys.executable,ROOT/'replication/replay_screening.py','--out',out/'screening'],logs/'screening-replay.log')
    call([sys.executable,EVIDENCE/'verify_replay.py','--out',out/'screening'],logs/'screening-verify.log')
    selection = out/'screening/first/handoffs'/TRIAL/'selected_topics.json'
    delivered = out/'inputs/packages/step3_risk_score_collaborator_20261027/data/topic_selection'/f'{TRIAL}.json'
    if selection.read_bytes() != delivered.read_bytes():
        raise ValueError('Replayed Step 2 handoff differs from the Step 3 selection')
    config = {'profile':'reproduce', 'python':sys.executable,
              'packages_root':str(out/'inputs/packages'),
              'catalogue':str(ROOT/'applications/ceo-risk-preference/study/screening/review/inputs/catalogue.json'),
              'selection':str(selection), 'step1':{'mode':'saved'},
              'stata_version':args.stata_version}
    if args.stata:
        config['stata_exe'] = str(Path(args.stata).expanduser().resolve())
    write(out/'reproduce.json', config)
    environment = {'python':sys.version, 'packages':{}, 'platform':sys.platform}
    for name in ['numpy','pandas','bottleneck','scipy','scikit-learn','xgboost','joblib','pyarrow','openpyxl','jsonschema','openai']:
        try: environment['packages'][name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError: environment['packages'][name] = None
    write(out/'ENVIRONMENT.json', environment)
    call([sys.executable,'-m','agent_system.empirical','--config',out/'reproduce.json',
          '--out',out/'workflow','--through',args.through],logs/'workflow.log')
    state = json.loads((out/'workflow/state.json').read_text())
    write(out/'REPRODUCTION.json', {'completed_utc':datetime.now(timezone.utc).isoformat(),
          'status':state['status'], 'requested_through':args.through,
          'stages':{k:v['status'] for k,v in state['stages'].items()},
          'screening_replay':'passed', 'selection_matches_delivered':True,
          'source_alignment':'Historical density ordering is delivery-declared, not independently authenticated.',
          'topic_training':'Saved representation replay; no new BERTopic fitting or sentiment generation.',
          'stata_version_requested':args.stata_version})
    print((out/'REPRODUCTION.json').read_text())


if __name__ == '__main__':
    main()
