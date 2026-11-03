# Understand, start and resume the WordDeed workflow

WordDeed proposes a workflow to integrate behavioral and narrative cues for the same latent microfoundational feature and develop a synthesized proxy. It maps narrative cues to an established behavioral proxy to extract their predicted common variation, then assesses what that measure supports. The four steps below retain the proposal's terminology; their intended scientific role must be distinguished from the implemented example.

For a first orientation, use the [reviewer guide](REVIEWER_GUIDE.md). The [CEO illustration](../applications/ceo-risk-preference/README.md) shows one application; the [capability note](WORKFLOW_CAPABILITY.md) explains what the prototype currently does. Identify the application and its scientific specification before running it. For a new case, follow [Adding an application](NEW_APPLICATION.md).

## Read the current state

Read the study configuration, available inputs, prior decisions, and saved handoff. Establish the construct, observation unit, period, narrative evidence, behavioral target, and intended use of the proxy. Reuse completed work when its inputs and scientific settings still match.

## Researcher decisions

The researcher chooses the construct and relevance rules, scientific model, sample and timing, assessment criteria, and interpretation. AI agents can recommend changes with reasons. Record an adopted change with its rationale and the affected version; do not silently change a rule to obtain a preferred result.

## Follow the four steps

1. **Characterizing the Corpus.** Establish a topic representation of the narrative material. The maintained route [binds a saved catalogue, densities and observation identities](workflows/01-topics.md); it does not retrain topics or regenerate sentiment.
2. **Topic decontextualization.** Select and interpret content relevant to the focal feature. The implemented [relevance screening](workflows/02-screen-topics.md) preserves independent initial readings, the source-release barrier, same-reader review and all votes. Agreement does not establish accuracy or removal of contextual influences.
3. **Synthesize the narrative and behavioral proxies.** Predict an established behavioral proxy from the retained narrative features. [Prediction](workflows/03-build-proxy.md) applies the specified target, features, grouped fitting and score definition; the CEO implementation uses selected topic densities and one overall sentiment feature.
4. **Validate the synthesized proxy.** Assess convergent and incremental validity, including whether the synthesized proxy contributes beyond narrative and behavioral proxies. The implemented [assessment](workflows/04-assess-proxy.md) matches scores, prepares and estimates the specified models, and leaves interpretation to researchers. Execution alone does not complete construct validation.

The coordinator owns dispatch and the integrated record. Readers author their judgments. Computational tools calculate numerical results.

## Choose an execution route

| Route | Purpose | What you provide |
| --- | --- | --- |
| Offline demo | Inspect coordinator, handoffs, persistence, and resume | Python 3.11+ only |
| Saved-reader replay | Recalculate recorded selections and compare saved handoffs | Released reader evidence and Python 3.11+; no new model calls |
| Empirical reproduction | Refit prediction and estimate the original 25 downstream models from saved representation and judgments | Compatible study packages, catalogue, selection, pinned Windows/Python environment, and compatible Stata |
| Fresh screening — inputs incomplete | Code implements one new P0 triad; the current release alone cannot run it | Complete verified source packets and toolkit, followed by separately authorized model access |

The actual fresh-screening preflight failed on 21 absent required release inputs before any provider call. Saved-reader replay works because it uses a different input arrangement. The [replication guide](../applications/ceo-risk-preference/REPLICATION.md) and [execution reference](../applications/ceo-risk-preference/REPLICATION_DETAILS.md) distinguish these routes and their prerequisites. The later submitted narrative benchmark and Table A13 extension are outside the recorded 25-model reproduction.

Real execution uses explicit local paths. The identified repository and its release assets were public when inspected on 2 November 2026; source-specific access conditions still apply. The adapters target the CEO/R&D study. Extending the method requires explicit scientific choices and compatible computation.

## Run and hand off

For a first inspection:

```sh
python3 -m agent_system.empirical.demo --out .local/demo
python3 -m agent_system.empirical.demo --out .local/demo --resume
```

Use the [CEO replication guide](../applications/ceo-risk-preference/REPLICATION.md) to choose a verification route, or the [runtime guide](../agent_system/empirical/README.md) for manual configuration and adaptation. The demonstration uses invented replies and numerical outputs; it makes no model calls and performs no empirical fitting or estimation. Check actual outputs before claiming completion. Preserve failed and interrupted attempts. Keep credentials in the environment.

Save a concise handoff alongside the run: configuration and input versions, completed stages and artifact paths, unresolved decisions, failures, and the next command. The [roadmap](ROADMAP.md) identifies further implementation and assessment milestones.
