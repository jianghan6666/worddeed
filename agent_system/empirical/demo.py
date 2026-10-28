"""Offline synthetic demonstration: python -m agent_system.empirical.demo --out DIR [--resume].

No datasets, training, finance reconstruction, scientific annotations, Stata or
model calls. Only the Workflow's worker subprocess is replaced with tiny fixtures.
"""

import argparse
import csv
import json
import shutil
import sys
from pathlib import Path
from unittest.mock import patch

from .coordinator import DEFAULT_COORDINATOR, run
from .workflow import STAGES, Workflow, sha, write_json

NOTICE = "SYNTHETIC DEMONSTRATION ONLY; not scientific results"


class DemoProvider:
    """Deterministic tool decisions from actual receipts, never a live model."""

    mode = "offline_fixture"
    requested_model = None
    requested_effort = None

    def respond(self, role, instructions, tools, history):
        calls = [item for item in history if item.get("type") == "function_call"]
        name, arguments = "get_status", {}
        if calls:
            last = calls[-1]
            receipt = next(item for item in reversed(history)
                           if item.get("type") == "function_call_output" and item["call_id"] == last["call_id"])
            result = json.loads(receipt["output"])
            if result["status"] == "ok" and last["name"] == "get_status":
                status = result["workflow"]
                required = STAGES[:STAGES.index(status["through"]) + 1]
                stage = next((s for s in required if status["stages"].get(s) != "complete"), None)
                name, arguments = ("run_stage", {"stage": stage}) if stage else ("finish", {})
            elif result["status"] == "ok" and last["name"] == "run_stage":
                name, arguments = "read_result", {"stage": json.loads(last["arguments"])["stage"]}
        number = len(calls) + 1
        return {"id": f"demo-response-{number:04}", "status": "completed", "model": None,
                "usage": None, "fixture": True, "demonstration": True, "notice": NOTICE,
                "scientific_completion": False,
                "output": [{"type": "function_call", "call_id": f"demo-call-{number:04}",
                            "name": name, "arguments": json.dumps(arguments)}]}


def _csv(path, rows):
    with Path(path).open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _rows(path):
    with Path(path).open(newline="") as stream:
        return list(csv.DictReader(stream))


def _fixture_worker(command, *, fail_stage=None, interrupt_stage=None, **kwargs):
    """Only called under the demo's scoped patch; never launches a subprocess."""
    request = json.loads(Path(command[-2]).read_text())
    stage, previous = request["stage"], request["artifacts"]
    out = Path(request["out"])
    # Partial artifacts are intentionally preserved by Workflow on failed attempts.
    (out / "DEMONSTRATION.txt").write_text(NOTICE + "\n")
    if stage == interrupt_stage:
        raise KeyboardInterrupt("Synthetic demonstration interruption")
    if stage == fail_stage:
        raise RuntimeError("Synthetic demonstration worker failure")
    artifacts = {"demonstration": True, "notice": NOTICE, "scientific_completion": False}
    if stage == "step1":
        topics = out / "topic_weights.json"
        write_json(topics, {"notice": NOTICE, "rows": [
            {"firm": "fixture-a", "year": 2020, "T1": 0.1, "T2": 0.3, "T3": 0.6},
            {"firm": "fixture-b", "year": 2020, "T1": 0.6, "T2": 0.2, "T3": 0.2},
        ]})
        artifacts.update(topics=str(topics), mode="fabricated_topic_weights_no_model")
    elif stage == "step2":
        selected = out / "selected_topics.json"
        shutil.copyfile(request["config"]["selection"], selected)
        artifacts.update(selection=str(selected), mode="author_written_fixture_selection")
    elif stage == "step3":
        selection = Path(previous["step2"]["selection"])
        ids = json.loads(selection.read_text())["selected_topic_ids"]
        topics = Path(previous["step1"]["topics"])
        scores = out / "generated_scores.csv"
        # Toy wiring arithmetic only; no trained/predictive/scientific interpretation.
        _csv(scores, [{"firm": row["firm"], "year": row["year"],
                       "demo_score": round(sum(row[topic] for topic in ids), 6),
                       "notice": NOTICE} for row in json.loads(topics.read_text())["rows"]])
        lineage = out / "score_lineage.json"
        write_json(lineage, {"notice": NOTICE, "selected_topic_ids": ids,
                             "selection": str(selection), "selection_sha256": sha(selection),
                             "topics": str(topics), "scores": str(scores), "scores_sha256": sha(scores),
                             "operation": "toy sum of fabricated selected weights; no training"})
        artifacts.update(scores=str(scores), lineage=str(lineage), selection=str(selection))
    elif stage == "step4_prepare":
        scores = Path(previous["step3"]["scores"])
        prepared = out / "step4_input.csv"
        _csv(prepared, _rows(scores))
        lineage = out / "input_lineage.json"
        write_json(lineage, {"notice": NOTICE, "scores": str(scores), "scores_sha256": sha(scores),
                             "step4_input": str(prepared), "step4_input_sha256": sha(prepared)})
        artifacts.update(input=str(prepared), scores=str(scores), lineage=str(lineage))
    else:
        prepared = Path(previous["step4_prepare"]["input"])
        result = out / "fixture_receipt.json"
        write_json(result, {"notice": NOTICE, "scientific_completion": False,
                            "estimation": "not_run", "input": str(prepared),
                            "input_sha256": sha(prepared), "fixture_rows": len(_rows(prepared))})
        artifacts.update(receipt=str(result), input=str(prepared), estimation="not_run")
    write_json(command[-1], artifacts)


def run_demo(out, resume=False, *, selected_topic_ids=("T1", "T3"), fail_stage=None, interrupt_stage=None):
    """Assemble or resume fixtures through the SAME dispatcher used by the CLI.

    Failure/interruption arguments are test hooks, not scientific worker options.
    """
    out = Path(out).resolve()
    config_path = out / "demo_config.json"
    if resume:
        if not config_path.is_file():
            raise ValueError("No demonstration configuration exists to resume")
        config = json.loads(config_path.read_text())
        if not config.get("demonstration"):
            raise ValueError("Resume is restricted to a synthetic demonstration")
    else:
        out.mkdir(parents=True, exist_ok=False)
        if not selected_topic_ids or len(set(selected_topic_ids)) != len(selected_topic_ids) or not set(selected_topic_ids) <= {"T1", "T2", "T3"}:
            raise ValueError("Expected unique fabricated topic IDs T1/T2/T3")
        fixture = out / "fixture-inputs"
        packages = fixture / "packages"
        # Invented inventories satisfy the dispatcher's input binding without any
        # access to the received scientific packages or supplied datasets.
        for name, inventory in (("step3_risk_score_collaborator_20261027", "MANIFEST.json"),
                                ("step4_full_from_raw_20261027", "manifest.json")):
            write_json(packages / name / inventory, {"notice": NOTICE, "synthetic_inventory": True})
        selection = fixture / "selection.json"
        write_json(selection, {"notice": NOTICE, "selected_topic_ids": list(selected_topic_ids)})
        config = {"profile": "reproduce", "demonstration": True, "notice": NOTICE,
                  "packages_root": str(packages), "selection": str(selection), "python": sys.executable,
                  "coordinator": dict(DEFAULT_COORDINATOR)}
        write_json(config_path, config)
    workflow = Workflow(config, out / "workflow")
    # The stage state, ordering, requests, attempts, hashes and resume are real.
    # Every numerical output and coordinator decision in this demo is a fixture.
    with patch("agent_system.empirical.workflow.subprocess.run",
               side_effect=lambda command, **kwargs: _fixture_worker(
                   command, fail_stage=fail_stage, interrupt_stage=interrupt_stage, **kwargs)):
        result = run(workflow, provider=DemoProvider())
    summary = {**result, "status": "demonstration_complete" if result["status"] == "completed" else result["status"],
               "notice": NOTICE, "demonstration": True, "scientific_completion": False,
               "live_model_calls": False, "training_executed": False, "estimation_executed": False,
               "artifacts": {stage: record["artifacts"] for stage, record in workflow.state["stages"].items()
                             if record["status"] == "complete"}}
    write_json(out / "summary.json", summary)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    summary = run_demo(args.out, resume=args.resume)
    print(json.dumps(summary, indent=2))
    return 0 if summary["status"] == "demonstration_complete" else 1


if __name__ == "__main__":
    raise SystemExit(main())
