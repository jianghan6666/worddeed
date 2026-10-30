"""Topic 描述：每个 topic 的名称、规模、关键词与代表性文档，导出为 Excel。

只读取模型目录中的文件（见 modelfiles.py），不需要安装 BERTopic。
"""

import ast
import logging
import re
from pathlib import Path

import numpy as np
import pandas as pd

from .modelfiles import load_ctfidf, read_topics_json, topic_ids

log = logging.getLogger(__name__)

_ILLEGAL_EXCEL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


def _words(pairs, n=None):
    return ", ".join(w for w, _ in pairs[:n] if w)


def top_words(model_dir, top_n=25):
    """每个 topic 按 c-TF-IDF 分数排序的前 top_n 个词（分数相同时按词的字母顺序）。

    返回 (长表: Topic / Rank / Word / Score, 宽表: 每个 topic 一行 word_1 … word_N)。
    """
    matrix, vocab = load_ctfidf(model_dir)
    ids = topic_ids(read_topics_json(model_dir))
    if matrix.shape[0] != len(ids):
        raise ValueError(f"c-TF-IDF 行数 {matrix.shape[0]} 与 topic 数 {len(ids)} 不一致")
    records = []
    for row_index, topic_id in enumerate(ids):
        row = matrix.getrow(row_index)
        row_words = vocab[row.indices]
        order = np.lexsort((row_words, -row.data))[:top_n]
        records += [{"Topic": topic_id, "Rank": rank, "Word": row_words[i], "Score": row.data[i]}
                    for rank, i in enumerate(order, start=1)]
    long = pd.DataFrame(records)
    wide = (long.pivot(index="Topic", columns="Rank", values="Word")
            .rename(columns=lambda r: f"word_{r}").reset_index())
    wide.columns.name = None
    return long, wide


def representative_docs(model_dir):
    """训练时每个 topic 的代表性文档（来自模型目录中的 topic_info*.csv，没有则返回空表）。"""
    files = sorted(Path(model_dir).glob("topic_info*.csv"))
    if not files:
        return pd.DataFrame(columns=["Topic", "Rank", "Document"])
    info = pd.read_csv(files[0])
    if "Representative_Docs" not in info:
        return pd.DataFrame(columns=["Topic", "Rank", "Document"])
    rows = []
    for topic, docs in zip(info["Topic"], info["Representative_Docs"]):
        if isinstance(docs, str):
            rows += [{"Topic": int(topic), "Rank": i, "Document": d} for i, d in enumerate(ast.literal_eval(docs), 1)]
    return pd.DataFrame(rows)


def topic_table(model_dir, n_words=10):
    """每个 topic 一行：自动名称、待人工填写的标签、训练文档数与占比、c-TF-IDF / KeyBERT / MMR 关键词。"""
    t = read_topics_json(model_dir)
    sizes = {int(k): v for k, v in t["topic_sizes"].items()}
    total = sum(sizes.values())
    aspects = t.get("topic_aspects") or {}
    custom = t.get("custom_labels")
    rows = []
    for tid in topic_ids(t):
        key = str(tid)
        row = {
            "Topic": tid,
            "Name": t["topic_labels"][key],
            "Label": (custom[tid + t.get("_outliers", 0)] if custom else ""),
            "Count": sizes.get(tid, 0),
            "Share": sizes.get(tid, 0) / total,
            f"Top{n_words}_cTFIDF": _words(t["topic_representations"][key], n_words),
        }
        for aspect, reps in aspects.items():
            row[aspect] = _words(reps.get(key, []))
        rows.append(row)
    return pd.DataFrame(rows)


def _readme_sheet(model_dir, table, top_n):
    t = read_topics_json(model_dir)
    n_train = int(table["Count"].sum())
    n_outlier = int(table.loc[table["Topic"] == -1, "Count"].sum())
    lines = [
        ("模型", Path(model_dir).name),
        ("训练文档数", f"{n_train:,}"),
        ("topic 数", f"{int((table['Topic'] >= 0).sum())}（另有离群类 -1：{n_outlier:,} 条，{n_outlier / n_train:.1%}）"),
        ("", ""),
        ("Topics 表", "每个 topic 一行"),
        ("  Topic", "topic 编号；-1 为离群类（训练时没有被分到任何 topic 的文档），不是一个真正的主题"),
        ("  Name", "BERTopic 自动生成的名称：编号 + c-TF-IDF 前 4 个词"),
        ("  Label", "人工命名，待填写" if not t.get("custom_labels") else "人工命名"),
        ("  Count / Share", "训练时被分到该 topic 的文档数，以及占全部训练文档的比例"),
        ("  Top10_cTFIDF", "c-TF-IDF 分数最高的 10 个词（1–2 gram），即 BERTopic 的主要表示"),
        ("  KeyBERT", "KeyBERTInspired：与 topic embedding 最相似的候选词，语义上更连贯"),
        ("  MMR", "Maximal Marginal Relevance（diversity=0.3）：在相关性之外兼顾多样性的关键词"),
        (f"Top{top_n}_Words", f"每个 topic 的 c-TF-IDF 前 {top_n} 个词（宽表）"),
        (f"Top{top_n}_With_Scores", "同上，长表，附 c-TF-IDF 分数"),
        ("Representative_Docs", "训练时每个 topic 最有代表性的 3 条发言（人名、公司名已打码）"),
    ]
    return pd.DataFrame(lines, columns=["项目", "说明"])


def _clean(df):
    return df.apply(lambda col: col.map(lambda v: _ILLEGAL_EXCEL_CHARS.sub("", v) if isinstance(v, str) else v))


def export_topic_excel(model_dir, out_path=None, top_n=25):
    """把 topic 描述写成一个 Excel（默认 <模型目录>/topic_descriptions.xlsx），返回文件路径。"""
    model_dir = Path(model_dir)
    out_path = Path(out_path) if out_path else model_dir / "topic_descriptions.xlsx"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    table = topic_table(model_dir)
    long, wide = top_words(model_dir, top_n)
    sheets = {
        "说明": _readme_sheet(model_dir, table, top_n),
        "Topics": table,
        f"Top{top_n}_Words": wide,
        f"Top{top_n}_With_Scores": long,
        "Representative_Docs": representative_docs(model_dir),
    }
    widths = {"说明": [22, 90], "Topics": [8, 40, 24, 10, 10, 70, 70, 70], "Representative_Docs": [8, 6, 150]}
    with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
        for name, df in sheets.items():
            _clean(df).to_excel(writer, sheet_name=name, index=False)
            ws = writer.sheets[name]
            ws.freeze_panes = "B2" if name != "说明" else None
            for i, w in enumerate(widths.get(name, []), start=1):
                ws.column_dimensions[ws.cell(row=1, column=i).column_letter].width = w
        writer.sheets["Topics"].column_dimensions["E"].number_format = "0.00%"
        for cell in writer.sheets["Topics"]["E"][1:]:
            cell.number_format = "0.00%"
    log.info("topic 描述已写入 %s（%d 个 topic）", out_path, len(table))
    return out_path
