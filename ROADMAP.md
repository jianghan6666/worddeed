# Roadmap

The [completed example](examples/completed-nbm/README.md) provides the empirical foundation. This roadmap identifies the next implementation and research milestones; it is not a schedule or a claim that future work is complete.

## Completed

- A four-step CEO speech/R&D application: topic representation, twelve-trial relevance screening, grouped Ridge/XGBoost prediction, and downstream dividend-policy analysis.
- Saved aggregate screening results, prediction metrics, and regression tables in the [worked example](examples/completed-nbm/README.md).
- A connected coordinator with stage adapters, saved state, and resume, demonstrated with invented inputs.
- User guides, an introduction, and a narrated walkthrough.

## 1. Execute the complete example through the agent

Run the connected workflow with authorized empirical inputs and compatible Python and Stata environments. Refit the prediction model, pass its new scores to the downstream stage, and compare declared outputs with the saved references.

**Done when:** a complete run preserves input identities, environment versions, stage outputs, diagnostics, comparison results, and a tested resume path. The offline fixture does not satisfy this milestone.

## 2. Strengthen input and screening evidence

Resolve remaining historical alignment limits where evidence permits, document sentiment and topic representation, and assess the screening procedure against task-specific independent references. Specify sensitivity questions and selection criteria before inspecting downstream consequences.

**Done when:** input mappings and annotation procedures are reproducible, and an assessment report distinguishes stability, agreement, accuracy, and unresolved cases.

## 3. Assess what the proxy measures

Evaluate competing interpretations such as industry, opportunity, and disclosure practices. Examine target missingness, timing, sample selection, and first-stage uncertainty. Define independent criteria and fair comparisons with alternative narrative and behavioral measures.

**Done when:** a prespecified assessment reports supporting evidence, counterevidence, uncertainty, and limits. Predictive fit and significant associations alone do not establish psychological meaning.

## 4. Support another application

Separate study-specific assumptions from reusable orchestration, provide an input template, and implement a second authorized study with its own construct definition, target, timing, and assessment plan.

**Done when:** the second study runs from its own inputs and documents what transferred, what changed, and what its results support.

Update milestone status when evidence changes, linking the actual result. Researchers retain scientific decisions; completed examples keep their original specification.
