# From managerial speech to behavioral prediction

Complete transcript · 9 minutes 50 seconds · synthetic Kokoro narration.

No empirical stages were run during video production. The three-topic example is an offline fixture. Captions are burned into the MP4; the VTT is optional.

Source: assembled implementation at commit `029541eefdc4d32f8e72e58d3618f62b9cf5aeec`. Chapter starts come from measured sentence audio and are rounded to 24 fps.

## 00:00 · What does the prediction measure?

This project studies how managerial speech relates to firm behavior, with CEO risk preference as the first measurement setting. Speech may express a manager's perspective, but it also serves an audience. Research and development spending reflects choices, opportunities, and constraints. A model can learn an association between these two sources. Whether its prediction measures risk preference requires separate evidence. This walkthrough explains the four existing stages, their assembled agent connections, and what the offline demonstration actually establishes.

Related guide: [Four-step workflow](../WORKFLOW.md) · [Completed example](../../examples/ceo-risk-preference/README.md) · [Runtime](../../agent_system/empirical/README.md).

## 00:41 · Existing methods, newly connected

The scientific packages and their received results already exist. The new work connects them through stage adapters and a resumable workflow. During this assembly, no fresh scientific screening, empirical model training, finance reconstruction, or Stata estimation was executed. The earlier eight-topic agent demonstration remains available. The connected demonstration uses three invented topics and scripted model replies. These distinctions matter: received results, implemented interfaces, and newly executed empirical evidence are different claims.

Related guide: [Four-step workflow](../WORKFLOW.md) · [Completed example](../../examples/ceo-risk-preference/README.md) · [Runtime](../../agent_system/empirical/README.md).

## 01:22 · A fixed catalogue of 354 topics

Step one connects the saved topic catalogue and the delivered matrix of topic densities. The study fixes three hundred and fifty-four topic columns. The adapter checks the catalogue, matrix dimensions, and model identity when inference is requested. Optional inference reuses the existing topic-model code. For the saved matrix, historical row ordering is taken from the delivery. This assembly does not independently authenticate that original ordering. It also retains the supplied sentiment input. It does not create sentiment measurements for a new corpus.

Related guide: [Four-step workflow](../WORKFLOW.md) · [Completed example](../../examples/ceo-risk-preference/README.md) · [Runtime](../../agent_system/empirical/README.md).

## 02:04 · Three readers, one sealed barrier

Fresh screening begins with three independent readers. Each reader labels the complete descriptor catalogue for binary relevance to risk preference. The readers do not divide the topics between them. Each makes an initial judgment about all three hundred and fifty-four topics. All three initial responses must be sealed before any reader receives source passages. This is the barrier between the two reading stages. The fresh-reader default is GPT six Astra at extra-high reasoning effort. These defaults were not validated with live calls during assembly.

Related guide: [Four-step workflow](../WORKFLOW.md) · [Completed example](../../examples/ceo-risk-preference/README.md) · [Runtime](../../agent_system/empirical/README.md).

## 02:46 · Own history, then a majority

In stage B, each reader continues its own history through eighteen review pages containing one thousand and sixty-two source passages. Each sees its own initial labels and the source material, without the other readers' votes. Initial judgments remain separately available. The original toolkit exports a two-of-three majority for relevance, alongside reasons and minority votes. Confidence does not weight the votes. The delivered primary selection contains three hundred and twenty-one topics from Astra, extra-high effort, repetition one. Its use does not establish superiority over other trials.

Related guide: [Four-step workflow](../WORKFLOW.md) · [Completed example](../../examples/ceo-risk-preference/README.md) · [Runtime](../../agent_system/empirical/README.md).

## 03:30 · Topic features + aggregate sentiment

Step three passes the selected topic identifiers to the supplied input builder and training script. The predictors are selected topic features and aggregate sentiment. The outcome is research and development spending divided by total assets. The original Ridge and XGBoost implementations retain their seeds and tuning grids. Firm and CEO connected groups define five folds. Each out-of-fold score comes from a model trained outside its held-out group. Firms that share a CEO remain in the same group. The saved topic representation remains fixed. These are contemporaneous predictions, rather than forecasts of future behavior. The implemented method does not first collapse topics into the earlier blueprint’s scalar narrative measure.

Related guide: [Four-step workflow](../WORKFLOW.md) · [Completed example](../../examples/ceo-risk-preference/README.md) · [Runtime](../../agent_system/empirical/README.md).

## 04:26 · What enters the supervised mapping?

The supplied target replaces missing research and development spending with zero, provided that total assets are positive. Rows with missing or nonpositive assets do not enter model training. They still receive held-out predictions. Selected topic densities use a centered log-ratio transformation. Topic features and aggregate sentiment are standardized. Imputation and scaling are fitted within training data. Target winsorization also uses training data, and tuning stays inside the training folds. Missing spending can mean missing disclosure. Consequently, the prediction can reflect reporting and industry patterns as well as managerial behavior.

Related guide: [Four-step workflow](../WORKFLOW.md) · [Completed example](../../examples/ceo-risk-preference/README.md) · [Runtime](../../agent_system/empirical/README.md).

## 05:15 · New scores enter the original matcher

Step four receives the newly generated score file through the original local matcher. The original rich identity panel remains the matching source. The adapter checks panel keys and fold identities. Negative out-of-fold predictions are clipped to zero, then multiplied by one hundred. This score is in percentage points of predicted research and development relative to assets. It is not a percentile rank. Model preparation retains the same twenty-five formulas. It is a separate stage from estimation in Stata. A completed preparation stage means that model inputs and the estimation script are ready. It does not mean regressions have been run.

Related guide: [Four-step workflow](../WORKFLOW.md) · [Completed example](../../examples/ceo-risk-preference/README.md) · [Runtime](../../agent_system/empirical/README.md).

## 06:05 · Dividend-payer status is the outcome

The downstream outcome is whether the firm pays dividends. The supplied specifications use logit models. Nine replication specifications accompany sixteen score specifications, for twenty-five formulas in total. The score specifications enter Ridge and XGBoost separately, alongside financial and compensation controls and industry and year effects. One set includes actual research and development relative to assets and its missingness indicator. The other omits both. These comparisons examine conditional association with dividend payment. They do not by themselves establish causality or construct validity.

Related guide: [Four-step workflow](../WORKFLOW.md) · [Completed example](../../examples/ceo-risk-preference/README.md) · [Runtime](../../agent_system/empirical/README.md).

## 06:53 · Four tools, one durable workflow

The coordinator has four named tools: get status, run stage, read result, and finish. These connect the model to the shared workflow. The dispatcher enforces stage order. Both direct execution and agent execution use the same saved state and artifact checks. A coordinator's completion claim cannot complete an unfinished stage. The saved outputs determine completion, and completed artifacts are checked again on resume. The coordinator cannot issue arbitrary commands or redefine the scientific method. Constructs, specifications, and the interpretation of evidence remain research decisions.

Related guide: [Four-step workflow](../WORKFLOW.md) · [Completed example](../../examples/ceo-risk-preference/README.md) · [Runtime](../../agent_system/empirical/README.md).

## 07:39 · A small, observable handoff

The offline example uses two fabricated rows and three invented topics. Its selection contains topic one and topic three. For the first row, the selected weights sum to zero point seven. For the second, they sum to zero point eight. Those toy scores are written to a file and carried into the step four input. They are wiring arithmetic, with no trained-model or scientific interpretation. The saved summary states that this is a demonstration, with no live model calls, no training, and no estimation.

Related guide: [Four-step workflow](../WORKFLOW.md) · [Completed example](../../examples/ceo-risk-preference/README.md) · [Runtime](../../agent_system/empirical/README.md).

## 08:17 · Resume from recorded artifacts

The connected demonstration was executed and then resumed for this walkthrough. Both runs returned demonstration complete. State, event history, stage requests, and results provide a record of the connection. Resume verifies completed artifacts rather than relying on a narrative assurance. Fresh screening also preserves reader requests, first responses, and sealed pages. Invalid or unresolved attempts remain visible for explicit recovery. The adapter does not silently repair labels or repeat uncertain first requests. This is a property of the workflow, not a guarantee of scientific correctness.

Related guide: [Four-step workflow](../WORKFLOW.md) · [Completed example](../../examples/ceo-risk-preference/README.md) · [Runtime](../../agent_system/empirical/README.md).

## 09:01 · Integration is one layer of evidence

The assembly's recorded checks cover handoffs, reader independence, stage ordering, and recovery. They use fixtures and mocked scientific execution. The original scientific packages and their results remain distinct from these checks. Reproduction requires the complete assets and the specified scientific runtimes. Prediction of research and development spending does not by itself establish psychological risk preference, causality, or superiority over other measures. The current contribution is a connected and inspectable implementation. An empirical run and independent construct validation remain separate research tasks.

Related guide: [Four-step workflow](../WORKFLOW.md) · [Completed example](../../examples/ceo-risk-preference/README.md) · [Runtime](../../agent_system/empirical/README.md).
