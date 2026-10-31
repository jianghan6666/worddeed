# Replication utilities and drivers

The [replication index](../REPLICATION.md) lists application packages. For the current completed case, use [CEO replication instructions](../applications/ceo-risk-preference/REPLICATION.md).

| Tools | Purpose and scope |
| --- | --- |
| `restore.py` | Verify and restore an inventoried archive, independently of its application. |
| `paths.json`, `paths.py` | Resolve historical repository locations while retaining recorded file identities. |
| `download.py`, `verify_source.py` | Obtain and verify the CEO application's frozen input releases. |
| `reproduce.py`, `replay_screening.py`, `check_supplementary.py` | Execute the CEO connected study and supplied supplementary checks. |
| `windows_refit.py`, `continue_stata.py`, `package_run.py` | Export the current Windows run, continue Stata estimation and package completed outputs. |
| `verify.py`, `verify_delivery.py`, `tests/` | Check imported scientific sources, reading copies, handoff compatibility and tooling. |

The CEO application's [manifests](../applications/ceo-risk-preference/replication/manifests/) and [verification receipts](../applications/ceo-risk-preference/replication/verification/README.md) live with its [scientific materials](../applications/ceo-risk-preference/study/README.md). Other applications must provide their own manifests, methods and execution checks. The current drivers do not select an arbitrary application by name; see [Adding an application](../docs/NEW_APPLICATION.md) for the adaptation boundary.

Reusable workflow execution remains in [agent_system/](../agent_system/README.md). Put new downloads and run outputs under ignored `.local/<application-name>/`.
