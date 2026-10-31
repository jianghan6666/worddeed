# Downstream assessment

| Route | Folder | Scope |
| --- | --- | --- |
| Full connected analysis | [full/](full/README.md) | Rebuild financial and matching data, prepare inputs, and estimate all 25 regressions: nine annual-behavior models and sixteen score models. |
| Compact score analysis | [score-models/](score-models/README.md) | Replay sixteen score models from the supplied frozen inputs. |

Use [the replication guide](../../REPLICATION.md) to connect newly fitted prediction scores to the full route. The compact route is retained separately because it starts from frozen inputs. Complete original tables and workbooks are also organized for reading under [applications/ceo-risk-preference/results/step4/](../../results/step4).
