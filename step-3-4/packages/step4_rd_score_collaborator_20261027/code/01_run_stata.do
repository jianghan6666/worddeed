* STEP 4: annual CEO B, 2013-2023; 16 score models from Excel sheets 3 and 4.
* Start Stata with current working directory set to the extracted package root.
* Run: do code/01_run_stata.do
* All outputs go to rerun/stata; frozen data and reference results remain unchanged.
* Two separate score algorithms; without/with ACTUAL R&D controls, not without/with predicted score.
* Does not retrain first-stage scores or rebuild raw WRDS financial/CEO variables.
version 19.0
capture mkdir "rerun"
capture mkdir "rerun/stata"
capture mkdir "rerun/stata/samples"
capture mkdir "rerun/stata/estimates"
capture mkdir "rerun/stata/covariances"
clear all
capture erase "rerun/stata/run_finished.txt"
global STEP4_FAILURES 0
set more off
set type double
file open START using "rerun/stata/run_started.txt", write replace
file write START "started" _n
file close START
set linesize 255
capture log close _all
log using "rerun/stata/regression.log", text replace
file open VER using "rerun/stata/runtime_version.txt", write replace
file write VER "Stata version " (c(stata_version)) _n
file close VER
postfile PCEOT4COEF str70 model_id str1 version str25 period str8 sample int model str40 term double coef double se_oim double z_oim double p_oim double se_cluster double z_cluster double p_cluster byte omitted_oim byte omitted_cluster using "rerun/stata/coefficients.dta", replace
postfile PCEOT4META str70 model_id str1 version str25 period str8 sample int model str60 status double N_input double N_after_pure double N_oim double N_cluster double N_clusters double ll_oim double ll_cluster double converged_oim double converged_cluster double rc double base_sic2 double base_fyear double core_omitted double max_b_change using "rerun/stata/model_summary.dta", replace
capture program drop table4fit
program define table4fit
    use "$SOURCE", clear
    if "$SM"=="common" {
        if inlist($M,3,9) keep if sample_ab_log==1
        else keep if sample_ab==1
    }
    if inlist($M,3,9) keep if sample_log==1
    local nin=_N
    assert _N==$NINPUT
    gen byte __pure=0
    local changed=1
    while `changed' > 0 {
        quietly count if __pure==1
        local before=r(N)
        foreach fac in sic2 fyear {
            tempvar ymin ymax
            bysort `fac': egen double `ymin'=min(payer) if __pure==0
            bysort `fac': egen double `ymax'=max(payer) if __pure==0
            replace __pure=1 if __pure==0 & !missing(`ymin') & `ymin'==`ymax'
            drop `ymin' `ymax'
        }
        quietly count if __pure==1
        local changed=r(N)-`before'
    }
    preserve
    keep event_id gvkey fyear sic2 payer __pure
    rename __pure pure_group_removed
    export delimited using "rerun/stata/samples/${MID}_input.csv", replace
    restore
    keep if __pure==0
    local npure=_N
    assert _N==$NUSED
    quietly summarize sic2, meanonly
    assert r(min)==$BSIC
    quietly summarize fyear, meanonly
    assert r(min)==$BYEAR
    egen long __cluster=group(gvkey)
    local j=0
    local zs ""
    foreach x of global XVARS {
        local ++j
        local sc: word `j' of $SCALES
        generate double z`j'=`x'/`sc'
        local zs "`zs' z`j'"
    }
    logit payer `zs' ib$BSIC.sic2 ib$BYEAR.fyear, asis collinear difficult iterate(50) tolerance(1e-8) ltolerance(1e-10) nrtolerance(1e-5)
    matrix BO=e(b)
    matrix VO=e(V)
    _ms_omit_info BO
    matrix OO=r(omit)
    local no=e(N)
    local llo=e(ll)
    local co=e(converged)
    local names: colnames BO
    generate byte esample_oim=e(sample)
    predict double probability_oim if esample_oim, pr
    estimates save "rerun/stata/estimates/${MID}_oim.ster", replace
    logit payer `zs' ib$BSIC.sic2 ib$BYEAR.fyear, vce(cluster __cluster) from(BO,copy) asis collinear difficult iterate(50) tolerance(1e-8) ltolerance(1e-10) nrtolerance(1e-5)
    matrix BC=e(b)
    matrix VC=e(V)
    _ms_omit_info BC
    matrix OC=r(omit)
    local nc=e(N)
    local ng=e(N_clust)
    local llc=e(ll)
    local cc=e(converged)
    generate byte esample_cluster=e(sample)
    estimates save "rerun/stata/estimates/${MID}_cluster.ster", replace
    preserve
    keep event_id gvkey fyear sic2 payer esample_oim esample_cluster probability_oim
    sort event_id
    ds,has(type numeric)
    format `r(varlist)' %24.17g
    export delimited using "rerun/stata/samples/${MID}_used.csv", replace datafmt
    restore
    local cols=colsof(BO)
    matrix TR=I(`cols')
    local coreomit=0
    scalar maxchange=0
    forvalues k=1/`cols' {
        local term: word `k' of `names'
        local reportterm "`term'"
        local sc=1
        if regexm("`term'","^z([0-9]+)$") {
            local ix=real(regexs(1))
            local reportterm: word `ix' of $XVARS
            local sc: word `ix' of $SCALES
            local coreomit=`coreomit'+OO[1,`k']
        }
        matrix TR[`k',`k']=1/`sc'
        scalar b=BO[1,`k']/`sc'
        scalar so=sqrt(VO[`k',`k'])/`sc'
        scalar z=b/so
        scalar po=2*normal(-abs(z))
        scalar scv=sqrt(VC[`k',`k'])/`sc'
        scalar zc=b/scv
        scalar pc=2*normal(-abs(zc))
        scalar maxchange=max(maxchange,abs((BO[1,`k']-BC[1,`k'])/`sc'))
        post PCEOT4COEF ("$MID") ("$V") ("$PER") ("$SM") ($M) ("`reportterm'") (b) (so) (z) (po) (scv) (zc) (pc) (OO[1,`k']) (OC[1,`k'])
    }
    matrix VOR=TR*VO*TR
    matrix VCR=TR*VC*TR
    preserve
    clear
    svmat double VOR,names(v)
    save "rerun/stata/covariances/${MID}_oim.dta",replace
    restore
    preserve
    clear
    svmat double VCR,names(v)
    save "rerun/stata/covariances/${MID}_cluster.dta",replace
    restore
    local stat="success"
    if `co'!=1 | `cc'!=1 local stat="not_converged"
    if `coreomit'>0 local stat="core_term_omitted"
    if `no'!=`npure' | `nc'!=`npure' local stat="additional_sample_deletion"
    post PCEOT4META ("$MID") ("$V") ("$PER") ("$SM") ($M) ("`stat'") (`nin') (`npure') (`no') (`nc') (`ng') (`llo') (`llc') (`co') (`cc') (0) ($BSIC) ($BYEAR) (`coreomit') (maxchange)
end




global MID "score_xgboost_no_rd_m08"
global V "b"
global PER "2013_2023"
global SM "natural"
global M "8"
global SOURCE "data/stata_inputs/score_xgboost_no_rd_m08.dta"
global XVARS "rd_score cash_m inside_debt_m equity_m vega_k age ln_tenure capx_at_pct asset_growth mb profitability_m size_pct re_at retvol255"
global SCALES "8.8432427357883903 1.314351670746732 16.946151253111175 4986.6732447282538 2209.6718592096577 57.596128110764134 2.0602360438203218 5.4817793936769039 0.36283989002245898 360.5431477636688 4591.3137340481035 62.913106001951668 1.201990217628413 2.6115554215286636"
global NINPUT "2967"
global NUSED "2927"
global BSIC "10"
global BYEAR "2013"
capture noisily table4fit
local modelrc=_rc
if `modelrc'!=0 {
    global STEP4_FAILURES = $STEP4_FAILURES + 1
    post PCEOT4META ("$MID") ("$V") ("$PER") ("$SM") ($M) ("stata_command_error") ($NINPUT) ($NUSED) (.) (.) (.) (.) (.) (.) (.) (`modelrc') ($BSIC) ($BYEAR) (.) (.)
}
global MID "score_xgboost_no_rd_m09"
global V "b"
global PER "2013_2023"
global SM "natural"
global M "9"
global SOURCE "data/stata_inputs/score_xgboost_no_rd_m09.dta"
global XVARS "rd_score cash_m ln_rellev equity_m vega_k age ln_tenure capx_at_pct asset_growth mb profitability_m size_pct re_at retvol255"
global SCALES "4.7131216063225754 1.395588362696407 2.4529204912974278 224.95882481955556 479.67145150428036 57.851035312700851 1.9557452218344431 5.5128694843959787 0.31853606894544828 476.22615552265478 5936.8418489101141 69.70907051354871 0.5262468078264505 2.3338698879444286"
global NINPUT "1727"
global NUSED "1653"
global BSIC "10"
global BYEAR "2013"
capture noisily table4fit
local modelrc=_rc
if `modelrc'!=0 {
    global STEP4_FAILURES = $STEP4_FAILURES + 1
    post PCEOT4META ("$MID") ("$V") ("$PER") ("$SM") ($M) ("stata_command_error") ($NINPUT) ($NUSED) (.) (.) (.) (.) (.) (.) (.) (`modelrc') ($BSIC) ($BYEAR) (.) (.)
}
global MID "score_xgboost_no_rd_m10"
global V "b"
global PER "2013_2023"
global SM "natural"
global M "10"
global SOURCE "data/stata_inputs/score_xgboost_no_rd_m10.dta"
global XVARS "rd_score cash_m high_rellev equity_m vega_k age ln_tenure capx_at_pct asset_growth mb profitability_m size_pct re_at retvol255"
global SCALES "8.8432427357883903 1.314351670746732 0.33881160506090907 4986.6732447282538 2209.6718592096577 57.596128110764134 2.0602360438203218 5.4817793936769039 0.36283989002245898 360.5431477636688 4591.3137340481035 62.913106001951668 1.201990217628413 2.6115554215286636"
global NINPUT "2967"
global NUSED "2927"
global BSIC "10"
global BYEAR "2013"
capture noisily table4fit
local modelrc=_rc
if `modelrc'!=0 {
    global STEP4_FAILURES = $STEP4_FAILURES + 1
    post PCEOT4META ("$MID") ("$V") ("$PER") ("$SM") ($M) ("stata_command_error") ($NINPUT) ($NUSED) (.) (.) (.) (.) (.) (.) (.) (`modelrc') ($BSIC) ($BYEAR) (.) (.)
}
global MID "score_xgboost_no_rd_m00"
global V "b"
global PER "2013_2023"
global SM "natural"
global M "0"
global SOURCE "data/stata_inputs/score_xgboost_no_rd_m00.dta"
global XVARS "rd_score cash_m equity_m age ln_tenure capx_at_pct asset_growth mb profitability_m size_pct re_at retvol255"
global SCALES "8.8432427357883903 1.314351670746732 4986.6732447282538 57.596128110764134 2.0602360438203218 5.4817793936769039 0.36283989002245898 360.5431477636688 4591.3137340481035 62.913106001951668 1.201990217628413 2.6115554215286636"
global NINPUT "2967"
global NUSED "2927"
global BSIC "10"
global BYEAR "2013"
capture noisily table4fit
local modelrc=_rc
if `modelrc'!=0 {
    global STEP4_FAILURES = $STEP4_FAILURES + 1
    post PCEOT4META ("$MID") ("$V") ("$PER") ("$SM") ($M) ("stata_command_error") ($NINPUT) ($NUSED) (.) (.) (.) (.) (.) (.) (.) (`modelrc') ($BSIC) ($BYEAR) (.) (.)
}
global MID "score_ridge_no_rd_m08"
global V "b"
global PER "2013_2023"
global SM "natural"
global M "8"
global SOURCE "data/stata_inputs/score_ridge_no_rd_m08.dta"
global XVARS "rd_score cash_m inside_debt_m equity_m vega_k age ln_tenure capx_at_pct asset_growth mb profitability_m size_pct re_at retvol255"
global SCALES "8.7749147590729404 1.314351670746732 16.946151253111175 4986.6732447282538 2209.6718592096577 57.596128110764134 2.0602360438203218 5.4817793936769039 0.36283989002245898 360.5431477636688 4591.3137340481035 62.913106001951668 1.201990217628413 2.6115554215286636"
global NINPUT "2967"
global NUSED "2927"
global BSIC "10"
global BYEAR "2013"
capture noisily table4fit
local modelrc=_rc
if `modelrc'!=0 {
    global STEP4_FAILURES = $STEP4_FAILURES + 1
    post PCEOT4META ("$MID") ("$V") ("$PER") ("$SM") ($M) ("stata_command_error") ($NINPUT) ($NUSED) (.) (.) (.) (.) (.) (.) (.) (`modelrc') ($BSIC) ($BYEAR) (.) (.)
}
global MID "score_ridge_no_rd_m09"
global V "b"
global PER "2013_2023"
global SM "natural"
global M "9"
global SOURCE "data/stata_inputs/score_ridge_no_rd_m09.dta"
global XVARS "rd_score cash_m ln_rellev equity_m vega_k age ln_tenure capx_at_pct asset_growth mb profitability_m size_pct re_at retvol255"
global SCALES "5.6435468461081504 1.395588362696407 2.4529204912974278 224.95882481955556 479.67145150428036 57.851035312700851 1.9557452218344431 5.5128694843959787 0.31853606894544828 476.22615552265478 5936.8418489101141 69.70907051354871 0.5262468078264505 2.3338698879444286"
global NINPUT "1727"
global NUSED "1653"
global BSIC "10"
global BYEAR "2013"
capture noisily table4fit
local modelrc=_rc
if `modelrc'!=0 {
    global STEP4_FAILURES = $STEP4_FAILURES + 1
    post PCEOT4META ("$MID") ("$V") ("$PER") ("$SM") ($M) ("stata_command_error") ($NINPUT) ($NUSED) (.) (.) (.) (.) (.) (.) (.) (`modelrc') ($BSIC) ($BYEAR) (.) (.)
}
global MID "score_ridge_no_rd_m10"
global V "b"
global PER "2013_2023"
global SM "natural"
global M "10"
global SOURCE "data/stata_inputs/score_ridge_no_rd_m10.dta"
global XVARS "rd_score cash_m high_rellev equity_m vega_k age ln_tenure capx_at_pct asset_growth mb profitability_m size_pct re_at retvol255"
global SCALES "8.7749147590729404 1.314351670746732 0.33881160506090907 4986.6732447282538 2209.6718592096577 57.596128110764134 2.0602360438203218 5.4817793936769039 0.36283989002245898 360.5431477636688 4591.3137340481035 62.913106001951668 1.201990217628413 2.6115554215286636"
global NINPUT "2967"
global NUSED "2927"
global BSIC "10"
global BYEAR "2013"
capture noisily table4fit
local modelrc=_rc
if `modelrc'!=0 {
    global STEP4_FAILURES = $STEP4_FAILURES + 1
    post PCEOT4META ("$MID") ("$V") ("$PER") ("$SM") ($M) ("stata_command_error") ($NINPUT) ($NUSED) (.) (.) (.) (.) (.) (.) (.) (`modelrc') ($BSIC) ($BYEAR) (.) (.)
}
global MID "score_ridge_no_rd_m00"
global V "b"
global PER "2013_2023"
global SM "natural"
global M "0"
global SOURCE "data/stata_inputs/score_ridge_no_rd_m00.dta"
global XVARS "rd_score cash_m equity_m age ln_tenure capx_at_pct asset_growth mb profitability_m size_pct re_at retvol255"
global SCALES "8.7749147590729404 1.314351670746732 4986.6732447282538 57.596128110764134 2.0602360438203218 5.4817793936769039 0.36283989002245898 360.5431477636688 4591.3137340481035 62.913106001951668 1.201990217628413 2.6115554215286636"
global NINPUT "2967"
global NUSED "2927"
global BSIC "10"
global BYEAR "2013"
capture noisily table4fit
local modelrc=_rc
if `modelrc'!=0 {
    global STEP4_FAILURES = $STEP4_FAILURES + 1
    post PCEOT4META ("$MID") ("$V") ("$PER") ("$SM") ($M) ("stata_command_error") ($NINPUT) ($NUSED) (.) (.) (.) (.) (.) (.) (.) (`modelrc') ($BSIC) ($BYEAR) (.) (.)
}
global MID "score_xgboost_with_rd_m08"
global V "b"
global PER "2013_2023"
global SM "natural"
global M "8"
global SOURCE "data/stata_inputs/score_xgboost_with_rd_m08.dta"
global XVARS "rd_score cash_m inside_debt_m equity_m vega_k age ln_tenure rd_at_pct rd_missing capx_at_pct asset_growth mb profitability_m size_pct re_at retvol255"
global SCALES "8.8432427357883903 1.314351670746732 16.946151253111175 4986.6732447282538 2209.6718592096577 57.596128110764134 2.0602360438203218 10.025909601777142 0.55327703422173458 5.4817793936769039 0.36283989002245898 360.5431477636688 4591.3137340481035 62.913106001951668 1.201990217628413 2.6115554215286636"
global NINPUT "2967"
global NUSED "2927"
global BSIC "10"
global BYEAR "2013"
capture noisily table4fit
local modelrc=_rc
if `modelrc'!=0 {
    global STEP4_FAILURES = $STEP4_FAILURES + 1
    post PCEOT4META ("$MID") ("$V") ("$PER") ("$SM") ($M) ("stata_command_error") ($NINPUT) ($NUSED) (.) (.) (.) (.) (.) (.) (.) (`modelrc') ($BSIC) ($BYEAR) (.) (.)
}
global MID "score_xgboost_with_rd_m09"
global V "b"
global PER "2013_2023"
global SM "natural"
global M "9"
global SOURCE "data/stata_inputs/score_xgboost_with_rd_m09.dta"
global XVARS "rd_score cash_m ln_rellev equity_m vega_k age ln_tenure rd_at_pct rd_missing capx_at_pct asset_growth mb profitability_m size_pct re_at retvol255"
global SCALES "4.7131216063225754 1.395588362696407 2.4529204912974278 224.95882481955556 479.67145150428036 57.851035312700851 1.9557452218344431 3.9909620968616193 0.56837399818682943 5.5128694843959787 0.31853606894544828 476.22615552265478 5936.8418489101141 69.70907051354871 0.5262468078264505 2.3338698879444286"
global NINPUT "1727"
global NUSED "1653"
global BSIC "10"
global BYEAR "2013"
capture noisily table4fit
local modelrc=_rc
if `modelrc'!=0 {
    global STEP4_FAILURES = $STEP4_FAILURES + 1
    post PCEOT4META ("$MID") ("$V") ("$PER") ("$SM") ($M) ("stata_command_error") ($NINPUT) ($NUSED) (.) (.) (.) (.) (.) (.) (.) (`modelrc') ($BSIC) ($BYEAR) (.) (.)
}
global MID "score_xgboost_with_rd_m10"
global V "b"
global PER "2013_2023"
global SM "natural"
global M "10"
global SOURCE "data/stata_inputs/score_xgboost_with_rd_m10.dta"
global XVARS "rd_score cash_m high_rellev equity_m vega_k age ln_tenure rd_at_pct rd_missing capx_at_pct asset_growth mb profitability_m size_pct re_at retvol255"
global SCALES "8.8432427357883903 1.314351670746732 0.33881160506090907 4986.6732447282538 2209.6718592096577 57.596128110764134 2.0602360438203218 10.025909601777142 0.55327703422173458 5.4817793936769039 0.36283989002245898 360.5431477636688 4591.3137340481035 62.913106001951668 1.201990217628413 2.6115554215286636"
global NINPUT "2967"
global NUSED "2927"
global BSIC "10"
global BYEAR "2013"
capture noisily table4fit
local modelrc=_rc
if `modelrc'!=0 {
    global STEP4_FAILURES = $STEP4_FAILURES + 1
    post PCEOT4META ("$MID") ("$V") ("$PER") ("$SM") ($M) ("stata_command_error") ($NINPUT) ($NUSED) (.) (.) (.) (.) (.) (.) (.) (`modelrc') ($BSIC) ($BYEAR) (.) (.)
}
global MID "score_xgboost_with_rd_m00"
global V "b"
global PER "2013_2023"
global SM "natural"
global M "0"
global SOURCE "data/stata_inputs/score_xgboost_with_rd_m00.dta"
global XVARS "rd_score cash_m equity_m age ln_tenure rd_at_pct rd_missing capx_at_pct asset_growth mb profitability_m size_pct re_at retvol255"
global SCALES "8.8432427357883903 1.314351670746732 4986.6732447282538 57.596128110764134 2.0602360438203218 10.025909601777142 0.55327703422173458 5.4817793936769039 0.36283989002245898 360.5431477636688 4591.3137340481035 62.913106001951668 1.201990217628413 2.6115554215286636"
global NINPUT "2967"
global NUSED "2927"
global BSIC "10"
global BYEAR "2013"
capture noisily table4fit
local modelrc=_rc
if `modelrc'!=0 {
    global STEP4_FAILURES = $STEP4_FAILURES + 1
    post PCEOT4META ("$MID") ("$V") ("$PER") ("$SM") ($M) ("stata_command_error") ($NINPUT) ($NUSED) (.) (.) (.) (.) (.) (.) (.) (`modelrc') ($BSIC) ($BYEAR) (.) (.)
}
global MID "score_ridge_with_rd_m08"
global V "b"
global PER "2013_2023"
global SM "natural"
global M "8"
global SOURCE "data/stata_inputs/score_ridge_with_rd_m08.dta"
global XVARS "rd_score cash_m inside_debt_m equity_m vega_k age ln_tenure rd_at_pct rd_missing capx_at_pct asset_growth mb profitability_m size_pct re_at retvol255"
global SCALES "8.7749147590729404 1.314351670746732 16.946151253111175 4986.6732447282538 2209.6718592096577 57.596128110764134 2.0602360438203218 10.025909601777142 0.55327703422173458 5.4817793936769039 0.36283989002245898 360.5431477636688 4591.3137340481035 62.913106001951668 1.201990217628413 2.6115554215286636"
global NINPUT "2967"
global NUSED "2927"
global BSIC "10"
global BYEAR "2013"
capture noisily table4fit
local modelrc=_rc
if `modelrc'!=0 {
    global STEP4_FAILURES = $STEP4_FAILURES + 1
    post PCEOT4META ("$MID") ("$V") ("$PER") ("$SM") ($M) ("stata_command_error") ($NINPUT) ($NUSED) (.) (.) (.) (.) (.) (.) (.) (`modelrc') ($BSIC) ($BYEAR) (.) (.)
}
global MID "score_ridge_with_rd_m09"
global V "b"
global PER "2013_2023"
global SM "natural"
global M "9"
global SOURCE "data/stata_inputs/score_ridge_with_rd_m09.dta"
global XVARS "rd_score cash_m ln_rellev equity_m vega_k age ln_tenure rd_at_pct rd_missing capx_at_pct asset_growth mb profitability_m size_pct re_at retvol255"
global SCALES "5.6435468461081504 1.395588362696407 2.4529204912974278 224.95882481955556 479.67145150428036 57.851035312700851 1.9557452218344431 3.9909620968616193 0.56837399818682943 5.5128694843959787 0.31853606894544828 476.22615552265478 5936.8418489101141 69.70907051354871 0.5262468078264505 2.3338698879444286"
global NINPUT "1727"
global NUSED "1653"
global BSIC "10"
global BYEAR "2013"
capture noisily table4fit
local modelrc=_rc
if `modelrc'!=0 {
    global STEP4_FAILURES = $STEP4_FAILURES + 1
    post PCEOT4META ("$MID") ("$V") ("$PER") ("$SM") ($M) ("stata_command_error") ($NINPUT) ($NUSED) (.) (.) (.) (.) (.) (.) (.) (`modelrc') ($BSIC) ($BYEAR) (.) (.)
}
global MID "score_ridge_with_rd_m10"
global V "b"
global PER "2013_2023"
global SM "natural"
global M "10"
global SOURCE "data/stata_inputs/score_ridge_with_rd_m10.dta"
global XVARS "rd_score cash_m high_rellev equity_m vega_k age ln_tenure rd_at_pct rd_missing capx_at_pct asset_growth mb profitability_m size_pct re_at retvol255"
global SCALES "8.7749147590729404 1.314351670746732 0.33881160506090907 4986.6732447282538 2209.6718592096577 57.596128110764134 2.0602360438203218 10.025909601777142 0.55327703422173458 5.4817793936769039 0.36283989002245898 360.5431477636688 4591.3137340481035 62.913106001951668 1.201990217628413 2.6115554215286636"
global NINPUT "2967"
global NUSED "2927"
global BSIC "10"
global BYEAR "2013"
capture noisily table4fit
local modelrc=_rc
if `modelrc'!=0 {
    global STEP4_FAILURES = $STEP4_FAILURES + 1
    post PCEOT4META ("$MID") ("$V") ("$PER") ("$SM") ($M) ("stata_command_error") ($NINPUT) ($NUSED) (.) (.) (.) (.) (.) (.) (.) (`modelrc') ($BSIC) ($BYEAR) (.) (.)
}
global MID "score_ridge_with_rd_m00"
global V "b"
global PER "2013_2023"
global SM "natural"
global M "0"
global SOURCE "data/stata_inputs/score_ridge_with_rd_m00.dta"
global XVARS "rd_score cash_m equity_m age ln_tenure rd_at_pct rd_missing capx_at_pct asset_growth mb profitability_m size_pct re_at retvol255"
global SCALES "8.7749147590729404 1.314351670746732 4986.6732447282538 57.596128110764134 2.0602360438203218 10.025909601777142 0.55327703422173458 5.4817793936769039 0.36283989002245898 360.5431477636688 4591.3137340481035 62.913106001951668 1.201990217628413 2.6115554215286636"
global NINPUT "2967"
global NUSED "2927"
global BSIC "10"
global BYEAR "2013"
capture noisily table4fit
local modelrc=_rc
if `modelrc'!=0 {
    global STEP4_FAILURES = $STEP4_FAILURES + 1
    post PCEOT4META ("$MID") ("$V") ("$PER") ("$SM") ($M) ("stata_command_error") ($NINPUT) ($NUSED) (.) (.) (.) (.) (.) (.) (.) (`modelrc') ($BSIC) ($BYEAR) (.) (.)
}
postclose PCEOT4COEF
postclose PCEOT4META
use "rerun/stata/coefficients.dta", clear
ds, has(type numeric)
format `r(varlist)' %24.17g
export delimited using "rerun/stata/coefficients.csv", replace datafmt
use "rerun/stata/model_summary.dta", clear
ds, has(type numeric)
format `r(varlist)' %24.17g
export delimited using "rerun/stata/model_summary.csv", replace datafmt
count if status!="success"
local bad=r(N)
if `bad'>0 | $STEP4_FAILURES>0 {
    display as error "STEP 4 replay failed: inspect rerun/stata/model_summary.csv and regression.log"
    log close
    exit 459
}
assert _N==16
file open DONE using "rerun/stata/run_finished.txt", write replace
file write DONE "completed" _n
file close DONE
log close
display as result "STEP 4 replay completed: 16 models. Compare with reference using code/02_check_stata.py."
