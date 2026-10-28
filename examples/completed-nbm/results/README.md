# Aggregate results and field guide

These three files preserve selected aggregate outputs from the completed NBM application. Screening finished on 21 October 2026; the prediction and dividend-analysis outputs were delivered on 27 October 2026. The files were copied byte-for-byte and given shorter filenames. They contain trial-level counts, model summaries, and regression tables, rather than individual speech, firm-year records, or reader responses.

## Screening counts

[`screening-counts.csv`](screening-counts.csv) has 24 rows: 12 trials × two stages. It contains the primary analysis of first submissions; recoveries are not silently substituted.

| Fields | Meaning |
| --- | --- |
| `trial_id` | Experimental run identifier; not a person identifier |
| `stage` | `initial_descriptor` or `source_review` |
| `block`, `model`, `prompt_id`, `effort` | Repetition, requested model, prompt family, and requested effort |
| `selected_N`, `excluded_N`, `unresolved_N` | Majority classifications; the three counts sum to 354 |
| `all_three_resolved_N` | Topics with resolved votes from all three readers |
| `operational_majority_missing_third_N` | Topics with a two-reader majority and a missing third resolved vote |

Model and effort labels describe requested configurations. Counts and agreement do not establish construct validity or independent reader errors.

## Prediction metrics

[`prediction-metrics.json`](prediction-metrics.json) describes the target, panel size, selected-topic count, and both fitted model families. For each model, `crossfit` contains R², MSE, and correlation; `folds` records training/scoring counts, tuning choices, and winsorization bounds. `full_insample_r2` is an in-sample diagnostic, not the reported cross-fitted performance. `versions` defines score transformations. `secs` records the supplied run's timing, not a runtime guarantee.

## Dividend results

[`dividend-results.md`](dividend-results.md) contains 16 pooled Logit score specifications: two algorithms × four specifications × two actual-R&D-control settings. Parentheses contain company-clustered standard errors. Stars follow the file's normal two-sided Wald conventions. Its notes identify score scaling, sample rules, and the separate sources of coefficient and fit-statistic values. Coefficients are associations conditional on these models and samples.

## File identity

The fingerprints bind the exact retained bytes. They establish file identity, not empirical validity or a new reproduction.

| File | Bytes | SHA-256 |
| --- | ---: | --- |
| `screening-counts.csv` | 2,051 | `7db341c46a2d5ea9465283468cb400efe3e65a46be16eb6bc1031242e686e672` |
| `prediction-metrics.json` | 5,637 | `8247f28cf66c4c81df0839a7e260080d5eb7964066cad85721bbe9898e21629c` |
| `dividend-results.md` | 11,132 | `867cfb1b5f5ca2f1c4fd0194d60237be4c5d34dcb69b6c064beea4d81a3e81ff` |

Return to the [completed example](../README.md) for interpretation and the runnable invented-input demonstration.
