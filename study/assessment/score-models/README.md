# Step 4 合作者复现包

发布：2026-10-27。范围：原工作簿第3页 **3 No actual RD** 与第4页 **4 With actual RD**，共16个模型。

**两组都包含预测的Ridge或XGBoost synthetic proxy of CEO risk preference。区别是是否控制实际R&D/资产，以及其缺失指示变量。** 两种预测分数分别回归。

## 先看什么

- [结果Excel](results/step4_score_tables.xlsx)：只有指定的两张工作表。
- [可直接打开的结果网页](results/RESULTS.html) / [结果Markdown](results/RESULTS.md)：完整四个面板、全部列示系数及公司聚类标准误。
- [研究报告](docs/REPLICATION_REPORT.md)：研究问题、主要结果、原论文联系与解释边界。
- [实现与匹配方法](docs/METHODS_AND_MATCHING.md) / [数据字典](docs/DATA_DICTIONARY.md)：研究单位、变量、CEO/公司/财年对接及删行处理。

## 直接复跑

1. 解压整个文件夹，保留子目录结构。不要在压缩包内部运行。
2. 在Stata中把工作目录设为本README所在目录。
3. 执行：

    do code/01_run_stata.do

程序读取随包提供的16份原始精度Stata输入，重新执行纯结果组筛选、OIM Logit及公司聚类Logit，结果写入新建的 **rerun/stata/**。原有 **reference/**、**results/** 和 **data/** 保持不变。第一次运行前无需WRDS、网络连接、原项目目录或ML模型文件。再次运行会覆盖rerun/stata中的上次复跑输出。

Stata版本以随包核验记录为准，原结果由Stata 19.5生成。该程序使用内置命令，不依赖第三方ado。程序使用数值缩放改善求解，导出的系数、SE和协方差均还原到下文原单位；.ster内参数仍对应缩放后的z变量，读其结果时须按模型配置映射。

可选的Python核验（仅标准库，无须安装pandas）：

    python code/00_verify_package.py
    python code/02_check_stata.py

第一条检查随包文件SHA256。第二条在Stata运行结束后，核对16个模型的系数、两种SE、p值、似然、N、公司数和实际估计样本ID。复跑后看 **rerun/stata/REPLAY_CHECK.json**。

## 数据与模型

| 项目 | 内容 |
|---|---|
| 研究单位 | 一行=公司GVKEY—财年，附该财年选定的ExecuComp CEO |
| 期间与口径 | 2013–2023年，年度CEO B，严格公司/人员/完整财年窗口匹配 |
| 严格输入 | 2,967行、600家公司 |
| 普通实际样本 | (8)/(10)/新增基准：2,927行、591家公司 |
| 对数设定样本 | (9)：正相对杠杆输入1,727行，实际1,653行、340家公司 |
| 因变量 | payer=1(DVPSX_F>0) |
| 预测分数 | 100×max(无_full的OOF预测R&D/资产,0)，单位：百分点 |
| 第二阶段 | 无惩罚Logit，截距、SIC2行业和财年虚拟变量，公司GVKEY单向聚类 |
| 第3页 | 不放实际R&D/资产，也不放R&D缺失指示变量 |
| 第4页 | 同时放实际R&D/资产和R&D缺失指示变量 |

每页：XGBoost与Ridge各做(8)、(9)、(10)和新增无内部债务/Vega基准，共8个模型。所有模型都不含Delta/Vega回归项；原年度B入样资格保持，删掉回归项没有放宽基础资格。详细解释变量和精确设计列见 [model_specifications.json](code/model_specifications.json)。

## 文件索引

| 路径 | 用途 |
|---|---|
| data/analysis_strict_2967.csv / .parquet | 同一份精简可读分析表，保留CEO身份、两个原始OOF分数、最终分数、控制变量与匹配时间信息 |
| data/score_provenance_2967.csv | 回归分数与源panel_id、分折/分组及CEO/公司键的逐行映射 |
| data/stata_inputs/ | 16个模型的冻结DTA输入，逐字节保持原精度 |
| code/01_run_stata.do | 只运行这16个模型的相对路径Stata入口 |
| reference/coefficients.csv / model_summary.csv | 冻结的权威Stata结果，含全部行业/年份虚拟变量项 |
| reference/samples/ | 每模型筛选记录及实际e(sample)，用于逐ID对照 |
| reference/estimates/ | 16份原公司聚类估计ster；对应缩放变量，见方法说明 |
| audit/target_b_2013_2023_matching_disposition.csv | 7,086个基础目标的逐行匹配去向及普通/对数样本标记 |
| audit/coverage*.csv / unmatched_and_excluded_reasons.csv | 覆盖、逐年样本量及失败原因 |
| audit/REPRODUCIBILITY_QA.json | 整体交付核验及实际复跑范围 |
| provenance/source_file_map.csv | 来源相对路径、复制/投影方法及源SHA256，仅用于来源追溯 |
| manifest.json | 本包全部静态文件大小和SHA256 |

CSV为UTF-8（数据CSV带BOM），缺失值为空。GVKEY、event_id和其他标识应按文本读取，保留前导0；推荐直接读取Stata输入或Parquet。不要把未匹配Score补0。合法负预测截0后取值0属于有效观测。

## 复现边界

本包自足地复跑**给定冻结文本分数与已处理财务变量后的第二阶段Step 4回归**。第一阶段的讲话处理、主题模型与Ridge/XGBoost训练，以及从WRDS原始日度/月度/期权表重新构建财务变量，属于上游步骤，本包保留说明和输入来源，不包含其完整重建材料。所有实际第二阶段回归输入均已包含。

本包不包含原论文表、原研究2006–2011/扩展窗口的无预测Score复现模型，也不包含其他实验或内部协作记录。研究报告中的原论文比较仅提供理论背景。

数据来自WRDS/Compustat/CRSP/ExecuComp及链接产品，随包数据用于有相应数据使用资格的研究协作，请勿作为公开数据集发布。

16个Score系数均为负且公司聚类p<0.01。该结果是冻结生成分数的条件关联，不能单独确认心理风险偏好的测量效度或因果关系。第一阶段估计不确定性未通过重训bootstrap计入当前SE。

