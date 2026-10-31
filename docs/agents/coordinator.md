# Coordinator

Read the study configuration and saved state. Dispatch the next stage, inspect its actual outputs, and integrate the execution record.

The executable coordinator uses get_status, run_stage, read_result, and finish. It cannot silently alter the method or claim completion without the required artifacts.

These guides describe workflow responsibilities. The executable system has one coordinator, three model readers for fresh screening, and computational stage adapters. Follow the [workflow guide](../WORKFLOW.md); researchers retain scientific decisions.

Handoffs preserve input versions, configuration, artifact paths, unresolved decisions, and the next step. See the [runtime guide](../../agent_system/empirical/README.md).
