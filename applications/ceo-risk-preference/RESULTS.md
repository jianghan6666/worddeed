# WordDeed CEO case results and evidence scope

WordDeed's CEO application learns the component of firms' R&D intensity that can be predicted from CEO earnings-call language, then examines its association with dividend payment. The saved results support grouped prediction of the behavioral anchor and negative dividend associations. They do not establish that the score isolates psychological risk preference or has a causal effect on payout.

This report distinguishes the original computational package from extensions reported in the submitted technical appendix. The original package contains **25 dividend models: nine conventional baseline specifications and sixteen synthesized-score specifications**. The final appendix additionally reports **eight models with a narrative proxy and actual R&D controls**, in Table A13. Those eight are outside the existing 25-model reproduction.

The [evidence-scope note](EVIDENCE_SCOPE.md) explains how this current account relates to the preserved historical reports and unresolved implementation differences. Use the [short application introduction](README.md) for the role of this case in the proposed workflow.

The [complete saved results](https://github.com/jianghan6666/worddeed/tree/b96f8f65352d24ffb6e5137d81bc50d59b3bf779/applications/ceo-risk-preference/results) and [reproduction record](https://github.com/jianghan6666/worddeed/blob/b96f8f65352d24ffb6e5137d81bc50d59b3bf779/applications/ceo-risk-preference/replication/verification/CONNECTED_REPRODUCTION.json) have different purposes: one preserves the empirical outputs; the other documents the earlier computational rerun.

## What the four stages produced

| Stage | Preserved evidence | Interpretation |
|---|---|---|
| Representation | A fixed 354-topic catalogue, topic methods, component features and historical model metadata. | A reusable representation; historical density ordering remains delivery-declared. |
| Screening | Twelve two-stage runs with 36 readers, primary and recovery outputs, reasons and minority judgments. | Sensitivity and repeatability of topic relevance judgments; no human-reference accuracy study. |
| Prediction | 29,506 scored firm-years and two grouped out-of-fold prediction series. | Prediction of contemporaneous R&D/assets under one adopted topic selection. |
| Dividend assessment | Nine baseline models and sixteen score models; the appendix separately reports eight narrative-adjusted extensions. | Conditional associations in a selected CEO–firm sample, with distinct computational coverage for the extension. |

## Narrative representation and topic selection

The historical BERTopic model contains **354 regular topics** plus an outlier category. It was trained on **887,488 speech components with nonmissing political-donation ideology scores**, drawn from a **5,765,638-component corpus covering 2013–2023**. That training subset is not restricted to CEO speech. The CEO prediction application uses **1,775,355 CEO-tagged components** and their supplied topic densities. The original density matrix does not embed row identities or model/column fingerprints; later identity checks cannot independently recover that missing historical provenance.

The main screening study crosses two requested model families, three effort settings and two repetitions. Three readers independently classify topic descriptors and then review common source passages in their own continuing sessions. An unweighted two-of-three majority determines inclusion. Only the direct-prompt condition was completed; the broader 84-run design was not executed in full.

Descriptor-only screening selects **66–87 of 354 topics**. Source review selects **313–321**, or **88.4–90.7%**. Of **4,247** run–topic comparisons resolved at both stages, **2,964 (69.79%)** change: 2,928 become relevant and 36 become irrelevant. The primary data retain **120 missing reader judgments out of 12,744 intended judgments**, leaving one unresolved final majority. Supplementary recovery resolves it without replacing the primary record.

The prediction models use one run: **b1-gpt-6-astra-P0-xhigh, repetition 1**, with **321 selected topics and 33 excluded**. Of the included topics, 302 have three agreeing votes, three have a two-to-one majority, and sixteen have two agreeing votes with the third absent. This is one ensemble's selection, not a consensus across twelve runs. The appendix discloses that its adoption followed inspection of preliminary predictive fit. Agreement and broad retention do not establish screening accuracy or removal of contextual confounds.

[Inspect all screening counts and decisions.](https://github.com/jianghan6666/worddeed/tree/b96f8f65352d24ffb6e5137d81bc50d59b3bf779/applications/ceo-risk-preference/results/step2/analyses)

## Predicting the behavioral anchor

The panel covers **2013–2023**, with **29,506 firm-years, 4,517 firms and 6,933 CEO identifiers**. The mapping uses **321 selected topic densities plus one aggregate sentiment feature**. Topic densities are weighted by speech word counts, transformed by a centered log ratio over the selected topics, and standardized. This is the implemented feature specification; the separate scalar narrative benchmark described below is not its input. No firm-size, industry, year or financial controls enter these prediction models.

The target is contemporaneous R&D expenditure divided by positive total assets. Missing expenditure is assigned zero. Of **29,191 valid targets**, **12,452 (42.66%)** are zero-filled for unreported R&D; another **3,601 (12.34%)** explicitly report zero. The remaining **315** scored rows have invalid or missing assets and do not enter target-based performance calculations.

Five outer folds keep each company–CEO connected group together. Each observation's score comes from a model fitted without its group. Four-way validation within the other folds chooses the Ridge penalty or XGBoost depth. All outer Ridge fits choose α=1,000; all XGBoost fits choose depth six. XGBoost uses 600 trees, learning rate .03, row subsampling .8, column subsampling .5, minimum child weight 10 and seed 42.

| Saved grouped OOF performance, N=29,191 | Ridge | XGBoost |
|---|---:|---:|
| R² | .5351 | .6128 |
| MSE, squared ratio units | .006006 | .005001 |
| Correlation with capped target | .7315 | .7829 |

These metrics compare raw out-of-fold predictions with R&D capped at the full labeled panel's 1st/99th percentiles, **0 to .642680488 in ratio units**. Training caps are set separately for each outer-training portion, before its inner tuning. The full-sample evaluation cap does not enter the fitting of an observation's own outer model, but it is part of the reported evaluation definition.

The stored scores allow these summary metrics to be recalculated without refitting. Such recalculation checks numerical consistency. It does not reexecute model training. Historical topic fitting includes held-out firms' text, and preliminary predictive performance informed topic-set choice; the reported metrics therefore condition on the adopted representation and selection. They are not a fully held-out evaluation of the entire discovery-and-selection process, nor a forecast of future years.

The three-seed robustness exercise uses grouped splits of approximately **20% training, 20% validation and 60% test**. Mean test R² and between-seed sample SD are **.507 (.011)** for Ridge and **.576 (.009)** for XGBoost. These are three resplits of the same panel, not independent external studies. Their comparison with stored OOF scores also compares different training sizes.

[Inspect the prediction method, scores and metrics.](https://github.com/jianghan6666/worddeed/tree/b96f8f65352d24ffb6e5137d81bc50d59b3bf779/applications/ceo-risk-preference/results/step3)

## Dividend associations in the original package

The dividend application adapts an established payout design to **2013–2023**. Matching yields **2,967 firm-years, 600 firms and 771 CEOs** from an eligible pool of 7,086 firm-years. After estimation screens, ordinary score specifications use **2,927 firm-years, 591 firms and 760 CEOs**. Positive-relative-leverage specifications use **1,653 firm-years, 340 firms and 441 CEOs**. These sample distinctions matter for comparisons across specifications.

The outcome is positive common dividends per share. The score enters as:

**100 × max(raw out-of-fold predicted R&D/assets, 0).**

A prediction of .05 therefore enters as five percentage points. Ridge and XGBoost enter separate pooled Logit equations with industry and year indicators and firm-clustered standard errors. Four compensation specifications are estimated with and without actual R&D/assets and its missing-value indicator, giving sixteen score models. Controls cover CEO experience, compensation incentives, investment demand, size, profitability, accumulated earnings and return volatility. These are not firm or CEO fixed-effects models.

All sixteen saved score coefficients are negative with firm-clustered p<.01. In the inside-debt specification:

| Score | Without actual R&D, β(SE) | With actual R&D, β(SE) | With-R&D odds ratio |
|---|---:|---:|---:|
| Ridge | −.1836 (.0218) | −.1478 (.0241) | .8626 |
| XGBoost | −.1915 (.0322) | −.1423 (.0347) | .8673 |

Holding included covariates fixed, the controlled estimates correspond to approximately **13.7% and 13.3% lower odds** of paying dividends per one-percentage-point increase in the respective score. They are not percentage-point changes in dividend probability or causal effects. Standard errors condition on the estimated scores and do not propagate the full training-and-selection uncertainty.

The ordinary estimation sample has **53.54% dividend payers** and **30.61% unreported R&D**. Mean actual R&D is **4.09% of assets**; the clipped predicted means are **5.62% Ridge** and **4.88% XGBoost**, with SDs **6.74 and 7.38 percentage points**.

The original package also contains nine conventional baseline equations across 2006–2011, 2006–2023 and 2013–2023. Their samples differ from the score models. Fit statistics across those different samples do not establish incremental predictive performance on common observations.

[Inspect all 25 model specifications, coefficients and used-sample records.](https://github.com/jianghan6666/worddeed/tree/b96f8f65352d24ffb6e5137d81bc50d59b3bf779/applications/ceo-risk-preference/results/step4/full/estimates)

## What the final appendix adds

Appendix §3.6 constructs a scalar narrative benchmark by multiplying each component's rescaled sentiment by its density across the selected topics, then aggregating with speech-word weights over topic-valid components. Higher values mean more positive coverage-weighted tone in those topics. The formula assigns no separate risk-seeking or risk-avoidance weights. Although R&D is absent from the aggregation formula, preliminary R&D fit informed selection of the topic set.

Table A15 reports correlations on **29,191 common firm-years**. The narrative benchmark correlates **.143 with Ridge, .147 with XGBoost and .079 with uncapped R&D intensity**. The synthesized scores correlate **.914 with each other** and **.537/.577 with uncapped R&D**. These differ from the capped-target correlations in the prediction table because the target definition differs. Closer alignment with the training anchor is expected from calibration and is not independent proof of construct validity.

Table A13 adds this narrative benchmark to eight dividend models already controlling for actual R&D. The submitted estimates are:

| Compensation setting | Ridge score β(SE) | XGBoost score β(SE) | N / firm clusters |
|---|---:|---:|---:|
| Inside debt | −.146 (.024) | −.141 (.035) | 2,927 / 591 |
| Log relative leverage | −.168 (.032) | −.150 (.050) | 1,653 / 340 |
| High relative leverage | −.152 (.024) | −.150 (.034) | 2,927 / 591 |
| Cash compensation and equity wealth | −.153 (.024) | −.153 (.034) | 2,927 / 591 |

All eight synthesized coefficients are reported significant at 1%; narrative coefficients are negative and nonsignificant, with p-values .357–.582. This supports a submitted claim of incremental conditional association under the reported specification. It does not by itself show predictive superiority, a valid psychological trait, or causal interpretation.

**Evidence status:** these are author-reported appendix results. Arithmetic using the rounded printed coefficients and standard errors is consistent with the significance statements. The audited public empirical package does not yet supply the keyed narrative series and eight-model construction/estimation lineage needed to reproduce A13 or the narrative entries of A15. The existing 25-model reproduction must not be described as verification of these extensions.

## Reproduction and interpretation boundaries

The existing connected-reproduction record documents reuse of the saved topic representation, offline aggregation of saved reader judgments, refitting of Ridge/XGBoost and estimation of the original 25 dividend equations. It reports sample checks and numerical agreement for that scope. It does not report fresh topic discovery, regenerated sentiment, new AI judgments or an A13 rerun. Saved-output arithmetic in this review is a separate, narrower check.

The submitted framework proposes additional tests: common-sample benchmarks, independent reference judgments, alternatives to the selected topic set, averaging across configurations, alternative behavioral anchors and decomposition of shared circumstances. Those remain development work. R&D prediction and dividend associations are useful feasibility evidence; their interpretation as CEO risk preference must still be evaluated against firm opportunities, resources, disclosure practices, timing and sample selection.

The repository is publicly viewable. Source-specific access and reuse conditions continue to apply to underlying materials; visibility alone does not grant a general license.
