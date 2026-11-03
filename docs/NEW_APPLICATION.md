# Adding an application

WordDeed connects narrative representation, relevance screening, behavioral prediction and downstream assessment. An application supplies the research question and the scientific choices for those stages. The [CEO risk-preference case](../applications/ceo-risk-preference/README.md) demonstrates one specification.

## Specify the research before running it

Start from the [application template](../applications/_template/README.md). Define the construct, narrative source, behavioral target, unit, period and intended interpretation. Name an external criterion and a result that would count against the proposed interpretation; plan comparisons among narrative, behavioral and synthesized proxies. Record data access, identifier alignment, timing and missingness rules. Prespecify how to distinguish the intended construct from competing explanations.

Choose the representation and screening protocol for the new material. Explain the readers' relevance rule, independence, source review, missing-response handling and aggregation. Choose the prediction model, feature transformations, splits, tuning and assessment design for the new target. These decisions belong to the researcher; the CEO study's R&D target and financial controls are not framework defaults.

## Reuse the orchestration and adapt the computation

The shared [runtime](../agent_system/README.md) supplies coordinator contracts, provider handling, stage handoffs, saved state and resume. The [workflow guide](WORKFLOW.md) and [role guides](agents/coordinator.md) describe the research responsibilities.

The current `agent_system/empirical/` path combines this orchestration with adapters for the CEO/R&D application. Its package names, data fields, model grids and downstream regressions are specific to that application. Changing a construct label does not make another study runnable. Review each stage's input/output contract and implement or select compatible adapters explicitly. A general application plug-in interface and an independently validated second application remain [roadmap](ROADMAP.md) work. The proposal reports a political-ideology trial, but its results are not packaged here.

For new AI screening, the current released archive is insufficient for the newer API adapter: its preflight fails on 21 missing required files before provider calls. Saved-reader replay uses a different input route. Supply a complete authorized packet tree and pass its actual input checks before a new live run; changing paths or obtaining model access alone does not repair the gap. See the [runtime guide](../agent_system/empirical/README.md).

Keep application-specific source code and scientific settings under `applications/<application-name>/study/`. Put reusable orchestration improvements in `agent_system/`, with tests that preserve existing applications. Configuration and entry points must identify the selected application; do not silently change another application's defaults.

## Package a complete application

Use the following structure as deliverables become available:

```text
applications/<application-name>/
|-- README.md          Research question and worked walkthrough
|-- study/             Scientific methods, inputs documentation and source code
|-- results/           Complete outputs, tables and figures
|-- replication/       Inventories, environments and executed verification
|-- RESULTS.md         Findings and output navigation
`-- REPLICATION.md     Exact reproduction instructions and boundaries
```

Keep large authorized inputs in inventoried releases and new runs in `.local/<application-name>/`. Preserve source identities, independent judgments, missingness and numerical settings. Test the new adapters, execute the study from a fresh download, and separate actual verification from fixtures or supplied historical checks.

Add the application to [applications/README.md](../applications/README.md), then to the root [results](../RESULTS.md) and [replication](../REPLICATION.md) indexes when those packages exist. Report unfinished stages and scientific limitations explicitly. Successful execution is separate from construct validity.
