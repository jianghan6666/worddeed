# Roadmap

The proposed framework integrates behavioral and narrative cues to develop a synthesized proxy. The next scientific tests ask whether their predicted common variation adds useful measurement information and whether it reflects the intended microfoundation. The [CEO illustration](../applications/ceo-risk-preference/README.md) provides a starting point; this roadmap records proposed work separately from the implemented and reproduced package.

## 1. Strengthen input and screening evidence

Resolve remaining historical alignment limits where evidence permits, document sentiment and topic representation, and assess the screening procedure against task-specific independent references. Specify sensitivity questions and selection criteria before inspecting downstream consequences.

**Done when:** input mappings and annotation procedures are reproducible, and an assessment report distinguishes stability, agreement, accuracy, and unresolved cases.

## 2. Propagate AI choices through measurement

Refit the twelve completed topic selections under the same grouped folds; compare them with all topics and conventional feature selectors. Evaluate equal-weight prediction averaging and selection-frequency-informed Ridge penalties, including standard Ridge in the tuning grid. Tune only within training data, and retain unsuccessful configurations. These are proposed extensions in the final appendix, not completed findings.

**Done when:** the alternative selections have linked prediction and dividend outputs, common comparison rules, and a report of sensitivity and any gains or losses.

## 3. Assess what the proxy measures

Evaluate competing interpretations such as industry, opportunity, and disclosure practices. Examine target missingness, timing, sample selection, and first-stage uncertainty. The final appendix Table A13 reports eight models adjusting for both a narrative proxy and actual R&D. Add their code, input definition, and reproducible outputs to the existing 25-model chain, then define independent criteria and fair performance comparisons with alternative measures.

**Done when:** a prespecified assessment reports supporting evidence, counterevidence, uncertainty, and limits. Predictive fit and significant associations alone do not establish psychological meaning.

## 4. Support another application

The [application collection](../applications/README.md) separates the packaged CEO case from the shared framework, and a [planning template](../applications/_template/README.md) describes what a new case must specify. The proposal reports an additional political-ideology trial, whose results are not packaged in this repository. Next, separate the remaining application-specific adapter assumptions behind explicit interfaces and implement a second authorized study with its own construct definition, target, timing and assessment plan.

**Done when:** the second study runs from its own inputs and documents what transferred, what changed, and what its results support.

## 5. Complete the fresh-screening input route and strengthen runtime checks

The newer API adapter implements one P0 three-reader analysis, but its preflight against the released archive failed on 21 missing required files before any provider call. Supply a complete authorized input export, preserve its scientific identities and pass the actual no-call preflight. Model availability, source-transmission conditions and a separately recorded live run are additional requirements. This work does not replace the working saved-reader replay or recreate the historical twelve-trial native-reader study.

Strengthen the generic dispatcher's required-artifact checks and input checks before each new stage. The standard reproduction wrapper already verifies restored package members; direct/manual routes need the same coverage. Synthetic diagnostics identified these gaps, not false completion in the recorded empirical run.

**Done when:** the released fresh-input tree passes the adapter's checks, runtime hardening passes focused software checks, and any later live run is separately documented. Fixture success is not live execution or scientific validation.

## Recorded implementation and reproduction

- A packaged four-step CEO speech/R&D application: topic representation, twelve-trial relevance screening, grouped Ridge/XGBoost prediction, and downstream dividend-policy analysis.
- Saved aggregate screening results, prediction metrics, and regression tables in the [worked example](../applications/ceo-risk-preference/README.md).
- A connected coordinator with stage adapters, saved state, and resume, demonstrated with invented inputs.
- A prior recorded [fresh-download connected empirical reproduction](../applications/ceo-risk-preference/replication/verification/CONNECTED_REPRODUCTION.json): saved screening replay, new Ridge/XGBoost fits, three-seed checks, raw-data reconstruction and all 25 Stata models.
- Existing user guides, an introduction and a narrated walkthrough. The local workflow-first presentation revision is separate from the deployed edition.

### Prior connected empirical run

The connected workflow ran from freshly downloaded inputs on Windows with Python 3.11.7, then continued the verified regression inputs in Stata 18. New prediction scores fed the full raw-data route. The original prediction, seed, finance, matching, regression and presentation checks passed.

**Completion evidence:** [REPLICATION.md](../applications/ceo-risk-preference/REPLICATION.md) links the code, input inventories, downloadable outputs, environment records and new verification. The run preserved input identities and original scientific settings, and reused completed fits after hash checks. The saved-representation boundary and historical alignment limits remain explicit.

The connected reproduction covers the original 25 downstream models. It does not reproduce the later narrative benchmark or eight Table A13 models reported in the submitted appendix. It starts from saved topic representation and judgments; it does not regenerate topics, sentiment or AI labels. The 2 November review checked the demo and saved-reader replay and inspected prior numerical receipts without repeating fitting or Stata estimation.

Update milestone status when evidence changes, linking the actual result. Researchers retain scientific decisions; preserve each packaged example's original specification.

