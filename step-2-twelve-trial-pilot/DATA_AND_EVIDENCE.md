# Data, evidence and reproduction

## Available immediately after cloning

This folder contains all 24 variant-specific handoff directories (12 trials × primary/supplementary), all 48 Git-delivered analysis tables/reports, the 354-topic catalogue, seven planned Stage A prompts, the common review prompt/output addendum, usage counters, the memo and workflow figure. [MANIFEST.json](MANIFEST.json) records the 131 copied files and their original repository paths and hashes. The frozen scientific bytes are unchanged.

The original package is:

```text
step-2-mvp-simple/experiment/expanded-ai-pilot/results-2026-10-21/
```

**Evidence paths in copied JSON remain relative to that original package.** For example, resolve `evidence/runtime/.../record.json` against the directory above, not against `step-2-twelve-trial-pilot/`. The machine-readable [TRIAL_INDEX.json](TRIAL_INDEX.json) provides `evidence_package_root_repository_relative`.

## Full reader judgments and source passages

The [private Step 2 release](https://github.com/joyzhzh/narrative-behavior-measurement/releases/tag/step2-twelve-trials-2026-10-21) contains `step2-twelve-evidence-2026-10-21.tar.gz`: 52,122,800 bytes and 3,840 files. It includes literal reader records, source passages, recovery records and detailed analysis artifacts. Full native chat logs are not part of the export.

From the repository root, using an account with access:

```sh
gh release download step2-twelve-trials-2026-10-21 \
  --repo joyzhzh/narrative-behavior-measurement \
  --pattern step2-twelve-evidence-2026-10-21.tar.gz \
  --dir .local/twelve-bundle
python3 step-2-mvp-simple/experiment/expanded-ai-pilot/results-2026-10-21/restore.py \
  --archive .local/twelve-bundle/step2-twelve-evidence-2026-10-21.tar.gz
```

Restoration verifies archive/member hashes and refuses to overwrite differing files. It restores inside the original package so existing evidence links remain valid. The two large `reader_stage_changes.private.csv` tables are also supplied by this release. The [bundle manifest](../step-2-mvp-simple/experiment/expanded-ai-pilot/results-2026-10-21/BUNDLE.json), [record index](../step-2-mvp-simple/experiment/expanded-ai-pilot/results-2026-10-21/RECORD_INDEX.json) and [provenance inventory](../step-2-mvp-simple/experiment/expanded-ai-pilot/results-2026-10-21/PROVENANCE.json) describe the exact records and administrative redactions.

## Original corpus, model and density data for Step 3

These larger assets remain in the separate [13 October private coauthor release](https://github.com/joyzhzh/narrative-behavior-measurement/releases/tag/coauthor-review-2026-10-13). Follow the [source-ceo-rd restoration instructions](../coauthor-review/CONTENTS.md#download-and-restore); the default documented destination is `restored-source/source/ceo_rd/`.

| Source-delivery path below `ceo_rd/` | Purpose |
|---|---|
| `models/bertopic_ideo_13-23_relaxed_354Topics/` | Saved model and topic catalogue/representatives |
| `data/replication_sample/topic_distr_is_ceo.npz` | Historical 354-column CEO-subset topic density matrix |
| `data/replication_sample/transcripts_is_ceo.pickle` | CEO-subset metadata and `orig_row` links |
| `data/t_combined_nodup_13-23_compNameOK_retainedNoEmpty_namesANDcomps_removed_w_scores_sentiment.pickle` | Retained masked/processed speech and source identifiers |

Review the [Step 3 handoff](STEP3_HANDOFF.md#3-bind-topic-ids-to-the-matching-density-data) before using these files: a valid text join does not independently authenticate historical density alignment, and generic sentiment is not automatically construct-specific direction.

## Reproduce without new model calls

First verify this delivery:

```sh
python3 step-2-twelve-trial-pilot/verify.py
```

After restoring the evidence archive, replay the original analyses into a new directory:

```sh
python3 step-2-mvp-simple/experiment/expanded-ai-pilot/results-2026-10-21/replay.py \
  --out .local/twelve-trial-replay
python3 step-2-mvp-simple/experiment/expanded-ai-pilot/results-2026-10-21/verify_replay.py \
  --out .local/twelve-trial-replay
```

These commands check preserved records and numerical aggregation. They perform no new annotations and do not establish human-reference accuracy or construct validity.
