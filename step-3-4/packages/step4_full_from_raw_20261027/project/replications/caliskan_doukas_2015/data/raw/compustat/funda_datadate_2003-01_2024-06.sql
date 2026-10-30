SELECT
    comp_na_daily_all.funda.costat,
    comp_na_daily_all.funda.curcd,
    comp_na_daily_all.funda.datafmt,
    comp_na_daily_all.funda.indfmt,
    comp_na_daily_all.funda.consol,
    comp_na_daily_all.funda.tic,
    comp_na_daily_all.funda.datadate,
    comp_na_daily_all.funda.gvkey,
    comp_na_daily_all.funda.conm,
    comp_na_daily_all.funda.cusip,
    comp_na_daily_all.funda.cik,
    comp_na_daily_all.funda.exchg,
    comp_na_daily_all.funda.fyr,
    comp_na_daily_all.funda.fic,
    id_table.sic,
    comp_na_daily_all.funda.fyear,
    comp_na_daily_all.funda.at,
    comp_na_daily_all.funda.ceq,
    comp_na_daily_all.funda.lt,
    comp_na_daily_all.funda.pstk,
    comp_na_daily_all.funda.pstkl,
    comp_na_daily_all.funda.pstkrv,
    comp_na_daily_all.funda.re,
    comp_na_daily_all.funda.seq,
    comp_na_daily_all.funda.txditc,
    comp_na_daily_all.funda.dvp,
    comp_na_daily_all.funda.ib,
    comp_na_daily_all.funda.txdi,
    comp_na_daily_all.funda.xrd,
    comp_na_daily_all.funda.capx,
    comp_na_daily_all.funda.csho,
    comp_na_daily_all.funda.dvpsx_c,
    comp_na_daily_all.funda.dvpsx_f,
    comp_na_daily_all.funda.prcc_f,
    comp_na_daily_all.funda.sich

FROM comp_na_daily_all.funda
LEFT JOIN (
    SELECT
        gvkey,
        sic
    FROM comp_na_daily_all.company
) AS id_table 

ON comp_na_daily_all.funda.gvkey = id_table.gvkey

WHERE comp_na_daily_all.funda.datadate BETWEEN
    '2003-01-01'::date AND '2024-06-30'::date

AND ("comp_na_daily_all"."funda"."consol" = ANY (ARRAY['C']) AND "comp_na_daily_all"."funda"."indfmt" = ANY (ARRAY['INDL']) AND "comp_na_daily_all"."funda"."datafmt" = ANY (ARRAY['STD']) AND "comp_na_daily_all"."funda"."curcd" = ANY (ARRAY['USD']) AND "comp_na_daily_all"."funda"."costat" = ANY (ARRAY['A','I']))
