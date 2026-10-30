"""Explicit external bindings replace historical workspace fallbacks."""

import json
import os
import subprocess
import tempfile
import unittest
import venv
from pathlib import Path
from unittest.mock import patch

from agent_system.empirical.config import load
from agent_system.empirical import screening


class ExternalInputTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.path = self.root / "config.json"
        for package in ("step3_risk_score_collaborator_20261027",
                        "step4_full_from_raw_20261027"):
            (self.root / "packages" / package / "data").mkdir(parents=True)

    def read(self, config):
        self.path.write_text(json.dumps(config))
        return load(self.path)

    def base(self):
        return {"profile": "reproduce", "python": "env/bin/python",
                "packages_root": "packages", "catalogue": "inputs/catalogue.json",
                "selection": "inputs/selection.json"}

    def test_reproduction_requires_explicit_catalogue_and_selection(self):
        for key in ("catalogue", "selection"):
            config = self.base()
            del config[key]
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, key):
                self.read(config)

    def test_external_paths_resolve_from_configuration_location(self):
        config = self.read(self.base())
        for key, relative in (("catalogue", "inputs/catalogue.json"),
                              ("selection", "inputs/selection.json"),
                              ("python", "env/bin/python")):
            self.assertEqual(config[key], str(self.root / relative))
        self.assertEqual(config["step3"]["topics"], str(
            self.root / "packages/step3_risk_score_collaborator_20261027/data/components/topic_distr.npz"))

    def test_fresh_requires_explicit_toolkit_and_packets(self):
        config = {**self.base(), "profile": "fresh"}
        for missing in ("toolkit", "packet_root"):
            config["step2"] = {k: "screening" for k in ("toolkit", "packet_root") if k != missing}
            with self.subTest(missing=missing), self.assertRaisesRegex(ValueError, missing):
                self.read(config)

    def test_configured_interpreter_keeps_virtual_environment(self):
        environment = self.root / "env"
        venv.EnvBuilder(with_pip=False, symlinks=os.name != "nt").create(environment)
        executable = environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        config = self.read({**self.base(), "python": str(executable)})
        prefix = subprocess.check_output([config["python"], "-c", "import sys; print(sys.prefix)"], text=True).strip()
        self.assertEqual(Path(prefix).resolve(), environment.resolve())

    def test_missing_screening_inputs_fail_before_toolkit_or_provider_load(self):
        with patch.object(screening, "_load_toolkit") as toolkit:
            for settings in ({}, {"toolkit": "absent.py"},
                             {"toolkit": "absent.py", "packet_root": "absent"}):
                with self.subTest(settings=settings), self.assertRaises(ValueError):
                    screening.run({"step2": settings}, self.root / "out", provider_factory=object())
            toolkit.assert_not_called()


if __name__ == "__main__":
    unittest.main()
