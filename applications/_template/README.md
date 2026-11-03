# Application: <name>

Copy this outline into `applications/<application-name>/README.md`. Replace every placeholder and link the actual evidence before labeling any stage complete. See [Adding an application](../../docs/NEW_APPLICATION.md).

## Research specification

- Construct and intended interpretation:
- Narrative source, access conditions and time window:
- Behavioral target and its measurement:
- Observation unit, identifiers and matching rules:
- External assessment setting, independent criteria and comparisons with narrative/behavioral proxies:
- Results that would count against the intended interpretation:
- Competing explanations, leakage risks and limitations:

## Four stages

| Stage | Chosen method | Inputs and identities | Outputs and checks | Status |
| --- | --- | --- | --- | --- |
| Representation | To specify | To specify | To specify | Planned |
| Relevance screening | To specify | To specify | To specify | Planned |
| Behavioral prediction | To specify | To specify | To specify | Planned |
| Assessment | To specify | To specify | To specify | Planned |

## Implementation and reproduction

Identify reused runtime components, application-specific adapters, required dependencies, exact execution commands and expected checks. Document what changes from existing applications. Specify each adapter's input/output contract and the code needed for new schemas, targets, features and downstream models; renaming a configuration is not a completed adaptation. Keep scientific settings explicit and distinguish fixtures, supplied results and newly executed results.

For new AI judgments, identify the complete authorized source packet, requested and observed model settings, reader histories, input checks and source-transmission conditions. The current CEO replay archive does not satisfy the newer fresh-screening adapter: 21 required inputs are absent. Do not mark fresh screening ready on the basis of a saved-record replay or fixture test.

Use `study/` for scientific material, `results/` for completed findings, and `replication/` for application inventories and verification receipts. Add `RESULTS.md` and `REPLICATION.md` when those deliverables exist. Keep new inputs and runs under ignored `.local/<application-name>/`; distribute authorized large inputs through inventoried releases.
