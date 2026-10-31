"""用已训练的 BERTopic 模型对文本推断。

两种输出：
- topic 分布（infer_topic_distribution）：approximate_distribution，只用 c-TF-IDF，不需要 embedding。
  输出压缩 npz，数组名 topic_distr，每行和为 1（没有足够相似的 topic 时全为 0）。
- 主 topic（assign_topics）：BERTopic transform。以 safetensors 保存的模型不含 UMAP / HDBSCAN，transform 会先用
  embedding 模型计算文本 embedding，再取余弦相似度最高的 topic embedding（可能是离群类 -1）。
  输出 parquet：row（在输入文件中的行号）、topic、topic_prob（与该 topic 的相似度）。

全量 5.77M 条文本计算量大（原机器上 topic 分布约 3.7 小时；主 topic 需要计算 embedding，建议用 GPU），
所以都按块计算并逐块落盘：中断后重新运行同一命令会跳过已完成的块。
"""

import gc
import json
import logging
import shutil
import time
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

from ..data import write_npz_chunks
from .modelfiles import training_topics
from .train import package_versions

log = logging.getLogger(__name__)

# 与原 notebook 一致（BERTopic approximate_distribution 的默认值，这里显式固定，避免随版本变化）
INFERENCE_DEFAULTS = {
    "window": 4,
    "stride": 1,
    "min_similarity": 0.1,
    "batch_size": 1000,
    "padding": False,
    "use_embedding_model": False,  # False：只用 c-TF-IDF，不需要计算 embedding
}
DEFAULT_EMBEDDING_MODEL = "sentence-transformers/all-mpnet-base-v2"


def load_topic_model(model_dir, embedding_model=None):
    """加载 safetensors 格式保存的 BERTopic 模型。

    只算 topic 分布（use_embedding_model=False）时不需要 embedding_model；算主 topic（transform）时需要，
    且须与训练时相同（现有模型为 all-mpnet-base-v2，可以是 Hugging Face 名称或本地路径）。
    """
    from bertopic import BERTopic

    return BERTopic.load(str(model_dir), embedding_model=embedding_model)


def _run_in_chunks(compute, texts, out_path, chunk_size, settings, overwrite):
    """对 texts 分块调用 compute(chunk) -> 二维数组，逐块写入 <out_path>.parts/；返回各块文件路径。"""
    out_path = Path(out_path)
    if out_path.exists() and not overwrite:
        raise FileExistsError(f"{out_path} 已存在；如确需覆盖请使用 overwrite")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    parts_dir = out_path.with_name(out_path.name + ".parts")
    parts_dir.mkdir(exist_ok=True)
    manifest = {"n_texts": len(texts), "chunk_size": chunk_size, **settings}
    manifest_file = parts_dir / "manifest.json"
    if manifest_file.exists():
        previous = json.loads(manifest_file.read_text(encoding="utf-8"))
        if previous != manifest:
            raise ValueError(f"{parts_dir} 中已有不同设置下的中间结果：{previous}；请删除该目录或使用相同设置")
    else:
        manifest_file.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    starts = list(range(0, len(texts), chunk_size))
    parts = [parts_dir / f"part_{k:05d}.npy" for k in range(len(starts))]
    t0, n_done = time.time(), 0
    for k, (start, part) in enumerate(zip(starts, parts)):
        if part.exists():
            continue
        chunk = texts[start:start + chunk_size]
        result = np.asarray(compute(chunk))
        if result.shape[0] != len(chunk):
            raise ValueError(f"第 {k} 块返回 {result.shape[0]} 行，应为 {len(chunk)} 行")
        tmp = part.with_name(part.stem + ".tmp.npy")
        np.save(tmp, result)
        tmp.replace(part)  # 写完再改名，中断时不会留下不完整的块
        n_done += 1
        remaining = sum(not p.exists() for p in parts)
        eta = (time.time() - t0) / n_done * remaining
        log.info("  块 %d/%d 完成（%s 行）；剩余 %d 块，预计 %.1f 分钟",
                 k + 1, len(parts), f"{start + len(chunk):,}", remaining, eta / 60)
    return parts, parts_dir


def _finish(out_path, parts_dir, keep_parts, info):
    out_path = Path(out_path)
    info = {**info, "output": str(out_path), "finished": datetime.now().isoformat(timespec="seconds"),
            "versions": package_versions()}
    out_path.with_name(out_path.name + ".meta.json").write_text(
        json.dumps(info, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    gc.collect()  # 释放 memmap，Windows 上才能删除分块文件
    if not keep_parts:
        shutil.rmtree(parts_dir)


def infer_topic_distribution(topic_model, texts, out_path, row_index=None, chunk_size=100_000,
                             overwrite=False, keep_parts=False, meta=None, **params):
    """计算 texts 的 topic 分布（approximate_distribution）并写入 out_path（npz，数组名 topic_distr）。

    topic_model: 已加载的 BERTopic 模型（或任何提供 approximate_distribution 的对象）
    row_index:   texts 在原文件中的行号；只对部分行推断时一并写入 npz（数组名 row_index）
    params:      覆盖 INFERENCE_DEFAULTS
    """
    unknown = set(params) - set(INFERENCE_DEFAULTS)
    if unknown:
        raise ValueError(f"未知的推断参数 {sorted(unknown)}；可用: {sorted(INFERENCE_DEFAULTS)}")
    params = {**INFERENCE_DEFAULTS, **params}
    parts, parts_dir = _run_in_chunks(
        lambda chunk: topic_model.approximate_distribution(chunk, **params)[0],
        texts, out_path, chunk_size, {"task": "distribution", "params": params}, overwrite)

    arrays = [np.load(p, mmap_mode="r") for p in parts]
    extra = {"row_index": np.asarray(row_index)} if row_index is not None else None
    write_npz_chunks(out_path, "topic_distr", arrays, extra=extra)
    n_topics = arrays[0].shape[1]
    n_zero = int(sum((np.asarray(a).sum(axis=1) == 0).sum() for a in arrays))
    del arrays
    _finish(out_path, parts_dir, keep_parts, {**(meta or {}), "n_rows": len(texts), "n_topics": n_topics,
                                              "n_all_zero_rows": n_zero, "params": params, "chunk_size": chunk_size})
    log.info("topic 分布 %s x %s 已写入 %s（全 0 行 %s）", f"{len(texts):,}", n_topics, out_path, f"{n_zero:,}")
    return Path(out_path)


def assign_topics(topic_model, texts, out_path, row_index=None, chunk_size=50_000,
                  overwrite=False, keep_parts=False, meta=None):
    """用 BERTopic transform 为每条文本分配主 topic，写入 out_path（parquet：row, topic, topic_prob）。

    topic_model 需要带 embedding 模型加载（见 load_topic_model）。
    """
    def compute(chunk):
        topics, probs = topic_model.transform(chunk)
        probs = np.asarray(probs, dtype=float)
        if probs.ndim == 2:  # calculate_probabilities=True 时返回整个相似度矩阵
            probs = probs.max(axis=1)
        return np.column_stack([np.asarray(topics, dtype=float), probs])

    parts, parts_dir = _run_in_chunks(compute, texts, out_path, chunk_size, {"task": "assign"}, overwrite)
    result = np.concatenate([np.load(p) for p in parts])
    out = pd.DataFrame({
        "row": np.asarray(row_index) if row_index is not None else np.arange(len(texts)),
        "topic": result[:, 0].astype(np.int32),
        "topic_prob": result[:, 1].astype(np.float32),
    })
    out.to_parquet(out_path, index=False)
    n_outlier = int((out["topic"] == -1).sum())
    _finish(out_path, parts_dir, keep_parts, {**(meta or {}), "n_rows": len(out), "n_outlier": n_outlier,
                                              "method": "BERTopic.transform", "chunk_size": chunk_size})
    log.info("主 topic 已写入 %s（%s 行，离群 -1：%s）", out_path, f"{len(out):,}", f"{n_outlier:,}")
    return Path(out_path)


def export_training_topics(model_dir, train_rows, out_path, overwrite=False):
    """导出训练文本在训练时被分到的主 topic（parquet：row, topic）。

    train_rows: 训练文本在文本文件中的行号（顺序与训练时一致）。用 ceo-rd topics train 训练的模型目录中有
                train_row_index.npy；现有模型的训练文本是 corpus 中 averageDem 非缺失的行。
    """
    out_path = Path(out_path)
    if out_path.exists() and not overwrite:
        raise FileExistsError(f"{out_path} 已存在；如确需覆盖请使用 overwrite")
    topics = training_topics(model_dir)
    train_rows = np.asarray(train_rows)
    if len(topics) != len(train_rows):
        raise ValueError(f"模型中有 {len(topics):,} 条训练文本的标签，但给出的训练行号有 {len(train_rows):,} 个")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({"row": train_rows, "topic": topics}).to_parquet(out_path, index=False)
    log.info("训练标签已写入 %s（%s 行，离群 -1：%s）", out_path, f"{len(topics):,}", f"{int((topics == -1).sum()):,}")
    return out_path
