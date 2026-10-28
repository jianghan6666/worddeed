"""Fast adapter/handoff tests: synthetic panels, no model fitting or raw data read."""

import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from agent_system.empirical import step3

try:
    import numpy as np
    import pandas as pd
except ImportError:
    np = pd = None


class SelectionTests(unittest.TestCase):
    def test_delivered_schema_and_plain_list(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "selection.json"
            for data in ([3, "0", 353], {"final": {"relevant": ["353", "0", "3"]}}):
                path.write_text(json.dumps(data))
                self.assertEqual(step3._selection(path), [0, 3, 353])

    def test_malformed_duplicate_and_unknown_topics_rejected(self):
        cases = [{}, {"final": []}, {"final": {"relevant": "1"}}, [], [True], [1.5],
                 ["1.0"], [None], ["-1"], [354], [1, "1"], ["topic_001"]]
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "selection.json"
            for data in cases:
                with self.subTest(data=data):
                    path.write_text(json.dumps(data))
                    with self.assertRaises(ValueError):
                        step3._selection(path)


@unittest.skipIf(pd is None, "analysis Python requires numpy/pandas")
class Step3Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.packages = self.root / "packages"
        self.package = self.packages / step3.PACKAGE
        self.out = self.root / "new-run"
        self.selection = self.root / "selected_topics.json"
        self.selection.write_text(json.dumps({"final": {"relevant": ["0", "3"]}}))
        for relative in [step3.SELECTION, "code/step3_lib.py", "code/02_train_and_score.py",
                         "data/components/components.parquet", "data/components/topic_distr.npz",
                         "data/compustat/compustat_panel_firms.csv"]:
            path = self.package / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(self.selection.read_text() if relative == step3.SELECTION else "fixture")
        self.config = {"packages_root": str(self.packages), "profile": "fresh"}
        self.panel = pd.DataFrame({"panel_id": range(10), "gvkey": range(10),
                                   "year": [2020] * 10, "ceo_id": [f"ceo_{i}" for i in range(10)],
                                   "split_group": range(10), "fold": [i % 5 for i in range(10)],
                                   "rd_at_fill0": [float(i) / 100 for i in range(10)],
                                   "sent_transformer": [0.2] * 10,
                                   "topic_000": [0.4] * 10, "topic_003": [0.6] * 10})
        self.panel.loc[0, "rd_at_fill0"] = np.nan
        self.frames = {str(self.package / "data/firm_year_inputs.parquet"): self.panel.copy(),
                       str(self.package / "results/risk_scores.parquet"): self.make_scores()}
        self.lib = SimpleNamespace(TARGET="rd_at_fill0", SENTIMENT="sent_transformer",
                                   load_topic_selection=lambda path: [f"topic_{i:03d}" for i in step3._selection(path)],
                                   build_inputs=lambda *args: self.panel.copy())
        self.trainer = SimpleNamespace(SELECTION=None, main=self.train_fixture)
        self.loaded = patch.object(step3, "_load_modules", return_value=(self.lib, self.trainer)).start()
        self.addCleanup(patch.stopall)

        def write(frame, path, **kwargs):
            self.frames[str(path)] = frame.copy()
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            Path(path).touch()

        patch.object(pd.DataFrame, "to_parquet", write).start()
        patch.object(pd, "read_parquet", side_effect=lambda path: self.frames[str(path)].copy()).start()

    def make_scores(self):
        scores = self.panel[step3.KEYS].copy()
        for model in step3.MODELS:
            for full in ("", "_full"):
                for version in step3.VERSIONS:
                    scores[f"risk_score_{model}{full}{version}"] = np.arange(10) / 10 + (0.01 if full else 0)
        return scores

    def train_fixture(self):
        self.assertEqual(self.trainer.SELECTION, self.selection.resolve())
        self.assertEqual(sys.argv[1:3], ["--models", "ridge"])
        self.assertIn("xgboost", sys.argv)
        self.assertEqual(Path(sys.argv[sys.argv.index("--inputs") + 1]), self.out / "firm_year_inputs.parquet")
        self.assertEqual(Path(sys.argv[-1]), self.out)
        scores = self.make_scores()
        scores.to_parquet(self.out / "results/risk_scores.parquet", index=False)
        metrics = {"target": self.lib.TARGET, "n_firm_years": 10, "n_labeled": 9,
                   "n_topics": len(step3._selection(self.selection)), "models": {}}
        for model in step3.MODELS:
            folds = {}
            for k in range(5):
                train = self.panel[(self.panel.fold != k) & self.panel[self.lib.TARGET].notna()]
                folds[str(k)] = {"scores_fold": k, "train_folds": sorted(train.fold.unique().tolist()),
                                 "n_train": len(train), "n_scored": int((self.panel.fold == k).sum())}
            metrics["models"][model] = {"folds": folds}
            for stem in [f"fold_{k}" for k in range(5)] + ["full"]:
                for suffix in [".joblib", ".json"] + ([".booster.json"] if model == "xgboost" else []):
                    path = self.out / "models" / model / (stem + suffix)
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text("mock fitted model")
        (self.out / "results/metrics.json").write_text(json.dumps(metrics))

    def test_run_builds_from_explicit_paths_and_returns_new_artifacts(self):
        with patch.object(self.lib, "build_inputs", return_value=self.panel.copy()) as build:
            old_argv = sys.argv
            result = step3.run(self.config, self.out, self.selection)
            self.assertIs(sys.argv, old_argv)
        build.assert_called_once_with(self.package / "data/components/components.parquet",
                                      self.package / "data/components/topic_distr.npz",
                                      self.package / "data/compustat/compustat_panel_firms.csv")
        self.assertEqual(set(result), {"panel", "scores", "metrics", "models"})
        json.dumps(result)
        self.assertEqual(result["scores"], str(self.out / "results/risk_scores.parquet"))
        self.assertTrue(all(Path(result[k]).is_file() for k in ("panel", "scores", "metrics")))
        self.assertEqual(json.loads(Path(result["metrics"]).read_text())["adapter_validation"]["profile"], "fresh")

    def test_overrides_and_changed_selection_allowed_in_fresh(self):
        self.selection.write_text("[3]")
        overrides = {}
        for name in ("components", "topics", "compustat"):
            path = self.root / name
            path.touch()
            overrides[name] = str(path)
        self.config["step3"] = overrides
        with patch.object(self.lib, "build_inputs", return_value=self.panel.copy()) as build:
            step3.run(self.config, self.out, self.selection)
        self.assertEqual(build.call_args.args, tuple(Path(overrides[n]) for n in ("components", "topics", "compustat")))

    def test_reproduce_records_maxima_and_exact_folds(self):
        self.config["profile"] = "reproduce"
        # Reference ordering does not affect key-based comparison.
        self.frames[str(self.package / "results/risk_scores.parquet")] = self.make_scores().iloc[::-1]
        result = step3.run(self.config, self.out, self.selection)
        report = json.loads(Path(result["metrics"]).read_text())["adapter_validation"]["reproduction"]
        self.assertTrue(report["passed"])
        self.assertTrue(report["folds_exact"])
        self.assertEqual(report["columns"]["risk_score_ridge"]["max_abs"], 0)

    def test_reproduce_rejects_changed_selection_before_build(self):
        self.config["profile"] = "reproduce"
        self.selection.write_text("[3]")
        with self.assertRaisesRegex(ValueError, "delivered selected topics"):
            step3.run(self.config, self.out, self.selection)
        self.loaded.assert_not_called()

    def test_reproduce_rejects_fold_change_before_training(self):
        self.config["profile"] = "reproduce"
        self.frames[str(self.package / "data/firm_year_inputs.parquet")].loc[0, "fold"] = 1
        with patch.object(self.trainer, "main") as train, self.assertRaisesRegex(ValueError, "fold assignment"):
            step3.run(self.config, self.out, self.selection)
        train.assert_not_called()

    def test_reproduce_failure_leaves_numeric_maxima_in_metrics(self):
        self.config["profile"] = "reproduce"
        self.frames[str(self.package / "results/risk_scores.parquet")].loc[0, "risk_score_ridge"] = 0.2
        with self.assertRaisesRegex(ValueError, "exceeds numerical tolerance"):
            step3.run(self.config, self.out, self.selection)
        report = json.loads((self.out / "results/metrics.json").read_text())["adapter_validation"]["reproduction"]
        self.assertFalse(report["passed"])
        self.assertAlmostEqual(report["columns"]["risk_score_ridge"]["max_abs"], 0.2)

    def test_tolerance_accepts_numerical_noise_but_not_material_change(self):
        scores, reference = self.make_scores(), self.make_scores()
        scores.loc[0, "risk_score_xgboost"] += 1e-7
        self.assertTrue(step3._compare_scores(scores, reference)["passed"])
        scores.loc[0, "risk_score_xgboost"] += 0.01
        self.assertFalse(step3._compare_scores(scores, reference)["passed"])

    def test_invalid_panel_keys_coverage_and_group_leakage(self):
        for case in ("duplicate", "null", "missing_fold", "leakage", "unknown_feature"):
            with self.subTest(case=case):
                panel = self.panel.copy()
                if case == "duplicate":
                    panel.loc[1, "panel_id"] = 0
                elif case == "null":
                    panel.loc[1, "ceo_id"] = None
                elif case == "missing_fold":
                    panel.loc[panel.fold == 4, "fold"] = 3
                elif case == "leakage":
                    panel.loc[1, "ceo_id"] = panel.loc[0, "ceo_id"]
                else:
                    panel = panel.drop(columns="topic_003")
                with self.assertRaises(ValueError):
                    step3._validate_panel(panel, ["topic_000", "topic_003"], self.lib)
        with self.assertRaisesRegex(ValueError, "row keys"):
            step3._coverage(self.make_scores().iloc[:-1], self.panel, "scores")

    def test_output_nonfinite_oof_leakage_and_missing_model_rejected(self):
        step3.run(self.config, self.out, self.selection)
        metrics = json.loads((self.out / "results/metrics.json").read_text())
        scores = self.make_scores()
        scores.loc[0, "risk_score_ridge"] = np.inf
        with self.assertRaisesRegex(ValueError, "nonfinite"):
            step3._validate_outputs(self.panel, scores, metrics, self.out, self.lib)
        metrics["models"]["ridge"]["folds"]["0"]["train_folds"].append(0)
        with self.assertRaisesRegex(ValueError, "OOF training/scoring"):
            step3._validate_outputs(self.panel, self.make_scores(), metrics, self.out, self.lib)
        metrics = json.loads((self.out / "results/metrics.json").read_text())
        (self.out / "models/xgboost/full.joblib").unlink()
        with self.assertRaisesRegex(ValueError, "newly fitted model"):
            step3._validate_outputs(self.panel, self.make_scores(), metrics, self.out, self.lib)

    def test_existing_output_and_package_destination_rejected(self):
        self.out.mkdir()
        (self.out / "results").mkdir()
        with self.assertRaises(FileExistsError):
            step3.run(self.config, self.out, self.selection)
        with self.assertRaisesRegex(ValueError, "separate"):
            step3.run(self.config, self.package / "rerun", self.selection)

    def test_trainer_failure_restores_argv_and_never_returns_stale_scores(self):
        old_argv = sys.argv
        with patch.object(self.trainer, "main", side_effect=RuntimeError("fixture fitting failure")):
            with self.assertRaisesRegex(RuntimeError, "fitting failure"):
                step3.run(self.config, self.out, self.selection)
        self.assertIs(sys.argv, old_argv)


if __name__ == "__main__":
    unittest.main()
