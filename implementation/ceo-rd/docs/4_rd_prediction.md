# 4. 用 CEO 讲话 topic 预测公司 R&D 强度

## 4.1 研究问题

CEO 在电话会议和投资者会议上的讲话 topic，在规模、行业、年份等常规控制变量之外，能否预测公司当年的 R&D 强度？

- **主结果：** R&D / 总资产。
- **稳健性：** R&D / 销售额。

这是一个 **回归任务**，预测连续的 ratio。R&D 强度主要由行业决定，而且在公司内部高度持续，topics 又很容易识别行业，所以只看 topics 的 R² 会高估文本的价值。因此本研究的核心指标是 **topics 相对控制变量的测试集 R² 增量（ΔR²）**，并逐步加严控制变量。

## 4.2 数据

| 数据 | 内容 |
|---|---|
| transcript 表 | Capital IQ 的 transcript component 级数据（不含文本），2013–2023 年 |
| topic 矩阵 | 每段发言的 354 维 topic 分布（见文档 2），与 transcript 表逐行对齐 |
| Compustat | Fundamentals Annual：`at`、`sale`、`xrd`、`sich` 等 |

**复现用子样本：** 数据包中的 `replication_sample/` 只含面板构建需要的行。用它得到的面板和实验结果，与用完整数据得到的完全一致。R&D 预测不需要数据包中的文本 pickle，它只用于 topic 训练和推断。

| 文件 | 行数 |
|---|---|
| transcript 表：全部 `is_ceo` 行，79 列，另加 `orig_row` | 1,775,355 |
| 对应的 topic 行 | 1,775,355 |
| 面板公司的 Compustat 行 | 53,729 |

**需要知道的数据特点：**

- **公司匹配：** transcript 数据中没有 gvkey，所以用 ticker（`symbolvalue`）加讲话年份，匹配 Compustat 的 `tic` 加 `fyear`。
  - 讲话年份是讲话日期（`mostimportantdateutc`）的自然年。
  - Compustat 的 `fyear` 是会计年度，所以这是**同期关联**，不是严格的事前预测。
- **`is_ceo` 标记偏宽：** 混入了子公司 CEO、CFO、COO 等。每个公司-年只保留发言词数最多的那位 CEO，他平均贡献 95% 的词数。
  - CEO 身份优先用 BoardEx 的 `directorid`；缺失时用 `transcriptpersonid`。
- **R&D 缺失：** `xrd` 缺失 42.7%，而且是结构性的，集中在金融（72%）、交通 / 公用事业（90%）、采矿（91%）、建筑（98%）等不做研发的行业。
  - 主结果把缺失视为 0，缺失视为 0 之后，55% 的公司-年 R&D 为 0。
  - 缺失是公司层面的固定特征：有 ≥3 年数据的公司中，40% 每年都缺失，56% 从不缺失，只有 4% 会切换。
  - 有的公司把研发并入 SG&A，所以"缺失 = 0"并不总是成立（Koh & Reeb, 2015）。

## 4.3 样本构建与变量

由 `ceo-rd build-panel` 生成，约 1 分钟。

| 步骤 | 处理 | 剩余 component |
|---|---|---|
| 1 | 保留 `is_ceo` | 1,775,355 |
| 2 | 匹配 Compustat | 1,547,519 |
| 3 | 每个公司-年只保留词数最多的 CEO | 1,420,208 |
| 4 | topic pooling 时排除 topic 全为 0 的发言（多为极短发言） | 1,411,341 参与 pooling |

**面板：** `data/panel/ceo_firm_year_panel.parquet`，共 29,506 个公司-年（firm-year）× 390 列，覆盖 4,517 家公司、6,933 位 CEO，年份 2013–2023。每个公司-年平均有 48 段发言。

| 变量 | 定义 |
|---|---|
| `topic_000` … `topic_353` | 主 CEO 当年所有发言的 topic 分布，按词数（`retained_word_count`）加权平均 |
| `rd_at_fill0` / `rd_sale_fill0` | xrd / at、xrd / sale，xrd 缺失视为 0（**主结果：`rd_at_fill0`**） |
| `rd_at` / `rd_sale` | 同上，xrd 缺失时为 NaN |
| `rd_at_lag` / `rd_sale_lag` | 上一财年的 ratio |
| `log_at`、`sich` | 规模；Compustat 历史 SIC 行业 |
| `ceo_gender` / `ceo_age` / `ceo_educ` | 主 CEO 的性别、年龄、学历（覆盖 84% 的公司-年） |
| `sent_transformer` | 讲话情绪 `sentiment_transformer`，按词数加权平均 |
| `fold`、`split_group` | 训练 / 测试划分 |
| `panel_id` | 可以通过 `component_map.parquet` 回溯到原始发言行 |

## 4.4 实验设计

- **划分：** 同一公司的所有年份，以及共享 CEO 的公司，都放在同一组（firm–CEO 连通分量，共 4,249 组）。然后用 `StratifiedGroupKFold`（5 折，按是否有 R&D 分层）划分。
  - **fold 0 为测试集**，约 20%。
  - 其余 4 折做分组交叉验证调参。
  - 只按 CEO 切分会泄露公司身份。
- **预处理：** 全部只在训练集上拟合。
  - 目标变量按训练集 1% / 99% 分位截尾。
  - topics 做 CLR 变换（成分数据）后标准化。
  - 数值变量中位数填补后标准化；类别变量 one-hot。
- **控制变量：**
  - 基准：log(总资产)、SIC 两位数行业、年份。
  - 更严格的版本依次替换或加入：SIC 三位 / 四位数行业、上一年 R&D 强度、CEO 性别 / 年龄 / 学历。
- **模型：**
  - Ridge（线性）；
  - XGBoost（非线性）；
  - 主实验另有 MLP 和 Random Forest。
- **指标：**
  - 测试集 R²、RMSE、Spearman。
  - 核心指标是 ΔR²，95% 置信区间按分组做 1,000 次 cluster bootstrap。
  - RMSE 的单位是 ratio 本身：测试集 R&D / 总资产截尾后均值 0.051、标准差 0.112，所以只预测均值的模型 RMSE 约为 0.112。

## 4.5 运行

```bash
cp data/replication_sample/paths.yaml configs/paths.yaml     # 使用复现子样本
ceo-rd build-panel
ceo-rd run experiments/strict_controls.yaml                  # 约 17 分钟
ceo-rd run experiments/ceo_demo.yaml                         # 约 19 分钟
ceo-rd run experiments/sentiment.yaml                        # 约 27 分钟
ceo-rd run experiments/main.yaml                             # 4 个模型 × 4 组目标，需要数小时
```

上面的耗时是在 20 核 CPU 上测得的。只跑一部分时，用 `--models ridge`、`--targets rd_at_fill0` 指定，并用 `--out` 指向别的目录，避免覆盖完整结果。

在 Python 中：

```python
import ceo_rd
ceo_rd.enable_logging()
panel = ceo_rd.load_panel()
res = ceo_rd.run_experiment("experiments/strict_controls.yaml")   # 也可以传 dict 配置或 panel=...
res.deltas                                                        # ΔR²、置信区间、RMSE
```

### 换用新的 topic 特征

如果按文档 1 的方向重新训练或优化了 topic 模型，可以这样换用新的特征：

1. 用 `ceo-rd topics infer <新模型> --rows-from data/replication_sample/transcripts_is_ceo.pickle --out <文件>`，只对 R&D 需要的行推断（见文档 2 的 2.3 节）；
2. 把 `configs/paths.yaml` 中的 `topics` 改成新文件；
3. 重新运行 `build-panel` 和各实验。

- topic 数可以不是 354。
- 运行实验时用 `ceo-rd run ... --out results/<新目录>`，就可以和现有结果直接比较 ΔR²。
- `build-panel` 会覆盖 `data/panel/` 中的面板。把 `topics` 改回原文件、重新运行一次，就能恢复。

### 实验配置

`experiments/` 下每个 YAML 是一个实验：

| 文件 | 内容 |
|---|---|
| `strict_controls.yaml` | 更严格的控制变量：SIC3 / SIC4、上一年 R&D 强度 |
| `ceo_demo.yaml` | 控制变量中加入 CEO 性别、年龄、学历 |
| `sentiment.yaml` | 加入讲话情绪：topics 与 topics + 情绪 |
| `main.yaml` | 4 组目标变量 × {controls, topics, controls + topics} × Ridge / XGBoost / MLP / RF |

格式：

```yaml
name: strict_controls            # 结果目录名
targets: [rd_at_fill0, rd_sale_fill0]
require: [y_lag]                 # 样本限定：这些变量非缺失

control_sets:                    # 每个 control set × text set 组合都会运行，特征 = 两者变量之和
  base:     [log_at, sic2, year]
  lag+sic4: [log_at, y_lag, sic4, year]
text_sets:
  none:   []
  topics: [topics]

models:
  ridge: {}                      # 默认调参网格
  xgboost:
    params: {min_child_weight: 10}   # 覆盖默认参数
    grid: {max_depth: [3, 6]}        # 覆盖调参网格

comparisons:                     # 计算哪些 R² 增量
  - label: topics | controls
    text: [none, topics]         # 在每个 control set 内比较两个 text set
  - label: lag
    control: [base, lag+sic4]    # 在每个 text set 内比较两个 control set（可给多组）
```

可选字段：`test_fold`（默认 0）、`winsorize`（默认 `[0.01, 0.99]`）、`n_boot`（默认 1000）、`seed`（默认 42）、`n_jobs`。

| 可用变量 | 类型 | 说明 |
|---|---|---|
| `log_at` | numeric | log(总资产) |
| `y_lag` | numeric | 上一年 R&D ratio（与目标变量同口径） |
| `ceo_age` | numeric | CEO 年龄 |
| `sentiment` | numeric | 讲话情绪 |
| `sic2` / `sic3` / `sic4` | categorical | SIC 行业 |
| `year` | categorical | 年份固定效应 |
| `ceo_gender` / `ceo_educ` | categorical | CEO 性别 / 学历 |
| `topics` | topics | 354 维 topic 分布 |

- **目标变量：**
  - `rd_at_fill0`（主结果）、`rd_at`；
  - `rd_sale_fill0`、`rd_sale`；
  - 带 `fill0` 的表示 R&D 缺失视为 0。
- **模型：** `ridge`、`xgboost`、`mlp`、`random_forest`，默认参数与网格见 `src/ceo_rd/models.py`。
- **加入新变量：**
  1. 在 `src/ceo_rd/panel.py` 中生成对应的列；
  2. 在 `src/ceo_rd/features.py` 的 `NUMERIC` / `CATEGORICAL` 中注册；
  3. 重新运行 `build-panel`。

### 输出

每个实验的结果目录 `results/<name>/` 包含：

| 文件 | 内容 |
|---|---|
| `metrics.csv` | 每个组合的交叉验证 R²、测试集 R² / RMSE / Spearman、选中的超参数 |
| `deltas.csv` | 每个比较的 ΔR²、95% 置信区间、RMSE |
| `predictions.parquet` | 测试集预测值 |
| `report.md` | 汇总表 |
| `spec.yaml`、`log.txt` | 本次运行的配置与日志 |

## 4.6 结果

粗体表示 95% 置信区间不包含 0。以下数字可以用上面的命令复现。

### 更严格的控制变量（`strict_controls`）

样本要求上一年 R&D 非缺失；测试集 5,871 个公司-年。

**R&D / 总资产**

| 控制变量 | 模型 | R²：controls | R²：+ topics | ΔR² [95% CI] | RMSE：controls → + topics |
|---|---|---|---|---|---|
| 规模 + SIC2 + 年份 | Ridge | 0.423 | 0.616 | **+0.193 [0.152, 0.239]** | 0.0849 → 0.0693 |
| | XGBoost | 0.534 | 0.729 | **+0.195 [0.145, 0.258]** | 0.0763 → 0.0582 |
| 规模 + SIC3 + 年份 | Ridge | 0.518 | 0.620 | **+0.101 [0.064, 0.143]** | 0.0776 → 0.0690 |
| | XGBoost | 0.582 | 0.727 | **+0.145 [0.098, 0.202]** | 0.0723 → 0.0584 |
| 规模 + SIC4 + 年份 | Ridge | 0.545 | 0.624 | **+0.079 [0.051, 0.112]** | 0.0754 → 0.0686 |
| | XGBoost | 0.596 | 0.730 | **+0.134 [0.093, 0.181]** | 0.0711 → 0.0581 |
| SIC2 + 上一年 R&D | Ridge | 0.823 | 0.832 | **+0.010 [0.005, 0.015]** | 0.0471 → 0.0458 |
| | XGBoost | 0.862 | 0.865 | +0.004 [−0.004, 0.012] | 0.0416 → 0.0410 |
| SIC4 + 上一年 R&D | Ridge | 0.828 | 0.833 | **+0.005 [0.001, 0.010]** | 0.0464 → 0.0457 |
| | XGBoost | 0.864 | 0.865 | +0.001 [−0.006, 0.008] | 0.0413 → 0.0411 |

- **当年与上一年 R&D 强度的相关：** 0.893。
- **加入上一年 R&D 后排序变差：** 加入 topics 后 R² 略升，但 Spearman 秩相关下降（Ridge 0.856 → 0.816）。这说明 topics 在零 R&D 公司内部引入了排序噪声。

**R&D / 销售额**（稳健性；测试集 5,713）：方向相同，噪声更大。

| 控制变量 | Ridge ΔR² | XGBoost ΔR² |
|---|---|---|
| SIC2 | **+0.138 [0.060, 0.194]** | **+0.161 [0.024, 0.282]** |
| SIC3 | **+0.092 [0.023, 0.151]** | **+0.166 [0.032, 0.298]** |
| SIC4 | +0.050 [−0.027, 0.097] | +0.108 [−0.003, 0.220] |
| SIC2 + 上一年 R&D | +0.018 [−0.003, 0.033] | +0.021 [−0.017, 0.058] |
| SIC4 + 上一年 R&D | +0.007 [−0.011, 0.018] | +0.013 [−0.022, 0.046] |

### CEO 个人特征（`ceo_demo`）

样本要求 CEO 三项特征都非缺失，约为上面样本的 84%；测试集 4,891 个公司-年。下表为 R&D / 总资产。

| 控制变量 | 模型 | CEO 特征本身的 ΔR²（不含 topics） | topics 的 ΔR²：不加 CEO 特征 | topics 的 ΔR²：加 CEO 特征 |
|---|---|---|---|---|
| SIC2 | Ridge | **+0.012 [0.000, 0.025]** | **+0.189 [0.144, 0.243]** | **+0.177 [0.133, 0.226]** |
| | XGBoost | +0.013 [−0.010, 0.035] | **+0.178 [0.127, 0.242]** | **+0.158 [0.109, 0.224]** |
| SIC4 | Ridge | +0.001 [−0.004, 0.006] | **+0.079 [0.044, 0.112]** | **+0.078 [0.046, 0.111]** |
| | XGBoost | +0.005 [−0.014, 0.021] | **+0.118 [0.076, 0.173]** | **+0.120 [0.074, 0.178]** |
| SIC4 + 上一年 R&D | Ridge | +0.000 [−0.000, 0.001] | **+0.007 [0.002, 0.012]** | **+0.006 [0.002, 0.012]** |
| | XGBoost | −0.000 [−0.004, 0.003] | −0.001 [−0.010, 0.008] | −0.001 [−0.010, 0.008] |

R&D / 销售额：CEO 特征的增量全部不显著。

### 讲话情绪（`sentiment`）

样本与 `strict_controls` 相同；下表为 R&D / 总资产。在有控制变量的行里，"topics"指 controls + topics。

| 控制变量 | 模型 | R²：topics | R²：topics + 情绪 | 情绪在 topics 之上的 ΔR² | 情绪在 controls 之上的 ΔR² |
|---|---|---|---|---|---|
| 无 | Ridge | 0.571 | 0.571 | +0.000 [−0.000, 0.000] | – |
| | XGBoost | 0.646 | 0.649 | +0.003 [−0.003, 0.009] | – |
| SIC2 | Ridge | 0.616 | 0.616 | −0.000 [−0.001, 0.000] | +0.001 [−0.003, 0.004] |
| | XGBoost | 0.729 | 0.733 | +0.004 [−0.002, 0.010] | +0.006 [−0.000, 0.011] |
| SIC4 | Ridge | 0.624 | 0.624 | −0.000 [−0.000, 0.000] | −0.000 [−0.001, 0.001] |
| | XGBoost | 0.730 | 0.726 | −0.004 [−0.010, 0.001] | +0.003 [−0.002, 0.007] |
| SIC4 + 上一年 R&D | Ridge | 0.833 | 0.833 | +0.000 [−0.000, 0.000] | +0.000 [−0.000, 0.000] |
| | XGBoost | 0.865 | 0.864 | −0.000 [−0.004, 0.003] | **−0.002 [−0.005, −0.000]** |

- **只用情绪时：** R² 约为 0.005。
- **R&D / 销售额：** 只有 SIC2 + XGBoost 下，情绪在 topics 之上为 +0.024 [0.001, 0.044]，但在 SIC4 下为 −0.012，方向不稳定。

### 主实验（`main.yaml`）

主实验用新的代码结构还没有完整运行过。之前只完成了 R&D / 总资产的一部分，样本不要求上一年 R&D 非缺失，测试集 5,894。测试集 R² 如下：

| 模型 | controls | topics | controls + topics |
|---|---|---|---|
| Ridge | 0.423 | 0.569 | 0.614 |
| XGBoost | 0.534 | 0.641 | 0.725 |
| MLP | 0.535 | 0.612 | 未跑 |
| Random Forest | 0.534 | 未跑 | 未跑 |

## 4.7 结论

1. **topics 的横截面预测力强，而且比四位数 SIC 更细。** 在规模、行业、年份之外，R² 提高约 0.19；换成 SIC4 后仍有 0.08–0.13，置信区间远离 0。
2. **几乎不能解释 R&D 的逐年变化。** 控制上一年 R&D 强度后，ΔR² ≤ 0.01。topics 反映的主要是"这是什么样的公司"这类长期稳定的特征。
3. **topics 的增量不是 CEO 可观测特征的代理。** CEO 性别、年龄、学历几乎没有预测力，加入后 topics 的增量也基本不变。
4. **有预测力的是 CEO 谈什么，而不是以什么语气谈。** 讲话情绪没有预测力。
5. **线性和非线性模型的增量相近。** XGBoost 对控制变量本身拟合更好，但 topics 的 ΔR² 与 Ridge 相近，结论不依赖模型。
6. **以 R&D / 总资产为主结果。** R&D / 销售额噪声大、置信区间宽。

## 4.8 局限与可扩展的方向

**局限：**
- **同期关联：** 讲话年份与 R&D 支出的财年在时间上重叠，当年的总资产在财年结束前也拿不到。改为用上一年的特征预测当年 R&D，可以得到严格的事前预测。
- **R&D 缺失：** 把缺失视为 0，会把"有研发但未单列"的公司错记为 0。topics 的一部分预测力来自区分做研发和不做研发的行业。
- **topic 模型训练语料：** 训练时用了全部语料中有意识形态标签的发言，测试集公司的文本也可能参与了 topic 的估计。这是轻微的无监督泄露。
- **其他：**
  - 公司只按 ticker 匹配，没有用公司名做交叉验证。
  - 同一年内换了 CEO 时，只保留发言最多的一位。

**可扩展的方向：**
1. **公司内部变化：** 用 topics 的年度变化预测 R&D 强度的年度变化，或者利用 CEO 更替事件。这对研究 CEO 风险偏好更有说服力。
2. **R&D 缺失的处理：**
   - 剔除金融（SIC 60–67）和公用事业（SIC 49）；
   - 只用报告过 R&D 的公司；
   - 用两段式（hurdle）模型：先预测是否有 R&D，再预测强度。
3. **因变量与模型：** 对因变量取 log(1 + ratio)，或者换成其他风险承担指标，例如资本支出、股票收益波动率、专利。
4. **解释与细化：**
   - 用 Ridge 系数或 SHAP 找出贡献最大的 topic；
   - 把 Presentation 和 Q&A 分开 pooling（面板中已有 `pres_word_share`）；
   - 做时间外检验：用 2013–2019 训练，2021–2023 测试。
5. **按研究需要优化 topic 模型：** 见 [1_topic_model_training.md](1_topic_model_training.md) 第 1.6 节。
