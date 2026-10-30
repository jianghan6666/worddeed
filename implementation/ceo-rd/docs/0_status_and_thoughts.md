# 项目现状与后续思路

这份笔记简要介绍目前的进展、数据的组织方式，以及我对下一步的一些想法。具体用法见 [README](../README.md) 和文档 1–4。

## 1. 项目包含的内容

这个项目包主要有三部分：

| 部分 | 内容 | 文档 |
|---|---|---|
| Topic modeling | 用 BERTopic 得到 354 个 topic；每个 topic 的关键词整理在 Excel 中 | [1](1_topic_model_training.md)、[3](3_topic_descriptions.md) |
| Topic distribution inference | 用训练好的模型计算每段发言的 topic 分布 | [2](2_topic_inference.md) |
| 公司 R&D ratio 预测 | 用 CEO 讲话的 topic 预测公司的 R&D 强度 | [4](4_rd_prediction.md) |

**关于 topic 模型：** 它沿用了另一项研究（CEO political ideology）训练的模型，这次没有重新训练。主要是时间比较紧，训练一个新模型预计需要两天以上。它没有针对当前任务优化，后续可以再改进，可能的方向见文档 1 的 1.6 节。

## 2. 数据的组织方式

- **按发言组织：** 文本数据以 transcript component 为单位，每一行是一个 component。
  - 一场 conference call 包含很多个 component。
  - 每个 component 可以理解为一位发言人说的一段话。
- **R&D 预测时的汇总方式：** 把每位 CEO 在一年中所有发言的 topic 分布按词数加权平均，得到 CEO-公司-年度层面的特征。
- **情绪得分：** `transcripts_is_ceo.pickle` 中的每一行都附有情绪得分，共三列：`sentiment_vader`、`sentiment_blob`、`sentiment_transformer`。R&D 分析中用的是 `sentiment_transformer`。

## 3. Topic 与 topic 名称

模型共有 354 个 topic（编号 0–353）。另外还有一个离群类 -1，用来放没有被聚到任何 topic 的发言，它不是一个真正的主题。

**BERTopic 不会生成自然语言的 topic 名称。** 它只根据每个 topic 中最有代表性的关键词给出描述，例如 `0_care_health_health care_medicare`。这些关键词和每个 topic 的代表性发言，都整理在 [topic_descriptions_354Topics.xlsx](topic_descriptions_354Topics.xlsx) 中。

**可以用 AI 起名：** 如果需要易读的名称，可以让 AI 根据关键词和代表性发言总结。表中的 `Label` 列留空，就是为这一步准备的。

**目前没有给 topic 起名的原因：** 担心起名所用的 prompt 会带入偏差，进而影响后续判断"某个 topic 是否包含 CEO 风险偏好（CEO risk preference）的信息"。

## 4. 每段发言的 topic 归属

对每段发言（transcript component）属于哪个 topic，有两种呈现形式：

1. **唯一归属（主 topic）：** BERTopic 在聚类时，会给每段文本分配唯一一个 topic 类别（也可能是离群类 -1）。
   - 训练用的文本，这个类别可以直接从模型文件中导出。
   - 其他文本需要用模型计算，建议用 GPU。
   - 具体方法见文档 2 的 2.2 节。
2. **多个 topic 的组合（topic 分布）：** 把每段文本看成多个 topic 的组合。比如一段话同时谈到了业绩、并购和投资，它在这三个 topic 上都有权重。
   - 数据包中的 `topic_distr_is_ceo.npz` 就是这种形式：每行 354 个权重，加起来为 1；只有极短的发言全为 0。
   - 它与 `transcripts_is_ceo.pickle` 逐行对应。
   - R&D 预测用的是这种形式。

## 5. 关于下一步

**目前的计划：** 我理解下一步是把 topic 分成几类，用来构建 narrative measure。

**理想的做法：** 如果能和 topic modeling 一起优化，效果应该会更好，毕竟现在的 topic 模型不是为这个任务专门训练的。不过这需要一些时间和计算资源。

**更快的起步方式：** 如果想先尽快搭起一个 AI 分析框架，可以先在现有的 354 个 topic 上让 AI 分类。分类依据是 [topic_descriptions_354Topics.xlsx](topic_descriptions_354Topics.xlsx) 中的关键词和代表性发言。分好类之后，可以直接沿用现有的流程：

1. 把每段发言在同一类 topic 上的权重相加，得到它在这一类上的得分；
2. 再按 CEO-公司-年度汇总。

**以后换模型时：** 如果之后换成新训练的 topic 模型，分类这一步需要在新模型的 topic 上重新做。
