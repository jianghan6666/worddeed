# Can Step 2 recover the Step 1 source text?

**Yes: the delivered Step 1 package retains the processed speech text and a working link from every row in its CEO subset back to that text.** This was checked directly on 20 October 2026, beyond the earlier four-call/76-component pilot. The available text has person/company names masked; it is not an unmodified full-call transcript.

This was read-only inspection of existing files. No topic modeling, new model inference, classification trial or source modification was performed. Literal texts, identifiers, all candidate duplicate matches and the inspection script/report are retained locally; this shareable report contains aggregate findings and source file identities only.

## What was opened and checked

Paths below are relative to the supplied `ceo_rd` delivery, not the Git checkout.

| Delivered artifact | Direct finding |
|---|---|
| `models/bertopic_ideo_13-23_relaxed_354Topics/topic_info_354Topics.csv` | Every one of 354 regular topics has three nonempty saved `Representative_Docs`: **1,062 topic–passage entries**, containing 1,035 distinct text strings. Outlier `-1` is separate. |
| `data/t_combined_nodup_13-23_compNameOK_retainedNoEmpty_namesANDcomps_removed_w_scores_sentiment.pickle` | **5,765,638 rows**, all with nonmissing `componenttext_masked`. It retains component/call/speaker/company identifiers and dates/order. The only speech-text field is the masked/processed text. |
| `data/replication_sample/transcripts_is_ceo.pickle` | **1,775,355 rows**, all with source `is_ceo=True`, and an `orig_row` link. It has metadata but no speech-text field. |
| `data/replication_sample/topic_distr_is_ceo.npz` | Supplied density has shape **1,775,355 × 354**. The container has only `topic_distr.npy`, with no embedded row identifiers or model fingerprint. |
| Saved BERTopic model and frozen Step 2 catalogue | All five saved model-file hashes match the earlier catalogue binding. The current Step 2 catalogue and recovered catalogue have the same exact topic-model identity and all 354 regular topic IDs. |

The full retained corpus contains **4,665,469 Answer components and 1,100,169 Presenter Speech components**. No analyst-question component type appears in this table. It therefore supports inspection of retained speech and reconstruction of the retained component order, not a claim to reproduce complete call dialogue or removed/unmasked content. A bounded file inventory of this delivery found no separate raw transcript corpus; this does not establish that the provider or researcher lacks an original elsewhere.

## Topic-to-passage and CEO-to-text results

All **1,062 representative entries** match exact strings in the full retained corpus; there are no unmatched entries. Of these, **994 have one exact source-row match** and **68 have multiple matches**. The 1,035 distinct strings match 1,614 distinct corpus rows. All candidate matches remain in the private record; duplicate passages are not assigned to one convenient speaker.

**691 representative entries have at least one match in the delivered CEO subset**, covering **290 of the 354 topics**. Within these, 670 entries have a unique source-row match. The other **371 entries** have no match in that subset. The **64 topics** without a CEO-matched representative are not thereby topics never discussed by CEOs: three saved representatives are not the full topic membership. Nor does “no CEO-subset match” independently prove a non-CEO role. Report the supplied attribution and its limits.

For **every one of the 1,775,355 CEO-subset rows**, `orig_row` is unique and in range, and the linked full-corpus row agrees on **seven fields, with zero mismatches**: `transcriptcomponentid`, `transcriptid`, `transcriptpersonid`, `componentorder`, `companyid`, `year` and `retained_word_count`. The subset contains two identically named component-ID columns; their values were checked identical before one was omitted in memory. Source files were unchanged. The older pilot's **76/76 texts** also matched the live source exactly.

Thus the delivery supports these two routes:

1. **Topic → saved representative passage → exact source match(es) → component, call, speaker and date metadata.** The saved topic association comes from the model export; exact-text matching supplies candidate source attribution and preserves duplicates.
2. **CEO subset row → `orig_row` → retained speech text + matching identifiers.** This row join was checked across the whole CEO subset, not merely a sample.

These checks establish retrieval and delivered attribution. They do not establish that a passage expresses risk preference, or independently validate the source's CEO role/tenure coding. Topics may include other managers' speech, and a topic label is not a claim about every passage within it.

## Separate limitation: historical density binding

The text joins above are verified. The historical density array remains an unkeyed artifact whose alignment to the CEO table is declared by the delivery. Equal shape and a valid metadata/text join do not prove how that historical matrix was generated. The missing contemporaneous row-key/model/column binding remains documented in the [adapter handoff](../../../step-2-mvp/data_adapter/REVISION_HANDOFF.md). Do not let that distinct limitation obscure the fact that the actual retained texts are retrievable. Do not describe any newly reconstructed density-based source link as a historically authenticated one without the missing provenance or a separately identified authorized recomputation.

## Source identities and use in Step 2

The corpus and CEO-subset file hashes were recomputed and match the previously identified delivery. The representative CSV hash was also computed:

| File | SHA-256 |
|---|---|
| Full retained corpus | `70dd42ff7f8b2974396886822a6c27f19a80e2c2e90bdb30b743991cc1992d11` |
| CEO metadata subset | `99791fb88efdbd3a6193d7dbd538e8cedeee0ce7b35a8602249eedc381f188d1` |
| Representative-topic CSV | `3aaf3cd7c68f3835640bb7f874768be00029e36bc4ef5f4398633fc917618309` |

The density container/header was inspected; its full hash was not recomputed in this check. Frozen topic-model identity: `bertopic_ideo_13-23_relaxed_354Topics:sha256:52deaf6581036e750af07604268d4665bfa3386b3797874e8374b3876b3b683f`.

**Workflow amendment after this inspection:** the user approved a two-stage plan, now recorded in [the current plan](PLAN.md) and the [source-evidence contract](OUTPUT_CONTRACT.md#linked-source-evidence-record). Initial Stage A readers still classify names/keywords and seal reasons/confidence before passage access. The same three saved representatives per topic then become common Stage B evidence for all 252 trials in revision 7's four-model design; reviewed labels determine the final majority, with initial labels and all changes retained. This explicitly supersedes revision 4's inspection-only passage use. It changes the planned workflow, not the source-inspection findings or the historical 12-run pilot. Source packet packaging and execution remain pending.
