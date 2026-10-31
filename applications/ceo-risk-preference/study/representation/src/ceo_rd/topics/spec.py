"""BERTopic 训练配置（topic_models/*.yaml）。"""

from dataclasses import asdict, dataclass, field, fields

import yaml

REPRESENTATION_TYPES = ("keybert", "mmr", "pos")
# 这些由 spec 的专门字段构造，不能出现在 bertopic 参数里
PIPELINE_KEYS = {"embedding_model", "umap_model", "hdbscan_model", "vectorizer_model", "representation_model"}


@dataclass
class TopicModelSpec:
    name: str
    text_column: str = "componenttext_masked"
    train_filter: dict = field(default_factory=dict)  # {"notna": [列名, ...]}：只用这些列非缺失的行训练
    embedding_model: str = "sentence-transformers/all-mpnet-base-v2"  # 名称或本地路径
    encode_batch_size: int = 32
    umap: dict = field(default_factory=dict)
    hdbscan: dict = field(default_factory=dict)
    vectorizer: dict = field(default_factory=dict)  # CountVectorizer 参数
    representation: dict = field(default_factory=dict)  # 名称 -> {type: keybert | mmr | pos, 其余为参数}
    bertopic: dict = field(default_factory=dict)  # 其余 BERTopic 参数，如 top_n_words

    @classmethod
    def from_yaml(cls, path):
        with open(path, encoding="utf-8") as fh:
            return cls.from_dict(yaml.safe_load(fh))

    @classmethod
    def from_dict(cls, d):
        allowed = {f.name for f in fields(cls)}
        unknown = set(d) - allowed
        if unknown:
            raise ValueError(f"topic model 配置中有未知字段 {sorted(unknown)}；可用字段: {sorted(allowed)}")
        spec = cls(**{k: v for k, v in d.items() if v is not None})  # YAML 中空着的字段用默认值
        spec.validate()
        return spec

    def to_dict(self):
        return asdict(self)

    @property
    def notna_columns(self):
        return list(self.train_filter.get("notna", []))

    def validate(self):
        if not self.name:
            raise ValueError("name 不能为空")
        if set(self.train_filter) - {"notna"}:
            raise ValueError(f"train_filter 目前只支持 notna，实际有 {sorted(self.train_filter)}")
        for name, cfg in self.representation.items():
            if not isinstance(cfg, dict) or cfg.get("type") not in REPRESENTATION_TYPES:
                raise ValueError(f"representation '{name}' 须包含 type，可选 {REPRESENTATION_TYPES}")
        clash = PIPELINE_KEYS & set(self.bertopic)
        if clash:
            raise ValueError(f"bertopic 参数中不能包含 {sorted(clash)}，请用 spec 的对应字段配置")
