# Execution reference for the WordDeed prototype

Start with [Try and inspect the WordDeed workflow](REPLICATION.md) for the contribution and a short choice of review routes. This reference supplies optional commands, version identities and evidence limits. The maintained empirical chain starts from **saved topic representations and saved AI judgments**, rebuilds predictors, refits Ridge and XGBoost, and estimates **25 downstream models** from supplied financial-data snapshots. It does not retrain BERTopic, regenerate sentiment, or ask AI readers to judge again.

The final submitted appendix also reports a directly aggregated narrative proxy (§3.6/Table A15) and eight models controlling for that proxy and actual R&D (Table A13). Those results are not covered by the existing 25-model reproduction. They remain author-reported until a separate extension packet is supplied and verified. The submitted results and the executable package have different coverage; the commands below cover only the latter.

## Choose a route

| Route | Inputs/software | What a successful run establishes |
|---|---|---|
| Read and check included results | Source checkout; Python 3.11+ | Integrity of imported reading copies, inventories, handoffs and 375 results files, with disclosed maintained-source exceptions |
| Offline workflow demo | Source checkout; Python 3.11+ standard library | Coordinator, artifact handoffs and resume work with invented data and replies |
| Replay saved screening | About 52 MB download; about 239 MB expanded evidence; Python 3.11+ | Recalculation of the primary and supplementary saved-record analyses and 122 analysis/handoff files |
| Inspect the prior verified run | About 544 MB output archive; Python 3.11+ for restore | Downloaded output integrity; it does not execute the models again |
| Connected empirical recomputation | Windows x64, Python 3.11.7, pinned numerical packages; supplied raw snapshots; compatible Stata | New prediction fits and downstream 25-model estimates, if every original acceptance check passes |
| Standalone compact/full Step 4 | Delivered packages, numerical environment and Stata | Separate estimation route using saved scores; not a new connected Step 3 fit |
| New AI screening — not ready from the current release alone | The actual released inputs fail preflight: 21 required files are absent | Code implements one new P0 triad; no live run has been verified. See the [fresh-screening boundary](#fresh-ai-screening-code-present-release-inputs-incomplete) |
| Upstream topic/sentiment work | Original source/model assets and separately specified environments | A separate analysis; exact recovery of the historical topic training is not established |

No route by itself establishes construct validity, accuracy of AI labels or a causal effect. Agreement measures repeatability; no completed human-reference validation is established by these computational checks.

## Fix the code and artifact versions

The code is public as inspected on 2 November 2026. Clone and select the exact code snapshot used for the lightweight checks in this guide:

```sh
git clone https://github.com/jianghan6666/worddeed.git
cd worddeed
git checkout --detach b96f8f65352d24ffb6e5137d81bc50d59b3bf779
git rev-parse HEAD
```

A source archive at that commit also works; the scripts do not require `.git`. Use a writable extraction directory because Step 2 restores evidence beside its frozen replay code. Record the source commit or archive identity with your run.

Keep these versions distinct:

| Material | Published tag | Observed tag commit |
|---|---|---|
| Frozen input bundles | `reviewer-replication-2026-10-30` | `f7f7c91409ef8415a9c080dcfea356a22d66dd9d` |
| Prior connected-run outputs | `reviewer-replication-2026-10-31` | `930e6bd777d810322e1096b2bf6b84ee3fed9d4d` |
| Browsable full results | `full-results-2026-10-31` | `51693efb0b4d2ae04d8aae2dfd59050682e638d2` |

The checked-in manifests at the selected code revision are the checksum trust anchors. Do not replace them with arbitrary newly downloaded manifests. The prior connected run used Windows code `4ea76294dbfb58c76fb61af23c940ee89ad03aa3` and local Stata-continuation code `d046fe2d72dcfcf1b7fc5d879517eed39eb92eb9`; its success is not a new full-chain run at the current documentation revision.

## Check the included files

From the repository root, run:

```sh
python3 replication/verify.py
python3 replication/verify_delivery.py
python3 applications/ceo-risk-preference/study/screening/review/verify.py
python3 applications/ceo-risk-preference/results/verify.py
```

On Windows use `py -3.11` in place of `python3`. All four commands must exit 0. Expect 521 imported-source entries with four reported maintained-path exceptions, 139 browsable delivery files and an inventory of 334 archive members, 131 screening review copies, and 375 browsable results files. Checking the delivery inventory is not verification of archive members that have not been downloaded. The results verifier reports 29,506 score rows, 25 models and 1,799 coefficient rows; these are saved results.

## Try the offline workflow demonstration

For the synthetic workflow demonstration, use a new output directory:

```sh
python3 -m agent_system.empirical.demo --out .local/connected-demo
python3 -m agent_system.empirical.demo --out .local/connected-demo --resume
```

Its topics, replies and numerical outputs are fixtures. Its receipts explicitly mark `scientific_completion: false` and Stata estimation as not run.

## Recalculate the saved screening results

Download `step2-twelve-evidence-2026-10-21.tar.gz` from the [frozen input release](https://github.com/jianghan6666/worddeed/releases/tag/reviewer-replication-2026-10-30). Public browser/HTTP download does not require a GitHub account. The existing CLI route is:

```sh
gh release download reviewer-replication-2026-10-30 --repo jianghan6666/worddeed --pattern step2-twelve-evidence-2026-10-21.tar.gz --dir .local/downloads
python3 applications/ceo-risk-preference/study/screening/experiment/results-2026-10-21/restore.py --archive .local/downloads/step2-twelve-evidence-2026-10-21.tar.gz
python3 replication/replay_screening.py --out .local/screening-review
python3 applications/ceo-risk-preference/study/screening/experiment/results-2026-10-21/verify_replay.py --out .local/screening-review
```

GitHub CLI may require its usual authentication setup. Alternatively, place the browser-downloaded archive at the indicated path and start with the restore command. No numerical packages, Stata or model account are needed. Allow at least 1 GB working space for this route and use a new replay-output directory.

The archive is 52,122,800 bytes; its SHA-256 is `edddd3adf79f93be90a3480ee3dfae607989393f289f2ea72f550d4e6622292d`. Restore verifies the archive and 3,840 evidence members. Successful comparison reports 122 reproduced files, excluding generation timestamps only. Preserve primary and supplementary results separately, including the primary unresolved majority. A restored corpus of saved records is not a new annotation run or a complete original chat history.

The adopted `b1-gpt-6-astra-P0-xhigh` handoff contains 321 relevant topics, 33 irrelevant topics and no unresolved final labels. Its SHA-256 is `be14a1f557fbb28a9f4702af15ec49d9fb0ea7534e7701fd5cc301872d4461e9`. Replaying that handoff does not establish that it is the most accurate topic selection.

## Inspect the prior connected-run outputs

This route was not re-downloaded in the 2 November lightweight review. It is the maintained route for inspecting the archived prior run without fitting again:

```sh
gh release download reviewer-replication-2026-10-31 --repo jianghan6666/worddeed --pattern 'fresh-reproduction.tar.gz.part*' --dir .local/verified-run
python3 -c "import shutil; shutil.copyfile('applications/ceo-risk-preference/replication/manifests/fresh-reproduction.manifest.json', '.local/verified-run/fresh-reproduction.manifest.json')"
python3 replication/restore.py .local/verified-run/fresh-reproduction.manifest.json --verify-only
python3 replication/restore.py .local/verified-run/fresh-reproduction.manifest.json --out .local/verified-run-expanded
```

Choose a new extraction directory. The archive contains 596 files. The portable export preserves scientific binaries and omits raw Stata license headers; it is an inspection copy rather than a portable resume directory. Inspect `applications/ceo-risk-preference/replication/verification/CONNECTED_REPRODUCTION.json` for the historical environment, new-score lineage, 25-model regression checks and explicit Stata 18 compatibility change.

## Execute the maintained empirical chain

This route refits models and can take substantial compute. The verified prediction environment is **Windows x64 and Python 3.11.7**, with every package in `agent_system/empirical/requirements.txt`, including Bottleneck 1.3.7. The latter is a verified compatible pin; its historical version was not recorded. The supplied fitting code uses 16 workers. Compressed download size is not a memory estimate.

Use a licensed Stata installation: supplied historical regressions used Stata 19.5 with a `version 19.0` declaration. The accepted connected run used an explicit Stata 18 compatibility route that changes only the declaration in a separate generated do-file and retains the original acceptance checks. Do not silently select a different version. Mac ARM64 refitting previously failed the unchanged numerical comparison and is a diagnostic route, not the verified exact-refit environment.

After checking out the fixed source revision, run in PowerShell:

```powershell
py -3.11 --version
# Continue only when this prints Python 3.11.7.
py -3.11 -m venv .venv
.venv\Scripts\python.exe -m pip install -r agent_system/empirical/requirements.txt
.venv\Scripts\python.exe -m pip check
.venv\Scripts\python.exe -c "import platform,sys; print(sys.version); print(platform.platform()); print(platform.machine())"
$env:PYTHONUTF8 = "1"
.venv\Scripts\python.exe replication/download.py --out .local/downloads
.venv\Scripts\python.exe replication/reproduce.py --downloads .local/downloads --out .local/reproduction --stata "C:\path\to\StataMP-64.exe" --stata-version 18
```

Replace the Stata path with the installed executable and select version 18 only for that intended compatibility route. For Stata 19, use `--stata-version 19`. The maintained downloader requires installed/authenticated `gh`; its `--transport curl` alternative still obtains authentication from `gh`. It currently has no fully anonymous bulk mode.

Core input downloads are about 1.18 GB compressed and about 1.46 GB expanded, before the environment and generated models. The optional original source/model archive adds about 2.9 GB compressed and 9.2 GB expanded and is unnecessary for saved-representation replay. Data access conditions still apply to delivered inputs.

Without Stata, add `--through step4_prepare`. This prepares inputs but does not complete estimation. Later repeat with the same output directory, scientific settings and intended Stata version plus the executable to finish. A completed chain must have `status: "complete"` and `step1`, `step2`, `step3`, `step4_prepare` and `step4` all complete in `REPRODUCTION.json`, with the original numerical checks passed.

The separate `replication/check_supplementary.py --run .local/reproduction` command executes the supplied saved-model and three-seed checks; report it separately from the core run. Windows preparation/local Stata continuation is also supported; see the route below. Repository-write permission is required to dispatch its Actions workflow; read-only reviewers can use local Windows execution. This review did not dispatch Actions or refit the empirical models.

### Windows preparation and local Stata continuation

The [Windows workflow](../../.github/workflows/windows-replication.yml) can produce a `reviewer-windows-handoff` artifact containing fitted prediction outputs, prepared regression inputs and a file-by-file inventory. Repository writers may dispatch it with `gh workflow run windows-replication.yml --repo jianghan6666/worddeed --ref main`. Record the actual code revision and run identity. Actions artifacts expire; an old run ID does not guarantee that its handoff is still downloadable.

After a successful Windows run, use the handoff on a machine with compatible Stata and the pinned Python environment. Restore the same core packages, replace `RUN_ID` with the actual run, and replace the Stata path:

```sh
.venv/bin/python replication/download.py --out .local/downloads
.venv/bin/python replication/restore.py \
  .local/downloads/DELIVERY.json --out .local/reproduction/inputs
gh run download RUN_ID --repo jianghan6666/worddeed \
  --name reviewer-windows-handoff --dir .local/windows-handoff
.venv/bin/python replication/continue_stata.py \
  --handoff .local/windows-handoff \
  --packages .local/reproduction/inputs/packages \
  --out .local/connected-reproduction \
  --stata /path/to/stata --stata-version 18
```

These commands retain the original documented split-runtime interface. Use `.venv/Scripts/python.exe` on Windows. Select version 18 only for the intended compatibility route; use version 19 with a compatible Stata 19 installation. The continuation checks the restored package members, exported handoff files, selected-topic identity and completed-stage lineage before estimating the prepared models. A failed handoff must not be treated as a completed run. The resulting record identifies split-runtime execution; it does not relabel frozen reference scores as new fits. This integration has not dispatched or reexecuted the route.

## Understand resume and failure evidence

Completed workflow stages are hash-checked before reuse. Preserve failed output and logs. An interrupted first extraction may leave `inputs/` without `RESTORE.json`; an interrupted screening run may leave an incomplete screening directory. These partial states are not covered by completed-stage resume: use a new run directory unless a specific recovery has been verified. Do not delete evidence, edit manifests or relax tolerances to obtain a pass. Keep raw Stata launcher logs local because they may contain license details.

## Fresh AI screening: code present, release inputs incomplete

The newer API adapter implements one new P0 three-reader analysis. It is **not runnable from the current release alone**. A separate 2 November workflow review used the actual restored toolkit and the adapter's actual input preflight; it failed before any provider call because 21 required files were absent:

- `packets/prompts/P0.md`;
- `packets/initial_addendum.md`;
- `packets/source_evidence.private.jsonl`;
- all 18 canonical pages, `packets/stageB/B01.json` through `B18.json`.

All 21 are also absent from the release inventory, so this is a packaging gap rather than a failed extraction. Prompt/addendum text and page content survive within other released records, but that does not supply the required complete input tree. The source-evidence JSONL was not located in the inspected release/repository trees. This guide does not reconstruct or substitute those files.

Saved-judgment replay succeeds because it uses a different input arrangement and recalculates existing records. That success does not establish readiness for new AI inference. The preflight harness exited successfully after recording the expected error; the **preflight itself failed**, with zero provider calls. No live model availability or annotation result was verified.

Before offering a fresh-screening route, supply a complete authorized packet tree, bind each input by hash and pass the no-call preflight against those released inputs. A later live run would additionally require an available model/account/effort, cost authorization and permission to transmit source passages. The historical records identify requested model/effort configurations; they do not establish immutable observed backend snapshots or deterministic future regeneration. A new API run is a new condition, not an exact rerun of the historical native-reader study.

## Access and new analysis prerequisites

Public visibility does not grant new rights in code, data or model assets. The repository currently grants no open-source license. The source-specific access documentation should identify permitted use and acquisition conditions for each bundle; the inspected package has only general statements, so those conditions remain to be clarified by the authors.

| Source/material | Use in the package | Information needed for external reuse |
|---|---|---|
| Capital IQ conference calls and derived source passages | Topic corpus, density/sentiment inputs, AI screening packets | Authorized access, reuse/redistribution and provider-transmission conditions |
| Compustat and ExecuComp | R&D target, financial and CEO/compensation inputs | Institution/vendor access and permitted distribution of snapshots/derivatives |
| CRSP | Market returns and linking inputs | Source access and permitted reuse of raw/derived data |
| FRED | Treasury-bill series | Exact series, retrieval/version record and applicable terms |
| Saved model files and AI records | Historical replay and inspection | Model/source terms, provenance and permitted reviewer use |

The incomplete fresh-screening input package must be resolved before that separate, potentially paid route can be offered to reviewers. Upstream inference applies the fixed saved topic model; upstream retraining needs its separate source environment and need not reproduce identical historical topics. The old unkeyed density matrix's original alignment remains delivery-declared even when its checksum passes.

## Evidence from the 2 November review

At main commit `b96f8f65352d24ffb6e5137d81bc50d59b3bf779`, a clean source snapshot on macOS 15.7.3 arm64/Python 3.12.14 passed the four standard-library checks, the synthetic demo/resume and 18 documented runtime tests. A new anonymous Step 2 download passed the archive/member checks and reproduced 122 saved analysis/handoff files. Release metadata matched the inspected pinned part/manifests; all large empirical assets were not re-downloaded. No empirical fit, Stata estimation, new AI inference, topic training or sentiment regeneration was run in that review.

The separate AI workflow review tested the released fresh-input preflight and found the 21 missing inputs described above. Its finding is incorporated here without repeating that test or any prior replay. This editorial revision added no installs, empirical computations or provider calls.
