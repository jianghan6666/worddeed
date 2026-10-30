# AI Microfoundation Proxy

**A workflow for constructing and assessing proxies from what people say and what they do.**

AI Microfoundation Proxy connects narrative evidence, AI-assisted topic screening, behavioral prediction, and downstream analysis. The first application studies CEO risk preference using earnings-call speech and R&D investment. Researchers define the construct and interpret the evidence; the agent coordinates the workflow and calls reusable computational tools.

**Reviewer results:** [Full four-step results](RESULTS.md) · [PDF report](results/report.pdf) · [Complete results download](https://github.com/joyzhzh/ai-microfoundation-proxy/releases/tag/full-results-2026-10-31)

[Introduction](docs/index.html) · [Video](docs/video/four-step-agent.mp4) · [Completed example](examples/ceo-risk-preference/README.md) · [Roadmap](ROADMAP.md) · [Workflow guide](WORKFLOW.md)

## What is AI Microfoundation Proxy?

Many organizational theories depend on beliefs, preferences, and judgments that researchers cannot observe directly. Speech offers one source of evidence; choices offer another. AI Microfoundation Proxy makes the connection between them explicit and inspectable.

You bring a construct, narrative material, a behavioral outcome, and a study setting. The workflow represents the narrative as topics, screens those topics for relevance, estimates a model linking narrative features to behavior, and passes the resulting scores to downstream analysis. You leave with **selected topics and their reasons, predicted behavioral scores, analysis outputs, and a saved execution record**.

The current empirical method predicts R&D/assets from selected topic features and aggregate sentiment. Its interpretation as CEO risk preference requires evidence beyond predictive fit or regression significance.

[![Watch the AI Microfoundation Proxy walkthrough](docs/video/poster.jpg)](docs/video/four-step-agent.mp4)

[Watch the video](docs/video/four-step-agent.mp4) · [Read the narration](docs/video/transcript.md) · [English captions](docs/video/four-step-agent.en.vtt). The local introduction below plays the video in the page.

## How it works

Agents follow explicit workflows and use tools for computation and record keeping. Saved outputs connect the stages. The researcher retains scientific decisions.

| Responsibility | Work | Output |
| --- | --- | --- |
| **Coordinator** | Reads the study configuration, dispatches stages, checks outputs, and resumes saved work. | An integrated execution record. |
| **Topic preparation** | Binds the topic catalogue, density inputs, and observation identities. | Ordered topics and their distributions. |
| **Screening readers** | Independently evaluate topic relevance, then review source passages in their own histories. | Selected topics, reasons, and minority votes. |
| **Proxy estimation** | Fits the specified grouped prediction models. | Scores, folds, models, and fit diagnostics. |
| **Downstream analysis** | Matches scores to the study panel and prepares and estimates the specified models. | Analysis inputs, tables, and diagnostics. |

The executable system has one coordinator and, for fresh screening, three independent model readers. Topic preparation, proxy estimation, and downstream analysis use Python adapters and scientific programs. The [role guides](agents/coordinator.md) explain these responsibilities.

### Multi-layered architecture

```text
                       HUMAN RESEARCHER
                              |
                         Coordinator
                              |
AGENTS      [ Independent screening readers ] <---+
                              |                  |
WORKFLOWS   [ Topics / Screen / Predict / Assess ] +--- RESOURCES
                              |                  |    Construct definition,
TOOLS       [ Python adapters + study programs ] <+    inputs and model settings
                              |
RECORDS     [ Decisions / outputs / saved state ]
```

### Four-step workflow

1. **Represent the narrative.** Bind the topic catalogue and density inputs to the study's observations. Preserve the topic ordering and input identities.
2. **Screen for relevance.** Three readers evaluate the complete catalogue independently. Seal all initial responses before releasing source passages; continue each reader's own history. Export a two-of-three vote with every reason and minority judgment.
3. **Estimate the proxy.** Use selected topic features and aggregate sentiment to predict the behavioral target. The current study uses grouped five-fold Ridge and XGBoost models for R&D/assets.
4. **Assess the proxy.** Match scores to downstream observations, estimate the specified models, and examine what the results support and what remains unresolved.

```text
Narrative evidence → Topics → Relevance screening
                                      |
                                      v
                         Behavioral prediction
                                      |
                                      v
                         Downstream assessment
                                      |
                                      v
                       Researcher interpretation
```

The [workflow guide](WORKFLOW.md) connects these steps to the runtime. The coordinator's tools are `get_status`, `run_stage`, `read_result`, and `finish`; saved artifacts determine whether a stage is complete.

## Completed example

The [CEO speech, R&D, and dividend-policy example](examples/ceo-risk-preference/README.md) follows a completed empirical application:

- **354 topics**, screened in twelve trials with 36 readers.
- **321 selected topics** used with sentiment to predict R&D/assets.
- Scores for **29,506 firm-years**, with cross-fitted R² of **0.5351 for Ridge** and **0.6128 for XGBoost**.
- A downstream dividend-policy analysis with **16 score specifications**.

The example includes aggregate results and an explanation of the method and its limits. The runnable demo below uses invented inputs to demonstrate the connected agent; it does not rerun the empirical study.

## Quick start

### Run the local demo

Use **Python 3.11 or newer**. The offline demo needs only the standard library.

```sh
git clone https://github.com/joyzhzh/ai-microfoundation-proxy.git
cd ai-microfoundation-proxy
python3 -m agent_system.empirical.demo --out .local/demo
python3 -m agent_system.empirical.demo --out .local/demo --resume
```

Start with a new output directory. Inspect `summary.json`, `workflow/state.json`, and `workflow/events.jsonl` inside it. The coordinator, handoffs, state checks, and resume logic execute; model replies and numerical outputs are explicit fixtures. No API key, empirical data, training, or Stata is needed.

For real execution, provide compatible study inputs and scientific packages through local configuration. See the [runtime guide](agent_system/empirical/README.md) for dependencies and external input contracts. The included adapters target the current CEO/R&D specification; another application requires an explicit method adaptation.

### Start prompt

Open this repository in your coding-agent workspace:

```text
Act as the coordinator for an AI Microfoundation Proxy study. Follow ./WORKFLOW.md.
Read the current configuration and saved handoff first.

Help me state the construct, narrative inputs, behavioral target,
observation unit, period, and intended interpretation. Coordinate topic
preparation, independent relevance screening, proxy estimation, and
assessment through the existing tools.

Preserve input identities, scientific settings, reader independence,
minority judgments, and completed outputs. Bring research decisions
and interpretation to me with the evidence and remaining limits.
Save new inputs and execution records under .local/.
```

### Open the introduction

```sh
python3 -m http.server 8765 --bind 127.0.0.1 --directory docs
```

Open [the local introduction](http://127.0.0.1:8765/) to explore the method and play the video. `Ctrl+C` stops the server. GitHub displays `docs/index.html` as source.

## Example prompts

| Task | Prompt to the coordinator |
| --- | --- |
| **Frame** | “State the construct, unit, period, behavioral target, and intended use of the proxy. Identify the decisions I need to make.” |
| **Prepare** | “Check topic identities and observation alignment. Explain which links are verified and which depend on supplied provenance.” |
| **Screen** | “Run the agreed independent-reader protocol and retain all reasons, missing responses, and minority votes.” |
| **Estimate** | “Use the agreed prediction method. Show the sample, target handling, folds, and diagnostics.” |
| **Assess** | “Explain what the results support, competing interpretations, and the next useful validation.” |
| **Resume** | “Verify saved outputs, resume the next unfinished stage, and leave a concise handoff.” |

## Repository layout

```text
ai-microfoundation-proxy/
|-- README.md                 Introduction and setup
|-- AGENTS.md                 Instructions for coding agents
|-- WORKFLOW.md               Start and resume a study
|-- ROADMAP.md                Completed work and next milestones
|-- agents/                   Roles and responsibilities
|-- workflows/                Four-step research protocols
|-- tools/                    Guide to callable tools
|-- resources/                Method and input guide
|-- agent_system/             Connected runtime, adapters, and tests
|-- examples/
|   `-- ceo-risk-preference/   Worked study and aggregate results
|-- docs/                     Introduction, video, and narration
`-- .github/workflows/        Software checks
```

Keep your study inputs, local configurations, and run outputs in the ignored `.local/` directory. This package contains the user-facing workflow and aggregate example results; datasets and full research records are separate inputs.

## Roadmap

The [roadmap](ROADMAP.md) builds on the completed example: run the full empirical chain through the connected agent, strengthen input and screening evidence, assess construct interpretation, and prepare a second application. Each milestone identifies what evidence would establish completion.

## Design principles

- **Let the researcher set the measurement claim.** Construct definition, scientific specifications, and interpretation remain research decisions.
- **Connect stages through explicit outputs.** Preserve topic identities, observation keys, folds, and score files.
- **Keep judgments inspectable.** Retain independent readings, reasons, disagreement, and missingness.
- **Distinguish different kinds of evidence.** Software execution, reader agreement, predictive fit, and construct validity answer different questions.
- **Make work resumable.** Save inputs, decisions, outputs, and failures so another session can continue.

## Checks and use

Run the self-contained tests with Python 3.11+:

```sh
python3 -m unittest agent_system.tests.empirical.test_demo agent_system.tests.empirical.test_coordinator agent_system.tests.empirical.test_workflow agent_system.tests.empirical.test_external_inputs -v
```

The example reports supplied empirical results; software checks do not establish construct validity. Source-specific terms apply to any study inputs you provide. No open-source license is granted by this repository at present.
