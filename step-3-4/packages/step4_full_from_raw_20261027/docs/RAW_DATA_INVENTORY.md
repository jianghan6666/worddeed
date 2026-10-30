# 原始数据及冻结输入清单

下列供应商下载数据保持原始文件字节；对应SQL、字段标签、查询条件、下载时间和既有校验记录在相同目录。文件SHA256见[immutable_inputs.csv](../provenance/immutable_inputs.csv)。

| 文件 | 大小（MB） | 用途 |
|---|---:|---|
| [funda_datadate_2003-01_2024-06.csv.gz](../project/replications/caliskan_doukas_2015/data/raw/compustat/funda_datadate_2003-01_2024-06.csv.gz) | 9.51 | 财务变量、股息、股价、市值与历史行业 |
| [funda_datadate_2003-01_2024-06.sql](../project/replications/caliskan_doukas_2015/data/raw/compustat/funda_datadate_2003-01_2024-06.sql) | 0.00 | 财务变量、股息、股价、市值与历史行业 |
| [funda_population_keys_all.csv.gz](../project/replications/caliskan_doukas_2015/data/raw/compustat/funda_population_keys_all.csv.gz) | 3.52 | 补充并精确核对POPSRC来源 |
| [funda_population_keys_all.sql](../project/replications/caliskan_doukas_2015/data/raw/compustat/funda_population_keys_all.sql) | 0.00 | 补充并精确核对POPSRC来源 |
| [ccm_link_history_all.csv.gz](../project/replications/caliskan_doukas_2015/data/raw/crsp/ccm_link_history_all.csv.gz) | 1.25 | 历史SAS快照，仅保留来源，不作为实际CCM输入 |
| [ccmxpf_lnkhist_postgres_all.csv.gz](../project/replications/caliskan_doukas_2015/data/raw/crsp/ccmxpf_lnkhist_postgres_all.csv.gz) | 1.10 | CRSP–Compustat历史证券连接 |
| [ccmxpf_lnkhist_postgres_all.sql](../project/replications/caliskan_doukas_2015/data/raw/crsp/ccmxpf_lnkhist_postgres_all.sql) | 0.00 | CRSP–Compustat历史证券连接 |
| [dsf_all_2005-01-01_2024-06-30.csv.gz](../project/replications/caliskan_doukas_2015/data/raw/crsp/dsf_all_2005-01-01_2024-06-30.csv.gz) | 455.54 | 日度证券条件与255日RETX波动率 |
| [msf_all_2000-12_2024-06.csv.gz](../project/replications/caliskan_doukas_2015/data/raw/crsp/msf_all_2000-12_2024-06.csv.gz) | 36.07 | 月度股价、拆股因子、60个月波动率 |
| [anncomp_1992_2023_allfields.csv.gz](../project/replications/caliskan_doukas_2015/data/raw/execucomp/anncomp_1992_2023_allfields.csv.gz) | 41.48 | 年度CEO、年龄、任期、现金薪酬、持股及年度债务总额 |
| [anncomp_1992_2023_allfields.sql](../project/replications/caliskan_doukas_2015/data/raw/execucomp/anncomp_1992_2023_allfields.sql) | 0.00 | 年度CEO、年龄、任期、现金薪酬、持股及年度债务总额 |
| [deferredcomp_2006_2023_allfields.csv.gz](../project/replications/caliskan_doukas_2015/data/raw/execucomp/deferredcomp_2006_2023_allfields.csv.gz) | 4.87 | 递延薪酬明细审计，不能填补年度总额 |
| [deferredcomp_2006_2023_allfields.sql](../project/replications/caliskan_doukas_2015/data/raw/execucomp/deferredcomp_2006_2023_allfields.sql) | 0.00 | 递延薪酬明细审计，不能填补年度总额 |
| [outstandingawards_2006_2023_allfields.csv.gz](../project/replications/caliskan_doukas_2015/data/raw/execucomp/outstandingawards_2006_2023_allfields.csv.gz) | 23.53 | 逐笔期权数量、行权价、到期日及数量对账 |
| [outstandingawards_2006_2023_allfields.sql](../project/replications/caliskan_doukas_2015/data/raw/execucomp/outstandingawards_2006_2023_allfields.sql) | 0.00 | 逐笔期权数量、行权价、到期日及数量对账 |
| [pension_2006_2023_allfields.csv.gz](../project/replications/caliskan_doukas_2015/data/raw/execucomp/pension_2006_2023_allfields.csv.gz) | 3.22 | 养老金明细审计，不能填补年度总额 |
| [pension_2006_2023_allfields.sql](../project/replications/caliskan_doukas_2015/data/raw/execucomp/pension_2006_2023_allfields.sql) | 0.00 | 养老金明细审计，不能填补年度总额 |
| [DTB3_2005-01-01_2024-06-30.csv](../project/replications/caliskan_doukas_2015/data/raw/fred/DTB3_2005-01-01_2024-06-30.csv) | 0.08 | 三个月国债利率 |
| [DTB3_metadata.json](../project/replications/caliskan_doukas_2015/data/raw/fred/DTB3_metadata.json) | 0.00 | 三个月国债利率 |
| [ciq_wrds_gvkey_all.csv.gz](../project/replications/caliskan_doukas_2015/data/raw/linking_20261025/ciq_wrds_gvkey_all.csv.gz) | 2.78 | 官方CIQ公司—GVKEY连接 |
| [ciq_wrds_gvkey_all.sql](../project/replications/caliskan_doukas_2015/data/raw/linking_20261025/ciq_wrds_gvkey_all.sql) | 0.00 | 官方CIQ公司—GVKEY连接 |
| [people_link_execucomp_boardex_all.csv.gz](../project/replications/caliskan_doukas_2015/data/raw/linking_20261025/people_link_execucomp_boardex_all.csv.gz) | 1.39 | 官方BoardEx—ExecuComp人员连接 |

## 冻结分数与匹配的输入

- project/data/panel/risk_scores.parquet：29,506行既有Ridge/XGBoost分数。实际回归只用无_full的OOF分数，不重新训练。
- project/data/panel/ceo_firm_year_panel.parquet：源分数的panel_id、GVKEY、自然年、讲话者与会计日期等元数据；代码只读取匹配需要的列。
- project/data/panel/component_map.parquet：源面板与实际讲话component的逐行连接。
- project/data/replication_sample/transcript_identity.pickle.gz：原讲话数据中匹配实际使用的14个身份、日期和计数字段，保留全部原始行、原数据类型及对象值；未附讲话正文或ML特征。投影导出代码、来源SHA及逐值核验随包提供。该文件没有任何预先计算的最终匹配标记。

原始月度数据从2000年12月开始、日度从2005年开始，并保留到2024年上半年缓冲；财务和年度薪酬保留构造前置历史。不能只保留2006或2013以后再计算历史波动率、增长或CEO链接。

## 范围

本包从这些原始财务/证券/薪酬与身份连接输入重新筛选、构建变量、核验身份和财年时间，再估计全部25个当前模型。已有文本synthetic proxy of CEO risk preference及其源行定义是给定输入；讲话提取、主题训练和分数模型训练不属于本次复现步骤。
