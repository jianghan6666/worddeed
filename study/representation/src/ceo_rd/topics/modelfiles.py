"""直接读取 BERTopic 以 safetensors 格式保存的模型文件，不需要安装 BERTopic。

模型目录（BERTopic.save(..., serialization="safetensors", save_ctfidf=True)）中：
    topics.json                 topic 表示、名称、大小、KeyBERT / MMR 等表示，以及训练文本的主 topic（topics）
    ctfidf.safetensors          c-TF-IDF 矩阵（行 = 按 id 排序的 topic，含离群类 -1；列 = 词表）
    ctfidf_config.json          CountVectorizer 参数与词表
    topic_embeddings.safetensors  每个 topic 的 embedding（transform 用它来分配主 topic）
"""

import json
from pathlib import Path

import numpy as np
from scipy import sparse

_DTYPES = {"F64": np.float64, "F32": np.float32, "F16": np.float16, "I64": np.int64, "I32": np.int32,
           "I16": np.int16, "I8": np.int8, "U8": np.uint8, "BOOL": np.bool_}


def read_safetensors(path):
    """读取 safetensors 文件，返回 {名称: numpy 数组}。"""
    with open(path, "rb") as fh:
        header_len = int.from_bytes(fh.read(8), "little")
        header = json.loads(fh.read(header_len))
        buf = fh.read()
    out = {}
    for name, info in header.items():
        if name == "__metadata__":
            continue
        start, stop = info["data_offsets"]
        out[name] = np.frombuffer(buf[start:stop], dtype=_DTYPES[info["dtype"]]).reshape(info["shape"])
    return out


def read_topics_json(model_dir):
    with open(Path(model_dir) / "topics.json", encoding="utf-8") as fh:
        return json.load(fh)


def topic_ids(topics_json):
    """模型中的全部 topic id（含离群类 -1），升序。"""
    return sorted(int(k) for k in topics_json["topic_representations"])


def load_ctfidf(model_dir):
    """返回 (c-TF-IDF 稀疏矩阵, 词表数组)；矩阵的行对应 topic_ids() 的顺序。"""
    model_dir = Path(model_dir)
    t = read_safetensors(model_dir / "ctfidf.safetensors")
    matrix = sparse.csr_matrix((t["data"], t["indices"], t["indptr"]), shape=tuple(int(x) for x in t["shape"]))
    with open(model_dir / "ctfidf_config.json", encoding="utf-8") as fh:
        vocab = json.load(fh)["vectorizer_model"]["vocab"]
    words = np.empty(len(vocab), dtype=object)
    for word, idx in vocab.items():
        words[idx] = word
    if matrix.shape[1] != len(words):
        raise ValueError(f"c-TF-IDF 列数 {matrix.shape[1]} 与词表大小 {len(words)} 不一致")
    return matrix, words


def training_topics(model_dir):
    """训练文本在训练时（UMAP + HDBSCAN）被分到的主 topic，顺序与训练文本相同；-1 为离群。"""
    return np.asarray(read_topics_json(model_dir)["topics"], dtype=np.int32)


def saved_embedding_model(model_dir):
    """模型保存时记录的 embedding 模型名称或路径（config.json 中的 embedding_model）；没有记录时返回 None。"""
    config = Path(model_dir) / "config.json"
    if not config.exists():
        return None
    with open(config, encoding="utf-8") as fh:
        return json.load(fh).get("embedding_model")
