# 2. 用已训练的模型做 Topic 推断

本文说明怎样用 354 个 topic 的模型 `models/bertopic_ideo_13-23_relaxed_354Topics/`，为每一段发言（transcript component）得到两种结果：

- **topic 分布（density）：** 一个 354 维向量，表示这段发言在各个 topic 上的分布。R&D 预测用的就是它。
- **主 topic：** BERTopic 给这段发言分配的单个 topic 类别，可能是离群类 -1。

推断（`infer`、`assign`）需要安装可选依赖：`pip install -e ".[topics]"`（bertopic==0.16.4 等）。训练标签（2.2 节的方法 1）只读模型文件，不需要安装 BERTopic。

## 2.1 Topic 分布

### 方法

用 BERTopic 的 `approximate_distribution`，只基于 c-TF-IDF，**不需要计算 embedding**：

1. 把每段发言切成长度为 4 个词的滑动窗口（`window=4, stride=1`）；
2. 计算每个窗口与每个 topic 的 c-TF-IDF 相似度，相似度低于 0.1 的记为 0（`min_similarity=0.1`）；
3. 把所有窗口的相似度相加，归一化，使每行和为 1。

如果一段发言没有任何窗口超过阈值（多为极短的发言），整行为 0。全量数据中这样的行有 45,704 段（0.8%）。

**列的含义：** 第 j 列对应 topic j（j = 0…353），**不含离群类 -1**。

### 命令

```bash
ceo-rd topics infer models/bertopic_ideo_13-23_relaxed_354Topics --out data/topic_density/topic_distr.npz
```

- **输入：** 默认是 `paths.yaml` 中 `corpus`（数据包中的文本 pickle）的全部行。
  - 换别的文件：`--input <文件> --text-col <列名>`，支持 pickle / parquet / csv。
  - 只处理某个列非缺失的行：`--filter-notna <列名>`。
  - 只处理指定的行：`--rows-from <文件>`，见 2.3。
- **参数：** 默认值与生成现有数据时完全相同（`window=4, stride=1, min_similarity=0.1, batch_size=1000, use_embedding_model=False`），可以用同名选项修改。
- **耗时：** 全量 5,765,638 段在原机器上约 3.7 小时。
  - 结果按块（`--chunk-size`，默认 10 万段）写到 `<输出>.parts/`，中断后重新运行同一命令会从断点继续，全部完成后再合并。
  - 输出文件已存在时需要加 `--overwrite`。

### 输出

- **`topic_distr.npz`：** 数组 `topic_distr`（N × 354，float64）。用了 `--filter-notna` 或 `--rows-from` 时，还会有数组 `row_index`，记录每一行在输入文件中的行号。
- **`topic_distr.npz.meta.json`：** 输入、参数、行数、全 0 行数、各个库的版本。

**对齐：** 第 i 行对应输入文件的第 i 行。全量推断时，就对应 transcript 数据的第 i 行。本项目的 transcript 数据、topic 矩阵和复现子样本都按行号对齐。

```python
import numpy as np, pandas as pd
distr = np.load("data/topic_density/topic_distr.npz")["topic_distr"]       # 全量约 16GB，注意内存
df = pd.read_pickle("data/<transcript 数据>.pickle")
df["main_topic_by_density"] = np.where(distr.sum(1) > 0, distr.argmax(1), -1)  # 见 2.2 的方法 3
```

## 2.2 主 Topic

BERTopic 本身会给每段文本一个主 topic。用于训练的 887,488 段文本，训练时已经有主 topic；其他文本则需要用模型的 `transform` 分配。共有三种获得方式：

| | 方法 1：训练标签 | 方法 2：BERTopic transform | 方法 3：分布取最大值 |
|---|---|---|---|
| 命令 | `ceo-rd topics training-labels` | `ceo-rd topics assign` | 对 2.1 的结果取 argmax |
| 覆盖范围 | 只有 887,488 段训练文本 | 任意文本 | 任意文本 |
| 依据 | 训练时 UMAP + HDBSCAN 的聚类结果 | 文本 embedding 与 355 个 topic embedding 的余弦相似度 | c-TF-IDF 窗口相似度 |
| 需要 | 只读模型文件 | BERTopic + `all-mpnet-base-v2`，计算每段文本的 embedding（建议用 GPU） | 已有的 topic 分布 |
| 离群类 -1 | 54.4% | 与"离群类"的 topic embedding 最相似时为 -1 | 分布全为 0 时记为 -1 |

### 方法 1：训练标签

```bash
ceo-rd topics training-labels models/bertopic_ideo_13-23_relaxed_354Topics --out training_topic_labels.parquet
```

- **输出：** parquet，列为 `row`（训练文本在 corpus 中的行号）和 `topic`。
- **训练文本的行号：** 由 corpus 中 `averageDem` 非缺失的行确定。用 `ceo-rd topics train` 训练的新模型，会把行号保存在模型目录的 `train_row_index.npy` 中，这时不需要 corpus。

### 方法 2：BERTopic transform

```bash
ceo-rd topics assign models/bertopic_ideo_13-23_relaxed_354Topics --out topic_assignments.parquet
```

- **原理：** 模型以 safetensors 格式保存，不含 UMAP / HDBSCAN。所以 `transform` 的做法是：
  1. 用 `all-mpnet-base-v2` 计算文本的 embedding；
  2. 计算它与 355 个 topic embedding（含 -1）的余弦相似度；
  3. 取最大者作为主 topic。
  
  因此，对训练文本用这种方法得到的结果，与方法 1 不完全相同。
- **embedding 模型：** 现有模型没有记录 embedding 模型的名称，命令默认使用 `sentence-transformers/all-mpnet-base-v2`（首次使用会自动下载）。也可以用 `--embedding-model <本地目录>` 指定。
- **输出：** parquet，列为 `row`（行号）、`topic`（主 topic）、`topic_prob`（与该 topic embedding 的余弦相似度）。
- **分块与断点续跑：** 和 `infer` 相同（`--chunk-size` 默认 5 万段）。全量 5.77M 段需要逐段计算 embedding，建议在 GPU 上运行。

### 方法 3：分布取最大值

不需要额外计算，见 2.1 的代码示例。

**注意：** 这不是 BERTopic 本身给出的类别。它反映的是用词上与哪个 topic 最接近，适合在无法计算 embedding 时作为近似。

## 2.3 与 R&D 预测衔接：只对需要的行推断

R&D 预测只用到 CEO 发言，也就是数据包中 `replication_sample/transcripts_is_ceo.pickle` 的 1,775,355 行。它的 `orig_row` 列就是这些行在文本 pickle 中的行号。

用 `--rows-from` 只对这些行推断，计算量约为全量的 1/3。输出与子样本逐行对齐，可以直接用于 R&D 预测：

```bash
ceo-rd topics infer models/<模型> --rows-from data/replication_sample/transcripts_is_ceo.pickle --out data/topic_density/<模型>_is_ceo.npz
# 把 configs/paths.yaml 中的 topics 改成上面的输出文件，然后重新构建面板、运行实验
ceo-rd build-panel
ceo-rd run experiments/strict_controls.yaml --out results/strict_controls_<模型>
```

- **主 topic：** `ceo-rd topics assign` 同样支持 `--rows-from`。
- **新模型的 topic 数：** 用重新训练的模型推断时，topic 数可以不是 354，面板构建和实验会自动适应。

**首次使用时建议先验证。** 用现有模型对少量行推断，结果应与数据包中的 `topic_distr_is_ceo.npz` 完全一致：

```python
import numpy as np, pandas as pd
rows = pd.read_pickle("data/replication_sample/transcripts_is_ceo.pickle")["orig_row"].to_numpy()
np.save("rows_check.npy", rows[:1000])
# ceo-rd topics infer models/bertopic_ideo_13-23_relaxed_354Topics --rows-from rows_check.npy --out check.npz
ref = np.load("data/replication_sample/topic_distr_is_ceo.npz")["topic_distr"][:1000]
print(np.abs(np.load("check.npz")["topic_distr"] - ref).max())     # 应为 0（或浮点误差量级）
```

## 2.4 在 Python 中使用

```python
from ceo_rd.topics import (load_corpus, load_topic_model, infer_topic_distribution, assign_topics,
                           export_training_topics)

texts, rows = load_corpus("data/<含文本的 pickle>", text_column="componenttext_masked")
model = load_topic_model("models/bertopic_ideo_13-23_relaxed_354Topics",
                         embedding_model="sentence-transformers/all-mpnet-base-v2")   # 只算分布时可省略

infer_topic_distribution(model, texts, "topic_distr.npz")       # 分布
assign_topics(model, texts, "topic_assignments.parquet")        # 主 topic

# 少量文本可以直接调用 BERTopic
distr, _ = model.approximate_distribution(["We are investing heavily in R&D ..."], window=4, stride=1,
                                          min_similarity=0.1, use_embedding_model=False)
topics, probs = model.transform(["We are investing heavily in R&D ..."])
```

**对其他文本推断：** 例如改写过的对照文本，用 `--input <csv> --text-col "<列名>"` 即可。原分析中就用这种方式对 263 段对照文本做过推断。
