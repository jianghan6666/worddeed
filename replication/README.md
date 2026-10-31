# Replication tools and evidence

Start with [REPLICATION.md](../REPLICATION.md) for the verified environment, downloads and complete execution commands.

| Location | Purpose |
| --- | --- |
| `download.py`, `restore.py`, `verify_source.py` | Obtain and verify the frozen inputs; restore or stream-check archives. |
| `reproduce.py`, `replay_screening.py`, `check_supplementary.py` | Execute the connected study and supplied supplementary checks. |
| `windows_refit.py`, `continue_stata.py`, `package_run.py` | Export the Windows run, continue Stata estimation and package completed outputs. |
| [manifests/](manifests/) | Frozen input/output inventories; the original combined prediction/assessment delivery is under `empirical-delivery/`. |
| [verification/](verification/README.md) | Newly executed checks and retained failed-attempt diagnostics. |
| `verify.py`, `verify_delivery.py`, `tests/` | Check imported identities, the relocated reading copies and replication tooling. |
| [paths.json](paths.json), `paths.py` | Resolve former repository paths recorded in historical manifests and handoffs. |

Scientific source packages are organized by stage under [study/](../study/README.md). Reusable workflow execution remains in [agent_system/](../agent_system/README.md). New downloads and run outputs belong under ignored `.local/`.
