"""读取 topic modeling 用的文本。"""

import gc
from pathlib import Path

import numpy as np
import pandas as pd


def _read_table(path, columns):
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix in (".pickle", ".pkl"):
        df = pd.read_pickle(path)
        missing = [c for c in columns if c not in df.columns]
        if missing:
            raise ValueError(f"{path} 中没有列 {missing}")
        df = df[columns].reset_index(drop=True)
        gc.collect()
        return df
    if suffix == ".parquet":
        return pd.read_parquet(path, columns=columns)
    if suffix == ".csv":
        return pd.read_csv(path, usecols=columns, low_memory=False)
    raise ValueError(f"不支持的文件类型: {path}（支持 .pickle / .pkl / .parquet / .csv）")


def read_row_numbers(path, column="orig_row"):
    """读取行号：.npy 数组，或表格文件中的一列（默认 orig_row，例如复现子样本的 transcripts_is_ceo.pickle）。"""
    if Path(path).suffix.lower() == ".npy":
        return np.load(path)
    return _read_table(path, [column])[column].to_numpy()


def load_corpus(path, text_column="componenttext_masked", notna=None, rows=None):
    """读取文本列。

    notna: 只保留这些列非缺失的行（如训练集的 averageDem）。
    rows:  只读取这些行（在文件中的行号，按给定顺序），例如复现子样本的 orig_row，使输出与子样本逐行对齐。
           与 notna 同时给出时，先取行再筛选。

    支持 .pickle / .pkl / .parquet / .csv。返回 (texts, row_index)：row_index 是所选行在文件中的行号（从 0 开始），
    用于把推断结果与其他按行对齐的数据（面板、topic 矩阵）对应起来。
    """
    notna = list(notna or [])
    df = _read_table(path, list(dict.fromkeys([text_column, *notna])))
    if rows is not None:
        rows = np.asarray(rows, dtype=np.int64)
        if len(rows) and (rows.min() < 0 or rows.max() >= len(df)):
            raise ValueError(f"行号超出范围：文件共 {len(df):,} 行")
        df = df.iloc[rows]
        base = rows
    else:
        base = np.arange(len(df))

    mask = np.ones(len(df), dtype=bool)
    for c in notna:
        mask &= df[c].notna().to_numpy()
    texts = df[text_column].to_numpy()[mask]
    if pd.isna(texts).any():
        raise ValueError(f"文本列 {text_column} 在所选行中有缺失值")
    return texts.tolist(), base[mask]
