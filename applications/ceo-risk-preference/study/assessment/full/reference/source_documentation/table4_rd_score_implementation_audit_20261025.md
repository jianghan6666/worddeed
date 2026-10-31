> Historical implementation snapshot. Machine paths and examples below are archival. Use the package root README for the current portable entry point.

# synthetic proxy of CEO risk preference回归实现审计：3 No actual RD 与 4 With actual RD

核查日期：2026-10-25（America/New_York）。操作者：Codex。本文只读整理当前工作簿这两页的源分数、CEO/公司匹配、样本覆盖和模型实现；没有重新下载、重匹配、重训、构建回归变量或重新估计，也没有修改工作簿、源分数和既有结果。

全文以实际文件、代码和逐行审计为依据。匹配和估计的历史执行，与本轮重新计数/数值回读，在下文分别说明。重点是明确每个分母、每条守卫以及未进入模型的观测去向。

## 目录

1. [范围、版本和工作表定位](#sec-1)
2. [研究单位与文件链](#sec-2)
3. [数据来源与下载快照](#sec-3)
4. [目标年度CEO及基础B样本如何形成](#sec-4)
5. [源synthetic proxy of CEO risk preference如何形成](#sec-5)
6. [公司、CEO身份如何匹配](#sec-6)
7. [自然年、实际财年与任期日期如何对齐](#sec-7)
8. [覆盖程度、逐年覆盖与互斥损耗](#sec-8)
9. [未匹配观测如何保存与处理](#sec-9)
10. [两页精确模型、变量、样本与FE](#sec-10)
11. [估计方法、标准误与Excel数值来源](#sec-11)
12. [版本传承、本轮核验与局限](#sec-12)
13. [逐行回溯和具体例子](#sec-13)
14. [文件索引与重跑边界](#sec-14)

<a id="sec-1"></a>

## 1. 范围、版本和工作表定位

当前对象为 主工作簿 (historical source reference: D:/pc_workspace_local/ceo_risk_taking/outputs/01a17125-70eb-72b1-abff-27491f3aec3e/table4_annual_b_tables.xlsx) 的两页，共16个Logit设定。

| 工作表 | 分数面板 | 系数及SE区域 | 四列设定 |
|---|---|---|---|
| 3 No actual RD | XGBoost | B7:E40 | (8)、(9)、(10)、No debt/Vega |
| 3 No actual RD | Ridge | B55:E88 | 同上 |
| 4 With actual RD | XGBoost | B7:E44 | 同上 |
| 4 With actual RD | Ridge | B59:E96 | 同上 |

以上列出系数与标准误区域。第3页不放实际R&D/资产及R&D missing indicator；第4页同时保留两者。两种score分别入模，所有模型使用年度CEO B、2013–2023年，均已按用户要求删除Delta/Vega回归项。

当前工作簿SHA256：`8f3df019e71f2c3d5b8281e51d3fc59936fe0fef5518b45a5f1686843ac1ae40`。本轮逐格核对496个系数/公司聚类SE数值及全部星号，并另核对160个模型信息单元格（N、公司数、FE、LL、pseudo-R²等，含文字字段），均与冻结payload完全相同。ZIP内保留的R18历史工作簿SHA以`8ca0ad7f`开头；当前主文件后来有第2页备注/格式另存差异，但这两页数值保持。本次没有修改任一版本。

快速口径：从2013–2023年已合格年度B的7,086个firm-year出发，官方严格同窗口匹配输入为2,967行/600家公司/771名不同execid；普通列实际2,927行/591公司/760名CEO；(9)实际1,653行/340公司/441名CEO。这不是全美上市公司或全美CEO的覆盖率。

<a id="sec-2"></a>

## 2. 研究单位与文件链

本文路径约定：

```text
ROOT = D:/pc_workspace_local/ceo_risk_taking
REP  = ROOT/replications/caliskan_doukas_2015
RUN  = REP/results/table4_compilation_rep_2013_2023_20261025
MATCH= REP/data/matched/rd_scores_wrds_20261025
AUD  = REP/audits/score_tables_documentation_20261025
```

当前两页的回归使用 `data/matched/rd_scores_wrds_20261025/annual/table4_b_extended_2006_2023_rd_scores.parquet` 衍生的年度CEO B严格同窗口子样本。它在原Table4 firm-year上新增证据和分数列，并没有把原回归表改成每个讲话者一行。

目标表在 `gvkey + fyear` 上唯一，另已有该firm-year选定的ExecuComp CEO `execid`、角色 `co_per_rol`、财年末 `datadate`。公司×财政年是最终一行的单位，CEO身份是这行的必要匹配属性；`event_id` 表示公司年度，`valuation_id` 另包含选定CEO。源score表在 `panel_id` 和 `gvkey + year` 上唯一，源 `year` 是讲话自然年；源面板在同一公司年度中保留上游选定的一位讲话者。

旧本地程序 `scripts/match_rd_scores.py:34–49, 87–101` 断言score与源面板的四键 `panel_id, gvkey, ceo_id, year` 逐行一致，且原master没有重复firm-year。先将GVKEY统一为保留前导零的六位字符串，用目标 `gvkey,fyear` 对源 `gvkey,score_year` 做 `left merge(validate='1:1')`，生成 `score_key_match`。这只是同公司/年份标签候选，不足以证明同一CEO或同一时间窗口。

在本次score接入Table4这一步，没有用ticker连接、没有仅以CEO-year跨公司转移score、没有姓名模糊匹配后自动赋分，也没有在同年CEO变更时把另一位CEO的分数平均或搬给财年末CEO。候选不符合所选CEO时保留为拒配/待核行。

完整文件链是：

```text
原讲话component + topic density + 源Compustat
  → ceo_firm_year_panel / component_map
  → risk_scores.parquet（29,506个源公司自然年、所选主讲话者）
  → 旧本地逐component身份与时间审计
  → WRDS官方公司/BoardEx人员核验：MATCH/annual/...parquet
  → official_strict_period_match：2,967行
  → RUN/input/score_annual_b_2013_2023.parquet（冻结同一输入）
  → (9)正相对杠杆限制 / 各类纯组剔除
  → Stata与Python保存结果、e(sample)、table_payload
  → 当前Excel两页（外部固定估计结果）
```

公司年度唯一并不表示每位CEO仅有一年，也不表示每家公司只出现一次。表中公司数G按GVKEY去重、CEO数按execid去重；跨年公司和CEO总数不可由逐年数量直接相加得到。

<a id="sec-3"></a>

## 3. 数据来源与下载快照

### 3.1 基础复制研究原始资料

| 用途 | 原始文件（REP/data/raw下） | query | 原始行×列 | 覆盖 | 下载UTC |
| --- | --- | --- | --- | --- | --- |
| 年度薪酬/CEO/债务/持股 | execucomp/anncomp_1992_2023_allfields.csv.gz (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/data/raw/execucomp/anncomp_1992_2023_allfields.csv.gz) | 11827426 | 364,196×107 | 财年1992–2023 | 2026-10-24 19:21:21.698 |
| 逐笔期权奖励 | execucomp/outstandingawards_2006_2023_allfields.csv.gz (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/data/raw/execucomp/outstandingawards_2006_2023_allfields.csv.gz) | 11827427 | 1,245,777×50 | 财年2006–2023 | 2026-10-24 19:22:45.396 |
| 养老金明细（核对） | execucomp/pension_2006_2023_allfields.csv.gz (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/data/raw/execucomp/pension_2006_2023_allfields.csv.gz) | 11827430 | 109,154×44 | 财年2006–2023 | 2026-10-24 19:23:51.086 |
| 递延薪酬明细（核对） | execucomp/deferredcomp_2006_2023_allfields.csv.gz (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/data/raw/execucomp/deferredcomp_2006_2023_allfields.csv.gz) | 11827432 | 111,504×46 | 财年2006–2023 | 2026-10-24 19:25:09.270 |
| Compustat年度财务 | compustat/funda_datadate_2003-01_2024-06.csv.gz (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/data/raw/compustat/funda_datadate_2003-01_2024-06.csv.gz) | 11827424 | 200,950×35 | DATADATE 2003-01至2024-06 | 2026-10-24 19:19:45.771 |
| POPSRC补充键 | compustat/funda_population_keys_all.csv.gz (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/data/raw/compustat/funda_population_keys_all.csv.gz) | 11827497 | 942,621×9 | 全表键与状态 | 2026-10-24 20:01:53.541 |
| 历史CCM | crsp/ccmxpf_lnkhist_postgres_all.csv.gz (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/data/raw/crsp/ccmxpf_lnkhist_postgres_all.csv.gz) | 11827499 | 123,388×8 | 历史链接至2026快照 | 2026-10-24 20:02:20.795 |
| CRSP月度 Legacy SIZ | crsp/msf_all_2000-12_2024-06.csv.gz (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/data/raw/crsp/msf_all_2000-12_2024-06.csv.gz) | 11827433 | 2,132,669×15 | 2000-12至2024-06 | 2026-10-24 19:25:53.371 |
| CRSP日度 Legacy SIZ | crsp/dsf_all_2005-01-01_2024-06-30.csv.gz (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/data/raw/crsp/dsf_all_2005-01-01_2024-06-30.csv.gz) | 11827435 | 36,618,473×11 | 2005-01至2024-06 | 2026-10-24 19:29:12.824 |
| FRED DTB3/H.15 | fred/DTB3_2005-01-01_2024-06-30.csv (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/data/raw/fred/DTB3_2005-01-01_2024-06-30.csv) | 不适用 | 5,085×2 | 2005-01至2024-06 | 2026-10-24 19:18:04.910 |

以上为历史下载元数据所记UTC，不是本轮新下载。原始表行数不能相加当研究样本量。当前用Postgres CCM，另存legacy CCM是历史副本。日/月数据为CRSP Legacy SIZ，未当成CIZ；其SAS表单没有SQL下载，查询payload与字段在stock_download_metadata.json，其他可下载原SQL仍保存。

ExecuComp原下载没有先筛CEO/行业/当前指数/仅active；这些筛选在后续构建。Compustat下载用consol=C、indfmt=INDL、datafmt=STD、curcd=USD、costat=A/I，DATADATE截止2024年6月；随后按原六键补POPSRC并筛D。没有额外fic=USA或指数/规模限制。USD/INDL/POPSRC D不能解释为美国注册，后续采用CRSP美国主要交易所普通股口径。

前置财务用于连续三年股息率、前一年资产，前置月度用于60个月波动，前置日度用于255个交易日波动；2024上半年缓冲用于fyear2023但实际FYE在2024的公司。这些公司可能符合基础B，但当前score严格完整窗口还会进一步限制。

### 3.2 官方身份桥

| 官方桥 | 原始文件 | query | 行×列 | 下载UTC |
| --- | --- | --- | --- | --- |
| CIQ公司→GVKEY | ciq_wrds_gvkey_all.csv.gz (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/data/raw/linking_20261025/ciq_wrds_gvkey_all.csv.gz) | 11828375 | 145,303×6 | 2026-10-25T04:47:52.162Z |
| ExecuComp→BoardEx | people_link_execucomp_boardex_all.csv.gz (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/data/raw/linking_20261025/people_link_execucomp_boardex_all.csv.gz) | 11828366 | 44,373×16 | 2026-10-25T04:47:52.162Z |

公司桥为全表全6字段、无公司/日期/primaryflag预筛；People Link保留全库全部质量score与matchStyle。公司桥原SQL已保存；People Link为SAS wrapper，没有可下载SQL，不能声称两桥都取得原SQL。元数据和原始SHA见 acquisition_metadata.json (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/data/raw/linking_20261025/acquisition_metadata.json)。

### 3.3 源讲话、topic与score

| 用途 | 本地文件 |
| --- | --- |
| 源配置 | configs/paths.yaml (historical source reference: D:/pc_workspace_local/ceo_risk_taking/configs/paths.yaml) |
| 源Compustat | compustat_fundamentals_annual_2010-2025.csv (historical source reference: D:/pc_workspace_local/ceo_risk_taking/data/ceo_and_firm/compustat_fundamentals_annual_2010-2025.csv) |
| component回溯pickle | transcripts_is_ceo.pickle (historical source reference: D:/pc_workspace_local/ceo_risk_taking/data/replication_sample/transcripts_is_ceo.pickle) |
| topic密度 | topic_distr_Full_wNoIdeoLabel.npz (historical source reference: D:/pc_workspace_local/ceo_risk_taking/data/topic_density/13-23_354Tpoics/topic_distr_Full_wNoIdeoLabel.npz) |
| CEO公司自然年面板 | ceo_firm_year_panel.parquet (historical source reference: D:/pc_workspace_local/ceo_risk_taking/data/panel/ceo_firm_year_panel.parquet) |
| component到panel映射 | component_map.parquet (historical source reference: D:/pc_workspace_local/ceo_risk_taking/data/panel/component_map.parquet) |
| 源score与metadata | risk_scores.parquet (historical source reference: D:/pc_workspace_local/ceo_risk_taking/data/panel/risk_scores.parquet)；risk_scores.json (historical source reference: D:/pc_workspace_local/ceo_risk_taking/data/panel/risk_scores.json) |

源Compustat与第二阶段复制研究Compustat是两份数据来源；本轮已另外检查严格输入对应的R&D比率一致性，详见第12节。

<a id="sec-4"></a>

## 4. 目标年度CEO及基础B样本如何形成

### 4.1 目标CEO与基础公司年度

目标使用 `build_regression_data.py` 定义的年度CEO：anncomp `CEOANN='CEO'`，按GVKEY+fyear接财务，结合财年末日期选择唯一在任者；没有增加Current CEO的PCEO筛选。这里B指股权财富/Delta/Vega的`standard_finance`公式版本；A/B共用年度CEO选择，不是同一firm-year中的第一位/第二位CEO。

- 财务POPSRC合并后，GVKEY+fyear存在多条记录时整组排除，保留歧义审计，不挑最后日期。
- 已知BECAMECEO不得晚于DATADATE；开始日在FYE当日可入选。已知LEFTOFC必须晚于DATADATE，离任日在FYE当日不入选。
- 只有该firm-year恰好一名合格FYE候选才选中，零/多候选不按姓名或薪酬任取。缺BECAMECEO可暂入候选，但后续ln_tenure缺失不能通过完整controls。
- 财务日期不存在时，唯一年度CEO只暂留损耗审计，最终由财务flag排除。
- `event_id = 六位GVKEY + ':' + fyear`；`valuation_id`再加execid。市场按event_id、期权组合按valuation_id，角色/年度使用co_per_rol+fyear，防止公司年度财务与错误CEO组合。

### 4.2 公司证券与历史日期

CCM只使用LC/LU、P/C、正PERMNO；在FYE要求linkdt≤DATADATE≤linkenddt，E或缺失结束日期视为开放，缺开始日期不自动无界。多行同PERMNO可合并，多不同PERMNO拒绝。按同一FYE选定PERMNO查历史，不按ticker拼证券。

CRSP截至FYE最近源行不得早于FYE前最后有效市场日，SHRCD须10/11、EXCHCD须1/2/3。历史行业使用SICH（100–9999），排除4900–4999和6000–6999及缺失/无效行业；不以当前SIC替代。AT和PRCC_F×CSHO严格为正。

### 4.3 期权组合、B财富与市场输入

原数量以千股转实际股数；S与X为美元/股。B股票财富只用 `Q=1000×SHROWN_EXCL_OPTS`，不额外加STOCK_UNVEST_NUM；B普通股直接Vega为0。STOCK_UNVEST_NUM必须作为输入列存在，但其逐行缺失/负值不是B的数值资格门槛。

```text
d1 = [ln(S/X)+(r-d+sigma²/2)T] / (sigma*sqrt(T)); d2=d1-sigma*sqrt(T)
C  = S*exp(-d*T)*Phi(d1) - X*exp(-r*T)*Phi(d2)
option delta for stock-price +1% = .01*S*exp(-d*T)*Phi(d1)
option vega for volatility +1pp  = .01*S*exp(-d*T)*phi(d1)*sqrt(T)
equity_b_m = [Q*S + sum(q_j*C_j)] / 1,000,000
vega_b_k   = sum(q_j*option_vega_j) / 1,000
delta_b_k  = [.01*S*Q + sum(q_j*option_delta_j)] / 1,000
```

正参数区用上述BSM/Merton；T=0、X=0或sigma=0采用解析极限，非有限/负期限/负strike/非正S等无效，不将缺strike/expiry补0。有效区域只对看涨价值舍入负数作max(value,0)。每笔q为OPTS_UNEX_EXER/UNEXER/UNEARN三类数量在行内结构性缺值按0合计后×1000；任一负数量仍标记失败。

| 输入 | 定义与原始来源 |
|---|---|
| S | Compustat PRCC_F，未复权财年末价 |
| X、T | Outstanding Awards EXPRIC；(EXDATE−DATADATE).days/365.25，逐笔期限 |
| sigma60 | CRSP月度abs(PRC)/CFACPR：FYE所在月之前的61个连续月价，60个log变化样本SD×sqrt(12)，缺月不以更早月补齐 |
| d | 过去三个连续财政年DVPSX_F/PRCC_F的算术均值，再log1p；不含本年，历史缺失不补0 |
| r | 财年末当日或之前最近非缺DTB3/100的log1p；不取未来，rf_gap_days保留但无另设最大间隔 |
| retvol255 | FYE严格之前固定255个有效全市场交易日的个股RETX样本SD×100；全部日期收益须有效，不年化、不以前更多有效日补齐 |

同一CEO-year共用S/r/d/sigma，逐笔X/T/q不同；没有按期限插值收益率曲线、提前行权或不可交易性折价。sigma60不是回归retvol255。价格/收益同键精确重复可合并，同键冲突报错；期权S与EXPRIC使用未复权报价基准，月度复权价只估sigma。

完整期权组合要求年度可行使/不可行使总量披露且非负，与逐笔两类总量分别在≤0.01千股（10股）容差内对账；所有正数量tranche有效、身份/奖励编号无缺失冲突或重复、原奖励表无负数量。unearned独立纳入估值，不机械加进年度unexercisable对账。结构性类别缺值不等于关键估值输入/年度count可一律补0。

组合失败会整组不保留财富/敏感度，不删掉坏tranche只估剩余。stock-only原奖励行也可能触发共享键/身份/负数量守卫。明确零期权组合可以通过组合审计，但B Vega=0仍不符合最终B资格。养老金/递延明细只核对，不替代缺失年度总额。

### 4.4 基础B累计资格与本次覆盖分母

| 累计阶段 | N | 该步损失 |
| --- | --- | --- |
| 已选定年度CEO的公司年度 | 20,707 | — |
| 财务存在且无年度歧义 | 20,549 | 158 |
| 历史行业有效且排除金融/公用事业 | 14,942 | 5,607 |
| AT与市场权益正 | 14,664 | 278 |
| 唯一FYE有效CCM PERMNO | 14,517 | 147 |
| 美国主要交易所普通股挂牌 | 13,822 | 695 |
| 因变量/原全部controls有限 | 12,565 | 1,257 |
| 现金及债务完整、债务非负 | 12,565 | 0 |
| 完整期权组合 | 10,913 | 1,652 |
| B全部指标有限、equity/Vega正 | 7,086 | 3,827 |

本表仅2013–2023年，按同一顺序累计应用flag；损失不能和单flag失败数混加。7,086是**已具备所声明财务、证券、controls及期权完整性条件的年度B目标firm-years**，并非全美CEO/上市公司总体。strict 2,967占已选CEO主面板20,707的14.33%，只能解释为该已选主面板口径下的进一步覆盖，不能称全美覆盖。

`sample_b`仍要求原11项controls、payer/SIC2/fyear有限；cash/debt完整且inside debt≥0；portfolio_complete；equity、Vega、Delta/Vega、relative leverage、high-relative-leverage有限且equity/Vega>0。当前删除DVR、m00删除debt/Vega、No actual RD删除两项RD控制，都没有放宽这些原资格重新吸收样本。未定义DVR或零Vega者未被重新纳入。

XRD缺失按既定规则填0并保留dummy；其它必需薪酬、债务、税项、账面权益等不统一填0。没有新增winsor/trim、epsilon、Vega下限或按显著性删行。这是公开研究者实现，不是作者未公开full-disclosure/历史样本ID已经恢复的证明。

<a id="sec-5"></a>

## 5. 源synthetic proxy of CEO risk preference如何形成

### 5.1 源分数单位

源文件为 `ROOT/data/panel/risk_scores.parquet` / `.csv`，29,506行、20列。四个键为 `panel_id, gvkey, ceo_id, year`，另16列是两种模型 × OOF/全样本拟合 × raw/clip0/pct/z。`panel_id` 唯一，`gvkey+year` 唯一；它是**每个公司—讲话自然年只选一个主讲话者的分数**，并非同一firm-year里所有CEO各有一行，也不是不分公司的CEO-year分数。

源 `year` 是讲话自然年，覆盖2013–2023。它在源设计中直接对应 Compustat 的 `fyear` 标签，但这种标签相等本身不保证自然年和真实财年区间相同。原2006–2011期和2012年没有本批现成分数。

对应面板：`ROOT/data/panel/ceo_firm_year_panel.parquet`；回溯表：`ROOT/data/panel/component_map.parquet`；分数 metadata：`ROOT/data/panel/risk_scores.json`。旧本地匹配程序在读取时对 score 与 panel 的四个键逐行精确比较，不仅比较集合（`REP/scripts/match_rd_scores.py:46–50`）。

### 5.2 源公司/主讲话者选择

上游 `ROOT/src/ceo_rd/data.py:18–34`：只读取 `is_ceo=True` 的 component。源人员键优先为 `bx_` + BoardEx `directorid`；无directorid时为 `tp_` + `transcriptpersonid`。两个前缀是不同命名空间，不能去前缀后按相同数字认作同一人。

`ROOT/src/ceo_rd/panel.py:133–160` 先将 component 的 `symbolvalue + year` 与上游 Compustat 的 `tic + fyear` 内连接（多对一）。源 Compustat 为 `ROOT/data/ceo_and_firm/compustat_fundamentals_annual_2010-2025.csv`；`data.py:37–45`先按 `gvkey,fyear,datadate` 排序，再对 `tic,fyear` 和 `gvkey,fyear` 依次保留最后记录。没有匹配到源 Compustat 的 component 不进入源面板。

之后 `panel.py:34–43` 在每个 `gvkey,year,ceo_id` 中累计 `retained_word_count`，每个 `gvkey,year` 仅保留总发言词数最多的ceo_id。选取用 `groupby().idxmax()`，不是按财年末CEO任职标记，也没有把当年两位CEO的讲话都平均。`is_ceo`标记可能包含division CEO等，最多词数是既有上游的主讲话者选择办法，不能单靠它证明该人就是发行人年末CEO。

`panel.py:46–65` 汇总meta时：`ceo_id`取所选组首值，`ceo_name`取讲话姓名众数，`companyid`取众数。**公司ID众数及姓名众数只描述源面板，不能掩盖构成component中有多个公司/多个身份。** 后续匹配审计重新读取全部原component，而不是只看这两个众数。

因此，源“讲话最多者”和目标“年度CEOANN + 财年末唯一在任者”可能不同。目标和源必须再核CEO身份；候选公司/年份标签命中后，不自动把一个CEO的分数赋给当年的另一位CEO。若发生CEO更替，而源全年主讲话者不是目标年末CEO，该行会因身份不同不进入正式score回归，而不是换一个名字或把分数按在任月数分摊。

### 5.3 Topic和情绪聚合

源主CEO的topic density按 `retained_word_count` 加权平均（`panel.py:68–100`）。topic向量行和不超过1e−9的component不参与topic平均分母；其component仍在component_map和其它meta统计中。情绪是 `sentiment_transformer` 的词数加权平均，缺情绪component不进情绪分母（`panel.py:103–110`）。

### 5.4 第一阶段训练目标、预处理和参数

`ROOT/scripts/risk_score.py:44–52,83–92,112–145`：

- 目标 `rd_at_fill0 = XRD.fillna(0)/AT`，仅AT>0时定义。源XRD缺失被当作0，不等于只对原始披露正R&D的公司训练，也不等于“无标签公司全部排除”。
- 源29,506行中，29,191行目标非缺失参与训练；315行因AT无效/缺失不参与训练，但仍被预测，因而源score本身覆盖全部29,506行。该目标处理在 `src/ceo_rd/panel.py:113–129`，Claude 2026-10-25补充条目也已更正旧“全部有R&D”措辞。
- 特征仅Astra筛选的321个topic + 情绪，不含行业、年份、年龄、规模、实际R&D等额外预测控制。selection为 `ROOT/topic_selections/b1-gpt-6-astra-P0-xhigh.json`，metadata记录SHA `be14a1f557fbb28a9f4702af15ec49d9fb0ea7534e7701fd5cc301872d4461e9`。
- topic在所选子集内作CLR：`log(density+1e−6) - 行内log均值`，之后列标准化；情绪中位数填补、标准化；预处理放在sklearn Pipeline中（`src/ceo_rd/features.py:47–49,109–122`）。这不是把topic权重按风险正负手工赋号。
- 每次 `fit()` 调用先用传入训练数据目标的1%/99%分位截尾，再作GridSearchCV。对外层OOF而言，该阈值来自排除当前测试fold后的训练部分；代码不是每个内部CV子折分别重算目标阈值。不能将源目标截尾描述为匹配后回归变量被缩尾。
- Ridge alpha网格为1/10/100/1000/10000；五个外层fold和最终模型均选1000。
- XGBoost用min_child_weight=10，max_depth在3/6中选，五fold及最终均选6。既有默认n_estimators=600、learning_rate=.03、subsample=.8、colsample_bytree=.5（`src/ceo_rd/models.py:43–48`）。

上面参数来自本轮读取的代码及 `risk_scores.json`，并未重新训练验证其数值结果。Claude后来单独生成的20%训练/三seed稳健性不属于这两页Excel的分数来源。

「3 No actual RD」的含义仅为第二阶段分红Logit不放实际R&D/资产及其missing indicator；它**不会改变第一阶段仍然用实际R&D构造训练目标**的事实。不能把该页的score解释为完全不使用R&D信息的文本测量。

### 5.5 OOF、全样本拟合与当前百分点分数

`src/ceo_rd/splits.py:10–25`把公司和源ceo_id构成二部图；同公司所有年份、及共享CEO的不同公司合并到同一连通分量 `split_group`。用5折 StratifiedGroupKFold、seed42、按has_rd分层。这样在**源ID键定义**下，公司和共享CEO的公司不会分到不同fold；它不是按时间先后划分的预测实验，也不能自动修复原始身份键错误。

`risk_score.py:124–130` 外层逐fold：仅以其它fold的有标签行训练，预测当前fold的全部行。内部超参数CV沿用训练部分的PredefinedSplit。结果写 `risk_score_ridge` 和 `risk_score_xgboost`（无_full）。

`risk_score.py:135–139`另以全部有标签行训练最终模型并预测整个面板，写 `risk_score_<model>_full`；对有标签行而言这是样本内拟合，315个无标签行没有贡献训练标签。模型文件在 `ROOT/models/risk_score/{ridge,xgboost}.joblib`。

当前官方匹配列为无_full交叉拟合值的逐值复制：`vendor_strict_risk_score_ridge`、`vendor_strict_risk_score_xgboost`；两页回归再用 `100 × max(该raw值,0)`，即预测R&D/资产的**百分点**。这不是源 `_pct` 百分位排名，也不是_full、源z分数或在回归子样本重新标准化。负预测截0是真实已匹配分数的变换，**不能把未匹配的缺分数也补0**。

当前strict 2,967行中，Ridge有657个负raw值、XGBoost有291个负raw值；它们截为0后保留，未删除。这与未匹配score保持缺失是两种处理。

<a id="sec-6"></a>

## 6. 公司、CEO身份如何匹配

### 6.1 逐component核对来源，避免只看面板的众数身份

旧程序 `match_rd_scores.py:50–86` 由 `component_map.orig_idx` 与原讲话pickle的 `orig_row` 一对一连接，重建全部1,420,208条构成score的component。逐行断言对应讲话、保留词数、源CEO标识和源自然年相同；按panel再核component数、不同transcript数、总词数完全相同。

人员ID生成保留命名空间：有BoardEx `directorid` 时为 `bx_<directorid>`，否则为 `tp_<transcriptpersonid>`。源面板display名称或众数companyid不是全量component身份的替代品。程序保留每个panel实际component的所有 `execid_list, companyid_list, transcriptpersonid_list, directorid_list, transcriptpersonname_list` 等集合。

本地继承ExecuComp证据依优先序为：

1. 该panel实际component恰好一个非缺失execid，记 `direct_inherited_execid`。
2. 该panel无execid，但同一带命名空间 `ceo_id` 在整份原讲话资料的其他行只对应一个execid，记 `cross_year_unique_source_ceo_id`。
3. 多个execid记歧义；没有可用证据记 `no_execid_link`。

即使有局部唯一ID，仍保留跨年/全源冲突守卫：同一源CEO ID对应多个execid、同一transcriptpersonid对应多个execid、同一源companyid映射多个源GVKEY等均不能放行；实际component混入多家公司或多execid也不能放行。原始pickle中继承execid的最初生成程序没有被本次重建，所以该本地证据本身不称官方认证。



### 6.2 姓名支持和会计期末核对

`match_rd_scores.py:100–122` 要求目标 `datadate == source_datadate`。此条件除同一年度标签外再核对同一个会计期末。

姓名守卫比较**全部实际component的讲话者姓名**与目标选定CEO `exec_fullname`，不是只看源modal `ceo_name`。标准化包括Unicode转ASCII、小写、去标点、剥离分号后头衔/逗号后后缀及JR/SR/学位/称谓等。每个姓名须至少两token，末token姓完全相同，首token首字母相同；所有讲话姓名均须支持。它不是全名逐字符相同，也不检查完整middle name，因此不能把 `score_name_support` 写成“姓名完全一致”。姓名支持是守卫，不能单独建立execid链接。

公司名称另生成 `score_company_name_support`（剥离常见公司法律后缀后与原ExecuComp公司名比较），但这只是诊断列，**不在旧 `score_entity_match` 或新 `official_entity_verified` 的验收布尔式中**。公司正式核验依靠官方ID桥和有效日期；不能把名称不一致（可能是子公司、曾用名）直接等同错误公司，也不能把名称相同直接当作公司通过。



### 6.3 官方公司桥：每个实际companyid、每个实际讲话日期

权威程序 `scripts/verify_rd_score_vendor_links.py:33–75` 读取WRDS `ciq_common.wrds_gvkey` 全表。原始文件 `data/raw/linking_20261025/ciq_wrds_gvkey_all.csv.gz`，145,303行×6列：`companyid,gvkey,companyname,startdate,enddate,primaryflag`。WRDS query11828375，SQL为全表查询，未按公司、日期或primaryflag预筛；原SQL和获取元数据在同一raw目录保存。`primaryflag`保留但当前代码没有用它择一消歧。

公司核验从全部实际component构造 `companyid + speech_date` 请求，再为每个panel的每个实际companyid追加源 `source_datadate` 请求，共167,445个请求。讲话时间由UTC解析后取日期；不只核对面板众数companyid或一个年度日期。

每个请求与该companyid的全部官方链接行连接，按以下兼容性约定判断有效：

    request_date >= startdate（若startdate已知）
    request_date <= enddate（若enddate已知）

端点含等号；缺失端点按无界处理；请求日期本身须存在。对所有有效行取不同GVKEY集合，必须恰好一个，且等于源score原始GVKEY；多条行但同一GVKEY可以通过，多条不同GVKEY不能凭primaryflag或众数择一。

请求状态为 `consistent`、`different_gvkey`、`multiple_active_gvkeys`、`no_company_link`、`no_active_link_at_date`。每个panel还必须恰好一个实际source companyid；`multiple_source_companyids`优先判拒。全panel所有请求均通过才可 `official_company_verified=True`。

**缺失端点作为无界仅是ID兼容性约定，不是完整历史有效期认证。** `official_company_temporal_evidence` 保留三类证据：全部只有无日期链接、每请求有记录端点、混合/部分。代码的 `explicit_bounds_on_all_requests` 表示每个请求至少存在一个记录端点的支持链接；并不保证每行start/end两个端点均有值。

发现官方GVKEY不同，当前只隔离并保留原值，不自动把旧score赋给另一个GVKEY。原因是原训练R&D标签、公司/CEO选择和分组fold也可能受上游公司映射影响；换一个标签不能修复已经训练的模型。本阶段没有重建上游面板或重新训练。



### 6.4 官方CEO桥和质量门槛

`verify_rd_score_vendor_links.py:76–132` 读取 `people_link_execucomp_boardex_all.csv.gz`，44,373行×16列，WRDS query11828366，全库ExecuComp–BoardEx People Link，保留全部score及matchStyle。字段包括双方人员ID/姓名、质量score、matchStyle。官方质量说明1最高、13最低；实际raw中的score1均为 `fullname+cusip`（21,765原链接行）。

当前主验收是研究者为精准匹配选择的保守门槛：

- 源 `score_ceo_id` 必须是 `bx_` 命名空间；
- 全部实际component必须恰好一个BoardEx directorid，且不能有缺directorid的component；
- 此directorid在全部 `score=1` 官方行中须恰好对应一个不同的ExecuComp execid；
- 这个唯一execid必须等于目标firm-year已选定CEO execid。

这不是论文或WRDS要求的唯一可用阈值。score1–8为带CUSIP/ticker/公司名支持的不同质量链接，9为existing，10/12为年龄型；全部保留作为证据，当前没有将低质量链接提升为主验收。一个directorid在低质量层还有其他execid，不会自动否决score1层唯一且一致的链接；相反score1层本身一对多不通过。低质量年龄候选与旧execid不同也不能称为已证实旧CEO错误。

`official_person_status` 区分：`consistent_score1`、`different_execid_score1`、`multiple_score1_execids`、`no_director_link`、`supported_lower_quality_company_backed`、`different_execid_company_backed`、`supported_only_existing_or_age`、`low_quality_disagreement_not_proven_wrong`及未验证命名空间等。`official_person_pair_any_score`或`official_person_pair_company_backed`只是诊断，不能替代 `official_person_verified`。

当前账号取不到CIQ Transcripts和People Intelligence产品；ExecuComp–CIQ People Intelligence全库query11828367返回No Results Found。`transcriptpersonid` 不等于People Intelligence `personid`；`proid`是人与公司/机构关联的professional实例，也不等于personid。需要 `ciq_pplintel.ciqprofessional(proid,personid,companyid)` 桥，但本次没有取得。**没有用相同数字把这些命名空间强连起来。** 这些TP行继续待核，未使用姓名单独补配或绕过权限。

官方directorid↔execid验证的是ID对，不能独自证明原始每段讲话的directorid赋值正确；故旧家庭成员、混人、多公司、全局冲突守卫继续有效，明确不同的继承execid不能用新桥覆盖。

### 6.5 联合验收守卫

`verify_rd_score_vendor_links.py:134–148`：

    official_local_guards = score_key_match
        & score_accounting_date_equal & score_name_support
        & (source_companyid_count == 1) & (source_execid_count <= 1)
        & ~source_ceo_global_conflict & ~source_tp_conflict
        & ~source_companyid_global_conflict

    official_inherited_execid_compatible = score_key_match
        & (resolved_source_execid 缺失 或 resolved_source_execid == 目标execid)

    official_entity_verified = official_local_guards
        & official_inherited_execid_compatible
        & official_company_verified & official_person_verified

    official_fiscal_compatible = official_entity_verified
        & score_speeches_within_fiscal & score_tenure_dates_support

    official_strict_period_match = official_fiscal_compatible
        & score_calendar_equals_fiscal

冲突守卫缺失按有冲突处理，不默认放行。允许继承execid缺失且由官方高质量唯一桥补证，但不允许覆盖已明确不一致的继承ID。

公司/人员各自通过不等于全联合规则通过。全局companyid对应多个源GVKEY也会保守隔离，可能包括合法重组历史；未通过不等于已证实误配。公司名支持仅为诊断，姓名支持也不能独自建立人员链接。

<a id="sec-7"></a>

## 7. 自然年、实际财年与任期日期如何对齐

第一步候选 `gvkey+fyear` 对 `gvkey+score_year`，并且源 `source_datadate` 必须等于目标DATADATE（`match_rd_scores.py:98–101`）。公司/人员通过后还要做时间审查，而不是仅因year数字相同就进当前回归。

`match_rd_scores.py:123–137`：

1. 读取目标Compustat年度表（INDL/STD/C/USD），每个gvkey/fyear必须只有一个会计期末；用fyear−1的DATADATE作为 `prior_fiscal_end`。
2. `fiscal_start = prior_fiscal_end + 1 day`；财年边界必须已知且本期末晚于上期末。
3. 所有已观察component日期的最早/最晚值须满足 `speech_first >= fiscal_start`、`speech_last <= DATADATE`。由于已核全体日期，min/max检查对应所有源component均落在实际财年内。
4. 若BECAMECEO已知，要求最早讲话不早于该日；若LEFTOFC已知，要求最晚讲话严格早于离任日。开始/离任日缺失本身不在这条时间规则中制造已知冲突，但保留 `score_tenure_start_known`、`score_tenure_left_date_known`。这不能证明未知区间的全年连续任职；目标年度B另有任期等完整变量资格。
5. 更严格地要求 `fiscal_start == score_year-01-01` 且 `DATADATE == score_year-12-31`。它排除了自然年与实际财年完整区间不同的情况，而非只要求已看到的几次讲话刚好在财年内。

新官方版未更改上述日期标记；`verify_rd_score_vendor_links.py:137–139`在新实体核验后组合：

```python
official_fiscal_compatible = (
    official_entity_verified
    & score_speeches_within_fiscal
    & score_tenure_dates_support
)
official_strict_period_match = (
    official_fiscal_compatible
    & score_calendar_equals_fiscal
)
```

因此，只有新 `official_strict_period_match=True` 才进入当前score回归的匹配输入。不能误用旧本地 `score_strict_period_match`；官方版公司/人员证据比旧版多，行集合不同。

新official实体核验沿用旧日期标记，没有平移年份、重聚合源讲话或重估score。完整窗口一致会排除非12月末财年，甚至已观测讲话恰好都位于FY内的公司也可能被排除。这是明确的保守时间口径，会改变公司构成。

<a id="sec-8"></a>

## 8. 覆盖程度、逐年覆盖与互斥损耗

### 8.1 顺序交集流程：所有百分比分母固定为7,086

| 阶段 | firm-year N | 公司GVKEY | CEO execid | 占7,086 | XRD原缺失N |
| --- | --- | --- | --- | --- | --- |
| 年度B基础目标 | 7,086 | 1,314 | 1,908 | 100.00% | 2,235 |
| 同GVKEY/年份标签候选 | 6,022 | 1,102 | 1,601 | 84.98% | 1,859 |
| 候选且公司官方通过 | 5,967 | 1,099 | 1,593 | 84.21% | 1,845 |
| 再要求人员score1通过 | 4,441 | 870 | 1,133 | 62.67% | 1,311 |
| 再要求本地守卫 | 4,412 | 863 | 1,125 | 62.26% | 1,306 |
| 再要求继承execid不冲突 | 4,404 | 862 | 1,124 | 62.15% | 1,298 |
| 官方实体联合通过（同上一行） | 4,404 | 862 | 1,124 | 62.15% | 1,298 |
| 再要求讲话/FY及任期兼容 | 3,289 | 723 | 911 | 46.42% | 973 |
| 再要求完整自然年=实际FY | 2,967 | 600 | 771 | 41.87% | 906 |
| 普通(8)/(10)/m00实际回归 | 2,927 | 591 | 760 | 41.31% | 896 |
| 另从strict取(9)正相对杠杆输入 | 1,727 | 354 | 460 | 24.37% | 573 |
| (9)实际回归 | 1,653 | 340 | 441 | 23.33% | 534 |

前九行是按声明顺序取交集；实体行与其上一行重合，不再损失样本。普通实际与(9)两行是从strict分出的不同分支，**(9)先施加sample_log，再在其输入上剔纯组**，不把普通2,927作为其起点。两页和两种score在同一类设定中使用完全相同ID。

2006–2011原年度B输入5,826行、2012年916行均没有本批现成score；本两页只消费2013–2023的7,086行目标。三者合计13,828是完整年度B扩展输入，不能将本页strict覆盖率的分母改成它又不说明跨期无分数。

官方company/person原flag是独立条件，原先各自通过数不能天然当作顺序损耗。本轮重构上述交集流程，才得到每步增量。7,086中的不同公司/CEO为1,314/1,908；strict为600/771；最终普通为591/760。重复年度记录不是重复身份错配。

### 8.2 逐年覆盖

| fyear | 基础B | 候选 | 公司通过 | 人员通过 | 实体联合 | FY兼容 | strict | 普通实际 | (9)实际 | 普通/基础B |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2013 | 874 | 686 | 677 | 502 | 499 | 372 | 337 | 332 | 189 | 37.99% |
| 2014 | 817 | 660 | 653 | 492 | 487 | 358 | 316 | 313 | 189 | 38.31% |
| 2015 | 765 | 614 | 608 | 453 | 449 | 333 | 303 | 300 | 177 | 39.22% |
| 2016 | 756 | 627 | 622 | 468 | 465 | 345 | 322 | 316 | 179 | 41.80% |
| 2017 | 439 | 363 | 359 | 278 | 275 | 190 | 178 | 176 | 82 | 40.09% |
| 2018 | 466 | 406 | 406 | 304 | 303 | 237 | 213 | 211 | 104 | 45.28% |
| 2019 | 631 | 553 | 546 | 415 | 411 | 308 | 275 | 273 | 160 | 43.26% |
| 2020 | 623 | 556 | 552 | 400 | 395 | 290 | 263 | 259 | 146 | 41.57% |
| 2021 | 607 | 551 | 543 | 404 | 400 | 292 | 268 | 264 | 156 | 43.49% |
| 2022 | 573 | 516 | 514 | 379 | 376 | 273 | 253 | 249 | 150 | 43.46% |
| 2023 | 535 | 490 | 487 | 346 | 344 | 291 | 239 | 234 | 121 | 43.74% |

逐年为firm-year数；在此年度B表内每公司年唯一。跨年公司/CEO不能用该表列和当作去重总数。逐年完整N/G/CEO和strict比例另保存在coverage_by_year_annual_b_2013_2023.csv。

### 8.3 互斥损耗：为什么7,086最终只剩2,927

| 本轮审计first-failure分类 | N | 占7,086 |
| --- | --- | --- |
| 无源公司/年份候选 `no_source_firm_year_key` | 1,064 | 15.02% |
| 有候选但官方公司未通过 `official_company_not_passed` | 55 | 0.78% |
| 前项通过但官方人员未通过 `official_person_not_passed` | 1,526 | 21.54% |
| 前项通过但本地守卫未通过 `local_guard_not_passed` | 29 | 0.41% |
| 前项通过但继承execid冲突 `inherited_execid_incompatible` | 8 | 0.11% |
| 实体通过但讲话/FY或任期不兼容 `speech_fiscal_or_known_tenure_incompatible` | 1,115 | 15.74% |
| FY兼容但完整自然年/FY不相同 `fiscal_window_not_equal_to_source_calendar_year` | 322 | 4.54% |
| strict通过但普通纯组删除 `ordinary_pure_outcome_group_removed` | 40 | 0.56% |
| 进入普通回归 `used_in_ordinary_models` | 2,927 | 41.31% |

未进入普通回归共4,159行，加最终2,927恰好等于7,086。`audit_disposition`是**本轮为报表构建的first-failure顺序分类**，没有改旧匹配flag或旧score_match_reason；同一行仍可能有多个原始问题。单独flag失败的人员1,581、本地420、继承ID314会重叠，不能直接相加。

1,115个实体通过但时间不兼容者中：1,017个讲话不全在FY内，116个不满足已知任期，18个两者同时失败，因此1,017+116−18=1,115；这些行FY边界均已知。仅讲话跨界者可再分666个末次讲话晚于FYE、351个首次讲话早于FY起点。之后322行是讲话/任期兼容却完整年度区间不同。

### 8.4 身份证据、保守拒配与未知日期

6,022候选的公司状态为5,967 consistent、54 different_gvkey、1 multiple_source_companyids。人员状态如下；它与公司/本地失败可能重叠，不可相加成总未配数：

| 人员状态 | N |
|---|---:|
| consistent_score1 | 4,441 |
| no_director_link | 577 |
| unverified_transcript_namespace | 543 |
| different_execid_score1 | 250 |
| supported_lower_quality_company_backed | 156 |
| low_quality_disagreement_not_proven_wrong | 34 |
| different_execid_company_backed | 12 |
| multiple_score1_execids | 5 |
| supported_only_existing_or_age | 4 |

旧本地entity接受5,314行；新官方entity不是简单“删910”：旧接受中1,079行没有取得新官方通过，同时169个旧 `no_execid_evidence` 行由官方桥新补证，净得到4,404。1,079旧接受未获通过的公司状态均consistent；人员原因是TP命名空间516、无director链接384、低质量公司支持156、低质量不同17、score1一对多5、score1与目标不同1。多数未通过是无法取得足够证据，不是已证实错误身份。

2,967个strict输入中，2,746行公司证据是无日期端点链接、221行每请求至少有一记录端点；全部BECAMECEO起点已知，LEFTOFC已知1,841、缺失1,126。源继承execid证据为直接继承2,827、跨年唯一31、旧无execid后由官方补证109。以上是精准可执行规则下的覆盖，并不意味着所有日期/讲话者人工核准。最终Logit N还会因正相对杠杆子样本和纯结果行业/年份组处理下降，需与本稿的匹配输入N分开。

全29,506源分数的公司状态为consistent28,557、different_gvkey921、mixed-company20、no_active_link_at_date7、no_company_link1。这些是全源构造状态，不能混作年度B目标样本中的未匹配损耗。

### 8.5 反向分母：从29,506个源score看覆盖

全部源panel_id唯一，6,022个有当前年度B资格目标候选，23,484个没有该B资格目标；strict使用2,967个，占全源10.0556%，普通实际2,927个，占全源9.9200%。这与目标端41.87%/41.31%的分母不同。23,484不能统称身份匹配失败，它们可能根本不属于本表财务/证券/期权完整性目标总体；源记录继续保留，不强配到其他公司或CEO。

### 8.6 实际R&D缺失和score零值

strict输入中906条原XRD缺失，普通实际中896条、(9)实际中534条；这些行按原口径实际R&D填0进入。No actual RD没有因XRD原缺失另删这896条；它只在第二阶段删除实际R&D及missing dummy。已有负预测截0是保留的有效分数，缺失score不补0。

<a id="sec-9"></a>

## 9. 未匹配观测如何保存与处理

| 情况 | 当前处理 | 没有采取的替代处理 |
|---|---|---|
| 2006–2012无本批score | 保留原目标行/无候选原因，score回归不纳入 | 不用后期CEO分数倒填历史 |
| 公司/年份候选相同，但源与目标DATADATE不同 | 不通过实体守卫，候选值留作审计 | 不忽略财务期末差异 |
| 非12月末财年或财年起点不是1月1日 | 即使身份通过、观察到的讲话均在FY内，也不通过strict完整窗口 | 不把自然年score平移到相邻财年 |
| 讲话跨财年边界 | 不通过speech-within-fiscal，保留时间标记与清单 | 不截掉几段讲话后继续沿用原score |
| 与已知BECAMECEO/LEFTOFC冲突 | 不通过tenure-date支持 | 不把原score分摊给前任/继任CEO |
| 原源ceo_id混入多个execid、多个公司或全局冲突 | 按本地/官方身份守卫隔离，保留candidate和拒配原因 | 不按名字众数或公司众数自动清洗后继续使用 |
| 实体核验通过但strict不通过 | 保留 `vendor_risk_score_*` 和官方实体flag；`vendor_strict_risk_score_*`保持缺失，列入period-review清单 | 不把宽口径分数冒充本页严格回归输入 |

这些行保留在master/annual新增列版本中；正式回归输入再筛strict flag。它们不是全部从原始数据文件物理删除，也不统一填0。需要区分“无score”“身份待核”“时间不一致”和“有可用score但后续回归pure组损耗”；后者由模型实现审计另列。

官方匹配只新增列。旧master全部293列、35,151行和年度/PCEO各六张输入的旧列、行序、dtype都精确保留；覆盖全期2006–2023并不表示2006–2012有score。当前score仅2013–2023，2006–2011原期和2012无现成score，未外推或前后填补。

以下均为匹配输出根 `data/matched/rd_scores_wrds_20261025/`：

- `master_with_rd_scores.parquet`和`annual/`保留全部目标行，新vendor分数按验收条件缺失；只在后续明确筛strict时不进入回归。
- `audit/all_target_rows.*`保存每个目标的旧/新标记、目标CEO、源CEO、公司及人员证据。
- `audit/unverified_candidates.csv`为有源候选但未获entity通过。
- `audit/entity_verified_period_review.csv`为entity已通过但不是strict窗口，不能当身份错误删除证据。
- `audit/newly_verified_missing_inherited_execid.csv`保存官方新补证；`old_accepted_not_officially_verified.csv`保存旧接受但新证据不足；旧拒配原因仍保留。
- `audit/source_company_problem_queue.csv`保留全源公司问题；`source_official_identity.*`覆盖所有源分数；`company_date_requests.*`、`company_link_row_evidence.parquet`、`person_link_row_evidence.parquet`可追溯到官方原表行号/日期/质量。
- 无源候选和源有分数但没有目标的详细清单仍在旧匹配根 `data/matched/rd_scores_20261025/audit/no_score_candidates.csv`、`source_rows_without_target.csv`；新表沿用旧列但不把旧strict或旧entity当成新官方通过。这两个旧队列按旧master的35,151个目标行定义，不能当作当前年度B的7,086行队列，也不是反向23,484个未获B资格目标源行的清单；当前年度B去向应查本轮7,086行audit_disposition表。

在新匹配构建时407份源/旧结果SHA保护通过，`audit/validation.json`记录1,420,208 components、167,445日期请求、29,506源行及旧列精确保留。本轮只是读这些历史验证并独立重数当前文件，不冒充重新运行407文件构建校验。新脚本拒绝覆盖已有目录；如需重建必须指定全新输出，重跑匹配并不授权重训上游或修复公司标签。

本轮7,086行逐行审计去向保存在target_b_2013_2023_matching_disposition.csv，含原身份/时间flag及新增互斥audit_disposition、audit_log_disposition。它是新增审计表，不替换原匹配输出。匹配失败、证据不足和已匹配但回归pure组排除应分别核验；都不是将原始行物理删除。

<a id="sec-10"></a>

## 10. 两页精确模型、变量、样本与FE

### 10.1 从strict输入到实际e(sample)

| 设定 | 输入N / 公司G | 下一步 | 实际N / 公司G |
|---|---:|---|---:|
| `(8)`、`(10)`、`m00` | 2,967 / 600 | 迭代剔除行业或年份虚拟变量中的纯结果组，共40行 | 2,927 / 591 |
| `(9)` | 先从2,967行筛 `sample_log==1`，得到1,727 / 354 | 在这一子样本重新识别纯结果组，共74行 | 1,653 / 340 |

`sample_log`表示原年度B合格样本中 `ln_rellev` 非缺失且有限，即 CEO relative leverage 严格为正；零内部债务仍可进入普通设定，但不能对零相对杠杆取对数。这里不是对score取对数。

顺序是“2,967行匹配输入→(9)正相对杠杆限制→该子样本的纯组剔除”，**不是先取普通设定2,927行再筛(9)**。两类样本分别保存逐ID原因。所有 `no_rd/with_rd`、Ridge/XGBoost和同类设定的实际ID均按既有结果保持一致，没有根据新回归显著性改变样本。

“纯结果组”指某个实际观测到的 SIC2 或 fyear 层内 payer 全为0或全为1。在含该组虚拟变量的 Logit 中它会完全预测结果；当前引擎在每一轮同时标记 SIC2 和年份中的纯组、取并集删除，再迭代至没有新纯组。这不是按财务数值大小删尾，也不是一条新的CEO匹配失败。程序保留每行 `reason`，如 `pure_sic2=25_y=1`，多因素原因用分号并列。

上述同时取并集描述的是Python实现；Stata helper在一轮内按SIC2→fyear先后更新 `__pure`，重复到闭包。两种程序不要求中间轮次标签相同，最终实际ID已独立对齐；当前数据两种样本均无纯年份组，最终同40/74行删除。

本数据实际两种样本都在第一轮完成，未删任何纯年份组：

- 普通设定删除：SIC2=1（1行、payer0）、12（1、1）、21（1、1）、22（1、0）、25（8、1）、54（6、0）、57（6、1）、83（6、0）、99（10、1），合计40。
- 对数相对杠杆设定删除：SIC2=12（1、1）、14（6、1）、21（1、1）、23（7、1）、25（4、1）、31（7、1）、47（12、1）、52（10、1）、57（5、1）、82（5、0）、83（6、0）、99（10、1），合计74。

逐行入口：`RUN/python/samples/{model_id}_sample.csv.gz`，其中 `used=True/False`、`reason=retained`或纯组原因；该文件的分母是已经施加(9)限制后的输入，不是所有无法匹配的原始行。实际拟合ID和概率在 `{model_id}_fitted.csv.gz`；Stata实际 `e(sample)` 在 `RUN/stata/samples/{model_id}_used.csv` 的 `esample_oim/esample_cluster`。不能只凭文件名的“used”判断未检验这些flag。

依据：pure组函数 (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/scripts/run_table4_python.py) 第18–33行、score runner (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/scripts/run_table4_compilation.py) 第60、84–89行；两种删除明细在当前 `python/models/score_xgboost_no_rd_m08.json` 和 `...m09.json`（同类所有面板一致）。

### 10.2 精确模型、控制变量与单位

m00是本项目新增的No debt/Vega设定，不是原论文Table4的一列。

定义基础控制：

`C0 = [age, ln_tenure, capx_at_pct, asset_growth, mb, profitability_m, size_pct, re_at, retvol255]`。

`C1 = [age, ln_tenure, rd_at_pct, rd_missing, capx_at_pct, asset_growth, mb, profitability_m, size_pct, re_at, retvol255]`。

| 列 | score和薪酬/债务解释变量（不含控制与FE） | 第3页 | 第4页 |
|---|---|---|---|
| `(8)` m08 | `rd_score, cash_m, inside_debt_m, equity_m, vega_k` | 加C0 | 加C1 |
| `(9)` m09 | `rd_score, cash_m, ln_rellev, equity_m, vega_k` | 加C0，正rellev子样本 | 加C1，正rellev子样本 |
| `(10)` m10 | `rd_score, cash_m, high_rellev, equity_m, vega_k` | 加C0 | 加C1 |
| `(No debt/Vega)` m00 | `rd_score, cash_m, equity_m` | 加C0 | 加C1 |

所有式另含截距、两组单独的 SIC2 行业和 fyear 年份虚拟变量。没有公司FE、CEO FE、行业×年份交互FE、权重或滞后因变量。行业/年份dummy不是cluster定义。

因变量 `payer = 1(DVPSX_F > 0)`，仅在原股息字段已知时定义。模型为 pooled 二元 Logit：

`Pr(payer_it=1 | X_it) = logistic(constant + beta_score*rd_score_it + compensation_it + controls_it + SIC2_i + fyear_t)`。

主要单位/构造为：

| 字段 | 构造或单位 |
|---|---|
| `rd_score` | `100*max(OOF预测R&D/资产,0)`，百分点；不是原始ratio或百分位 |
| `cash_m` | `(SALARY+BONUS)/1000`，百万美元 |
| `inside_debt_m` | `(DEFER_BALANCE_TOT+PENSION_VALUE_TOT)/1000`，百万美元；年度总数未自动缺失填0 |
| `equity_m` | B版普通股财富+期权BSM价值，百万美元；B股票部分只取SHROWN_EXCL_OPTS，不额外加STOCK_UNVEST_NUM |
| `vega_k` | B版期权组合波动率上升1个百分点的财富敏感度，千美元；普通股直接Vega=0 |
| `ln_rellev` | `ln[(inside_debt/equity)/(LT/market_equity)]`，仅正值定义；firm leverage的LT是total liabilities |
| `high_rellev` | `1(relative leverage>1)`，不是附录另一个诊断阈值 |
| `age` | 年度ExecuComp AGE，年；不是header现任CEO年龄 |
| `ln_tenure` | `ln[1+floor((DATADATE-BECAMECEO).days/365.25)]`；不是入职工龄 |
| `rd_at_pct` | `100*XRD.fillna(0)/AT`，仅AT>0；XRD缺失填0 |
| `rd_missing` | 原始XRD是否缺失；在上述填0前生成 |
| `capx_at_pct` | `100*CAPX/AT`，百分点 |
| `asset_growth` | `(AT_t-AT_{t-1})/AT_{t-1}`，decimal ratio；上一连续财年、正AT |
| `mb` | market equity / book equity；有限负book equity比率仍保留 |
| `profitability_m` | `IB-DVP+TXDITC`，Compustat百万美元；未除AT |
| `size_pct` | 同fyear base-eligible参考总体中market equity严格小于本公司的比例×100；在完整案例/score筛选之前计算，不在2,967或2,927行重排 |
| `re_at` | RE/AT，decimal ratio |
| `retvol255` | 财年末之前255个有效真实交易日RETX样本标准差×100，百分点 |

第3页移除 `rd_at_pct` 和 `rd_missing` 只改变回归控制，不改变第一阶段模型训练目标的既有XRD缺失填0口径。`_full`、不同seed稳健性score也没有因删除实际R&D控制而被替换进来。

### 10.3 FE层、参数维度和样本

以下N/G/K在两种score之间完全相同；K含截距和实际非省略dummy。

| 页 | 设定 | 非FE解释变量数 | SIC2层数 / dummy数 | 年层数 / dummy数 | K | 实际N / G |
|---|---|---:|---:|---:|---:|---:|
| 3 No actual RD | m08 / m10 | 14 | 44 / 43 | 11 / 10 | 68 | 2,927 / 591 |
| 3 No actual RD | m09 | 14 | 37 / 36 | 11 / 10 | 61 | 1,653 / 340 |
| 3 No actual RD | m00 | 12 | 44 / 43 | 11 / 10 | 66 | 2,927 / 591 |
| 4 With actual RD | m08 / m10 | 16 | 44 / 43 | 11 / 10 | 70 | 2,927 / 591 |
| 4 With actual RD | m09 | 16 | 37 / 36 | 11 / 10 | 63 | 1,653 / 340 |
| 4 With actual RD | m00 | 14 | 44 / 43 | 11 / 10 | 68 | 2,927 / 591 |

所有模型的基准SIC2为10、基准fyear为2013。普通设定的SIC2层为 `10,13,14,15,16,17,20,23,24,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,42,44,45,47,48,50,51,52,55,58,59,70,72,73,75,78,79,80,82,87`；m09为 `10,13,15,16,20,24,26,27,28,29,30,32,33,34,35,36,37,38,39,40,42,44,45,48,50,51,55,58,59,70,72,73,75,78,79,80,87`。年份均2013–2023。


### 10.4 账面权益与Size的补充细节

`market_equity_m=PRCC_F×CSHO`；shareholder equity逐行依次取SEQ、CEQ+PSTK、AT−LT；preferred equity依次取PSTKL、PSTKRV、PSTK；book equity=shareholder equity−preferred equity+TXDITC。候选加法项缺失不补0；pref三项或TXDITC缺失则book equity缺失，有限负book equity并未单独剔除。

Size在各fyear基本资格公司参考总体内用`100*(rank(ME,method='min')−1)/N`，ties严格小于、分母N不是N−1；参考资格在完整controls、期权和score匹配之前。2013–2023及score子样本没有重新排Size。

<a id="sec-11"></a>

## 11. 估计方法、标准误与Excel数值来源

这些模型是未惩罚Logit普通MLE；没有Ridge/Elastic Net惩罚被施加到第二阶段Logit，Ridge只指第一阶段生成score的算法。无新增winsorization、Firth或按显著性筛样本。

Python使用 tail-safe likelihood/残差与动态Fisher缩放Newton，maxiter500，要求缩放后score无穷范数<1e−8且相对Newton步长<1e−8。解释变量先以maxabs后RMS作可逆尺度变换，不中心化；估计后系数、协方差和SE恢复原单位。FE和截距尺度为1；不存在因改单位而改变实际预测函数。

Stata19.5先按同一可逆scale生成z变量，使用：

```stata
logit payer z1 z2 ... ib10.sic2 ib2013.fyear, ///
    asis collinear difficult iterate(50) ///
    tolerance(1e-8) ltolerance(1e-10) nrtolerance(1e-5)
```

先OIM拟合保存BO；再从BO启动同模型并加 `vce(cluster __cluster)`，其中cluster对应公司GVKEY分组。`asis collinear`用于保留声明的样本/设计供审核，而不是允许删除核心变量后仍声称同式。所有16模型当前两次估计都收敛、核心变量遗漏数0，OIM/cluster实际ID一致。

表中系数取Stata第一次OIM拟合的BO（恢复原单位）；括号取第二次拟合的公司cluster SE；`max_b_change`保留两次极小数值差异。星号用表中b除cluster SE、正态Wald双侧p：p<.01、.05、.10各***、**、*，而非使用OIM p。**表中括号是SE，不是原论文的signed sqrt(Wald)。**

公司聚类协方差为：`G/(G−1) * H^{-1} [sum_g S_g S_g'] H^{-1}`；每家公司的score先对该公司所有firm-year求和。没有额外乘OLS的 `(N−1)/(N−K)`，没有行业/年份双向cluster或行业×年单元cluster。

表格数值层：

- b、cluster SE、p与星号：`RUN/stata/coefficients.csv`，`omitted_oim=omitted_cluster=0`的非省略term。
- N/G、Stata状态、两次fit的LL、基准层和遗漏状态：`RUN/stata/model_summary.csv`。
- 展示footer的LL及McFadden pseudo-R²：Python模型JSON；`pseudo_r2=1-LL/LL_null`，null只有截距且在该列同一实际样本上计算。Python与Stata LL数值近似一致但并非逐位相同，不能把两种来源混为精确同一字节值。
- 四表统一展示接口：`RUN/table_payload.json`；逐格长表为 `RUN/displayed_table_cells.csv`，其中table_id=table3/table4，panel=0(XGBoost)/1(Ridge)，column_id就是模型ID，term对应变量。
- 标准误和全部FE参数保留于Stata/Python完整CSV；Excel主面板只展示核心控制及FE Yes。表格是外部固定估计结果，编辑Excel输入不自动重估。

依据：引擎 (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/scripts/run_table4_python.py) 第35–60、87–130行；Stata便携driver (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/results/table4_compilation_rep_2013_2023_20261025/stata/RUN_TABLE4.do) 第69–122行；assembler (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/scripts/assemble_table4_compilation.py) 第25、49–72、108–115、163–169行。

<a id="sec-12"></a>

## 12. 版本传承、本轮核验与局限

### 12.1 哪些模型重估、哪些原字节继承

| 版本 | 发生了什么 | 当前16列的来源 |
|---|---|---|
| R14 `table4_compilation_20261025` | 最初22模型，普通8–10含DVR；score截0×100；当时no_rd仍保留missing dummy | 历史版，不直接作为当前推断 |
| R16 `table4_compilation_no_dvr_20261025` | 所有22模型重新估计仅删除DVR；逐ID、其它变量/尺度不变 | 当前8个with_rd模型在这一版估计，m00原本无DVR也统一重核 |
| R17 `table4_compilation_no_dvr_no_rd_missing_20261025` | 仅重估8个no_rd模型，额外删除rd_missing；另14列不重估 | 当前8个no_rd模型在这一版估计；8个with_rd模型原字节沿用R16 |
| R18 当前RUN | 仅新增3个2013–2023完整年度B的Replication模型，另22列不重估 | **当前16个score模型全部原字节沿用R17**，包括R17中已继承的with_rd |

当前 `model_provenance.csv/.json` 对这16列都写 `copied_without_refitting`，直接source_run为R17。`regression_config.json`把可复核当前快照路径指向当前RUN；原字节复制的每模型Python JSON内部 `snapshot_file/source_run` 可保留较早producer目录。这不是自动读错数据的证据，应联合当前config、provenance和copy manifest解析，而不能只看JSON内一条路径判断当前来源。

当前 `stata/compilation_estimates.do`实际只估计R18新增3个Replication模型，因此**不能用它当成这16列的生产执行日志或完整重跑程序**。完整25模型入口为 `RUN/stata/RUN_TABLE4.do`，同目录有25份 `inputs/*.dta`、`prepared.json`。若未来要复核，复制整个stata目录到新的独立位置，再从副本stata目录执行该便携driver；它会重建输出，不要在冻结权威结果目录直接运行。它重跑25列，不是仅16列。本轮没有执行任何driver。

### 12.2 历史独立数值核验的真实范围

实际读取的三份独立summary均status=passed：

1. R16 `audit/independent/summary.json`：22个全设计模型、Stata两种VCE与独立statsmodels全部收敛；删除仅DVR，原ID/其它变量保持。最大LL差1.2483e−7、标准化coef差9.2018e−9、OIM SE相对差2.5731e−6、cluster SE相对差2.5321e−6，星号一致。这包括当前with_rd八列。
2. R17 `audit/independent/summary.json`：仅八个no_rd新模型独立重估，另14模型参数/summary字段相同，154个per-model文件原字节相同。八个新模型最大LL差3.8871e−8、coef尺度化差7.9843e−9、OIM SE相对差7.3774e−7、cluster SE相对差1.4805e−6，所有星号一致。
3. R18当前 `audit/independent/summary.json`：仅新增三个Replication模型独立重估；验证旧22参数/summary全同、242个per-model文件原字节相同，因此当前16列传承可追溯。不能把“当前目录25模型都有结果”说成“本轮独立新拟合25个”，也不能把旧160-score/PCEO实验的验证总数当成本两页的16个模型数。

当前16列都是已认证的regular MLE，无DVR弱识别标记；这不改变第一阶段分数身份/覆盖和生成变量不确定性的限制。第二阶段SE条件于冻结score，没有把第一阶段重训不确定性bootstrap进去，亦不是检验CEO个人风险偏好的因果效度。

### 12.3 本轮新增只读核验

- 当前16个配置、回归项、N/G/K、逐ID样本、pure组、截0单位和来源继承已与保存文件对照；没有重新拟合。当前两页496个系数及clusterSE格、全部星号与payload一致。
- 本轮另从copied_file_manifest逐文件核对16个score模型共176个per-model文件：当前文件SHA、live R17源文件SHA、manifest记录SHA全部一致。这是本轮沿用关系的字节核验，不是本轮新增独立MLE。
- 当前源risk_scores按panel_id及四键映射回冻结strict快照，两种无_full raw值逐值精确一致；没有把后来seed稳健性版本或_full换进来。
- 另外将strict 2,967行源面板**训练截尾前**`rd_at_fill0`与第二阶段冻结`rd_at_pct/100`逐行比较：两边全部有限，2,967行均在rtol=1e−10/atol=1e−12内相等，最大绝对差`1.1102230246251565e−16`，没有源label缺失。此项是本轮额外验证，不是匹配验收条件；score_accounting_date_equal原来只核日期。第一阶段每fold仍按其训练部分1%/99%截尾，不能把这里的一致说成每fold实际fit目标与第二阶段actualRD逐值相同。
- 覆盖流程、逐年表、first-failure去向、全7086行审计、转化值、当前工作簿定位及源R&D一致性均保存在AUD；本轮文档构建QA检查本地链接和再现表的计数。

### 12.4 当前16个score行的数值索引

| 页 | score | 设定 | score系数 | 公司cluster SE | cluster p | N | G | K |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 3 No actual RD | xgboost | m08 | -0.19146022 | 0.03220489 | 2.7634365e-09 | 2,927 | 591 | 68 |
| 3 No actual RD | xgboost | m09 | -0.18240466 | 0.04817805 | 0.00015305906 | 1,653 | 340 | 61 |
| 3 No actual RD | xgboost | m10 | -0.20283747 | 0.03191028 | 2.0641178e-10 | 2,927 | 591 | 68 |
| 3 No actual RD | xgboost | m00 | -0.20431084 | 0.03167459 | 1.1162331e-10 | 2,927 | 591 | 66 |
| 3 No actual RD | ridge | m08 | -0.18358938 | 0.02182944 | 4.0940632e-17 | 2,927 | 591 | 68 |
| 3 No actual RD | ridge | m09 | -0.18901922 | 0.02996851 | 2.8401763e-10 | 1,653 | 340 | 61 |
| 3 No actual RD | ridge | m10 | -0.19211297 | 0.02148954 | 3.8974738e-19 | 2,927 | 591 | 68 |
| 3 No actual RD | ridge | m00 | -0.19259026 | 0.02118834 | 9.9545077e-20 | 2,927 | 591 | 66 |
| 4 With actual RD | xgboost | m08 | -0.14234514 | 0.03473423 | 4.1651476e-05 | 2,927 | 591 | 70 |
| 4 With actual RD | xgboost | m09 | -0.15005533 | 0.05019050 | 0.0027923705 | 1,653 | 340 | 63 |
| 4 With actual RD | xgboost | m10 | -0.15160162 | 0.03415524 | 9.0543742e-06 | 2,927 | 591 | 70 |
| 4 With actual RD | xgboost | m00 | -0.15450270 | 0.03405423 | 5.7070637e-06 | 2,927 | 591 | 68 |
| 4 With actual RD | ridge | m08 | -0.14776864 | 0.02407609 | 8.3794949e-10 | 2,927 | 591 | 70 |
| 4 With actual RD | ridge | m09 | -0.16801325 | 0.03174611 | 1.2071837e-07 | 1,653 | 340 | 63 |
| 4 With actual RD | ridge | m10 | -0.15321369 | 0.02358948 | 8.3032842e-11 | 2,927 | 591 | 70 |
| 4 With actual RD | ridge | m00 | -0.15422585 | 0.02349791 | 5.259943e-11 | 2,927 | 591 | 68 |

这里仅为定位这些冻结列的摘要，不是本轮新估计；完整控制变量/FE/协方差仍在RUN，主表星号以Stata公司聚类p为准。K包含实际非省略FE和截距。

### 12.5 剩余边界

上游源面板先用ticker+讲话年构造公司标签，官方审计另发现部分CIQ companyid与源GVKEY不一致。官方匹配对当前接受行施加额外核验、隔离失败行，**并没有重建全部源面板、改训练标签或重训第一阶段模型**。即使当前回归行本身通过官方链接，它的score训练仍可能受到其它源训练行身份/公司问题影响。

如果官方链接指向另一个GVKEY，程序不把已训练score搬到另一个公司；该值的原始R&D标签、main-CEO选择及fold/group都可能已依赖旧源映射。准确的新财年score也不能靠对已有年度score算加权平均生成，需要回到component重新确定年度、CEO归属、聚合、分组及第一阶段估计；本轮文档没有执行这种方法变更。

严格通过的2,967行中仍有2,746行只有无日期端点公司链接、1,126行缺LEFTOFC；这些未知不能因strict flag为真就写成完整历史人工认证。未匹配并不全是被证实错误；多ID/低质量/缺权限/昵称等守卫会带来保守覆盖损失。以上限制也不因第二阶段score显著而消失。

<a id="sec-13"></a>

## 13. 逐行回溯和具体例子

### 13.1 单个样本的核验路径

1. 在当前模型的保存样本找到 `event_id=GVKEY:fyear` 和目标execid、模型输入score列。
2. 回到 `REP/data/matched/rd_scores_wrds_20261025/annual/table4_b_extended_2006_2023_rd_scores.parquet` 同一行，检查新strict flag、`score_panel_id`、`score_ceo_id`、日期与官方ID证据。
3. 由score_panel_id回到 `audit/source_official_identity.*` 和旧 `data/matched/rd_scores_20261025/audit/source_score_identity.*`，检查原所有execid/companyid/directorid/讲话名字集合，不只看众数。
4. 由 `component_map.panel_id` 找orig_idx；在 `transcripts_is_ceo.pickle.orig_row`查原component的日期、公司和人员ID。核时间窗与任职边界。
5. 在源 `risk_scores.parquet` 同panel_id的无_full raw值，确认正式列逐值复制，回归输入为 `100*max(raw,0)`；缺strict flag的行不应出现在正式回归ID集合。

### 13.2 各种实际去向的例子

| event_id | 目标CEO | 源主讲话者 | 本轮审计去向 |
| --- | --- | --- | --- |
| 001004:2013 | David P. Storch | David Storch | 实体通过但讲话/FY或任期不兼容 |
| 001072:2013 | John S. Gilbertson | 无候选 | 无源公司/年份候选 |
| 001076:2013 | Ronald W. Allen | Ronald Allen | 进入普通回归 |
| 001076:2015 | John W. Robinson, III, C.F.A. | Ryan Woodley | 前项通过但官方人员未通过 |
| 001300:2016 | David M. Cote, J.D. | David Cote | strict通过但普通纯组删除 |
| 001533:2013 | Joseph Carleone, Ph.D. | Joe Carleone | FY兼容但完整自然年/FY不相同 |
| 003093:2013 | Christopher L. Conway | Thomas Wellner | 有候选但官方公司未通过 |
| 003980:2020 | Robert A. Chapek | Bob Chapek | 前项通过但本地守卫未通过 |
| 004001:2013 | Daniel K. Frierson | Daniel Frierson | 前项通过但继承execid冲突 |

这些是保留在文件中的数据记录姓名，不据此认证当年公司名称/职位。例子只说明代码如何作决定：

- `001076:2013`身份及窗口通过、普通列使用，但rellev=0不能进(9)取对数。
- `001300:2016`身份和strict通过，后续因pure组未进入普通及log模型；它不是匹配失败。
- `001533:2013`旧无execid证据被官方桥补证，但非完整日历财年仍不进strict。
- `003980:2020`官方score1桥支持，但源Bob/目标Robert未通过现有首字母姓名守卫，保留为local-guard未通过；不能把保守拒配自动当作人员已证实错误。
- `004001:2013`官方链接支持目标，但继承源execid明确冲突，因此不覆盖旧ID强行放行。

完整字段在matching_disposition_examples.csv及7,086行审计表；原score_match_reason与本轮audit_disposition可以不同，后者取的是此报表顺序中的第一个失败，不改写前者。

<a id="sec-14"></a>

## 14. 文件索引与重跑边界

### 14.1 关键文件索引

| 用途 | 可点击文件 |
| --- | --- |
| 源score | risk_scores.parquet (historical source reference: D:/pc_workspace_local/ceo_risk_taking/data/panel/risk_scores.parquet) |
| 第一阶段metadata | risk_scores.json (historical source reference: D:/pc_workspace_local/ceo_risk_taking/data/panel/risk_scores.json) |
| 源面板与fold | ceo_firm_year_panel.parquet (historical source reference: D:/pc_workspace_local/ceo_risk_taking/data/panel/ceo_firm_year_panel.parquet) |
| component map | component_map.parquet (historical source reference: D:/pc_workspace_local/ceo_risk_taking/data/panel/component_map.parquet) |
| 第一阶段runner | risk_score.py (historical source reference: D:/pc_workspace_local/ceo_risk_taking/scripts/risk_score.py) |
| 源面板构建 | panel.py (historical source reference: D:/pc_workspace_local/ceo_risk_taking/src/ceo_rd/panel.py) |
| 分组fold | splits.py (historical source reference: D:/pc_workspace_local/ceo_risk_taking/src/ceo_rd/splits.py) |
| 基础B构建 | build_regression_data.py (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/scripts/build_regression_data.py) |
| 期权组合 | option_portfolios.py (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/scripts/option_portfolios.py) |
| 市场输入 | market_inputs.py (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/scripts/market_inputs.py) |
| 旧本地匹配 | match_rd_scores.py (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/scripts/match_rd_scores.py) |
| 官方核验 | verify_rd_score_vendor_links.py (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/scripts/verify_rd_score_vendor_links.py) |
| 官方年度B新增列表 | table4_b_extended_2006_2023_rd_scores.parquet (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/data/matched/rd_scores_wrds_20261025/annual/table4_b_extended_2006_2023_rd_scores.parquet) |
| 匹配变量字典 | match_variable_dictionary.csv (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/data/matched/rd_scores_wrds_20261025/match_variable_dictionary.csv) |
| 官方源身份逐行 | source_official_identity.parquet (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/data/matched/rd_scores_wrds_20261025/audit/source_official_identity.parquet) |
| 全目标官方审计 | all_target_rows.parquet (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/data/matched/rd_scores_wrds_20261025/audit/all_target_rows.parquet) |
| 公司日期请求 | company_date_requests.parquet (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/data/matched/rd_scores_wrds_20261025/audit/company_date_requests.parquet) |
| 公司原始行证据 | company_link_row_evidence.parquet (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/data/matched/rd_scores_wrds_20261025/audit/company_link_row_evidence.parquet) |
| 人员原始行证据 | person_link_row_evidence.parquet (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/data/matched/rd_scores_wrds_20261025/audit/person_link_row_evidence.parquet) |
| 当前16列配置 | regression_config.json (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/results/table4_compilation_rep_2013_2023_20261025/regression_config.json) |
| 当前冻结score输入 | score_annual_b_2013_2023.parquet (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/results/table4_compilation_rep_2013_2023_20261025/input/score_annual_b_2013_2023.parquet) |
| 模型来源 | model_provenance.csv (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/results/table4_compilation_rep_2013_2023_20261025/model_provenance.csv) |
| 原字节复制清单 | copied_file_manifest.json (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/results/table4_compilation_rep_2013_2023_20261025/copied_file_manifest.json) |
| 当前16模型176文件复制核验 | copy_provenance_current_verification.csv (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/audits/score_tables_documentation_20261025/copy_provenance_current_verification.csv) |
| 当前复制核验摘要 | copy_provenance_current_QA.json (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/audits/score_tables_documentation_20261025/copy_provenance_current_QA.json) |
| 主系数与聚类SE/p | coefficients.csv (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/results/table4_compilation_rep_2013_2023_20261025/stata/coefficients.csv) |
| Stata模型summary | model_summary.csv (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/results/table4_compilation_rep_2013_2023_20261025/stata/model_summary.csv) |
| 统一表格payload | table_payload.json (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/results/table4_compilation_rep_2013_2023_20261025/table_payload.json) |
| 逐格结果 | displayed_table_cells.csv (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/results/table4_compilation_rep_2013_2023_20261025/displayed_table_cells.csv) |
| 完整25模型便携driver | RUN_TABLE4.do (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/results/table4_compilation_rep_2013_2023_20261025/stata/RUN_TABLE4.do) |
| 累计B资格计数 | base_B_attrition_2013_2023.json (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/audits/score_tables_documentation_20261025/base_B_attrition_2013_2023.json) |
| 匹配覆盖流程 | coverage_flow_annual_b_2013_2023.csv (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/audits/score_tables_documentation_20261025/coverage_flow_annual_b_2013_2023.csv) |
| 逐年覆盖 | coverage_by_year_annual_b_2013_2023.csv (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/audits/score_tables_documentation_20261025/coverage_by_year_annual_b_2013_2023.csv) |
| 互斥去向计数 | unmatched_and_excluded_reasons.csv (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/audits/score_tables_documentation_20261025/unmatched_and_excluded_reasons.csv) |
| 目标7086行去向 | target_b_2013_2023_matching_disposition.csv (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/audits/score_tables_documentation_20261025/target_b_2013_2023_matching_disposition.csv) |
| 反向源覆盖 | reverse_source_coverage.json (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/audits/score_tables_documentation_20261025/reverse_source_coverage.json) |
| 分数/样本核验 | coverage_and_sample_QA.json (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/audits/score_tables_documentation_20261025/coverage_and_sample_QA.json) |
| 当前源值与时间核验 | live_source_and_time_QA.json (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/audits/score_tables_documentation_20261025/live_source_and_time_QA.json) |
| 两阶段R&D比率对照 | source_vs_second_stage_RD_labels.csv (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/audits/score_tables_documentation_20261025/source_vs_second_stage_RD_labels.csv) |
| 两阶段R&D核验摘要 | source_vs_second_stage_RD_QA.json (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/audits/score_tables_documentation_20261025/source_vs_second_stage_RD_QA.json) |
| Excel逐格核验 | workbook_numeric_cell_validation.csv (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/audits/score_tables_documentation_20261025/workbook_numeric_cell_validation.csv) |
| 工作簿核验摘要 | workbook_QA.json (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/audits/score_tables_documentation_20261025/workbook_QA.json) |
| 示例去向 | matching_disposition_examples.csv (historical source reference: D:/pc_workspace_local/ceo_risk_taking/replications/caliskan_doukas_2015/audits/score_tables_documentation_20261025/matching_disposition_examples.csv) |

### 14.2 单模型ID如何找

模型ID公式为`score_{xgboost|ridge}_{no_rd|with_rd}_{m08|m09|m10|m00}`。对应每个ID：

```text
RUN/python/models/ID.json                       原设计、scale、LL、nullLL、纯组trace
RUN/python/models/ID_covariances.npz             完整Python协方差
RUN/python/samples/ID_sample.csv.gz              输入及used/reason
RUN/python/samples/ID_fitted.csv.gz              最终ID、线性预测及概率
RUN/stata/inputs/ID.dta                          保存的原单位输入
RUN/stata/samples/ID_used.csv                    实际e(sample)双VCE旗标
RUN/stata/estimates/ID_oim.ster、ID_cluster.ster   保存的估计
RUN/stata/covariances/ID_oim.dta、ID_cluster.dta   完整协方差
```

不要只看文件名`used`就假定所有行已检验；读取esample_oim/esample_cluster。主Excel表格是外部固定估计，不会因编辑单元格自动重估。

### 14.3 重跑边界

当前`stata/compilation_estimates.do`是R18新增三列Replication的实际生产入口，不能冒充16个score列的生产日志。完整`RUN_TABLE4.do`会重估25列并重建输出，因此若要重跑，应先把整个stata目录（包括25份inputs、prepared等）复制到**新的独立目录**，从副本stata目录执行`do RUN_TABLE4.do`。不能直接在冻结RUN内运行并覆盖证据；它也不是仅重跑本两页16列的driver。

若要重建匹配，`verify_rd_score_vendor_links.py --out 全新目录`拒绝覆盖；它需要原R9版和官方raw，不会重训源score。若要改变财年、主CEO、链接门槛或重新纳入零Vega等，要另立显式新研究规格，不能静默改本表口径。

本轮仅新增这份Markdown与AUD下审计证据；没有执行这些重跑命令。作者原样本/历史数据及若干未披露口径未恢复，这两页应解释为所述年度B、严格匹配子样本下的新proxy检验。

