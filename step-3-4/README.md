# Step 3 and Step 4 collaboration delivery

Received on 28 October 2026; source packages dated 27 October. This folder integrates the supplied code, methods, models, data and results into the permanently private project. Code and reports are browsable below. The complete packages, including large inputs and models, are in the [private release](https://github.com/joyzhzh/ai-microfoundation-proxy/releases/tag/reviewer-replication-2026-10-30).

| Package | Delivered scope | Start here |
|---|---|---|
| Step 3 | Component-to-firm-year inputs, Ridge/XGBoost training, grouped cross-fitted scores, fitted models and robustness results | [README](packages/step3_risk_score_collaborator_20261027/README.md), [method](packages/step3_risk_score_collaborator_20261027/docs/METHOD.md) |
| Step 4, full | Raw finance/market/compensation inputs, source identity matching and all 25 regressions, with retained replay checks | [README](packages/step4_full_from_raw_20261027/README.md), [reproduction scope](packages/step4_full_from_raw_20261027/docs/SCOPE_AND_COMPARISON.md), [results](packages/step4_full_from_raw_20261027/results/REPLAYED_TABLES.md) |
| Step 4, compact | The 16 score regressions from frozen Stata inputs, with and without actual R&D controls | [README](packages/step4_rd_score_collaborator_20261027/README.md), [research report](packages/step4_rd_score_collaborator_20261027/docs/REPLICATION_REPORT.md), [results](packages/step4_rd_score_collaborator_20261027/results/RESULTS.md) |

## Connection to the completed Step 2 work

Step 3 uses **primary `b1-gpt-6-astra-P0-xhigh`**, with 321 selected topics, 33 excluded and none unresolved. Its selection JSON is byte-identical to the [completed Step 2 handoff](../step-2-twelve-trial-pilot/results/primary/handoffs/b1-gpt-6-astra-P0-xhigh/selected_topics.json): SHA-256 `be14a1f557fbb28a9f4702af15ec49d9fb0ea7534e7701fd5cc301872d4461e9`. All twelve fitted-model feature specifications use the same ordered 321 topic columns. This records the configuration used by the delivered analysis; it does not establish that this classifier is superior to the other completed trials.

Evidence paths embedded in the selection JSON are relative to the original [Step 2 results package](../step-2-mvp-simple/experiment/expanded-ai-pilot/results-2026-10-21/README.md), not the Step 3 data folder. Preserve the earlier primary/supplementary distinction.

## What the delivered method computes

Step 3 predicts **R&D/assets from the selected topic features and aggregate sentiment** using firm–CEO connected-component grouped five-fold cross-fitting. It supplies scores for 29,506 firm-years; 29,191 have the target. Reported cross-fitted R² is 0.5351 for Ridge and 0.6128 for XGBoost. The delivered method does not first calculate the separate density × topic-specific sentiment scalar N or fit `f(N, controls)` described in the earlier blueprint. Those earlier specifications remain historical alternatives; intake does not change the supplied scientific method.

Step 4 uses **100 × max(OOF predicted R&D/assets, 0)**. It preserves the supplied Step 3 scores without retraining and matches them to the financial/CEO data. The compact package contains 2,967 strict input rows across 600 firms and 16 score regressions. The full package additionally rebuilds financial variables and identity matching and supplies 25 regressions. The author reports negative score coefficients with company-clustered p < .01 in all 16 score models. These are conditional associations from a generated proxy, not evidence by themselves of psychological construct validity, causality, or superiority over separate N and B measures. See the supplied methods for sample selection, R&D missingness and first-stage uncertainty limits.

## Download and restore all inputs and models

The Git view is intentionally a reading copy. Links to omitted binary/data files inside the original READMEs work after restoring the complete archive. `DELIVERY.json` inventories every exported file and the browsable subset; it includes original and exported hashes.

From the repository root, with access to this private repository:

```sh
gh release download reviewer-replication-2026-10-30 \
  --repo joyzhzh/ai-microfoundation-proxy \
  --pattern 'step3-step4-2026-10-28.tar.gz.part*' --pattern 'DELIVERY.json' \
  --dir .local/step3-step4-download
python scripts/restore_review_bundle.py .local/step3-step4-download/DELIVERY.json \
  --out .local/step3-step4-restored
```

Download all 17 archive parts and the manifest into the same directory. The output directory must be new. Restoration checks the archive and each member before reporting success. Complete packages are then under `.local/step3-step4-restored/packages/`; original supplied manifests are under `source-manifests/`. Use each restored package's README for execution. No new data acquisition is needed.

- Step 3's complete saved-model verification needs the supplied compatible Python 3.11 environment (including scikit-learn 1.2.2 and XGBoost 2.1.1). Avoid loading its joblib models in an incompatible environment; portable JSON models are also supplied.
- Full Step 4 data reconstruction uses its pinned Python dependencies. Regression replay requires Stata; the supplied results were produced with StataNow/SE 19.5. The full package supports a data-only run without Stata.
- Keep the compact and full Step 4 routes separate. Neither retrains the first-stage score model.

## Intake checks and export changes

The [intake record](INTAKE_CHECKS.json) distinguishes inspection here from the supplied historical empirical replay. Source originals remain unchanged. Of 328 entries in the three supplied manifests, 327 match received files. The sole mismatch is the Step 3 README's stale size/hash entry. Export manifests bind the received bytes, and the original supplied manifests remain available under [source-manifests](source-manifests/).

One personal Windows source-file path in the full Step 4 `reference/regression/table_payload.json` is replaced with a portable article reference. Its article hash, numerical tables and all other values are preserved. The corresponding export manifest is refreshed. Operating-system metadata is excluded. The file-level inventory records each change; no model, dataset, coefficient or scientific setting is modified.

```sh
python step-3-4/verify.py
```

This verifies the browsable files, export-manifest coverage and exact Step 2 selection linkage using the standard library. Complete archive restoration verifies all data and models. Intake does not claim a fresh model-training or Stata-reproduction run.

## Connected reproduction

The [reviewer replication guide](../REPLICATION.md) connects the delivered packages to the empirical adapters, with fresh model fitting, downstream reconstruction and numerical checks. The [new verification record](../replication/verification/README.md) distinguishes newly executed results from these historical intake checks. The earlier blueprint’s separate N/B/S comparison is not claimed as completed by these different delivered models.

Data and source-derived research identifiers are for authorized private collaboration under the source vendors' conditions. This delivery does not publish the website or change repository visibility.
