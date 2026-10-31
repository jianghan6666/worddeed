# 从分数源记录重建CEO、公司与时间匹配

本包直接使用既有Ridge、XGBoost分数，不重新训练。这里的匹配代码会重新计算身份、日期及冲突守卫，不读取已经生成的最终匹配标记作为输入。财务变量与年度CEO基础目标先由原始WRDS数据重建。

## 输入数据

下列路径相对于本包根目录：

| 输入 | 用途 |
|---|---|
| `project/data/panel/risk_scores.parquet` | 原有29,506行分数表；包含原始OOF及其既有变换。回归采用无`_full`版本。 |
| `project/data/panel/ceo_firm_year_panel.parquet` | 源panel_id、GVKEY、自然年、主要讲话者、源会计日期、fold/group、组成讲话数及词数。 |
| `project/data/panel/component_map.parquet` | 1,420,208个实际组成分数的component到panel_id的映射，包含orig_idx。 |
| `project/data/replication_sample/transcript_identity.pickle.gz` | 原讲话源表的14列无损投影，保留全部1,775,355行、原行序、字段值、dtype及混合日期对象；用于重新计算人员、公司、姓名与全局冲突证据。 |
| `project/replications/caliskan_doukas_2015/data/raw/execucomp/anncomp_1992_2023_allfields.csv.gz` | 目标CEO姓名字段及年度原始身份信息。 |
| `project/replications/caliskan_doukas_2015/data/raw/compustat/funda_datadate_2003-01_2024-06.csv.gz` | 重建实际财政窗口边界。 |
| `project/replications/caliskan_doukas_2015/data/raw/linking_20261025/ciq_wrds_gvkey_all.csv.gz` | 官方公司连接表，145,303行、6列。 |
| `project/replications/caliskan_doukas_2015/data/raw/linking_20261025/people_link_execucomp_boardex_all.csv.gz` | 官方人员连接表，44,373行、16列，保留全部质量分数和匹配方式。 |
| `rerun/project/replications/caliskan_doukas_2015/data/processed/panel_master_audit.parquet` | 由本包财务/CEO重建阶段生成的35,151个年度目标。不是随包预先匹配好的结果。 |
| 同一`data/processed/`下三个`table4_b_*.parquet` | 从原始财务、证券与期权数据重建的三个年度B合格样本期间。 |

分数源面板及component映射属于既有分数的来源记录。分数已经固定，本包不重新选择讲话者、不移动分数到另一个公司、不重聚合非日历财年讲话。源面板初始公司关联使用过上游ticker/年份规则；下述Step 4接入与官方核验阶段使用GVKEY和正式ID证据，不把整个上游流程笼统称为从未使用ticker。

## 为什么原讲话数据使用身份列投影

冻结分数下的匹配只读取以下14列：

```text
orig_row companyid transcriptid transcriptpersonid directorid
transcriptpersonname execid exec_fullname companyname_execucomp
companyname mostimportantdateutc year retained_word_count proid
```

投影没有筛掉任何源行，也没有按CEO、公司或年度聚合。尤其全局CEO和transcriptpersonid冲突守卫需要全部1,775,355行；只给实际映射的1,420,208行会丢失守卫所需的其他来源证据。

混合的原始字符串/Timestamp日期对象保留在gzip pickle中，避免Parquet强制统一日期类型。`identity_projection_metadata.json`记录完整上游源文件SHA256、投影SHA256、行数、字段与逐值/dtype核验。可选脚本`code/extract_identity_source.py`公开投影过程。它需要上游完整讲话snapshot；日常复现本包匹配时直接使用已提供的无损身份投影，无需讲话正文或机器学习特征。

源`execid`等继承字段仍作为来源证据及冲突守卫保存。它们的更早赋值不在本次冻结分数的训练重建范围内；正式接纳还须通过下面的独立官方身份桥。官方ID配对也不等于人工认证每段讲话的原始人物标注。

## 第一阶段：重建本地身份及时间证据

代码：`code/matching/local_match.py`。

1. 核对分数与源面板的panel_id、GVKEY、ceo_id、year逐值相同；要求源panel_id以及GVKEY–year唯一。
2. 从全部身份源行重建`ceo_id`，以及同一源CEO ID、transcriptpersonid是否关联多个不同ExecuComp execid的全局冲突。
3. 按orig_idx→orig_row一对一连接实际component映射，核对transcriptid、词数、源CEO和年份，再重建每个panel的全部公司/人物ID集合、姓名集合、讲话最早/最晚日、component数量、transcript数量和词数总和。
4. 目标单位为`gvkey+fyear`，附该财年所选年度/FYE CEO。用规范化六位GVKEY和年度标签作一对一候选连接。相同公司年份本身不足以认定同一CEO或同一期间。
5. 保存源/目标会计日期是否相同、继承execid是否唯一且相同、姓氏与名字首字母是否支持，以及全局人员/公司冲突等标记。公司名称支持仅作诊断，不替代正式ID。
6. 实际财年开始为前一连续财年末加1日。讲话的最早和最晚日期须位于实际财年内；已知BECAMECEO须不晚于最早讲话，已知LEFTOFC须严格晚于最晚讲话。未知任职边界单独标记。
7. 严格期间另要求源自然年1月1日至12月31日与实际财年完整起止一致，不作跨年平移。

该阶段保留旧继承身份验收标记供审计，但它不是当前正式回归的最终接纳条件。

## 第二阶段：官方公司和CEO桥核验

代码：`code/matching/official_match.py`。

**公司：**从每个实际component的companyid及讲话日期重建全部请求，并加入源会计日期请求。对每次请求，使用官方CIQ–GVKEY桥，只接受日期兼容且唯一映射到原目标GVKEY的情况。边界含端点；缺失起止边界按无界处理。这是兼容性约定，不是已认证完整历史有效期。一个源panel出现多个公司、不同GVKEY、同日多个GVKEY或无有效链接，都保留原因而不以多数票代替。

**人员：**检查所有实际component的BoardEx directorid。当前验收要求人物ID齐全、唯一，并且People Link的最高质量`score=1`层只对应一个execid，且与目标年度CEO一致。全部较低质量链接及其方式仍保留。这个门槛是本研究的保守选择，不是论文或WRDS规定的唯一用法。

`transcriptpersonid`、CIQ personid、professional proid是不同命名空间，不能按相同数字强配。缺少相应CIQ桥或只有低质量候选时继续拒绝/待核，不因希望提高覆盖率而自动接受。公司/人物桥没有覆盖更早源面板的标签构造，也不触发重新训练。

最终标记为：

```text
official_entity_verified = 公司桥通过
                         & 人员桥通过
                         & 原本地姓名/会计日/唯一ID/无冲突守卫通过
                         & 继承execid缺失或与目标execid一致

official_fiscal_compatible = official_entity_verified
                          & 所有讲话位于实际财年
                          & 无已知任职日期冲突

official_strict_period_match = official_fiscal_compatible
                            & 自然年与完整财年起止相同
```

只有正式接纳行得到对应`vendor_*`分数；严格行得到`vendor_strict_*`分数。未通过的正式分数保持缺失，绝不补0。负的合法OOF预测在后续回归输入构造时按`100×max(raw,0)`转换为百分点；这与匹配失败缺失不同。

## 执行与输出

在包根目录，先完成财务/CEO/证券/期权重建，再执行：

```text
python code/matching_stage.py --stage all
```

也可以使用同一入口的`--package-root`和`--run-root`。相对run-root以包根为基准。程序输出在：

```text
rerun/project/replications/caliskan_doukas_2015/data/matched/local/
rerun/project/replications/caliskan_doukas_2015/data/matched/official/
```

两个目录必须为新目录；脚本拒绝覆盖。正式阶段保留完整master、三个年度B附表、源官方身份、逐公司日期请求、连接原表行号证据、逐目标失败原因、未匹配及新增补证队列、字段字典和源/输出SHA256。不能只核对最终N，须同时核对逐ID标记、分数及来源证据。

目标2013–2023年度B合格样本预期7,086行；严格匹配输入预期2,967行。普通回归的纯组筛选后预期2,927行，对数相对杠杆设定先限正值得到1,727行，再按自己的纯组规则得到1,653行。这里列的是既有结果的核对基准，不是人为强制凑样本量的筛选参数。
