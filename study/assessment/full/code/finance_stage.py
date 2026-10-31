"""Rebuild annual CEO finance inputs from the package's unmodified raw files.

The three historical finance modules are imported without editing their source.
Their input/output path constants are redirected so package inputs remain read-only
and all constructed data, audit evidence, and CRSP caches are written under rerun.
No model is estimated and no score is trained by this stage.
"""
from __future__ import annotations

import argparse
import importlib
import importlib.util
import hashlib
import json
import sys
sys.dont_write_bytecode = True
import time
import traceback
from pathlib import Path

REPLICATION_NAME = Path("replications/caliskan_doukas_2015")
STAGES = ("prepare", "market", "valuations", "options", "finalize")


def run_finance(package_root: Path, run_root: Path | None = None,
                stage: str = "all") -> dict:
    """Run in order; run_root denotes the generated output root.

    Default output: PACKAGE/rerun/project/replications/caliskan_doukas_2015.
    An explicitly supplied relative run_root is relative to package_root.
    """
    package_root = Path(package_root).resolve()
    source_rep = package_root / "project" / REPLICATION_NAME
    if run_root is None:
        generated_root = package_root / "rerun"
    else:
        generated_root = Path(run_root)
        if not generated_root.is_absolute():
            generated_root = package_root / generated_root
    run_project = generated_root.resolve() / "project"
    output_rep = run_project / REPLICATION_NAME
    if output_rep == source_rep:
        raise ValueError("Generated output must be separate from package/project inputs")
    for directory in (output_rep / "data/interim", output_rep / "data/processed",
                      output_rep / "audits", output_rep / "reports"):
        directory.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(source_rep / "scripts"))
    source_file = source_rep / "scripts/build_regression_data.py"
    source_text = source_file.read_text(encoding="utf8")
    # These three substitutions change provenance-path serialization only.
    # No sample, formula, value, market-window, or option calculation is changed.
    adapters = {
        "str(path.relative_to(ROOT))": "str(Path('data/raw') / path.relative_to(RAW))",
        "sorted((ROOT/'scripts').glob('*.py'))": "sorted((SOURCE_ROOT/'scripts').glob('*.py'))",
        "str(p.relative_to(ROOT))": "str(p.relative_to(SOURCE_ROOT))",
    }
    adapted_text = source_text
    for old, new in adapters.items():
        if adapted_text.count(old) != 1:
            raise ValueError("Historical source changed; inspect manifest adapter: " + old)
        adapted_text = adapted_text.replace(old, new)
    spec = importlib.util.spec_from_file_location("_step4_finance_core", source_file)
    core = importlib.util.module_from_spec(spec)
    exec(compile(adapted_text, str(source_file), "exec"), core.__dict__)
    market = importlib.import_module("market_inputs")
    options = importlib.import_module("option_portfolios")
    # ROOT is also used for relative output paths and provenance manifests.
    # Configuration was already loaded from source_rep/build_config.json.
    core.ROOT = output_rep
    core.SOURCE_ROOT = source_rep
    core.RAW = source_rep / "data/raw"
    core.INT = output_rep / "data/interim"
    core.OUT = output_rep / "data/processed"
    core.AUD = output_rep / "audits"
    core.REPORT = output_rep / "reports"
    source_files = [
        "compustat/funda_datadate_2003-01_2024-06.csv.gz",
        "compustat/funda_population_keys_all.csv.gz",
        "execucomp/anncomp_1992_2023_allfields.csv.gz",
        "execucomp/outstandingawards_2006_2023_allfields.csv.gz",
        "execucomp/pension_2006_2023_allfields.csv.gz",
        "execucomp/deferredcomp_2006_2023_allfields.csv.gz",
        "crsp/ccmxpf_lnkhist_postgres_all.csv.gz",
        "crsp/msf_all_2000-12_2024-06.csv.gz",
        "crsp/dsf_all_2005-01-01_2024-06-30.csv.gz",
        "fred/DTB3_2005-01-01_2024-06-30.csv",
    ]
    missing = [name for name in source_files if not (core.RAW / name).is_file()]
    if missing:
        raise FileNotFoundError("Required raw finance files missing: " + ", ".join(missing))
    report = {
        "status": "running", "stage_requested": stage,
        "input_raw_root": str(core.RAW), "generated_replication_root": str(output_rep),
        "historical_finance_source_files_unmodified": True,
        "manifest_only_runtime_adapters": adapters,
        "source_build_module_sha256": hashlib.sha256(source_file.read_bytes()).hexdigest(),
        "adapted_build_text_sha256": hashlib.sha256(adapted_text.encode()).hexdigest(),
        "configuration_from": str(source_rep / "build_config.json"),
        "original_production_outputs_used_as_inputs": False,
        "preexisting_market_cache": (core.INT / "market_cache").exists(),
        "scope": "Raw financial data reconstruction; annual-B regression branch downstream",
        "stages": [], "regressions_run": False, "scores_retrained": False,
    }
    report_path = core.AUD / "FINANCE_STAGE.json"

    def write_report():
        report_path.write_text(json.dumps(report, indent=2), encoding="utf8")

    def do_market():
        return market.build_market_inputs(
            core.INT / "market_requests_latest.parquet", core.RAW / "crsp",
            core.INT / "market_inputs.parquet", core.AUD / "market")

    def do_options():
        return options.build_option_portfolios(
            core.INT / "ceo_valuation_inputs.parquet",
            core.RAW / "execucomp/outstandingawards_2006_2023_allfields.csv.gz",
            core.RAW / "execucomp/pension_2006_2023_allfields.csv.gz",
            core.RAW / "execucomp/deferredcomp_2006_2023_allfields.csv.gz",
            core.INT / "option_portfolios.parquet", core.AUD / "options")

    actions = {"prepare": core.prepare, "market": do_market,
               "valuations": core.make_valuation_inputs,
               "options": do_options, "finalize": core.finalize}
    started = time.monotonic()
    write_report()
    try:
        for name in STAGES if stage == "all" else (stage,):
            print("FINANCE stage " + name + " started", flush=True)
            began = time.monotonic()
            actions[name]()
            report["stages"].append({"stage": name, "status": "completed",
                                      "elapsed_seconds": time.monotonic() - began})
            write_report()
            print("FINANCE stage " + name + " completed", flush=True)
        report["status"] = "completed"
        report["elapsed_seconds"] = time.monotonic() - started
        write_report()
        return report
    except Exception:
        report["status"] = "failed"
        report["elapsed_seconds"] = time.monotonic() - started
        report["error"] = traceback.format_exc()
        write_report()
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package-root", type=Path,
                        default=Path(__file__).resolve().parents[1])
    parser.add_argument("--run-root", type=Path, default=None,
                        help="Generated output root; default PACKAGE/rerun; contains project/")
    parser.add_argument("--stage", choices=("all",) + STAGES, default="all")
    args = parser.parse_args()
    result = run_finance(args.package_root, args.run_root, args.stage)
    print(json.dumps({"status": result["status"],
                      "generated_root": result["generated_replication_root"],
                      "elapsed_seconds": result["elapsed_seconds"]}), flush=True)


if __name__ == "__main__":
    main()
