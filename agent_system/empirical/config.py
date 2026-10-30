"""Small explicit configuration for the existing study."""

import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def load(path):
    path = Path(path).resolve()
    config = json.loads(path.read_text())
    if config.get("profile") not in {"reproduce", "fresh"}:
        raise ValueError("profile must be reproduce or fresh")
    required = ["packages_root", "python", "catalogue"]
    if config["profile"] == "reproduce":
        required.append("selection")
    for key in required:
        if not config.get(key):
            raise ValueError(f"Missing configuration: {key}; supply an explicit external input")
    if config["profile"] == "fresh":
        for key in ("toolkit", "packet_root"):
            if not config.get("step2", {}).get(key):
                raise ValueError(f"Missing configuration: step2.{key}; supply the external screening runtime")
    config.setdefault("step1", {"mode": "saved"})
    config.setdefault("step3", {})
    path_keys = {"packages_root", "python", "catalogue", "selection", "stata_exe",
                 "components", "topics", "compustat", "model_dir", "corpus", "rows",
                 "toolkit", "packet_root"}

    def paths(value):
        for key, item in value.items():
            if isinstance(item, dict):
                paths(item)
            elif key in path_keys and item:
                p = Path(item).expanduser()
                candidate = path.parent / p if not p.is_absolute() else p
                # A venv's python is commonly a symlink. Executing the resolved
                # base binary bypasses pyvenv.cfg and loses the pinned packages.
                value[key] = os.path.abspath(candidate) if key == "python" else str(candidate.resolve())
    paths(config)
    packages = Path(config["packages_root"])
    step3 = packages / "step3_risk_score_collaborator_20261027"
    for key, relative in {"components": "data/components/components.parquet",
                          "topics": "data/components/topic_distr.npz",
                          "compustat": "data/compustat/compustat_panel_firms.csv"}.items():
        config["step3"].setdefault(key, str(step3 / relative))
    for name in ("step3_risk_score_collaborator_20261027", "step4_full_from_raw_20261027"):
        if not (packages / name / "data").exists() and not (packages / name / "project").exists():
            raise ValueError(f"Restore the complete private package: {packages / name}")
    return config
