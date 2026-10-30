"""原始数据读取：transcript component（pickle）、topic density（npz，分块流式读取）、Compustat（CSV）。"""

import gc
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

TRANSCRIPT_COLS = [
    "companyid", "transcriptid", "transcriptpersonid", "directorid", "transcriptpersonname",
    "symbolvalue", "year", "retained_word_count", "transcriptcomponenttypename", "ggroup",
    "gender", "age", "educ_level", "sentiment_transformer",
]
COMPUSTAT_COLS = ["tic", "gvkey", "fyear", "datadate", "at", "sale", "xrd", "sich"]


def load_ceo_components(path):
    """读取 is_ceo 的 component。返回 (components, 原始总行数)；orig_idx 为在原始文件及 topic 矩阵中的行号。"""
    df = pd.read_pickle(path)
    n_total = len(df)
    if not df.index.equals(pd.RangeIndex(n_total)):
        raise ValueError("transcript 文件的 index 必须是 0..N-1，才能与 topic 矩阵逐行对齐")
    comp = df.loc[df["is_ceo"], TRANSCRIPT_COLS].copy()
    del df
    gc.collect()
    comp["orig_idx"] = comp.index
    # CEO 身份：优先 BoardEx directorid（同一人可能有多个 transcriptpersonid）
    comp["ceo_id"] = np.where(
        comp["directorid"].notna(),
        "bx_" + comp["directorid"].astype("Int64").astype(str),
        "tp_" + comp["transcriptpersonid"].astype("Int64").astype(str),
    )
    return comp.reset_index(drop=True), n_total


def load_compustat(path):
    """读取 Compustat，(tic, fyear) 与 (gvkey, fyear) 唯一，并附上上一财年的 at / sale / xrd。"""
    f = pd.read_csv(path)
    f = f[COMPUSTAT_COLS].sort_values(["gvkey", "fyear", "datadate"])
    # (tic, fyear) 仅极少数（LIMX/VSXY）有重复且财务值为空，保留最新 datadate
    f = f.drop_duplicates(["tic", "fyear"], keep="last").drop_duplicates(["gvkey", "fyear"], keep="last")
    lag = f[["gvkey", "fyear", "at", "sale", "xrd"]].copy()
    lag["fyear"] += 1
    return f.merge(lag, on=["gvkey", "fyear"], how="left", suffixes=("", "_lag"))


def _open_npy(zf, key):
    fh = zf.open(f"{key}.npy")
    version = np.lib.format.read_magic(fh)
    if version == (1, 0):
        shape, fortran, dtype = np.lib.format.read_array_header_1_0(fh)
    elif version == (2, 0):
        shape, fortran, dtype = np.lib.format.read_array_header_2_0(fh)
    else:
        raise ValueError(f"不支持的 npy 版本: {version}")
    if fortran or len(shape) != 2:
        raise ValueError(f"topic 矩阵须为 C 顺序的二维数组，实际 shape={shape}, fortran={fortran}")
    return fh, shape, dtype


def topic_shape(path, key="topic_distr"):
    with zipfile.ZipFile(path) as zf:
        fh, shape, _ = _open_npy(zf, key)
        fh.close()
    return shape


def iter_topic_chunks(path, key="topic_distr", chunk_rows=200_000):
    """逐块读取 npz 中的 topic 矩阵，产出 (起始行号, 块)；避免一次性载入全部（float64 全量约 16GB）。"""
    with zipfile.ZipFile(path) as zf:
        fh, (n_rows, n_cols), dtype = _open_npy(zf, key)
        with fh:
            for start in range(0, n_rows, chunk_rows):
                stop = min(start + chunk_rows, n_rows)
                buf = fh.read((stop - start) * n_cols * dtype.itemsize)
                yield start, np.frombuffer(buf, dtype=dtype).reshape(stop - start, n_cols)


def write_npz_chunks(path, key, chunks, extra=None):
    """把按行分块的二维数组流式写入压缩 npz（不在内存中拼接整个数组），np.load 可直接读取。

    chunks: 列数与 dtype 相同的二维数组序列（可以是 np.load(..., mmap_mode="r") 的结果）
    extra:  {名称: 数组}，一并写入的小数组（如行号）
    """
    chunks = list(chunks)
    if not chunks:
        raise ValueError("没有可写入的数据块")
    n_cols, dtype = chunks[0].shape[1], chunks[0].dtype
    if any(c.ndim != 2 or c.shape[1] != n_cols or c.dtype != dtype for c in chunks):
        raise ValueError("各数据块的列数与 dtype 必须一致")
    header = {"descr": np.lib.format.dtype_to_descr(dtype), "fortran_order": False,
              "shape": (sum(len(c) for c in chunks), n_cols)}
    path = Path(path)
    tmp = path.with_name(path.name + ".tmp")
    with zipfile.ZipFile(tmp, "w", compression=zipfile.ZIP_DEFLATED, allowZip64=True) as zf:
        with zf.open(f"{key}.npy", "w", force_zip64=True) as fh:
            np.lib.format.write_array_header_1_0(fh, header)
            for c in chunks:
                fh.write(np.ascontiguousarray(c).tobytes())
        for name, arr in (extra or {}).items():
            with zf.open(f"{name}.npy", "w", force_zip64=True) as fh:
                np.lib.format.write_array(fh, np.asarray(arr), allow_pickle=False)
    tmp.replace(path)  # 写完再改名，中断不会留下损坏的输出文件
    return path
