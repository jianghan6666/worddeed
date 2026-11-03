# Match Words with Deeds

An AI-empowered proxy framework for organizational microfoundations

**Local preview — not published.**

4 min 04 sec · English narration synthesized with Kokoro 0.9.4 (voice af_heart).

Subtitles are included in the picture of the main film.

[Watch the subtitled film](player.html) · [Accessible HTML transcript](transcript.html) · [Clean film](workflow-preview.mp4) · [Separate English captions](captions.en.vtt)

Narration is verbatim. Visual descriptions are marked separately.

## 00:00–00:36 — Organizational microfoundations

Organizational microfoundations—the cognitions, beliefs, and traits of individual members—can steer firms' strategic decisions, operations, and performance. These latent cognitive and psychological properties are generally hard to observe and quantify. Behavioral proxies face the problem of attribution; narrative proxies face the problem of authenticity. Both face potential measurement errors. In this study, we strive to integrate the behavioral and narrative cues for the same latent microfoundational feature to develop a synthesized proxy.

**On screen:** Beliefs and priorities are posed as unobserved constructs. Narrative and behavioral branches carry separate contextual influences before approaching a candidate measure. No removal of those influences is asserted.

## 00:36–01:57 — The four-step workflow

Step one: Characterizing the Corpus. We use unsupervised topic discovery to establish the thematic structure emerging from corporate linguistics. Step two: Topic decontextualization. The task here is one of selection and interpretation—establishing which topics constitute evidence about the focal feature. AI agents first classify topic descriptors, then review common source passages within their own histories. An unweighted two-of-three majority determines selection. Agreement measures repeatability, not independently validated accuracy. Step three: Synthesize the narrative and behavioral proxies. Narrative features are used to predict an established behavioral proxy. The behavioral outcome, reconstructed from the narrative evidence for observations excluded from model fitting, serves as the synthesized proxy. This is the predicted common variation that the framework seeks to examine. Step four: Validate the synthesized proxy. We assess consistency with alternative measurements and whether the synthesized proxy affords extra explanatory power beyond the narrative and behavioral proxies together. Evidence of this kind licenses a falsifiable proposition rather than a claim of superiority.

**On screen:** One four-step diagram is developed through topic discovery, relevance judgments, supervised prediction and empirical assessment. The researcher chooses the construct, behavioral indicator and evaluation. Reasons and disagreement remain visible; predictions are made for observations excluded from model fitting.

## 01:57–02:28 — AI judgments as measurement inputs

To accomplish this task, we integrate three core AI techniques: unsupervised machine learning, AI agents, and supervised machine learning. The aim is a scalable and inspectable toolkit for organizational research, allowing AI judgments to function as explicit, versioned, and falsifiable measurement inputs. The prototype retains judgments and outputs for inspection. Comparing alternative topic selections through the full analysis remains a development task.

**On screen:** The different roles of topic discovery, language models and numerical models are shown. A conceptual record connects source material, a relevance judgment and disagreement to the measure. Alternative selections are marked as a planned comparison, not a completed finding.

## 02:28–03:05 — One illustration: CEO risk preference

We have conducted a demonstration study to examine the feasibility of this workflow, focusing on CEOs' risk preference. We use CEOs' linguistics in conference calls to develop narrative features, then fit selected topic densities and overall sentiment to research and development intensity, a behavioral proxy. The fitted value is used as the synthesized proxy in an assessment of dividend decisions. Higher scores are associated with lower odds of paying dividends. The interpretation as underlying CEO risk preference still needs independent evidence.

**On screen:** The same workflow is instantiated with earnings-call themes, risk-relevance judgments, features including overall sentiment, predicted research spending relative to assets and dividend assessment. A qualitative negative association is accompanied by the limit that the underlying trait interpretation still needs independent evidence.

## 03:05–03:37 — Inspecting and reusing the workflow

The repository provides a connected prototype and an offline demonstration. The empirical review route starts from saved text representations and reader judgments. Some reported comparisons remain outside that reproduction. Fresh screening through the newer API route is not yet ready to run from the release. A new application needs its own behavioral and narrative cues, validation evidence, and compatible numerical tools. The current adapters target the CEO case.

**On screen:** Three routes invite the viewer to understand the workflow, try an offline example and inspect evidence. Saved-record replay is separated from fresh screening, whose release inputs are incomplete. New applications require their own scientific specification and compatible tools.

## 03:37–04:04 — Key risks, future work, and implications

The key assumption is that this common variation is primarily caused by latent microfoundations as the shared driver. We plan to examine common-factor variation, judgment stability, and independent human reference. If the framework works, it offers a design template that confronts a central empirical challenge: inherent measurement error, helping enhance consistency between theory and empirics.

**On screen:** The common variation must reflect the latent microfoundations as a shared driver. Open tests concern common-factor variation, judgment stability and independent human reference. The framework is presented conditionally as a design template addressing measurement error and consistency between theory and empirics.

## Evidence and scope

**Design and implementation.** The general workflow allows application-specific features and controls. The CEO model uses selected topic densities and one overall annual sentiment feature, without firm controls or fixed effects. The narrative-only comparison measure is separate from these model inputs.

**Selection and interpretation.** The adopted topic selection followed inspection of preliminary predictive performance. Reader agreement measures repeatability, not independently verified accuracy. Grouped fitting limits overlap within model fitting; it does not make the full representation and selection process independent. Shared circumstances may still explain the apparent signal.

**Evidence beyond the film.** Additional narrative-controlled comparisons and component correlations have been reported beyond the packaged reproduction. Some narrative–synthesized correlations are weak. The evidence does not establish uniformly strong convergence, causal effects or an independently validated CEO trait.

**What can be replayed.** The empirical route starts from saved text representations and reader judgments. It does not regenerate topic discovery, sentiment or historical AI readings. Fresh screening through the newer API route lacks required release inputs. The offline demonstration checks software handoffs; it is distinct from empirical reproduction.

**Adapting the workflow.** A new application requires its own construct definition, appropriate narratives and behavioral indicator, evaluation evidence and compatible numerical tools. The current adapters implement the CEO case.

[Explore the workflow](../../index.html) · [CEO illustration](../../ceo-case.html) · [Inspect and reproduce](../../reproduce.html) · [AI reading aid](../../review-ai/)
