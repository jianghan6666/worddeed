#!/usr/bin/env python3
"""Compare a fresh offline replay with all saved cohort analysis and handoff files."""
import argparse
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', required=True, type=Path)
    args=parser.parse_args()
    frozen=HERE/'analysis'
    names={p.relative_to(frozen) for p in frozen.rglob('*') if p.is_file()}
    actual={p.relative_to(args.out) for p in args.out.rglob('*') if p.is_file()}
    if names != actual:
        raise ValueError('Replay file set differs from the saved package')
    for name in sorted(names):
        if name.name=='SUMMARY.json':
            left=json.loads((frozen/name).read_text())
            right=json.loads((args.out/name).read_text())
            left.pop('completed_utc');right.pop('completed_utc')
        else:
            left=(frozen/name).read_bytes();right=(args.out/name).read_bytes()
        if left != right:
            raise ValueError('Replay differs: '+str(name))
    for variant,complete,defects in [('first',67,62),('recovered',72,12)]:
        summary=json.loads((args.out/variant/'SUMMARY.json').read_text())
        assert summary['planned_trials']==12 and summary['planned_readers']==36
        assert summary['saved_stage_records']==72 and summary['not_recorded_stage_records']==0
        assert summary['complete_roster_stage_records']==complete
        assert summary['mechanical_defect_count']==defects
    print(f'{len(names)} saved analysis/handoff files reproduced; only generation timestamps excluded. Primary missingness and supplementary recoveries remain separate.')


if __name__=='__main__':
    main()
