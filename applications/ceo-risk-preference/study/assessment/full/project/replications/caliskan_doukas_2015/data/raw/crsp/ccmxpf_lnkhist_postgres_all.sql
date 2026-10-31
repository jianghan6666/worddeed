SELECT
    crsp_a_ccm.ccmxpf_lnkhist.gvkey,
    crsp_a_ccm.ccmxpf_lnkhist.linkdt,
    crsp_a_ccm.ccmxpf_lnkhist.linkprim,
    crsp_a_ccm.ccmxpf_lnkhist.liid,
    crsp_a_ccm.ccmxpf_lnkhist.linktype,
    crsp_a_ccm.ccmxpf_lnkhist.lpermno,
    crsp_a_ccm.ccmxpf_lnkhist.lpermco,
    crsp_a_ccm.ccmxpf_lnkhist.linkenddt

FROM crsp_a_ccm.ccmxpf_lnkhist

WHERE linkdt BETWEEN
    '1946-01-01'::date AND '2026-01-30'::date
