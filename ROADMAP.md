# Roadmap

The [completed example](examples/ceo-risk-preference/README.md) provides the empirical foundation. This roadmap identifies the next implementation and research milestones; it is not a schedule or a claim that future work is complete.

## Completed

- A four-step CEO speech/R&D application: topic representation, twelve-trial relevance screening, grouped Ridge/XGBoost prediction, and downstream dividend-policy analysis.
- Saved aggregate screening results, prediction metrics, and regression tables in the [worked example](examples/ceo-risk-preference/README.md).
- A connected coordinator with stage adapters, saved state, and resume, demonstrated with invented inputs.
- A [fresh-download connected empirical reproduction](replication/verification/CONNECTED_REPRODUCTION.json): saved screening replay, new Ridge/XGBoost fits, three-seed checks, raw-data reconstruction and all 25 Stata models.
- User guides, an introduction, and a narrated walkthrough.

## 1. Execute the complete example through the agent — completed

The connected workflow ran from freshly downloaded inputs on Windows with Python 3.11.7, then continued the verified regression inputs in Stata 18. New prediction scores fed the full raw-data route. The original prediction, seed, finance, matching, regression and presentation checks passed.

**Completion evidence:** [REPLICATION.md](REPLICATION.md) links the code, input inventories, downloadable outputs, environment records and new verification. The run preserved input identities and original scientific settings, and reused completed fits after hash checks. The saved-representation boundary and historical alignment limits remain explicit.

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
