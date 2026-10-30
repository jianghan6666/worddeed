# Step 3 方法说明：Ridge 与 XGBoost 的 synthetic proxy of CEO risk preference

本文说明 synthetic proxy of CEO risk preference（数据文件中的列名仍为 `risk_score_*`）是怎么得到的：数据从哪里来、用了哪些特征、两个模型怎么训练、用了哪些超参数、分数怎么生成。文中提到的路径都相对于包根目录。

**一句话概括：** synthetic proxy of CEO risk preference 是用 CEO 讲话内容预测出的 **R&D / 总资产**。

- **特征：** GPT 筛选后的 321 个 topic 和讲话情绪；
- **方法：** 交叉拟合，每个 CEO-firm-year 的分数都来自一个没有见过这家公司的模型。

> **注意：** 这个分数是用 R&D 作为监督信号训练出来的。它衡量的是"讲话内容像不像高 R&D 的公司"，和不使用 R&D 构造的 narrative measure 性质不同。

---

## 1. 数据来源

| 文件 | 内容 |
|---|---|
| `data/components/components.parquet` | Capital IQ 电话会议中被标为 CEO（`is_ceo`）的全部发言段落（transcript component），共 1,775,355 行。只保留 Step 3 用到的列：键、ticker、年份、发言人 ID、词数 `retained_word_count`、情绪 `sentiment_transformer` |
| `data/components/topic_distr.npz` | 每段发言的 354 维 topic 分布（数组名 `topic_distr`，float64），与 `components.parquet` 的 `row` 列逐行对齐 |
| `data/compustat/compustat_panel_firms.csv` | Compustat Fundamentals Annual 中面板公司的全部年份（53,729 行），用到 `tic`、`gvkey`、`fyear`、`datadate`、`at`、`xrd`、`sale`、`sich` |
| `data/topic_selection/b1-gpt-6-astra-P0-xhigh.json` | Step 2 的 topic 筛选结果（GPT-6 Astra，xhigh，重复 1，primary 版本），`final.relevant` 中有 321 个 topic |
| `data/firm_year_inputs.parquet` | 由以上文件构建的 firm-year 输入表（第 1 步的输出，见第 2 节），29,506 行 |

**补充说明：**
- **topic 分布的来源：** topic 分布由 BERTopic 模型（354 个 topic，embedding 为 `all-mpnet-base-v2`）的 `approximate_distribution` 生成。极短的发言没有分配 topic，整行为 0。
- **原始文件中的行号：** `components.parquet` 的 `orig_row` 列是该段发言在原始全量语料（5,765,638 行）中的行号，用于溯源。

## 2. 第 1 步：component → firm-year 输入表

代码在 `code/step3_lib.py` 的 `build_inputs`，入口为 `code/01_build_inputs.py`。

1. **匹配 Compustat：** 发言的 ticker（`symbolvalue`）和讲话日期所在的自然年，对应 Compustat 的 `tic` 和 `fyear`。匹配上 1,547,519 段。Compustat 中极少数 `(tic, fyear)` 或 `(gvkey, fyear)` 重复的情况，保留 `datadate` 最新的一条。
2. **保留主 CEO：** 每个 firm-year 只保留当年发言总词数最多的那位 CEO，剩下 1,420,208 段，因为 `is_ceo` 标记会混入子公司 CEO、CFO 等。
   - CEO 身份优先用 BoardEx 的 `directorid`，在 `ceo_id` 中加前缀 `bx_`；
   - 没有 `directorid` 时用 Capital IQ 的 `transcriptpersonid`，前缀为 `tp_`。
3. **topic 汇总：** 对主 CEO 当年的各段发言按词数 $n_i$ 加权平均，$D_k = \sum_i n_i d_{ik} / \sum_i n_i$。topic 全为 0 的 8,867 段不参与。结果存为 float32。
4. **情绪汇总：** `sentiment_transformer` 按词数加权平均，**包括** topic 全为 0 的短发言。原始取值在 [−0.85, 0.88]，0 为中性。
5. **目标变量：**

   $$y = \text{rd\_at\_fill0} = \frac{\text{xrd（缺失视为 0）}}{\text{at}}, \qquad \text{at} > 0；\text{否则为缺失}$$

   - 29,506 个 firm-year 中，xrd 缺失的有 12,767 个；其中总资产为正的 12,452 个，y 记为 0。
   - 总资产缺失或 ≤ 0 的 315 个 firm-year，y 为缺失。
   - 有 y 的 firm-year 共 29,191 个，其中 42.7% 是补 0 得到的。
6. **分组划分：**
   - **分组：** 把公司和 CEO 连成二部图，取连通分量作为分组单位（`split_group`）。同一家公司的所有年份，以及共享过 CEO 的几家公司，都在同一组。
   - **切分：** 用 `StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=42)`，按 `has_rd`（xrd > 0）分层，把全部 29,506 个 firm-year 分成 5 个 fold（`fold` 列 0–4），每个约占 20%。

结果共 29,506 个 firm-year（2013–2023），覆盖 4,517 家公司、6,933 位 CEO。

## 3. 特征

不含任何控制变量（行业、规模、年度等），只有两组文本特征。

| 特征 | 维数 | 预处理 |
|---|---|---|
| 情绪 `sent_transformer` | 1 | 中位数填补（实际没有缺失）→ 标准化 |
| Astra 筛选的 topic（`topic_XXX`） | 321 | 在这 321 个 topic 内部做 CLR → 标准化 |

CLR 的公式为

$$\text{CLR}(D)_k = \log(D_k + 10^{-6}) - \frac{1}{321}\sum_{j} \log(D_j + 10^{-6})$$

填补值、标准化的均值和标准差都**只在训练部分**计算。

## 4. 模型与超参数

| | Ridge | XGBoost |
|---|---|---|
| 实现 | `sklearn.linear_model.Ridge`（scikit-learn 1.2.2） | `xgboost.XGBRegressor`（xgboost 2.1.1） |
| 固定参数 | 带截距；其余为默认值 | `n_estimators=600`，`learning_rate=0.03`，`subsample=0.8`，`colsample_bytree=0.5`，`min_child_weight=10`，`tree_method="hist"`，`objective="reg:squarederror"`，`random_state=42`，`n_jobs=16`；没有 early stopping；其余（`reg_lambda=1`、`gamma=0` 等）为默认值 |
| 调参网格 | α ∈ {1, 10, 100, 1000, 10000} | max_depth ∈ {3, 6} |
| 调参方式 | 在训练部分内部，按其 fold 做分组交叉验证，以 R² 选最优，再用全部训练部分重新拟合 | 同左 |
| **选出的值** | **α = 1000**（5 个 fold 模型和全样本模型都一样） | **max_depth = 6**（5 个 fold 模型和全样本模型都一样） |

**目标变量的截尾：** 按训练部分的 1% / 99% 分位 winsorize，下界为 0，上界约 0.643。

## 5. 第 2 步：分数怎么生成

代码在 `code/02_train_and_score.py`。

**交叉拟合（主版本，列名 `risk_score_<模型>`）：** 训练 5 个模型，每个模型只给自己留出的那个 fold 打分。

| 模型文件 | 训练用的 fold | 训练样本 | 打分的 fold | 打分的 firm-year |
|---|---|---|---|---|
| `models/<模型>/fold_0.*` | 1, 2, 3, 4 | 23,297 | 0 | 见 `results/metrics.json` |
| `models/<模型>/fold_1.*` | 0, 2, 3, 4 | 23,309 | 1 | |
| `models/<模型>/fold_2.*` | 0, 1, 3, 4 | 23,224 | 2 | |
| `models/<模型>/fold_3.*` | 0, 1, 2, 4 | 23,487 | 3 | |
| `models/<模型>/fold_4.*` | 0, 1, 2, 3 | 23,447 | 4 | |

每个模型的训练步骤：
1. 只取训练 fold 中 y 非缺失的行；
2. winsorize 阈值和预处理参数都只用这些行计算；
3. 在这 4 个 fold 上做 4 折分组交叉验证选超参数；
4. 用 4 个 fold 的全部数据重新拟合。

打分时会给留出 fold 中的**全部** firm-year 打分，包括 y 缺失的行。所以：
- 每个 firm-year 的分数只来自**一个**模型，而这个模型训练时**没有见过这家公司**（也没有见过和它共享 CEO 的公司），分数是样本外预测；
- 5 个模型合起来见过了全部数据，但不会用见过某家公司的模型去给这家公司打分；
- `results/risk_scores.parquet` 中的 `fold` 列标明了每个分数来自哪个模型。

**全样本版（列名 `risk_score_<模型>_full`）：** 用全部 29,191 个有 y 的 firm-year 训练一个模型，超参数同样用 5 折分组交叉验证选择，然后给所有 firm-year 打分。模型文件为 `models/<模型>/full.*`。

- **用途：** 对**新数据**（新年份、新公司）做推断。
- **不适合本样本分析：** 它对本样本的分数是样本内拟合，XGBoost 的样本内 R² 高达 0.898，明显虚高。

**4 个版本：** 每个分数列另有 3 个转换版本，都在全部 29,506 个 firm-year 上计算。

| 后缀 | 含义 | 范围（交叉拟合版） |
|---|---|---|
| （无） | 原始值：预测的 R&D / 总资产。线性模型和树模型都可能为负 | Ridge −0.106 到 0.431（26% 为负）；XGBoost −0.026 到 0.570（19% 为负） |
| `_clip0` | 负值截到 0 | ≥ 0 |
| `_pct` | 百分位排名，同值取平均排名 | (0, 1] |
| `_z` | 标准化：(原始值 − 均值) / 标准差 | 均值 0、标准差 1 |

## 6. 性能

指标在 29,191 个有 y 的 firm-year 上计算，y 用全样本模型的 winsorize 口径。

| | Ridge | XGBoost |
|---|---|---|
| **交叉拟合 R²**（样本外） | **0.5351** | **0.6128** |
| 交叉拟合 MSE | 0.00601 | 0.00500 |
| 与 y 的相关系数 | 0.7315 | 0.7829 |
| 各 fold 内部交叉验证 R² | 0.524–0.537 | 0.595–0.610 |
| 全样本模型的样本内 R² | 0.553 | 0.898（过拟合） |

- 两个模型交叉拟合分数之间的相关系数为 0.913。
- 作为参照，只预测均值时 MSE 约为 0.0129。

## 7. 第 3 步：小训练集稳健性

代码在 `code/03_seed_robustness.py`，结果见 `results/seed_robustness_report.md`。

- **做法：**
  - 用 3 个随机种子（1、2、3），在有 y 的 firm-year 上重新做分组、分层划分，切成 20% 训练、20% 验证、60% 测试。
  - 超参数网格中的每个取值只在训练集上拟合，按验证集 R² 选择。
  - 对照：交叉拟合分数在同一测试集上的表现。
- **结果：** 测试 R² 为 Ridge 0.507 ± 0.011、XGBoost 0.576 ± 0.009。交叉拟合分数在同一测试集上为 0.530 和 0.605。
- **含义：** 训练数据从约 80% 降到 20%，R² 只下降 0.02–0.03，结果对随机划分也不敏感。

## 8. 局限

- **补 0 带来的行业成分：** R&D 缺失补 0 会把"有研发但没单独披露"的公司记为 0。模型的一部分预测力来自区分做研发和不报 R&D 的行业（金融、公用事业、采矿等行业的 R&D 大多缺失）。
- **没有控制变量：** 分数里包含行业信息。比较行业内的差异时，需要在后续回归中加行业固定效应。
- **同期关联：** 讲话年份与 R&D 所在财年重叠，这不是事前预测。
- **topic 模型来源：** topic 模型来自另一项研究（CEO 政治意识形态），并在全部讲话语料上训练，测试公司的文本也参与了 topic 的估计。这是轻微的无监督泄露，与 R&D 无关。
- **公司匹配：** 公司只按 ticker 匹配，没有用公司名交叉核对。
