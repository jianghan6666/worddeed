# Reviewer start here

AI Microfoundation Proxy is a framework for connecting narratives, relevance judgments, behavioral prediction and downstream assessment. [CEO risk preference](../applications/ceo-risk-preference/README.md) is its first complete application. The shared orchestration is reusable; the current numerical adapters implement that case. A new application needs its own scientific specification and compatible adapters; see [Adding an application](NEW_APPLICATION.md).

## Read the findings

Open the CEO application's [full results guide](../applications/ceo-risk-preference/RESULTS.md), [PDF report](../applications/ceo-risk-preference/results/report.pdf), and [file guide](../applications/ceo-risk-preference/results/README.md). They lead to all four stages, including the 354-topic catalogue, twelve screening trials, 29,506 firm-year scores and 25 downstream models. The [full results ZIP](https://github.com/jianghan6666/worddeed/releases/tag/full-results-2026-10-31) adds the literal reader evidence. Download and open HTML reports and topic browsers locally; GitHub displays their source.

The [replication package](../applications/ceo-risk-preference/REPLICATION.md) is a separate deliverable: data, model assets, saved judgments, executable code, environments and newly executed verification. Its [verified-output release](https://github.com/jianghan6666/worddeed/releases/tag/reviewer-replication-2026-10-31) lets you inspect the new run without fitting again.

## Get a fresh copy and check it

This repository and its release assets are private. The owner must grant your GitHub account access first. Sign in to GitHub, then use **Code → Download ZIP** and extract it, or clone with authenticated GitHub CLI:

```sh
gh auth login
gh repo clone jianghan6666/worddeed
cd worddeed
```

For a ZIP, open a terminal in the extracted folder containing `README.md`, `agent_system/` and `applications/`. The verification and reproduction scripts do not require `.git`. A source ZIP or clone includes the reading copies and full browsable results; large empirical inputs are downloaded separately from the private releases. Keep the downloaded folder writable because screening restore adds inventoried evidence beside its replay code.

With **Python 3.11+**, run these checks from that root. They use only the standard library and need no model account, Stata or empirical input download. On Windows, replace `python3` with `py -3.11`.

```sh
python3 replication/verify.py
python3 replication/verify_delivery.py
python3 applications/ceo-risk-preference/study/screening/review/verify.py
python3 applications/ceo-risk-preference/results/verify.py
```

Each command must exit successfully. The source and results verifiers report `passed: true`; the delivery and screening verifiers print their successful checks. They check 521 imported source identities, the supplied package inventory and handoff, screening review copies, and 375 result files. These are integrity checks, not a new scientific fit. For an optional orchestration demonstration, follow the [offline demo](../agent_system/empirical/README.md#run-the-self-contained-demo).

## What can be reproduced at each step?

| Step | What the maintained reproduction does | Evidence to inspect |
| --- | --- | --- |
| 1. Represent narratives | Loads the saved catalogue, density matrix and component metadata; checks their identities, dimensions and declared ordering. It does **not** retrain BERTopic or regenerate sentiment. The optional source/model archive preserves the upstream code, corpus and models. | [Topic outputs](../applications/ceo-risk-preference/results/step1/) and the run's `workflow/step1/` receipt. Historical unkeyed density alignment remains delivery-declared. |
| 2. Screen relevance | Recalculates both primary and supplementary analyses from saved reader records, exports every trial handoff and checks the selected 321-topic handoff against Step 3. It does **not** ask AI readers to judge again. | [Reader browser](../applications/ceo-risk-preference/results/step2/explorers/index.html), `screening/first/`, `screening/recovered/`; 122 analysis/handoff files checked. |
| 3. Estimate the proxy | Rebuilds the 29,506-row panel and refits Ridge and XGBoost with the original grouped folds and settings. | New `workflow/step3/` scores and validation metrics. The [supplementary command](../applications/ceo-risk-preference/REPLICATION.md#additional-supplied-analyses) runs saved-model and seed checks too. |
| 4. Assess the proxy | Reconstructs financial/matching data from the supplied raw inputs, passes the **new** Step 3 scores forward, and estimates all 25 models in Stata. | `workflow/step4_prepare/` model inputs and audits, estimation reports and final `REPRODUCTION.json`. Preparation alone is not completed estimation. |

The accepted [connected verification](../applications/ceo-risk-preference/replication/verification/CONNECTED_REPRODUCTION.json) covers this chain. It is a reproduction from saved representation and judgments, not a raw-speech-to-new-AI-judgments rerun. Original topic training, fresh AI screening and independent construct validation have different evidence requirements.

## Choose the execution route

- **Replay Step 2 on any supported desktop:** the following commands download about 52 MB and restore about 239 MB of reader evidence, then recalculate and compare the saved analyses. They require authenticated `gh` and Python 3.11+, but no numerical packages or model calls. Allow at least 1 GB of free working space for this review route, including extracted files and replay outputs. Use a new output directory.

```sh
gh release download reviewer-replication-2026-10-30 --repo jianghan6666/worddeed --pattern step2-twelve-evidence-2026-10-21.tar.gz --dir .local/downloads
python3 applications/ceo-risk-preference/study/screening/experiment/results-2026-10-21/restore.py --archive .local/downloads/step2-twelve-evidence-2026-10-21.tar.gz
python3 replication/replay_screening.py --out .local/screening-review
python3 applications/ceo-risk-preference/study/screening/experiment/results-2026-10-21/verify_replay.py --out .local/screening-review
```

- **Run the complete maintained chain:** follow [Fresh checkout and core reproduction](../applications/ceo-risk-preference/REPLICATION.md#fresh-checkout-and-core-reproduction). Use Windows x64, Python **3.11.7**, all pinned requirements and compatible Stata. Core inputs are about **1.18 GB compressed**, with about **1.46 GB of restored inputs/evidence**, plus the environment and generated fits. Allow additional working space; the optional source/model bundle adds about 2.9 GB compressed and 9.2 GB expanded. An exact Mac ARM64 XGBoost refit did not pass and is not a substitute for the verified Windows route.
- **Prepare on Windows, estimate elsewhere:** the [split-runtime instructions](../applications/ceo-risk-preference/REPLICATION.md#windows-preparation-and-local-stata-continuation) explain the Windows workflow and local Stata continuation. GitHub Actions dispatch requires repository write access; a read-only reviewer can run the local Windows commands or inspect the permanent verified-output release. Actions artifacts are temporary; the release is the durable review copy.

Use Stata 19 for the original version declaration, or explicitly choose the verified `--stata-version 18` compatibility route. Without Stata, `--through step4_prepare` stops before estimation; the same run can later continue with Stata. Successful stages are checked before reuse. A final complete run must show `status: "complete"` and all five workflow stages (`step1`, `step2`, `step3`, `step4_prepare`, `step4`) complete in `REPRODUCTION.json`.

The [verification index](../applications/ceo-risk-preference/replication/verification/README.md) separates historical findings, accepted new fits, failed diagnostics and software-only checks. Prediction, screening agreement and conditional associations do not establish psychological construct validity or causal effects.
