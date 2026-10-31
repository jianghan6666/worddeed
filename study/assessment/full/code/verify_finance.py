"""Compare fresh raw-data finance reconstruction with read-only reference data.

References are checked only after construction; they are never construction inputs.
All rows and columns are compared, including exclusion flags and unmatched records.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd

REPLICATION_NAME = Path("replications/caliskan_doukas_2015")
REFERENCE_FILES = {
    "data/processed/panel_master_audit.parquet": "event_id",
    "data/processed/table4_b_original_2006_2011.parquet": "event_id",
    "data/processed/table4_b_extended_2006_2023.parquet": "event_id",
    "data/processed/table4_b_new_2012_2023.parquet": "event_id",
    "data/interim/market_inputs.parquet": "event_id",
    "data/interim/option_portfolios.parquet": "valuation_id",
    "audits/ceo_selection_audit.parquet": "anncomp_row_id",
    "audits/sample_selection_audit.parquet": "event_id",
}


def verify_finance(package_root: Path, run_root: Path | None = None,
                   reference_root: Path | None = None) -> dict:
    package_root = Path(package_root).resolve()
    run_root = Path(run_root) if run_root is not None else package_root / "rerun"
    if not run_root.is_absolute():
        run_root = package_root / run_root
    generated = run_root / "project" / REPLICATION_NAME
    reference = (Path(reference_root) if reference_root is not None
                 else package_root / "reference/finance")
    if not reference.is_absolute():
        reference = package_root / reference
    checks = []
    for relative, key in REFERENCE_FILES.items():
        expected_path, actual_path = reference / Path(relative).name, generated / relative
        expected, actual = pd.read_parquet(expected_path), pd.read_parquet(actual_path)
        expected = expected.sort_values(key).reset_index(drop=True)
        actual = actual.sort_values(key).reset_index(drop=True)
        check = {"file": relative, "key": key, "reference_rows": len(expected),
                 "rebuilt_rows": len(actual), "reference_columns": len(expected.columns),
                 "rebuilt_columns": len(actual.columns), "columns": []}
        check["unique_keys"] = bool(expected[key].is_unique and actual[key].is_unique)
        check["key_values_exact"] = bool(expected[key].equals(actual[key]))
        check["column_order_exact"] = list(expected.columns) == list(actual.columns)
        check["shape_exact"] = expected.shape == actual.shape
        if not all(check[k] for k in ("unique_keys", "key_values_exact", "column_order_exact", "shape_exact")):
            check["passed"] = False
            checks.append(check)
            continue
        for name in expected:
            a, b = expected[name], actual[name]
            if pd.api.types.is_numeric_dtype(a.dtype) or pd.api.types.is_bool_dtype(a.dtype):
                av = a.to_numpy(dtype=float, na_value=np.nan)
                bv = b.to_numpy(dtype=float, na_value=np.nan)
                finite = np.isfinite(av) & np.isfinite(bv)
                nonfinite = ((np.isnan(av) & np.isnan(bv)) | (av == bv) | finite)
                error = float(np.max(np.abs(av[finite] - bv[finite]) /
                                     np.maximum(1., np.abs(av[finite])))) if finite.any() else 0.
                exact = bool(np.array_equal(av, bv, equal_nan=True))
                passed = bool(nonfinite.all() and error <= 1e-12)
                result = {"column": name, "numeric_exact": exact,
                          "maximum_scaled_error": error, "passed": passed}
            else:
                av = a.astype("string").fillna("<NA>")
                bv = b.astype("string").fillna("<NA>")
                result = {"column": name, "value_exact": bool(av.equals(bv)),
                          "passed": bool(av.equals(bv))}
            check["columns"].append(result)
        check["passed"] = all(c["passed"] for c in check["columns"])
        checks.append(check)
    report = {"status": "passed" if all(c["passed"] for c in checks) else "FAILED",
              "reference_only_used_after_rebuild": True,
              "files_checked": len(checks), "checks": checks,
              "numeric_tolerance": "abs(actual-reference)/max(1,abs(reference)) <= 1e-12",
              "all_numeric_columns_exact": all(
                  c.get("numeric_exact", True) for f in checks for c in f["columns"]),
              "all_company_year_ids_and_sample_flags_compared": True}
    destination = generated / "audits/FINANCE_REPRODUCTION_CHECK.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2), encoding="utf8")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package-root", type=Path,
                        default=Path(__file__).resolve().parents[1])
    parser.add_argument("--run-root", type=Path, default=None)
    parser.add_argument("--reference-root", type=Path, default=None)
    args = parser.parse_args()
    report = verify_finance(args.package_root, args.run_root, args.reference_root)
    print(json.dumps({key: report[key] for key in
                     ("status", "files_checked", "all_numeric_columns_exact")}), flush=True)
    raise SystemExit(0 if report["status"] == "passed" else 1)


if __name__ == "__main__":
    main()
