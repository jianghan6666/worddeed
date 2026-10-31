# Completed example: CEO speech, R&D prediction, and dividends

**An AI Microfoundation Proxy application from narrative representation to a behavioral proxy and downstream analysis.**

This example explains the completed screening study and the empirical results delivered on 27 October 2026. Three small [aggregate result files](results/README.md) let readers inspect the findings. The connected agent is separately demonstrated with invented inputs; it has not rerun this complete empirical study.

## Research question

Can CEO speech support a candidate proxy for risk-taking, and is that proxy associated with firms' dividend decisions?

The study predicts **R&D divided by total assets** from earnings-call topic features and aggregate sentiment. It then tests whether higher predicted R&D intensity is associated with a lower likelihood of paying dividends, including after accounting for actual R&D and the specified compensation and firm controls.

The resulting score is a text-predicted behavioral outcome. Its interpretation as psychological risk preference requires evidence beyond prediction and regression significance.

## 1. Represent the narratives

The supplied study starts with 1,775,355 CEO-tagged speech components and an existing 354-topic representation. Speech is matched to company-year financial records; the CEO with the most spoken words is retained for each firm-year. Topic densities and sentiment are aggregated using speech word counts, with different handling of zero-topic components.

The resulting input panel contains **29,506 firm-years, 4,517 firms, and 6,933 CEOs**, covering 2013–2023. Screening determines which topic columns enter prediction. The original density matrix lacks embedded row identities and model/column fingerprints, so its historical ordering remains delivery-declared.

[Topic workflow](../../docs/workflows/01-topics.md)

## 2. Select relevant topics

The completed pilot contains **12 trials and 36 readers**: two requested model families, three effort settings, and two repetitions per configuration. Every reader first evaluates all 354 topic descriptors independently. Initial attempts are sealed or explicitly recorded as missing before passages are released. The protocol then continues each reader's own history through source review without peer judgments. A two-of-three Stage B majority determines topic selection; initial labels remain a separate comparison.

The [screening counts](results/screening-counts.csv) preserve both stages and incomplete voting coverage. Initial descriptor readings selected **66–87 topics** per trial; source review selected **313–321**. The primary results retain one unresolved majority. This broadening shows sensitivity to the reading procedure; it is not an accuracy estimate.

The delivered prediction analysis uses primary trial `b1-gpt-6-astra-P0-xhigh`, repetition 1: **321 selected, 33 excluded, and zero unresolved topics**. This identifies the input actually used. The pilot did not establish that this classifier was superior to the alternatives. Its twelve-trial scope was ratified after collection.

[Screening workflow](../../docs/workflows/02-screen-topics.md)

## 3. Predict the behavioral outcome

Step 3 predicts R&D/assets using the **321 selected topic features plus one aggregate sentiment feature**. Topic features receive a centered log-ratio transformation and standardization. Ridge and XGBoost use firm–CEO connected-component grouped five-fold cross-fitting: each firm's score comes from a model trained without that firm or other firms connected to it through shared CEOs.

Scores are provided for all 29,506 firm-years. The target is available for 29,191. Missing R&D is set to zero when assets are positive; **42.7% of available targets arise from this zero-fill rule**. The remaining 315 observations lack a target because assets are missing or nonpositive.

| Delivered cross-fitted performance | Ridge | XGBoost |
| --- | ---: | ---: |
| R² | **0.5351** | **0.6128** |
| Mean squared error | 0.006006 | 0.005001 |
| Correlation with target | 0.7315 | 0.7829 |
| Selected tuning value | α = 1,000 | Max depth = 6 |

The [machine-readable metrics](results/prediction-metrics.json) include per-fold settings and counts. Evaluation uses target-available rows and the delivered full-model winsorization convention. Full-sample fitted scores also exist, but downstream analysis uses out-of-fold scores. The prediction features contain no industry, size, or year controls. This method differs from the earlier proposed scalar narrative measure N followed by `f(N, controls)`.

[Proxy workflow](../../docs/workflows/03-build-proxy.md)

## 4. Assess the proxy in dividend decisions

Strict company/person/time matching yields **2,967 inputs across 600 firms** from an eligible pool of 7,086 firm-years. Ordinary score models use 2,927 observations across 591 firms after excluding industry groups that perfectly predict dividend status. The positive-relative-leverage specification uses 1,653 observations across 340 firms.

The dependent variable is dividend payment. Pooled Logit models include separate industry and year effects and company-clustered standard errors. Ridge and XGBoost enter separate models, using:

```text
Score = 100 × max(out-of-fold predicted R&D/assets, 0)
```

A prediction of 0.05 therefore enters as 5 percentage points. Four specifications for each algorithm, with and without actual R&D controls, produce **16 score models**. All 16 delivered score coefficients are negative with company-clustered p < .01.

One representative specification, column (8), gives:

| Score | Without actual R&D: coefficient (SE) | With actual R&D: coefficient (SE) |
| --- | ---: | ---: |
| XGBoost | −0.1915 (0.0322) | −0.1423 (0.0347) |
| Ridge | −0.1836 (0.0218) | −0.1478 (0.0241) |

These are conditional log-odds coefficients. The controlled XGBoost coefficient implies an odds ratio of approximately 0.867 for a one-percentage-point increase in the score, holding included variables fixed. It does not represent a 13-percentage-point change in dividend probability or a causal effect.

Read [all 16 result tables and estimation notes](results/dividend-results.md). They are the score-model subset of a larger 25-specification delivered study.

[Assessment workflow](../../docs/workflows/04-assess-proxy.md)

## What remains open

The study connects a recorded topic-selection procedure, grouped text-based prediction, and a completed dividend analysis. Several questions remain:

- **Meaning:** R&D prediction can reflect industry, opportunities, and disclosure practices as well as risk preference. Independent construct validation and a separate N/B/S comparison remain open.
- **Inputs and timing:** Historical density alignment is delivery-declared; missing R&D is often zero-filled; speech and the target overlap in time. The topic model also used held-out firms' text during unsupervised fitting.
- **Screening:** No human-reference accuracy study or superior classifier was established.
- **Inference:** Matching selects a subset. Clustered standard errors condition on the frozen first-stage score and do not propagate retraining uncertainty. Related specifications are not independent replications.

The [roadmap](../../docs/ROADMAP.md) develops these questions into next steps.

## Try the connected workflow

From the repository root, with Python 3.11 or newer:

```sh
python3 -m agent_system.empirical.demo --out .local/example-fixture
python3 -m agent_system.empirical.demo --out .local/example-fixture --resume
```

Inspect `summary.json`, `workflow/state.json`, and `workflow/events.jsonl` inside that output directory. The fixture uses three invented topics and two invented rows to exercise coordinator dispatch, stage handoffs, persistence, and resume. It makes no live model calls and performs no empirical training or Stata estimation.

The aggregate files document the delivered findings; they are not sufficient to reproduce the underlying empirical estimates. See the [workflow guide](../../docs/WORKFLOW.md) for the executable interfaces and required study inputs.
