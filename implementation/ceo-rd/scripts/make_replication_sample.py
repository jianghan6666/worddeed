"""生成复现 R&D 预测所需的数据子样本（发给合作者）。

只保留面板构建会用到的行，格式与原始数据相同，合作者把 paths.yaml 指向这些文件即可运行 ceo-rd build-panel 与全部实验：
    transcripts_is_ceo.pickle     transcript 表中 is_ceo 的行（全部 79 列 + orig_row：在完整数据中的行号）
    topic_distr_is_ceo.npz        topic 矩阵的对应行（数组名 topic_distr），与上表逐行对齐
    compustat_panel_firms.csv     Compustat 中面板公司（gvkey）的全部年份（含计算上一年 R&D 所需的年份）
    paths.yaml                    指向以上文件以及 topic 文本（corpus）的路径配置

数据包另含 topic 训练 / 推断用的文本 pickle（paths.yaml 中的 corpus，全部行，不做筛选），由打包时一并提供。

用法：python scripts/make_replication_sample.py [--paths configs/paths.yaml] [--out data/replication_sample]
"""

import argparse
import gc
import logging
import shutil
from pathlib import Path

import numpy as np
import pandas as pd

from ceo_rd import enable_logging
from ceo_rd.config import load_paths
from ceo_rd.data import iter_topic_chunks, write_npz_chunks
from ceo_rd.panel import PANEL_FILE

log = logging.getLogger("ceo_rd.sample")

TRANSCRIPTS_FILE = "transcripts_is_ceo.pickle"
TOPICS_FILE = "topic_distr_is_ceo.npz"
COMPUSTAT_FILE = "compustat_panel_firms.csv"


def write_paths_yaml(out, paths):
    """数据包的路径配置：R&D 用子样本中的三个文件；topic 训练 / 推断用完整的文本 pickle（corpus）。"""
    out = Path(out)
    lines = [
        "# 数据包的路径配置：把数据包解压到项目的 data/ 下，复制本文件为 configs/paths.yaml",
        f"transcripts: {out.as_posix()}/{TRANSCRIPTS_FILE}",
        f"topics: {out.as_posix()}/{TOPICS_FILE}",
        f"topics_key: {paths.topics_key}",
        f"compustat: {out.as_posix()}/{COMPUSTAT_FILE}",
    ]
    if paths.corpus is not None:
        lines.append(f"corpus: {paths.corpus.as_posix()}")
    lines += ["models_dir: models", "panel_dir: data/panel", "results_dir: results"]
    (out / "paths.yaml").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(paths="configs/paths.yaml", out="data/replication_sample"):
    paths = load_paths(paths)
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)

    log.info("1/3 transcript 表：保留 is_ceo 的行")
    df = pd.read_pickle(paths.require("transcripts"))
    n_total = len(df)
    keep = df["is_ceo"].to_numpy(dtype=bool)
    rows = np.flatnonzero(keep)
    sub = df.loc[keep].reset_index(drop=True)
    del df
    gc.collect()
    sub["orig_row"] = rows
    sub.to_pickle(out / TRANSCRIPTS_FILE)
    log.info("  %s / %s 行，%d 列", f"{len(sub):,}", f"{n_total:,}", sub.shape[1])
    del sub
    gc.collect()

    log.info("2/3 topic 矩阵：取对应行")
    tmp = out / "_topic_parts"
    tmp.mkdir(exist_ok=True)
    part_files = []
    for start, X in iter_topic_chunks(paths.require("topics"), paths.topics_key):
        if start + len(X) > n_total:
            raise ValueError("topic 矩阵行数多于 transcript 表")
        lo, hi = np.searchsorted(rows, [start, start + len(X)])
        if hi > lo:
            part = tmp / f"part_{len(part_files):05d}.npy"
            np.save(part, X[rows[lo:hi] - start])
            part_files.append(part)
    arrays = [np.load(p, mmap_mode="r") for p in part_files]
    if sum(len(a) for a in arrays) != len(rows):
        raise ValueError("topic 矩阵行数与 transcript 表不一致")
    write_npz_chunks(out / TOPICS_FILE, paths.topics_key, arrays)
    n_topics = arrays[0].shape[1]
    del arrays
    gc.collect()  # 释放 memmap，Windows 上才能删除临时文件
    shutil.rmtree(tmp)
    log.info("  %s x %d", f"{len(rows):,}", n_topics)

    log.info("3/3 Compustat：保留面板公司的全部年份")
    gvkeys = pd.read_parquet(paths.panel_dir / PANEL_FILE, columns=["gvkey"])["gvkey"].unique()
    firm = pd.read_csv(paths.require("compustat"))
    firm_sub = firm[firm["gvkey"].isin(gvkeys)]
    firm_sub.to_csv(out / COMPUSTAT_FILE, index=False)
    log.info("  %s / %s 行，%s 家公司", f"{len(firm_sub):,}", f"{len(firm):,}", f"{len(gvkeys):,}")

    write_paths_yaml(out, paths)
    log.info("完成：%s", out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--paths", default="configs/paths.yaml")
    ap.add_argument("--out", default="data/replication_sample")
    args = ap.parse_args()
    enable_logging()
    main(args.paths, args.out)
