# Ratified twelve-trial Step 2 study

**Scope amendment 3, ratified 21 October 2026 after collection.** The current study is the completed **12-trial P0 cohort: two models × three efforts × two repetitions**, with three independent readers per trial. The human instructed: “the 12 trial plan should be our ratified plan” and authorized pushing and merging its results. [Ratification record](RATIFICATION.json) · [results and measured usage](results-2026-10-21/README.md) · [exact schedule](SCHEDULE.json).

This is a post-collection scope decision. The original revision-9 design scheduled 84 trials across P0–P6. Following cost concerns during collection, the human stopped admissions after the first 12 ordered P0 trials, let their existing 36 readers finish, and then ratified these 12 as the study. The other **72 trials were never admitted and are superseded historical work**, not failed trials or remaining obligations. The [original scientific schedule](historical/revision-9-SCHEDULE.json) and [amendment-2 plan](historical/amendment-2/PLAN.md) remain unchanged historical records. Do not describe this reduction as prospective preregistration or coauthor approval.

## Scope and question

Describe how topic selection, repeatability, confidence and evidence support vary between two requested models and three requested effort settings, and between initial descriptor judgments and subsequent source review. Only P0 was run; **prompt-strategy effects cannot be estimated**. The earlier [19 October descriptor-only pilot](../comparison-2026-10-19/comparison.md) remains a separate exploratory study, with its original outputs intact.

| Design element | Ratified scope |
|---|---|
| Topic universe | Fixed, ordered 354-topic Step 1 catalogue |
| Requested models | `gpt-6.1-sol`, `gpt-6-astra` |
| Requested effort | `medium`, `high`, `xhigh` in both repetitions |
| Initial prompt | Frozen [P0 direct prompt](prompts/P0-direct.md) and [output addendum](READER_OUTPUT_ADDENDUM.md) |
| Repetitions | Two fresh three-reader trials per model–effort cell; six cells, 12 trials |
| Reader independence | 36 fresh native chats; each reader keeps its own chat through both stages |
| Logical stage records | 72: 36 Stage A and 36 Stage B |
| Intended topic rows | 12,744 per stage; 25,488 across both stages, excluding supplementary attempts |
| Source review | 1,062 frozen representative passages; 18 ordered pages per reader, 648 page dispositions |
| Current execution | Completed; no new seats, replacements, retries or trial admissions authorized |

Stages and topics within a reader are paired observations, not additional independent trials. Logical stage counts are not model-call or billing counts. Settings are requested native-chat settings; backend versions and actual effort are not independently verified.

## Frozen procedure

1. **Stage A:** each reader labels every topic from its name and ranked keywords, with a reason, exact keyword evidence, confidence and confidence reason. No source passages, peer answers or earlier pilot outcomes are supplied.
2. **Per-trial barrier:** all three initial attempts are sealed or explicitly missing before source release. Each reader sees only its own initial response.
3. **Stage B:** the same reader, model and effort review all three representatives for every topic under the frozen [common review prompt](SOURCE_REVIEW_PROMPT.md), including initially excluded topics. Retain the exact bounded transport, complete current-page reload after observed compaction, source attribution limits, interpretation checks, literal reasons, confidence and changes. All 18 page dispositions are preserved.
4. **Final vote:** two matching resolved Stage B votes out of three decide; confidence is not a weight. Stage A majority is reported separately. There is no initial-label fallback, negative fill, coordinator vote, label-driven retry or substitution of inferred judgments.

The coordinator directly dispatched readers and owned seals, releases, assemblies and analysis. There is no CMD layer. [Seat plan](SEAT_PLAN.md) and [closed dispatch record](startup-promptwise/README.md) document the completed execution. Exact scientific prompts, schemas, catalogue, source text and original sealed local records remain unchanged by this scope amendment. The shared export identifies administrative redactions and preserves scientific fields.

## Results and analysis contract

All 12 workflows and 36 readers finished. Completion does not mean every first save was valid: primary Stage B contains **12,624 of 12,744 rows**, with 120 absent rows from six failed/malformed first page saves across five readers. Seven trials have fully present primary review records; five retain missingness. The supplementary recovered analysis contains all 12,744 rows. Stage A contains all 12,744 rows, including five abstentions. Preserve both variants; 51 page recovery pairs, 52 supplementary page attempts and four unapplied errata are disclosed.

Primary final totals across 4,248 trial-topic decisions are **3,795 relevant, 452 irrelevant and one unresolved**. Supplementary totals are 3,796, 452 and zero. These are repeated decisions on 354 topics, not 4,248 unique topics. Report per-trial selection, individual votes and minority reasons, coverage, within-cell repeats, matched model/effort contrasts, positive/negative agreement, Jaccard, confidence and paired A→B changes with their denominators. No pooled “best” classifier or new single handoff is adopted.

Use the existing frozen toolkit and analyzer, with the documented portable cohort adapter for this export. The adapter limits scheduled rows and comparison loops to the ratified cells; it does not change voting, validation or reader judgments. Reconcile against the frozen full-grid analysis for all observed P0 comparisons. Preserve first attempts as primary and explicitly indexed latest recoveries as supplementary.

## Interpretation, cost and next decision

Stage B selects 313–321 topics per trial, versus 66–87 in Stage A. This broadening needs substantive review against the unchanged relevance rule. Agreement, confidence and successful execution do not establish accuracy or construct validity. Three masked/processed representatives illustrate rather than exhaust a topic, and are not all independently verified CEO speech. Source review combines text access, reconsideration and anchoring, so it does not identify a causal effect of adding text.

Ordered admission, overlapping workload, service interruptions and the account switch confound model/effort comparisons with time and environment. Two repetitions give descriptive evidence with limited precision. Scope reduction followed cost concerns and was ratified after results were available. One coordinator-guide access deviation remains flagged; literal votes are retained. The prior ten synthetic toolkit tests do not constitute a final independent revision-9 QA pass or human-reference validation. Remaining evidence-format defects are disclosed in the results.

The observed reader usage span was about 8.13 hours including overlaps, waits and the account-switch pause. Native counters record 3.291 billion input tokens (96.65% cached) and 11.734 million output tokens across the 36 readers; they are not a bill or subscription-allowance measurement. Review results and measured usage alongside the earlier pilot before any later extension. No additional collection is part of this ratified plan.
