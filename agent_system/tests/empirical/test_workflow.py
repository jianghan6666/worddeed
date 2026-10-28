import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agent_system.empirical.workflow import Workflow, write_json


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.packages = self.root / "packages"
        for name, inventory in (("step3_risk_score_collaborator_20261027", "MANIFEST.json"),
                                ("step4_full_from_raw_20261027", "manifest.json")):
            write_json(self.packages / name / inventory, {})
        self.input = self.root / "input.txt"
        self.input.write_text("fixed")
        self.config = {"packages_root": str(self.packages), "profile": "reproduce", "python": "/unused",
                       "selection": str(self.input)}
        self.out = self.root / "run"

    def adapter(self, command, **kwargs):
        request = json.loads(Path(command[-2]).read_text())
        artifact = Path(request["out"]) / "artifact.txt"
        artifact.write_text(request["stage"])
        write_json(command[-1], {"artifact": str(artifact)})

    def test_resume_skips_completed_and_rejects_changed_output(self):
        with patch("agent_system.empirical.workflow.subprocess.run", side_effect=self.adapter) as run:
            workflow = Workflow(self.config, self.out)
            workflow.execute("step2")
            self.assertEqual(run.call_count, 2)
            resumed = Workflow(self.config, self.out)
            resumed.execute("step2")
            self.assertEqual(run.call_count, 2)
            (self.out / "step1/artifact.txt").write_text("changed")
            with self.assertRaisesRegex(ValueError, "output changed"):
                resumed.execute("step3")

    def test_changed_input_and_out_of_order_rejected(self):
        workflow = Workflow(self.config, self.out)
        with self.assertRaisesRegex(ValueError, "before step3"):
            workflow.run_stage("step3")
        self.input.write_text("other")
        with self.assertRaisesRegex(ValueError, "input changed"):
            Workflow(self.config, self.out)

    def test_failure_is_persisted_and_retry_preserves_first_attempt(self):
        with patch("agent_system.empirical.workflow.subprocess.run", side_effect=self.adapter):
            workflow = Workflow(self.config, self.out)
            workflow.execute("step2")
        with patch("agent_system.empirical.workflow.subprocess.run", side_effect=RuntimeError("interrupted")):
            with self.assertRaisesRegex(RuntimeError, "interrupted"):
                workflow.execute("step3")
        self.assertEqual(json.loads((self.out / "state.json").read_text())["status"], "failed")
        with patch("agent_system.empirical.workflow.subprocess.run", side_effect=self.adapter):
            Workflow(self.config, self.out).execute("step3")
        self.assertEqual(len(list(self.out.glob("step3.interrupted-*"))), 1)

    def test_frozen_package_output_rejected(self):
        with self.assertRaisesRegex(ValueError, "frozen packages"):
            Workflow(self.config, self.packages / "run")

    def test_stata_can_be_configured_after_preparation(self):
        with patch("agent_system.empirical.workflow.subprocess.run", side_effect=self.adapter) as run:
            Workflow(self.config, self.out).execute("step4_prepare")
            updated = {**self.config, "stata_exe": str(self.root / "later-stata")}
            Workflow(updated, self.out).execute()
            self.assertEqual(run.call_count, 5)
            with self.assertRaisesRegex(ValueError, "configuration changed"):
                Workflow({**updated, "stata_exe": "different"}, self.out)


if __name__ == "__main__":
    unittest.main()
