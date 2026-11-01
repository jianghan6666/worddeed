# Repository guide

AI Microfoundation Proxy is a research framework with an application collection. Shared infrastructure and scientific applications have separate homes.

| Location | Purpose |
| --- | --- |
| [agent_system/](../agent_system/README.md) | Coordinator contracts, provider handling, stage execution, state and tests. The current empirical adapters implement the CEO case. |
| [docs/](README.md) | Shared workflow, roles, protocols, roadmap, introduction and guidance for developing another application. |
| [applications/](../applications/README.md) | Named applications, each with its own research specification, scientific material, findings and reproduction evidence. |
| [replication/](../replication/README.md) | Archive utilities and maintained execution drivers; current empirical drivers target the CEO application. |

The root [results](../RESULTS.md) and [replication](../REPLICATION.md) indexes direct reviewers to each application's deliverables. The first complete case lives in [applications/ceo-risk-preference/](../applications/ceo-risk-preference/README.md):

```text
README.md          Research question and four-step walkthrough
study/             Representation, screening, prediction and assessment packages
summary/           Selected aggregate findings for quick reading
results/           Complete reports, judgments, scores, tables and workbooks
replication/       Application inventories and executed verification receipts
RESULTS.md         Results guide and full archive download
REPLICATION.md     Environment, input downloads and exact execution commands
```

The scientific choices inside that folder belong to the CEO case. The framework's broader purpose is described in the [workflow](WORKFLOW.md) and [new-application guide](NEW_APPLICATION.md). New cases belong beside the CEO folder; an [application template](../applications/_template/README.md) identifies the required research and implementation decisions. It is a planning template, not another executable empirical study.

## Current implementation boundary

Reusable orchestration is implemented, and the CEO application has a verified connected empirical reproduction. The existing numerical adapters and empirical drivers contain CEO-specific package names, data fields, models and downstream formulas. Another application requires compatible adapters and its own scientific checks. A general application plug-in interface remains roadmap work.

Keep new inputs, restored packages and run outputs under ignored `.local/<application-name>/`. Each application documents access to its large datasets and models through inventoried private releases.

## Reading copies and languages

Some files exist in two places on purpose. The application's `study/` tree holds each supplied scientific package in the layout its own code and historical hashes expect. The `results/` tree is the reviewer presentation and carries copies of the reports, tables and audit files it needs. Where the same file appears in both, the copies are byte-identical. For example, the Step 2 analysis tables sit under both `study/screening/review/results/` and `results/step2/analyses/`, and the Step 4 historical audit files sit under both `study/assessment/full/audit/` and `results/step4/full/audit/`. The `results/` copies are inventoried and checked by `results/verify.py`; the `study/` copies are the supplied originals. Read either; edit neither.

The supplied Step 3 and Step 4 packages under `study/` were written in Chinese by the original collaboration, including their READMEs, method notes, data dictionaries and raw-data download ledgers. They are kept verbatim as scientific records. The English application README, results guide and replication guide summarize what they contain. Windows paths inside the ledgers refer to the machine that executed the original run, not to this checkout.

## Historical paths and frozen artifacts

[replication/paths.json](../replication/paths.json) maps the former root `study/`, `results/`, `examples/ceo-risk-preference/`, Step 2 and Step 3/4 delivery paths to the current application. The identity verifiers resolve historical source paths without rewriting scientific records. Previously exported Windows handoffs can use either former catalogue path or the current application path after checking the same file hash.

Frozen archives retain their original member names and hashes. A downloaded results ZIP still contains `results/`; restored empirical inputs still contain `packages/...`. Historical receipts and source documents describe the layout at their recorded execution. Use the selected application's current replication guide for commands in a new checkout. Prior release tags remain fixed.

Existing local runs can contain absolute paths into their original checkout. Resume them with that checkout, or start a new run directory with the current layout. The application move does not change scientific settings, labels, scores or estimates.
