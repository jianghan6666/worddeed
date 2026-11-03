# Coordinator

Read the study configuration and saved state. Dispatch the next stage, inspect its actual outputs, and integrate the execution record.

The executable coordinator uses `get_status`, `run_stage`, `read_result` and `finish`. It cannot edit the configured method through these tools. Completion follows recorded stage status and checks of recorded artifact hashes; the current scientific adapters also perform stage-specific checks. Model narration alone cannot finish a run.

The generic dispatcher does not yet enforce every required artifact or recheck every input before each new stage. The standard reproduction wrapper separately rehashes restored package members; direct/manual execution should not be assumed to provide the same coverage. Synthetic fault checks demonstrated these limits, not false completion in the recorded empirical run. Required-artifact and input-check hardening remain [roadmap](../ROADMAP.md) work.

These guides describe workflow responsibilities. The executable system has an optional model coordinator, an implemented three-reader fresh-screening interface and computational stage adapters. The current release lacks 21 required fresh-screening inputs and fails preflight before provider calls; saved-reader replay remains available. Follow the [workflow guide](../WORKFLOW.md); researchers retain scientific decisions.

Handoffs preserve input versions, configuration, artifact paths, unresolved decisions, and the next step. See the [runtime guide](../../agent_system/empirical/README.md).
