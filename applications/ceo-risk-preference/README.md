# CEO risk preference

This demonstration study examines the feasibility of the proposed [AI-empowered proxy framework](../../README.md). It focuses on CEOs’ risk preference, using CEO language in conference calls as the ground for narrative evidence and R&D intensity as the behavioral proxy.

The framework integrates behavioral and narrative cues for the same latent microfoundational feature to develop a synthesized proxy. The CEO case illustrates how that workflow connects topic judgments, behavioral prediction and an empirical assessment.

| Proposed step | CEO application |
| --- | --- |
| Characterizing the Corpus | A saved topic model provides a common representation of conference-call language. |
| Topic decontextualization | Three LLM readers classify topic descriptors, then review common source passages within their own histories. Votes determine selection; reasons, disagreement and missing responses remain inspectable. |
| Synthesize the narrative and behavioral proxies | Ridge and XGBoost use selected topic densities and overall sentiment to predict R&D intensity. Each score excludes its connected firm–CEO group from model fitting. The predicted behavior serves as the synthesized proxy. |
| Validate the synthesized proxy | Dividend-payment models examine the proxy against a decision separate from its prediction target. Higher scores are associated with lower odds of dividend payment after the included controls. |

This is preliminary evidence of feasibility. Firm circumstances can shape both language and investment, and the topic set was adopted after preliminary predictive comparisons. Prediction and dividend associations do not establish a psychological ground truth or causal effect. The submitted appendix reports additional narrative-benchmark comparisons; their separate computation is outside the current 25-model reproduction.

Read the [results and interpretation](RESULTS.md), [evidence scope](EVIDENCE_SCOPE.md), or [replication routes](REPLICATION.md) for supporting detail. The [workflow guide](../../docs/WORKFLOW.md) explains the shared design; the [application guide](../../docs/NEW_APPLICATION.md) identifies the scientific choices and adapters another study would require.
