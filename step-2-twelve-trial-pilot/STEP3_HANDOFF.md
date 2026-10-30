# Using the twelve-trial Step 2 outputs in Step 3

The deliverable is a **topic-selection vector for each trial**, accompanied by all three reader votes and evidence. It is not a firm-year score, a sentiment series or a behavioral prediction. Use the same selected IDs throughout a documented downstream specification.

## 1. Choose and record a trial and variant

Use [TRIAL_INDEX.csv](TRIAL_INDEX.csv) or the [trial table](README.md#trial-outputs). Each of the 12 trials has three readers and a Stage B majority. No trial is designated the preferred classifier, and no majority across all 12 trials has been adopted. For sensitivity analysis, carry each complete selection through the same downstream procedure; do not select the trial giving the preferred regression result.

- **Primary:** `results/primary/handoffs/<trial_id>/`. These are the original submissions, including missingness. Trial `b2-gpt-6-astra-P0-xhigh` has one unresolved majority, topic `224`.
- **Supplementary:** `results/supplementary/handoffs/<trial_id>/`. These incorporate explicitly indexed recoveries. They resolve topic `224` as relevant in that trial; final selections in the other 11 trials are unchanged. The underlying recovered records differ more extensively than this one majority change.

All 12 trials shared the same scientific protocol; requested model and effort were the only varied experimental factors, with two independent repetitions per configuration. Missing saves and mechanical flags are execution deviations. Sol xhigh repetition 1 has complete original Stage B judgments and zero recorded mechanical flags, but this provides only an operational reason for using it provisionally in pipeline development. It does not establish a scientifically preferred classifier. Scientific adoption remains a coauthor decision informed by substantive audit and sensitivity across trial outputs. See the [trial-level accounting](../step-2-mvp-simple/TECHNICAL_APPENDIX.md#common-protocol-and-execution-deviations).

Record the trial ID, requested model/effort, repetition, variant, selection-file SHA-256 and downstream specification. A supplementary selection must remain identified as supplementary.

## 2. Read the correct output fields

| File / field | Meaning and use |
|---|---|
| `selected_topics.json` → `final.relevant` | String topic IDs selected by the Stage B majority; this is the selection input for Step 3 |
| `final.irrelevant` | Explicitly excluded IDs |
| `final.unresolved` | IDs without two matching resolved votes; retain an explicit missing-data disposition |
| `initial_separate` / `initial_topic_labels.csv` | Stage A comparison only; never a substitute for missing Stage B votes |
| `topic_labels.csv` | One row per topic, final status/label, three individual votes, minority and missing-reader indicators |
| `topic_model_id`, `catalogue_sha256`, `prompt_sha256`, `source_packet_original_sha256` | Input identities to retain with the downstream analysis |
| `reader_records_package_relative` | Evidence paths relative to the original result-package root, given in [TRIAL_INDEX.json](TRIAL_INDEX.json); restore the evidence archive to read them |

Unresolved is not equivalent to irrelevant. Do not silently replace primary records with recovered ones, fill a missing vote, weight by confidence, or combine Stage A and B as six votes.

This minimal Python example reads an **explicitly chosen** selection; it does not score data or choose a classifier:

```python
import hashlib
import json
from pathlib import Path

def read_selection(repository_root, trial_id, variant):
    if variant not in {"primary", "supplementary"}:
        raise ValueError("Specify primary or supplementary")
    hub = Path(repository_root) / "step-2-twelve-trial-pilot"
    index = json.loads((hub / "TRIAL_INDEX.json").read_text())
    trial = next(t for t in index["trials"] if t["trial_id"] == trial_id)
    path = hub / trial["variants"][variant]["selected_topics"]
    payload = path.read_bytes()
    selection = json.loads(payload)
    return {
        "selected_ids": selection["final"]["relevant"],
        "excluded_ids": selection["final"]["irrelevant"],
        "unresolved_ids": selection["final"]["unresolved"],
        "topic_model_id": selection["topic_model_id"],
        "selection_sha256": hashlib.sha256(payload).hexdigest(),
    }
```

## 3. Bind topic IDs to the matching density data

The [catalogue](inputs/catalogue.json) contains 354 IDs and the frozen model identity:

```text
bertopic_ideo_13-23_relaxed_354Topics:sha256:52deaf6581036e750af07604268d4665bfa3386b3797874e8374b3876b3b683f
```

Use an explicitly verified topic-ID-to-density-column mapping for that model. Do not use the CSV row position as a density-column identity, or assume that converting an ID to an integer establishes the mapping. Preserve CEO/component/call/company/period keys when joining data.

The delivered source package contains `data/replication_sample/topic_distr_is_ceo.npz` (1,775,355 × 354) and `transcripts_is_ceo.pickle`. The metadata-to-retained-text join was checked, but the historical density matrix lacks embedded row IDs and model/column fingerprints. Its original alignment is declared by the delivery, not independently authenticated. Resolve this distinct provenance limitation before treating density-based scores as verified empirical inputs. [Source/density inspection](../step-2-mvp-simple/experiment/expanded-ai-pilot/SOURCE_TRACE_INSPECTION.md) · [source delivery and restoration](DATA_AND_EVIDENCE.md).

## 4. Specify downstream scoring separately

Step 2 selects topics; it does not supply risk-seeking/risk-averse direction, topic-specific sentiment, density normalization, firm-year aggregation or a validated scalar narrative measure. Document those choices and the handling of unresolved topics before scoring. Retain the full topic-selection vector, evidence identifiers and any comparison with alternative trials. Keep narrative N, observed behavior B and fitted S distinct.

Coauthors should review the substantial Stage A–B broadening before adopting a preferred selection. Human-reference validation was not performed in this pilot. These limitations do not prevent inspecting or importing the supplied IDs; they define what any resulting Step 3 analysis may claim.
