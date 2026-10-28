"""Fresh-score I/O around the supplied Step 4 model construction functions."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


def _ids_hash(ids):
    return hashlib.sha256("\n".join(sorted(ids)).encode()).hexdigest()


def prepare_fresh(source, annual_path, matched_path, output, reference):
    """Reuse original jobs, trimming, design, and Stata engine; recalculate scales."""
    import numpy as np
    import pandas as pd

    output = Path(output)
    if output.exists() and any(output.iterdir()):
        raise FileExistsError(f"Use a fresh regression directory: {output}")
    annual, matched = pd.read_parquet(annual_path), pd.read_parquet(matched_path)
    cohorts, jobs = source.jobs_from_data(annual, matched)
    refs = {m["model_id"]: m for m in json.loads(Path(reference).read_text(encoding="utf-8-sig"))["models"]}
    if len(jobs) != 25 or set(refs) != {j["model_id"] for j in jobs}:
        raise ValueError("Expected the original 25 model declarations")
    for sub in ("input", "audit", "stata/inputs", "stata/samples", "stata/estimates", "stata/covariances"):
        (output / sub).mkdir(parents=True, exist_ok=True)
    for name, frame in cohorts.items():
        frame.reset_index(drop=True).to_parquet(output / "input" / f"{name}.parquet", index=False)
    models, blocks = [], []
    for job in jobs:
        mid = job["model_id"]
        ref = refs[mid]
        frame = cohorts[job["cohort"]].copy()
        if job["setting"] == "m09":
            frame = frame.loc[frame.sample_log.eq(1)].copy()
        if job["score_model"]:
            frame["rd_score"] = frame[job["score_column"]].to_numpy(copy=True)
        used, removed, trace = source.trim_pure_groups(frame)
        names, scales, bases = source.design(used, job["regressors"])
        ids_hash = _ids_hash(used.event_id)
        if (job["regressors"] != ref["regressors"] or names != ref["design_columns"]
                or len(frame) != ref["N_input"] or len(used) != ref["N_used"]
                or bases["sic2"] != ref["base_sic2"] or bases["fyear"] != ref["base_fyear"]
                or ids_hash != ref["used_ids_sha256"]):
            raise ValueError(f"{mid}: formula, sample or factor declarations changed")
        if not np.isfinite(scales).all() or not (scales > 0).all():
            raise ValueError(f"{mid}: invalid new numerical scales")
        # Only rd_score scales may differ: every financial input remains fixed.
        fixed = [i for i, name in enumerate(names) if name != "rd_score"]
        np.testing.assert_allclose(scales[fixed], np.asarray(ref["numerical_scales"])[fixed], rtol=2e-12, atol=1e-14)
        dta = frame[["event_id", "gvkey", "fyear", "sic2", "payer", "sample_log"] + job["regressors"]].reset_index(drop=True)
        if not frame.payer.isin([0, 1]).all() or not np.isfinite(dta.select_dtypes(include="number")).all().all():
            raise ValueError(f"{mid}: nonfinite input or nonbinary outcome")
        dta.to_stata(output / "stata/inputs" / f"{mid}.dta", write_index=False, version=118)
        sample = frame[["event_id", "gvkey", "fyear", "payer"]].copy()
        sample["used"] = sample.event_id.isin(used.event_id)
        sample = sample.merge(removed[["event_id", "reason"]], on="event_id", how="left", validate="1:1")
        sample["reason"] = sample.reason.fillna("retained")
        sample.to_csv(output / "audit" / f"{mid}_selection.csv", index=False, float_format="%.17g")
        y = used.payer.to_numpy(float)
        mean = float(y.mean())
        item = {**job, "N_input": len(frame), "N_used": len(used), "N_clusters": int(used.gvkey.nunique()),
                "base_sic2": bases["sic2"], "base_fyear": bases["fyear"], "design_columns": names,
                "numerical_scales": scales.tolist(), "pure_group_trace": trace,
                "input_file": f"inputs/{mid}.dta", "used_ids_sha256": ids_hash,
                "ll_null": float(np.sum(y * np.log(mean) + (1 - y) * np.log1p(-mean)))}
        models.append(item)
        values = {"MID": mid, "V": "b", "PER": job["period"], "SM": "natural",
                  "M": str(int(job["setting"][1:])), "SOURCE": f"./inputs/{mid}.dta",
                  "XVARS": " ".join(job["regressors"]),
                  "SCALES": " ".join(format(x, ".17g") for x in scales[:len(job["regressors"])]),
                  "NINPUT": str(len(frame)), "NUSED": str(len(used)),
                  "BSIC": str(bases["sic2"]), "BYEAR": str(bases["fyear"])}
        # The original template supplies table4fit. Stop immediately on any
        # command error; its final summary also rejects failed convergence.
        blocks.append("\n".join(f'global {key} "{value}"' for key, value in values.items()) + "\ntable4fit\n")
    template = Path(source.__file__).with_name("stata_engine_template.do").read_text(encoding="utf8")
    if template.count("@@MODEL_BLOCKS@@") != 1:
        raise ValueError("Unexpected original Stata template")
    (output / "stata/RUN_MODELS.do").write_text(template.replace("@@MODEL_BLOCKS@@", "\n\n".join(blocks)), encoding="utf8")
    source.write_json(output / "model_specifications.json", {"models": models, "profile": "fresh",
        "input_sources": {"annual_b_sha256": source.sha(annual_path), "matched_sha256": source.sha(matched_path)},
        "origin": "Original jobs_from_data, trim_pure_groups and design; newly supplied Step 3 scores"})
    source.write_json(output / "audit/PREPARATION_QA.json", {"passed": True, "models": len(models),
        "profile": "fresh", "formulas_samples_and_keys_match": True,
        "new_score_scales": True, "frozen_score_scale_equality_checked": False,
        "annual_B_rows": len(annual), "strict_score_rows": len(cohorts["scores_2013_2023"])})


def check_fresh_estimates(regression, reference):
    """Check schema, numerical health, and exact samples without old fit equality."""
    import math
    import numpy as np

    def read(path):
        with Path(path).open(encoding="utf-8-sig", newline="") as stream:
            return list(csv.DictReader(stream))

    regression, reference = Path(regression), Path(reference)
    specs = json.loads((regression / "model_specifications.json").read_text())["models"]
    expected = {s["model_id"]: s for s in specs}
    rows = read(regression / "stata/model_summary.csv")
    actual = {r["model_id"]: r for r in rows}
    if len(rows) != 25 or len(actual) != 25 or set(actual) != set(expected):
        raise ValueError("Expected 25 unique fitted model IDs")
    coefficients = read(regression / "stata/coefficients.csv")
    frozen = read(reference / "coefficients.csv")
    keys = lambda rs: {(r["model_id"], r["term"]) for r in rs}
    if len(keys(coefficients)) != len(coefficients) or keys(coefficients) != keys(frozen):
        raise ValueError("Coefficient keys differ from declared original models")
    frozen_by_key = {(r["model_id"], r["term"]): r for r in frozen}
    for row in coefficients:
        for field in ("coef", "se_oim", "se_cluster"):
            if not math.isfinite(float(row[field])):
                raise ValueError(f"Nonfinite {field}: {row['model_id']}/{row['term']}")
        if min(float(row["se_oim"]), float(row["se_cluster"])) < 0:
            raise ValueError("Negative standard error")
        for suffix in ("oim", "cluster"):
            omitted = int(float(row["omitted_" + suffix]))
            frozen_row = frozen_by_key[(row["model_id"], row["term"])]
            if omitted not in (0, 1) or omitted != int(float(frozen_row["omitted_" + suffix])):
                raise ValueError("Changed omitted-term flag")
            if not omitted and not 0 <= float(row["p_" + suffix]) <= 1:
                raise ValueError("Invalid nonomitted-term probability")
    for mid, spec in expected.items():
        row = actual[mid]
        numeric = {"N_input": spec["N_input"], "N_after_pure": spec["N_used"],
                   "N_oim": spec["N_used"], "N_cluster": spec["N_used"], "N_clusters": spec["N_clusters"],
                   "base_sic2": spec["base_sic2"], "base_fyear": spec["base_fyear"],
                   "converged_oim": 1, "converged_cluster": 1, "rc": 0, "core_omitted": 0}
        if row["status"] != "success" or any(float(row[k]) != v for k, v in numeric.items()):
            raise ValueError(f"{mid}: failed model/sample checks")
        likelihoods = [float(row[k]) for k in ("ll_oim", "ll_cluster")]
        if not all(math.isfinite(v) for v in likelihoods):
            raise ValueError(f"{mid}: nonfinite likelihood")
        np.testing.assert_allclose(*likelihoods, rtol=0, atol=1e-5)
        if not math.isfinite(float(row["max_b_change"])) or float(row["max_b_change"]) > 1e-5:
            raise ValueError(f"{mid}: OIM and cluster coefficient estimates differ")
        samples = read(regression / "stata/samples" / f"{mid}_used.csv")
        if len({r["event_id"] for r in samples}) != len(samples):
            raise ValueError(f"{mid}: duplicate estimation sample IDs")
        for field in ("esample_oim", "esample_cluster"):
            ids = [r["event_id"] for r in samples if float(r[field]) == 1]
            if len(ids) != spec["N_used"] or _ids_hash(ids) != spec["used_ids_sha256"]:
                raise ValueError(f"{mid}: changed {field} IDs")
        if any(not 0 <= float(r["probability_oim"]) <= 1 for r in samples):
            raise ValueError(f"{mid}: invalid fitted probabilities")
    destination = regression / "audit/REGRESSION_REPLAY_QA.json"
    destination.write_text(json.dumps({"passed": True, "profile": "fresh", "models": 25,
        "frozen_coefficient_equality_checked": False, "schema_samples_and_numerical_checks": True}, indent=2), encoding="utf8")
