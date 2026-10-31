# Outputs and source traceability

**Scientific protocol revision 9; current scope amendment 3, ratified after collection on 21 October 2026.** The completed [plan](PLAN.md) contains 12 P0 trials and 36 original readers. This contract describes the frozen two-stage procedure; it authorizes no new execution. The separate 19 October descriptor-only pilot remains immutable.

## Initial and reviewed classification records

**Stage A:** supply the frozen P0 template, same descriptor catalogue and [initial-output addendum](READER_OUTPUT_ADDENDUM.md). Seal the complete initial response before passage access. **Stage B:** continue the same reader's private standalone chat with its own initial response, the [common review prompt](SOURCE_REVIEW_PROMPT.md) and identical frozen source passages/attribution. All three initial attempts must be sealed or explicitly missing before review begins; neither peer outputs nor either majority are shown until all reviews are sealed. The executed P0 preserves the historical risk codebook while clarifying initial versus reviewed voting and the Step 3 handoff; it is not byte-identical to the historical prompt. The ratified cohort contains **12 trials / 36 readers**, producing **72 reader-stage responses** and an intended **12,744 topic rows per stage / 25,488 total**; primary missingness remains disclosed. These are paired stages, not extra independent readers or trials.

For each of 354 topics, each reader supplies these fields separately at both stages:

| Field | Requirement |
|---|---|
| `topic_id` | Exact supplied topic ID, preserved as a string. |
| `status` | `resolved`, `abstain` or `failed`. |
| `label` | `relevant` or `irrelevant` for resolved rows; otherwise null. |
| `rationale` | Concise, topic-specific justification for the label or reason no label can be given. |
| `evidence_keywords` | One to five distinct exact supplied keywords for resolved rows. They anchor the descriptor interpretation; Stage B passage citations can expose its limitations. Missing decisions must not acquire invented support. |
| `confidence_level` | `high`, `medium`, `low`, or null when unresolved at reader level, using the common rubric. |
| `confidence_reason` | Concise explanation of the evidence sufficiency or ambiguity underlying confidence; explain missing confidence explicitly. |

Stage B adds these fields:

| Field | Requirement |
|---|---|
| `reviewed_passage_ids` | IDs of all supplied passages actually checked for this topic. The planned set is the three saved representatives; preserve any missing/unread passage as a coverage defect. |
| `evidence_passages` | For each cited item, a supplied `passage_id` and exact excerpt, linked to retained text/hash and candidate source identifiers. Resolved reviews require at least one supporting excerpt and must discuss material contrary evidence. Exact quotation checks are mechanical, not proof of support. |
| `topic_interpretation_assessment` | `supported`, `mixed`, `not_supported` or `insufficient_evidence`: fit between topic descriptors and supplied passages, separate from the binary relevance label. |
| `interpretation_reason` | Why the passages support, complicate or fail to establish that topic interpretation. |
| `review_action` | `retained` for the same resolved label; `revised` for a changed resolved binary label; `newly_resolved` if the initial judgment was missing/abstained/failed and review resolves it; `unresolved` for a missing/abstained/failed reviewed judgment. |
| `change_reason` | Why the initial decision was retained, changed, newly resolved or left unresolved. Do not equate a changed label with a corrected error. |

The envelope preserves `stage` (`initial_descriptor` or `source_review`), trial/reader IDs, model/effort assignment and observations, prompt/addendum/schema/catalogue hashes, topic-model identity, source-packet hash for review and the literal response. A reviewed response references the sealed initial file/hash without overwriting it. The importer can generate an explicit missing-attempt record after a technical failure, but must not invent the reader's reason or confidence. Any recovery retains the original attempt and identifies the change.

The final `topic_labels.csv`, `selected_topics.json` and `HANDOFF.md` are explicitly **Stage B reviewed-majority outputs**. Retain the same files under a separately named `initial/` output for the Stage A baseline. The final topic table carries initial and reviewed votes, both reasons/confidence reports, review findings/actions, evidence references and minority disagreements for all three readers and both categories; detailed JSON/source tables preserve full citation lists and source matches. `selected_topics.json` binds final selected/excluded/unresolved IDs to the exact model, review stage and source-packet hash. Two matching resolved Stage B labels decide, regardless of confidence. No initial-label fallback, cross-stage mixing or six-vote count is permitted. Missing confidence is a reporting defect; freeze schema/recovery treatment before execution without inventing confidence, changing recorded labels or treating defects as irrelevance.

Keep self-reported confidence, within-stage vote agreement, repeatability and initial-to-reviewed changes separate. Report confidence distributions, transitions and missingness by stage/model/template/effort/label. Do not convert ordinal categories to probabilities, weight votes, automatically relabel low-confidence topics or select the most confident model as most accurate. Review-induced changes may reflect passage access, reconsideration or anchoring; no accuracy gain or isolated causal passage effect is established.

[ICLR (2024), *Can LLMs Express Their Uncertainty?*](https://proceedings.iclr.cc/paper_files/paper/2024/hash/6733cf15e10e2cd1d59af033c3bb8507-Abstract-Conference.html), **published abstract, read 20 October 2026**, report overconfidence in verbalized confidence and imperfect calibration across their studied models/tasks. That supports treating confidence as an uncalibrated diagnostic. Our three-level rubric is a design choice, not their validated instrument. Calibration against suitable human references remains a later study.

## Linked source-evidence record

The [direct Step 1 inspection](SOURCE_TRACE_INSPECTION.md) confirms that source passages are recoverable from the delivery. A topic is a corpus-level pattern, not one CEO statement. Keep a separate, one-to-many source-evidence table linked by **topic-model identity + topic ID**; a topic name alone is insufficient.

| Field group | Planned source-evidence fields |
|---|---|
| Topic association | `topic_model_id`, `topic_id`, `link_method` (saved representative passage, supplied hard assignment or supplied density), saved representative rank or density value when available. These methods are distinct. |
| Source identity | Delivered file name/version/hash, `orig_row`, `transcriptcomponentid`, `transcriptid`, `transcriptpersonid`, `componentorder`, company ID and available source dates/year. |
| Speaker attribution | Source speaker metadata and `is_ceo` flag when present; distinguish a delivered CEO flag from independently verified role/tenure. Missing attribution stays unknown. |
| Text | Exact retained text, text SHA-256 and text version (`masked_processed_component`). A separate display transformation must identify its changes and retain the original. |
| Link status | Exact-text match status, number/all candidate source matches, linkage method and limits. Do not choose one speaker arbitrarily when the same text has several matches. |
| Review use | Frozen Stage B evidence, released only after initial sealing, with the same passages/order for every condition and both initial label categories. Reviewed judgments have their own stage/version and never overwrite initial ones. |

Freeze the three already-saved representative passages per topic in their saved order before collection, with stable passage IDs, exact text/hashes and candidate source links. Use all three for both initial categories; do not choose or replace passages in response to labels. All 1,062 entries were recovered, but they are not all CEO passages and 68 have ambiguous duplicate-text matches. Show delivered attribution and ambiguity; do not filter these away silently. A CEO-only sample is a separate planned extension. Absence of a CEO-matched representative does not establish absence of CEO discussion. The main packet uses saved representatives, without relying on historical unkeyed density to rank new examples. Include only relevant source metadata; behavior/outcomes, demographics, political scores and model performance are not reader evidence.

This table now supports both **Stage B AI review and traceback** in all 12 ratified trials, superseding revision 4's inspection-only boundary. It remains withheld during Stage A. Freeze the same complete source packet across configurations and retain the full-roster reading procedure used during execution; do not silently truncate passages, supply generated summaries or switch context structure. Three representatives are illustrations, not exhaustive topic membership or proof of risk preference. Keep exact passages and identifying metadata in authorized private storage; shared planning prose contains aggregate findings/file identities rather than full text.

## Implementation acceptance before a future launch

The frozen wrapper must enforce initial sealing before passage release, maintain the same independent reader/model/effort across stages, and freeze reviews before peer comparison. Both schemas and all reasons, confidence, review actions, quotations and source links must survive import/export/replay. A proportional synthetic check should cover a changed label, an unchanged label, newly resolved/missing review, duplicate attribution and confidence-independent voting, proving that the final majority uses Stage B only. Freeze technical-defect/recovery handling and verify complete passage access without truncation. The relevant checks are retained in the private runtime; the historical one-stage runner is not the study procedure. Final independent data-freeze QA closed without a final PASS, and that limitation remains explicit. No additional readiness campaign is required.

## Paged source review and context continuity

Use the ratified 18-page starting layout in [SEAT_PLAN.md](SEAT_PLAN.md#source-packet-size-and-reader-context). Preserve the full sealed initial response. Each page receives exact descriptors, that reader's corresponding initial rows, all three exact passages per topic and common instructions. Save literal reviewed page rows with page ID, topic range, packet/initial hashes, chat identity and available continuation/compaction observations. Assemble the final Stage B envelope from those immutable rows; do not regenerate judgments at assembly. Each stage must cover all 354 topics exactly once or explicitly account for missing material. Page fragments and continuation messages add no votes or independent trials. The same reader/model/effort persists; resets are deviations. Freeze transport, recovery and reporting rules before collection.
