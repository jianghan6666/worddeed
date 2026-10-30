# Newly executed verification

This directory holds concise verification evidence produced for the reviewer replication release. Reports distinguish fresh-download integrity, offline saved-record replay, new empirical fitting/estimation, resume behavior, and software fixtures. Historical supplied results remain in their inventoried packages.

| Executed check | Evidence and scope |
| --- | --- |
| Fresh core download and restore | [CORE_DOWNLOAD.json](CORE_DOWNLOAD.json): all core compressed assets and 334 expanded Step 3/4 members verified. |
| Fresh full source/model download | [SOURCE_DOWNLOAD.json](SOURCE_DOWNLOAD.json): all 43 transport parts, the complete archive, and all 61 expanded members verified by streaming. |
| Software and identity checks | [SOFTWARE_CHECKS.json](SOFTWARE_CHECKS.json): 56 adapter tests with no skips, 11 packaging tests, fixture execution/resume, exact saved-record replay of 122 analysis/handoff files, imported source identities, and the separate results package. These are distinct from empirical reproduction. |
| Mac ARM64 refit diagnostic | [MACOS_DIAGNOSTICS.json](MACOS_DIAGNOSTICS.json): identical panel values and passing Ridge comparison; XGBoost refit and some exact transformations failed. Numerical thresholds were not widened. |
| Missing numerical dependency resolved | [NUMERICAL_BACKEND.json](NUMERICAL_BACKEND.json): Bottleneck 1.3.7 restores the original frozen transformations; the unchanged saved-model verifier passes all 13 checks. The earlier Mac XGBoost refit failure is a separate platform issue. |
| First Windows refit diagnostic | [WINDOWS_PRE_BACKEND.json](WINDOWS_PRE_BACKEND.json): the new raw XGBoost predictions match exactly and Ridge predictions pass, but the missing Bottleneck backend prevents supplementary verification. This failed attempt is retained separately from the corrected rerun. |
| Independent Stata 18 compatibility | [STATA18_REFERENCE_CHECK.json](STATA18_REFERENCE_CHECK.json): 25 models, 410 regression checks, and presentation checks passed from frozen reference tables. This is not a newly fitted connected chain. |

The Windows refit, original three-seed checks, full raw-data preparation and connected Stata continuation are still being verified. Their final evidence is added only after each check completes. Local user paths and Stata license headers are excluded from published reports.
