# Roadmap

The [completed example](../applications/ceo-risk-preference/README.md) provides the empirical foundation. This roadmap identifies the next implementation and research milestones; it is not a schedule or a claim that future work is complete.

## Completed

- A four-step CEO speech/R&D application: topic representation, twelve-trial relevance screening, grouped Ridge/XGBoost prediction, and downstream dividend-policy analysis.
- Saved aggregate screening results, prediction metrics, and regression tables in the [worked example](../applications/ceo-risk-preference/README.md).
- A connected coordinator with stage adapters, saved state, and resume, demonstrated with invented inputs.
- A [fresh-download connected empirical reproduction](../applications/ceo-risk-preference/replication/verification/CONNECTED_REPRODUCTION.json): saved screening replay, new Ridge/XGBoost fits, three-seed checks, raw-data reconstruction and all 25 Stata models.
- User guides, an introduction, and a narrated walkthrough.

## 1. Execute the complete example through the agent — completed

The connected workflow ran from freshly downloaded inputs on Windows with Python 3.11.7, then continued the verified regression inputs in Stata 18. New prediction scores fed the full raw-data route. The original prediction, seed, finance, matching, regression and presentation checks passed.

**Completion evidence:** [REPLICATION.md](../applications/ceo-risk-preference/REPLICATION.md) links the code, input inventories, downloadable outputs, environment records and new verification. The run preserved input identities and original scientific settings, and reused completed fits after hash checks. The saved-representation boundary and historical alignment limits remain explicit.

## 2. Strengthen input and screening evidence

Resolve remaining historical alignment limits where evidence permits, document sentiment and topic representation, and assess the screening procedure against task-specific independent references. Specify sensitivity questions and selection criteria before inspecting downstream consequences.

**Done when:** input mappings and annotation procedures are reproducible, and an assessment report distinguishes stability, agreement, accuracy, and unresolved cases.

## 3. Propagate AI choices through measurement

Refit the twelve completed topic selections under the same grouped folds; compare them with all topics and conventional feature selectors. Evaluate equal-weight prediction averaging and selection-frequency-informed Ridge penalties, including standard Ridge in the tuning grid. Tune only within training data, and retain unsuccessful configurations. These are proposed extensions in the final appendix, not completed findings.

**Done when:** the alternative selections have linked prediction and dividend outputs, common comparison rules, and a report of sensitivity and any gains or losses.

## 4. Assess what the proxy measures

Evaluate competing interpretations such as industry, opportunity, and disclosure practices. Examine target missingness, timing, sample selection, and first-stage uncertainty. The final appendix Table A13 reports eight models adjusting for both a narrative proxy and actual R&D. Add their code, input definition, and reproducible outputs to the existing 25-model chain, then define independent criteria and fair performance comparisons with alternative measures.

**Done when:** a prespecified assessment reports supporting evidence, counterevidence, uncertainty, and limits. Predictive fit and significant associations alone do not establish psychological meaning.

## 5. Support another application

The [application collection](../applications/README.md) now separates the completed CEO case from the shared framework, and a [planning template](../applications/_template/README.md) describes what a new case must specify. The proposal reports an additional political-ideology trial, whose results are not packaged in this repository. Next, separate the remaining application-specific adapter assumptions behind explicit interfaces and implement a second authorized study with its own construct definition, target, timing and assessment plan.

**Done when:** the second study runs from its own inputs and documents what transferred, what changed, and what its results support.

Update milestone status when evidence changes, linking the actual result. Researchers retain scientific decisions; completed examples keep their original specification.
