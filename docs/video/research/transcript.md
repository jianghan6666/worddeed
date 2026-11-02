# Match Words with Deeds

**An AI-empowered proxy framework for organizational microfoundations**

The film follows the framework’s first application, CEO risk preference.

**Research film transcript** · WordDeed · 4 minutes 30 seconds · English narration synthesized with Kokoro (voice af_heart).

Each chapter includes its narration and a description of the evidence on screen. The final appendix extension and the reproduced 25-model package are identified separately.

[Play the research film](match-words-with-deeds.mp4) · [English captions](captions.en.vtt) · [Accessible HTML transcript](transcript.html)

## 0:00–0:30 · One decision, two explanations

Why would a firm spend heavily on research and development? Its chief executive might welcome risk. Or the industry might offer an opportunity that even a cautious executive would pursue.

Now listen to the earnings call. An executive may talk boldly to impress investors, while committing very little. If both the decision and the words are open to interpretation, what can we learn by reading them together?

**On screen**

Two explanations lead to the same high research and development (R&D) spending. A second comparison pairs a bold public statement with limited investment. Both examples are illustrative.

## 0:30–1:05 · How Figure 1 joins words and deeds

Figure 1 starts with a choice. Which unobserved trait are we measuring? Here, it is a chief executive’s willingness to take risks. On the words branch, unsupervised discovery builds one catalogue across firms. Three language model readers judge which topics bear on the trait.

On the deeds branch, researchers choose a theoretically justified behavioral measure. Each application specifies its target and any covariates. Step 3 predicts behavior from the selected narrative features. Predictions for held-out observations form the synthesized proxy. Step 4 evaluates the measure.

**On screen**

Figure 1 joins a corporate-text branch and a separately chosen behavioral anchor. Researchers specify the construct, target, features, and any covariates for each application. Held-out predictions form the synthesized proxy; a separate outcome and component-proxy comparisons assess it.

[View Figure 1](../../figures/figure-1.svg) · [Download Figure 1 as a PDF](../../figures/figure-1.pdf)

## 1:05–1:55 · Topic 224 and the deciding vote

The CEO study used a saved topic catalogue. Topic 224 described the Canadian market. All three readers initially voted to exclude it. Each reader then reviewed the same passages independently. Two saw the discussion of expansion as evidence of risk taking.

One still saw geography. Under an unweighted two-out-of-three rule, the topic stayed in. The dissent was preserved. Across 12 trials and 354 regular topics, descriptors alone yielded 66 to 87 selections. Passage review raised that range to 313 to 321. The prediction study used the 321 topics from this trial. Would human readers agree on the borderline cases? That test remains open.

**On screen**

The selected trial is b1-gpt-6-astra-P0-xhigh. Initially A, B and C all voted to exclude Topic 224. After independent review of the same passages, A still voted to exclude it, while B and C voted to include it. Across the 12 trials, passage-review majorities retained 313–321 of 354 topics (88.4–90.7%). Reviewer reproduction checks the delivered rows and ordering. The historical alignment has limited independent provenance.

[Initial topic labels](https://github.com/jianghan6666/worddeed/blob/5aae577d4d09f5fb93bc5dd93704b18ed3eae368/applications/ceo-risk-preference/results/step2/analyses/primary/handoffs/b1-gpt-6-astra-P0-xhigh/initial_topic_labels.csv) · [Final topic labels](https://github.com/jianghan6666/worddeed/blob/5aae577d4d09f5fb93bc5dd93704b18ed3eae368/applications/ceo-risk-preference/results/step2/analyses/primary/handoffs/b1-gpt-6-astra-P0-xhigh/topic_labels.csv) · [Counts for all 12 trials](https://github.com/jianghan6666/worddeed/blob/5aae577d4d09f5fb93bc5dd93704b18ed3eae368/applications/ceo-risk-preference/summary/screening-counts.csv)

## 1:55–2:50 · What the score actually predicts

Each firm-year had 321 transformed topic densities and one overall sentiment measure. Prediction used no firm controls or fixed effects. The target was same-year R&D divided by assets. With positive assets, missing R&D was set to zero. That rule supplied 42.7 percent of the available targets. Missing disclosure may differ from true zero.

Five folds kept connected firms and executives together. Each firm received a score from a model trained on four other folds. The models scored 29,506 firm-years. Cross-fitted R squared was 0.5351 for Ridge and 0.6128 for XGBoost, for contemporaneous spending. Observed minus predicted behavior gives a signed gap. It cannot establish intent. The dividend study uses the prediction itself.

**On screen**

Five folds kept every firm and all firms linked through a CEO in the same fold. The score estimates same-year R&D/assets for 29,506 firm-years. Cross-fitted R² is evaluated on the 29,191 observations with a target. Of these, 12,452 with positive assets had missing R&D coded as zero. The metric uses the target winsorized at the full-sample thresholds. A signed residual records a departure from fitted behavior. Its cause needs separate evidence.

[Prediction methods](https://github.com/jianghan6666/worddeed/blob/5aae577d4d09f5fb93bc5dd93704b18ed3eae368/applications/ceo-risk-preference/study/prediction/docs/METHOD.md) · [Machine-readable model metrics](https://github.com/jianghan6666/worddeed/blob/5aae577d4d09f5fb93bc5dd93704b18ed3eae368/applications/ceo-risk-preference/summary/prediction-metrics.json)

## 2:50–3:45 · What the dividend test establishes

Does the score relate to a different decision? Following the Caliskan and Doukas dividend-policy setting, the study asked whether the firm paid a dividend. It used held-out predicted R&D divided by assets, set negative predictions to zero, and expressed the score in percentage points.

Look at column eight with actual R&D controls. For each one-point increase in the XGBoost score, the estimated log odds fell by 0.1423. The firm-clustered standard error was 0.0347. Higher scores were associated with lower odds of paying dividends. The sign was negative in all sixteen specifications that included a score. The final appendix adds eight models with both a narrative proxy and actual R&D controls. The synthesized score remains negative and significant in all eight. These additional results are reported in Table A13.

**On screen**

The dividend-payer logit coefficient for the XGBoost score in the original column (8), with actual R&D controls, is −0.1423 (firm-clustered SE 0.0347; 2,927 observations, 591 firms). Table A13 in the final appendix adds a narrative proxy to eight R&D-adjusted specifications. All eight synthesized-proxy coefficients remain negative and significant at p < 0.01. The inside-debt estimates are −0.146 for Ridge and −0.141 for XGBoost. Table A13 is author-reported and is not covered by the repository’s existing 25-model connected reproduction.

[Dividend estimates, including column (8)](https://github.com/jianghan6666/worddeed/blob/5aae577d4d09f5fb93bc5dd93704b18ed3eae368/applications/ceo-risk-preference/summary/dividend-results.md) · [All 25 regression specifications](https://github.com/jianghan6666/worddeed/blob/5aae577d4d09f5fb93bc5dd93704b18ed3eae368/applications/ceo-risk-preference/RESULTS.md) · [Final appendix, Table A13](../../resources/technical-appendix.docx)

## 3:45–4:30 · What could change the interpretation?

Return to Figure 1. Convergence asks whether the score tracks both narrative and behavioral measures. Checking it against an independent measure of executive risk preference remains open. Suppose an industry shock changes both the language of earnings calls and research spending. If industry and firm conditions account for the association, the interpretation as a personal trait weakens.

Or shuffle the narrative features and fit the same models. If shuffled topics predict just as well, topic selection has little claim to the result. WordDeed provides the results, reproduction instructions, and final appendix. The next tests will carry alternative AI selections through prediction and assessment, and examine shared causes and additional constructs.

**On screen**

An industry shock can affect both earnings-call language and spending. A permutation test illustrates an alternative explanation. The appendix proposes carrying all twelve topic selections through learning and dividend assessment, prediction averaging, and selection-informed regularization. Human-reference assessment and independent construct validation remain open. The proposal reports a political-ideology trial whose results are not packaged here.

[Inspect the CEO results](https://github.com/jianghan6666/worddeed/blob/5aae577d4d09f5fb93bc5dd93704b18ed3eae368/applications/ceo-risk-preference/RESULTS.md) · [Reproduce the analysis](https://github.com/jianghan6666/worddeed/blob/5aae577d4d09f5fb93bc5dd93704b18ed3eae368/applications/ceo-risk-preference/REPLICATION.md) · [Read the planned tests](../../index.html#open-tests) · [Proposal and evidence scope](../../resources/README.md)
