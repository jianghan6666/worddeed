# WordDeed as a measurement workflow

Start at `index.html#workflow`. WordDeed proposes a way to study organizational beliefs, preferences and other microfoundations by bringing together what people say and what organizations do. The research opportunity is a measure whose construction can be inspected, questioned and tested at each step. The CEO study is one example; the proposed contribution is a method other scholars could adapt to their own constructs and evidence.

This guide uses **S1** for the submitted proposal, **S2** for the final appendix, **S3** for an authorized repository snapshot and **S4** for the [venue call](https://orgsci.org/). S1–S3 are not bundled or uploaded. Use originals only if supplied separately through authorized editorial access; do not seek public copies. No anonymous destination is assumed. The route reflects a 2 November 2026 source review. Obtain exact snapshot identities from the supplied manifest; a draft revision, local preview and deployed page are different states.

## The problem and the proposed connection

Many organizational theories depend on attributes that cannot be observed directly. Narratives offer clues but reflect audiences, context and strategic presentation. Behavior supplies another signal but also depends on resources and opportunities. WordDeed asks whether learning the relationship between relevant language and an established behavioral indicator can produce a useful additional proxy.

This is a measurement hypothesis. Shared context can create predictive alignment without identifying the intended latent attribute. The workflow's value therefore depends on making assumptions testable, as well as producing scores. [S1 mission/four steps; S2 opening framework; S3 `README.md`, `docs/WORKFLOW.md`]

| Stage | Work and purpose | Output for the next stage |
|---|---|---|
| Represent narratives | Topic discovery provides a common description of recurring content. | Topic catalogue, source passages and narrative features. |
| Select relevant content | AI readers apply researcher-defined criteria, examine source evidence and retain reasons and disagreement. | Explicit decisions about content that may inform the construct. |
| Learn from behavior | Supervised models predict a justified behavioral indicator from selected narrative features. | A synthesized proxy evaluated on held-out observations. |
| Assess usefulness | Compare the measure with existing proxies in a separate application and test competing explanations. | Evidence for or against incremental usefulness and intended interpretation. |

Researchers define the construct, evidence, anchor and criteria for success. AI readers supply semantic judgments; numerical tools estimate; coordination software connects tasks through saved outputs and execution records. Agreement checks repeatability, not correctness against an independent reference. [S3 `docs/WORKFLOW.md`]

## Why AI matters

The combination can give researchers a shared representation of a large narrative corpus, explicit construct-relevance judgments they can inspect, and a learned relation between retained language and behavior. Recording the judgments makes evidence selection part of the measurement design that researchers can vary and evaluate.

The scientific opportunity is to test how semantic interpretation changes measurement and subsequent findings. Comparing judgments, anchors and methods could reveal when a proxy adds information and when it fails. Those comparisons remain a development agenda; several model outputs do not demonstrate its completion. S4 invites new measurement and reusable research infrastructure and evaluates novelty, feasibility, auditability, reproducibility and adoption.

## One optional illustration

The CEO application screens conference-call topics for risk relevance, then uses selected densities plus overall sentiment to predict R&D intensity. It examines dividend payment outside that training target. Reported prediction and downstream association illustrate a connected route from judgments to a candidate measure and substantive assessment; they do not establish a psychological ground truth. Narrative benchmark, behavioral anchor and learned score are distinct. [S2 §§3–4; S3 `applications/ceo-risk-preference/README.md`]

Use `ceo-case.html` for that illustration. Exact coefficients and model variants are optional supporting evidence, not prerequisites for understanding the workflow.

## Reuse and current feasibility

Shared coordination, saved-state/resume logic, documented judgments and CEO numerical adapters exist. The historical connected reproduction starts with saved representations and reader judgments, then refits prediction and estimates specified models. Saved-judgment replay succeeded in review. Neither route regenerates raw-text representation and new AI judgments. [S3 `agent_system/empirical/README.md`; `applications/ceo-risk-preference/replication/verification/CONNECTED_REPRODUCTION.json`]

The newer fresh-screening adapter exists, but the actual released-input preflight failed: 21 required files are absent and no provider call occurred. A complete authorized input package must pass that check before this route can be offered as runnable. An AI account alone cannot repair the package. See `reproduce.html` for the practical boundaries.

A new study needs its own construct, data rights, relevance criteria, anchor, timing and validation design, plus compatible adapters. A general application interface and independently validated second use remain development work. [S3 `docs/NEW_APPLICATION.md`]

The most useful next tests ask whether screening helps relative to simpler feature choices, whether results survive alternative selections and anchors, and whether independent criteria distinguish the intended construct from shared context. Selection and estimation uncertainty also need fuller propagation. Informative failures can establish the workflow's limits as well as successes establish its usefulness.

## Depth when it changes the assessment

If S1/S2 are supplied privately, compare the proposal's mission, four steps, risks and Figure 1 with the appendix's opening account. Material differences in corpus coverage, mapping controls and sentiment construction must be considered before claiming full alignment. Agreement/accuracy and residual/decoupling language also require explicit comparison. A13's reported narrative-controlled extension is outside the original 25-model replay.

For implementation checks, follow S3 `applications/ceo-risk-preference/study/representation/topic_models/bertopic_ideo_13-23_relaxed.yaml`; the two screening prompts under `applications/ceo-risk-preference/study/screening/review/protocol/`; `applications/ceo-risk-preference/study/prediction/code/step3_lib.py`; and `applications/ceo-risk-preference/study/assessment/full/code/prepare_models.py`. These are supporting routes, not a required first-pass code audit.

The focused guides under `review-ai/` offer optional CEO and replication depth. A source receipt is not the reader's own rerun. Preserve consequential conflicts and report what you actually inspected, ran or could not access. This guide executes nothing.
