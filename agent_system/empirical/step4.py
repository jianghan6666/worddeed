"""Connect new Step 3 scores to the supplied, immutable full Step 4 pipeline.

``prepare`` stops after writing the 25 model inputs and original Stata do-file.
``run`` additionally estimates and validates; ``estimate`` resumes a prepared run.
Imported source stages use process globals, so calls must be serialized.
"""
from __future__ import annotations

from contextlib import contextmanager
import importlib.util
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

PACKAGE = "step4_full_from_raw_20261027"
REP = Path("project/replications/caliskan_doukas_2015")
KEYS = ["panel_id", "gvkey", "ceo_id", "year", "fold"]


class NeedsStataError(RuntimeError):
    """Preparation succeeded but estimation needs a compatible Stata runtime."""

    def __init__(self, message, artifacts):
        super().__init__(message)
        self.artifacts = artifacts


def _package(config):
    if config.get("profile", "reproduce") not in {"reproduce", "fresh"}:
        raise ValueError("profile must be reproduce or fresh")
    package = Path(config["packages_root"]).expanduser().resolve() / PACKAGE
    if not (package / "code/prepare_models.py").is_file():
        raise FileNotFoundError(f"Complete Step 4 package required: {package}")
    return package


@contextmanager
def _source_context():
    argv, paths, env = sys.argv[:], sys.path[:], os.environ.copy()
    bytecode = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        yield
    finally:
        sys.argv, sys.path = argv, paths
        sys.dont_write_bytecode = bytecode
        os.environ.clear()
        os.environ.update(env)


def _load(path):
    spec = importlib.util.spec_from_file_location("_connected_step4_" + path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _main(module, *args):
    saved = sys.argv
    try:
        sys.argv = [str(module.__file__), *map(str, args)]
        result = module.main()
        if result not in (None, 0):
            raise RuntimeError(f"{module.__file__} failed with status {result}")
    finally:
        sys.argv = saved


def _write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2), encoding="utf8")


def _check_identity(package, scores, panel):
    import numpy as np
    import pandas as pd

    original = pd.read_parquet(package / "project/data/panel/ceo_firm_year_panel.parquet", columns=KEYS)
    current = pd.read_parquet(panel, columns=KEYS)
    score = pd.read_parquet(scores)
    for name, frame in [("original", original), ("panel", current), ("scores", score)]:
        if frame[KEYS].isna().any().any() or not frame.panel_id.is_unique or frame.duplicated(["gvkey", "year"]).any():
            raise ValueError(f"{name}: missing or duplicate panel keys")
        # The supplied local matcher also requires original row order and dtypes.
        pd.testing.assert_frame_equal(frame[KEYS].reset_index(drop=True), original.reset_index(drop=True))
    columns = [c for c in score if c.startswith("risk_score_")]
    if len(columns) != 16 or not np.isfinite(score[columns].to_numpy(float)).all():
        raise ValueError("Expected 16 finite Step 3 score columns")
    return {"passed": True, "rows": len(current), "checked_keys": KEYS,
            "scores": str(scores), "panel": str(panel), "fixed_identity_sources": True}


def _match(package, out, scores):
    os.environ["FULLRAW_INPUT_ROOT"] = str(package / "project")
    os.environ["FULLRAW_OUTPUT_ROOT"] = str(out / "project")
    for label in ("local", "official"):
        module = _load(package / "code/matching" / f"{label}_match.py")
        if label == "local":
            module.SCORE = scores
        _main(module, "--out", out / REP / "data/matched" / label)


def _normalize_finance_audit_key(package, out):
    """Record a lossless native-integer width conversion after construction.

    NumPy's native integer width differs between the supplied Windows runtime
    and macOS. Only the regenerated audit key's storage type may change here;
    values are checked exactly before and after. The original verifier still
    checks every value, identity, sample flag and numerical tolerance.
    """
    import numpy as np
    import pandas as pd

    path = out / REP / "audits/ceo_selection_audit.parquet"
    reference = package / "reference/finance/ceo_selection_audit.parquet"
    actual, expected = pd.read_parquet(path), pd.read_parquet(reference)
    key = "anncomp_row_id"
    source, target = actual[key].dtype, expected[key].dtype
    if source == target:
        return
    if not (pd.api.types.is_integer_dtype(source) and pd.api.types.is_integer_dtype(target)):
        raise ValueError("Audit key normalization only supports integer storage widths")
    pd.testing.assert_series_equal(actual[key].sort_values().reset_index(drop=True),
                                   expected[key].sort_values().reset_index(drop=True),
                                   check_dtype=False, check_exact=True)
    limits = np.iinfo(target)
    if actual[key].isna().any() or not actual[key].between(limits.min, limits.max).all():
        raise ValueError("Audit key conversion would lose information")
    converted = actual.copy()
    converted[key] = actual[key].astype(target)
    pd.testing.assert_frame_equal(actual, converted, check_dtype=False, check_exact=True)
    original_hash = hashlib.sha256(path.read_bytes()).hexdigest()
    converted.to_parquet(path, index=False)
    pd.testing.assert_frame_equal(pd.read_parquet(path), converted, check_exact=True)
    _write(out / REP / "audits/INTEGER_STORAGE_COMPATIBILITY.json", {
        "file": str(path.relative_to(out)), "column": key,
        "from": str(source), "to": str(target), "rows": len(actual),
        "all_values_exactly_preserved": True, "reference_values_copied": False,
        "before_sha256": original_hash,
        "after_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "supplied_verifier_unchanged": True})


def _check_fresh_matching(package, out):
    """Keep every frozen identity/sample check; allow only score values to vary."""
    import pandas as pd

    base, ref = out / REP / "data/matched", package / "reference/matching"
    pairs = [
        ("local/audit/source_score_identity.parquet", "source_score_identity_local.parquet", "score_panel_id"),
        ("official/audit/source_official_identity.parquet", "source_official_identity.parquet", "score_panel_id"),
        ("official/master_with_rd_scores.parquet", "master_with_rd_scores.parquet", "event_id"),
        ("official/annual/table4_b_extended_2006_2023_rd_scores.parquet", "table4_b_extended_2006_2023_rd_scores.parquet", "event_id"),
    ]
    checks = []
    for actual, expected, key in pairs:
        got, frozen = pd.read_parquet(base / actual), pd.read_parquet(ref / expected)
        if not got[key].is_unique or not frozen[key].is_unique or set(got[key]) != set(frozen[key]):
            raise ValueError(f"Matching IDs changed: {actual}")
        if not set(frozen).issubset(got):
            raise ValueError(f"Matching schema changed: {actual}")
        got = got.set_index(key).loc[frozen[key]].reset_index()
        columns = [c for c in frozen if "risk_score_" not in c]
        pd.testing.assert_frame_equal(got[columns], frozen[columns].reset_index(drop=True),
                                      check_dtype=False, check_exact=False, rtol=1e-11, atol=1e-11)
        # The source matchers separately assert exact transfer of all new scores,
        # all original finance columns, match guards and protected file hashes.
        checks.append({"table": actual, "rows": len(got), "identity_columns_checked": len(columns)})
    _write(out / "matching_reproduction_check.json", {"passed": True, "profile": "fresh",
           "frozen_score_equality_checked": False, "checks": checks})


def artifacts(out):
    out = Path(out).resolve()
    paths = {
        "annual_b": out / REP / "data/processed/table4_b_extended_2006_2023.parquet",
        "matched": out / REP / "data/matched/official/annual/table4_b_extended_2006_2023_rd_scores.parquet",
        "model_inputs": out / "regression/stata/inputs",
        "prepared_data": out / "regression/stata/inputs",
        "model_specifications": out / "regression/model_specifications.json",
        "dofile": out / "regression/stata/RUN_MODELS.do",
        "stata18_dofile": out / "regression/stata/RUN_MODELS_stata18.do",
        "stata_compatibility": out / "regression/audit/STATA_COMPATIBILITY.json",
        "regression_results": out / "regression/stata/coefficients.csv",
        "model_summary": out / "regression/stata/model_summary.csv",
        "local_match_report": out / REP / "data/matched/local/MATCH_REPORT.md",
        "official_match_report": out / REP / "data/matched/official/MATCH_REPORT.md",
        "tables_html": out / "regression/tables/REPLAYED_TABLES.html",
        "tables_markdown": out / "regression/tables/REPLAYED_TABLES.md",
    }
    return {**{key: str(path) for key, path in paths.items() if path.exists()},
            "reports": [str(p) for p in sorted(out.rglob("*.json"))
                        if "QA" in p.name or "check" in p.name.lower() or p.name == "CONNECTED_INPUTS.json"]}


def prepare(config: dict, out: Path, scores: Path, panel: Path) -> dict:
    """Rebuild finance, match supplied scores, and prepare all 25 Stata models."""
    package, out = _package(config), Path(out).resolve()
    scores, panel = Path(scores).resolve(), Path(panel).resolve()
    if out == package.parent or package.parent in out.parents or out in package.parents:
        raise ValueError("Output must be outside the immutable packages tree")
    if out.exists() and any(out.iterdir()):
        raise FileExistsError(f"Step 4 preparation requires a fresh output directory: {out}")
    with _source_context():
        identity = _check_identity(package, scores, panel)
        _write(out / "CONNECTED_INPUTS.json", {**identity, "profile": config.get("profile", "reproduce")})
        _load(package / "code/finance_stage.py").run_finance(package, out)
        _normalize_finance_audit_key(package, out)
        finance = _load(package / "code/verify_finance.py").verify_finance(package, out)
        if finance["status"] != "passed":
            raise ValueError("Financial reconstruction failed its source checks")
        _match(package, out, scores)
        profile = config.get("profile", "reproduce")
        if profile == "reproduce":
            _main(_load(package / "code/verify_matching.py"), "--package-root", package, "--run-root", out)
        else:
            _check_fresh_matching(package, out)
        annual = out / REP / "data/processed/table4_b_extended_2006_2023.parquet"
        matched = out / REP / "data/matched/official/annual/table4_b_extended_2006_2023_rd_scores.parquet"
        original = _load(package / "code/prepare_models.py")
        reference = package / "reference/regression/model_reference.json"
        if profile == "reproduce":
            _main(original, "--annual-b", annual, "--matched", matched, "--output", out / "regression", "--reference", reference)
        else:
            from .model_inputs import prepare_fresh
            prepare_fresh(original, annual, matched, out / "regression", reference)
    return {"status": "prepared", "profile": profile, **artifacts(out)}


def estimate(config: dict, out: Path) -> dict:
    """Estimate a preparation; an explicit version-18 compatibility run is recorded."""
    package, out = _package(config), Path(out).resolve()
    available = artifacts(out)
    script = out / "regression/stata/RUN_MODELS.do"
    if not script.is_file():
        raise FileNotFoundError("Run Step 4 prepare first")
    prepared = json.loads((out / "CONNECTED_INPUTS.json").read_text())
    if prepared["profile"] != config.get("profile", "reproduce"):
        raise ValueError("Estimation profile differs from prepared inputs")
    value = config.get("stata_exe")
    executable = (shutil.which(str(value)) or str(Path(value).expanduser())) if value else None
    if not executable or not Path(executable).is_file():
        raise NeedsStataError("Step 4 inputs are prepared. Set stata_exe to a compatible Stata executable. Delivered results used Stata 19.5; version 18 requires explicit stata_version=18.", available)
    version = config.get("stata_version", 19)
    if version not in (18, 19):
        raise ValueError("stata_version must be 18 or 19")
    executed = script
    if version == 18:
        original = script.read_text()
        if original.count("version 19.0\n") != 1:
            raise ValueError("Expected exactly one original Stata version declaration")
        executed = script.with_name("RUN_MODELS_stata18.do")
        executed.write_text(original.replace("version 19.0\n", "version 18.0\n", 1))
        _write(out / "regression/audit/STATA_COMPATIBILITY.json", {
            "requested_version": 18, "delivered_runtime": "19.5",
            "only_change": "version 19.0 -> version 18.0 in a separate generated do-file",
            "original_sha256": hashlib.sha256(script.read_bytes()).hexdigest(),
            "executed_sha256": hashlib.sha256(executed.read_bytes()).hexdigest(),
            "acceptance": "Unchanged supplied coefficient, SE, sample, fit and presentation checks must pass."})
    # Remove only the completion marker so failed reruns cannot pass on stale output.
    (script.parent / "run_finished.txt").unlink(missing_ok=True)
    command = [executable, "/e" if os.name == "nt" else "-b", "do", executed.name]
    with (script.parent / "launcher.log").open("w") as log:
        result = subprocess.run(command, cwd=script.parent, stdout=log, stderr=subprocess.STDOUT)
    if result.returncode or not (script.parent / "run_finished.txt").is_file():
        raise NeedsStataError("Stata estimation did not complete. Inspect regression/stata/launcher.log and regression.log; delivered results used Stata 19.5.", artifacts(out))
    with _source_context():
        reg, ref = out / "regression", package / "reference/regression"
        if config.get("profile", "reproduce") == "reproduce":
            _main(_load(package / "code/check_models.py"), "--reference", ref, "--generated", reg)
        else:
            from .model_inputs import check_fresh_estimates
            check_fresh_estimates(reg, ref)
        _main(_load(package / "code/render_replayed_tables.py"), "--generated", reg)
        args = ["--workbook", package / "results/table4_annual_b_tables.xlsx", "--payload", ref / "table_payload.json", "--output", out / "qa/PRESENTATION_QA.json"]
        if config.get("profile", "reproduce") == "reproduce":
            args += ["--generated", reg]
        _main(_load(package / "code/check_presentation.py"), *args)
    return {"status": "passed", "profile": config.get("profile", "reproduce"), **artifacts(out)}


def run(config: dict, out: Path, scores: Path, panel: Path) -> dict:
    prepare(config, out, scores, panel)
    return estimate(config, out)
