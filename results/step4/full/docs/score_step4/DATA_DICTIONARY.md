> Historical implementation snapshot. Machine paths and examples below are archival. Use the package root README for the current portable entry point.

# Step 4：数据字典

整理日期：2026-10-27。对应 analysis_strict_2967.csv (historical source reference: ../data/analysis_strict_2967.csv) 与 Parquet副本 (historical source reference: ../data/analysis_strict_2967.parquet)，共2,967行、66列。两份文件逐值同源；CSV日期为ISO格式，原布尔列输出为True/False，新增样本标记used_ordinary/used_log为0/1；ID应保留原类型。

本表是已严格匹配输入，尚包含40个普通模型未使用的纯组观测；不是所有行都进入每个模型。只有 `ln_rellev` 有1,240个缺失，原因是相对杠杆为0不能取log，这些行仍可用于普通设置。涵盖匹配成功与失败的7,086行目标审计在单独审计表 (historical source reference: ../audit/target_b_2013_2023_matching_disposition.csv)，没有把失败分数填0。

下表按分析数据的实际列顺序列出全部66列。单位沿用财务构建口径，金额不是统一缩放；尤其实际R&D/资产、CAPX/资产和预测分数使用百分点，资产增长、RE/AT等仍是decimal ratio。

| # | 字段 | 单位/类型 | 定义 |
|---:|---|---|---|
| 1 | `event_id` | 标识符字符串 | 六位gvkey:fyear；本表唯一firm-year键。 |
| 2 | `gvkey` | identifier | Compustat company key, string retaining six digits |
| 3 | `fyear` | fiscal year | ExecuComp fiscal year matched to Compustat fyear; current-year controls |
| 4 | `datadate` | date | Compustat fiscal-end data date; Stata %td |
| 5 | `permno` | identifier | Unique date-valid CCM LC/LU, P/C security; no ticker matching |
| 6 | `execid` | identifier | ExecuComp executive identifier |
| 7 | `co_per_rol` | identifier | ExecuComp executive/company role identifier |
| 8 | `conm` | text | Compustat company name |
| 9 | `exec_fullname` | text | ExecuComp executive name |
| 10 | `sich` | industry code | Historical Compustat SIC; missing historical SIC is excluded, not replaced by current SIC |
| 11 | `sic2` | industry code | floor(sich/100), categorical two-digit industry |
| 12 | `formula_version` | text | B_standard_finance；年度CEO选择与历史A版本共用，B不是第二名CEO。 |
| 13 | `payer` | 0/1 | 1(dvpsx_f>0); missing fiscal dividend per share is not zero |
| 14 | `cash_m` | USD millions | (SALARY+BONUS)/1000; original amounts thousands; no missing imputation |
| 15 | `inside_debt_m` | USD millions | (DEFER_BALANCE_TOT+PENSION_VALUE_TOT)/1000; both annual inputs required; detail tables audit only |
| 16 | `ln_rellev` | natural log | ln(rellev), only rellev>0; no log1p or zero-debt fill |
| 17 | `high_rellev` | 0/1 | 1(rellev>1), body-text threshold; missing leverage stays missing |
| 18 | `equity_m` | 百万美元 | [1000×SHROWN_EXCL_OPTS×PRCC_F + 全部期权BSM价值]/1e6；股票不额外加入STOCK_UNVEST_NUM。 |
| 19 | `vega_k` | 千美元 / 波动率1pp | B版全部期权Vega/1000，股票直接Vega=0；未截尾或设置下限。 |
| 20 | `rellev` | ratio | (inside_debt_m/equity_m)/(LT/(PRCC_F*CSHO)); requires positive equity and firm leverage, nonnegative inside debt |
| 21 | `age` | years | Annual ExecuComp AGE, not present-age header PAGE |
| 22 | `ln_tenure` | natural log years | ln(1+floor((datadate-becameceo).days/365.25)); header-date limitation documented |
| 23 | `rd_at_pct` | percentage points | 100*XRD/AT; original missing XRD ->0 only with rd_missing indicator |
| 24 | `rd_missing` | 0/1 | Original XRD missing before the specific R&D ratio fill0 |
| 25 | `capx_at_pct` | percentage points | 100*CAPX/AT; missing CAPX is not zero |
| 26 | `asset_growth` | ratio | (AT_t-AT_t-1)/AT_t-1, strictly consecutive fyear and prior datadate; not multiplied by100 |
| 27 | `mb` | ratio | (PRCC_F*CSHO)/BE；BE=股东权益−优先股权益+TXDITC。股东权益优先SEQ，缺时用CEQ+PSTK，再缺用AT−LT；优先股权益依次PSTKL、PSTKRV、PSTK取首个非缺失。有限负BE保留，零或缺失分母设缺失，不把缺项补0。 |
| 28 | `profitability_m` | USD millions | IB-DVP+TXDITC, literal printed mnemonic; original paper thousand label conflicts with text scale |
| 29 | `size_pct` | percentile 0-100 | 100*count(reference market equity strictly smaller)/N within fiscal year; reference is base-eligible CEO-company-CRSP firms before complete-case filters |
| 30 | `re_at` | ratio | RE/AT, not multiplied by100 |
| 31 | `retvol255` | daily percentage points | 100*sample sd(RETX), ddof1, prior255 true market dates strictly before datadate, all255 valid, not annualized |
| 32 | `sample_log` | 0/1 | 1(rellev>0)，用于m09的对数相对杠杆输入；其它三种设置不要求此标记为1 |
| 33 | `size_ref_n` | 公司数 | 相应财政年度计算size_pct的base-eligible CEO–公司–CRSP参考组N，早于完整案例筛选；本包不重算。 |
| 34 | `score_panel_id` | 源行标识符 | 源ceo_firm_year_panel及risk_scores中的唯一panel_id；本表逐行对应。 |
| 35 | `score_year` | 自然年 | 源讲话聚合的自然年；当前严格输入均等于fyear。 |
| 36 | `score_ceo_id` | 源人物键字符串 | 源面板所选主要讲话者的ceo_id，可能含bx_前缀；不能直接当ExecuComp execid。 |
| 37 | `score_ceo_name` | 文本 | 源面板所选讲话者名称，保留用于追溯。 |
| 38 | `score_companyid` | 标识符 | 源CIQ公司ID；使用官方公司桥核验GVKEY。 |
| 39 | `score_fold` | 折号0–4 | 第一阶段外折测试fold；每个源panel的OOF预测来自未使用本折训练的模型。 |
| 40 | `score_split_group` | 分组标识符 | 第一阶段公司–CEO二部图连接分组；同组不跨外折，不能解释为时序分组。 |
| 41 | `vendor_strict_risk_score_ridge` | R&D/资产 decimal ratio | 严格官方身份/时间匹配接纳的原始Ridge OOF预测，允许负数；不含_full。 |
| 42 | `vendor_strict_risk_score_xgboost` | R&D/资产 decimal ratio | 严格官方身份/时间匹配接纳的原始XGBoost OOF预测，允许负数；不含_full。 |
| 43 | `ridge_clip0_pp` | 百分点 | 100×max(vendor_strict_risk_score_ridge,0)；实际Ridge模型分数项。不是百分位。 |
| 44 | `xgboost_clip0_pp` | 百分点 | 100×max(vendor_strict_risk_score_xgboost,0)；实际XGBoost模型分数项。不是百分位。 |
| 45 | `source_datadate` | 日期 | 源讲话面板匹配的Compustat会计日期；严格守卫要求等于目标datadate。 |
| 46 | `prior_fiscal_end` | 日期 | 目标公司前一连续财政年的财政年末，用于实际FY窗口。 |
| 47 | `fiscal_start` | 日期 | prior_fiscal_end+1天；当前严格输入必须为源自然年1月1日。 |
| 48 | `speech_first` | 日期 | 进入源公司自然年面板的实际讲话component最早日期。 |
| 49 | `speech_last` | 日期 | 进入源公司自然年面板的实际讲话component最晚日期。 |
| 50 | `n_components_audit` | 计数 | 该源公司自然年实际保留的讲话component数。 |
| 51 | `n_transcripts_audit` | 计数 | 该源公司自然年保留component覆盖的不同transcript数。 |
| 52 | `words_audit` | 计数 | 该源公司自然年保留component的词数合计，沿用上游保留词口径。 |
| 53 | `source_identity_method` | 历史诊断标签 | 旧本地继承execid方法：direct_inherited_execid / cross_year_unique_source_ceo_id / no_execid_link；不是当前官方最终接纳状态。no_execid_link行可由官方桥补证。 |
| 54 | `official_directorid` | 标识符 | 源component对应且已核验的BoardEx directorid；不等同transcriptpersonid或CIQ personid。 |
| 55 | `official_person_score1_unique_execid` | 标识符 | People Link score=1层唯一ExecuComp execid；当前接纳行等于目标execid。 |
| 56 | `official_company_temporal_evidence` | 日期证据标签 | undated_links_only：仅无日期边界链接；explicit_bounds_on_all_requests：每次请求至少一条链接具有已知边界，并不保证起止两端同时已知。 |
| 57 | `score_tenure_left_date_known` | 0/1 | 源匹配对应目标CEO的LEFTOFC是否已知；未知并不自动判为离任冲突。 |
| 58 | `official_company_verified` | 0/1 | 所有实际companyid及讲话/源会计日期仅唯一映射到目标GVKEY；缺失链接端点按开放边界。 |
| 59 | `official_person_verified` | 0/1 | 实际BoardEx人物的score=1链接唯一映射目标execid，且component人物ID齐全。 |
| 60 | `official_local_guards` | 0/1 | 候选key、会计日期、姓氏+首字母支持、唯一公司/人物和全局无冲突等原本地守卫通过。 |
| 61 | `official_inherited_execid_compatible` | 0/1 | 已有继承source execid缺失或与目标execid相等，拒绝已有不同ID冲突。 |
| 62 | `official_entity_verified` | 0/1 | 公司桥、人员桥、本地守卫和继承execid兼容全部通过。 |
| 63 | `official_fiscal_compatible` | 0/1 | official_entity_verified且所有讲话位于实际FY内、无已知CEO任职日期冲突。 |
| 64 | `official_strict_period_match` | 0/1 | official_fiscal_compatible且完整FY等于源自然年1月1日至12月31日；本分析表全为真。 |
| 65 | `used_ordinary` | 0/1 | 普通m08/m10/m00最终实际估计e(sample)，两算法及两RD控制组相同；和为2927。 |
| 66 | `used_log` | 0/1 | m09正相对杠杆并经该子样本纯组处理后的最终e(sample)，两算法及两RD控制组相同；和为1653。 |

## 模型内生成的字段与其它数据文件

- `rd_score`：每次选择Ridge或XGBoost后的分数别名；始终使用上表的 `ridge_clip0_pp` 或 `xgboost_clip0_pp`，不同时放入两种算法。
- 逐模型Stata `.dta` 保存该模型的固定输入与相关识别/选择列，不要求包含所有66个审计列；精确入样本ID可与 `reference/samples/*_used.csv` 比较。
- score_provenance_2967.csv (historical source reference: ../data/score_provenance_2967.csv) 是上表中源panel键、公司/CEO/年度、外折、分组和四个分数列的13列投影，方便逐行检查分数版本及转换，不是另一套样本。
- model_specifications.json (historical source reference: ../code/model_specifications.json) 声明16模型的变量、样本、基准类别、设计列及数值尺度。数值尺度用于优化而后还原原单位，不是回归经济变量的额外标准化。
- reference/coefficients.csv (historical source reference: ../reference/coefficients.csv) 保存模型ID、term、系数、OIM与公司聚类SE/z/p及省略标记；reference/model_summary.csv (historical source reference: ../reference/model_summary.csv) 保存输入N、纯组后N、实际N、公司聚类数、LL、收敛与基准类别。
- `*_input.csv`与`*_used.csv`中的 `event_id/gvkey/fyear/payer`识别行；`esample_oim/esample_cluster`指相应Stata拟合的最终估计样本，名称以实际表头为准。

主要变量规则、基样本资格及匹配政策详见方法说明 (historical source reference: METHODS_AND_MATCHING.md)。
