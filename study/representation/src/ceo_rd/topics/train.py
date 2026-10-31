"""训练 BERTopic 模型。

流程：读取文本（按 train_filter 筛选）→ 计算 / 读取 sentence embedding（分块缓存，可断点续跑）
→ UMAP + HDBSCAN + c-TF-IDF 拟合 → 以 safetensors 格式保存模型 → 导出 topic 描述（Excel）与训练元数据。
训练文本的主 topic 保存在模型的 topics.json 中，可用 ceo-rd topics training-labels 导出。
"""

import json
import logging
import time
from datetime import datetime
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

import numpy as np
import yaml

from .corpus import load_corpus
from .describe import export_topic_excel
from .spec import TopicModelSpec

log = logging.getLogger(__name__)

TRACKED_PACKAGES = ["bertopic", "sentence-transformers", "umap-learn", "hdbscan", "torch", "scikit-learn", "numpy"]


def package_versions():
    out = {}
    for pkg in TRACKED_PACKAGES:
        try:
            out[pkg] = version(pkg)
        except PackageNotFoundError:
            out[pkg] = None
    return out


def load_embeddings(path):
    """读取已有 embedding：.npy、.npz（数组名 embeddings）或 encode_corpus 的分块缓存目录。"""
    path = Path(path)
    if path.is_dir():
        parts = sorted(path.glob("part_*.npy"))
        if not parts:
            raise FileNotFoundError(f"{path} 中没有 part_*.npy")
        return np.concatenate([np.load(p) for p in parts])
    if path.suffix == ".npz":
        return np.load(path)["embeddings"]
    return np.load(path)


def encode_corpus(texts, model_name, cache_dir, chunk_size=100_000, batch_size=32):
    """计算 sentence embedding，按块缓存到 cache_dir（中断后重新运行会跳过已完成的块）。"""
    from sentence_transformers import SentenceTransformer

    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    meta_file = cache_dir / "manifest.json"
    meta = {"model": str(model_name), "n_texts": len(texts), "chunk_size": chunk_size}
    if meta_file.exists() and json.loads(meta_file.read_text(encoding="utf-8")) != meta:
        raise ValueError(f"{cache_dir} 中已有不同设置下的 embedding 缓存，请删除或换一个目录")
    meta_file.write_text(json.dumps(meta, indent=2), encoding="utf-8")

    model = None
    starts = range(0, len(texts), chunk_size)
    for k, start in enumerate(starts):
        part = cache_dir / f"part_{k:05d}.npy"
        if part.exists():
            continue
        if model is None:
            model = SentenceTransformer(str(model_name))
        emb = model.encode(texts[start:start + chunk_size], batch_size=batch_size, show_progress_bar=True)
        tmp = part.with_name(part.stem + ".tmp.npy")
        np.save(tmp, emb)
        tmp.replace(part)
        log.info("  embedding 块 %d/%d 完成", k + 1, len(starts))
    return load_embeddings(cache_dir)


def _representation_model(cfg):
    from bertopic.representation import KeyBERTInspired, MaximalMarginalRelevance, PartOfSpeech

    cfg = dict(cfg)
    kind = cfg.pop("type")
    return {"keybert": KeyBERTInspired, "mmr": MaximalMarginalRelevance, "pos": PartOfSpeech}[kind](**cfg)


def build_topic_model(spec, embedding_model):
    """按配置构造未训练的 BERTopic 对象。"""
    from bertopic import BERTopic
    from hdbscan import HDBSCAN
    from sklearn.feature_extraction.text import CountVectorizer
    from umap import UMAP

    vectorizer = dict(spec.vectorizer)
    if "ngram_range" in vectorizer:
        vectorizer["ngram_range"] = tuple(vectorizer["ngram_range"])  # sklearn 要求 tuple
    representation = {name: _representation_model(cfg) for name, cfg in spec.representation.items()} or None
    return BERTopic(
        embedding_model=embedding_model,
        umap_model=UMAP(**spec.umap),
        hdbscan_model=HDBSCAN(**spec.hdbscan),
        vectorizer_model=CountVectorizer(**vectorizer),
        representation_model=representation,
        **spec.bertopic,
    )


def train_topic_model(spec, corpus, out_dir, embeddings=None, embedding_cache=None,
                      embedding_model=None, overwrite=False):
    """训练并保存模型。

    spec:            TopicModelSpec、YAML 路径或 dict
    corpus:          文本文件（见 load_corpus）
    out_dir:         模型输出目录（BERTopic safetensors 文件 + 描述表 + 元数据）
    embeddings:      已有 embedding（文件或分块目录），行须与筛选后的文本一一对应；不给则重新计算
    embedding_cache: 新计算 embedding 的缓存目录（默认 <out_dir>.embeddings，与模型目录分开，便于单独分发模型）
    embedding_model: 覆盖 spec.embedding_model（如本地模型路径）
    """
    if isinstance(spec, (str, Path)):
        spec = TopicModelSpec.from_yaml(spec)
    elif isinstance(spec, dict):
        spec = TopicModelSpec.from_dict(spec)
    out_dir = Path(out_dir)
    if out_dir.exists() and any(out_dir.iterdir()) and not overwrite:
        raise FileExistsError(f"{out_dir} 已存在且非空；如确需覆盖请使用 overwrite")
    out_dir.mkdir(parents=True, exist_ok=True)
    emb_model = embedding_model or spec.embedding_model
    started = datetime.now().isoformat(timespec="seconds")

    log.info("1/4 读取文本 %s（筛选：%s 非缺失）", corpus, spec.notna_columns or "无")
    texts, row_index = load_corpus(corpus, spec.text_column, spec.notna_columns)
    log.info("  训练文本 %s 条", f"{len(texts):,}")
    with open(out_dir / "train_spec.yaml", "w", encoding="utf-8") as fh:
        yaml.safe_dump(spec.to_dict(), fh, allow_unicode=True, sort_keys=False)
    np.save(out_dir / "train_row_index.npy", row_index)

    log.info("2/4 sentence embedding（%s）", emb_model)
    if embeddings is not None:
        emb = load_embeddings(embeddings)
    else:
        cache = Path(embedding_cache) if embedding_cache else out_dir.with_name(out_dir.name + ".embeddings")
        emb = encode_corpus(texts, emb_model, cache, batch_size=spec.encode_batch_size)
    if len(emb) != len(texts):
        raise ValueError(f"embedding 行数 {len(emb):,} 与文本数 {len(texts):,} 不一致")

    log.info("3/4 拟合 BERTopic（UMAP + HDBSCAN + c-TF-IDF）")
    t0 = time.time()
    topic_model = build_topic_model(spec, emb_model)
    topics, _ = topic_model.fit_transform(texts, emb)
    fit_minutes = (time.time() - t0) / 60

    log.info("4/4 保存模型与描述表")
    # 保存 embedding 模型的名称 / 路径，之后加载时不必再手动指定
    topic_model.save(str(out_dir), serialization="safetensors", save_ctfidf=True,
                     save_embedding_model=str(emb_model))
    topic_model.get_topic_info().to_csv(out_dir / "topic_info.csv", index=False)  # 含代表性文档
    export_topic_excel(out_dir)
    topics = np.asarray(topics)
    meta = {
        "name": spec.name, "corpus": str(corpus), "n_train_docs": len(texts),
        "n_topics": int(len(set(topics.tolist())) - (topics == -1).any()),
        "n_outlier_docs": int((topics == -1).sum()), "fit_minutes": round(fit_minutes, 1),
        "embedding_model": str(emb_model), "started": started,
        "finished": datetime.now().isoformat(timespec="seconds"), "versions": package_versions(),
    }
    (out_dir / "train_meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    log.info("完成：%d 个 topic，离群文档 %s 条，模型已保存到 %s", meta["n_topics"],
             f"{meta['n_outlier_docs']:,}", out_dir)
    return topic_model
