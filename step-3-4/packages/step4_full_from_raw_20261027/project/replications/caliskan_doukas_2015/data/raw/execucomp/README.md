# ExecuComp raw downloads

Downloaded through the already signed-in WRDS browser on 2026-10-24 by Codex. Each original CSV gzip file is copied byte-for-byte; accompanying .sql is downloaded from WRDS. No data transformations, sample selection, regression variables, imputation or regressions have been applied.

| Table | Fiscal years | Rows | CSV columns | Query |
|---|---:|---:|---:|---:|
| comp_execucomp.anncomp | 1992–2023 | 364,196 | 107 | 11827426 |
| comp_execucomp.outstandingawards | 2006–2023 | 1,245,777 | 50 | 11827427 |
| comp_execucomp.pension | 2006–2023 | 109,154 | 44 | 11827430 |
| comp_execucomp.deferredcomp | 2006–2023 | 111,504 | 46 | 11827432 |

All available fields were requested. The UI counts GVKEY twice in its grouping, so actual distinct CSV column counts are one lower than the displayed variable-picker totals. Queries include all executives and companies; identify annual CEO using CEOANN in later work, rather than current PCEO. SQL contains exact year restrictions and joins.

Structural validation read each gzip to EOF, parsed every CSV row, matched WRDS reported row counts, checked year coverage, and computed SHA256. All years in requested windows are present; no malformed CSV rows. validation.json records yearly row counts, columns, bytes and hashes. validate_raw_downloads.py reproduces these checks.

field_labels.json and per-table labels in download_metadata.json preserve WRDS Query Form variable explanations (whitespace/apostrophe escapes normalized). Numeric source units and missing-value representation are preserved; a UI $ label alone does not establish scaling. Consult vendor field documentation before unit conversion in a later stage.

Downloads are licensed WRDS data; store locally in the authorized project.
