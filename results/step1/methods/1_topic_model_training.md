# 1. Topic 模型的训练

本项目的 topic 特征来自一个 **已经训练好的 BERTopic 模型**：`models/bertopic_ideo_13-23_relaxed_354Topics/`，共 354 个 topic。后续的 topic 推断（见 [2_topic_inference.md](2_topic_inference.md)）和 R&D 预测（见 [4_rd_prediction.md](4_rd_prediction.md)）都基于这个模型。

本文说明这个模型是怎么训练的、怎样重新训练，以及可以按本研究的需要从哪些方面优化。

## 1.1 方法：BERTopic

BERTopic 把每段文本转换成语义向量，再在向量空间里聚类，每个簇就是一个 topic；每个 topic 的关键词用 c-TF-IDF（按簇计算的 TF-IDF）提取。具体流程和本模型的设置如下（BERTopic 0.16.4）：

| 步骤 | 组件 | 设置 |
|---|---|---|
| 1. 文本向量化 | sentence-transformers `all-mpnet-base-v2` | 每段发言得到一个 768 维 embedding |
| 2. 降维 | UMAP | `n_neighbors=15, n_components=5, min_dist=0.0, metric=cosine, random_state=42` |
| 3. 聚类 | HDBSCAN | `min_cluster_size=120, min_samples=100, metric=euclidean, cluster_selection_method=eom`。模型名中的"relaxed"指这组参数 |
| 4. 词表 | CountVectorizer | 英文停用词，`min_df=10`，1–2 gram |
| 5. topic 关键词 | c-TF-IDF | 每个 topic 取分数最高的 15 个词作为主要表示 |
| 6. 补充表示 | KeyBERTInspired；MaximalMarginalRelevance（`diversity=0.3`） | 两组语义上更连贯、更多样的关键词 |

聚不进任何簇的文本被归为离群类 **-1**。它不是一个真正的主题。

## 1.2 训练数据

- **语料：** Capital IQ 的电话会议与投资者会议记录，2013–2023 年，以 transcript component（一段发言）为单位，共 5,765,638 段。
- **文本：** 文本列是 `componenttext_masked`，其中人名、公司名已替换为占位符（如 `[PERSON]`）。
- **训练集：** 只用 **发言人有政治捐款意识形态得分（`averageDem` 非缺失）** 的发言，共 **887,488** 段。
  - 这个模型最初是为一项政治意识形态研究构建的，所以训练集按这个标准筛选。
  - 训练集里不只是 CEO 的发言。
- **数据文件：** 训练文本来自数据包中含文本的 pickle（`paths.yaml` 中的 `corpus`，共 5,765,638 行），这个文件的行顺序与本项目其他数据完全一致。训练时按 `averageDem` 非缺失筛出 887,488 行，正好是原训练集。

## 1.3 训练结果

| 项目 | 数值 |
|---|---|
| topic 数 | 354（编号 0–353），另有离群类 -1 |
| 离群文档 | 482,860 段，占训练文档的 54.4% |
| 每个 topic 的训练文档数 | 最少 120，中位数 355，最多 32,216 |
| 词表 | 357,429 个词（含 2-gram） |
| 训练时间 | 2026-07-03（Python 3.12，bertopic 0.16.4） |

各个 topic 的关键词和名称见 [3_topic_descriptions.md](3_topic_descriptions.md)。

## 1.4 模型文件

模型以 BERTopic 的 safetensors 格式保存（`serialization="safetensors", save_ctfidf=True`）：

| 文件 | 内容 |
|---|---|
| `config.json` | BERTopic 参数 |
| `topics.json` | 每个 topic 的关键词、名称、规模、KeyBERT / MMR 表示，以及 887,488 段训练文本各自的主 topic |
| `topic_embeddings.safetensors` | 355 个 topic（含 -1）的 768 维 embedding |
| `ctfidf.safetensors`、`ctfidf_config.json` | c-TF-IDF 矩阵与词表 |
| `topic_info_354Topics.csv / .xlsx`、`topic_top25_words.xlsx` | 训练时导出的 topic 信息与每个 topic 的前 25 个词 |

这种格式 **不保存 UMAP 与 HDBSCAN 模型，也不保存 embedding 模型本身**。这对推断有两点影响，详见 [2_topic_inference.md](2_topic_inference.md)：
- **topic 分布：** 不需要 embedding 模型，可以直接计算。
- **新文本的主 topic：** 需要另外加载 `all-mpnet-base-v2`，并改用"与 topic embedding 的相似度"来分配。

## 1.5 重新训练

训练的全部参数都记录在 [topic_models/bertopic_ideo_13-23_relaxed.yaml](../topic_models/bertopic_ideo_13-23_relaxed.yaml) 中。重新训练：

```bash
pip install -e ".[topics]"                # bertopic==0.16.4、sentence-transformers、umap-learn、hdbscan
ceo-rd topics train topic_models/bertopic_ideo_13-23_relaxed.yaml
# → models/bertopic_ideo_13-23_relaxed/
```

- **数据：** 需要数据包中含文本的 pickle（`paths.yaml` 中的 `corpus`），读入时进程内存峰值约 11GB。
- **训练集：** 按配置中的 `train_filter` 筛选（默认 `averageDem` 非缺失）。
- **embedding：** 分块计算，缓存在 `models/<name>.embeddings/`，中断后可以续跑。
  - 改了 UMAP / HDBSCAN 参数再训练时，可以用 `--embeddings models/<name>.embeddings` 复用已算好的 embedding。
  - `--embedding-model` 可以改用本地模型目录。
- **算力：** 原模型训练时，88.7 万段文本的 embedding 计算和 UMAP 降维都很耗时（仅 UMAP 就约 20 分钟），建议在有 GPU 的机器上运行。
- **输出：**
  - 模型文件；
  - `topic_info.csv`；
  - `topic_descriptions.xlsx`（见文档 3）；
  - `train_row_index.npy`：训练文本在 corpus 中的行号；
  - `train_meta.json`：训练文档数、topic 数、离群数、各个库的版本。
- **不可完全复现：** UMAP / HDBSCAN 的结果会随库版本和硬件变化，重新训练得不到与现有模型完全相同的 topic。本项目的分析都以现有模型为准。

在 Python 中：

```python
from ceo_rd.topics import TopicModelSpec, train_topic_model
spec = TopicModelSpec.from_yaml("topic_models/bertopic_ideo_13-23_relaxed.yaml")
spec.hdbscan["min_cluster_size"] = 200          # 修改参数后训练一个新模型
spec.name = "bertopic_ceo_trial"
train_topic_model(spec, corpus="data/<含文本的 pickle>", out_dir="models/bertopic_ceo_trial")
```

## 1.6 可以按本研究需要优化的方向

现有模型是为政治意识形态研究训练的，直接用于 CEO 风险偏好 / R&D 研究时，可以考虑以下方向。这些都只是可选的方向，目前没有做过：

1. **训练语料：** 现在的训练集是"有意识形态标签的发言人"。可以改为 CEO 的发言，或全部发言（在 YAML 中修改 `train_filter`），让 topic 更贴近 CEO 的表述。
2. **离群比例：** 现在有 54% 的训练文本是离群类。可以调小 HDBSCAN 的 `min_cluster_size` / `min_samples`，或在训练后用 BERTopic 的 `reduce_outliers` 重新分配离群文本。
3. **topic 粒度：** 354 个 topic 中有不少是行业主题（医疗、航空、保险等）。如果研究更关心战略、风险、创新类的表述，可以：
   - 用 `nr_topics` 合并相近的 topic；
   - 用层次 topic 查看结构；
   - 用 guided topic modeling（`seed_topic_list`）给创新、研发、风险等主题提供种子词。
4. **embedding 模型：** 可以换成金融文本领域的句向量模型（在 YAML 中修改 `embedding_model`）。
5. **评价标准：** 除了 topic coherence / diversity，还可以直接用下游任务评价：新 topic 在 R&D 预测中相对控制变量的增量 ΔR²（见文档 4）。
