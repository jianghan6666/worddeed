# ceo-rd：用 CEO 讲话 topic 预测公司 R&D 强度

本项目从 Capital IQ 电话会议记录出发，先用 BERTopic 得到每段发言的 topic 分布，再汇总成 CEO-公司-年度的特征，用来预测公司的 R&D 强度。项目分为四部分：

| 部分 | 内容 | 文档 |
|---|---|---|
| 1. Topic 模型训练 | 354 个 topic 的 BERTopic 模型是怎么训练的（all-mpnet-base-v2 + UMAP + HDBSCAN + c-TF-IDF），怎样重新训练，以及可以优化的方向 | [docs/1_topic_model_training.md](docs/1_topic_model_training.md) |
| 2. Topic 推断 | 用已训练的模型得到每段发言的 topic 分布与主 topic | [docs/2_topic_inference.md](docs/2_topic_inference.md) |
| 3. Topic 描述 | 354 个 topic 的名称、关键词、规模与代表性发言 | [docs/3_topic_descriptions.md](docs/3_topic_descriptions.md)、[Excel](docs/topic_descriptions_354Topics.xlsx) |
| 4. R&D 预测 | 数据、样本构建、实验设计、运行方法、结果与结论 | [docs/4_rd_prediction.md](docs/4_rd_prediction.md) |

## 安装

在项目根目录（需要 Python ≥ 3.10）：

```bash
pip install -e ".[dev]"        # R&D 预测与 topic 描述：numpy、pandas、scikit-learn、xgboost 等
pip install -e ".[topics]"     # 另外安装 topic 模型的训练与推断：bertopic==0.16.4、sentence-transformers、umap-learn、hdbscan
pytest                         # 用合成数据测试，几秒钟，不需要原始数据，也不需要 BERTopic
```

topic 模型的训练和推断计算量大（需要计算文本 embedding 时建议用 GPU），只在需要时安装 `.[topics]`。R&D 预测和 topic 描述不需要它。

## 数据与路径配置

数据有授权限制，以单独的数据包提供（见下）。数据路径在 `configs/paths.yaml` 中配置：

| 字段 | 内容 | 用于 |
|---|---|---|
| `transcripts` | transcript component 级数据（pickle，不含文本），index 为 0..N-1，与 topic 矩阵逐行对齐 | R&D 预测 |
| `topics` / `topics_key` | 每段发言的 topic 分布（npz，N × 354，数组名 `topic_distr`） | R&D 预测 |
| `compustat` | Compustat Fundamentals Annual（CSV） | R&D 预测 |
| `corpus` | 含文本的 pickle（`componenttext_masked`、`averageDem` 等列），行顺序与 `transcripts` 一致 | topic 训练 / 推断 |
| `models_dir` | topic 模型目录（默认 `models/`） | topic 训练 |
| `panel_dir` / `results_dir` | 面板与实验结果的输出目录 | R&D 预测 |

相对路径以运行命令时的工作目录（项目根目录）为基准。

**数据包：** 数据包包含运行四个部分所需的全部数据：
- R&D 预测用的子样本 `replication_sample/`，用它得到的结果与完整数据完全一致；
- topic 训练 / 推断用的全部发言文本（约 7.7GB）。

使用步骤：
1. 把数据包解压到项目的 `data/` 下；
2. 运行 `cp data/replication_sample/paths.yaml configs/paths.yaml`。

之后四个部分都可以直接运行，说明见 `data/replication_sample/README.md`。

## 快速上手

```bash
# 1. topic 模型训练（需要 .[topics] 与 corpus）
ceo-rd topics train topic_models/bertopic_ideo_13-23_relaxed.yaml

# 2. topic 推断（需要 .[topics] 与 corpus）
ceo-rd topics infer  models/bertopic_ideo_13-23_relaxed_354Topics --out topic_distr.npz            # topic 分布
ceo-rd topics assign models/bertopic_ideo_13-23_relaxed_354Topics --out topic_assignments.parquet  # 主 topic
ceo-rd topics training-labels models/bertopic_ideo_13-23_relaxed_354Topics --out training_topic_labels.parquet

# 3. topic 描述（只读模型文件）
ceo-rd topics describe models/bertopic_ideo_13-23_relaxed_354Topics --out docs/topic_descriptions_354Topics.xlsx

# 4. R&D 预测
ceo-rd build-panel
ceo-rd run experiments/strict_controls.yaml      # 结果在 results/strict_controls/（含 report.md）
```

各命令的选项见 `ceo-rd <命令> --help` 和对应的文档。

## 项目结构

```
README.md
pyproject.toml                 包 ceo-rd（import ceo_rd），命令行 ceo-rd
configs/paths.example.yaml     数据路径模板
docs/                          四部分文档与 topic 描述 Excel
models/bertopic_ideo_13-23_relaxed_354Topics/   已训练的 354 topic BERTopic 模型
topic_models/*.yaml            topic 模型训练配置（记录了现有模型的全部参数）
experiments/*.yaml             R&D 预测实验配置
src/ceo_rd/
  topics/        topic 模型：spec 配置、corpus 读取文本、train 训练、infer 推断（分布 / 主 topic）、
                 describe 描述、modelfiles 直接读取模型文件
  data.py        读取 transcript 与 Compustat；topic 矩阵分块读写（全量约 16GB，避免一次载入）
  panel.py       构建 CEO-公司-年度面板
  features.py    变量注册表、目标变量、预处理
  splits.py      按公司分组的训练 / 测试划分
  models.py      模型注册表（Ridge、XGBoost、MLP、Random Forest）
  evaluation.py  指标与 cluster bootstrap
  experiment.py  实验运行器
  report.py      结果汇总表
  cli.py         命令行
scripts/make_replication_sample.py   从完整数据生成复现用子样本
tests/                         合成数据测试
legacy/                        重构前的脚本与 notebook（仅供参考；notebooks/ 中有训练现有 topic 模型的原 notebook）
```
