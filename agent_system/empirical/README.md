# Connected four-step workflow

One coordinator connects topic inputs, independent relevance screening, proxy estimation and downstream analysis through saved artifacts. Start with the offline demo to inspect these handoffs. The [reviewer replication guide](../../applications/ceo-risk-preference/REPLICATION.md) separates the demo, saved-judgment replay and numerical reproduction. The identified repository and release assets were public when inspected on 2 November 2026; source-specific access conditions still apply. The released replay archive is incomplete for the newer fresh-screening API route.

## Run the self-contained demo

From the repository root with **Python 3.11 or newer**:

```sh
python3 -m agent_system.empirical.demo --out .local/connected-demo
python3 -m agent_system.empirical.demo --out .local/connected-demo --resume
```

Use a new directory for the first command. The demo requires only the standard library. Its three invented topics, model replies and numerical outputs are fixtures; it makes no model calls and performs no empirical training or Stata estimation.

Inspect `summary.json`, `workflow/state.json` and `workflow/events.jsonl` under the output directory. The coordinator, dispatcher, artifact hashing and resume checks are the same components used by the empirical route. Changing the fixture selection changes the generated scores and Step 4 inputs.

## Stage connections

| Stage | Adapter | External inputs for empirical use |
| --- | --- | --- |
| 1. Topic inputs | [step1.py](step1.py) | Ordered 354-topic catalogue, component metadata and matching density matrix; optional installed topic package for inference |
| 2. Relevance screening | [screening.py](screening.py), [worker.py](worker.py) | Explicit saved selection, or compatible screening toolkit and complete source-review packets |
| 3. Proxy estimation | [step3.py](step3.py) | Compatible `step3_risk_score_collaborator_20261027` package with scientific code and data |
| 4. Downstream analysis | [step4.py](step4.py), [model_inputs.py](model_inputs.py) | Compatible `step4_full_from_raw_20261027` package and Stata for estimation |

The supplied study predicts R&D/assets from selected topic features and aggregate sentiment using grouped five-fold Ridge/XGBoost cross-fitting. The adapters retain its formulas and settings. The `reproduce` profile refits from an explicit saved selection and compares with frozen outputs. `fresh` implements one new P0 triad before passing its selection through the same stages, but the current released inputs do not satisfy its preflight. Historical density ordering remains delivery-declared; these adapters do not establish independent construct validity.

The recorded numerical reproduction covers the original 25 downstream models, excluding the later submitted narrative benchmark and eight Table A13 models. It starts from saved representation and judgments; it does not regenerate topic discovery, sentiment or AI labels. See the [evidence scope](../../applications/ceo-risk-preference/EVIDENCE_SCOPE.md).

The fresh-screening API implementation keeps three independent reader histories. All three initial descriptor readings are sealed before source review starts. Each reader then reviews all 18 pages and 1,062 passages in its own history, without peer votes. A two-of-three Stage B majority preserves all reasons, minority votes and missingness; confidence does not weight votes. Interrupted or invalid attempts remain visible. The API acceptance policy is stricter than the historical native-reader importer: quotation and coverage defects that could remain flagged in archived votes halt the new adapter. It does not silently retry or repair a failed first response. Historical requested model/effort labels do not independently establish observed backend identities. This API route is not a rerun of the twelve-trial native-reader study.

## Configure an empirical run

For the packaged CEO case, use the [reviewer replication guide](../../applications/ceo-risk-preference/REPLICATION.md). Its detailed route downloads inventoried data, fitted models and saved reader evidence from repository releases and constructs the reproduction configuration automatically. Those assets support saved replay; they do not supply every canonical input required by the fresh-screening adapter. The exact refit uses Windows x64 and Python 3.11.7. These assets are not required for the demo. The manual configuration below is for inspecting or adapting the runtime; retain the packages’ inventories and internal structure.

1. Create the compatible **Python 3.11.7** analysis environment and install [requirements.txt](requirements.txt). The fixed versions match the delivered Step 3 models; the external full Step 4 package also documents its environment.
2. Place or reference your authorized inputs locally. Copy [reproduce.example.json](reproduce.example.json) or [fresh.example.json](fresh.example.json) into `.local/` and edit every input/runtime path. Paths resolve relative to the configuration file. The examples assume the copied configuration lives in `.local/`.
3. Set explicit `catalogue` and, for reproduction, `selection` paths. The selection must match the catalogue's identity and partition all 354 topics. `packages_root` must contain both named stage packages.
4. Only after supplying and verifying the complete missing fresh-input tree described below, set `step2.toolkit` to the compatible Python toolkit and `step2.packet_root` to the complete frozen packet directory containing `PACKET_MANIFEST.json`, `packets/` and `schemas/`. The adapter checks required files before model calls. Use your trusted study toolkit; it is executable code.
5. Configure `python` to the analysis interpreter. Stata estimation uses the version-19 do-file; the supplied results used Stata 19.5. Set `stata_exe` when estimation is ready. Explicit `stata_version: 18` uses a separate do-file with only its version declaration changed, retains the original, and requires the same numerical checks.

The saved-density mode is the default. Optional `step1.mode=infer` requires a compatible `ceo_rd` topic package and its dependencies installed in the configured analysis environment, plus the matching model and corpus. The implementation is included under `applications/ceo-risk-preference/study/representation`; its model and source assets are in the optional source/model release archive. That route needs the separately documented topic dependencies and is not part of saved-representation replay. It applies a fixed model; it does not retrain topic discovery or regenerate sentiment.

From the repository root, after configuration:

```sh
python3 -m agent_system.empirical --config .local/reproduce.json --out .local/reproduction --through step4_prepare
python3 -m agent_system.empirical --config .local/reproduce.json --out .local/reproduction
python3 -m agent_system.empirical --config .local/reproduce.json --out .local/reproduction --status
```

The first command prepares the downstream analysis; the second resumes estimation. Preparation can finish without Stata. Scientific configuration and input bindings must remain identical on resume. Stata's executable may be configured after preparation, before estimation completes; this change is logged.

## Fresh screening: implemented interface, incomplete released inputs

The actual released-input preflight failed with `ValueError` on 21 required files before any provider call. Missing inputs, relative to the restored toolkit root `evidence/runtime/data-analysis/`, are `packets/prompts/P0.md`, `packets/initial_addendum.md`, `packets/source_evidence.private.jsonl` and all 18 canonical pages from `packets/stageB/B01.json` through `B18.json`. All are absent from the release inventory. Repeating the same restore or obtaining model access does not supply them.

Saved-reader replay passed because it recalculates existing judgments through a different input route. The preflight harness exited 0 after recording the expected failure; the input check itself failed, with zero provider calls. Passing screening tests with fabricated complete packets does not establish fresh execution from released evidence.

The following command is an implementation-interface reference, **not a runnable route from the current release alone**. Before using it, supply a complete authorized packet tree, verify its identities and pass the actual no-call preflight. A live run additionally requires model availability, supported settings, permission to transmit source passages and authorized usage costs. No live run is verified by the current documentation review.

For model-coordinated execution, provide `OPENAI_API_KEY` through the environment and use `--agent`. Model/effort fields are configuration defaults, not immutable backend snapshots or guarantees of live availability.

```sh
python3 -m agent_system.empirical --config .local/fresh.json --out .local/fresh-run --agent
```

The coordinator uses `get_status`, `run_stage`, `read_result` and `finish`. Completion follows recorded stage status and checks of recorded artifact hashes; the scientific adapters also perform stage-specific checks. The generic dispatcher does not yet enforce every required artifact or recheck every input before each new stage. The standard reproduction wrapper rehashes restored package members; that protection should not be assumed for direct/manual routes. Synthetic diagnostics found these limits, not false completion of the recorded empirical run. Inspect expected outputs and preserve failed evidence. Keep separate output directories for changed scientific settings. See the [coordinator responsibilities](../../docs/agents/coordinator.md) and [roadmap](../../docs/ROADMAP.md).

## Software checks

These self-contained standard-library tests exercise the demo, coordinator and saved-state behavior:

```sh
python3 -m unittest agent_system.tests.empirical.test_demo agent_system.tests.empirical.test_coordinator agent_system.tests.empirical.test_workflow -v
```

After installing analysis dependencies, run the wider adapter suite:

```sh
python3 -m unittest discover -s agent_system/tests -v
```

Most adapter tests fabricate inputs and mock scientific execution. The full screening checks need `AI_MICROFOUNDATION_PROXY_SCREENING_TOOLKIT` pointing to the compatible external toolkit; they create invented packets and make no live calls. Two original-function checks need `AI_MICROFOUNDATION_PROXY_PACKAGES_ROOT` pointing to authorized complete packages. Those external checks are explicitly skipped when their inputs are absent. Passing software tests is distinct from empirical reproduction.
