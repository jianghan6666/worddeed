* All25 annualCEO B models from reconstructed inputs. Run with cwd=this stata directory.
version 19.0
capture erase "./run_finished.txt"
global REPLAY_FAILURES 0
capture mkdir "samples"
capture mkdir "estimates"
capture mkdir "covariances"
clear all
set more off
set type double
file open START using "./run_started.txt", write replace
file write START "started" _n
file close START
set linesize 255
capture log close _all
log using "./regression.log", text replace
file open VER using "./runtime_version.txt", write replace
file write VER "Stata version " (c(stata_version)) _n
file close VER
postfile PCEOT4COEF str70 model_id str1 version str25 period str8 sample int model str40 term double coef double se_oim double z_oim double p_oim double se_cluster double z_cluster double p_cluster byte omitted_oim byte omitted_cluster using "./coefficients.dta", replace
postfile PCEOT4META str70 model_id str1 version str25 period str8 sample int model str60 status double N_input double N_after_pure double N_oim double N_cluster double N_clusters double ll_oim double ll_cluster double converged_oim double converged_cluster double rc double base_sic2 double base_fyear double core_omitted double max_b_change using "./model_summary.dta", replace
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
    export delimited using "./samples/${MID}_input.csv", replace
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
    estimates save "./estimates/${MID}_oim.ster", replace
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
    estimates save "./estimates/${MID}_cluster.ster", replace
    preserve
    keep event_id gvkey fyear sic2 payer esample_oim esample_cluster probability_oim
    sort event_id
    ds,has(type numeric)
    format `r(varlist)' %24.17g
    export delimited using "./samples/${MID}_used.csv", replace datafmt
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
    save "./covariances/${MID}_oim.dta",replace
    restore
    preserve
    clear
    svmat double VCR,names(v)
    save "./covariances/${MID}_cluster.dta",replace
    restore
    local stat="success"
    if `co'!=1 | `cc'!=1 local stat="not_converged"
    if `coreomit'>0 local stat="core_term_omitted"
    if `no'!=`npure' | `nc'!=`npure' local stat="additional_sample_deletion"
    post PCEOT4META ("$MID") ("$V") ("$PER") ("$SM") ($M) ("`stat'") (`nin') (`npure') (`no') (`nc') (`ng') (`llo') (`llc') (`co') (`cc') (0) ($BSIC) ($BYEAR) (`coreomit') (maxchange)
end



@@MODEL_BLOCKS@@
postclose PCEOT4COEF
postclose PCEOT4META
use "./coefficients.dta", clear
ds, has(type numeric)
format `r(varlist)' %24.17g
export delimited using "./coefficients.csv", replace datafmt
use "./model_summary.dta", clear
ds, has(type numeric)
format `r(varlist)' %24.17g
export delimited using "./model_summary.csv", replace datafmt
count if status!="success"
local bad=r(N)
if `bad'>0 | $REPLAY_FAILURES>0 {
 display as error "Some reconstructed model replay failed; inspect model_summary.csv"
 log close
 exit 459
}
assert _N==25
file open DONE using "./run_finished.txt", write replace
file write DONE "completed" _n
file close DONE
log close
