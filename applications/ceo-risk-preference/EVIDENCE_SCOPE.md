# CEO example: evidence scope

This note accompanies the current [results account](RESULTS.md) and [replication guide](REPLICATION.md). The CEO application illustrates the proposed workflow for combining behavioral and narrative cues into a synthesized proxy. It supplies evidence of feasibility; psychological construct validity and causal interpretation remain open questions.

## Current account and historical outputs

The files under `results/` preserve an earlier computational package and its presentation. Their manifests and numerical bytes remain unchanged. Historical descriptions there should be read with the current results account: they do not automatically incorporate later submitted analyses or the 2 November review.

| Evidence | Scope |
| --- | --- |
| Original saved computation and connected reproduction | Nine conventional baseline models and sixteen synthesized-score models: 25 downstream models in total. Prediction starts from saved topic representation and reader judgments. |
| Submitted appendix extension | A narrative benchmark and eight additional narrative-plus-actual-R&D specifications in Table A13; Table A15 reports component correlations. These are reported results outside the original 25-model reproduction. The separate narrative-series and computation package was not found in the reviewed released route. |
| Saved-reader replay checked on 2 November | Recalculation of archived judgments and 122 analysis/handoff outputs, without new AI inference. |
| Newer API screening adapter | Its actual released-input preflight failed on 21 absent required files, before any provider call. Successful archived replay does not make this route ready from the current release alone. |

The submitted documents are supplied separately through the editorial process. This note neither bundles them nor supplies public download links.

## Intended design and implemented example

The CEO prediction uses 321 topic densities and one overall sentiment feature, without firm controls or fixed effects in the prediction model. The historical topic model was trained on a political-donation-score-available subset of the broader corpus. These facts qualify broader design descriptions about topic-specific sentiment, first-stage controls or whole-corpus training.

The saved model setting `top_n_words=15` differs from Table A14's 25. An export of 25 topic descriptors does not resolve that fitted-setting discrepancy. Missing R&D is assigned zero, the adopted topic selection followed preliminary predictive-fit inspection, and historical density alignment remains delivery-declared. The [detailed results](RESULTS.md) retain the relevant denominators, specifications and interpretation limits.

Agreement, prediction and downstream association provide different evidence. They should not be treated as independent proof that the score isolates CEO risk preference. The [execution reference](REPLICATION_DETAILS.md) distinguishes computational checks, recorded earlier refits and work still needed.
