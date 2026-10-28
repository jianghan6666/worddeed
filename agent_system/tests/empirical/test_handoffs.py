import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd

from agent_system.empirical import step1, worker
from agent_system.empirical.workflow import sha, write_json


class HandoffTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.catalogue = self.root / "catalogue.json"
        write_json(self.catalogue, {"topic_model_id": "test-model", "topics": [
            {"topic_id": str(i), "name": f"Fixture {i}", "keywords": ["fixture"]} for i in range(354)]})
        self.components, self.topics = self.root / "components.parquet", self.root / "topics.npz"
        pd.DataFrame({"orig_row": [0, 1]}).to_parquet(self.components)
        np.savez(self.topics, topic_distr=np.zeros((2, 354)))
        self.config = {"profile": "reproduce", "catalogue": str(self.catalogue),
                       "step3": {"components": str(self.components), "topics": str(self.topics)}}

    def test_saved_input_header_and_row_count(self):
        result = step1.run(self.config, self.root / "step1")
        self.assertEqual((result["rows"], result["n_topics"]), (2, 354))
        np.savez(self.topics, topic_distr=np.zeros((3, 354)))
        with self.assertRaisesRegex(ValueError, "align"):
            step1.run(self.config, self.root / "bad")

    def test_selection_is_bound_to_catalogue_before_copy(self):
        selection = self.root / "selection.json"
        write_json(selection, {"topic_model_id": "test-model", "catalogue_sha256": sha(self.catalogue),
                              "final": {"relevant": ["0"], "irrelevant": [str(i) for i in range(1, 354)], "unresolved": []}})
        config = {**self.config, "selection": str(selection)}
        out = self.root / "step2"
        out.mkdir()
        request = {"stage": "step2", "config": config, "out": str(out),
                   "artifacts": {"step1": {"catalogue": str(self.catalogue), "topic_model_id": "test-model"}}}
        self.assertEqual(Path(worker.execute(request)["selection"]).read_bytes(), selection.read_bytes())
        request["artifacts"]["step1"]["topic_model_id"] = "different"
        with self.assertRaisesRegex(ValueError, "different topic model"):
            worker.execute(request)

    def test_worker_passes_actual_stage_outputs(self):
        previous = {"step1": {"topics": "new-topics", "components": "components"},
                    "step2": {"selection": "new-selection"},
                    "step3": {"scores": "new-scores", "panel": "new-panel"}}
        request = {"stage": "step3", "config": copy.deepcopy(self.config), "out": str(self.root), "artifacts": previous}
        with patch("agent_system.empirical.step3.run", return_value={}) as fit:
            worker.execute(request)
            self.assertEqual(fit.call_args.args[0]["step3"]["topics"], "new-topics")
            self.assertEqual(fit.call_args.args[2], Path("new-selection"))
        request["stage"] = "step4_prepare"
        with patch("agent_system.empirical.step4.prepare", return_value={}) as prepare:
            worker.execute(request)
            self.assertEqual(prepare.call_args.args[2:], (Path("new-scores"), Path("new-panel")))


if __name__ == "__main__":
    unittest.main()
