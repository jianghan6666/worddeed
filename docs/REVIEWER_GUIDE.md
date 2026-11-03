# Reviewer start here

WordDeed proposes an AI-empowered framework to integrate behavioral and narrative cues for the same latent microfoundational feature and develop a synthesized proxy. The workflow maps narrative cues to an established behavioral proxy to extract their predicted common variation, then assesses the resulting measure. Whether that common variation reflects the intended microfoundation remains a question for validation.

## Understand the workflow

Read the [workflow guide](WORKFLOW.md) in the proposal's four steps: **Characterizing the Corpus**, **Topic decontextualization**, **Synthesize the narrative and behavioral proxies**, and **Validate the synthesized proxy**. Follow how a topic becomes a relevance judgment, how the selected features enter behavioral prediction, and how the score reaches a separate empirical assessment.

The [capability note](WORKFLOW_CAPABILITY.md) distinguishes the proposed design from the implemented prototype. Researchers choose the construct, relevance criteria, behavioral anchor and assessment. LLM readers provide inspectable judgments; computational tools perform estimation. Reader agreement measures repeatability, not accuracy or successful removal of contextual influences.

The [application guide](NEW_APPLICATION.md) explains what another scholar would need to specify and implement. The current numerical adapters target the CEO case; changing a construct label does not make another study runnable. The [roadmap](ROADMAP.md) identifies the scientific tests and development work still needed.

## Choose an optional closer look

| Your question | Reading route |
| --- | --- |
| What does the workflow look like in one study? | The brief [CEO illustration](../applications/ceo-risk-preference/README.md) connects conference-call narratives, R&D intensity and dividend payment. |
| What supports the example? | The [results guide](../applications/ceo-risk-preference/RESULTS.md) and [evidence scope](../applications/ceo-risk-preference/EVIDENCE_SCOPE.md) distinguish the original package from later reported results. |
| Can I try or check the software? | [Try and inspect the workflow](../applications/ceo-risk-preference/REPLICATION.md), then choose the demo, saved-reader replay, prior-run inspection or optional numerical reproduction. |
| Can an AI assistant help me read it? | The [AI reading guide](AI_READING_GUIDE.md) starts with the workflow and offers focused evidence questions. |

The synthetic demo and saved-reader replay passed the 2 November 2026 review. The prior connected numerical reproduction starts from saved topic representation and judgments, then refits prediction and estimates the original 25 downstream models. The later submitted narrative benchmark and eight Table A13 models are outside that reproduced package. These are different evidence scopes; none alone establishes psychological construct validity or a causal effect.

Fresh AI screening is a separate route. The newer API adapter's actual released-input preflight failed on **21 missing required files before any provider call**. Saved-reader replay works with a different input arrangement. A model account does not repair the missing package. The [execution reference](../applications/ceo-risk-preference/REPLICATION_DETAILS.md) supplies the commands, environments, access requirements and exact boundaries.

## Sources and access

This is the identified public research repository as inspected on 2 November 2026. Large input and output bundles are separate release assets; public availability does not grant new rights to reuse or redistribute source data. The execution reference distinguishes public browser downloads from the authenticated bulk-download route. No open-source license is currently granted.

The submitted proposal and appendix are supplied separately through the editorial process and are not distributed by this guide. If you have them, compare intended design and reported findings with the implementation. If you do not, state that limit and continue with the repository evidence. Do not assume a source checkout includes the submitted originals or that a local presentation draft is already deployed.
