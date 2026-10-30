# Start and resume an AI Microfoundation Proxy study

Start with the [completed example](examples/ceo-risk-preference/README.md) to see the method and outputs. Use the [reviewer replication guide](REPLICATION.md) to reproduce the supplied study, or the [runtime guide](agent_system/empirical/README.md) for configuration and other compatible inputs.

## Read the current state

Read the study configuration, available inputs, prior decisions, and saved handoff. Establish the construct, observation unit, period, narrative evidence, behavioral target, and intended use of the proxy. Reuse completed work when its inputs and scientific settings still match.

## Researcher decisions

The researcher chooses the construct and relevance rules, scientific model, sample and timing, assessment criteria, and interpretation. Agents can recommend changes with reasons. Record an adopted change with its rationale and the affected version; do not silently change a rule to obtain a preferred result.

## Follow the four steps

1. [Topics](workflows/01-topics.md): bind the catalogue, density inputs, and observation identities.
2. [Screening](workflows/02-screen-topics.md): preserve independent initial readings, the source-release barrier, same-reader review, and all votes.
3. [Prediction](workflows/03-build-proxy.md): apply the specified target, features, grouped fitting, and score definition.
4. [Assessment](workflows/04-assess-proxy.md): match scores, prepare analysis, estimate, and interpret the evidence.

The coordinator owns dispatch and the integrated record. Readers author their judgments. Computational tools calculate numerical results.

## Choose an execution route

| Route | Purpose | What you provide |
| --- | --- | --- |
| Offline demo | Inspect coordinator, handoffs, persistence, and resume | Python 3.11+ only |
| Empirical reproduction | Execute the current method using a saved selection | Compatible external study packages, catalogue, selection, dependencies, and Stata for estimation |
| Fresh screening | Obtain a new triad and propagate its selection | The above plus complete source packets, compatible screening toolkit, and model access |

Real execution uses explicit local paths. The repository does not supply empirical datasets or full reader evidence. The adapters target the demonstrated CEO/R&D study; extending the method to another setting requires explicit configuration and implementation work.

## Run and hand off

For a first inspection:

```sh
python3 -m agent_system.empirical.demo --out .local/demo
python3 -m agent_system.empirical.demo --out .local/demo --resume
```

Use the [runtime guide](agent_system/empirical/README.md) for real-study setup. Check actual outputs before claiming completion. Preserve failed and interrupted attempts. Keep credentials in the environment.

Save a concise handoff alongside the run: configuration and input versions, completed stages and artifact paths, unresolved decisions, failures, and the next command. The [roadmap](ROADMAP.md) identifies further implementation and assessment milestones.
