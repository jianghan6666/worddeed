# Repository guide

The repository is organized by purpose, with the study materials following the four scientific stages.

| Folder | What belongs here |
| --- | --- |
| [agent_system/](../agent_system/README.md) | Executable coordinator, stage adapters, contracts and runtime tests. The Python module name stays stable for existing commands. |
| [docs/](README.md) | Workflow, roles, protocols, reference guides, roadmap and the local introduction/video. |
| [examples/](../examples/ceo-risk-preference/README.md) | Concise worked application and aggregate findings. |
| [study/](../study/README.md) | Original scientific methods and code, organized as representation, screening, prediction and assessment. |
| [results/](../results/README.md) | Full reviewer report, figures, searchable judgments, scores, workbooks and tables. |
| [replication/](../replication/README.md) | Download/restore/reproduction tools, inventories, tests and newly executed verification evidence. |

[RESULTS.md](../RESULTS.md) and [REPLICATION.md](../REPLICATION.md) are the two reviewer entry points at the repository root. New local inputs, restored packages and runs belong in ignored `.local/`. Large historical inputs and complete output archives are distributed through the linked private releases.

## Historical paths and frozen packages

The earlier repository exposed delivery and experiment names as top-level folders. Those materials now have one home per stage:

| Former location | Current location |
| --- | --- |
| `implementation/ceo-rd/` | `study/representation/` |
| `step-2-twelve-trial-pilot/` | `study/screening/review/` |
| `step-2-mvp-simple/experiment/expanded-ai-pilot/` | `study/screening/experiment/` |
| `step-2-mvp-simple/experiment/comparison-2026-10-19/` | `study/screening/history/comparison-2026-10-19/` |
| `step-3-4/packages/step3_risk_score_collaborator_20261027/` | `study/prediction/` |
| `step-3-4/packages/step4_full_from_raw_20261027/` | `study/assessment/full/` |
| `step-3-4/packages/step4_rd_score_collaborator_20261027/` | `study/assessment/score-models/` |
| `step-3-4/DELIVERY.json` and source manifests | `replication/manifests/empirical-delivery/` |
| `scripts/restore_review_bundle.py` | `replication/restore.py` |

[paths.json](../replication/paths.json) records the complete mapping, including moved documentation. The identity verifiers resolve old repository paths through this map. The catalogue binding in previously exported Windows handoffs remains accepted after verifying the same file hash.

Frozen archive members, supplied scientific package contents and historical verification receipts retain their original names and hashes. Their paths describe the archived layout at the time of execution. Restoring an archive under `.local/` therefore still produces its original `packages/...` structure; the runtime uses that restored structure. Historical source documents may refer to those paths or the former repository layout. Follow the current [replication guide](../REPLICATION.md) for commands.

Repository reorganization does not change empirical settings, labels, scores or estimates. Earlier release tags remain fixed so the completed reproduction can still be inspected at its recorded code revision.

Existing local runs can contain absolute paths into their original checkout. Resume those runs with that checkout, or start a new run directory with this layout. Portable exported Windows handoffs support both historical and current catalogue paths after checking the same file identity.
