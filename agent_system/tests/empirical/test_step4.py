"""Fast adapter checks; original-function checks use AI_MICROFOUNDATION_PROXY_PACKAGES_ROOT if supplied."""
import csv
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from agent_system.empirical import step4
from agent_system.empirical.model_inputs import prepare_fresh, check_fresh_estimates, _ids_hash

try:
    import numpy as np
    import pandas as pd
except ImportError:
    np = pd = None


class Step4ContractTests(unittest.TestCase):
    def test_source_context_restores_globals_on_failure(self):
        argv, paths, before = sys.argv[:], sys.path[:], dict(os.environ)
        with self.assertRaisesRegex(RuntimeError, "failure"):
            with step4._source_context():
                sys.argv = ["source"]
                sys.path.insert(0, "source")
                os.environ["FULLRAW_INPUT_ROOT"] = "changed"
                raise RuntimeError("failure")
        self.assertEqual(argv, sys.argv)
        self.assertEqual(paths, sys.path)
        self.assertEqual(before, dict(os.environ))

    def test_new_scores_are_set_only_on_local_module(self):
        local, official = SimpleNamespace(), SimpleNamespace()
        with step4._source_context(), patch.object(step4, "_load", side_effect=[local, official]), patch.object(step4, "_main") as main:
            step4._match(Path("/package"), Path("/run"), Path("/new/scores.parquet"))
            self.assertEqual(local.SCORE, Path("/new/scores.parquet"))
            self.assertFalse(hasattr(official, "SCORE"))
            self.assertEqual(main.call_count, 2)
            self.assertEqual(main.call_args_list[0].args[-1], Path("/run") / step4.REP / "data/matched/local")

    def test_missing_stata_keeps_prepared_artifacts(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            script = out / "regression/stata/RUN_MODELS.do"
            script.parent.mkdir(parents=True)
            script.write_text("version 19.0\n")
            (out / "CONNECTED_INPUTS.json").write_text('{"profile":"fresh"}')
            with patch.object(step4, "_package", return_value=Path("/package")):
                with self.assertRaises(step4.NeedsStataError) as error:
                    step4.estimate({"profile": "fresh"}, out)
            self.assertEqual(error.exception.artifacts["dofile"], str(script.resolve()))
            self.assertEqual(script.read_text(), "version 19.0\n")

    def test_run_prepares_before_stata_check(self):
        with patch.object(step4, "prepare") as prepare, patch.object(step4, "estimate", side_effect=step4.NeedsStataError("needed", {})):
            with self.assertRaises(step4.NeedsStataError):
                step4.run({}, Path("out"), Path("scores"), Path("panel"))
            prepare.assert_called_once_with({}, Path("out"), Path("scores"), Path("panel"))

    def test_cannot_prepare_inside_packages(self):
        with patch.object(step4, "_package", return_value=Path("/immutable/packages") / step4.PACKAGE):
            with self.assertRaisesRegex(ValueError, "immutable"):
                step4.prepare({}, Path("/immutable/packages/new"), Path("scores"), Path("panel"))

    @unittest.skipIf(pd is None, "pandas and numpy required")
    def test_identity_rejects_fold_drift_and_nonfinite_scores(self):
        original = pd.DataFrame({"panel_id": [0, 1], "gvkey": [1, 2], "ceo_id": ["a", "b"], "year": [2013, 2014], "fold": [0, 1]})
        scores = original.copy()
        for i in range(16):
            scores[f"risk_score_{i}"] = [0.1, 0.2]
        with patch.object(pd, "read_parquet", side_effect=[original, original.copy(), scores]):
            self.assertEqual(step4._check_identity(Path("pkg"), Path("scores"), Path("panel"))["rows"], 2)
        changed = original.copy()
        changed.loc[0, "fold"] = 4
        with patch.object(pd, "read_parquet", side_effect=[original, changed, scores]):
            with self.assertRaises(AssertionError):
                step4._check_identity(Path("pkg"), Path("scores"), Path("panel"))
        scores.loc[0, "risk_score_0"] = np.inf
        with patch.object(pd, "read_parquet", side_effect=[original, original, scores]):
            with self.assertRaisesRegex(ValueError, "finite"):
                step4._check_identity(Path("pkg"), Path("scores"), Path("panel"))


@unittest.skipUnless(pd is not None and os.environ.get("AI_MICROFOUNDATION_PROXY_PACKAGES_ROOT"), "Set AI_MICROFOUNDATION_PROXY_PACKAGES_ROOT for original-function tests")
class OriginalFunctionTests(unittest.TestCase):
    def test_fresh_estimates_allow_changed_coefficients_but_reject_bad_numerics(self):
        reference = Path(os.environ["AI_MICROFOUNDATION_PROXY_PACKAGES_ROOT"]) / step4.PACKAGE / "reference/regression"
        specs = json.loads((reference / "model_reference.json").read_text())["models"]
        with (reference / "model_summary.csv").open() as stream:
            summaries = {r["model_id"]: r for r in csv.DictReader(stream)}
        for spec in specs:
            spec["N_clusters"] = int(summaries[spec["model_id"]]["N_clusters"])
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "stata").mkdir()
            (root / "audit").mkdir()
            (root / "model_specifications.json").write_text(json.dumps({"models": specs}))
            (root / "stata/samples").symlink_to(reference / "samples", target_is_directory=True)
            shutil.copyfile(reference / "model_summary.csv", root / "stata/model_summary.csv")
            with (reference / "coefficients.csv").open() as stream:
                rows = list(csv.DictReader(stream))
            rows[0]["coef"] = str(float(rows[0]["coef"]) + 1)
            def write_coefficients():
                with (root / "stata/coefficients.csv").open("w") as stream:
                    writer = csv.DictWriter(stream, fieldnames=rows[0].keys())
                    writer.writeheader()
                    writer.writerows(rows)
            write_coefficients()
            check_fresh_estimates(root, reference)
            rows[0]["se_cluster"] = "nan"
            write_coefficients()
            with self.assertRaisesRegex(ValueError, "Nonfinite"):
                check_fresh_estimates(root, reference)

    def test_fresh_scores_change_scales_but_keep_original_25_formulas(self):
        package = Path(os.environ["AI_MICROFOUNDATION_PROXY_PACKAGES_ROOT"]) / step4.PACKAGE
        with step4._source_context():
            source = step4._load(package / "code/prepare_models.py")
            random = np.random.default_rng(42)
            n = 1800
            annual = pd.DataFrame({"event_id": [f"event{i}" for i in range(n)],
                "gvkey": [f"{i:06d}" for i in range(n)], "fyear": np.repeat(np.arange(2006, 2024), 100),
                "sic2": np.tile([10, 20], n // 2), "payer": np.tile([0, 0, 1, 1], n // 4),
                "sample_log": np.ones(n), "formula_version": "B_standard_finance"})
            for column in set(source.CONTROLS + sum(source.SETTINGS.values(), [])):
                annual[column] = random.normal(size=n)
            matched = annual.copy()
            matched["official_strict_period_match"] = True
            for model in ("ridge", "xgboost"):
                matched["vendor_strict_risk_score_" + model] = random.uniform(0.01, 0.2, n)
            cohorts, jobs = source.jobs_from_data(annual, matched)
            references = []
            for job in jobs:
                frame = cohorts[job["cohort"]].copy()
                if job["setting"] == "m09":
                    frame = frame.loc[frame.sample_log.eq(1)].copy()
                if job["score_model"]:
                    frame["rd_score"] = frame[job["score_column"]]
                used, _, _ = source.trim_pure_groups(frame)
                names, scales, bases = source.design(used, job["regressors"])
                references.append({**job, "N_input": len(frame), "N_used": len(used),
                    "base_sic2": bases["sic2"], "base_fyear": bases["fyear"],
                    "design_columns": names, "numerical_scales": scales.tolist(),
                    "used_ids_sha256": _ids_hash(used.event_id)})
            for model in ("ridge", "xgboost"):
                matched["vendor_strict_risk_score_" + model] *= 2
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                reference = root / "reference.json"
                reference.write_text(json.dumps({"models": references}))
                with patch.object(pd, "read_parquet", side_effect=[annual, matched]), patch.object(pd.DataFrame, "to_parquet"), patch.object(pd.DataFrame, "to_stata"), patch.object(source, "sha", return_value="test"):
                    prepare_fresh(source, "annual", "matched", root / "regression", reference)
                actual = json.loads((root / "regression/model_specifications.json").read_text())["models"]
                self.assertEqual(len(actual), 25)
                self.assertEqual(sum(bool(x["score_model"]) for x in actual), 16)
                for got, ref in zip(actual, references):
                    self.assertEqual(got["regressors"], ref["regressors"])
                    self.assertEqual(got["used_ids_sha256"], ref["used_ids_sha256"])
                    if got["score_model"]:
                        self.assertAlmostEqual(got["numerical_scales"][0], 2 * ref["numerical_scales"][0])
                dofile = (root / "regression/stata/RUN_MODELS.do").read_text()
                self.assertIn("version 19.0", dofile)
                self.assertNotIn("@@MODEL_BLOCKS@@", dofile)
                self.assertEqual(dofile.count("\ntable4fit\n"), 25)
                # Fresh mode must still reject sample drift.
                matched = matched.iloc[1:].copy()
                annual = annual.iloc[1:].copy()
                with patch.object(pd, "read_parquet", side_effect=[annual, matched]), patch.object(pd.DataFrame, "to_parquet"):
                    with self.assertRaisesRegex(ValueError, "sample"):
                        prepare_fresh(source, "annual", "matched", root / "changed", reference)


if __name__ == "__main__":
    unittest.main()
