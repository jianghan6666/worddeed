# 原始财务数据、CEO筛选与变量构建

本说明只描述财务面板的原始数据重建。Ridge、XGBoost沿用既有OOF分数；分数的公司/人员/讲话窗口匹配以及回归由后续步骤执行，不在本财务构建步骤中训练任何模型。

## 原始输入与查询记录

原始输入位于包内 `project/replications/caliskan_doukas_2015/data/raw/`。保留完整原下载文件、SQL/查询元数据、字段说明及下载核验记录，不先根据最终回归样本裁剪原始表。

| 数据 | 使用的原始文件 | 作用 |
|---|---|---|
| ExecuComp Annual Compensation | `execucomp/anncomp_1992_2023_allfields.csv.gz` | 年度CEO、身份、任职日期、年龄、现金薪酬、普通股、年度期权数量、内部债务总额 |
| ExecuComp Outstanding Awards | `execucomp/outstandingawards_2006_2023_allfields.csv.gz` | CEO逐笔期权数量、行权价、到期日、奖励ID与身份核验 |
| ExecuComp Pension | `execucomp/pension_2006_2023_allfields.csv.gz` | 年度养老金总额的明细核对；不作为年度缺失值的填补来源 |
| ExecuComp Deferred Compensation | `execucomp/deferredcomp_2006_2023_allfields.csv.gz` | 年度递延余额的明细核对；不作为年度缺失值的填补来源 |
| Compustat Fundamentals Annual | `compustat/funda_datadate_2003-01_2024-06.csv.gz` | 当期财务、财政年末、历史行业、每股股利以及所需前置三年财务历史 |
| Compustat population补充表 | `compustat/funda_population_keys_all.csv.gz` | 精确补充POPSRC，核验原财务文件的每一行后限定D |
| CRSP–Compustat历史连接 | `crsp/ccmxpf_lnkhist_postgres_all.csv.gz` | 财年末有效的GVKEY–PERMNO链接；不是旧SAS快照 |
| CRSP月度 | `crsp/msf_all_2000-12_2024-06.csv.gz` | 连续61个月末复权价格，构造60个月收益波动率 |
| CRSP日度 | `crsp/dsf_all_2005-01-01_2024-06-30.csv.gz` | 全市场实际收益日期、255日收益波动和历史证券类型/交易所 |
| FRED DTB3 | `fred/DTB3_2005-01-01_2024-06-30.csv` | 财年末当日或之前最近的非缺失三个月国债率 |

十个实际财务构建源文件合计578,911,787字节。包内可能另外保留旧CCM、官方身份桥等来源材料；财务模块明确读取上表文件，不能仅凭文件名相似替换源表。

## 执行顺序与可移植入口

入口为 `code/finance_stage.py`。默认读取上述只读原始文件，输出到 `rerun/project/replications/caliskan_doukas_2015/`。

```text
python code/finance_stage.py
```

默认依次执行五阶段：

1. `prepare`：原财务处理、年度CEO与财政年末任职识别、有效CCM选择、无前视国债率对接，输出 `data/interim/base_panel.parquet` 与市场请求。
2. `market`：从原CRSP日/月CSV重建全市场日期和历史波动，输出 `data/interim/market_inputs.parquet`。
3. `valuations`：将财务/CEO与市场输入组织为逐CEO估值输入。
4. `options`：读取全部相关原始奖励、核对年度数量并逐笔估值，输出组合和奖励明细审计。
5. `finalize`：构造财富/相对杠杆、计算Size参考百分位、执行完整案例与资格筛选，输出公司财年主审计表、各期间B表和逐步损耗。

也可以指定 `--stage prepare|market|valuations|options|finalize`，但后段必须已有同一输出根下的前段结果。`--run-root`表示输出根，实际财务结果保存在其 `project/replications/caliskan_doukas_2015/` 子目录，不会写回包内原始数据或历史结果。

首次执行不依赖预先生成的CRSP缓存。`market`会扫描36,618,473条原始日度记录，用全市场有效RETX生成日历，之后把请求证券分为64个Parquet桶。缓存只写在生成目录的 `data/interim/market_cache/` 中；清单标记为未完成的中断缓存不会被当成有效输入。后续重复运行可能使用同一原始文件SHA和请求证券签名对应的完整缓存；其是否预先存在会写入 `audits/FINANCE_STAGE.json`。

## 财务表与CEO选择

原Compustat查询采用INDL/STD/C/USD，保留active与inactive。POPSRC补充连接键为GVKEY、DATADATE、INDFMT、CONSOL、DATAFMT、CURCD；要求一对一且每行均能匹配，再保留D。对一个GVKEY–FYEAR有多条财务记录的情况，整组排除，不任取最新一行。

ExecuComp先保留2006–2023年度 `CEOANN='CEO'`。结合财年末选择唯一在任者：已知BECAMECEO不能晚于财年末，已知LEFTOFC须严格晚于财年末。开始日等于财年末可以入选，离任日等于财年末则排除。多名候选不能唯一确定时不随意选择。缺失BECAMECEO可暂进入候选，但随后对数任期缺失，无法满足最终完整案例资格。没有增加PCEO筛选。

一行键为六位GVKEY和FYEAR；选定CEO以EXECID和CO_PER_ROL保留。源筛选全过程写入 `audits/ceo_selection_audit.parquet`，包括没有进入最终面板的候选。

用历史SICH限定有效100–9999行业，排除4900–4999公用事业与6000–6999金融业。缺SICH不使用当前SIC补回。资产和市场权益均须为正。

CCM只保留LC/LU、P/C及正PERMNO，要求LINKDT不晚于财年末，LINKENDDT不早于财年末；原始E或缺失LINKENDDT按开放末端处理。同一公司财年若有效候选对应多个不同PERMNO则排除。证券要求普通股10/11、交易所1/2/3，并在财年末对应最近市场日期仍有有效证券记录。

## 市场与期权输入

`sigma60`使用财年末所在月之前61个连续月末的 `abs(PRC)/CFACPR`，形成60个月度对数价格变化，样本标准差乘√12。缺失月份不向更早历史补齐。

`retvol255`使用严格早于财年末的255个全市场有效收益日期，取该PERMNO的RETX样本标准差乘100，不年化。需要全部255个有效收益，不用更早有效收益代替缺口。CRSP非数值缺失码、非有限收益和RETX<-1保留缺失；只有事件记录但全市场没有有效经济收益的日期不进入市场日历。

股息收益输入为前三个连续财政年 `DVPSX_F/PRCC_F` 的均值再取log1p，三年均须有效。国债率为财年末之前最近有效DTB3，转为 `r=log1p(DTB3/100)`，不使用未来观察。`T=(到期日−财年末).days/365.25`，股价S与行权价X均为实际美元。

逐笔含股息Black–Scholes–Merton估值同时计算期权价值、股价上升1%的Delta和波动率上升1个百分点的Vega。零到期、零波动和零行权价采用代码显式极限；负到期、负数量或其他无效输入不能直接估值。

原数量单位为千股/千份，先乘1000再估值。所有正数量期权tranche必须估值有效、身份相符、奖励ID不缺且不重复。年度已归属可行权/未归属不可行权数量必须披露，并分别与明细在0.01千份内核对；未获收益期权独立纳入全部组合。明细数量类别的结构性缺失在合计时按0，但年度总数量、行权价、到期日、年度债务缺失不会因此补0。股票或非期权奖励行中的身份/键冲突也可能触发组合失败。

年度B使用普通股持有量SHROWN_EXCL_OPTS×1000×S加期权价值，不额外再加未归属股票；股票直接Vega为0。B的股票Delta为0.01×股数×S，与期权1%股价敏感度同尺度。金额、Delta、Vega组合均逐笔保留审计。

## 主要回归变量与缺失规则

| 变量 | 构建规则与尺度 |
|---|---|
| payer | 1(DVPSX_F>0)；每股股利缺失不当作0 |
| cash_m | (SALARY+BONUS)/1000，百万美元 |
| inside_debt_m | (DEFER_BALANCE_TOT+PENSION_VALUE_TOT)/1000，百万美元；年度两项均须有效 |
| equity_m | B普通股财富加全部期权价值，美元除1e6 |
| vega_k | B全部期权Vega，美元除1000；单位为千美元/波动率1pp |
| rellev | (inside_debt_m/equity_m)/(LT/(PRCC_F×CSHO))；分母是公司总负债/市场权益 |
| ln_rellev | ln(rellev)，仅严格正值；零内部债务可留普通模型，不补log1p |
| high_rellev | 1(rellev>1) |
| age | 年度AGE，不使用当前年龄PAGE |
| ln_tenure | ln[1+floor((DATADATE−BECAMECEO).days/365.25)] |
| rd_at_pct / rd_missing | 100×XRD.fillna(0)/AT；missing dummy在补0前生成 |
| capx_at_pct | 100×CAPX/AT；缺CAPX不补0 |
| asset_growth | (AT−前一连续财政年AT)/前一年AT；decimal ratio，要求前一会计日期早于当前 |
| mb | 市场权益/账面权益。股东权益依次SEQ、CEQ+PSTK、AT−LT；优先股权益依次PSTKL、PSTKRV、PSTK；BE=股东权益−优先股权益+TXDITC。负而有限BE保留，零/缺分母设缺失，不把组成缺项补0 |
| profitability_m | IB−DVP+TXDITC，沿用Compustat百万美元，不除以资产 |
| size_pct | 财年内base-eligible参考组中市场权益严格小于本行的数量/N×100；并列值使用min rank，不在后期/匹配子样本重算 |
| re_at | RE/AT，decimal ratio |
| retvol255 | 上述255个真实市场日期RETX样本标准差×100 |

除明确的实际XRD处理外，所需变量缺失不会自动补0。当前回归移除了Delta/Vega项，但基础B资格仍要求正Vega、有限DVR及相应财富/杠杆可定义；删除回归项不放宽既有入样资格。

年度B最终资格依次为：有效财务、行业、正资产/市值、唯一CCM、美国普通股上市、完整控制、有效现金与非负内部债务、完整期权组合、有效B指标。逐行首次失败原因保存在 `audits/sample_selection_audit.parquet`；累计损耗见 `reports/sample_attrition.csv`。Size参考组早于完整案例，不能先删缺失再重算Size。

原历史构建模块内部还计算A版和A/B交集标记，以保持B表中既有样本字段和审计与冻结文件一致；本包第二阶段回归只选择年度B，不因此估计A或PCEO模型。

## 从原始数据重建后的验证

`code/verify_finance.py`仅在构建完成后读取 `reference/finance/` 的冻结文件，用于比较，不参与构造。它核对三期B表、完整主审计面板、CEO选择、逐行筛选、市场窗口和期权组合共8份文件的全部行/列，报告精确ID、字符/日期/标记值以及各数值列误差和是否逐值完全相同。

```text
python code/verify_finance.py
```

结果写在生成目录 `audits/FINANCE_REPRODUCTION_CHECK.json`。CSV/Parquet物理字节可能受版本、压缩或元数据影响；比较数据值而不是文件字节才是重建等价性的主要判断。

三个历史财务源脚本原文保存在包内。包装器仅在内存中改写三个来源清单的路径序列化表达式，使只读原始输入和生成目录可以分离；筛选、公式、窗口、估值与数据值计算没有修改。准确替换式、源SHA、适配后代码文本SHA及阶段耗时记录在 `audits/FINANCE_STAGE.json`。
