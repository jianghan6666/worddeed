# Compustat Fundamentals Annual — raw download

Source: WRDS Compustat North America Fundamentals Annual. Query ID `11827424`.

File: `funda_datadate_2003-01_2024-06.csv.gz`

- Requested date filter: `datadate`, 2003-01 through 2024-06.
- Actual date range: 2003-01-31 through 2024-06-30.
- Actual fiscal-year range: 2002–2024. Boundary fiscal years arise because the download was filtered by report date, not fiscal year. 2024 is a partial buffer year, not a complete analysis period.
- 200,950 rows; 35 columns; 9513386 compressed bytes. Row count matches the WRDS result page.
- Gzip read successfully to EOF, CSV rows all have the expected width; all 30 required Table 4 acquisition fields are present.
- Observed filters: INDL, STD, C, USD throughout; active A=118747, inactive I=82203.
- All companies/all industries were requested. Financials and utilities have not been excluded at download stage.
- `popsrc` was not separately selected in the UI and is not in the file. Inspection of the exact saved SQL confirms there is no `popsrc` predicate. No `popsrc` value/filter is inferred.
- Exact WRDS server SQL is saved as `funda_datadate_2003-01_2024-06.sql` and was inspected. Source table: `comp_na_daily_all.funda`, with company identifiers joined from `comp_na_daily_all.company`. Retrieval timestamp is retained by the root downloader; validation does not invent it.
- Raw file unchanged. SHA-256: `885730ce1967bac4a4c79313805730f3d10114b8e35dfadee0d1c9d8d7f45b3f`.

## Fields

`costat`, `curcd`, `datafmt`, `indfmt`, `consol`, `tic`, `datadate`, `gvkey`, `conm`, `cusip`, `cik`, `exchg`, `fyr`, `fic`, `sic`, `fyear`, `at`, `ceq`, `lt`, `pstk`, `pstkl`, `pstkrv`, `re`, `seq`, `txditc`, `dvp`, `ib`, `txdi`, `xrd`, `capx`, `csho`, `dvpsx_c`, `dvpsx_f`, `prcc_f`, `sich`

## Fiscal-year row counts

| fyear | rows |
|---|---:|
| 2002 | 1175 |
| 2003 | 9755 |
| 2004 | 9494 |
| 2005 | 9315 |
| 2006 | 9208 |
| 2007 | 9187 |
| 2008 | 9015 |
| 2009 | 8942 |
| 2010 | 9002 |
| 2011 | 9232 |
| 2012 | 9428 |
| 2013 | 9519 |
| 2014 | 9375 |
| 2015 | 9262 |
| 2016 | 9282 |
| 2017 | 9229 |
| 2018 | 9313 |
| 2019 | 9552 |
| 2020 | 9919 |
| 2021 | 10235 |
| 2022 | 10532 |
| 2023 | 10632 |
| 2024 | 347 |

`validation.json` records field checks, raw missing counts, date-year counts, observed filter values and source/query information. Missing values are retained; no imputation, regression variable construction, analysis-sample filtering or regressions were performed.
