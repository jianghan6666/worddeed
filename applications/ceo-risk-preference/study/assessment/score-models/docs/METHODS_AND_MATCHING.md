# Step 4：方法、CEO/公司匹配与样本覆盖

整理日期：2026-10-27。完整结果见[结果展示](../results/RESULTS.md)，变量逐列定义见[数据字典](DATA_DICTIONARY.md)。

本说明对应原工作簿 `table4_annual_b_tables.xlsx` 的 `3 No actual RD` 与 `4 With actual RD`，共16个模型，财政年度为2013–2023年，均使用年度CEO B。这里两组**都放入预测的synthetic proxy of CEO risk preference**；区别是是否控制实际R&D/资产及其缺失指示变量。Ridge与XGBoost分别估计，并未同时放入一个模型。

主要分析数据：[analysis_strict_2967.csv](../data/analysis_strict_2967.csv)；同内容Parquet：[analysis_strict_2967.parquet](../data/analysis_strict_2967.parquet)。源分数与折号索引：[score_provenance_2967.csv](../data/score_provenance_2967.csv)。

本包的复现边界是：从已经构建、已经严格匹配并冻结的分析数据，重新估计这16个Logit模型，核对系数、公司聚类标准误和实际入样本ID。包内预测分数是既有交叉拟合输出；运行第二阶段无需WRDS登录或重新训练机器学习模型。从原始讲话重新提取特征、训练分数、从原始WRDS大表重建期权组合与重新核验官方身份桥，属于上游数据生产流程。本包的方法说明交代这些来源，但不能把第二阶段复跑称为上游全链条重建。

## 研究单位与CEO版本

最终一行是公司×财政年，键为保留六位前导零的 `gvkey` 加 `fyear`，并带有该firm-year选定的CEO `execid` 和公司任职角色 `co_per_rol`。`event_id=gvkey:fyear`，`valuation_id`进一步包含CEO身份。CSV读取时应将GVKEY和event_id作为字符串，避免丢失前导零。

年度CEO先要求ExecuComp `CEOANN='CEO'`，再用Compustat财政年末 `datadate`、已知 `BECAMECEO` 和 `LEFTOFC` 选择唯一财政年末在任CEO。开始日在FYE当日可入选；已知离任日须严格晚于FYE。多名合格CEO不任取一人。没有使用 `PCEO='CEO'` 额外筛选。B是股权财富、Delta和Vega的标准金融公式版本，并非同年第二名CEO；它与历史A版本共用年度CEO选择规则。

## 基础财务与薪酬数据

主要来源为WRDS的ExecuComp Annual Compensation与Outstanding Awards、Compustat Fundamentals Annual、CRSP Legacy日/月数据及CRSP–Compustat历史连接表，另用FRED的三个月国债率DTB3。养老金与递延薪酬明细用于核对；内部债务金额使用年度表总额，不用明细填补年度缺失。

Compustat采用INDL、STD、C、USD，补充并核验POPSRC D，保留active和inactive。历史行业用 `SICH`，剔除公用事业4900–4999及金融6000–6999；缺失或无效历史SIC排除。CCM采用LC/LU、P/C、财政年末有效且唯一的PERMNO。证券要求CRSP普通股10/11和主要交易所1/2/3，资产与市场权益为正；未额外限制当前指数成分、美国注册地或当前CEO名单。

B股票财富为普通股持有量 `SHROWN_EXCL_OPTS` ×1000×财年末股价；不额外加未归属股票。B股权财富还包括Black–Scholes–Merton逐笔期权价值，股票直接Vega为0。期权Vega为波动率上升1个百分点的美元敏感度。估值使用逐笔行权价和到期日、前60个完整月的复权股价波动、前三个财政年的股息率和财政年末之前最近的DTB3。回归用的 `retvol255` 是另一项指标：FYE严格之前255个交易日RETX的样本标准差×100，不年化。

基础B资格还要求完整的期权组合、年度数量与明细对账、财务/CEO控制变量完整、现金和债务有效、股权财富和Vega为正等。**从当前模型删除Delta/Vega、实际R&D控制，或在第四种设定删除内部债务/Vega，没有放宽原B样本资格重新纳入观测。** 这使四种设定和两种RD控制可以在既定样本内比较，但并不代表未报告债务或零Vega CEO已进入简化模型。

## 分数来源与尺度

源score表来自29,506个公司自然年；一家公司自然年保留由上游规则选定的主要讲话者（按保留词数最多），并非自动等于该公司财政年末CEO。Ridge和XGBoost用Astra 321个主题与情绪预测实际 `XRD/AT`：原始XRD缺失填0，AT缺失或不正的315行不参与训练。有效训练目标为29,191行。第一阶段不含财务控制变量。

主要分数为按公司—CEO连接分组的5折out-of-fold交叉拟合预测，seed=42；同一外折测试组的分数由未使用该组训练的模型生成。这里不使用带 `_full` 的全样本拟合分数。这是分组交叉拟合，不能解释为按时间向未来的样本外预测或外生工具变量。

第二阶段使用：

```text
ridge_clip0_pp   = 100 × max(vendor_strict_risk_score_ridge, 0)
xgboost_clip0_pp = 100 × max(vendor_strict_risk_score_xgboost, 0)
```

`rd_score`是每次估计所选算法分数的别名。数值1表示预测R&D/资产高1个百分点；不是百分位、不是z-score，也不是概率上升1个百分点。通过匹配但预测为负的分数截为0并保留；严格输入中Ridge有657个此类0，XGBoost有291个。**匹配失败的分数保留缺失并排除，绝不当作0。** 第二阶段未重新训练分数，也未新增winsor、trim、Vega下限、epsilon或惩罚项。

## 公司、CEO和时间窗口如何匹配

候选连接用规范化六位GVKEY和年份一对一连接目标 `gvkey,fyear` 与源 `gvkey,year`，不能仅凭这个候选给分。源讲话的自然年与目标财政年可能不同，源主讲话者也可能不同于目标FYE CEO。

正式接纳还需同时满足：

1. 对所有实际讲话component的CIQ公司ID和日期，使用WRDS CIQ公司→GVKEY桥，映射到同一目标GVKEY。多公司冲突不能以主公司或多数票覆盖。官方桥缺少起止日期时按开放边界处理，这是兼容性政策，不能当作严格历史日期证据。
2. 对所有实际component的BoardEx `directorid`，使用WRDS ExecuComp–BoardEx People Link的高质量score=1、唯一ExecuComp ID，并与目标CEO的 `execid` 一致。缺桥、低质量、歧义及冲突不自动接受。`transcriptpersonid`、`personid`与professional ID是不同命名空间，不以数值相同代替身份桥。
3. 通过原本地审计守卫：源与目标会计日期一致、姓名姓氏+首字母支持、公司/人员无已知全局冲突等；已有继承execid须缺失或与目标一致。姓名守卫不是完整姓名精确匹配，也不是模糊匹配后自动赋分。
4. 所有讲话日期在目标实际财政年起止区间内，且不与已知CEO任职起止冲突；严格版本进一步要求完整财政窗口等于源自然年1月1日至12月31日。没有简单跨年移动分数或把另一位CEO的分数转给财政年末CEO。

这些都是研究者为第二阶段采用的保守核验政策；不能声称是原论文已披露的匹配实现，也不能证明上游每条原始讲话者标注都绝对无误。 严格输入中2,746行仅有无日期边界公司链接；221行的每项日期请求至少有一条具有已知边界的链接，但不表示两端边界同时已知。已知离任日的行有1,841，另1,126行离任日缺失；这些缺失日期的证据限制随数据保留。

## 样本覆盖与损耗

| 累计阶段 | firm-years | 不同公司 | 不同execid |
|---|---:|---:|---:|
| 2013–2023已合格年度B目标 | 7,086 | 1,314 | 1,908 |
| 公司年份候选 | 6,022 | 1,102 | 1,601 |
| 通过公司桥 | 5,967 | 1,099 | 1,593 |
| 再通过人员桥 | 4,441 | 870 | 1,133 |
| 再通过本地守卫及继承ID兼容 | 4,404 | 862 | 1,124 |
| 讲话及已知任职窗口兼容 | 3,289 | 723 | 911 |
| 严格自然年=完整财政年输入 | 2,967 | 600 | 771 |
| 普通设定实际估计 | 2,927 | 591 | 760 |
| (9)正相对杠杆输入 | 1,727 | 354 | 460 |
| (9)实际估计 | 1,653 | 340 | 441 |

严格输入占已合格年度B目标的41.87%；普通实际估计为41.31%。分母不是全美上市公司、全美CEO或全部讲话源样本。公司数和CEO数是跨年去重，不能相加各年数。完整[覆盖流程](../audit/coverage_flow_annual_b_2013_2023.csv)、[逐年覆盖](../audit/coverage_by_year_annual_b_2013_2023.csv)、[7,086行处置审计](../audit/target_b_2013_2023_matching_disposition.csv)及[互斥损耗汇总](../audit/unmatched_and_excluded_reasons.csv)随包保存。

普通模型实际用样本的互斥首个失败归类为：无候选1,064；公司桥55；人员桥1,526；本地守卫29；继承ID不兼容8；讲话/任职时间1,115；财政窗口不等于源自然年322；普通纯结果组40；实际使用2,927，总计7,086。未通过核验表示未满足当前证据政策，不等于已证明原始身份错误。

纯组处理在每类模型输入中迭代删除SIC2或年度内因变量全0或全1的组，并逐ID留痕。(9)先从2,967严格输入要求正相对杠杆，得到1,727，再做自己的纯组处理得到1,653；不是先把普通模型2,927行当作(9)筛选起点。

## 16个模型的共同设定

因变量 `payer=1(DVPSX_F>0)`。估计未惩罚的pooled Logit，常数项、分开的SIC2行业虚拟变量和财政年度虚拟变量都保留；没有公司或CEO固定效应，没有行业×年度交互固定效应，没有权重。所有解释变量为当期值。

四种设置：

| 设置 | 核心解释变量（另加控制变量与FE） |
|---|---|
| (8) / m08 | rd_score、cash_m、inside_debt_m、equity_m、vega_k |
| (9) / m09 | rd_score、cash_m、ln_rellev、equity_m、vega_k |
| (10) / m10 | rd_score、cash_m、high_rellev、equity_m、vega_k |
| No debt/Vega / m00 | rd_score、cash_m、equity_m |

`m00`是本项目新增设定，不是原论文的一列；它仍保留cash和equity。所有16个模型都不放Delta/Vega，亦没有单独Delta项。相对杠杆为 `(inside_debt/equity)/(LT/market_equity)`；(9)取自然对数且要求正，(10)使用 `1(rellev>1)`。

第3页控制：`age ln_tenure capx_at_pct asset_growth mb profitability_m size_pct re_at retvol255`。

第4页在相同设置上同时添加 `rd_at_pct rd_missing`。实际R&D/资产为 `100*XRD/AT`，仅原始XRD缺失时填0，并以missing dummy标记；第3页两者都不放。分数仍可能包含与公司业务、创新策略、CEO及文本风格相关的成分，控制实际R&D并不能直接识别纯粹心理风险偏好。

两算法、两RD控制组在同一设置的最终样本ID一致。普通m08/m10/m00共2,927行、591家公司，m09为1,653行、340家公司。普通模型基准SIC2为10，年度基准2013；对数模型同基准。所有16模型历史Stata OIM与cluster拟合均收敛、无核心变量省略。

逐模型精确声明见[model_specifications.json](../code/model_specifications.json)，历史估计系数见[reference/coefficients.csv](../reference/coefficients.csv)，样本量及收敛状态见[reference/model_summary.csv](../reference/model_summary.csv)。`used_ordinary`和`used_log`记录最终估计样本；逐模型输入及e(sample)证据在 `reference/samples/`。

## 推断和数值核对

结果表报告Logit系数；括号内是按公司 `gvkey` 聚类的标准误，协方差修正为CR0×G/(G−1)，不使用OLS额外的(N−1)/(N−K)。星号采用双侧normal-Wald检验：1%、5%、10%。行业/年度虚拟变量不等于行业或年度聚类。原论文Table4未明确披露cluster维度，不能把当前公司聚类称为已恢复作者标准误设置。

原工作簿的系数来自Stata的OIM拟合，聚类SE和p值来自在同一设计/样本上以该解起始的cluster拟合；两次b仅有浮点级差异。LL和pseudo-R²表脚来自经独立核验的Python模型输出。复跑时系数/SE应按合理浮点容差比较，不能用文件字节或终端四舍五入值判断数值一致。

16个分数系数全部负且公司聚类p<0.01；控制实际R&D后绝对系数均缩小。以withRD的(8)为例，XGBoost系数−0.142345、Ridge−0.147769，每增加1pp分数对应优势比约0.8673、0.8626，属于股息支付odds低约13.27%、13.74%的条件关联。不能解释为支付概率下降同样百分点，亦不能据此宣称因果或完成心理风险偏好的构念验证。

## 文献定位

Deren Caliskan and John A. Doukas (2015), “CEO risk preferences and dividend policy decisions,” Journal of Corporate Finance 35, 18–42. DOI: 10.1016/j.jcorpfin.2015.08.007。本实验借用其股息支付Logit框架，加入预测synthetic proxy of CEO risk preference；本包不包含原论文2006–2011或全期基准复现结果。
