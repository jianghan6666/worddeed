> Historical implementation snapshot. Machine paths and examples below are archival. Use the package root README for the current portable entry point.

# 5. synthetic proxy of CEO risk preference：Ridge 与 XGBoost 模型

本文说明 synthetic proxy of CEO risk preference 是怎么得到的：用了哪些特征、两个模型怎么训练、用了哪些超参数、分数怎么生成，以及输出文件的格式和复现方法。

**一句话概括：** synthetic proxy of CEO risk preference 是用 CEO 讲话内容预测出的 **R&D / 总资产**。

- **特征：** GPT 筛选后的 321 个 topic 和讲话情绪；
- **方法：** 交叉拟合，每个 CEO-firm-year 的分数都来自一个没有见过这家公司的模型。

> **注意：** 这个分数是用 R&D 作为监督信号训练出来的。它衡量的是"讲话内容像不像高 R&D 的公司"，和不使用 R&D 构造的 narrative measure 性质不同。

---

## 1. 样本与分析单位

- **单位：** firm-year（2013–2023），每个 firm-year 只保留当年发言词数最多的 CEO（Capital IQ 的 `is_ceo` 标记会混入子公司 CEO、CFO 等）。共 **29,506** 个 firm-year，覆盖 4,517 家公司、6,933 位 CEO。
- **匹配：** 讲话日期所在的自然年对应 Compustat 的 `fyear`；公司按 ticker 匹配。
- 面板构建见 4_rd_prediction.md (historical source reference: 4_rd_prediction.md)。

## 2. 目标变量

$$y = \text{R\&D / 总资产} = \frac{\text{xrd（缺失视为 0）}}{\text{at}}, \qquad \text{at} > 0$$

- **R&D 缺失补 0：** xrd 缺失的 12,452 个 firm-year，y 记为 0，占训练样本的 42.7%。缺失集中在金融、公用事业、采矿等行业。
- **剔除的行：** 总资产缺失或 ≤ 0 的 315 个 firm-year，y 为缺失，不参与训练和评估，但仍然会被打分（见第 5 节）。
- **训练样本：** 29,191 个 firm-year。
- **winsorize：** 按**训练部分**的 1% / 99% 分位截尾，下界为 0，上界约 0.64；评估时用同一阈值。

## 3. 特征

不含任何控制变量（行业、规模、年度等），只有两组文本特征。

**(1) Topic：321 维**

- **来源：** BERTopic 模型（354 个 topic，`all-mpnet-base-v2` embedding）给每段发言（transcript component）一个 354 维的 topic 分布 $d_{ik}$。
- **筛选：** 合作者 Step 2 中 `b1-gpt-6-astra-P0-xhigh` 这次试验的筛选结果（GPT 判断 topic 是否与风险相关），保留 321 个 topic。文件为 `topic_selections/b1-gpt-6-astra-P0-xhigh.json`。
- **汇总到 firm-year：** 主 CEO 当年各段发言按词数 $n_i$ 加权平均，即 $D_k = \sum_i n_i d_{ik} / \sum_i n_i$。topic 权重全为 0 的极短发言不参与。
- **变换：** 在这 321 个 topic 内部做 CLR，$\text{CLR}(D)_k = \log(D_k + 10^{-6}) - \frac{1}{321}\sum_j \log(D_j + 10^{-6})$，再标准化（均值 0、标准差 1）。

**(2) 情绪：1 维**

- **来源：** 每段发言的 `sentiment_transformer` 分数，原始取值在 [−0.85, 0.88]，0 为中性。
- **汇总：** 主 CEO 当年各段发言按词数加权平均，包括 topic 全为 0 的短发言。
- **变换：** 中位数填补（实际没有缺失），再标准化。

标准化的均值和标准差都**只在训练部分**计算。

## 4. 模型与超参数

| | Ridge | XGBoost |
|---|---|---|
| 实现 | `sklearn.linear_model.Ridge`（scikit-learn 1.2.2） | `xgboost.XGBRegressor`（xgboost 2.1.1） |
| 固定参数 | 带截距；其余为默认值 | `n_estimators=600`，`learning_rate=0.03`，`subsample=0.8`，`colsample_bytree=0.5`，`min_child_weight=10`，`tree_method="hist"`，`objective="reg:squarederror"`，`random_state=42`；没有 early stopping；其余（`reg_lambda=1`、`gamma=0` 等）为默认值 |
| 调参网格 | α ∈ {1, 10, 100, 1000, 10000} | max_depth ∈ {3, 6} |
| 调参方式 | 训练部分内部做按公司分组的交叉验证，以 R² 选最优，再用全部训练部分重新拟合 | 同左 |
| **选出的值** | **α = 1000**（5 个 fold 和全样本模型都一样） | **max_depth = 6**（5 个 fold 和全样本模型都一样） |

## 5. 分数怎么生成：交叉拟合

**划分：**
- 先把公司和 CEO 连成二部图，取连通分量作为分组单位。同一家公司的所有年份，以及共享过 CEO 的几家公司，都在同一组。
- 再用 `StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=42)` 把全部 29,506 个 firm-year 分成 5 个 fold，按"是否有 R&D"分层。每个 fold 约占 20%。

**交叉拟合（主版本）：** 训练 5 个模型，每个模型只给自己留出的那个 fold 打分。

| 模型 | 训练用的 fold | 训练样本 | 打分的 fold |
|---|---|---|---|
| 模型 1 | 1, 2, 3, 4 | 23,297 | 0 |
| 模型 2 | 0, 2, 3, 4 | 23,309 | 1 |
| 模型 3 | 0, 1, 3, 4 | 23,224 | 2 |
| 模型 4 | 0, 1, 2, 4 | 23,487 | 3 |
| 模型 5 | 0, 1, 2, 3 | 23,447 | 4 |

每个模型的训练步骤：
1. 只取训练 fold 中 y 非缺失的行；
2. winsorize 阈值、标准化参数都只用这些行计算；
3. 在这 4 个 fold 上做 4 折分组交叉验证选超参数；
4. 用 4 个 fold 的全部数据重新拟合。

打分时会给留出 fold 中的**全部** firm-year 打分，包括 y 缺失的行。所以：
- 每个 firm-year 的分数只来自**一个**模型，而这个模型在训练时**没有见过这家公司**（也没有见过和它共享 CEO 的公司），分数是真正的样本外预测；
- 5 个模型合起来见过了全部数据，但不会用见过某家公司的模型去给这家公司打分。

**全样本版（`_full`）：** 用全部 29,191 个有标签的 firm-year 训练一个模型，超参数同样用 5 折分组交叉验证选择，然后给所有 firm-year 打分。

- **用途：** 这个模型存成文件，用于对**新数据**（新年份、新公司）做推断。
- **不适合本样本分析：** 它对本样本的分数是样本内拟合，XGBoost 的样本内 R² 高达 0.898，明显虚高。

## 6. 性能

所有指标都在 29,191 个有标签的 firm-year 上计算，y 按 winsorize 后的口径。

| | Ridge | XGBoost |
|---|---|---|
| **交叉拟合 R²**（样本外） | **0.535** | **0.613** |
| 交叉拟合 MSE | 0.00601 | 0.00500 |
| 与 y 的相关系数 | 0.731 | 0.783 |
| 各 fold 内部交叉验证 R² | 0.524–0.537 | 0.595–0.610 |
| 全样本版样本内 R² | 0.553 | 0.898（过拟合） |

- 两个模型交叉拟合分数之间的相关系数是 0.913。
- 作为参照，只预测均值时 MSE 约为 0.0129，R² 为 0。

**小训练集稳健性：**
- **做法：** 用 3 个随机种子分别重新做分组划分，按 20% 训练、20% 验证、60% 测试切分。超参数在验证集上选。
- **结果：** 测试 R² 为 Ridge 0.502 ± 0.010、XGBoost 0.576 ± 0.009。在同一测试集上，原交叉拟合分数的 R² 为 0.530 和 0.605。
- **含义：** 训练数据从约 80% 降到 20%，R² 只下降约 0.03，结果对随机划分也不敏感。
- 详见 `results/risk_score_seed_robustness/report.md`。

## 7. 输出文件

**分数：** `data/panel/risk_scores.parquet`（同内容的 `.csv`），29,506 行。

| 列 | 说明 |
|---|---|
| `panel_id`, `gvkey`, `ceo_id`, `year` | 键。`ceo_id` 优先用 BoardEx 的 `directorid`（前缀 `bx_`），否则用 Capital IQ 的 `transcriptpersonid`（前缀 `tp_`） |
| `risk_score_ridge`, `risk_score_xgboost` | **交叉拟合分数（主版本，用于分析）** |
| `risk_score_ridge_full`, `risk_score_xgboost_full` | 全样本模型的分数（对本样本是样本内拟合） |

每个分数列另有 3 个转换版本，都在全部 29,506 个 firm-year 上计算：

| 后缀 | 含义 | 范围 |
|---|---|---|
| （无） | 原始值：预测的 R&D / 总资产，线性模型和树模型都可能为负 | Ridge 交叉拟合 −0.106 到 0.431（26% 为负）；XGBoost −0.026 到 0.570（19% 为负） |
| `_clip0` | 负值截到 0 | ≥ 0 |
| `_pct` | 百分位排名，同值取平均排名 | (0, 1] |
| `_z` | 标准化 | 均值 0、标准差 1 |

**其他文件：**
- **模型：** `models/risk_score/ridge.joblib`、`models/risk_score/xgboost.joblib`，都是全样本模型。每个文件包含整条 sklearn Pipeline（预处理加模型）、变量列表、321 个 topic 列名，以及 winsorize 阈值。
- **元数据：** `data/panel/risk_scores.json`，记录每个 fold 选出的超参数、交叉验证 R²、上面的评估指标、筛选文件的 SHA-256，以及 4 个版本的定义。

**对新数据打分：** 先按第 3 节的方法构造面板列（`topic_000`…`topic_353` 和 `sent_transformer`），再调用：

```python
import joblib
bundle = joblib.load("models/risk_score/xgboost.joblib")
score = bundle["model"].predict(new_panel)   # Pipeline 内部会自动选取 321 个 topic 列并做 CLR / 标准化
```

## 8. 复现

在项目根目录运行（需要面板 `data/panel/ceo_firm_year_panel.parquet` 和筛选文件 `topic_selections/b1-gpt-6-astra-P0-xhigh.json`）：

```bash
python scripts/risk_score.py                       # 训练两个模型、交叉拟合、生成 4 个版本（Ridge 约 0.5 分钟，XGBoost 约 9 分钟）
python scripts/risk_score.py --models ridge        # 只跑 Ridge
python scripts/risk_score.py --transform-only      # 只重新生成转换版本
python scripts/risk_score_seed_robustness.py       # 20% 训练集稳健性（3 个 seed）
```

划分、超参数网格和随机种子都是固定的。重新运行应得到相同的分数，可以用以下参考值核对：交叉拟合 R² 为 Ridge 0.5351、XGBoost 0.6128。

## 9. 局限

- **补 0 带来的行业成分：** R&D 缺失补 0 会把"有研发但没单独披露"的公司记为 0。模型的一部分预测力来自区分做研发和不报 R&D 的行业。
- **没有控制变量：** 分数里包含行业信息。比较行业内的差异时，需要在后续回归中加行业固定效应。
- **同期关联：** 讲话年份与 R&D 所在财年重叠，这不是事前预测。
- **topic 模型来源：** topic 模型来自另一项研究（CEO 政治意识形态），并在全部讲话语料上训练，测试公司的文本也参与了 topic 的估计。这是轻微的无监督泄露，与 R&D 无关。
