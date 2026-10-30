# Twelve-trial Step 2 results and measured usage

**All 12 trials and 36 original readers finished; all 648 source-review page dispositions are terminal.** The human ratified these 12 P0 trials as the study after collection on 21 October 2026. The other 72 originally scheduled trials were never admitted and are superseded historical work. No new seats are authorized. [Ratified plan](../PLAN.md) · [scope decision](../RATIFICATION.json) · [record index](RECORD_INDEX.json).

Stage B selects **313–321 of 354 topics per trial**, compared with **66–87 in descriptor-only Stage A**. That broadening is the main finding to review against the unchanged risk-relevance rule. High agreement does not establish that the broader selections are correct. No human-reference accuracy or construct-validity claim is made, and no winning classifier or single preferred handoff is adopted.

## Results by model and effort

The two numbers in each cell are repetition 1 / repetition 2. Counts refer to majority-selected topics out of 354. Primary analysis uses first saves, preserving missingness; the recovered variant is supplementary.

| Requested model | Effort | Stage A selected | Stage B primary selected | Stage B supplementary selected |
|---|---|---:|---:|---:|
| GPT-6.1 Sol | Medium | 70 / 68 | 313 / 314 | 313 / 314 |
| GPT-6.1 Sol | High | 70 / 66 | 316 / 316 | 316 / 316 |
| GPT-6.1 Sol | Xhigh | 72 / 66 | 318 / 316 | 318 / 316 |
| GPT-6 Astra | Medium | 76 / 77 | 316 / 316 | 316 / 316 |
| GPT-6 Astra | High | 85 / 87 | 317 / 317 | 317 / 317 |
| GPT-6 Astra | Xhigh | 84 / 82 | 321 / 315* | 321 / 316 |

\* Repetition 2 Astra Xhigh has one unresolved primary majority, topic 224: reader A is missing, B votes irrelevant and C relevant. The explicitly indexed recovery supplies A's relevant vote. The primary row remains unresolved.

Across 4,248 trial-topic decisions, primary final totals are **3,795 relevant, 452 irrelevant and one unresolved**; supplementary totals are **3,796 relevant, 452 irrelevant and zero unresolved**. These are repeated decisions on 354 topics. Across the 12 primary outputs, 306 topics are always selected, 31 always excluded and 17 vary, including the topic with primary missingness.

Among 4,247 jointly resolved A→B majority comparisons, **2,964 change (69.79%)**: 2,928 irrelevant→relevant and 36 relevant→irrelevant. Strict within-cell Stage B repeat agreement is 98.09–98.87%, using 314 or 354 topics where all three votes are resolved in both repetitions. Supplementary strict repeat agreement is 98.31–98.87%, with all 354 topics. These denominators and positive/negative agreement, Jaccard, constituent comparisons and matched model/effort contrasts are retained in the [primary analysis](analysis/first/paired_comparisons.csv) and [supplementary analysis](analysis/recovered/paired_comparisons.csv).

## Completion, missingness and recovery

| Quantity | Primary first attempts | Supplementary recovered |
|---|---:|---:|
| Saved logical A/B records | 72 / 72 | 72 / 72 |
| Stage A topic rows | 12,744; five abstentions | Same |
| Stage B topic rows | 12,624 / 12,744 | 12,744 / 12,744 |
| Stage B rows absent | 120 | 0 |
| Readers with full Stage B roster | 31 / 36 | 36 / 36 |
| Trials with all three full review rosters | 7 / 12 | 12 / 12 |
| Unresolved final trial-topic majorities | 1 | 0 |
| Mechanical flags in Stage B | 62 | 12 |

Six malformed/failed first page saves across five readers account for the 120 absent primary rows. The study preserves **51 page recovery pairs, 52 supplementary page attempts and four unapplied reader errata** in the [recovery ledger](evidence/runtime/direct/RECOVERIES.json). Recovery is not a clean replacement of the primary data. First saves, parsed records, explicit missing dispositions, original hashes, literal recovery files and links remain available through the [record index](RECORD_INDEX.json) and [provenance inventory](PROVENANCE.json).

The primary flags comprise 10 passage-coverage, 30 quotation, 17 keyword and five roster flags. The supplementary flags comprise one passage-coverage, nine quotation and two keyword flags. These are mechanical diagnostics, not a count of semantically wrong labels; no votes were silently edited or excluded because of them. Inspect [primary defects](analysis/first/mechanical_defects.private.json) and [supplementary defects](analysis/recovered/mechanical_defects.private.json) with the exact reader reasons.

One [protocol deviation](evidence/runtime/direct/PROTOCOL_DEVIATIONS.json) concerns repetition 1 Astra High reader B accessing a coordinator-only methodology guide after saving B09, following observed compaction and before the full recovery reload. The reader reported no peer judgments or earlier pilot outcomes accessed; that timing was not independently verified. B09 and subsequent pages remain flagged. Original votes are retained, without regeneration or silent exclusion.

## Inspect the handoffs and scientific records

The [primary handoffs](analysis/first/handoffs/) and [supplementary handoffs](analysis/recovered/handoffs/) contain one directory per trial. Each has:

- `topic_labels.csv`: Stage B final label, all three votes, minority and missing-reader indicators for all 354 topics.
- `selected_topics.json`: relevant, irrelevant and unresolved IDs bound to topic-model, catalogue, prompt and source identities, with package-relative links to every selected reader record.
- `initial_topic_labels.csv`: the separately reported Stage A majority and votes. It never supplies fallback votes to Stage B.

Each linked reader record preserves the authored rationale, exact keyword evidence, confidence/reason, source excerpts, interpretation assessment and retention/change reason. Minority judgments are preserved in full. Page seals link each assembled review to its literal page attempts; original and export SHA-256 values distinguish unchanged scientific content from redacted administrative metadata. There are no coordinator votes, negative fills or confidence weights.

The fixed [catalogue](evidence/runtime/data-analysis/packets/catalogue.json) and [source packet](evidence/runtime/data-analysis/packets/source_packet.private.json) retain the supplied text and attribution. Three representatives illustrate rather than exhaust a topic. Text is masked/processed and not a complete unmodified call; delivered CEO flags are not independent role verification, and duplicate source matches remain explicit. Do not interpret relevance as the risk direction of a person or use these lists with a different density-column identity.

## Measured usage and cost limits

The [usage record](USAGE.json) sums the last cumulative native counter from each of the 36 unique reader sessions, without summing repeated cumulative events. Counter decreases were checked; none were found. Cached input is already part of input tokens; reasoning output is already part of output tokens.

| Reader counter | Observed total |
|---|---:|
| Input tokens | 3,291,128,094 |
| Cached input tokens | 3,180,908,544 (96.65% of input) |
| Input minus cached input | 110,219,550 |
| Output tokens | 11,734,335 |
| Reasoning output, included above | 1,028,668 |
| Native compaction records | 316 |

The observed reader usage span is **20 October 23:25:58 UTC to 21 October 07:33:47 UTC**, about **8.13 hours**. This includes concurrent work, waits and pauses; it is not summed active compute time. The recorded human pause/resume-authority interval was about 23.8 minutes, not a precise authentication or per-reader inactivity interval. The account identity was not collected.

A separate coordinator snapshot through 07:34:48 UTC records 143,239,581 input tokens (141,105,152 cached) and 479,739 output tokens. Later integration work is outside that snapshot. Earlier coordinators, CMD/support work and the earlier pilot are also excluded. Native counters do **not** establish money charged or subscription allowance consumed, so no currency total or pilot/current cost ratio is inferred. Per-reader and model/effort breakdowns remain in the usage record.

## Interpretation and next review

Only P0 was run. There is no prompt-strategy comparison, and two repetitions give limited precision. Admission order, overlapping load, service interruptions and the account switch can confound model/effort differences with time and environment. Stage B combines text access, re-examination and anchoring after Stage A. Larger selections and A→B changes do not establish improvement or a causal passage effect. Topics within a chat are not independent replications; confidence is uncalibrated ordinal self-report.

The [earlier 19 October pilot](../../comparison-2026-10-19/comparison.md) remains separate: 12 descriptor-only conditions, 36 readers and selections of 54–95 topics. Ordered topic IDs, names, keywords and model identity match, but P0 workflow wording, the confidence addendum, schemas and wrappers differ. It is not an isolated experimental contrast with the present cohort. See [comparability evidence](evidence/runtime/direct/EARLIER_PILOT_COMPARABILITY.json).

Review representative inclusions and exclusions, minority reasons, the large source-review broadening and actual usage before proposing another study. Scope reduction followed cost concerns during collection and was ratified after outcomes were available. The current plan is complete; further seats require a separate human instruction.

## Offline replay and verification scope

The detailed evidence and two large reader-transition tables are delivered as a [private release bundle](https://github.com/joyzhzh/narrative-behavior-measurement/releases/tag/step2-twelve-trials-2026-10-21), following the repository's large-artifact convention. [BUNDLE.json](BUNDLE.json) inventories every member and its SHA-256. Links into `evidence/` and the two `reader_stage_changes.private.csv` tables refer to restored local files. The Git tree contains the plan, scientific summaries, handoffs, portable code and provenance manifests; full native chat logs are not included.

From the repository root, with access to this private repository, download the bundle using the signed-in GitHub CLI (or the release page), then restore it:

```sh
gh release download step2-twelve-trials-2026-10-21 --repo joyzhzh/narrative-behavior-measurement --pattern step2-twelve-evidence-2026-10-21.tar.gz --dir .local/twelve-bundle
python3 step-2-mvp-simple/experiment/expanded-ai-pilot/results-2026-10-21/restore.py --archive .local/twelve-bundle/step2-twelve-evidence-2026-10-21.tar.gz
```

The restore verifies archive and member hashes, allows only regular files inside the package and refuses to overwrite different local files. With Python 3.9+, replay the saved evidence with **no model calls**:

```sh
python3 step-2-mvp-simple/experiment/expanded-ai-pilot/results-2026-10-21/replay.py --out .local/twelve-trial-replay
python3 step-2-mvp-simple/experiment/expanded-ai-pilot/results-2026-10-21/verify_replay.py --out .local/twelve-trial-replay
```

Use a new output directory. The [frozen toolkit](evidence/runtime/data-analysis/toolkit.py) and [original analyzer](evidence/runtime/data-analysis/analyze.py) remain byte-identical. [cohort_analysis.py](cohort_analysis.py) differs from that analyzer only in two comparison loops, which enumerate present prompts rather than assume all seven. [replay.py](replay.py) resolves portable paths and supplies the ratified 12-job schedule during analysis; it does not change the collection schedule or sealed scientific fields. All observed P0 trial results and matched contrasts are reconciled to the original full-grid analysis. The original full-grid summaries are historical provenance: their 432 unrecorded stage slots belong to 72 never-admitted trials, not failed attempts.

The export preserves 1,938 JSON files containing identical scientific label arrays, plus linked literal fragments and observations; administrative paths/session identifiers are redacted or replaced by stable trial/reader aliases. [PROVENANCE.json](PROVENANCE.json) records original/export hashes and transformations. The original source-passage text is unchanged. Native full conversations, account identifiers, credentials, meeting recordings and meeting transcripts are excluded. Shared source material remains inside the authorized private repository.

The prior [ten synthetic toolkit fixtures](evidence/runtime/data-analysis/TEST_RESULTS.json) and [code-identity check](evidence/runtime/direct/ANALYSIS_CODE_IDENTITY.json) concern technical behavior. The portable replay checks scientific-result preservation and reproducibility from these saved records. Neither constitutes a final independent revision-9 scientific QA pass, human-reference accuracy assessment or construct validation. Pre-ratification [collection snapshots](collection-snapshot/) retain their original hold wording as history; the current [ratification](../RATIFICATION.json) governs scope.
