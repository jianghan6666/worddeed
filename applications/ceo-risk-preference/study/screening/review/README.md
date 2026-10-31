# Step 2 twelve-trial pilot

**Start here for the completed 21 October 2026 pilot and its Step 3 inputs.** All 12 P0 trials and 36 readers finished. This folder contains the coauthor memo, workflow figure, frozen catalogue and prompts, all Git-delivered analysis tables, and both variants of every trial’s output. Full reader/source evidence is available through the linked private release. The final scope was ratified after collection.

## Reading and use

1. Read the [coauthor memo](MEMO.md) for the task, procedure, exact executed prompts, seven-strategy plan, completed P0 results, interpretation and next steps. The [formatted HTML](MEMO.html) is self-contained: download/open it locally; GitHub displays its source.
2. Inspect the [workflow figure](procedure.svg) ([editable Mermaid source](procedure.mmd)). Each reader keeps the same chat through Stage A and Stage B.
3. For downstream work, follow the [Step 3 handoff guide](STEP3_HANDOFF.md), then choose an explicitly recorded trial and analysis variant from the table below. **No preferred trial or pooled topic selection has been adopted.**
4. Use [data and evidence access](DATA_AND_EVIDENCE.md) for source passages, literal reader judgments, full provenance, historical density data and offline reproduction.

## Where the files are

| Material | Location | Use |
|---|---|---|
| Memo and procedure graph | [MEMO.md](MEMO.md), [procedure.svg](procedure.svg) | Coauthor interpretation and review |
| Step 3 instructions | [STEP3_HANDOFF.md](STEP3_HANDOFF.md) | Trial selection, topic IDs, density binding, missingness |
| Trial inventory and file paths | [TRIAL_INDEX.csv](TRIAL_INDEX.csv), [TRIAL_INDEX.json](TRIAL_INDEX.json) | All 12 trials × two analysis variants |
| Primary final classifications and IDs | [results/primary/handoffs/](results/primary/handoffs/) | First submissions; preserve one unresolved majority |
| Supplementary final classifications and IDs | [results/supplementary/handoffs/](results/supplementary/handoffs/) | Explicitly indexed recoveries; no unresolved majorities |
| Counts, agreement, transitions, coverage and diagnostics | [results/primary/](results/primary/), [results/supplementary/](results/supplementary/) | All published analysis tables; Stage A remains separate |
| Fixed topic catalogue | [inputs/catalogue.json](inputs/catalogue.json) | Topic IDs, names, keywords and model identity |
| Exact candidate and executed prompts | [protocol/](protocol/README.md) | Seven planned Stage A strategies; P0 alone executed |
| Recorded reader usage | [USAGE.json](USAGE.json) | Native counters and elapsed span; not a monetary bill |
| File identity and evidence locations | [MANIFEST.json](MANIFEST.json), [DATA_AND_EVIDENCE.md](DATA_AND_EVIDENCE.md) | Source-copy hashes and restoration instructions |

## Trial outputs

Every output directory contains `selected_topics.json`, `topic_labels.csv` and `initial_topic_labels.csv`. Counts are final Stage B majority selections out of 354. Primary and supplementary results are separate analyses of the same 12 trials, not 24 trials.

| Trial | Model / effort / repetition | Primary selected | Supplementary selected | Outputs |
|---|---|---:|---:|---|
| `b1-gpt-6-astra-P0-medium` | gpt-6-astra / medium / 1 | 316 | 316 | [Primary](results/primary/handoffs/b1-gpt-6-astra-P0-medium) · [Supplementary](results/supplementary/handoffs/b1-gpt-6-astra-P0-medium) |
| `b2-gpt-6-astra-P0-medium` | gpt-6-astra / medium / 2 | 316 | 316 | [Primary](results/primary/handoffs/b2-gpt-6-astra-P0-medium) · [Supplementary](results/supplementary/handoffs/b2-gpt-6-astra-P0-medium) |
| `b1-gpt-6-astra-P0-high` | gpt-6-astra / high / 1 | 317 | 317 | [Primary](results/primary/handoffs/b1-gpt-6-astra-P0-high) · [Supplementary](results/supplementary/handoffs/b1-gpt-6-astra-P0-high) |
| `b2-gpt-6-astra-P0-high` | gpt-6-astra / high / 2 | 317 | 317 | [Primary](results/primary/handoffs/b2-gpt-6-astra-P0-high) · [Supplementary](results/supplementary/handoffs/b2-gpt-6-astra-P0-high) |
| `b1-gpt-6-astra-P0-xhigh` | gpt-6-astra / xhigh / 1 | 321 | 321 | [Primary](results/primary/handoffs/b1-gpt-6-astra-P0-xhigh) · [Supplementary](results/supplementary/handoffs/b1-gpt-6-astra-P0-xhigh) |
| `b2-gpt-6-astra-P0-xhigh` | gpt-6-astra / xhigh / 2 | 315; 1 unresolved | 316 | [Primary](results/primary/handoffs/b2-gpt-6-astra-P0-xhigh) · [Supplementary](results/supplementary/handoffs/b2-gpt-6-astra-P0-xhigh) |
| `b1-gpt-6.1-sol-P0-medium` | gpt-6.1-sol / medium / 1 | 313 | 313 | [Primary](results/primary/handoffs/b1-gpt-6.1-sol-P0-medium) · [Supplementary](results/supplementary/handoffs/b1-gpt-6.1-sol-P0-medium) |
| `b2-gpt-6.1-sol-P0-medium` | gpt-6.1-sol / medium / 2 | 314 | 314 | [Primary](results/primary/handoffs/b2-gpt-6.1-sol-P0-medium) · [Supplementary](results/supplementary/handoffs/b2-gpt-6.1-sol-P0-medium) |
| `b1-gpt-6.1-sol-P0-high` | gpt-6.1-sol / high / 1 | 316 | 316 | [Primary](results/primary/handoffs/b1-gpt-6.1-sol-P0-high) · [Supplementary](results/supplementary/handoffs/b1-gpt-6.1-sol-P0-high) |
| `b2-gpt-6.1-sol-P0-high` | gpt-6.1-sol / high / 2 | 316 | 316 | [Primary](results/primary/handoffs/b2-gpt-6.1-sol-P0-high) · [Supplementary](results/supplementary/handoffs/b2-gpt-6.1-sol-P0-high) |
| `b1-gpt-6.1-sol-P0-xhigh` | gpt-6.1-sol / xhigh / 1 | 318 | 318 | [Primary](results/primary/handoffs/b1-gpt-6.1-sol-P0-xhigh) · [Supplementary](results/supplementary/handoffs/b1-gpt-6.1-sol-P0-xhigh) |
| `b2-gpt-6.1-sol-P0-xhigh` | gpt-6.1-sol / xhigh / 2 | 316 | 316 | [Primary](results/primary/handoffs/b2-gpt-6.1-sol-P0-xhigh) · [Supplementary](results/supplementary/handoffs/b2-gpt-6.1-sol-P0-xhigh) |

## Interpretation and integrity

Stage A selected 66–87 topics per trial; Stage B selected 313–321. Primary totals are 3,795 relevant, 452 irrelevant and one unresolved across 4,248 trial–topic decisions; supplementary totals are 3,796, 452 and zero. These classifications are candidate inputs for Step 3, not a validated firm-level risk-preference measure. The [memo](MEMO.md#5-execution-findings-and-interpretation) reports missingness, recoveries, usage and limitations.

The result files, catalogue and prompts here are byte-identical copies, indexed in [MANIFEST.json](MANIFEST.json), of the [canonical frozen result package](../step-2-mvp-simple/experiment/expanded-ai-pilot/results-2026-10-21/README.md). In copied JSON, `reader_records_package_relative` remains relative to that original evidence-package root; [TRIAL_INDEX.json](TRIAL_INDEX.json) supplies that root explicitly. No reader vote, reason, input binding or missing disposition has been changed.

From the repository root, verify the delivery without model calls:

```sh
python3 step-2-twelve-trial-pilot/verify.py
```

See the [ratified plan](../step-2-mvp-simple/experiment/expanded-ai-pilot/PLAN.md) for scope. Further trials require a separate decision; none are launched by these files or verification commands.
