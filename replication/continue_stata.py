"""Verify the Windows refit/raw-data handoff and run its Stata regressions locally.

This records a split-runtime reproduction, not a resumed Windows workflow.
The Windows files remain byte-identical to the checksummed review export.
"""
import argparse
from datetime import datetime, timezone
import importlib.metadata
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from replication.download import digest
from replication.paths import repository_path
from replication.executables import resolve_executable
from agent_system.empirical import step4


def verify_catalogue_binding(portable, expected_hash):
    """Accept the current or historical name only for the same frozen catalogue."""
    prefix = 'REPOSITORY_ROOT/'
    if not portable.startswith(prefix):
        raise ValueError('Unexpected repository input binding: ' + portable)
    path = repository_path(portable.removeprefix(prefix))
    catalogue = ROOT / 'applications/ceo-risk-preference/study/screening/review/inputs/catalogue.json'
    if path != catalogue or digest(path) != expected_hash:
        raise ValueError('Workflow catalogue binding changed: ' + portable)


def verify_handoff(handoff, packages):
    report = json.loads((handoff / 'HANDOFF.json').read_text(encoding='utf8'))
    if not report.get('passed') or not report.get('supplementary_passed'):
        raise ValueError('Windows core and supplementary checks must pass first')
    for stage in ['step1', 'step2', 'step3', 'step4_prepare']:
        if report.get('stage_status', {}).get(stage) != 'complete':
            raise ValueError('Incomplete Windows stage: ' + stage)
    seen = set()
    for row in report['files']:
        relative = PurePosixPath(row['path'])
        if relative.is_absolute() or '..' in relative.parts or '\\' in row['path'] or row['path'] in seen:
            raise ValueError('Unsafe or duplicate handoff member')
        seen.add(row['path'])
        path = handoff / relative
        if path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(handoff.resolve()):
            raise ValueError('Handoff member must be a regular file: ' + row['path'])
        if path.stat().st_size != row['bytes'] or digest(path) != row['sha256']:
            raise ValueError('Handoff member changed: ' + row['path'])
    for package, name in [('step3_risk_score_collaborator_20261027', 'MANIFEST.json'),
                          ('step4_full_from_raw_20261027', 'manifest.json')]:
        if digest(packages / package / name) != report.get('package_manifests', {}).get(package):
            raise ValueError('Local input inventory differs from Windows run: ' + package)
    delivery = json.loads((ROOT / 'applications/ceo-risk-preference/replication/manifests/empirical-delivery/DELIVERY.json').read_text(encoding='utf8'))
    for row in delivery['files']:
        path = packages.parent / row['path']
        if path.stat().st_size != row['export_bytes'] or digest(path) != row['export_sha256']:
            raise ValueError('Restored scientific input changed: ' + row['path'])
    selection = handoff / 'workflow/step2/selected_topics.json'
    supplied = packages / 'step3_risk_score_collaborator_20261027/data/topic_selection/b1-gpt-6-astra-P0-xhigh.json'
    if digest(selection) != report['selection_sha256'] or selection.read_bytes() != supplied.read_bytes():
        raise ValueError('Screening selection differs from supplied primary handoff')
    required = ['workflow/step2/selected_topics.json', 'workflow/state.json',
                'workflow/step3/results/metrics.json', 'workflow/step3/results/risk_scores.parquet',
                'workflow/step3/firm_year_inputs.parquet', 'workflow/step4_prepare/CONNECTED_INPUTS.json',
                'workflow/step4_prepare/regression/stata/RUN_MODELS.do', 'supplementary/VERIFICATION.json']
    if not set(required).issubset(seen):
        raise ValueError('Required scientific evidence is missing from handoff inventory')
    metrics = json.loads((handoff / required[2]).read_text(encoding='utf8'))
    if not metrics['adapter_validation']['reproduction']['passed']:
        raise ValueError('New Windows scores failed supplied comparison')
    if not json.loads((handoff / required[-1]).read_text(encoding='utf8'))['passed']:
        raise ValueError('Supplementary report did not pass')
    state = json.loads((handoff / 'workflow/state.json').read_text(encoding='utf8'))
    indexed = {row['path']: row for row in report['files']}
    input_hashes = {'REPRODUCTION_ROOT/inputs/' + row['path']: row['export_sha256']
                    for row in delivery['files']}
    for stage in ['step1', 'step2', 'step3', 'step4_prepare']:
        record = state['stages'][stage]
        if record['status'] != 'complete':
            raise ValueError('Incomplete workflow record: ' + stage)
        for path, original_hash in record['outputs'].items():
            portable = path.replace('\\', '/')
            if portable.startswith('REPOSITORY_ROOT/'):
                verify_catalogue_binding(portable, original_hash)
                continue
            # Saved Step 1 returns validated immutable inputs, not copied outputs.
            if portable in input_hashes:
                if original_hash != input_hashes[portable]:
                    raise ValueError('Workflow input binding changed: ' + portable)
                continue
            if not portable.startswith('REPRODUCTION_ROOT/'):
                raise ValueError('Unexpected Windows output path: ' + portable)
            relative = portable.removeprefix('REPRODUCTION_ROOT/')
            if indexed.get(relative, {}).get('original_sha256') != original_hash:
                raise ValueError('Workflow output does not match handoff lineage: ' + relative)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--handoff', type=Path, required=True)
    parser.add_argument('--packages', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--stata', required=True)
    parser.add_argument('--stata-version', type=int, choices=[18, 19], default=19)
    parser.add_argument('--link-handoff', action='store_true',
                        help='Hard-link immutable handoff files on the same filesystem to avoid a second large copy')
    args = parser.parse_args()
    stata = resolve_executable(args.stata)
    handoff, packages, out = args.handoff.resolve(), args.packages.resolve(), args.out.resolve()
    evidence = verify_handoff(handoff, packages)
    if out.exists():
        raise FileExistsError('Use a fresh continuation directory; failed evidence is retained')
    out.mkdir(parents=True)
    windows = out / 'windows'
    windows.mkdir()
    for row in evidence['files']:
        target = windows / row['path']
        target.parent.mkdir(parents=True, exist_ok=True)
        if args.link_handoff:
            os.link(handoff / row['path'], target)
        else:
            shutil.copyfile(handoff / row['path'], target)
    shutil.copyfile(handoff / 'HANDOFF.json', windows / 'HANDOFF.json')
    verify_handoff(windows, packages)
    config = {'profile': 'reproduce', 'python': sys.executable, 'packages_root': str(packages),
              'stata_exe': stata, 'stata_version': args.stata_version}
    (out / 'reproduce.json').write_text(json.dumps(config, indent=2) + '\n')
    local_packages = {}
    for name in ['numpy', 'pandas', 'bottleneck', 'scipy', 'scikit-learn',
                 'xgboost', 'joblib', 'pyarrow', 'openpyxl', 'jsonschema', 'openai']:
        try:
            local_packages[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            local_packages[name] = None
    report = {'status': 'running', 'scope': 'Connected split-runtime reproduction: Windows Steps 1–3 and raw-data Step 4 preparation, local Stata estimation',
              'windows_commit': evidence['commit'], 'windows_workflow_run': evidence['workflow_run'],
              'windows_workflow_attempt': evidence['workflow_attempt'],
              'handoff_sha256': digest(handoff / 'HANDOFF.json'),
              'source_alignment': 'Historical density ordering is delivery-declared, not independently authenticated.',
              'topic_training': 'Saved representation replay; no new BERTopic fitting or sentiment generation.',
              'new_step3_scores_used': True, 'supplementary_passed': True,
              'stata_version_requested': args.stata_version, 'local_python': sys.version,
              'local_packages': local_packages,
              'stata_executable_sha256': digest(Path(stata)),
              'local_platform': sys.platform, 'stages': {s: 'complete' for s in ['step1', 'step2', 'step3', 'step4_prepare']}}
    destination = out / 'REPRODUCTION.json'
    def save():
        destination.write_text(json.dumps(report, indent=2) + '\n')
    save()
    try:
        result = step4.estimate(config, windows / 'workflow/step4_prepare')
        # Estimation may add files, but may never change any prepared evidence.
        verify_handoff(windows, packages)
        report.update(status='complete', result=result,
                      completed_utc=datetime.now(timezone.utc).isoformat())
        report['stages'].update(step4_prepare='complete', step4='complete')
    except BaseException as exc:
        report.update(status='failed', error=str(exc))
        raise
    finally:
        save()
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
