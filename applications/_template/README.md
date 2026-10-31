# Application: <name>

Copy this outline into `applications/<application-name>/README.md`. Replace every placeholder and link the actual evidence before labeling any stage complete. See [Adding an application](../../docs/NEW_APPLICATION.md).

## Research specification

- Construct and intended interpretation:
- Narrative source, access conditions and time window:
- Behavioral target and its measurement:
- Observation unit, identifiers and matching rules:
- Assessment setting and independent validation criteria:
- Competing explanations, leakage risks and limitations:

## Four stages

| Stage | Chosen method | Inputs and identities | Outputs and checks | Status |
| --- | --- | --- | --- | --- |
| Representation | To specify | To specify | To specify | Planned |
| Relevance screening | To specify | To specify | To specify | Planned |
| Behavioral prediction | To specify | To specify | To specify | Planned |
| Assessment | To specify | To specify | To specify | Planned |

## Implementation and reproduction

Identify reused runtime components, application-specific adapters, required dependencies, exact execution commands and expected checks. Document what changes from existing applications. Keep scientific settings explicit and distinguish fixtures, supplied results and newly executed results.

Use `study/` for scientific material, `results/` for completed findings, and `replication/` for application inventories and verification receipts. Add `RESULTS.md` and `REPLICATION.md` when those deliverables exist. Keep new inputs and runs under ignored `.local/<application-name>/`; distribute authorized large inputs through inventoried releases.
