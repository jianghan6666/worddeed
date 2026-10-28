"""Sequential stages, durable artifacts and stage-level resume."""

import copy
import hashlib
import json
import os
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

from .config import ROOT

STAGES = ("step1", "step2", "step3", "step4_prepare", "step4")


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n")
    tmp.replace(path)


def files(value, include_dirs=False):
    if isinstance(value, dict):
        for item in value.values():
            yield from files(item, include_dirs)
    elif isinstance(value, list):
        for item in value:
            yield from files(item, include_dirs)
    elif isinstance(value, str) and Path(value).is_absolute():
        path = Path(value)
        if path.is_file():
            yield path
        elif include_dirs and path.is_dir():
            yield from (p for p in path.rglob("*") if p.is_file())


class Workflow:
    def __init__(self, config, out):
        self.config = copy.deepcopy(config)
        self.out = Path(out).resolve()
        # Outputs never go inside a supplied scientific package.
        packages = Path(config["packages_root"]).resolve()
        if self.out == packages or self.out.is_relative_to(packages):
            raise ValueError("Output must be outside the frozen packages")
        self.out.mkdir(parents=True, exist_ok=True)
        self.path = self.out / "state.json"
        if self.path.exists():
            self.state = json.loads(self.path.read_text())
            old_config = self.state["config"]
            changed_stata = old_config.get("stata_exe") != self.config.get("stata_exe")
            scientific_old = {k: v for k, v in old_config.items() if k != "stata_exe"}
            scientific_new = {k: v for k, v in self.config.items() if k != "stata_exe"}
            if scientific_old != scientific_new or (changed_stata and
                    self.state["stages"].get("step4", {}).get("status") == "complete"):
                raise ValueError("Run configuration changed; start a new output directory")
            for path, digest in self.state["inputs"].items():
                if changed_stata and path == old_config.get("stata_exe"):
                    continue
                if not Path(path).is_file() or sha(path) != digest:
                    raise ValueError(f"Run input changed: {path}")
            if changed_stata:
                self.state["inputs"].pop(old_config.get("stata_exe"), None)
                value = self.config.get("stata_exe")
                if value and Path(value).is_file():
                    self.state["inputs"][value] = sha(value)
                self.state["config"] = self.config
                self.save()
                self.event("stata_executable_configured", path=value)
        else:
            inputs = {str(p): sha(p) for p in set(files(config))}
            # Bind the scientific package inventories without copying their assets.
            for name, inventory in (("step3_risk_score_collaborator_20261027", "MANIFEST.json"),
                                    ("step4_full_from_raw_20261027", "manifest.json")):
                p = packages / name / inventory
                inputs[str(p)] = sha(p)
            self.state = {"config": self.config, "inputs": inputs, "status": "ready", "stages": {}}
            self.save()
            self.event("run_created", profile=config["profile"])

    def save(self):
        write_json(self.path, self.state)

    def event(self, event, **data):
        with (self.out / "events.jsonl").open("a") as stream:
            stream.write(json.dumps({"at": datetime.now(timezone.utc).isoformat(),
                                     "event": event, **data}, ensure_ascii=False, allow_nan=False) + "\n")

    def status(self):
        return {"status": self.state["status"], "profile": self.config["profile"],
                "stages": {k: v["status"] for k, v in self.state["stages"].items()},
                "output": str(self.out)}

    def next_stage(self):
        return next((s for s in STAGES if self.state["stages"].get(s, {}).get("status") != "complete"), None)

    def run_stage(self, stage):
        if stage not in STAGES:
            raise ValueError(f"Unknown stage: {stage}")
        record = self.state["stages"].get(stage, {})
        if record.get("status") == "complete":
            for path, digest in record["outputs"].items():
                if not Path(path).is_file() or sha(path) != digest:
                    raise ValueError(f"Completed output changed: {path}")
            return record["artifacts"]
        if stage != self.next_stage():
            raise ValueError(f"Run {self.next_stage()} before {stage}")
        for prior in STAGES[:STAGES.index(stage)]:
            self.run_stage(prior)
        directory = self.out / ("step4" if stage == "step4" else stage)
        if directory.exists() and stage not in {"step1", "step2", "step4"}:
            directory.rename(self.out / f"{stage}.interrupted-{time.time_ns()}")
        directory.mkdir(exist_ok=True)
        request = {"stage": stage, "config": self.config, "out": str(directory),
                   "artifacts": {s: r["artifacts"] for s, r in self.state["stages"].items()
                                 if r.get("status") == "complete"}}
        request_path = self.out / f"{stage}.request.json"
        result_path = self.out / f"{stage}.result.json"
        write_json(request_path, request)
        record = {"status": "running", "attempt": record.get("attempt", 0) + 1}
        self.state["stages"][stage] = record
        self.state["status"] = "running"
        self.save()
        self.event("stage_started", stage=stage, attempt=record["attempt"])
        try:
            with (self.out / f"{stage}.log").open("a") as log:
                subprocess.run([self.config["python"], "-u", "-m", "agent_system.empirical.worker",
                                str(request_path), str(result_path)], cwd=ROOT, check=True,
                               stdout=log, stderr=subprocess.STDOUT,
                               env={**os.environ, "PYTHONUNBUFFERED": "1", "PYTHONDONTWRITEBYTECODE": "1"})
            artifacts = json.loads(result_path.read_text())
            outputs = {str(p): sha(p) for p in set(files(artifacts, include_dirs=True))}
            record.update(status="complete", artifacts=artifacts, outputs=outputs)
            self.state["status"] = "complete" if self.next_stage() is None else "ready"
            self.save()
            self.event("stage_complete", stage=stage, artifacts=artifacts)
            return artifacts
        except BaseException as exc:
            record.update(status="failed", error=str(exc), log=str(self.out / f"{stage}.log"))
            self.state["status"] = "failed"
            self.save()
            self.event("stage_failed", stage=stage, error=str(exc))
            raise

    def execute(self, through="step4"):
        if through not in STAGES:
            raise ValueError(f"Unknown stage: {through}")
        for stage in STAGES[:STAGES.index(through) + 1]:
            self.run_stage(stage)
        return self.status()
