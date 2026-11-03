# Try and inspect the WordDeed workflow

Organizational narratives and behavior each offer imperfect clues to beliefs and preferences. WordDeed explores whether combining them can produce more useful measures. Its four-step workflow discovers topics in a corpus, uses LLM readers to judge their relevance to a construct, predicts a behavioral measure from the retained narrative features, and assesses the resulting synthesized measure against a separate outcome.

Reproducibility makes that design open to scrutiny. A researcher can inspect which topics were retained, follow the saved judgments into the selected features, and trace those features through prediction and assessment. Keeping these decisions visible provides a basis for testing alternatives as the framework develops. The value of the prototype is this inspectable sequence; whether it improves measurement remains an empirical question.

## Start with the question you want to answer

| Your question | Suggested route | What you can learn |
|---|---|---|
| How do the steps connect? | [Try the offline demonstration](REPLICATION_DETAILS.md#try-the-offline-workflow-demonstration) | Inspect stage handoffs and saved-state resume using a small synthetic example. It needs no model account or empirical-data download; the replies and numerical outputs are invented. |
| Can I check how the AI judgments became inputs? | [Replay the saved screening analysis](REPLICATION_DETAILS.md#recalculate-the-saved-screening-results) | Recalculate selections from archived reader records, including disagreement and missingness. This route makes no new AI calls. |
| What evidence supports the implemented application? | [Inspect the prior connected-run outputs](REPLICATION_DETAILS.md#inspect-the-prior-connected-run-outputs) | Follow the recorded computation and its scope without fitting the models again. |
| Can I execute the empirical chain myself? | [Use the detailed reproduction instructions](REPLICATION_DETAILS.md#execute-the-maintained-empirical-chain) | Rebuild and estimate the maintained application in its supported environment, with authorized inputs and the original numerical checks. This is optional technical depth. |

The demonstration and saved-screening replay passed the 2 November review. The repository also retains a prior verified empirical run; this review did not repeat its model fitting or Stata estimation.

## A concrete illustration, with room to extend

The CEO example connects conference-call narratives to R&D investment, then examines the synthesized measure in relation to dividend payment. It shows how the same workflow can join language, a behavioral anchor and a separate empirical assessment. The optional evidence routes above let readers examine this illustration in more depth. The later submitted narrative benchmark and Table A13 extension are outside the current executable reproduction.

For another organizational construct, a researcher would need to specify the relevance criteria, a defensible behavioral anchor, suitable data and an assessment that tests the measure's usefulness. The existing adapters implement the CEO example; another application needs its own scientific specification and compatible adapters. Preserving inputs and decisions is what allows others to evaluate those choices rather than accept a score without examining its construction.

## What is ready, and what still needs development

The saved-judgment route can be checked now. **Fresh AI screening is not ready to run from the current release alone:** the newer API adapter's input preflight fails on 21 missing required files, before any provider call. This is compatible with successful saved replay because the two routes require different inputs. See the [precise input gap and prerequisites](REPLICATION_DETAILS.md#fresh-ai-screening-code-present-release-inputs-incomplete).

Replaying saved records establishes computational traceability, not label accuracy. Prediction and downstream association also remain distinct from construct validity and causal inference. Expanded screening comparisons, independent validation and easier reuse are development tasks. [The execution reference](REPLICATION_DETAILS.md) retains the code pins, manifests, commands, access conditions and exact verification limits for readers who want to go further.
