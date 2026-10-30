import json
import sys
from pathlib import Path
import tempfile
import unittest
from replication.package_run import package_run
from scripts.restore_review_bundle import restore


class PackageTests(unittest.TestCase):
    def test_portable_export_preserves_scientific_values_and_omits_launch_header(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);run=root/'run';run.mkdir()
            (run/'REPRODUCTION.json').write_text('{"status":"complete"}')
            (run/'reproduce.json').write_text(json.dumps({'python':'/fixture/bin/python'}))
            outputs=run/'workflow';outputs.mkdir()
            (outputs/'metrics.json').write_text(json.dumps({'score':0.6128,'file':str(run/'model'),
                                                          'stdlib_file':str(Path(sys.base_prefix).resolve()/'lib')}))
            (outputs/'model.bin').write_bytes(bytes(range(256)))
            (outputs/'RUN_MODELS_stata18.log').write_text('private license header')
            result=package_run(run,root/'export')
            self.assertTrue(result['passed'])
            restore(root/'export/fresh-reproduction.manifest.json',root/'restored')
            data=json.loads((root/'restored/workflow/metrics.json').read_text())
            self.assertEqual(data,{'score':0.6128,'file':'REPRODUCTION_ROOT/model',
                                   'stdlib_file':'PYTHON_BASE_ENVIRONMENT/lib'})
            self.assertEqual((root/'restored/workflow/model.bin').read_bytes(),bytes(range(256)))
            self.assertFalse((root/'restored/workflow/RUN_MODELS_stata18.log').exists())
