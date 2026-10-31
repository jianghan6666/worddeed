# CCM linking history raw acquisition

Downloaded from WRDS standard Annual Update → CRSP/Compustat Merged → Compustat CRSP Link form. Query `11827431`, download completed UTC 2026-10-24T19:24:35.783Z.

- Raw file `ccm_link_history_all.csv.gz`: 110124 rows, 1249975 bytes.
- Full available history in the form; all eight UI link types LC/LU/LS/LX/LD/LN/NR/NU selected, no primary-link or date filter.
- All eight link fields selected; form automatically adds company ticker `tic`. Original mixed-case columns retained.
- LINKDT ordinary dates: 1946-01-01 to 2025-12-31. LINKENDDT ordinary dates: 1950-05-30 to 2026-01-30.
- 20,367 raw `E` LINKENDDT sentinels retained unchanged. No date-sentinel conversion or matching performed.
- 68,891 rows have no LPERMNO/LPERMCO, corresponding to retained unlinked records; they were not dropped.
- Gzip successfully read to EOF; valid CSV widths; row count matches WRDS result page. SHA-256 `d08c0887de29af1a1f2381bad13191b0e4ca1b5abdf882f3b35d9dcfe2adb8d1`.

## Completeness caveat

The linked data dictionary for `crsp_a_ccm.ccmxpf_lnkhist` reports 123,388 rows, whereas the standard legacy SAS form returned 110,124. The cause is not established. This download includes every offered link type and matches the query result; it must not be described as a verified complete extract of the current Postgres table.

## Provenance

`ccm_link_history_query_parameters.json` transcribes the expanded Input Parameters from WRDS. The form reports library `crspa`, file `ccmlinktable` and dictionary table `ccmxpf_lnkhist`. It does not expose exact server SQL; no invented SQL file was generated. `ccm_link_history_metadata.json` records URLs, field descriptions and the discrepancy; `ccm_link_history_validation.json` records row counts, raw missing and sentinel counts.

No raw values changed, no analysis-sample filtering, regression variables or regressions.
