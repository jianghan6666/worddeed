# WordDeed: detailed reading guide

Start with the [project README](../README.md) and [workflow](WORKFLOW.md) to understand the measurement problem and four stages. This guide supplies evidence boundaries and optional reading routes for researchers and AI assistants. It describes the reviewed repository and release state on 2 November 2026; later revisions should be checked against their own files and receipts.

## Choose a reading route

| Purpose | Sources |
| --- | --- |
| Understand the design | [Workflow](WORKFLOW.md), then the [research roadmap](ROADMAP.md). Distinguish proposed validation from completed evidence. |
| Plan a new study | [Application guide](NEW_APPLICATION.md) and [planning template](../applications/_template/README.md). Specify the construct, unit and period, narrative source, behavioral anchor, external criterion, and compatible adapters. |
| Examine the proof of concept | [CEO case](../applications/ceo-risk-preference/README.md), then [results](../applications/ceo-risk-preference/RESULTS.md). |
| Check execution or reproduce results | [Replication instructions](../applications/ceo-risk-preference/REPLICATION.md), [verification records](../applications/ceo-risk-preference/replication/verification/README.md), and [empirical runtime documentation](../agent_system/empirical/README.md). Read the scope below before choosing a route. |

## What the implementation supports

The current shared workflow retains topic judgments and stage records. The numerical adapters implement the CEO case. Retaining alternative judgments does not establish that their effects have been propagated through every predictive and empirical specification. A new application requires scientific choices and compatible adapters.

The historical representation was trained on 887,488 components selected for nonmissing political-donation ideology scores from a broader corpus of 5,765,638 components. It was not trained on the entire corpus or on a CEO-only corpus. Historical topic-density alignment remains delivery-declared. The implemented predictive mapping uses selected topic densities and one overall sentiment feature, without firm controls or fixed effects; it differs from broader intended specifications.

Missing R&D is assigned zero in target construction. The adopted topic set followed preliminary performance inspection. The scores used in the dividend assessment are out-of-fold predictions, but the representation predates those folds and includes held-out text. Those facts qualify claims about missingness and independent validation. Agreement among readers, prediction of R&D, conditional dividend associations, and psychological construct validity are distinct kinds of evidence. Shared firm conditions may explain common variation.

## Execution and reproduction scope

| Route | Supported scope | Boundary |
| --- | --- | --- |
| Offline demonstration | Coordinator, stage handoffs, state checks and resume logic with explicit fixtures. | No model calls, empirical training or statistical estimation; output records `scientific_completion: false`. |
| Saved-judgment replay | Reads archived reader evidence and regenerates the recorded screening outputs. | Does not obtain new judgments from a live model. |
| Recorded numerical reproduction | Starts with saved topic representation and reader judgments, refits prediction models, and estimates the original 25 dividend models. | Does not regenerate topics, sentiment or AI judgments. The accepted route uses Windows x64, Python 3.11.7 with pinned dependencies, and compatible Stata estimation. The recorded Mac ARM64 XGBoost refit failed the strict reproduction comparisons. |
| Fresh API screening | An adapter exists for new reader judgments. | The current release lacks 21 required input files. Its input check fails before any provider call. Tests that supply fixtures do not establish that this route runs from the release alone. |

The original numerical chain contains 9 baseline and 16 score models. Additional narrative-benchmark results reported in the submitted appendix, including Table A13, are outside that reproduction record. Do not describe that receipt as verification of the additional models, or as a complete regeneration of the measurement pipeline. Submitted documents may be supplied separately for editorial review; this guide does not bundle or link them.

Large inputs are distributed separately as release assets. Public availability does not remove source-specific data terms or grant an open-source license. A website deployment and a repository revision may also differ. Cite the revision and files actually inspected.

## Optional AI reading prompt

```text
Read README.md and docs/WORKFLOW.md. Explain the measurement problem,
how the four steps address it, what AI contributes, and what another
researcher would need to adapt the workflow. Retain the author's terms,
including behavioral and narrative cues, predicted common variation,
and synthesized proxy. Use the CEO case only as a brief illustration.
Separate demonstrated capabilities from proposed work, and identify the
most important limitation. Cite repository paths and the revision inspected.
Offer optional follow-ups on case evidence or replication, using
docs/AI_READING_GUIDE.md for the relevant routes and evidence boundaries.
If I supply submitted documents separately, compare them with the
implementation and report conflicts; do not assume they are bundled.
Do not run models or call external services for this reading task.
```
