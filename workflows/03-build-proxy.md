# Estimate the behavioral proxy

## Inputs

Selected topics, narrative features, behavioral target, observation keys, and explicit model settings.

## Procedure

The current study uses selected topic features plus aggregate sentiment to predict R&D/assets with Ridge and XGBoost. Preserve the specified firm–CEO groups, five folds, training-only transformations, tuning rules, and target handling. Keep out-of-fold and full-sample scores distinct.

## Output

Scores, fold identities, model receipts, fit diagnostics, and uncertainty limits.

Use the [runtime guide](../agent_system/empirical/README.md) for commands. The [completed example](../examples/ceo-risk-preference/README.md) illustrates the delivered method; the [roadmap](../ROADMAP.md) identifies further assessment.
