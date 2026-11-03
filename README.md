# WordDeed

**Match Words with Deeds: An AI-Empowered Proxy Framework for Organizational Microfoundations**

Organizational microfoundations—the cognitions, beliefs, and traits of individual members, as well as their collection and integration—can steer firms’ strategic decisions, operations, and performance. These latent cognitive and psychological properties are generally hard to observe and quantify.

Behavioral proxies face a problem of attribution: firms’ decisions and activities can be determined by many factors, including the specificities of the firm and its environment. Narrative proxies face a problem of authenticity: firms can strategically orchestrate public communications through social desirability and impression management. Both streams of proxies face potential measurement errors.

In this study, we strive to integrate the behavioral and narrative cues for the same latent microfoundational feature to develop a synthesized proxy. The workflow combines unsupervised topic modeling, LLM agents, and supervised machine learning to extract relevant narrative cues, map them with established behavioral proxies, and test the predicted common variation as a synthesized proxy.

[Basic workflow](docs/WORKFLOW.md) · [Try the prototype](#try-the-prototype) · [New applications](docs/NEW_APPLICATION.md) · [Project website](https://astounding-entremet-7d220b.netlify.app/)

## Basic workflow

**Step 1: Characterizing the Corpus.** Establish a generalizable narrative framework that describes corporate texts on a common scale. Unsupervised topic discovery identifies the thematic structure emerging from corporate language; this topic structure is the input to the second stage.

**Step 2: Topic decontextualization.** The task is one of selection and interpretation: establishing which topics constitute evidence about the focal feature rather than about the contextual specificities facing a firm. LLM agents first classify topic descriptors, then review common source passages within their own histories. An unweighted two-of-three majority determines selection.

**Step 3: Synthesize the narrative and behavioral proxies.** Use the selected narrative features to predict an established behavioral proxy for the focal microfoundational feature, through gradient boosting and regularized regression. The fitted value of the behavior serves as the synthesized proxy, capturing predicted common variation between the narrative and behavioral proxies.

**Step 4: Validate the synthesized proxy.** Gauge convergent validity and incremental validity. The former concerns consistency with an alternative measurement rather than with latent ground truth. The latter asks whether the synthesized proxy affords extra explanatory power beyond the narrative proxy and the behavioral proxy together. Evidence of this kind licenses a falsifiable proposition rather than a claim of superiority.

The design allows AI judgments to function as explicit, versioned, and falsifiable measurement inputs. Shared firm conditions may still drive the common variation, and LLM judgments may vary across model versions and prompting configurations. Further validation must address both risks; agreement among readers or predictive fit alone does not establish construct validity.

## One proof of concept: CEO risk preference

Our demo study focuses on CEOs’ risk preference. CEOs’ language in conference calls provides the narrative cues; R&D intensity provides the behavioral proxy. The synthesized proxy is then examined in dividend-payment models. Higher scores are associated with a lower propensity to pay dividends, including specifications controlling for actual R&D.

The example demonstrates the feasibility of connecting narrative cues, a behavioral proxy, and a separate organizational outcome. Shared firm conditions could still explain the relationship; the result does not establish a psychological trait or causal effect. [Read the CEO case](applications/ceo-risk-preference/README.md).

## New applications and further development

If the framework works, it offers a design template that confronts a central empirical challenge in microfoundations research: inherent measurement error. A new application needs a focal feature, sources of behavioral and narrative cues, and an external criterion for validation. The current numerical adapters implement the CEO case; another study needs its own scientific specification and compatible adapters. See the [application guide](docs/NEW_APPLICATION.md) and [planning template](applications/_template/README.md).

Further work will examine shared causes, propagate variation in LLM judgments through prediction and validation, and assess the framework across more microfoundational features and data sources. These developments remain to be tested; see the [research roadmap](docs/ROADMAP.md).

## Try the prototype

The offline demonstration runs stage handoffs, state checks, and resume logic with fixtures. Use Python 3.11+ and a fresh output directory; only the standard library is needed.

```sh
git clone https://github.com/jianghan6666/worddeed.git
cd worddeed
python3 -m agent_system.empirical.demo --out .local/demo
python3 -m agent_system.empirical.demo --out .local/demo --resume
```

Inspect `summary.json`, `workflow/state.json`, and `workflow/events.jsonl`. This demonstration makes no model calls and performs no empirical training or statistical estimation. It records `scientific_completion: false`.

## Evidence and replication

The [results](applications/ceo-risk-preference/RESULTS.md) and [replication instructions](applications/ceo-risk-preference/REPLICATION.md) document the CEO example. Saved-judgment replay is available. Fresh AI screening cannot run from the current release alone because required inputs are missing.

The [detailed reading guide](docs/AI_READING_GUIDE.md) explains the evidence, implementation limits, and reproduction scope, and includes an optional AI reading prompt. Large inputs are separate release assets; source-specific data terms apply, and no open-source license is currently granted. The website is deployed separately and may show an earlier edition.
