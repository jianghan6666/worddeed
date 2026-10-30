# 从原始数据复现 Table 4：完整协作包

发布：2026-10-27。此文件夹是独立的新版本，保留此前精简Step 4包不动。

本包包含原始财务、薪酬、期权、证券、利率及官方身份连接数据；从这些输入重新筛选年度CEO、计算财务/市场/期权变量、匹配已有Ridge和XGBoost分数，再重新估计当前Excel的全部25个自有模型。**synthetic proxy of CEO risk preference直接读取既有OOF分数，不重新训练。**

## 先看结果与说明

- [完整Excel](results/table4_annual_b_tables.xlsx)：与原主文件逐字节相同，保留所有5个工作表。
- [完整结果网页](results/TABLE4_TABLES.html)：发布时的冻结展示。
- [从原始数据重建后生成的结果](results/REPLAYED_TABLES.html)：已通过原表核验的新估计。
- [冻结分数版本](docs/FROZEN_SCORES.md)：OOF、截0、百分点和不重训的边界。
- [财务构建细节](docs/FINANCIAL_DATA_PIPELINE.md)：原始表、筛选、CEO选择、变量、期权与市场窗口。
- [从源身份数据重新匹配](docs/MATCHING_FROM_SOURCE.md)：公司、CEO、人员ID命名空间、财年及任期守卫。
- [原始数据清单](docs/RAW_DATA_INVENTORY.md)：各原始文件、用途、大小、SQL与下载元数据。
- [复跑范围和与精简包的区别](docs/SCOPE_AND_COMPARISON.md)。

## 环境

本地验证环境为Python 3.11、StataNow/SE 19.5。回归程序声明Stata 19.0语法，建议使用同版本19.5。Python的numpy/pandas/scipy/pyarrow已按实际验证版本固定。无需WRDS登录、互联网查询、原项目目录或ML模型文件。首次安装Python依赖时需要可用的安装源。

在本README所在目录打开终端，执行：

    python -m pip install -r requirements.txt

## 一个命令从原始数据完整运行

    python code/run_from_raw.py --stata-exe "C:/Program Files/StataNow19/StataSE-64.exe"

Stata在PATH或设置STATA_EXE环境变量时，可省略--stata-exe：

    python code/run_from_raw.py

程序依次执行：

1. 从原始Compustat/ExecuComp筛选年度CEO、匹配证券并计算财务变量。
2. 流式读取原始CRSP月度/日度数据，重新计算60个月波动率和255日收益波动率；重建所有期权组合估值、Delta/Vega、内部债务与年度B资格。
3. 读取已有score、源面板与逐讲话身份明细，从头生成本地身份审计，再使用官方公司和人员连接表核验公司、CEO、讲话日期、财年与任期窗口。
4. 将新构建数据与冻结参考作逐行核对；参考表仅用于验收，不用于构建或决定配对。
5. 从新数据生成25份Stata输入、重新做纯结果组筛选和数值尺度计算，估计OIM及公司GVKEY聚类Logit。
6. 对照原结果的系数、标准误、样本ID和模型信息，并生成新的HTML/Markdown回归表。

**全部生成文件写入rerun/，原始输入和results/reference保持不变。** 完整运行要求新输出目录。第二次运行可指定另一目录：

    python code/run_from_raw.py --run-root rerun_second

若暂时没有Stata，只重建数据、匹配和回归输入：

    python code/run_from_raw.py --stage data

分阶段继续执行，例如数据阶段完成后运行回归：

    python code/run_from_raw.py --stage estimate --stata-exe "C:/Program Files/StataNow19/StataSE-64.exe"

单独重跑某阶段可使用--stage finance、matching、models、verify或report；matching和models拒绝覆盖已有产物。请优先使用新--run-root完整重跑。中途失败后，先查看rerun/logs及FULL_PIPELINE_STATUS.json；不应把失败末解当作完成。

## 运行后检查什么

| 生成路径（均相对rerun） | 内容 |
|---|---|
| FULL_PIPELINE_STATUS.json | 各阶段状态、日志和运行耗时 |
| project/replications/caliskan_doukas_2015/data/processed/ | 从原始数据重建的公司年度与年度B分析表 |
| project/replications/caliskan_doukas_2015/audits/ | CEO筛选、市场、期权组合、样本损耗及FINANCE_REPRODUCTION_CHECK.json |
| project/replications/caliskan_doukas_2015/data/matched/local/ | 由所有原始身份行重新生成的本地匹配与冲突审计 |
| project/replications/caliskan_doukas_2015/data/matched/official/ | 官方公司/人员/日期证据、匹配去向和严格分数表 |
| matching_reproduction_check.json | 全部源身份及目标配对、严格匹配分数的参考对照 |
| regression/audit/PREPARATION_QA.json | 新数据生成模型设计、尺度和样本的核验 |
| regression/stata/coefficients.csv、model_summary.csv | 重新估计的全部25模型结果 |
| regression/audit/REGRESSION_REPLAY_QA.json | 系数、SE、LL、N/G和e(sample)逐ID核验 |
| regression/tables/REPLAYED_TABLES.html、.md | 根据本次新估计生成的7个自有结果面板 |

完整Excel是冻结参考，不会被运行程序覆盖。新HTML/CSV是本次重建后估计的输出；原论文已发表的一页是文献参考，不会被重新估计。

## 目录与数据边界

| 目录 | 内容 |
|---|---|
| project/replications/caliskan_doukas_2015/data/raw/ | 原始下载文件、SQL、字段与查询元数据；保持下载字节 |
| project/data/panel/ | 已有score及其源面板/逐讲话连接表，仅读取，不训练 |
| project/data/replication_sample/ | 原讲话数据中匹配用到的14字段，保留全部177万余行、原类型与原值；gzip压缩，未按最终样本过滤 |
| code/ | 可移植总入口、构建/匹配适配器、模型生成及验证程序 |
| project/replications/caliskan_doukas_2015/scripts/ | 未修改的原分析脚本归档，由适配器调用；不要直接按历史绝对路径示例运行 |
| reference/ | 发布时的冻结数据与结果，仅用于核验，以及历史完整实现说明 |
| results/ | 原完整Excel及冻结展示 |
| docs/ | 当前包的来源、规则、匹配、环境及边界说明 |
| audit/ | 本包实际从原始输入重建和估计的验收证据 |
| provenance/ | 来源SHA、无损投影信息与适配代码的修改范围 |

讲话正文、主题/情绪特征生成和Ridge/XGBoost训练不在本次运行范围。已有score及其源面板定义是给定输入；匹配需要的全部未聚合身份记录已随包提供。不存在用最终匹配标记直接代替重新匹配的步骤。

## 文件完整性

    python code/verify_package.py

该检查使用Python标准库，逐文件核验manifest中的大小和SHA256；无需安装分析依赖。数据来自有使用条件的供应商，限有相应数据使用资格的研究协作，请勿将本包作为公开数据集发布。

