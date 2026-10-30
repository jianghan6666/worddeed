# Stage A: common initial-output addendum — prospective revision 7

Supply this exact addendum with every P0–P6 template for **Stage A, initial descriptor-only labeling**. It adds confidence reporting without changing the Stage A classification rule or evidence boundary. The historical 12-run pilot did not request these fields. A separate source-review prompt is released only after this response is sealed; do not anticipate its passages or alter this initial record later.

Return one JSON object with a `labels` array containing every supplied topic exactly once. For each topic retain `topic_id`, `status`, `label`, `rationale` and `evidence_keywords`, and add:

- `confidence_level`: `high`, `medium` or `low` for a resolved label; `null` for abstention or failure.
- `confidence_reason`: a concise, topic-specific explanation of why the supplied name/keywords make this decision clear or uncertain. For abstention/failure, explain why confidence cannot be assigned.

`rationale` explains the label; `confidence_reason` explains the certainty or ambiguity of that judgment. Use the same supplied descriptors and codebook for both. A reason is a brief evidence-based justification, not a hidden reasoning trace.

Use this common rubric:

| Level | Meaning |
|---|---|
| `high` | The descriptors clearly support the chosen side of the inclusion/exclusion boundary, with little material ambiguity. A clearly irrelevant topic can receive high confidence. |
| `medium` | The chosen label is defensible, but some descriptor meaning or its fit to the codebook is ambiguous. Identify that ambiguity. |
| `low` | A defensible choice is possible but rests on a borderline or tenuous interpretation. Identify the weakness. If no judgment is possible, abstain rather than force a label. |

These are your self-reported judgments about evidence sufficiency and codebook fit, not numerical probabilities, risk severity, managerial preference or agreement with other readers. Do not use a target label or confidence distribution. Cite one to five distinct exact supplied keywords for each resolved label. Use `status` `abstain` or `failed`, `label: null` and `confidence_level: null` when no resolved judgment is possible; retain the reason and do not invent keyword support.

Record and freeze the label, rationale, keyword citations, confidence level and confidence reason together before passage access or peer comparison. At this stage do not consult earnings-call passages, source-link tables, previous labels or outside evidence. The program will preserve this initial record and its majority separately. After source review, the final majority uses only the three reviewed Stage B labels; initial and reviewed labels are never six votes. Confidence never weights either majority.
