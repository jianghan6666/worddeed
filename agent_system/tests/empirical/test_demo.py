import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agent_system.empirical.demo import NOTICE, _rows, run_demo
from agent_system.empirical.workflow import sha


class DemoTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def test_demo_wires_selection_to_generated_scores_to_step4_input(self):
        with patch("agent_system.providers.ResponsesProvider.respond", side_effect=AssertionError("No API allowed")):
            summary = run_demo(self.root / "demo")
        self.assertEqual(summary["status"], "demonstration_complete")
        self.assertFalse(summary["scientific_completion"])
        self.assertFalse(summary["live_model_calls"])
        self.assertFalse(summary["training_executed"])
        self.assertFalse(summary["estimation_executed"])
        stages = summary["artifacts"]
        selection = Path(stages["step2"]["selection"])
        score = Path(stages["step3"]["scores"])
        prepared = Path(stages["step4_prepare"]["input"])
        lineage = json.loads(Path(stages["step3"]["lineage"]).read_text())
        self.assertEqual(lineage["selection_sha256"], sha(selection))
        self.assertEqual(lineage["selected_topic_ids"], ["T1", "T3"])
        self.assertEqual([float(row["demo_score"]) for row in _rows(score)], [0.7, 0.8])
        self.assertEqual(_rows(prepared), _rows(score))
        input_lineage = json.loads(Path(stages["step4_prepare"]["lineage"]).read_text())
        self.assertEqual(input_lineage["scores"], str(score))
        self.assertEqual(input_lineage["scores_sha256"], sha(score))
        receipt = json.loads(Path(stages["step4"]["receipt"]).read_text())
        self.assertEqual(receipt["input_sha256"], sha(prepared))
        self.assertEqual(receipt["estimation"], "not_run")
        state = json.loads((self.root / "demo/workflow/state.json").read_text())
        self.assertTrue(state["config"]["demonstration"])
        self.assertTrue(all(a["notice"] == NOTICE for a in stages.values()))

    def test_changing_fixture_selection_changes_scores_and_step4_input(self):
        first = run_demo(self.root / "first")
        second = run_demo(self.root / "second", selected_topic_ids=("T2",))
        first_scores = _rows(first["artifacts"]["step3"]["scores"])
        second_scores = _rows(second["artifacts"]["step3"]["scores"])
        self.assertNotEqual(first_scores, second_scores)
        self.assertEqual([float(row["demo_score"]) for row in second_scores], [0.3, 0.2])
        self.assertEqual(second_scores, _rows(second["artifacts"]["step4_prepare"]["input"]))

    def test_completed_resume_does_not_execute_workers_or_model(self):
        out = self.root / "demo"
        original = run_demo(out)
        checkpoint = out / "workflow/coordinator.json"
        before = checkpoint.read_bytes()
        with patch("agent_system.empirical.demo._fixture_worker", side_effect=AssertionError("No rerun")):
            resumed = run_demo(out, resume=True)
        self.assertEqual(resumed, original)
        self.assertEqual(checkpoint.read_bytes(), before)
        with self.assertRaises(FileExistsError):
            run_demo(out)

    def test_failed_and_interrupted_stages_resume_without_repeating_completed_stages(self):
        for failure in ("fail_stage", "interrupt_stage"):
            with self.subTest(failure=failure):
                out = self.root / failure
                summary = run_demo(out, **{failure: "step3"})
                self.assertEqual(summary["status"], "tool_failed" if failure == "fail_stage" else "interrupted")
                state_path = out / "workflow/state.json"
                failed = json.loads(state_path.read_text())
                self.assertEqual(failed["stages"]["step3"]["status"], "failed")
                self.assertEqual(failed["stages"]["step2"]["attempt"], 1)
                frozen = {stage: dict(failed["stages"][stage]["outputs"]) for stage in ("step1", "step2")}
                resumed = run_demo(out, resume=True)
                self.assertEqual(resumed["status"], "demonstration_complete")
                state = json.loads(state_path.read_text())
                for stage in ("step1", "step2"):
                    self.assertEqual(state["stages"][stage]["outputs"], frozen[stage])
                    self.assertEqual(state["stages"][stage]["attempt"], 1)
                self.assertEqual(state["stages"]["step3"]["attempt"], 2)
                self.assertEqual(len(list((out / "workflow").glob("step3.interrupted-*"))), 1)

    def test_resume_requires_demo_state_and_changed_input_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "configuration"):
            run_demo(self.root / "absent", resume=True)
        out = self.root / "demo"
        run_demo(out)
        (out / "fixture-inputs/selection.json").write_text("changed")
        with self.assertRaisesRegex(ValueError, "input changed"):
            run_demo(out, resume=True)


if __name__ == "__main__":
    unittest.main()
