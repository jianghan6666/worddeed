SELECT
    ciq_common.wrds_gvkey.companyid,
    ciq_common.wrds_gvkey.gvkey,
    ciq_common.wrds_gvkey.companyname,
    ciq_common.wrds_gvkey.startdate,
    ciq_common.wrds_gvkey.enddate,
    ciq_common.wrds_gvkey.primaryflag

FROM ciq_common.wrds_gvkey

WHERE 1 = 1
