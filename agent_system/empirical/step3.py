"""Thin adapter for the delivered Step 3 code; run in the pinned analysis Python.

``run(config, out, selection)`` rebuilds inputs and fits both delivered models.
Paths in ``config['step3']`` (components/topics/compustat) override package data.
Reproduce compares against delivered results; fresh permits a changed selection.
The return value contains JSON-serializable artifact paths. The unsuffixed scores
are OOF predictions; ``_full`` columns are in-sample/inference-model predictions.
"""

import importlib.util
import json
import sys
from pathlib import Path


PACKAGE = "step3_risk_score_collaborator_20261027"
SELECTION = "data/topic_selection/b1-gpt-6-astra-P0-xhigh.json"
KEYS = ["panel_id", "gvkey", "ceo_id", "year", "fold"]
MODELS = ("ridge", "xgboost")
VERSIONS = ("", "_clip0", "_pct", "_z")


def _selection(path):
    """Validate the delivered list or final.relevant schema without coercion loss."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(data, dict):
        final = data.get("final")
        if not isinstance(final, dict) or "relevant" not in final:
            raise ValueError("Step 3 selection requires final.relevant")
        data = final["relevant"]
    if not isinstance(data, list) or not data:
        raise ValueError("Step 3 selected topics must be a nonempty list")
    ids = []
    for value in data:
        if type(value) is int:
            topic = value
        elif isinstance(value, str) and value.isascii() and value.isdecimal():
            topic = int(value)
        else:
            raise ValueError(f"Invalid selected topic ID: {value!r}")
        if not 0 <= topic < 354:
            raise ValueError(f"Unknown selected topic ID: {topic}; expected 0..353")
        ids.append(topic)
    if len(set(ids)) != len(ids):
        raise ValueError("Duplicate selected topic IDs")
    return sorted(ids)


def _load_modules(package):
    # Keep the canonical module name importable for supplied joblib files and
    # joblib workers. Never bind it to a different package in the same process.
    code = package / "code"
    lib_path = code / "step3_lib.py"
    lib = sys.modules.get("step3_lib")
    if lib is not None and Path(lib.__file__).resolve() != lib_path.resolve():
        raise ValueError("step3_lib already loaded from another package; use a fresh analysis process")
    if str(code) not in sys.path:
        sys.path.insert(0, str(code))
    if lib is None:
        spec = importlib.util.spec_from_file_location("step3_lib", lib_path)
        lib = importlib.util.module_from_spec(spec)
        sys.modules["step3_lib"] = lib
        try:
            spec.loader.exec_module(lib)
        except BaseException:
            sys.modules.pop("step3_lib", None)
            raise
    spec = importlib.util.spec_from_file_location("_connected_step3_train", code / "02_train_and_score.py")
    trainer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(trainer)
    return lib, trainer


def _keys(frame, label):
    missing = set(KEYS) - set(frame.columns)
    if missing:
        raise ValueError(f"{label}: missing keys {sorted(missing)}")
    if frame.empty or frame[KEYS].isna().any().any():
        raise ValueError(f"{label}: empty rows or null keys")
    if frame.panel_id.duplicated().any() or frame.duplicated(["gvkey", "year"]).any():
        raise ValueError(f"{label}: duplicate panel_id or firm-year keys")
    if set(frame.fold) != set(range(5)):
        raise ValueError(f"{label}: expected exactly folds 0..4")


def _coverage(actual, expected, label):
    _keys(actual, label)
    _keys(expected, "expected panel")
    left = actual.sort_values("panel_id")[KEYS].reset_index(drop=True)
    right = expected.sort_values("panel_id")[KEYS].reset_index(drop=True)
    if len(left) != len(right) or not left.eq(right).all().all():
        raise ValueError(f"{label}: row keys or fold assignment differ from expected panel")


def _validate_panel(panel, topic_cols, lib):
    _keys(panel, "built panel")
    missing = set(topic_cols + [lib.TARGET, lib.SENTIMENT, "split_group"]) - set(panel.columns)
    if missing:
        raise ValueError(f"Built panel is missing features/target: {sorted(missing)}")
    for group in ("gvkey", "ceo_id", "split_group"):
        if panel[group].isna().any() or panel.groupby(group).fold.nunique().max() != 1:
            raise ValueError(f"Built panel leaks {group} across folds")
    if not panel[lib.TARGET].notna().any():
        raise ValueError("Built panel has no labeled R&D observations")


def _validate_outputs(panel, scores, metrics, out, lib):
    import numpy as np

    _coverage(scores, panel, "generated scores")
    columns = [f"risk_score_{m}{f}{v}" for m in MODELS for f in ("", "_full") for v in VERSIONS]
    if set(scores.columns) != set(KEYS + columns):
        raise ValueError("Generated scores must contain both models, OOF/full and all four versions")
    if not np.isfinite(scores[columns].to_numpy(dtype=float)).all():
        raise ValueError("Generated scores contain nonfinite predictions")
    labeled = panel[lib.TARGET].notna()
    if (metrics.get("target") != lib.TARGET or metrics.get("n_firm_years") != len(panel)
            or metrics.get("n_labeled") != int(labeled.sum())):
        raise ValueError("Generated metrics do not cover the built panel/target")
    for model in MODELS:
        folds = metrics.get("models", {}).get(model, {}).get("folds", {})
        if set(folds) != {str(k) for k in range(5)}:
            raise ValueError(f"{model}: missing OOF fold records")
        for k in range(5):
            info = folds[str(k)]
            train = panel[(panel.fold != k) & labeled]
            if (info.get("scores_fold") != k or info.get("train_folds") != sorted(train.fold.unique().tolist())
                    or info.get("n_train") != len(train) or info.get("n_scored") != int((panel.fold == k).sum())):
                raise ValueError(f"{model} fold {k}: invalid OOF training/scoring coverage")
        for stem in [f"fold_{k}" for k in range(5)] + ["full"]:
            suffixes = [".joblib", ".json"] + ([".booster.json"] if model == "xgboost" else [])
            for suffix in suffixes:
                if not (out / "models" / model / (stem + suffix)).is_file():
                    raise ValueError(f"Missing newly fitted model artifact: {model}/{stem}{suffix}")


def _compare_scores(scores, reference):
    import numpy as np

    _coverage(scores, reference, "reproduced scores")
    if set(scores.columns) != set(reference.columns):
        raise ValueError("Reproduced score columns differ from delivered scores")
    new = scores.sort_values("panel_id")
    old = reference.sort_values("panel_id")
    report = {"folds_exact": True, "columns": {}, "passed": True}
    for col in [c for c in scores if c.startswith("risk_score_")]:
        a, b = new[col].to_numpy(dtype=float), old[col].to_numpy(dtype=float)
        # Float64 Ridge/float32 XGB, same pinned versions on different BLAS/CPU.
        # Percentile ranks may move by one row when numerical ties separate.
        atol = 1 / len(new) + 1e-8 if col.endswith("_pct") else (1e-5 if col.endswith("_z") else 1e-6)
        rtol = 0.0 if col.endswith("_pct") else 1e-5
        delta = np.abs(a - b)
        passed = bool(np.isfinite(b).all() and np.allclose(a, b, atol=atol, rtol=rtol))
        report["columns"][col] = {"atol": atol, "rtol": rtol, "max_abs": float(delta.max()),
                                   "max_rel": float((delta / np.maximum(np.abs(b), 1e-12)).max()), "passed": passed}
        report["passed"] &= passed
    return report


def run(config: dict, out: Path, selection: Path) -> dict:
    """Build and train freshly; raise ValueError on an invalid handoff/reproduction.

    Output must be outside packages_root and have no prior panel/results/models.
    Uses process-global imports/argv during the supplied script call: run serially
    in the dedicated pinned analysis process, not concurrent Python threads.
    """
    import pandas as pd

    packages = Path(config["packages_root"]).expanduser().resolve()
    package = packages / PACKAGE
    out, selection = Path(out).resolve(), Path(selection).resolve()
    profile = config.get("profile", "fresh")
    if profile not in ("fresh", "reproduce"):
        raise ValueError("Step 3 profile must be fresh or reproduce")
    if out == packages or packages in out.parents or out in packages.parents:
        raise ValueError("Step 3 output must be separate from supplied packages")
    ids = _selection(selection)
    if profile == "reproduce" and ids != _selection(package / SELECTION):
        raise ValueError("Reproduce requires the delivered selected topics; use fresh for changed selections")
    overrides = config.get("step3", {})
    defaults = {"components": "data/components/components.parquet", "topics": "data/components/topic_distr.npz",
                "compustat": "data/compustat/compustat_panel_firms.csv"}
    paths = {name: Path(overrides.get(name, package / relative)).expanduser().resolve()
             for name, relative in defaults.items()}
    for path in [selection, package / "code/step3_lib.py", package / "code/02_train_and_score.py", *paths.values()]:
        if not path.is_file():
            raise FileNotFoundError(f"Step 3 input is missing: {path}")
    panel_path = out / "firm_year_inputs.parquet"
    if any(p.exists() for p in (panel_path, out / "results", out / "models")):
        raise FileExistsError("Step 3 requires fresh panel/results/models output paths")
    lib, trainer = _load_modules(package)
    topic_cols = lib.load_topic_selection(selection)
    if topic_cols != [f"topic_{i:03d}" for i in ids]:
        raise ValueError("Delivered loader disagrees with selected topic IDs")
    panel = lib.build_inputs(paths["components"], paths["topics"], paths["compustat"])
    _validate_panel(panel, topic_cols, lib)
    if profile == "reproduce":
        _coverage(panel, pd.read_parquet(package / "data/firm_year_inputs.parquet"), "rebuilt panel")
    out.mkdir(parents=True, exist_ok=True)
    panel.to_parquet(panel_path, index=False)
    trainer.SELECTION = selection
    previous_argv = sys.argv
    try:
        sys.argv = [str(package / "code/02_train_and_score.py"), "--models", *MODELS,
                    "--inputs", str(panel_path), "--out", str(out)]
        trainer.main()
    finally:
        sys.argv = previous_argv
    score_path, metric_path = out / "results/risk_scores.parquet", out / "results/metrics.json"
    scores = pd.read_parquet(score_path)
    metrics = json.loads(metric_path.read_text(encoding="utf-8"))
    if metrics.get("n_topics") != len(ids):
        raise ValueError("Generated metrics do not cover the selected topics")
    _validate_outputs(panel, scores, metrics, out, lib)
    validation = {"profile": profile, "score_role": "OOF: risk_score_<model>; full fit: risk_score_<model>_full",
                  "rows": len(panel), "selected_topics": len(ids), "folds": 5}
    if profile == "reproduce":
        validation["reproduction"] = _compare_scores(scores, pd.read_parquet(package / "results/risk_scores.parquet"))
    # Add adapter checks without altering the scientific metrics written by source.
    metrics["adapter_validation"] = validation
    metric_path.write_text(json.dumps(metrics, indent=2, ensure_ascii=False), encoding="utf-8")
    if profile == "reproduce" and not validation["reproduction"]["passed"]:
        failed = [k for k, v in validation["reproduction"]["columns"].items() if not v["passed"]]
        raise ValueError(f"Step 3 reproduction exceeds numerical tolerance for {failed}; maxima in {metric_path}")
    return {"panel": str(panel_path), "scores": str(score_path), "metrics": str(metric_path),
            "models": {m: str(out / "models" / m) for m in MODELS}}
