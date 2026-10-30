"""BERTopic topic modeling：训练、推断（topic 分布与主 topic）、topic 描述。

- 训练（train.py）与推断（infer.py）需要可选依赖：pip install -e ".[topics]"（bertopic==0.16.4 等），
  BERTopic 只在真正训练 / 推断时才导入。
- topic 描述（describe.py）与训练标签只读取模型目录中的文件（modelfiles.py），不需要 BERTopic。
"""

from .corpus import load_corpus, read_row_numbers
from .describe import export_topic_excel, representative_docs, top_words, topic_table
from .infer import (DEFAULT_EMBEDDING_MODEL, INFERENCE_DEFAULTS, assign_topics, export_training_topics,
                    infer_topic_distribution, load_topic_model)
from .modelfiles import load_ctfidf, read_topics_json, saved_embedding_model, training_topics
from .spec import TopicModelSpec
from .train import train_topic_model

__all__ = [
    "DEFAULT_EMBEDDING_MODEL", "INFERENCE_DEFAULTS", "TopicModelSpec", "assign_topics", "export_topic_excel",
    "export_training_topics", "infer_topic_distribution", "load_corpus", "load_ctfidf", "load_topic_model",
    "read_row_numbers", "read_topics_json", "representative_docs", "saved_embedding_model", "top_words",
    "topic_table", "train_topic_model", "training_topics",
]
