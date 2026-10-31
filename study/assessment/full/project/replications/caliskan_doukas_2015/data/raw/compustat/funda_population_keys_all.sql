SELECT
    comp_na_daily_all.funda.gvkey,
    comp_na_daily_all.funda.datadate,
    comp_na_daily_all.funda.fyear,
    comp_na_daily_all.funda.indfmt,
    comp_na_daily_all.funda.consol,
    comp_na_daily_all.funda.popsrc,
    comp_na_daily_all.funda.datafmt,
    comp_na_daily_all.funda.curcd,
    comp_na_daily_all.funda.costat

FROM comp_na_daily_all.funda

WHERE 1 = 1
