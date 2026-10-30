# Step 3：Synthetic proxy of CEO risk preference（Ridge / XGBoost）复现包

*2026-10-27*

这个包包含 Step 3 的全部内容：用 CEO 讲话的 topic 和情绪训练 Ridge 与 XGBoost，给每个 CEO-firm-year 计算 synthetic proxy of CEO risk preference（数据文件中的列名为 `risk_score_*`）。从 component 级数据开始，到 firm-year 输入表、模型训练、交叉拟合打分、稳健性检验，所有数据、代码、模型和结果都在包内，不需要联网，也不需要 WRDS。

- **synthetic proxy of CEO risk preference 是什么：** 用讲话内容预测出的 **R&D / 总资产**。它用 R&D 作为监督信号训练，衡量"讲话内容像不像高 R&D 的公司"。
- **用于后续分析：** 请使用**交叉拟合分数**（`risk_score_ridge`、`risk_score_xgboost` 及其转换版本，不带 `_full`）。Step 4 的回归用的就是交叉拟合版本中负值截到 0 的那一版（`_clip0`），并乘以 100，以百分点表示。

方法细节见 [docs/METHOD.md](docs/METHOD.md)。

## 1. 包内容

```
README.md                     本文件
requirements.txt              Python 包版本
MANIFEST.json                 全部文件的大小与 SHA-256
docs/METHOD.md                方法说明：数据、特征、模型、超参数、交叉拟合、性能、局限
data/
  components/components.parquet         CEO 发言段落（1,775,355 行；键、ticker、年份、发言人、词数、情绪）
  components/topic_distr.npz            每段发言的 354 维 topic 分布（与 components 的 row 列逐行对齐）
  compustat/compustat_panel_firms.csv   Compustat 年度数据（面板公司的全部年份）
  topic_selection/b1-gpt-6-astra-P0-xhigh.json   Step 2 的 topic 筛选（321 个）
  firm_year_inputs.parquet              firm-year 输入表（29,506 行；第 1 步的输出）
code/
  step3_lib.py                 共用函数（读取、构建、预处理、模型、划分、可移植格式）
  01_build_inputs.py           第 1 步：component → firm-year 输入表
  02_train_and_score.py        第 2 步：训练、交叉拟合打分、保存模型
  03_seed_robustness.py        第 3 步（可选）：20% 训练集稳健性
  04_verify.py                 第 4 步：校验
  tools/make_manifest.py       生成 MANIFEST.json
models/
  ridge/   fold_0 … fold_4、full   各有 .joblib（完整 Pipeline）和 .json（可移植格式）
  xgboost/ 同上；另有 .booster.json（XGBoost 原生格式）
results/
  risk_scores.parquet / .csv   每个 firm-year 的分数（29,506 行）
  metrics.json                 各 fold 的超参数、交叉验证 R²、交叉拟合与样本内指标
  seed_robustness_metrics.csv  稳健性检验的逐项结果
  seed_robustness_report.md    稳健性检验的说明与汇总
logs/02_train_and_score.log    生成交付结果时的运行日志
```

总大小约 446MB，其中 topic 矩阵占 342MB。

## 2. 分数文件 `results/risk_scores.parquet`

每行一个 CEO-firm-year，共 29,506 行。其中 315 行没有 R&D（总资产缺失），不参与训练，但同样有分数。

| 列 | 说明 |
|---|---|
| `panel_id` | 行号键，与 `data/firm_year_inputs.parquet` 一致 |
| `gvkey`, `year` | Compustat 公司代码；年份（讲话日期所在自然年，对应 Compustat `fyear`） |
| `ceo_id` | CEO 标识：`bx_<BoardEx directorid>`，或 `tp_<Capital IQ transcriptpersonid>` |
| `fold` | 交叉拟合的 fold（0–4），表示该行分数来自 `models/<模型>/fold_<fold>` |
| `risk_score_ridge`, `risk_score_xgboost` | **交叉拟合分数（主版本）** |
| `risk_score_ridge_full`, `risk_score_xgboost_full` | 全样本模型的分数（对本样本是样本内拟合，只用于对照或推断新数据） |

每个分数列有 4 个版本：

| 后缀 | 含义 |
|---|---|
| （无） | 原始值：预测的 R&D / 总资产，可能为负 |
| `_clip0` | 负值截到 0 |
| `_pct` | 百分位排名，范围 (0, 1] |
| `_z` | 标准化，均值 0、标准差 1 |

转换版本都在全部 29,506 行上计算。

## 3. 运行环境

Python 3.11，包版本见 `requirements.txt`：

```bash
pip install -r requirements.txt
```

- **joblib 模型：** 需要**相同版本**的 scikit-learn（1.2.2）和 xgboost（2.1.1）才能保证加载。版本不同时，请改用可移植的 JSON 格式（见第 5 节）。
- **训练耗时：** XGBoost 默认用 16 个线程，约 12 分钟；线程数可以在 `code/step3_lib.py` 的 `N_JOBS` 中修改，不影响结果。
- **内存：** 第 1 步峰值约 6GB。

## 4. 复现步骤

所有命令都在**包根目录**运行。重跑的输出默认写到 `rerun/`，不会覆盖交付的结果。

```bash
python code/04_verify.py                 # 先校验交付内容（约 1 分钟）
python code/01_build_inputs.py           # 第 1 步：component → rerun/firm_year_inputs.parquet（约 0.5 分钟）
python code/02_train_and_score.py        # 第 2 步：训练 + 打分 → rerun/models、rerun/results（约 13 分钟）
python code/03_seed_robustness.py        # 第 3 步：稳健性 → rerun/results/seed_robustness_metrics.csv（约 6 分钟）
python code/04_verify.py                 # 再次校验：比较 rerun/ 与交付结果
```

- 第 2、3 步默认读取交付的 `data/firm_year_inputs.parquet`。如果想用第 1 步重建的版本，加上 `--inputs rerun/firm_year_inputs.parquet`。
- 只跑 Ridge 时，加上 `--models ridge`。

**`04_verify.py` 检查的内容：**

| 编号 | 检查内容 |
|---|---|
| A | MANIFEST 中全部文件的大小与 SHA-256 |
| B | 用 5 个 fold 模型和全样本模型重新打分，与交付的分数比较（容差 1e-9） |
| C | 可移植 JSON 格式的预测与 joblib 模型一致 |
| D | 3 个转换版本可由原始分数重算 |
| E–G | 如果存在 `rerun/`，比较重建的输入表、重跑的分数和稳健性指标与交付版本 |

**参考值：**

| | Ridge | XGBoost |
|---|---|---|
| 选出的超参数 | α = 1000 | max_depth = 6 |
| 交叉拟合 R² | 0.5351 | 0.6128 |
| 交叉拟合 MSE | 0.006006 | 0.005001 |
| 与 y 的相关系数 | 0.7315 | 0.7829 |

第 1 步各环节的行数：1,775,355 段发言 → 匹配 Compustat 后 1,547,519 → 保留主 CEO 后 1,420,208 → 29,506 个 firm-year，其中有 R&D 的 29,191 个。

## 5. 加载模型、对新数据打分

新数据需要先按 `docs/METHOD.md` 第 2 节的方法构造成 firm-year 表，包含 `sent_transformer` 和 `topic_000`…`topic_353` 列，然后有两种方式打分。

**方式一：joblib（需要相同的库版本）**

```python
import sys, joblib
sys.path.insert(0, "code")                  # 模型引用了 step3_lib.clr
bundle = joblib.load("models/xgboost/full.joblib")
score = bundle["pipeline"].predict(new_df)  # Pipeline 内部会选取 321 个 topic 列，并做 CLR 和标准化
```

**方式二：可移植 JSON（不依赖 scikit-learn 的版本）**

```python
import sys
sys.path.insert(0, "code")
import step3_lib as L
score = L.predict_portable("models/xgboost/full.json", new_df)   # Ridge 只需要 numpy；XGBoost 需要 xgboost
```

JSON 文件记录了特征顺序、情绪的填补值和标准化参数、321 个 topic 的列名和标准化参数，以及 Ridge 的系数和截距（XGBoost 指向同名的 `.booster.json`）。

**选哪个模型：**
- 对新数据打分，用 `full` 模型；
- 重现本样本的交叉拟合分数，用 `fold_k` 模型给 `fold == k` 的行打分。

## 6. 数据使用

数据来自 Capital IQ（电话会议）、Compustat 和 BoardEx，受相应的数据授权约束，只能在授权范围内用于本研究合作，请勿公开或转发。
