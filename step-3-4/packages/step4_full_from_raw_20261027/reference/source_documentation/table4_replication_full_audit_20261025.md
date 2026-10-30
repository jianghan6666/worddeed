> Historical implementation snapshot. Machine paths and examples below are archival. Use the package root README for the current portable entry point.

# “2 Replication”完整实现与核验说明

**核对日期：2026-10-25（America/New_York）。这是当前已保存结果的实现说明，不是候选计划。**

对象是 table4_annual_b_tables.xlsx (historical source reference: D:/pc_workspace_local/ceo_risk_taking/outputs/01a17125-70eb-72b1-abff-27491f3aec3e/table4_annual_b_tables.xlsx) 的 **`2 Replication`工作表**，三个财政年度窗口各有第(8)–(10)列，共9个Logit模型。当前工作簿SHA256：`8f3df019e71f2c3d5b8281e51d3fc59936fe0fef5518b45a5f1686843ac1ae40`。

本文把“实际代码做了什么”“对应的证据在哪里”“哪些原文规则尚未恢复”分开记录。整理期间只读取既有数据、代码、估计和Excel，未重新构造研究变量、运行回归或修改工作簿。

### 目录

- [范围、版本和九列样本指纹](#scope)
- [原始数据、连接与样本预处理](#data)
- [变量、期权估值和历史窗口公式](#variables)
- [模型、标准误、数值方法和安全重跑](#models)
- [工作表全部系数与聚类SE](#estimates)
- [完整FE集合与逐模型文件](#design)
- [单位依据及与原论文的差异](#differences)
- [本次实际完成的只读核验](#verification)
- [优先核验的问题清单](#checklist)

<a id="scope"></a>

## 1. 先核对这六件事

1. **年度CEO B、公司年度为观测单位。** 每个公司财政年度选择唯一CEO；`event_id=gvkey:fyear`，期权估值另带CEO的`execid`。无PCEO附加条件。
2. **本页无Ridge/XGBoost score，也不受其覆盖限制。** 2013–2023使用完整年度B源样本；不是其他score页的2927/1653观测。
3. **当前是“删除Delta/Vega回归项”的修改规格。** 第(8)/(9)/(10)的内部债务代理分别为金额、自然对数相对杠杆、高相对杠杆dummy；三式都保留Vega、equity、cash、实际R&D和missing dummy。
4. **删除回归项没有放宽原B资格。** 建表仍要求正Vega、可计算且有限的DVR及其他组合指标；原来不满足这些条件的行没有放回。这与“只按当前无DVR解释变量重新找最大完整案例样本”不同。
5. **括号为公司`gvkey`聚类SE。** 行业SIC2和财政年度dummy是两组相加FE，不是行业/年份聚类。主表系数/SE/星号来自Stata；LL/pseudo-R² footer来自Python元数据，二者已数值核对。
6. **未恢复作者最终样本和全部操作定义。** 论文原期普通/log N为2117/834；当前原期N为5736/3416，且原文(8)–(10)含DVR，故不能把本页称为作者方程与样本的精确复制。

### 文件和路径约定

| 名称 | 本文所指位置 |
|---|---|
| PROJECT | `D:/pc_workspace_local/ceo_risk_taking` |
| REP | `D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015` |
| RUN（最新完整25模型结果根） | `D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/results/table4_compilation_rep_2013_2023_20261025` |
| 当前9模型的权威估计 | Stata系数、OIM/公司cluster SE与p (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/results/table4_compilation_rep_2013_2023_20261025/stata/coefficients.csv) |
| 当前面板及显示值索引 | [table_payload.json的tables[1]](<D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/results/table4_compilation_rep_2013_2023_20261025/table_payload.json>)；displayed_table_cells.csv中table_id=table2 (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/results/table4_compilation_rep_2013_2023_20261025/displayed_table_cells.csv) |
| 最终版本状态 | run_manifest.json (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/results/table4_compilation_rep_2013_2023_20261025/run_manifest.json)，不是旧估计结束快照 |
| 源构建状态/决策 | build_config.json (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/build_config.json)；build_manifest.json (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/build_manifest.json) |

默认相对路径以REP为根；明确写PROJECT或RUN的路径按上表解释。原始数据、公司/CEO键和精确ID均属于本地研究资料。本文没有新发布或上传这些数据。

### 当前主文件与R18冻结副本的差异

当前主文件的二进制SHA是上方的`8f3df019e71f2c3d5b8281e51d3fc59936fe0fef5518b45a5f1686843ac1ae40`；重跑ZIP里的历史冻结副本是`8ca0ad7fa448f9b1622a62d8f351191b286bcf5aca9db072c8b2fb2c44bcceb3`。两者不同，本次没有替换任何一份文件。

现场对比`2 Replication!A1:D220`：全部估计数值、原有变量标签、footer和公式都相同；仅新增两条非估计文字：

| 单元格 | 冻结副本 | 当前主文件 | 所在位置 |
|---|---|---|---|
| A20 | 空白 | 方向不一致 | 2006–2011面板CEO age的SE行左侧 |
| A22 | 空白 | 方向不一致 | 2006–2011面板Log CEO tenure的SE行左侧 |

这两条是当前文件中的注记，不是模型变量、估计输出或样本筛选规则；本次没有推断其添加者。当前144个系数格的负数格式由`-`改写成转义`\-`，归一化后显示语义和星号一致。另有字体family元数据及两注记字体、默认行高15→14、B:D有效列宽约18.13→18.164的保存差异，冻结窗格B7、显式行尺寸、合并和打印设置保持。完整差异证据：current_vs_frozen_sheet2.json (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/audits/replication_documentation_20261025/current_vs_frozen_sheet2.json)。

### 九列的样本指纹

下列payer数量由当前Stata实际`e(sample)`文件重新读取，分母是实际估计N。不同列的N差异先来自正相对杠杆限制，再来自pure-group剔除。

| model_id | 输入N | 实际N | 公司G | payer=1数量 | payer比例 | 自由参数K |
| --- | --- | --- | --- | --- | --- | --- |
| rep_original_2006_2011_m08 | 5826 | 5736 | 1424 | 2581 | 0.449965 | 70 |
| rep_original_2006_2011_m09 | 3495 | 3416 | 850 | 2089 | 0.611534 | 68 |
| rep_original_2006_2011_m10 | 5826 | 5736 | 1424 | 2581 | 0.449965 | 70 |
| rep_extended_2006_2023_m08 | 13828 | 13716 | 1793 | 6826 | 0.497667 | 84 |
| rep_extended_2006_2023_m09 | 7903 | 7784 | 1055 | 5200 | 0.668037 | 82 |
| rep_extended_2006_2023_m10 | 13828 | 13716 | 1793 | 6826 | 0.497667 | 84 |
| rep_2013_2023_m08 | 7086 | 7035 | 1304 | 3752 | 0.533333 | 76 |
| rep_2013_2023_m09 | 3889 | 3782 | 728 | 2692 | 0.711793 | 71 |
| rep_2013_2023_m10 | 7086 | 7035 | 1304 | 3752 | 0.533333 | 76 |

<a id="data"></a>

## 2. 原始数据、连接与样本预处理



核查日期：2026-10-25；核对者：Codex。下文 `REP` 指 `D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015`。本段依据当前构建代码、原始下载元数据及实际 parquet/csv 计算；未下载、重建变量或重新估计。两份协作记录已经读取，但没有仅凭其中的历史“尚未回归”标记判断当前状态。

### 1. 下载来源与文件

当前数据构建直接涉及10份原始文件。download_manifest.json (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/download_manifest.json)有11个下载条目，其中110,124行 legacy CCM 是保留的历史快照；当前构建使用123,388行 Postgres CCM。原始文件总行数相加不是研究样本量，不同来源间也不是去重后的公司年度数。

下表时间均为下载元数据所记UTC时间；下表所列原始SHA来自下载/构建清单；本次整理另对构建清单全部11份raw文件逐字节重算SHA256，包含日度大表，全部匹配，见文末完整性核验。

| 数据源/功能 | 本地原始文件（REP相对路径） | query id | 原始行数×列数 | 实际覆盖 | 下载UTC |
|---|---|---:|---:|---|---|
| WRDS S&P ExecuComp Annual Compensation | data/raw/execucomp/anncomp_1992_2023_allfields.csv.gz (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/data/raw/execucomp/anncomp_1992_2023_allfields.csv.gz) | 11827426 | 364,196×107 | 财年1992–2023 | 2026-10-24 19:21:21.698 |
| ExecuComp Outstanding Awards | data/raw/execucomp/outstandingawards_2006_2023_allfields.csv.gz (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/data/raw/execucomp/outstandingawards_2006_2023_allfields.csv.gz) | 11827427 | 1,245,777×50 | 财年2006–2023 | 2026-10-24 19:22:45.396 |
| ExecuComp Pension detail（核对用途） | data/raw/execucomp/pension_2006_2023_allfields.csv.gz (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/data/raw/execucomp/pension_2006_2023_allfields.csv.gz) | 11827430 | 109,154×44 | 财年2006–2023 | 2026-10-24 19:23:51.086 |
| ExecuComp Deferred Compensation detail（核对用途） | data/raw/execucomp/deferredcomp_2006_2023_allfields.csv.gz (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/data/raw/execucomp/deferredcomp_2006_2023_allfields.csv.gz) | 11827432 | 111,504×46 | 财年2006–2023 | 2026-10-24 19:25:09.270 |
| WRDS Compustat North America Daily Fundamentals Annual | data/raw/compustat/funda_datadate_2003-01_2024-06.csv.gz (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/data/raw/compustat/funda_datadate_2003-01_2024-06.csv.gz) | 11827424 | 200,950×35 | datadate 2003-01-31–2024-06-30 | 2026-10-24 19:19:45.771 |
| Compustat POPSRC补充键表 | data/raw/compustat/funda_population_keys_all.csv.gz (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/data/raw/compustat/funda_population_keys_all.csv.gz) | 11827497 | 942,621×9 | datadate 1950-06-30–2026-09-30 | 2026-10-24 20:01:53.541 |
| 当前完整 CCM Postgres link history | data/raw/crsp/ccmxpf_lnkhist_postgres_all.csv.gz (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/data/raw/crsp/ccmxpf_lnkhist_postgres_all.csv.gz) | 11827499 | 123,388×8 | linkdt 1946-01-01–2026-01-30；未到期末值保留缺失 | 2026-10-24 20:02:20.795 |
| WRDS CRSP Legacy Annual SIZ monthly | data/raw/crsp/msf_all_2000-12_2024-06.csv.gz (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/data/raw/crsp/msf_all_2000-12_2024-06.csv.gz) | 11827433 | 2,132,669×15 | 2000-12-29–2024-06-28 | 2026-10-24 19:25:53.371 |
| WRDS CRSP Legacy Annual SIZ daily | data/raw/crsp/dsf_all_2005-01-01_2024-06-30.csv.gz (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/data/raw/crsp/dsf_all_2005-01-01_2024-06-30.csv.gz) | 11827435 | 36,618,473×11 | 2005-01-03–2024-06-28 | 2026-10-24 19:29:12.824 |
| FRED DTB3；底层来源Federal Reserve H.15 | data/raw/fred/DTB3_2005-01-01_2024-06-30.csv (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/data/raw/fred/DTB3_2005-01-01_2024-06-30.csv) | 不适用 | 5,085×2 | 2005-01-03–2024-06-28 | 2026-10-24 19:18:04.910 |

日度/月度下载采用 **CRSP Legacy SIZ**，不能默认为新版CIZ。SAS Legacy表单没有提供SQL下载；其精确请求字段和可见payload参数保存在 data/raw/crsp/stock_download_metadata.json (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/data/raw/crsp/stock_download_metadata.json)，不要把这两表说成保存了可下载的SQL。ExecuComp、Compustat及当前Postgres CCM有原SQL。每个WRDS query可按 `https://wrds-www.wharton.upenn.edu/query-manager/query/<id>/` 在有权限的登录会话中核对。

原始FRED DTB3的标题是 `3-Month Treasury Bill Secondary Market Rate, Discount Basis`，单位为年百分率、未季调；5,085行中207行为原始缺失、4,878行有值。源页为 https://fred.stlouisfed.org/series/DTB3 。下载保留缺失，没有先填补利率。

原始元数据入口：data/raw/execucomp/download_metadata.json (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/data/raw/execucomp/download_metadata.json)、data/raw/compustat/download_metadata.json (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/data/raw/compustat/download_metadata.json)、data/raw/crsp/stock_download_metadata.json (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/data/raw/crsp/stock_download_metadata.json)、data/raw/fred/DTB3_metadata.json (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/data/raw/fred/DTB3_metadata.json)。补充POPSRC和CCM的后续来源核对在 metadata/source_audit_20261024.json (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/metadata/source_audit_20261024.json) 与 download_manifest.json (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/download_manifest.json)；初始Compustat metadata里“未取得popsrc”是当时状态，不能覆盖后续已经完成的补充。

#### 原始文件SHA256清单

| 原始文件简称 | 清单记录的SHA256 |
|---|---|
| anncomp | `724e65e4748724bba9d8673218d9237db89bc2c5436e6f9d5e736e8d6ccbf9ac` |
| outstandingawards | `c0bca00b66b96de191a6235a7feddc8c02aadb71ad20a051c1b291cd5195b8b9` |
| pension | `c3b352f4b285448e6cad3cfc86cdc60ade037ca2d8830186144d257adcac6be7` |
| deferredcomp | `a288fe545ead67e6692301d35c8c402ccebcb067b427fecf141420bdb2d4d561` |
| funda金融数值 | `885730ce1967bac4a4c79313805730f3d10114b8e35dfadee0d1c9d8d7f45b3f` |
| funda POPSRC补充键 | `4a88ca650aae23cc8cfdd112b9ea1eb812c73b9d054c80c9bca62eb8c6e1f2c0` |
| 当前Postgres CCM | `21294af9b68abc6d12e333521743459f3f45509d14547649349e4ef49f5ef905` |
| CRSP monthly | `bb5e4b1af023bc9a11ab0cca444b498c8fd4dbe968a42ff1e6fd9640b7b49dc5` |
| CRSP daily | `248b2903269864d287e7649006b14720d1993027be647cf5390d0d9b8d1b7d86` |
| DTB3 | `c75a500df79ed08cd24922a20ba58b564b54abd77629dbbe1fcad99ae1170a86` |

### 2. 抽取条件与前置历史

ExecuComp四份SQL都是各表全库公司、所列全部可选字段：anncomp仅限制 `year BETWEEN 1992 AND 2023`，其余三表仅限制 `year BETWEEN 2006 AND 2023`。**下载时没有CEO、行业、国家、当前指数成员或仅active的筛选**；CEO与行业选择发生在后续构建。

Compustat原SQL为 `comp_na_daily_all.funda`，左接 `company` 的当前 `sic` 作身份字段；查询日期 `datadate BETWEEN '2003-01-01' AND '2024-06-30'`，并限制 `consol='C'`、`indfmt='INDL'`、`datafmt='STD'`、`curcd='USD'`、`costat IN ('A','I')`。实际行业筛选使用历史 `sich`，没有使用这个左接的当前 `sic`。精确条件为SICH非缺失、100≤SICH≤9999，且不在4900–4999或6000–6999；行业dummy使用`floor(SICH/100)`。未加 `fic='USA'`、S&P指数或公司规模限制。

POPSRC补充表为 `comp_na_daily_all.funda WHERE 1=1` 的9个原始键/状态字段，没有日期或人口限制。构建按六键 `gvkey, datadate, indfmt, consol, datafmt, curcd` 一对一合并；补充表六键不得重复，原财务200,950行必须全部找到popsrc，否则程序停止；然后筛 `popsrc='D'`。本次200,950行全部匹配到D。D、USD或INDL都不等于美国注册，不能据此声称 `fic='USA'`。当前2006–2023的原始B输入13,828行中，原fic字段为USA的13,745行、非USA共83行（IRL39、GBR25、CHE9、ISR5、BMU2、CYM2、IND1）；只是对所保存fic字段的实际统计，不独立认证历史注册地。

前置历史保留目的：2003起财务用于过去三财政年的股息率及前一年资产；月度从2000-12起支持60个月收益/61个价格；日度从2005起支持255个前置市场日；2024上半年缓冲覆盖Compustat fyear2023但实际财年结束日在2024年上半年的公司。因此窗口按**财政年 `fyear`**，不等于把日历日期一刀切在2023-12-31。没有利用期末以后的收益或利率填充前置窗口。

证据：原SQL及 scripts/build_regression_data.py:43–83 (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/scripts/build_regression_data.py:43)、`market_inputs.py:93–126`、`:130–177`；冻结裁定在 build_config.json (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/build_config.json)。

### 3. 公司年度与CEO身份选择

1. 财务表popsrc合并后，只要 `gvkey+fyear` 有多条记录，**整组排除**，不挑最后日期、不按值优先。共22个原财务行被这种歧义标记；不将22行误说成22家公司。歧义行保留 audits/ambiguous_funda_fiscal_years.csv (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/audits/ambiguous_funda_fiscal_years.csv)。fyear缺失也不进入唯一财务面板。
2. anncomp筛 `ceoann == 'CEO'` 且 `year`在2006–2023，重命名year为fyear，再按 `gvkey+fyear` 连接财务。**没有加PCEO条件**，也不采用A公式。该年度CEOANN表示all or most of year，与当前CEO的PCEO不是同一概念。
3. 在有财年末日期的组，候选须 `becameceo <= datadate`（如已知）且 `leftofc > datadate`（如已知）。开始日在财年末当日可以入选，离任日在财年末当日则不入选。缺任期日期不会自动证实任期；缺becameceo可暂入候选，但后续tenure缺失会使控制变量完整性不通过。
4. 只有该公司年度恰好一个财年末候选才选中；仍有多候选/零候选不按薪酬或名字任取。没有财务日期时，唯一年度CEO暂留作损耗审计，最终被flag_funda排除。只保留 `selected_ceo` 后assert `gvkey+fyear` 唯一。
5. `event_id = 六位GVKEY + ':' + fyear`；`valuation_id`再加execid。市场数据按event_id一对一，期权按valuation_id一对一，避免公司年度变量与错误CEO组合。`co_per_rol+fyear`的估值输入也assert唯一。

实测年度CEO原始行38,591，年度CEO唯一公司年度38,413；最终选中35,151个公司年度，其中34,767有无歧义财务。任期冲突原始行标记为：开始晚于FYE1,147、离任不晚于FYE2,147；两者可能重叠，不能相加当互斥损失。审计为 audits/ceo_selection_audit.parquet (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/audits/ceo_selection_audit.parquet)、`prepare_summary.json`、reports/ceo_selection_counts.csv (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/reports/ceo_selection_counts.csv)。严格FYE选择是研究者明确裁定，尚未证实就是作者当年CEO规则。

代码：scripts/build_regression_data.py:53–57 (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/scripts/build_regression_data.py:53)、`:84–107`、`:151–156`。

### 4. CCM、证券类别、日期及市场输入

当前CCM来自 `crsp_a_ccm.ccmxpf_lnkhist`，SQL只限制linkdt在1946-01-01至2026-01-30，不在原始查询中预筛linktype/linkprim。构建时才筛 `linktype IN ('LC','LU')`、`linkprim IN ('P','C')` 且lpermno>0。财年末匹配为 `linkdt <= datadate <= linkenddt`，end为原E哨兵或缺失视为open；缺linkdt不当无界开始。每个event有效链接如指向多个不同PERMNO则拒绝，不任取；多个链接行只要是同一PERMNO可去重保留一个。本次selected主面板有1,697个event找不到有效链接、0个多PERMNO冲突；准备33,454条市场请求，包含不合格行业等仍需后续审计的公司，不等于最终样本。

每个请求用**FYE时选中的同一PERMNO**查前置CRSP历史，不用ticker拼接不同证券。最后截至FYE的源记录日期 `last_trade_date` 须不早于全市场最后一个有效市场日，且不晚于FYE；然后要求该源记录 `SHRCD IN (10,11)`、`EXCHCD IN (1,2,3)`。这识别的是美国主要交易所普通股上市口径。代码中的 `last_trade_date` 是最近源记录日期，不能无条件解读成每条记录都有经济收益。

全市场日历要求当天全源至少一条有限RETX且>=−1，合法0收益保留。18个全源均无经济RETX的纯事件日期被排除，剩4,905个市场日。日度个股RETX非数值、非有限或<−1置缺失，不把SAS缺失码当收益。日度同一permno/date，月度同一permno/month，完全相同值的重复记录可以折叠；若同键有冲突值，程序报错停止，不随意挑值。

月度要求财年末所在月之前的61个连续月价格，每个为abs(PRC)/CFACPR且PRC非零、CFACPR>0；由60个连续log价格变化算样本标准差×sqrt(12)。缺月不以更早记录补足。日度要求FYE严格之前的255个全市场交易日，个股每一天RETX都有效；不足255天或有缺失则retvol255缺失，不向前再找更多有效收益补齐。日度波动是样本std×100，不年化。BSM即期股价仍用Compustat未复权PRCC_F，与未复权EXPRIC保持同一报价基准；月度复权价格只用于sigma估计。

无风险率按每个财年末用 `merge_asof(direction='backward')` 取得当日或之前最近非缺DTB3，绝不取未来值。rf_gap_days留作审计，代码没有另设最大允许间隔；转换r为log1p(rate/100)，并未把原DTB3 discount-basis利率另转换成到期匹配的零息利率。

代码：`build_regression_data.py:108–133`、`:200–206`；`market_inputs.py:40–65`、`:81–90`、`:93–177`。证据：audits/ccm_valid_link_candidates.parquet (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/audits/ccm_valid_link_candidates.parquet)、audits/market/market_build_summary.json (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/audits/market/market_build_summary.json)、`excluded_event_only_dates.csv`、`incomplete_market_windows.csv`及每行市场窗口字段。

### 5. 完整案例、缺失、期权披露与样本继承

构建只对XRD缺失补0并保留事前missing indicator；salary/bonus、养老金/递延总额、book equity或税项等必需值不自动填0。safe_ratio要求分子/分母有限，并按定义要求分母非零或严格正；非有限分析值不入完整样本。实际9列Replication仍控制实际R&D与missing dummy。

`flag_base_eligible`须财务、行业、资产/市值、唯一CCM、美国普通股上市5个flag同时通过。历史 `sich` 须在100–9999，排除公用事业4900–4999与金融6000–6999；缺失/无效SIC不入样。随后要求所有controls与payer/sic2/fyear有限；cash_m与inside_debt_m有限、inside debt>=0；portfolio_complete通过；最后按B组合指标完整性。零内部债务可留普通列；(9)只留严格正relative leverage后取自然对数，不以log1p替代。没有另加年龄上下限或正book-equity门槛；控制变量是否有效依其实际公式及finite判定，负book equity产生的有限M/B可保留。

`portfolio_complete`在期权模块中按正数量每个tranche身份/award键、价格/期限等输入、非负数量、全组合有效以及年度已披露“未行权但可行权/未行权且尚不可行权”两类数量对账决定。容差为0.01千股（10份期权），不是0.01份；unearned另计组合，不机械加入annual unexercisable对账。类别不适用缺值可按0求和但留缺失flag；年度总额/关键字段缺失不能一律当0。无明细只在年度两类数量明确为0时才可认定零期权，不把有正年度数量却缺明细当0。养老金/递延detail只辅助核对，不用于补齐缺失年度总额。具体公式与tranche验证应结合主文变量审计段落。

**重要：当前无DVR回归仍继承原先构建的B分析样本。** `build_regression_data.py:215–218`定义 `sample_b`时，仍要求equity、Vega、DVR、relative leverage、high-relative-leverage全部有限，并要求equity>0、Vega>0。用户后来去掉DVR只是删除回归解释变量，没有放宽样本资格、重新纳入零Vega或未定义DVR者。2013–2023也是从这份已筛过的B extended输入13,828行再截窗口。因此不能声称“当前样本仅按当前无DVR解释变量的非缺失重新确定”。这是保留同样本比较的历史继承条件，应在验证或未来变更样本时明确。

没有按连续变量尾部分位winsorize、trim或额外z标准化；这不等于没有前述资格筛选或后续pure-group剔除。变量定义本身的ln、比率、百分点和Size百分位仍照公式构建，MLE另有纯数值可逆尺度而不改变统计模型。没有按结果显著性删样本，也没有epsilon或Vega下限。作者写了full disclosure，但未恢复可执行规则/样本ID；当前portfolio_complete是公开研究者实现，不等于认证作者规则。

### 6. 累计筛选人数：三窗口原B输入

下表每列都**按相同顺序累计应用**flag，不能与各flag单独失败人数相加。前两列来自reports/sample_attrition.csv (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/reports/sample_attrition.csv)的B记录；2013–2023列由本次只读`panel_master_audit.parquet`按同一代码顺序、仅筛fyear2013..2023重新计数。35,151主面板是已选择CEO的公司年度，而不是原全部ExecuComp行。

| 累计阶段 | 2006–2011 | 2006–2023 | 2013–2023 |
|---|---:|---:|---:|
| 已选年度CEO的公司年度 | 12,386 | 35,151 | 20,707 |
| 财务存在且无年度歧义flag_funda | 12,193 | 34,767 | 20,549 |
| 历史SIC有效、非金融/公用事业 | 9,292 | 25,751 | 14,942 |
| 资产与市场权益严格正 | 9,046 | 25,165 | 14,664 |
| 唯一有效CCM PERMNO | 8,842 | 24,788 | 14,517 |
| 当前美国主要交易所普通股 | 8,607 | 23,809 | 13,822 |
| payer与全部controls有限 | 7,672 | 21,456 | 12,565 |
| cash/debt完整且debt非负 | 7,436 | 21,220 | 12,565 |
| portfolio_complete | 6,591 | 18,619 | 10,913 |
| B所有组合指标有限、equity/Vega正 | 5,826 | 13,828 | 7,086 |

这是“回归输入N”，还不是Logit实际估计N。源构建B log输入分别3,495、7,903、3,889；当前9模型在各自窗口内迭代剔除pure SIC2/year组后，普通(8)/(10)实际N分别5,736、13,716、7,035；(9)分别3,416、7,784、3,782。pure组规则及每个模型精确ID应在主文估计段落核对，不能把输入N误写成Excel N。

原始2006–2023基础资格23,809行的非缺失诊断为：age缺44、ln_tenure缺331、capx_at_pct缺15、asset_growth缺21、mb与profitability_m各缺1,418、re_at缺5、retvol255缺602、inside_debt_m缺269；payer、rd_at_pct、rd_missing、size_pct及cash_m缺0。它们会重叠，不能相加；现金/debt累计损失236也包含inside debt非负要求及前面控制筛选。证据 reports/required_variable_missingness.csv (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/reports/required_variable_missingness.csv)。

主面板与审计文件：data/processed/panel_master_audit.parquet (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/data/processed/panel_master_audit.parquet)有原选中35,151公司年度及所有flag；audits/sample_selection_audit.parquet (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/audits/sample_selection_audit.parquet)逐行保留first_exclusion/portfolio_reason、market失败原因。构建审计的 `first_exclusion_b` 是按固定顺序的第一个失败原因，不等于每行只有一个问题。原构建记录时间为build_manifest.json (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/build_manifest.json)的2026-10-24T20:23:33.899588+00:00，其“regressions_run=false”仅表示数据构建阶段，不代表当前Excel未估计。

### 7. 可验证而仍未恢复的部分

- 论文原期普通列N2,117、log列N834，当前原期输入/实际N均更大，作者最终IDs与full-disclosure实际规则未取得；不能靠当前数值接近就称精确复现。
- 当前CEOANN+严格FYE、B股票/期权规则、缺失与完整披露实现是有证据和代码的公开选择，但部分并非已获作者确认。原文的股票Delta/Vega与附录单位矛盾应在主文公式段另行指出。
- 当前数据库是2026-10-24下载快照，不是作者2015时点的历史数据版本；历史重述、供应商更新可能影响复现。
- 去DVR后仍继承正Vega/可计算DVR的B样本，这是当前版本确定事实；如未来想最大化无DVR模型的完整案例样本，须另建并明确标记新样本，不能偷偷改变本表N。
- `data/raw/linking_20261025`里的CIQ/BoardEx官方桥及OOF/full分数只影响其他score表，不是本页9列Replication的数据来源或样本覆盖限制。


<a id="variables"></a>

## 3. 变量、期权估值和历史窗口的精确公式


本节核对的是截至 2026-10-25 当前工作簿 `2 Replication` 三个窗口、各第 (8)–(10) 列实际使用的变量。代码和路径均相对于 `REP=replications/caliskan_doukas_2015`。所有回归变量均按原财政年度 `fyear=t` 匹配；除了下列明确的历史输入和资产增长滞后，没有把 CEO 薪酬、内部债务或财务控制统一滞后一年。

当前九个模型均使用 B（`standard_finance`）公式，均不含 `delta_vega` 回归项，也不含任何 Ridge/XGBoost score。`rd_at_pct` 与 `rd_missing` 都仍在这九个模型中；用户要求移除两者的是另外的 `3 No actual RD` 页，不适用于 Replication。

主要代码证据：`scripts/build_regression_data.py:58–83,102–107,138–149,200–218`，`scripts/option_portfolios.py:25–60,189–203`，scripts/market_inputs.py:93–178 (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/scripts/market_inputs.py:93)。声明与代码一致性见 build_config.json:41–58 (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/build_config.json:41)、reports/variable_dictionary.csv:15–45 (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/reports/variable_dictionary.csv:15)。

#### A. 因变量和共同控制变量

这里的“百分比点/pp”指原比例乘以 100；“ratio/decimal”不乘 100。金额除明确的股票价格、行权价与内部估值美元外，Compustat 财务变量使用原始百万美元量纲。

| 回归字段 | 原始来源字段及实际计算 | Excel 单位/含义 | 缺失、分母和边界规则 | 代码证据 |
|---|---|---|---|---|
| `payer` | Compustat `DVPSX_F` 非缺失时，`1(DVPSX_F>0)` | 0/1；财政年 ex-date 股息每股是否为正 | `DVPSX_F` 缺失时结果为缺失，不补 0；实现中非正但非缺失值记 0。没有使用 `DVPSX_C`、`DVC`、支付率、回购或净支付来定义本因变量 | `build_regression_data.py:71–72,207` |
| `age` | ExecuComp 年度 `AGE` | 年 | 取年度年龄，非当前年龄 header 字段 `PAGE`；代码只要求进入完整样本时为有限值，未新增年龄区间截断 | `build_regression_data.py:84–87,138,212`；字典第 24 行 |
| `ln_tenure` | `tenure_years = 1+floor((datadate−becameceo).days/365.25)`；再取自然对数 | `ln(年)` | 只有 `tenure_years>0` 才取 log；不是 `ln(1+年差)` 的连续时长，也不是日历年差。新任不足一年通常记 tenure=1、log=0。`becameceo` 缺失会使 tenure/log 缺失，最终完整样本排除。日期字段的原始 header/历史任职限制仍存在 | `build_regression_data.py:88,92–107` |
| `rd_at_pct` | `100 × XRD.fillna(0) / AT` | R&D/资产的百分点 | 必须 `AT>0` 且有限；先生成 missing indicator，再仅对 `XRD` 缺失补 0。未把负的已报告 XRD 截成 0，也未缩尾。本页九列同时保留 missing indicator | `build_regression_data.py:66–67,138` |
| `rd_missing` | 补 0 前的 `1(XRD is missing)` | 0/1 | 与实际报告 `XRD=0` 区分；报告为 0 时 indicator=0，原始缺失补为 0 时 indicator=1 | `build_regression_data.py:66–67` |
| `capx_at_pct` | `100 × CAPX / AT` | CAPEX/资产的百分点 | `AT>0` 且分子分母有限；缺失 CAPX 不补 0，无负值截断/缩尾 | `build_regression_data.py:37–39,68` |
| `asset_growth` | `(AT_t−AT_{t−1})/AT_{t−1}` | decimal ratio，不是百分点 | 通过同一 `gvkey`、**严格相邻的 `fyear=t−1`** 找资产，不能以更早最近非缺失年替代；要求 lagged `AT>0`、数值有限且 lagged `datadate<` 当前 `datadate`。当前 AT 也因基样本要求大于 0。未乘 100 | `build_regression_data.py:78–81,105` |
| `mb` | `market_equity_m/book_equity_m`，详细回退链见下一小节 | ratio | 分母只要求非零且有限，并未统一要求正 book equity。**有限的负 book equity/负 MB 保留**；零 book equity 记缺失。缺失组成项不擅自补 0 | `build_regression_data.py:37–39,58–63` |
| `profitability_m` | `IB−DVP+TXDITC` | 百万美元；不是 ROA、利润率，也未除以 AT | 沿用论文印刷的 mnemonic `TXDITC`；缺失 IB、DVP 或 TXDITC 不补 0。负的有限结果可保留。`IB−DVP+TXDI` 只输出为诊断字段 `profitability_txdi_m`，未用于当前九列 | `build_regression_data.py:58,64–65,138` |
| `size_pct` | 同财政年参考总体中市场权益严格小于本公司的百分比：`100×(rank_min(ME)−1)/N_t` | 0–100 尺度的 percentile；不是 log assets 或 log sales | 参考总体和 ties/分母规则见下文；使用每年 base-eligible、完整案例筛选之前的公司。没有在各模型、正债务子样本、2013–2023 子窗或 score 匹配样本内重排 | `build_regression_data.py:143–144,200–206` |
| `re_at` | `RE/AT` | decimal ratio，不乘 100 | `AT>0` 且分子分母有限；RE 可为负，不补 0、不截断 | `build_regression_data.py:37–39,69` |
| `retvol255` | 严格在 `datadate` 之前的 255 个真实市场日期上，`100×sample_sd(RETX,ddof=1)` | 日收益波动率百分点 | 要求该证券在固定的全部 255 日期上都存在有效 RETX；不以更早有效收益补足，不年化，未用 market-model residual、36-month idiosyncratic risk 或月度 sigma60 替代 | `market_inputs.py:130–178` |

`safe_ratio(a,b,positive=False)` 的共同操作是：分子、分母必须有限；`positive=False` 时分母不能等于 0，`positive=True` 时分母必须严格大于 0，其他情况输出缺失。最终样本又要求所需变量全部有限，因此除法产生非有限结果也不会入样本。这里没有普遍地把缺失项、负数或离群点补零/截尾。证据：`build_regression_data.py:37–39,158–159,212–218`；`build_config.json:45,50`。

#### B. Market-to-book 的精确回退链

下式使用同一公司/财政年 Compustat 值；`first_nonmissing` 是逐行按顺序选择第一个非缺失值：

```text
market_equity_m = PRCC_F × CSHO
shareholder_equity_m = first_nonmissing(SEQ, CEQ + PSTK, AT − LT)
preferred_equity_m   = first_nonmissing(PSTKL, PSTKRV, PSTK)
book_equity_m       = shareholder_equity_m − preferred_equity_m + TXDITC
mb                  = market_equity_m / book_equity_m
```

- 优先顺序是 **PSTKL → PSTKRV → PSTK**，不是先 PSTKRV。
- `CEQ+PSTK` 任一缺失会使该候选缺失，然后才尝试 `AT−LT`；不会把其中缺失项当 0。
- `preferred_equity_m` 三项都缺失，或 `TXDITC` 缺失，book equity 保持缺失。
- `PRCC_F` 是美元/股、`CSHO` 为百万股，所以市场权益为百万美元，与 book equity 量纲一致。
- 基样本另要求 `AT>0` 且市场权益 `ME>0`；并未因此要求 book equity>0。

证据：`build_regression_data.py:58–70,103–105`；reports/variable_dictionary.csv:30–31 (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/reports/variable_dictionary.csv:30)。论文 Appendix A 的 shareholder/preferred/book-equity 算法与印刷字段见 `audits/sample_gap_20261024/paper_fulltext.txt:1290,1302–1310,1323–1325`。

#### C. Size percentile 的参考总体不能换掉

构建程序先在所有已选定年度 CEO 的 firm-year 中定义：

```text
flag_base_eligible =
  flag_funda
  & flag_industry
  & flag_positive_assets_me
  & flag_ccm_unique
  & flag_common_us_listing
```

然后仅在 `flag_base_eligible=True` 的公司中，按每个 `fyear` 计算：

\[
Size_{it}=100\frac{\#\{j\in\mathcal R_t: ME_{jt}<ME_{it}\}}{N_t},
\qquad N_t=|\mathcal R_t|.
\]

代码以 `rank(method='min')−1` 实现严格小于计数，因此并列 ME 的公司有相同分位；分母是 **N，而不是 N−1**。最小值为 0，样本有限时最大值通常小于 100。`size_ref_n` 记录该年 N。参考总体排除了基本财务/行业/正资产正市值/CCM/CRSP挂牌不合格者，但在期权完整性、全部控制完整案例等最终删样本条件之前，因此不等于最终 5,736、13,716 或 7,035 个回归行。

此参考总体并非所有 CRSP 上市公司、仅 NYSE 公司或最终回归样本。论文 Appendix A 只写“时点 t 市场权益更小的公司占比”，未在该句给出可恢复的参考公司全集和 ties 分母实现；本项目的参考总体是明确公开的研究者实现，不能声称作者的总体已被认证相同。

证据：`build_regression_data.py:143–144,200–206`；build_config.json:46 (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/build_config.json:46)；字典第 32、43 行；论文提取文本第 1325 行。2013–2023 是冻结输入的年份子集，未在新子窗口重算 Size。

#### D. CEO 财富/薪酬变量与相对杠杆

内部期权估值统一先转为实际美元和实际股数。以下 `SALARY`、`BONUS`、`DEFER_BALANCE_TOT`、`PENSION_VALUE_TOT` 原数值按千美元，ExecuComp 持股/期权数量按千股转换，`PRCC_F` 和 `EXPRIC` 为实际美元/股。代码单位说明见 `option_portfolios.py:1–6,119–125,189–203,221–223`。

令 `Q_i = 1000×SHROWN_EXCL_OPTS_i`，`S_i=PRCC_F_i`，`q_ij` 是第 j 笔期权的实际数量，`C_ij` 是每份期权的 BSM 美元价值：

\[
\begin{aligned}
Cash_{it}\;(\$m)&=(SALARY+BONUS)/1000,\\
InsideDebt_{it}\;(\$m)&=(DEFER\_BALANCE\_TOT+PENSION\_VALUE\_TOT)/1000,\\
Equity^{B}_{it}\;(\$m)&=\left[Q_i S_i+\sum_j q_{ij}C_{ij}\right]/10^6,\\
Vega^{B}_{it}\;(\$k/1pp)&=\left[\sum_jq_{ij}\nu_{ij}\right]/1000.
\end{aligned}
\]

- `cash_m` 仅 salary+bonus，未额外加 LTIP、non-equity incentive、other compensation 等。两项任一缺失不补 0。
- `inside_debt_m` 严格使用 **anncomp 年度总额**；养老金/递延明细表只核对，不能用明细和或 0 回填年度缺失。最终要求总 inside debt 非负；零 debt 可进入非对数列。
- B 只用 `SHROWN_EXCL_OPTS`，未另外把 `STOCK_UNVEST_NUM` 相加。这里不能未经供应商进一步证明就把该持股字段叫成“只有已归属股票”。字段取负时股数设缺失；S 必须>0。
- B 普通股直接 Vega=0，因此 `vega_k` 仅来自期权；普通股不是人为向 Vega 分母加入 0.01×股数。
- B 的 `equity_m` 不含 inside debt、现金薪酬，包含上述股票和全部合格期权的价值。

相对杠杆使用：

\[
\begin{aligned}
FirmLeverage_{it}&=LT_{it}/(PRCC\_F_{it}\,CSHO_{it}),\\
CEOLeverage_{it}&=InsideDebt_{it}/Equity^{B}_{it},\\
RelLev_{it}&=CEOLeverage_{it}/FirmLeverage_{it},\\
ln\_rellev_{it}&=\ln(RelLev_{it})\quad\text{仅当 }RelLev_{it}>0,\\
high\_rellev_{it}&=1(RelLev_{it}>1).
\end{aligned}
\]

`LT` 是 total liabilities，不是 `DLC+DLTT`。CEO equity 和 firm leverage 分母必须正，inside debt 非负。零 inside debt 可产生 RelLev=0、high=0，但 `ln_rellev` 缺失，故第 (9) 列排除零相对杠杆。阈值是严格 **>1**，等于 1 时 high=0；含义是 CEO 的 debt/equity 超过公司的 debt/market-equity，而不是 `RelLev>FirmLeverage`。后者作为另一个 `high_appendix` 诊断字段保留，没有进入这九列。证据：`build_regression_data.py:70,146–149,208–218`；`option_portfolios.py:189–210`；build_config.json:47 (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/build_config.json:47)。

#### E. 每笔期权的输入、BSM/Merton 公式与汇总

##### E1. 输入规则

| 记号 | 当前实际输入 | 时间与缺失规则 | 代码证据 |
|---|---|---|---|
| S | Compustat `PRCC_F` | 财年末实际美元/股；不把用于历史波动率的 CRSP 复权价格作为这里的 S | `build_regression_data.py:130` |
| X | ExecuComp 逐笔 `EXPRIC` | 实际美元/股，和未复权 S 使用同一股数/价格基准；没有全表重新拆股或改用平均行权价 | `option_portfolios.py:105–118,133–134` |
| T | `(EXDATE−datadate).days/365.25` | 实际剩余日数转年；不是固定 10 年、7.5 年，也没有额外 0.7 乘数；过期 T<0 无效 | `option_portfolios.py:116,130,146` |
| σ | `sigma60` | 61 个连续月价格构成的 60 个对数变化，样本 SD×√12；见下一节 | `market_inputs.py:93–127` |
| d | `ln(1 + mean(dvy_{t−1},dvy_{t−2},dvy_{t−3}))`；`dvy=DVPSX_F/PRCC_F` | 3 个严格相邻财政年都必须有非负股息、正股价形成的比率，且每个历史 `datadate` 严格小于当前。取“比率算术均值后 log1p”，不是均值 log；不含当年股息、不用未来值、缺历史不补 0 | `build_regression_data.py:71,73–83` |
| r | `ln(1+DTB3/100)` | 按财年末向后取最近一个非缺失 FRED 3-month T-bill 报价（on/before FYE）；节假日不前取未来。保存 `rf_date/rf_gap_days`，代码没有另外规定最大 gap 天数 | `build_regression_data.py:123–130` |
| q | `1000×(OPTS_UNEX_EXER + OPTS_UNEX_UNEXER + OPTS_UNEX_UNEARN)` | 逐笔正数量期权，数量类别空白在明细内部按 0 合计；先留 missing/negative 审计 flag。总量和年度 disclosed totals 的对账另行检查 | `option_portfolios.py:16–17,119–125,171–176` |

同一 CEO-year 的所有 tranche 共用该年 S、σ、r、d，X/T/q 则逐笔不同。没有为不同到期日构造不同期限的利率曲线，也没有在该程序中实现美式期权提前行权、归属条件、离职或不可交易性折价。这里是以每笔完整披露数据估计的 BSM/Merton 近似。

##### E2. 正常参数区域

对每份期权，在 `S>0,X>0,T>0,σ>0` 且输入有限时：

\[
d_1=\frac{\ln(S/X)+(r-d+\sigma^2/2)T}{\sigma\sqrt T},\qquad d_2=d_1-\sigma\sqrt T,
\]

\[
\begin{aligned}
C&=S e^{-dT}\Phi(d_1)-X e^{-rT}\Phi(d_2),\\
\Delta^{1\%}_{option}&=0.01 S e^{-dT}\Phi(d_1),\\
\nu^{1pp}_{option}&=0.01 S e^{-dT}\phi(d_1)\sqrt T.
\end{aligned}
\]

上式 Δ 是纯价格偏导乘以 `S×0.01` 后的**股价上升 1% 的一阶美元财富敏感度**；Vega 是波动率绝对增加 0.01（1 个百分点）的敏感度，不是波动率相对增加 1%。每份的 value/delta/vega 乘该 tranche 实际数量 q，再跨所有有效 tranche 求和。证据：`option_portfolios.py:25–60,130–138,151–188`。

虽然当前九列已经去掉 `delta_vega`，用于构建审计的 B 总 Delta 仍为：

\[
\Delta^{B}_{CEO}\;(\$k)=\left[0.01S Q_i+\sum_j q_{ij}\Delta^{1\%}_{option,j}\right]/1000,
\qquad DVR=\Delta^{B}_{CEO}/Vega^{B}_{CEO}\quad(Vega^{B}_{CEO}>0).
\]

`delta_vega` 没有 epsilon、分母下限、log、winsor 或零替代；零 Vega 得缺失。它不是当前回归项，但其**原始可计算资格仍影响冻结样本**，详见 G。

##### E3. 解析极限与无效输入

- 总体有效条件是 `isfinite(S+X+T+r+d+sigma)` 且 `S>0,X>=0,T>=0,sigma>=0`。
- `T=0`：价值为 `max(S−X,0)`；Delta 为 `0.01S×{1,0,0.5}`，分别对应 S>X、S<X、S=X；Vega=0。
- `T>0,X=0`：价值 `S exp(−dT)`，Delta 为其 0.01 倍，Vega=0。
- `T>0,X>0,σ=0`：使用确定性 forward 极限，价值 `max(Sexp(−dT)−Xexp(−rT),0)`；Delta 按 forward 价内/价外决定，在 `np.isclose(ds,dx,rtol=1e−12,atol=1e−12)` 的 ATM 处取半 Delta；ATM 的单边 Vega=`ds×√T×0.01/√(2π)`，非 ATM 为 0。
- `T<0`、X<0、σ<0、S≤0 或无效/缺失参数均无效。没有将缺失行权价或到期日改成 0。
- 有效区域内最终 value=`max(value,0)`，只消除本应非负看涨期权价值的数值舍入负数；这不是对 CEO 财富或财务变量做尾部缩尾。

证据：`option_portfolios.py:25–60`。原始代码未在这些分支中将负值/零值一概删除；后续能否入样本还取决于组合完整性和 B Vega>0 等条件。

#### F. 市场历史窗口的严格定义

##### F1. `sigma60`：年化的月度价格波动率

1. 历史月价格由 CRSP `abs(PRC)/CFACPR` 构造，要求 PRC、CFACPR 有限，PRC≠0、CFACPR>0。负 PRC 取绝对值，不按负价格删除。
2. 对当前 `datadate`，终点是**财年末所在日历月的前一个月**，不是财年末月。取终点向前共 61 个连续 calendar-month 价格。
3. 对其计算 60 个相邻 `ln(P_m/P_{m−1})`。必须 60 个变化全部有效；缺任一月不以更早月份补齐。
4. `sigma60 = sd(log changes, ddof=1)×sqrt(12)`，为年化 decimal SD，不乘 100。每月 `(permno,month)` 键精确重复可去重；同键冲突报错，不任意取第一条。

证据：`market_inputs.py:81–127`。`sigma60` 仅供期权估值，**不是** 回归中的 `retvol255`。

##### F2. `retvol255`：不年化的日收益 SD

1. 全市场 calendar 由所有下载 CRSP 日度行中，“当天至少有一条有限且 RETX≥−1（包括 0）”的日期构造，排除只有无经济收益事件行的日期；不是从某一公司的有效收益日期单独推断 calendar。
2. 对当前 `datadate`，取 calendar 中严格小于该日的最后 255 个日期。当 FYE 本身是市场日，该日收益也不进入窗口。
3. 按该 PERMNO 在这固定 255 日期 reindex，非数值代码、非有限 RETX、RETX<−1 保持缺失。只有 255 个日期且 255 收益全部有效才计算。
4. `retvol255 = 100×sd(RETX,ddof=1)`。不乘 √255、√252 或 √12；不用 total-return RET 替代 RETX；不采用市场模型残差。
5. 同 `(permno,date)` 精确重复可去重，收益/SHRCD/EXCHCD冲突报错。证券挂牌元数据从最后 `date<=datadate` 的 CRSP **观测行**取；变量名 `last_trade_date` 并不证明该日真实发生交易。挂牌资格另检查该观测日不早于 FYE 前最后一个真实市场日。

证据：`market_inputs.py:26,40–64,81–90,130–178,299–321`，`build_regression_data.py:200–202`。月度和日度窗口均留有准确起止月份/日期、有效数量及 failure 字段，可直接核对 audits/market/monthly_features.parquet (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/audits/market/monthly_features.parquet)、`incomplete_market_windows.csv`、`corrected_market_calendar.csv` 等。

#### G. 缺失、离群值和冻结资格：删掉 DVR 不代表放宽原样本

当前复现保留了原先构建的年度 B 完整样本，再按各时间窗口/正相对杠杆/pure-group 规则取样。原构建资格不是为每列单独找最大可用样本，而是共同要求：

```text
flag_controls_complete = finite(payer, sic2, fyear, 全11个控制变量)
flag_cash_debt_complete = finite(cash_m, inside_debt_m) & inside_debt_m>=0
flag_measures_b = finite(equity_b_m, vega_b_k, dv_ratio_b, rellev_b, high_rellev_b)
                  & equity_b_m>0 & vega_b_k>0
sample_b = flag_base_eligible & flag_controls_complete
           & flag_cash_debt_complete & portfolio_complete & flag_measures_b
sample_log_b = sample_b & finite(ln_rellev_b)
```

因此：

- 当前 (8)/(10) 虽不回归 DVR，仍继承 `DVR` 有限、Vega>0、relative leverage 可计算等原资格。没有放回零期权/零 Vega 或 LT≤0 造成 relative leverage 无效的公司年。
- 所有 (8)–(10) 都继承共同控制完整性；并非 (8) 只需金额 debt 就允许无法计算 relative leverage 的行进入。
- 零 inside debt 可以进入 (8)/(10)，但不能进入 (9) 的自然对数相对杠杆样本。
- 期权组合必须所有正数量 tranche 有效，年度可行使/不可行使数量必须披露且与明细在 **0.01 千股（10股）**内对账；明细中 unearned 类独立纳入组合。`any_award_category_missing` 只留审计标记，不作为一刀切删除条件。缺到期/行权价不补 0，年度养老金/递延缺失不以明细或 0 补回。
- 完整组合的零期权情况可先被识别为 `zero_options_explicit`，但因 B Vega=0，不满足最终 B 样本资格。
- 无 winsorization/trim、无统一 top/bottom percentile 删除、无回归前 z 标准化、无按显著性选择阈值。R&D 缺失补 0+dummy、数量类别的结构性空白合计、有效期权价值的数值非负修正是各自明示的局部规则，不是通用缺失替代政策。

证据：`build_regression_data.py:138–149,158–159,212–247`；`option_portfolios.py:119–125,139–188,202–223`；build_config.json:45–51 (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/build_config.json:45)。回归引擎为了数值稳定进行可逆变量缩放，是估计层的重参数化；最终系数回原单位，不能将其误写成这里的经济变量已标准化。

##### G1. `portfolio_complete` 的完整条件，以及哪些 A/B 共享字段会筛样本

`STOCK_UNVEST_NUM` **不是 B 的数值有效性门槛**。它必须作为输入数据集的一列存在（缺整列会报 schema 错误），但 `portfolio_complete` 不要求该列每行非缺失/非负。代码先将它转 numeric，随后 `unvested_shares=1000×STOCK_UNVEST_NUM`、负数设缺失，仅供 A 的 `shares_a` 使用；B 的 equity/Delta 只引用 `common_shares`，B Vega 只引用期权。因此不能写成“为了共用 A/B，B 仍要求非缺失未归属股数”。证据：`option_portfolios.py:89–103,189–201`；`build_regression_data.py:214–218`。

相反，`SHROWN_EXCL_OPTS` 是 B 必需的持股输入，负值/缺失使 `common_shares` 缺失，进而 B equity 缺失并由 `flag_measures_b` 剔除；该失败未必让 `portfolio_complete` 变 false，因为后者本身只审计**期权组合**。薪酬和年度内部债务缺失也由后续 `flag_cash_debt_complete` 处理，不应与期权完整性混成一个旗标。

以下是源码的完整逻辑（`option_portfolios.py:171–176`）：

```text
annual_counts_disclosed =
    OPT_UNEX_EXER_NUM.notna() & OPT_UNEX_UNEXER_NUM.notna()
    & OPT_UNEX_EXER_NUM>=0 & OPT_UNEX_UNEXER_NUM>=0

annual_counts_reconciled = annual_counts_disclosed
    & abs(sum_detailed_exer_k − OPT_UNEX_EXER_NUM)<=0.01
    & abs(sum_detailed_unexer_k − OPT_UNEX_UNEXER_NUM)<=0.01

portfolio_complete = annual_counts_reconciled
    & (n_valid_tranches == n_option_tranches)
    & ~any_award_identity_mismatch
    & ~any_award_identity_missing
    & ~any_missing_award_number
    & ~any_negative_award_quantity
    & ~any_duplicate_award_key
```

具体边界：

- 两项年度 count 都必须披露，允许等于 **0**；没有“至少一项严格正数”或最小正期权数量阈值。原始数量单位为千股，容差 `<=0.01` 为含边界的 10 股。年度 count 的 nonnegative/disclosed predicate 本身是非缺失和 `>=0`；最终还要通过数量差的容差比较。
- `is_option_row` 是明细的三类数量中**任意一类>0**；`total_quantity_k` 为三类在该明细行内缺失补 0 的和，再乘 1000。负的任何一类数量被标记，并非只要总数为正就接受。三类都非正/缺失的行不进入 `n_option_tranches`，但仍可能触发原始奖励表的共享 flags。
- 明细的可行使与不可行使两类分别与 anncomp 两项年度数对账；`OPTS_UNEX_UNEARN` 独立加入期权估值和组合总量，**没有再与某个 anncomp 年度 unearned 总额对账**。若年度 exer/unexer 都为 0，但存在有效的正 unearned 明细，不能仅由这两个年度 0 推断整个期权组合为 0。
- `zero_options_explicit` 的精确定义是：`annual_counts_disclosed`、两项年度 count 都为 0、且 `n_option_tranches==0`。仅“两项年度 count 为0”还不够。零组合可以通过上述期权完整性测试，但最终 B 因 Vega=0 仍不进入分析样本。
- `annual_counts_disclosed` 不通过时，不用明细 sum 替代；所有 positive tranche 必须有效，不能删掉一笔无效 tranche 后只估其余部分。`option_value/delta/vega_usd` 只有 `portfolio_complete=True` 才保留（否则整组合量置缺失）。
- `any_award_category_missing` **不在 `portfolio_complete` 中**，也不是最终 sample_b 的单独剔除条件。

共享原始奖励表 flags 的粒度也重要（`option_portfolios.py:105–129,163–176`）：

| flag | 真值条件与粒度 |
|---|---|
| `any_award_identity_mismatch` | 同 `co_per_rol+year` 匹配的原始 award 行中，非缺失 award GVKEY/EXECID 与当前 CEO 输入不一致，任一行为真即整个组合失败；此检查不只局限于 positive-option 行 |
| `any_award_identity_missing` | award GVKEY 或 EXECID 缺失，**且该行是 positive-option 行**，任一行为真即失败 |
| `any_missing_award_number` | 原始 award 的 `OUTAWDNUM` 缺失，任一行为真；不是只看正期权行 |
| `any_duplicate_award_key` | 在原始 award 表上按规范化后的 `co_per_rol+year+OUTAWDNUM` 检查重复，`keep=False` 标记重复组所有行，任一行为真；并非先去重后估值 |
| `any_negative_award_quantity` | 原始 award 任一行、任一期权数量类别<0，任一行为真；并非仅检查正期权行或三类数量的和 |

因此，B 虽然不另外使用 `STOCK_UNVEST_NUM` 估价，仍可能因同一角色/年度**stock-only 原始 award 行的键、身份不一致或负数量 flags**失败；这是共享的奖励表完整性门槛，和“强制未归属股数量有效”是不同机制。B 与 A 共用期权定价输入 S、r、d、σ、期权数量、strike/expiry、身份/键及年度对账；但 A 的 `STOCK_UNVEST_NUM` 数值门槛并未移植到 B。

`valid_tranche` 的完整 predicate 是（第139行）：`isfinite(value+delta+vega)`，数量不为负，无身份不一致、无 award 重复/缺编号、无 positive-row 身份缺失，并且实际数量有限。期权参数 S/X/T/r/d/σ 的有效/解析极限见 E3。

##### G2. 失败原因的优先级不能当成互斥的原始问题

`portfolio_reason` 是 `np.select` **按下列顺序只取第一个失败原因**；一个组合可能同时触发多个原始 flags，不能用 reason 的单一分类推断其他 flags 都没问题（`option_portfolios.py:177–186`）：

1. `annual_option_counts_missing_or_negative`
2. `identity_mismatch`
3. `identity_missing`
4. `missing_award_number`
5. `duplicate_award_key`
6. `negative_award_quantity`
7. `annual_count_mismatch`
8. `invalid_or_missing_tranche_inputs`
9. 无上述失败时为 `complete`。

逐笔的 `invalid_reason` 另有相应优先序（第140–150行）：`identity_mismatch` → `identity_missing` → `missing_award_number` → `duplicate_award_key` → `negative_quantity` → `expired_before_fiscal_end` → `missing_expiry` → `negative_strike` → `missing_or_invalid_valuation_inputs`；无匹配项时为空字符串。它与组合级 reason 不完全同名，例如 tranche 用 `negative_quantity`，组合用 `negative_award_quantity`。

#### H. 与论文描述的差异/未确认事项

1. **Delta/Vega 已被用户移出当前九列。** 论文原 Table4(8)–(10)包含这一项；当前是修改规格，不能称原模型的精确复制。期权估值仍必须做，因为 Vega、equity、relative leverage 依赖它。
2. **普通股 Delta/Vega 记法存在原文内部差异。** 论文正文 §3.2.4 写股票 Delta=股数、Vega=股数×0.01，并以股价 +1 美元叙述；Appendix B 的期权 Delta 又乘 `S/100`（+1%股价）。B 为统一量纲，股票 Delta=`0.01NS`、股票 Vega=0；这是本项目的明确标准金融实现，不能据此确认作者代码采用 B。A 的旧机械实现只作历史诊断，未用于当前九列。
3. **高相对杠杆 dummy 的正文/附录表述不同。** 主实现 `1(RelLev>1)` 对应 CEO leverage 超过 firm leverage；Appendix B 字面 `1(RelLev>firm_leverage)` 另存 `high_appendix`，当前未用。不能把两阈值混为同一变量。
4. **Profitability 的字段和单位须保留限定。** 论文 Appendix A 将所得税递延的文字与 `TXDITC` mnemonic 并列，本实现采用印刷 `TXDITC`，而 `TXDI` 只诊断。原 Table4 行标签为 `$thousand`，当前 Compustat/回归字段明确是 `$million`，未为了追原系数擅自改成千美元，也不能由印刷标签推定作者实际数值尺度已经确认。
5. **资产增长单位不同。** 原表标签为 `%`，当前 `asset_growth` 是 decimal（不乘100）；R&D、CAPEX 是百分点，RE/AT 与 MB 是 ratio，日收益波动率是百分点。不能将所有 ratio 一律当百分点比较系数。
6. **Size 参考总体和 full-disclosure 操作定义未由作者代码认证。** 本项目已公开精确实现，但原作者最终 ID、原始历史数据快照、完整可执行筛选规则未恢复。单位说明、同代码可复现和数值校验通过，均不等于作者样本/实现已被精确复制。

论文本地证据：`audits/sample_gap_20261024/paper_fulltext.txt:302–319,589–616,1287–1387`；构建证据见前述三脚本及 reports/variable_dictionary.csv (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/reports/variable_dictionary.csv)。本节是对现有实现的只读核查，没有新建变量、重估、修改输入或替作者补定未披露规则。


<a id="models"></a>

## 4. 方程、估计、推断、Excel取值与安全复跑


审计日期：2026-10-25，America/New_York。核对者：Codex。本节按实际代码、配置、逐模型JSON、Stata程序及验证产物核查；本次没有重新估计或修改Excel。

本文约定项目根为 `D:/pc_workspace_local/ceo_risk_taking`；`REP` 为其下 `replications/caliskan_doukas_2015`；`RUN` 为 `REP/results/table4_compilation_rep_2013_2023_20261025`。下列相对路径均相对于REP。

### 1. 本节准确覆盖什么

当前Excel主文件是 outputs/01a17125-70eb-72b1-abff-27491f3aec3e/table4_annual_b_tables.xlsx (historical source reference: D:/pc_workspace_local/ceo_risk_taking/outputs/01a17125-70eb-72b1-abff-27491f3aec3e/table4_annual_b_tables.xlsx)。本轮现场主文件SHA256为 `8f3df019e71f2c3d5b8281e51d3fc59936fe0fef5518b45a5f1686843ac1ae40`，大小488,975 bytes；记录的mtime为2026-10-25T21:27:46.330Z。本次整理开始和结束时均为该哈希，本轮没有修改此文件。R18导出的历史冻结工作簿SHA是 `8ca0ad7fa448f9b1622a62d8f351191b286bcf5aca9db072c8b2fb2c44bcceb3`，仍保存在当前ZIP包内；不能将该旧哈希继续当作当前主文件的哈希。这里只解释工作表 **`2 Replication`**：三个财政年度窗口，每个窗口第(8)、(9)、(10)列，共9个Logit模型。

这些都是年度CEO B、无PCEO筛选、无Ridge/XGBoost分数的回归。三个窗口均保留实际R&D/资产和R&D missing dummy。所有9式都按用户修改后的设定**不含Delta/Vega解释变量**，但保留Vega。第(8)列使用内部债务金额，第(9)列使用log CEO相对杠杆，第(10)列使用high-relative-leverage虚拟变量。旧的零Vega/有限DVR等建表资格并未因删除回归中的DVR而放宽，见样本构建章节。

因此，当前表是从原论文Table4(8)–(10)出发、按用户要求修改的规格；不是作者原方程和原始样本的精确复现。`1 Original`是另一个工作表，不应将其印刷统计量或作者样本当成本页当前回归。

#### 1.1 当前另存主文件与R18冻结副本的现场差异

本轮以内存只读方式打开当前主文件与ZIP内的冻结Excel，对`2 Replication!A1:D220`逐格解码比较值/公式/数字格式/字体等样式、行列尺寸和合并。结果如下，证据为audits/replication_documentation_20261025/current_vs_frozen_sheet2.json (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/audits/replication_documentation_20261025/current_vs_frozen_sheet2.json)：

| 类别 | 当前8f3...相对于冻结8ca...的差异 |
|---|---|
| 回归系数、SE、N/G/LL/pseudo-R2等footer、原有变量标签 | 全部相同；本次核对另直接对当前288个系数/SE数字与冻结payload核对，最大数值差0 |
| 额外单元格文字 | `A20`、`A22`从空白变成“方向不一致”，分别位于CEO age和Log CEO tenure下方的SE行左侧 |
| 公式 | 无差异 |
| 数字格式代码 | 144格系数格式的负数段将`-`改写为转义字面量`\-`；解除该负号转义后所有格式代码相同，原有星号后缀未变 |
| 字体属性 | 所比较880格中878格仅font family元数据从空变为2；A20/A22另变为宋体、charset134。其余已比较的字体/填充/边框/对齐/保护属性没有新增差异 |
| 行尺寸 | 所有显式row dimensions相同；工作表默认行高从15变成14 |
| 列尺寸 | A列宽仍38.75；B:D原各18.1299991607666，当前均18.1640625，且以一个B:D列组存储，而不是三个独立列定义 |
| 合并/冻结/打印 | 两者均无合并，冻结窗格均B7；打印选项、页面设置及页边距相同 |

因此当前文件**不只是字节或格式变化**，还包含两条新增文字注记，但没有改变本页回归数字。此两条“方向不一致”并非估计程序输出，本审计不据它们判断原文结论是否一致，也不推断添加者身份。当前回归数值仍可追溯到冻结R18参数；包内重跑复现的是冻结输入及模型，不能据此声称重现当前另存文件的全部字体、列宽、额外文字或保存元数据。

### 2. 三个方程和共同控制

每个实际估计样本中，模型是带截距的pooled二元Logit：

\[
 P(payer_{it}=1\mid X_{it})=\Lambda(\eta_{it}),\qquad
 \Lambda(a)=\frac{1}{1+e^{-a}},
\]

\[
\eta_{it}=\alpha+\beta_C cash\_m_{it}+\beta_Z Z_{it}
+\beta_E equity\_m_{it}+\beta_V vega\_k_{it}
+\gamma' C_{it}+\delta_{SIC2(i,t)}+\tau_{fyear(t)}.
\]

| Excel列 | `Z`的实际代码名 | 额外样本要求 |
|---|---|---|
| (8) | `inside_debt_m` | 普通B输入样本 |
| (9) | `ln_rellev` | `sample_log == 1`，即使用构建时定义的正relative-leverage子样本；没有改成`log1p` |
| (10) | `high_rellev` | 普通B输入样本 |

共同控制向量按实际顺序为：

```text
age ln_tenure rd_at_pct rd_missing capx_at_pct asset_growth
mb profitability_m size_pct re_at retvol255
```

故每式有15个非FE解释变量：4个CEO薪酬/财富变量加11个共同控制。随后加入SIC2虚拟变量、财政年度虚拟变量和截距。没有公司FE、CEO FE、行业×年份交互FE、滞后因变量或回归权重；没有将三个内部债务代理同时放在一式中。

年度和行业dummies是**两组相加的固定效应**。它们不意味着按行业和年份双向聚类，也不意味着行业×年聚类。

权威逐式变量列表：RUN/regression_config.json (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/results/table4_compilation_rep_2013_2023_20261025/regression_config.json)的`model_plan[].regressors`；实际Stata输入与对应尺度：RUN/stata/prepared.json (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/results/table4_compilation_rep_2013_2023_20261025/stata/prepared.json)。

### 3. 九个模型的样本损耗、维度与基准组

`N_input`是完成上游建表资格与窗口筛选后的输入，**不是原始Compustat或ExecuComp行数**。第(9)列的`N_input`已额外经过`sample_log==1`。`N_used`才是Excel的N，且OIM与cluster两次Stata估计使用相同ID。

| model_id | 输入N | 纯组剔除 | 实际N | 公司G | K | SIC2基准 | SIC2 dummy数 | 年基准 | 年dummy数 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `rep_original_2006_2011_m08` | 5826 | 90 | 5736 | 1424 | 70 | 2 | 49 | 2006 | 5 |
| `rep_original_2006_2011_m09` | 3495 | 79 | 3416 | 850 | 68 | 2 | 47 | 2006 | 5 |
| `rep_original_2006_2011_m10` | 5826 | 90 | 5736 | 1424 | 70 | 2 | 49 | 2006 | 5 |
| `rep_extended_2006_2023_m08` | 13828 | 112 | 13716 | 1793 | 84 | 1 | 51 | 2006 | 17 |
| `rep_extended_2006_2023_m09` | 7903 | 119 | 7784 | 1055 | 82 | 1 | 49 | 2006 | 17 |
| `rep_extended_2006_2023_m10` | 13828 | 112 | 13716 | 1793 | 84 | 1 | 51 | 2006 | 17 |
| `rep_2013_2023_m08` | 7086 | 51 | 7035 | 1304 | 76 | 1 | 50 | 2013 | 10 |
| `rep_2013_2023_m09` | 3889 | 107 | 3782 | 728 | 71 | 10 | 45 | 2013 | 10 |
| `rep_2013_2023_m10` | 7086 | 51 | 7035 | 1304 | 76 | 1 | 50 | 2013 | 10 |

K包括15个非FE变量、所有非基准行业/年dummy和截距。例如7035行普通模型的K为 `15 + 50 + 10 + 1 = 76`。设计按本模型实际使用数据中的因子值排序，以最小值作为基准，所以2013–2023的第(9)列SIC2基准是10，而普通模型为1；不能跨列强制使用已被该列样本剔掉的基准。

三个窗口的普通输入至第(9)列输入分别为：5826→3495、13828→7903、7086→3889。这一步是正relative-leverage子样本限制，后面的纯组剔除分别再损失79、119、107。删掉DVR解释变量时没有额外放回之前不满足B建表资格的观测。

#### 3.1 纯结果行业/年份组的确切算法

在每个窗口和每列子样本内，循环执行：

1. 对尚保留行，分别按`SIC2`和`fyear`计算`payer`的min/max。
2. 某一组min=max，表示该组全为0或全为1；标记该组全部行。行业与年份的删除标记取并集，不将同一行重复计数。
3. 删除已标记行，重复检查直到没有新删除。
4. 每个被删`event_id`、原因和轮次均保存；非有限设计矩阵直接报错，不在拟合时静默删行或改值。

Python证据：scripts/run_table4_python.py:18–33 (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/scripts/run_table4_python.py:18)；Stata等价循环：`RUN/stata/compilation_estimates.do:26–48`。Python在一轮中对两因子的当时样本取删除并集，Stata顺序更新；最终逐ID相等已独立验证。本次9式的trace全部在第一轮记录纯SIC2组；没有记录纯财政年度组，后续检查没有新增删除。

下面记号为 `SIC2:payer常数值:删除行数`。同窗口(8)/(10)的纯组相同。

| 输入样本 | 记录的纯SIC2组 |
|---|---|
| 原期普通 | `1:0:5; 7:0:5; 21:1:10; 22:0:17; 41:0:4; 72:1:30; 76:0:5; 83:0:7; 99:1:7`，共90 |
| 原期(9) | `1:0:5; 7:0:2; 14:1:18; 17:1:1; 21:1:10; 22:0:9; 72:1:25; 83:0:2; 99:1:7`，共79 |
| 全期普通 | `7:0:10; 21:1:16; 22:0:37; 41:0:10; 76:0:6; 83:0:13; 99:1:20`，共112 |
| 全期(9) | `7:0:7; 14:1:43; 17:1:2; 21:1:16; 22:0:23; 41:0:1; 83:0:8; 99:1:19`，共119 |
| 2013–2023普通 | `2:1:1; 7:0:4; 21:1:5; 22:0:17; 41:0:6; 83:0:6; 99:1:12`，共51 |
| 2013–2023(9) | `1:1:4; 2:1:1; 7:0:4; 14:1:22; 17:1:1; 21:1:5; 22:0:13; 41:0:1; 47:1:13; 52:1:26; 83:0:6; 99:1:11`，共107 |

该处理是避免常数结果dummy组造成的完美预测，不是为了恢复作者N进行的任意缩样，也不是对连续变量进行分位数截尾。它不等于证明全模型在数学上绝不可能存在其他分离方向；本9式另有有限MLE、信息矩阵和独立数值拟合一致的证据。

#### 3.2 逐ID证据的读法

对任一`model_id`：

- `RUN/python/samples/{model_id}_sample.csv.gz`：输入行及`used`、`reason`、删除原因；
- `RUN/python/samples/{model_id}_fitted.csv.gz`：实际拟合ID、预测概率和线性预测；
- `RUN/stata/samples/{model_id}_input.csv`：Stata输入及`pure_group_removed`；
- `RUN/stata/samples/{model_id}_used.csv`：`event_id/gvkey/fyear/sic2/payer`、两种VCE的`e(sample)`、OIM预测概率。

核对时应比较`event_id`集合和逐行字段，而不是只比较N。`gvkey`应作为字符串保留前导零；不要用ticker或公司名作为该阶段连接键。

### 4. MLE的具体数值方法

#### 4.1 Python独立引擎

代码：scripts/run_table4_python.py:35–120 (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/scripts/run_table4_python.py:35)，由compilation wrapper调用。它估计未惩罚Logit，没有Ridge/Firth/Lasso，也不按结果对样本或变量做选择。

- 对每个非FE解释变量x，用 `a=max(abs(x))`，再算 `s=a*sqrt(mean((x/a)^2))`；非零变量以`x/s`拟合，零变量保留默认尺度。没有中心化。dummy和截距的尺度为1。这个写法避免直接平方极大值溢出；它是单位的可逆重参数化，不是对原变量截尾或更换经济量纲。
- 完整设计矩阵的非有限值触发错误。将列归一化后进行SVD检查；若最小奇异值小于最大值的`1e-12`倍，报数值秩不足，而不是静默删解释变量。
- 初值：各斜率为0，截距为该样本payer均值的log-odds。
- 最大迭代500。稳定似然为 `-sum(logaddexp(0, -(2*y-1)*eta))`；残差按`y==1`用`expit(-eta)`、否则用`-expit(eta)`，避免尾部的`1-p`消减误差。
- Newton步由Fisher信息求解；每次先对信息矩阵对角正规化，再Cholesky求解。要求缩放设计中的score最大绝对值 `<1e-8`，且 `max(abs(Newton_step)/(1+abs(beta))) <1e-8`，两项同时满足。
- 线搜索最多60次步长减半；接受条件为有限LL且 `LL_new >= LL_old + 1e-4*alpha*max(0,score' step) - 2e-10`。
- 返回原单位时，系数、OIM与cluster协方差均通过保存的对角变换还原；标准误先开方再除以尺度，避免方差下溢。每个模型的`numerical_scales`、`design_columns`和NPZ的`transform`是精确记录，无需手工复写浮点尺度。

当前9个Python模型均在8个记录迭代内通过上述双条件；新窗口最大相对Newton步约`2.705e-10`，不是仅因LL显示的小数不再变化而报成功。完整迭代历史在每个`python/models/{model_id}.json`的`history`。

#### 4.2 Stata实际运行

实际可执行文件为 `C:/Program Files/StataNow19/StataSE-64.exe`，运行时版本文件记录19.5。do-file头的`version 19.0`是命令兼容性设置，不能据此把运行软件写成19.0。数据、矩阵和输出均以double保留，CSV以`%24.17g`导出。

Stata对每个模型先生成`z1...z15`，按元数据中的同一尺度缩放原变量，随后执行：

```stata
logit payer `zs' ib$BSIC.sic2 ib$BYEAR.fyear, ///
    asis collinear difficult iterate(50) ///
    tolerance(1e-8) ltolerance(1e-10) nrtolerance(1e-5)
matrix BO=e(b)
matrix VO=e(V)
logit payer `zs' ib$BSIC.sic2 ib$BYEAR.fyear, ///
    vce(cluster __cluster) from(BO,copy) ///
    asis collinear difficult iterate(50) ///
    tolerance(1e-8) ltolerance(1e-10) nrtolerance(1e-5)
```

其中`egen long __cluster=group(gvkey)`，OIM拟合不传Python候选作为起点，cluster拟合从OIM的`BO`开始。`asis collinear`是保留声明模型/观测的选项，不代表允许未检查的解释变量省略；程序检查`core_omitted==0`、两次N均等于审计后的N，并保存`e(sample)`。所有9式OIM和cluster均为`converged=1`、status=`success`。

精确命令和导出方法：`RUN/stata/compilation_estimates.do:53–133`。该文件本轮只包含新增3模型的driver；较早6个模型的相同估计来自R16，当前完整25重跑入口为`RUN/stata/RUN_TABLE4.do`。

### 5. 标准误、Wald、LL和pseudo-R2究竟来自哪里

#### 5.1 OIM与公司聚类不是两种不同的Logit方程

OIM协方差为观测Fisher信息逆矩阵。令`x_i`为含截距/dummies的设计向量，`p_i=Lambda(x_i'b)`，`s_g=sum_{i in g} x_i(y_i-p_i)`：

\[
H=\sum_i p_i(1-p_i)x_ix_i',\qquad
V_{OIM}=H^{-1},
\]

\[
V_{cluster}=\frac{G}{G-1}\,H^{-1}\left(\sum_g s_gs_g'\right)H^{-1}.
\]

这里g是`gvkey`公司，不是CEO，不是SIC2，不是年份，也不是行业×年。主用的有限G修正只有`G/(G-1)`，**没有OLS式`(N-1)/(N-K)`额外因子**。Python保留了未修正CR0及full-OLS候选方便诊断，但当前Excel不采用它们。代码：`run_table4_python.py:122–130`及`run_table4_compilation.py:93–108`；Stata与手算sandwich的独立核查已通过。

#### 5.2 当前Excel的系数、括号与星号

当前每个常规模型的系数、公司cluster SE和相应p均读取RUN/stata/coefficients.csv (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/results/table4_compilation_rep_2013_2023_20261025/stata/coefficients.csv)，不是从四舍五入的HTML或截图反推。`b`实际是第一次OIM的`BO`还原值；cluster SE来自第二次拟合的`VC`，两次在同一MLE目标下的微小点估计差另记`max_b_change`。新(9)最大原单位变化约`4.723e-10`，不是更换样本或模型。

\[
z=b/SE_{cluster},\qquad p=2\Phi(-|z|).
\]

使用标准正态Wald，不用t分布/`G-1`自由度t检验。`***`为p<0.01，`**`为p<0.05，`*`为p<0.10；边界等于阈值不落入该更严格星级。Excel中的括号是**公司聚类标准误**。原论文表括号是印刷的signed sqrt(Wald)，不能把两者直接逐格比较。

代码：`RUN/stata/compilation_estimates.do:96–115`；`scripts/assemble_table4_compilation.py:25,66–70`。Excel的星号是数字格式展示的一部分，原始数值仍为数值，不是包含星号的字符串。

**重要取值细节：当前Excel footer的LL和pseudo-R2来自Python元数据，而非直接从Stata的e(ll)栏拷入。** 这是`assemble_table4_compilation.py:72`的实际实现。两套LL最大差在约1.25e−7量级，四位小数显示一致；不得据此写成“表中每个统计量都直接来自Stata”。N/G也取逐模型JSON，并已和Stata相同ID/样本核验。

空白/横线的债务代理格表示该列未包含该变量，不是系数为0，也不是Stata因共线性自动删除。

#### 5.3 LL和McFadden pseudo-R2的定义及精确数值

模型LL是实际使用行上的二元Logit对数似然总和。令`pbar=mean(payer)`，null LL仅含截距：

\[
LL_0=\sum_i[y_i\log(\bar p)+(1-y_i)\log(1-\bar p)],\quad
R^2_{McFadden}=1-LL/LL_0.
\]

不是线性回归R2，也不是“只含行业/年份FE”的参照模型。每个不同实际样本都有自己的`pbar`和LL0。代码：`run_table4_compilation.py:106–108`。

| 模型 | Excel源Python LL | Python LL0 | pseudo-R2 |
|---|---:|---:|---:|
| 原期(8) | −2750.226066568473 | −3947.124087234105 | 0.30323293471737356 |
| 原期(9) | −1729.934100310602 | −2282.0826471167957 | 0.24194940858245573 |
| 原期(10) | −2787.5162693545326 | −3947.124087234105 | 0.2937854985684406 |
| 2006–2023(8) | −6587.4218457414245 | −9507.057413349383 | 0.3071019181506506 |
| 2006–2023(9) | −3674.652145068055 | −4947.199805502169 | 0.25722584703751283 |
| 2006–2023(10) | −6598.753524823331 | −9507.057413349383 | 0.30590999528858875 |
| 2013–2023(8) | −3213.4522107795456 | −4860.645481022711 | 0.3388836475884238 |
| 2013–2023(9) | −1581.1615712566468 | −2271.23740801237 | 0.30383254270174687 |
| 2013–2023(10) | −3203.5621435074922 | −4860.645481022711 | 0.34091837061248864 |

Stata的对应LL保留在RUN/stata/model_summary.csv (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/results/table4_compilation_rep_2013_2023_20261025/stata/model_summary.csv)。例如2013–2023(8)为−3213.452210692471，(9)为−1581.161571256647，(10)为−3203.5621434410168。

### 6. Excel与权威产物的坐标映射

| 工作表区域 | 内容 | 三列B/C/D对应 |
|---|---|---|
| A5:D52 | 2006–2011面板 | `rep_original_2006_2011_m08/m09/m10` |
| A55:D102 | 2006–2023面板 | `rep_extended_2006_2023_m08/m09/m10` |
| A105:D152 | 2013–2023面板 | `rep_2013_2023_m08/m09/m10` |
| A3:A4 | 三窗口字幕及无DVR说明 | 不是回归数据 |
| A155起 | 样本、VCE、单位、作者差异说明 | 不是额外模型 |

每式有15个非FE解释变量；面板按三式并集展示17个解释变量行（其中3个债务代理互斥）及截距，共18行，系数与括号SE各占相邻一行。行业/年份FE系数不在主表逐项显示，但全部在系数CSV和协方差文件中。RUN/table_payload.json (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/results/table4_compilation_rep_2013_2023_20261025/table_payload.json)的`tables[1]`存本页全部面板/脚注/元数据；RUN/displayed_table_cells.csv (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/results/table4_compilation_rep_2013_2023_20261025/displayed_table_cells.csv)以`table_id=table2`、`column_id=model_id`、`term`对应每个非空系数格；它是核对显示的便利索引，估计权威仍是Stata系数文件。

协方差位置：`RUN/python/models/{model_id}_covariances.npz`保存原单位与scaled表示；`RUN/stata/covariances/{model_id}_{oim,cluster}.dta`保存Stata矩阵。**Stata矩阵可能包含被作为基准省略的因子列，不能直接按Python的K行号生硬对比。** 应按对应模型系数CSV的term顺序或`.ster`的`e(b)`列名对齐，并使用`omitted_oim/omitted_cluster`标志排除基准列。`core_omitted=0`不意味着基准因子也作为自由参数估计。

### 7. 验证覆盖与继承关系

原期和2006–2023的六个当前无DVR模型首次在`results/table4_compilation_no_dvr_20261025`（R16）估计。它们进入R17、再进入当前R18时是已验证数值的复制，没有在每次更新Excel时重估。2013–2023三个模型是在R18新增估计。

| 核验层 | 实际覆盖 | 关键证据 |
|---|---|---|
| R16独立数值 | 22个无DVR模型，包括本页前6个；独立statsmodels+手算公司cluster | results/table4_compilation_no_dvr_20261025/audit/independent/summary.json (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/results/table4_compilation_no_dvr_20261025/audit/independent/summary.json) |
| R18独立数值 | 新3模型：独立源窗口筛选/pure组/设计/fit/两VCE/星号；旧22复制完整性 | RUN/audit/independent/summary.json (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/results/table4_compilation_rep_2013_2023_20261025/audit/independent/summary.json) |
| 全25保存结果与Python核对 | 包括本页9个，逐ID、列、尺度、系数、OIM/cluster SE、LL、预测等 | RUN/stata/STATA_AUDIT.json (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/results/table4_compilation_rep_2013_2023_20261025/stata/STATA_AUDIT.json)及`comparison.csv` |
| R18冻结Excel XML | 对历史8ca...工作簿：原前两面板384格保持，新48coef+48SE+30footer准确；ModelData原1526条完整保留、新增223条 | RUN/audit/independent/workbook_XML_validation.json (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/results/table4_compilation_rep_2013_2023_20261025/audit/independent/workbook_XML_validation.json) |

R16全22模型的独立max LL差约1.2483e−7，OIM/cluster SE最大相对差约2.5731e−6/2.5321e−6；这是全22模型的上界，不能把它误称为本页六模型独有误差。R18新3的max LL差8.7074e−8、缩放系数差2.9316e−9、OIM/cluster SE相对差3.1301e−8/5.7208e−8，星号全部相同。

R18冻结工作簿共5页、全表25模型；本节当前现场范围只核查`2 Replication`的9个，不把全25当本页模型数，也不将本页比较结论外推为其它工作表当前值/格式已验证。R18保护旧22模型242份文件逐字节一致，不等于本轮又独立重估旧22次。

### 8. 分层复核与安全重跑

#### 8.1 不重估、不改文件的核查

直接读取当前RUN/regression_config.json (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/results/table4_compilation_rep_2013_2023_20261025/regression_config.json)、`model_provenance.csv`、九个模型JSON、`stata/model_summary.csv`、`stata/coefficients.csv`、样本ID和XML验证文件。确认：

1. 只选`table_group == replication`，应有9个模型；regressors无DVR、无score，均有`rd_at_pct`及`rd_missing`。
2. 按上表检查N/G/K/基准组与pure trace；OIM/cluster样本ID一致，原值/单位与snapshot相同。
3. 将系数CSV筛到同模型和term，检查coef、`se_cluster`、`p_cluster`；按正态Wald重新算星号，再与payload的未四舍五入值及Excel显示对照。
4. 用每模型实际payer重算LL0与pseudo-R2，说明采用Python还是StataLL，保留约1e−7的数值差而非将其四舍五入后称字节相同。
5. 本轮主Excel现场哈希是第1节的8f3d...，历史R18的8ca0...只对应包内冻结副本。RUN/package_validation.json (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/results/table4_compilation_rep_2013_2023_20261025/package_validation.json)的“包内Excel字节相同”是打包当时的历史结论，不表示目前主文件与包内副本相同。核查目前主文件必须使用本轮现场单元值/格式比较证据；不能将旧XML验证报告或哈希直接当作新文件的证明。

#### 8.2 在新目录重跑包内完整25模型

当前重跑包：项目outputs/01a17125-70eb-72b1-abff-27491f3aec3e/table4_annual_b_package.zip (historical source reference: D:/pc_workspace_local/ceo_risk_taking/outputs/01a17125-70eb-72b1-abff-27491f3aec3e/table4_annual_b_package.zip)，SHA256为`23eac0ea2422c4febb2421f2504cdd44ff3ecc989efd6eeed169a44db704e5a0`，23,341,750 bytes，含25份Stata输入DTA和完整相对路径程序。包内Excel为历史冻结8ca...，目前主文件为8f3d...，两者字节不同。以下重跑验证的是冻结R18输入和估计，不是重新验证目前另存版本的格式/保存行为。包无需WRDS重新登录，也不会重新训练synthetic proxy of CEO risk preference。

请把它解压到一个**新的验证目录**，不要直接运行当前项目RUN下带绝对路径和`replace`的估计do-file。以下PowerShell只新建/解压，不删除或移动原结果：

```powershell
$projectDir = 'D:\pc_workspace_local\ceo_risk_taking'
$verifyDir = Join-Path $projectDir 'verification_runs\table4_audit_001'
if (Test-Path -LiteralPath $verifyDir) { throw '请改用一个尚不存在的验证目录名' }
New-Item -ItemType Directory -Path $verifyDir -Force | Out-Null
Expand-Archive -LiteralPath (Join-Path $projectDir 'outputs\01a17125-70eb-72b1-abff-27491f3aec3e\table4_annual_b_package.zip') -DestinationPath $verifyDir
```

再在Stata中：

```stata
cd "D:/pc_workspace_local/ceo_risk_taking/verification_runs/table4_audit_001"
do "RUN_TABLE4.do"
```

包根入口会进入`stata`目录执行其中的`RUN_TABLE4.do`，回归完整25个模型（包括本页9个），并替换**该新解压目录内**已有的Stata输出；不会触及当前项目结果根。Stata的版本及浮点差可能导致极小差异，应按未四舍五入值和既有容差核对，不要求所有CSV文件字节相同。

#### 8.3 如果只想重跑本页9个模型

仍在上一步新建的验证副本中，按`global MID`driver块筛选`rep_`模型，保留同一程序头和导出尾。以下Python只创建验证副本中的新do，不执行回归；存在同名目标时拒绝覆盖：

```python
from pathlib import Path
import re

verification_root = Path(r'D:/pc_workspace_local/ceo_risk_taking/verification_runs/table4_audit_001')
source = verification_root / 'stata/RUN_TABLE4.do'
target = verification_root / 'stata/RUN_REPLICATION_9.do'
if target.exists():
    raise FileExistsError(target)
text = source.read_text(encoding='utf-8')
start = text.index('global MID ')
finish = text.index('postclose PCEOT4COEF', start)
chunks = re.split(r'(?m)(?=^global MID )', text[start:finish])
selected = [block for block in chunks if re.match(r'global MID "rep_', block)]
assert len(selected) == 9
target.write_text(text[:start] + ''.join(selected) + text[finish:], encoding='utf-8')
```

在Stata中把工作目录设为该验证副本的`stata`目录，再`do RUN_REPLICATION_9.do`。新复制目录的汇总CSV/DTA将只含这9个模型，不能拿它覆盖项目内完整25模型汇总表。先按`model_id,term`与当前权威CSV对齐，排除base omitted行，再比较系数/SE/LL；同时比较`*_used.csv`的实际ID及OIM/cluster样本标记。

#### 8.4 需要从原始数据重构时

本页的重跑包从已冻结DTA开始，能验证Logit与展示，不会重新验证CEO选择、CCM、CRSP历史、期权完整性或所有原始字段。完整端到端复核必须按前面的数据/变量章节重新构造输入。

原始建表/估计脚本可能使用固定结果路径；不应在当前研究目录直接“全部再跑”后覆盖旧产物。应复制完整项目或使用明确独立的新输出根，并把新数据、参数、运行版本、ID损耗和哈希与当前冻结输入比较。仅重新组装Excel/HTML不能替代原始数据重构，也不是新一轮估计。


<a id="estimates"></a>

## 5. 当前工作表的完整系数与公司聚类SE

系数和SE使用冻结导出时的显示字符串；footer保留元数据未四舍五入值，便于精确核验。当前文件若仅有格式变化，应以底层数值比较。这不是重新估计。每个参数格是系数和括号内公司cluster SE，星号按对应normal-Wald p生成。未纳入的互斥债务代理留空；不存在DVR或ML score行。行业/年dummy的完整系数在上述CSV中。

系数是条件log-odds系数。连续变量每增加一个本表单位，条件odds乘以exp(β)；概率边际效应为p(1−p)β，依赖于协变量和基准概率，不能把β或(exp(β)−1)直接称为固定的概率百分点变化。本页pooled相关回归及风险暴露proxy也不直接识别CEO私人心理偏好或因果效应。



### Original window2006–2011


| 变量 | (8) | (9) | (10) |
| --- | --- | --- | --- |
| CEO cash comp. ($ million) | 0.1002* (0.0591) | 0.0700 (0.0798) | 0.1419** (0.0717) |
| CEO inside debt ($ million) | 0.0579*** (0.0197) | — | — |
| Log CEO relative leverage | — | 0.1445*** (0.0494) | — |
| High relative leverage dummy | — | — | 0.5357*** (0.1917) |
| CEO equity wealth ($ million) | -4.515e-06 (4.100e-05) | -5.753e-05 (5.583e-05) | -4.415e-05 (4.142e-05) |
| CEO Vega ($ thousand / 1pp vol.) | -9.479e-05 (0.0003) | 0.0007* (0.0004) | 0.0002 (0.0003) |
| CEO age (years) | 0.0218** (0.0100) | 0.0195 (0.0137) | 0.0256** (0.0100) |
| Log CEO tenure | -0.1366* (0.0758) | -0.1038 (0.0968) | -0.0813 (0.0737) |
| Actual R&D/assets (pp) | -0.0987*** (0.0261) | -0.1175*** (0.0394) | -0.1135*** (0.0270) |
| R&D missing dummy | 0.3749** (0.1811) | 0.2390 (0.2340) | 0.3648** (0.1809) |
| CAPEX/assets (pp) | -0.0073 (0.0126) | -0.0084 (0.0167) | -0.0099 (0.0127) |
| Asset growth (decimal ratio) | -0.9532*** (0.2147) | -0.5898*** (0.1737) | -1.0040*** (0.2194) |
| Market/book | 0.0005 (0.0017) | -0.0034 (0.0028) | 1.293e-05 (0.0018) |
| Profitability ($ million) | 0.0001 (8.677e-05) | 7.040e-05 (7.286e-05) | 0.0001 (9.516e-05) |
| Size percentile (0-100) | 0.0118*** (0.0031) | 0.0145*** (0.0040) | 0.0152*** (0.0031) |
| Retained earnings/assets (ratio) | 1.4121*** (0.2656) | 1.8652*** (0.3372) | 1.3315*** (0.2553) |
| Return volatility (pp) | -0.2979*** (0.0561) | -0.2083*** (0.0666) | -0.2837*** (0.0561) |
| Constant | -1.3681 (1.4346) | -0.8948 (1.6410) | -1.8179 (1.5621) |
| Industry FE | Yes | Yes | Yes |
| Year FE | Yes | Yes | Yes |
| Actual R&D control | Yes | Yes | Yes |
| N | 5736 | 3416 | 5736 |
| Firm clusters | 1424 | 850 | 1424 |
| Log likelihood | -2750.226066568473 | -1729.934100310602 | -2787.5162693545326 |
| Pseudo R2 | 0.30323293471737356 | 0.24194940858245573 | 0.2937854985684406 |
| Inference | Regular | Regular | Regular |
| Estimate source | Stata19.5 | Stata19.5 | Stata19.5 |
| Stata attempt | success | success | success |


### Extended window2006–2023


| 变量 | (8) | (9) | (10) |
| --- | --- | --- | --- |
| CEO cash comp. ($ million) | 0.1223** (0.0579) | 0.0841 (0.0714) | 0.1563** (0.0616) |
| CEO inside debt ($ million) | 0.0316 (0.0267) | — | — |
| Log CEO relative leverage | — | 0.1461*** (0.0404) | — |
| High relative leverage dummy | — | — | 0.6629*** (0.1661) |
| CEO equity wealth ($ million) | 4.112e-06 (1.824e-05) | -2.940e-05 (5.860e-05) | -1.620e-06 (1.150e-05) |
| CEO Vega ($ thousand / 1pp vol.) | -6.535e-05 (0.0001) | 0.0005 (0.0004) | -3.954e-05 (5.055e-05) |
| CEO age (years) | 0.0239*** (0.0083) | 0.0235** (0.0115) | 0.0250*** (0.0079) |
| Log CEO tenure | -0.2134*** (0.0629) | -0.2088*** (0.0768) | -0.1742*** (0.0550) |
| Actual R&D/assets (pp) | -0.1220*** (0.0192) | -0.1298*** (0.0278) | -0.1307*** (0.0187) |
| R&D missing dummy | 0.3936** (0.1602) | 0.2216 (0.2069) | 0.3757** (0.1590) |
| CAPEX/assets (pp) | -0.0437*** (0.0115) | -0.0352** (0.0160) | -0.0462*** (0.0116) |
| Asset growth (decimal ratio) | -0.7078*** (0.1127) | -0.4632*** (0.1040) | -0.7344*** (0.1052) |
| Market/book | 3.188e-05 (7.869e-05) | -8.769e-05 (5.580e-05) | 3.883e-06 (6.751e-05) |
| Profitability ($ million) | 5.536e-05 (4.453e-05) | 6.346e-05 (4.594e-05) | 7.525e-05 (4.644e-05) |
| Size percentile (0-100) | 0.0136*** (0.0030) | 0.0168*** (0.0035) | 0.0154*** (0.0025) |
| Retained earnings/assets (ratio) | 1.0083*** (0.1884) | 1.4738*** (0.2799) | 0.9613*** (0.1791) |
| Return volatility (pp) | -0.4969*** (0.0526) | -0.3366*** (0.0638) | -0.4884*** (0.0525) |
| Constant | -1.2291 (1.0811) | -1.2913 (1.1246) | -1.3609 (1.0851) |
| Industry FE | Yes | Yes | Yes |
| Year FE | Yes | Yes | Yes |
| Actual R&D control | Yes | Yes | Yes |
| N | 13716 | 7784 | 13716 |
| Firm clusters | 1793 | 1055 | 1793 |
| Log likelihood | -6587.4218457414245 | -3674.652145068055 | -6598.753524823331 |
| Pseudo R2 | 0.3071019181506506 | 0.25722584703751283 | 0.30590999528858875 |
| Inference | Regular | Regular | Regular |
| Estimate source | Stata19.5 | Stata19.5 | Stata19.5 |
| Stata attempt | success | success | success |


### Additional window2013–2023


| 变量 | (8) | (9) | (10) |
| --- | --- | --- | --- |
| CEO cash comp. ($ million) | 0.2125* (0.1098) | 0.2835 (0.2068) | 0.2291** (0.1137) |
| CEO inside debt ($ million) | 0.0139 (0.0296) | — | — |
| Log CEO relative leverage | — | 0.1579*** (0.0567) | — |
| High relative leverage dummy | — | — | 0.6890*** (0.2380) |
| CEO equity wealth ($ million) | 1.282e-05 (2.491e-05) | 0.0006 (0.0007) | 1.062e-05 (2.252e-05) |
| CEO Vega ($ thousand / 1pp vol.) | -7.941e-05 (0.0001) | 0.0001 (0.0006) | -6.732e-05 (0.0001) |
| CEO age (years) | 0.0247** (0.0113) | 0.0225 (0.0179) | 0.0252** (0.0109) |
| Log CEO tenure | -0.3019*** (0.0851) | -0.3053** (0.1251) | -0.2854*** (0.0753) |
| Actual R&D/assets (pp) | -0.1375*** (0.0241) | -0.1510*** (0.0347) | -0.1429*** (0.0229) |
| R&D missing dummy | 0.4884** (0.2138) | 0.3224 (0.2961) | 0.4634** (0.2114) |
| CAPEX/assets (pp) | -0.0780*** (0.0161) | -0.0649*** (0.0246) | -0.0795*** (0.0161) |
| Asset growth (decimal ratio) | -0.5175*** (0.1290) | -0.2978* (0.1551) | -0.5166*** (0.1180) |
| Market/book | 4.933e-05 (7.541e-05) | 5.074e-05 (0.0001) | 3.510e-05 (7.396e-05) |
| Profitability ($ million) | 3.352e-05 (4.323e-05) | 4.531e-05 (5.095e-05) | 4.271e-05 (4.241e-05) |
| Size percentile (0-100) | 0.0140*** (0.0037) | 0.0189*** (0.0056) | 0.0146*** (0.0033) |
| Retained earnings/assets (ratio) | 0.8847*** (0.1964) | 1.3559*** (0.3356) | 0.8540*** (0.1927) |
| Return volatility (pp) | -0.7610*** (0.0848) | -0.5827*** (0.1113) | -0.7511*** (0.0846) |
| Constant | 0.7049 (1.3017) | 1.2987 (1.2019) | 0.4704 (1.2527) |
| Industry FE | Yes | Yes | Yes |
| Year FE | Yes | Yes | Yes |
| Actual R&D control | Yes | Yes | Yes |
| N | 7035 | 3782 | 7035 |
| Firm clusters | 1304 | 728 | 1304 |
| Log likelihood | -3213.4522107795456 | -1581.1615712566468 | -3203.5621435074922 |
| Pseudo R2 | 0.3388836475884238 | 0.30383254270174687 | 0.34091837061248864 |
| Inference | Regular | Regular | Regular |
| Estimate source | Stata19.5 | Stata19.5 | Stata19.5 |
| Stata attempt | success | success | success |


<a id="design"></a>

## 6. 完整FE取值集合及精确源文件入口

以下集合包含基准组；估计时省略所列base。普通(8)/(10)共享同样本和FE集合，只替换内部债务代理。



```text
Original window2006–2011 (8)/(10)
SIC2（含base）: 2, 10, 12, 13, 14, 15, 16, 17, 20, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 42, 44, 45, 47, 48, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 70, 73, 75, 78, 79, 80, 82, 87
SIC2 base: 2
财政年（含base）: 2006, 2007, 2008, 2009, 2010, 2011
fyear base: 2006
```



```text
Original window2006–2011 (9)
SIC2（含base）: 2, 10, 12, 13, 15, 16, 20, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 42, 44, 45, 47, 48, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 70, 73, 75, 78, 79, 80, 82, 87
SIC2 base: 2
财政年（含base）: 2006, 2007, 2008, 2009, 2010, 2011
fyear base: 2006
```



```text
Extended window2006–2023 (8)/(10)
SIC2（含base）: 1, 2, 10, 12, 13, 14, 15, 16, 17, 20, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 42, 44, 45, 47, 48, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 70, 72, 73, 75, 78, 79, 80, 82, 87
SIC2 base: 1
财政年（含base）: 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023
fyear base: 2006
```



```text
Extended window2006–2023 (9)
SIC2（含base）: 1, 2, 10, 12, 13, 15, 16, 20, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 42, 44, 45, 47, 48, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 70, 72, 73, 75, 78, 79, 80, 82, 87
SIC2 base: 1
财政年（含base）: 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023
fyear base: 2006
```



```text
Additional window2013–2023 (8)/(10)
SIC2（含base）: 1, 10, 12, 13, 14, 15, 16, 17, 20, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 42, 44, 45, 47, 48, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 70, 72, 73, 75, 78, 79, 80, 82, 87
SIC2 base: 1
财政年（含base）: 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023
fyear base: 2013
```



```text
Additional window2013–2023 (9)
SIC2（含base）: 10, 12, 13, 15, 16, 20, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 42, 44, 45, 48, 50, 51, 53, 54, 55, 56, 57, 58, 59, 70, 72, 73, 75, 78, 79, 80, 82, 87
SIC2 base: 10
财政年（含base）: 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023
fyear base: 2013
```



| model_id | 模型元数据 | 输入 | 样本 | Stata估计 |
| --- | --- | --- | --- | --- |
| rep_original_2006_2011_m08 | 规格/尺度/迭代历史 (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/results/table4_compilation_rep_2013_2023_20261025/python/models/rep_original_2006_2011_m08.json) | 原单位Stata输入 (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/results/table4_compilation_rep_2013_2023_20261025/stata/inputs/rep_original_2006_2011_m08.dta) | 精确e(sample) (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/results/table4_compilation_rep_2013_2023_20261025/stata/samples/rep_original_2006_2011_m08_used.csv) | cluster估计对象 (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/results/table4_compilation_rep_2013_2023_20261025/stata/estimates/rep_original_2006_2011_m08_cluster.ster) |
| rep_original_2006_2011_m09 | 规格/尺度/迭代历史 (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/results/table4_compilation_rep_2013_2023_20261025/python/models/rep_original_2006_2011_m09.json) | 原单位Stata输入 (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/results/table4_compilation_rep_2013_2023_20261025/stata/inputs/rep_original_2006_2011_m09.dta) | 精确e(sample) (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/results/table4_compilation_rep_2013_2023_20261025/stata/samples/rep_original_2006_2011_m09_used.csv) | cluster估计对象 (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/results/table4_compilation_rep_2013_2023_20261025/stata/estimates/rep_original_2006_2011_m09_cluster.ster) |
| rep_original_2006_2011_m10 | 规格/尺度/迭代历史 (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/results/table4_compilation_rep_2013_2023_20261025/python/models/rep_original_2006_2011_m10.json) | 原单位Stata输入 (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/results/table4_compilation_rep_2013_2023_20261025/stata/inputs/rep_original_2006_2011_m10.dta) | 精确e(sample) (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/results/table4_compilation_rep_2013_2023_20261025/stata/samples/rep_original_2006_2011_m10_used.csv) | cluster估计对象 (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/results/table4_compilation_rep_2013_2023_20261025/stata/estimates/rep_original_2006_2011_m10_cluster.ster) |
| rep_extended_2006_2023_m08 | 规格/尺度/迭代历史 (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/results/table4_compilation_rep_2013_2023_20261025/python/models/rep_extended_2006_2023_m08.json) | 原单位Stata输入 (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/results/table4_compilation_rep_2013_2023_20261025/stata/inputs/rep_extended_2006_2023_m08.dta) | 精确e(sample) (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/results/table4_compilation_rep_2013_2023_20261025/stata/samples/rep_extended_2006_2023_m08_used.csv) | cluster估计对象 (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/results/table4_compilation_rep_2013_2023_20261025/stata/estimates/rep_extended_2006_2023_m08_cluster.ster) |
| rep_extended_2006_2023_m09 | 规格/尺度/迭代历史 (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/results/table4_compilation_rep_2013_2023_20261025/python/models/rep_extended_2006_2023_m09.json) | 原单位Stata输入 (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/results/table4_compilation_rep_2013_2023_20261025/stata/inputs/rep_extended_2006_2023_m09.dta) | 精确e(sample) (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/results/table4_compilation_rep_2013_2023_20261025/stata/samples/rep_extended_2006_2023_m09_used.csv) | cluster估计对象 (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/results/table4_compilation_rep_2013_2023_20261025/stata/estimates/rep_extended_2006_2023_m09_cluster.ster) |
| rep_extended_2006_2023_m10 | 规格/尺度/迭代历史 (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/results/table4_compilation_rep_2013_2023_20261025/python/models/rep_extended_2006_2023_m10.json) | 原单位Stata输入 (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/results/table4_compilation_rep_2013_2023_20261025/stata/inputs/rep_extended_2006_2023_m10.dta) | 精确e(sample) (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/results/table4_compilation_rep_2013_2023_20261025/stata/samples/rep_extended_2006_2023_m10_used.csv) | cluster估计对象 (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/results/table4_compilation_rep_2013_2023_20261025/stata/estimates/rep_extended_2006_2023_m10_cluster.ster) |
| rep_2013_2023_m08 | 规格/尺度/迭代历史 (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/results/table4_compilation_rep_2013_2023_20261025/python/models/rep_2013_2023_m08.json) | 原单位Stata输入 (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/results/table4_compilation_rep_2013_2023_20261025/stata/inputs/rep_2013_2023_m08.dta) | 精确e(sample) (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/results/table4_compilation_rep_2013_2023_20261025/stata/samples/rep_2013_2023_m08_used.csv) | cluster估计对象 (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/results/table4_compilation_rep_2013_2023_20261025/stata/estimates/rep_2013_2023_m08_cluster.ster) |
| rep_2013_2023_m09 | 规格/尺度/迭代历史 (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/results/table4_compilation_rep_2013_2023_20261025/python/models/rep_2013_2023_m09.json) | 原单位Stata输入 (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/results/table4_compilation_rep_2013_2023_20261025/stata/inputs/rep_2013_2023_m09.dta) | 精确e(sample) (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/results/table4_compilation_rep_2013_2023_20261025/stata/samples/rep_2013_2023_m09_used.csv) | cluster估计对象 (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/results/table4_compilation_rep_2013_2023_20261025/stata/estimates/rep_2013_2023_m09_cluster.ster) |
| rep_2013_2023_m10 | 规格/尺度/迭代历史 (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/results/table4_compilation_rep_2013_2023_20261025/python/models/rep_2013_2023_m10.json) | 原单位Stata输入 (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/results/table4_compilation_rep_2013_2023_20261025/stata/inputs/rep_2013_2023_m10.dta) | 精确e(sample) (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/results/table4_compilation_rep_2013_2023_20261025/stata/samples/rep_2013_2023_m10_used.csv) | cluster估计对象 (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/results/table4_compilation_rep_2013_2023_20261025/stata/estimates/rep_2013_2023_m10_cluster.ster) |


<a id="differences"></a>

## 7. 单位依据、版本与已知差异的定位



金额和数量的转换不只依据WRDS表单中简短的“$”标签。2026-10-24的源审计保存了供应商定义、WRDS dictionary观察值和页码：source_audit_20261024.json的units部分 (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/metadata/source_audit_20261024.json)。其供应商文档为[ExecuComp Data Definitions By Table (S&P vendor definitions mirrored by university)](https://www.takming.edu.tw/lib/file/ExecuComp_Definitions(%E8%A8%BB%E8%A7%A3%E7%89%88).pdf)（大学镜像）；anncomp持股、未归属股与outstanding options分别对应PDF零基页10/12/39。该审计确认数量为千股/千份标的证券、salary/bonus/养老金/递延余额为千美元，S/X为实际美元每股。本次核对实际换算代码与该冻结依据；未把当时的在线核对说成今天重新查询。



原文来源：用户提供的《CEO risk preferences and dividend policy decisions》，Caliskan & Doukas，JCF35(2015)，18–42。Table4为PDF第11页/刊物第28页；公司变量见Appendix A，CEO变量见Appendix B。可核对原Table4页图 (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/results/table4_compilation_rep_2013_2023_20261025/reference/original_table4_page11.png)、本地全文摘录 (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/audits/sample_gap_20261024/paper_fulltext.txt)和原期样本差额审计 (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/audits/sample_gap_20261024/SAMPLE_GAP_REPORT.txt)。



原期实际N与原文的数值差：普通列5736−2117=3619；log列3416−834=2582。它们是净数量差，**不是已识别的额外ID清单，也不能据此认定两样本互相嵌套**。未取得作者原ID、程序或完整披露的精确规则，样本差额原因没有被唯一确定。没有为了逼近原N或符号新增任意市值、指数、tranche数或缺失门槛。



删除DVR的历史原因及原值核对记录在DVR极端值/不收敛审计 (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/audits/dvr_nonconvergence_20261025/DVR_NONCONVERGENCE_REPORT.html)。当时极小正Vega令DVR范围极端、似然平坦；本页按用户要求删除该回归项，再验证常规MLE。此举改变方程，没有被声称是作者未披露的缩尾规则，也没有放宽冻结B样本资格。



<a id="verification"></a>

## 8. 本次整理实际完成的只读核验



- 现场读取当前Excel和R18配置，核对9个Replication模型，全部无DVR/ML score，全部保留实际R&D及missing indicator。
- 从Excel OOXML直接核对144个系数和144个公司cluster SE，共288个数值单元，全部匹配当前payload；未用截图或四舍五入值作估计源。
- 从实际样本CSV重数每式N、公司G、payer数量/比例，并核对唯一event_id。
- 在内存结构核对文中9-only Stata driver抽取：恰好9个model_id，完整保留table4fit程序头和导出尾，路径为相对路径；没有执行该do或任何回归。
- 对构建ledger全部11个raw文件逐字节重算SHA256，包括CRSP日度大表；全部等于构建清单。11包含保留但不用的旧CCM，当前活跃源为前述10份。
- 整理前后对当前Excel、核心构建代码/配置、9模型元数据/协方差、Stata输入/样本等48文件作SHA保护；它们没有被本文生成过程修改。



证据：本次文档QA (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/audits/replication_documentation_20261025/DOCUMENT_QA.json)；raw SHA逐文件比较 (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/audits/replication_documentation_20261025/raw_source_integrity.json)；整理前SHA (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/audits/replication_documentation_20261025/protected_before.json)；整理后SHA (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/audits/replication_documentation_20261025/protected_after.json)。



| 原始文件（含1历史保留） | 本次SHA256与构建清单匹配 |
| --- | --- |
| funda_datadate_2003-01_2024-06.csv.gz (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/data/raw/compustat/funda_datadate_2003-01_2024-06.csv.gz) | `885730ce1967bac4a4c79313805730f3d10114b8e35dfadee0d1c9d8d7f45b3f` |
| funda_population_keys_all.csv.gz (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/data/raw/compustat/funda_population_keys_all.csv.gz) | `4a88ca650aae23cc8cfdd112b9ea1eb812c73b9d054c80c9bca62eb8c6e1f2c0` |
| ccm_link_history_all.csv.gz (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/data/raw/crsp/ccm_link_history_all.csv.gz) | `d08c0887de29af1a1f2381bad13191b0e4ca1b5abdf882f3b35d9dcfe2adb8d1` |
| ccmxpf_lnkhist_postgres_all.csv.gz (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/data/raw/crsp/ccmxpf_lnkhist_postgres_all.csv.gz) | `21294af9b68abc6d12e333521743459f3f45509d14547649349e4ef49f5ef905` |
| dsf_all_2005-01-01_2024-06-30.csv.gz (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/data/raw/crsp/dsf_all_2005-01-01_2024-06-30.csv.gz) | `248b2903269864d287e7649006b14720d1993027be647cf5390d0d9b8d1b7d86` |
| msf_all_2000-12_2024-06.csv.gz (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/data/raw/crsp/msf_all_2000-12_2024-06.csv.gz) | `bb5e4b1af023bc9a11ab0cca444b498c8fd4dbe968a42ff1e6fd9640b7b49dc5` |
| anncomp_1992_2023_allfields.csv.gz (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/data/raw/execucomp/anncomp_1992_2023_allfields.csv.gz) | `724e65e4748724bba9d8673218d9237db89bc2c5436e6f9d5e736e8d6ccbf9ac` |
| deferredcomp_2006_2023_allfields.csv.gz (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/data/raw/execucomp/deferredcomp_2006_2023_allfields.csv.gz) | `a288fe545ead67e6692301d35c8c402ccebcb067b427fecf141420bdb2d4d561` |
| outstandingawards_2006_2023_allfields.csv.gz (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/data/raw/execucomp/outstandingawards_2006_2023_allfields.csv.gz) | `c0bca00b66b96de191a6235a7feddc8c02aadb71ad20a051c1b291cd5195b8b9` |
| pension_2006_2023_allfields.csv.gz (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/data/raw/execucomp/pension_2006_2023_allfields.csv.gz) | `c3b352f4b285448e6cad3cfc86cdc60ade037ca2d8830186144d257adcac6be7` |
| DTB3_2005-01-01_2024-06-30.csv (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/data/raw/fred/DTB3_2005-01-01_2024-06-30.csv) | `c75a500df79ed08cd24922a20ba58b564b54abd77629dbbe1fcad99ae1170a86` |



以上检查确认的是当前保存输入、代码、估计与Excel的一致性；没有把源数据逐行与上市公司所有原始披露重新核查，也没有重新下载数据库、恢复作者2015数据快照或独立重跑本次9个MLE。此前的独立统计验证覆盖已在第4节逐层注明。

本文生成及只读核对脚本：build_audit_markdown.py (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/audits/replication_documentation_20261025/build_audit_markdown.py)。再次执行仅重新生成本文和本次文档QA，不执行研究数据构建或回归；如需保留本文当前版本，请先另存。



<a id="checklist"></a>

## 9. 核验时先看的差异清单

| 想确认的问题 | 当前事实 | 首选证据 |
|---|---|---|
| 是作者原样本/原式吗 | 未恢复原样本；本页还明确删了DVR | 第1/7节，原表和sample-gap审计 |
| 是PCEO或A吗 | 年度CEO B；不加PCEO | config、CEO选择和B公式 |
| 为何无DVR还排零Vega | 固定原B共同完整样本资格没有放宽 | build_regression_data.py215–218 |
| 为何(9)N少 | 正relative leverage，再重新剔纯结果组 | 每式sample和pure trace |
| SIC2+year是cluster吗 | 两组dummy；SE另按gvkey公司cluster | 方程、do和sandwich公式 |
| 是否有R&D missing | 本页九列全有，且控制实际R&D | regressors、Excel第3面板123–126行 |
| 是否用了_full或OOF score | 本页完全没有ML score | Replication的9份regressors |
| 2013窗是否仅score覆盖公司 | 否，完整年度B；N7035/3782/7035 | 新快照、source window审计 |
| 数值缩放是否改了单位 | 没有，MLE可逆重参数化并回原单位 | 模型JSON scales和NPZ transform |
| footer LL是否直接来自Stata | 来自Python元数据，和Stata近似一致 | assembler及两套LL文件 |
| 重跑是否会覆盖旧结果 | 原绝对路径脚本可能覆盖；使用新解压副本 | 第4节安全重跑说明 |
