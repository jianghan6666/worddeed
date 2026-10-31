# Results file guide

Start with [report.pdf](report.pdf) or [report.html](report.html). Download/open HTML files locally; GitHub shows their source. The report summarizes the existing four-step application; the files below retain the full detail.

| Step | Read | Inspect complete outputs |
|---|---|---|
| 1. Topics | [Training method](step1/methods/1_topic_model_training.md), [inference method](step1/methods/2_topic_inference.md) | [Catalogue](step1/catalogue.json), [descriptions workbook](step1/topic_descriptions_354Topics.xlsx), [topic information CSV](step1/topic_info_354Topics.csv), [information workbook](step1/topic_info_354Topics.xlsx), [top-25 keywords](step1/topic_top25_words.xlsx), [saved topic metadata](step1/topics.json) |
| 2. Screening | [All-trial reader browser](step2/explorers/index.html), [coauthor memo](step2/MEMO.md) | [Primary reports/tables](step2/analyses/primary/), [supplementary reports/tables](step2/analyses/supplementary/), [reader index](step2/READER_INDEX.json), [exact prompts](step2/protocol/), [recorded usage](step2/USAGE.json) |
| 3. Prediction | [Method](step3/docs/METHOD.md), [robustness report](step3/results/seed_robustness_report.md) | [All scores CSV](step3/results/risk_scores.csv), [Parquet](step3/results/risk_scores.parquet), [metrics and folds](step3/results/metrics.json), [robustness metrics](step3/results/seed_robustness_metrics.csv), [actual selected topics](step3/selected_topics.json) |
| 4. Full study | [All 25 model tables](step4/full/results/REPLAYED_TABLES.html), [matching method](step4/full/docs/MATCHING_FROM_SOURCE.md) | [Original five-sheet workbook](step4/full/results/table4_annual_b_tables.xlsx), [coefficients](step4/full/estimates/coefficients.csv), [model summaries](step4/full/estimates/model_summary.csv), [specifications](step4/full/estimates/model_reference.json), [used-sample records](step4/full/estimates/samples/), [historical checks](step4/full/audit/) |
| 4. Score-model subset | [All 16 score tables](step4/score-models/results/RESULTS.html), [research report](step4/score-models/docs/REPLICATION_REPORT.md) | [Original score workbook](step4/score-models/results/step4_score_tables.xlsx), [historical checks](step4/score-models/audit/) |

## Reader evidence

Each trial browser includes every scientific label field from all three readers at both stages. Primary first attempts and supplementary recoveries can be selected separately. Missing responses are explicitly shown as missing. Nothing is filled with a negative label, and confidence does not weight the majority.

The Git view holds 95 distinct assembled reader records, indexed across 144 trial/reader/stage/variant positions. Identical records are shared between analysis variants. The complete results ZIP adds `reader-evidence/`: the original frozen result package, including the 3,840 release-bundle members, literal submissions, source packets, seals, recovery records, deviations, and provenance. The archive also includes the associated ratified protocol files under `reader-protocol/`.

Paths embedded in original reader records and handoff JSON are relative to the original frozen evidence package. Resolve `evidence/...` against `results/reader-evidence/` in the full ZIP. Historical copied documents may refer to their original repository layout; use this file guide and `SOURCES.json` for the current locations. No scientific field or original result was rewritten to repair a historical relative link.

## File identity and interpretation

`SOURCES.json` maps preserved files to the supplied packages. `MANIFEST.json` binds the current browsable files. `EVIDENCE_MANIFEST.json` binds all additional ZIP-only reader records. `verify.py` checks file identities, all handoffs, browser contents, score coverage, and model inventories. This is a packaging check, not fresh estimation or construct validation.

Original numerical outputs and saved judgments are copied byte-for-byte from the privacy-reviewed collaboration exports. The new PDF, HTML, charts and browsers present those outputs. The supplied Step 3/4 audit files describe historical checks; they are not relabeled as checks run for this release.

The delivered prediction specification uses selected topic features and aggregate sentiment to predict R&D/assets. It does not implement the earlier proposed separate scalar N followed by `f(N, controls)`, nor an independent N/B/S comparison. Read the report's limitations before interpreting the score as CEO risk preference.

For computational reproduction and raw inputs, use the separate replication package. Source data remain subject to the existing private research access conditions.
