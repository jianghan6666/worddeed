# Reviewer replication package

This private package contains the available code, data, models, saved judgments and evidence for all four stages of the CEO speech/R&D study. The [verified replication release](https://github.com/joyzhzh/ai-microfoundation-proxy/releases/tag/reviewer-replication-2026-10-31) records the accepted code revision and newly executed outputs. This checkout uses the reorganized paths below; the [repository guide](docs/REPOSITORY.md) maps the earlier layout. Large historical inputs are frozen in the separate [input release](https://github.com/joyzhzh/ai-microfoundation-proxy/releases/tag/reviewer-replication-2026-10-30); that earlier tag's code snapshot is superseded by the verified release. No access to the former development repository is needed for the commands below.

The executable replay starts from the **saved topic representation and saved reader records**. It recomputes the twelve-trial screening analyses, rebuilds firm-year predictors, refits Ridge and XGBoost, and sends the new cross-fitted scores into raw-data reconstruction and all 25 downstream Stata regressions. It does not call AI readers again, fit a new BERTopic model, or regenerate upstream sentiment. Those would be new analyses, not recovery of the historical judgments.

## Contents and boundaries

| Stage | Code and review material in Git | Large release evidence | Reproduction boundary |
| --- | --- | --- | --- |
| 1. Narrative representation | [Topic implementation](study/representation/README.md), [original model specifications](study/representation/topic_models/bertopic_ideo_13-23_relaxed.yaml), [catalogue](study/screening/review/inputs/catalogue.json) | Source/model bundle: 61 files including original code/notebooks, processed speech, CEO metadata, historical density matrix, BERTopic model and topic descriptions | Saved density shape, catalogue identity and delivered ordering are bound to the run. Historical density files lack embedded original row/column fingerprints; byte integrity cannot retroactively prove their original alignment. |
| 2. Relevance screening | [Twelve-trial report](study/screening/review/README.md), [protocols](study/screening/review/protocol/README.md), [replay code](study/screening/experiment/results-2026-10-21/replay.py) | 3,840 evidence files: source packets, saved records, seals, frozen analysis runtime and detailed transitions | Offline recalculation of primary and supplementary results separately. Preserve the primary unresolved majority and all missing reader rows. Full native chat histories were not part of the reviewed export. |
| 3. Behavioral prediction | [Supplied method and code](study/prediction/README.md), [connected adapter](agent_system/empirical/step3.py) | Components, density matrix, Compustat input, saved fits and scores, seed robustness results | Rebuild 29,506 firm-years; refit grouped five-fold Ridge/XGBoost with the delivered settings and 321-topic selection. |
| 4. Downstream assessment | [Full package](study/assessment/full/README.md), [compact route](study/assessment/score-models/README.md), [adapter](agent_system/empirical/step4.py) | Raw financial/market/compensation data, identity links, model inputs, coefficients, tables and audit outputs | Full route rebuilds the analysis data and runs 25 regressions (9 annual-behavior + 16 score models). The compact package is a separate frozen-input route. |

The [complete bundle inventory](replication/INVENTORY.json) covers 4,235 frozen archive members (4.05 GB compressed; 10.68 GB expanded, including intentional overlaps). All 334 files in the three supplied Step 3/4 packages are inventoried in [DELIVERY.json](replication/manifests/empirical-delivery/DELIVERY.json). The [Step 2 inventory](study/screening/experiment/results-2026-10-21/BUNDLE.json) and [source/model inventory](replication/manifests/source-ceo-rd.manifest.json) bind every release member. [IMPORT.json](replication/IMPORT.json) records the imported Git files and their original hashes. The supplied scientific package files remain unchanged from the reviewed export. Original supplied manifests are retained, including the recorded stale Step 3 README entry. The export redacts one personal path and refreshes the affected manifests; numerical files are unchanged.

Historical imported guides may mention the development repository, earlier plans or local paths. They document their original context. Use this guide and the release in this repository for current access and execution.

## Fresh checkout and core reproduction

Prerequisites: access to this private repository, authenticated GitHub CLI (`gh`), **Windows x64 with Python 3.11.7** for the historical numerical pipeline, and a Stata installation for estimation. The exact Python dependencies are in [requirements.txt](agent_system/empirical/requirements.txt). The core download is approximately 1.18 GB; restored inputs, evidence and generated models need additional working space. The original source/model bundle is separate so routine replay does not duplicate its 9.2 GB expanded corpus.

The supplied XGBoost fits and exact score transformations are platform-sensitive. A newly executed Mac ARM64 refit failed the original comparisons despite identical panel values; its failure is retained in [MACOS_DIAGNOSTICS.json](replication/verification/MACOS_DIAGNOSTICS.json). XGBoost documents differences in random sampling between Windows and other platforms, even with the same seed ([official documentation](https://xgboost.readthedocs.io/en/stable/tutorials/learning_to_rank.html)). Do not loosen tolerances to make a different-platform run pass.

Install the complete maintained requirements, including **Bottleneck 1.3.7**. The supplied requirements omitted this optional pandas reduction backend. Without it, the frozen XGBoost full-sample z-scores fail their original check by about `2e-5`; with it, they match exactly and the unchanged 13-check saved-model verifier passes. [NUMERICAL_BACKEND.json](replication/verification/NUMERICAL_BACKEND.json) records the controlled comparison. This is a verified compatible dependency pin; the historical environment did not record its Bottleneck version.

Run these commands in PowerShell with Python 3.11.7 installed:

```powershell
gh repo clone joyzhzh/ai-microfoundation-proxy
cd ai-microfoundation-proxy
py -3.11 --version
py -3.11 -m venv .venv
.venv\Scripts\python.exe -m pip install -r agent_system/empirical/requirements.txt
$env:PYTHONUTF8 = "1"
.venv\Scripts\python.exe replication/download.py --out .local/downloads
.venv\Scripts\python.exe replication/reproduce.py --downloads .local/downloads --out .local/reproduction --stata "C:\path\to\StataMP-64.exe"
```

If GitHub CLI transfers stall on your network, add `--transport curl` to the download or streaming-verification command. This uses authenticated HTTP/1.1 with the same hash checks; `curl` must be installed. For a network with intermittently stalled asset connections, `--refresh-slow` retries a fresh signed URL after 15 seconds below 256 KiB/s. It affects downloads only.

For the separate Mac diagnostic, XGBoost also needed an OpenMP runtime matching the Python architecture. The verification machine used the universal `libomp.dylib` already installed with Stata 18, without modifying either application or scientific code:

```sh
export DYLD_LIBRARY_PATH=/Applications/Stata/StataMP.app/Contents/Frameworks
.venv/bin/python -c "import xgboost; print(xgboost.__version__)"
```

Use that example only when the library exists at that installation path; otherwise provide your compatible OpenMP installation. The verification record includes the exact library hash. No native runtime binary is redistributed in this package.

Use the executable path for your installation (for example `stata-mp`), not the application bundle directory. Supplied historical regressions used **Stata 19.5** and declare `version 19.0`. An explicit `--stata-version 18` creates a separate do-file changing only that declaration; the original do-file remains intact and the same numerical acceptance checks still apply. It is never selected silently.

Without Stata, add `--through step4_prepare` to build all regression inputs. Later rerun the same command with `--stata` and the same output directory to finish estimation. Set the intended `--stata-version` consistently from the first run. Successful completed stages are hash-checked and reused on resume. Interrupted scientific output remains available for inspection; a failed fit may require a new run directory rather than overwriting partial work.

The driver verifies compressed and expanded inputs, restores Step 2 evidence beside its frozen replay code, recomputes both analysis variants, checks that the primary `b1-gpt-6-astra-P0-xhigh` handoff is byte-identical to the Step 3 input, and invokes the connected stages. That selection is 321 relevant, 33 irrelevant and zero unresolved; its SHA-256 is `be14a1f557fbb28a9f4702af15ec49d9fb0ea7534e7701fd5cc301872d4461e9`.

Inspect these outputs:

- `REPRODUCTION.json`, `ENVIRONMENT.json`, `RESTORE.json`: run scope, completion and environment.
- `screening/first/` and `screening/recovered/`: newly recalculated screening analyses and all trial handoffs.
- `workflow/state.json` and `workflow/events.jsonl`: stage bindings, artifacts and resumable execution record.
- Stage 3 validation and Stage 4 audit/QA reports under `workflow/`: numerical comparison with supplied results.
- `logs/`: detailed local execution logs. Stata launcher headers may contain local license information; keep raw logs local.

The driver preserves the supplied model grids, folds, seeds and computational settings. The Step 3 code uses its original 16-worker setting. No resource cap or scientific shortcut is introduced by the replication wrapper.

### Windows preparation and local Stata continuation

The [Windows verification workflow](.github/workflows/windows-replication.yml) fresh-downloads the private inputs, replays all screening analyses, refits both models, runs the supplied saved-model and three-seed checks, resumes completed fits without refitting, and rebuilds the financial data and 25 Stata model inputs. It uses a read-only token. Git preserves inventoried bytes on Windows; the replay wrapper specifies only UTF-8/LF JSON serialization and portable path separators. Frozen scientific code and output comparisons remain unchanged.

The workflow exports `reviewer-windows-handoff` with a file-by-file inventory, original and portable-export hashes, package manifests, selection identity, commit and Actions run identifiers. After a successful run, download that artifact to a machine with Stata and the pinned Python environment. Restore the same core input bundles on that machine, then run:

```sh
.venv/bin/python replication/download.py --out .local/downloads
.venv/bin/python replication/restore.py \
  .local/downloads/DELIVERY.json --out .local/reproduction/inputs
gh run download RUN_ID --repo joyzhzh/ai-microfoundation-proxy \
  --name reviewer-windows-handoff --dir .local/windows-handoff
.venv/bin/python replication/continue_stata.py \
  --handoff .local/windows-handoff \
  --packages .local/reproduction/inputs/packages \
  --out .local/connected-reproduction \
  --stata /path/to/stata --stata-version 18
```

Use `.venv/Scripts/python.exe` on Windows. Omit `--stata-version 18` for Stata 19. The continuation rechecks every restored input and exported handoff file, verifies completed-stage output lineage, then estimates the Windows-prepared model inputs. It records a split-runtime run explicitly; it does not rewrite the Windows workflow state or pass off frozen scores as new fits. Failed evidence remains available, and a failed handoff cannot be continued. [STATA18_REFERENCE_CHECK.json](replication/verification/STATA18_REFERENCE_CHECK.json) separately records the successful 25-model Stata 18 compatibility test from frozen reference tables.

## Completed verification and downloadable outputs

The [connected verification record](replication/verification/CONNECTED_REPRODUCTION.json) documents a successful fresh Windows run and local Stata 18 continuation. It replayed 122 screening analysis/handoff files, rebuilt the 29,506-row panel exactly, refitted both models, passed the original three-seed checks, rebuilt the financial and matching data, and estimated all 25 downstream models. All eight XGBoost score columns match the reference exactly; Ridge passes the original tolerances. Financial reconstruction passes its original `1e-12` comparison, without claiming every numeric value is bitwise identical. All 410 regression checks and the coefficient/SE, sample and presentation checks pass at their unchanged thresholds. Completed prediction stages were hash-checked and reused when advancing to regression preparation.

The accepted Windows run is [41107621004, attempt 2](https://github.com/joyzhzh/ai-microfoundation-proxy/actions/runs/41107621004). Its 428 exported files were verified before and after Stata estimation. The completion report identifies both code commits, Python dependencies, the Stata executable hash and the explicit version-18 compatibility change. Earlier failed and cancelled attempts are retained separately in the [verification index](replication/verification/README.md).

To inspect the newly executed outputs without fitting again:

```sh
gh release download reviewer-replication-2026-10-31 \
  --repo joyzhzh/ai-microfoundation-proxy \
  --pattern 'fresh-reproduction.tar.gz.part*' --dir .local/verified-run
cp replication/manifests/fresh-reproduction.manifest.json .local/verified-run/
.venv/bin/python replication/restore.py \
  .local/verified-run/fresh-reproduction.manifest.json --out .local/verified-run-expanded
```

Use `.venv/Scripts/python.exe` on Windows. The checked-in manifest is the checksum trust anchor. Add `--verify-only` instead of `--out ...` to verify every archive member without extracting. The [fresh-download receipt](replication/verification/FINAL_OUTPUT_DOWNLOAD.json) records the independent download check. The export preserves scientific binaries, replaces local paths with portable labels, and omits raw Stata license headers. It is a review copy; start a fresh reproduction to execute again.

## Full source/model download or streaming verification

To retain all original source/model files as well as the core assets (the examples below use the Unix virtual-environment path; on Windows substitute `.venv/Scripts/python.exe`):

```sh
.venv/bin/python replication/download.py --out .local/downloads --source
.venv/bin/python replication/restore.py \
  .local/downloads/source-ceo-rd.manifest.json --out .local/source
```

This adds approximately 2.9 GB compressed and 9.2 GB expanded. The three original source archive parts were repartitioned into 64 MiB transport parts; the concatenated archive hash and every member hash are unchanged. Extraction streams directly from the parts without creating an extra assembled archive. The original code, model files and corpus are preserved for inspection and authorized upstream work; availability is distinct from a claim of newly repeated topic training.

When storage cannot hold the expanded source, verify a fresh download of **every member** without extracting:

```sh
.venv/bin/python replication/verify_source.py --out .local/source-verification.json
```

This downloads each part into a new temporary directory, checks each part, the full archive, and every expanded file, then removes only those temporary downloads. The receipt records the complete check. For an already downloaded archive, `replication/restore.py MANIFEST --verify-only` verifies it without extraction.

## Additional supplied analyses

The release retains Step 3 saved-model/portable-model checks and all seed robustness evidence. To execute the original checks and the three supplied robustness seeds after the connected run:

```sh
.venv/bin/python replication/check_supplementary.py --run .local/reproduction
```

This invokes the unchanged supplied scientific scripts, compares the rebuilt panel exactly, and checks the robustness metrics at the original `1e-9` tolerance. It writes `supplementary/VERIFICATION.json` and preserves the generated metrics and logs. The connected core run and these additional checks are recorded separately.

The compact Step 4 package provides a separate 16-model frozen-input replay. It is included for review but is not a substitute for the connected full raw-data route. Its README supplies its original execution commands.

## Verification record and interpretation

New verification evidence is retained under [replication/verification](replication/verification). Supplied historical reports, newly executed empirical checks, and fixture-based software tests are distinct. Predictive fit, screening agreement and downstream associations do not by themselves establish psychological construct validity, causal effects or superiority over another measurement approach.

The repository and release remain private. Source-specific data access conditions continue to apply; this package grants no new license or redistribution rights.
