import json
from pathlib import Path
import tempfile
import unittest
from replication.continue_stata import verify_handoff


class HandoffTests(unittest.TestCase):
    def test_failed_scientific_verification_cannot_continue(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'HANDOFF.json').write_text('{"passed":false}')
            with self.assertRaisesRegex(ValueError, 'must pass first'):
                verify_handoff(root, root / 'packages')

    def test_tampered_or_escaping_handoff_is_rejected_before_estimation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = {'passed': True, 'supplementary_passed': True,
                      'stage_status': {s: 'complete' for s in ['step1','step2','step3','step4_prepare']}}
            (root / 'score.bin').write_bytes(b'changed')
            for path, message in [('score.bin', 'member changed'), ('../score.bin', 'Unsafe')]:
                report['files'] = [{'path': path, 'bytes': 7, 'sha256': 'incorrect'}]
                (root / 'HANDOFF.json').write_text(json.dumps(report))
                with self.assertRaisesRegex(ValueError, message):
                    verify_handoff(root, root / 'packages')
