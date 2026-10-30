"""命令行入口：ceo-rd build-panel / run / report。"""

import argparse
import logging
import sys

from .config import DEFAULT_PATHS


def enable_logging(level=logging.INFO):
    """把 ceo_rd 的进度日志输出到控制台（notebook 中也可调用）。"""
    logger = logging.getLogger("ceo_rd")
    if not any(isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler)
               for h in logger.handlers):
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter("%(asctime)s %(message)s", "%H:%M:%S"))
        logger.addHandler(handler)
    logger.setLevel(level)


def main(argv=None):
    parser = argparse.ArgumentParser(prog="ceo-rd", description="用 CEO 讲话 topic 预测公司 R&D 强度")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("build-panel", help="从原始数据构建 firm-year 面板")
    p.add_argument("--paths", default=DEFAULT_PATHS, help="路径配置（默认 %(default)s）")
    p.add_argument("--out", default=None, help="输出目录（默认取路径配置中的 panel_dir）")

    p = sub.add_parser("run", help="运行一个实验配置，并生成 report.md")
    p.add_argument("spec", help="实验配置 YAML，例如 experiments/strict_controls.yaml")
    p.add_argument("--paths", default=DEFAULT_PATHS, help="路径配置（默认 %(default)s）")
    p.add_argument("--out", default=None, help="结果目录（默认 results_dir/<实验名>）")
    p.add_argument("--targets", nargs="+", help="只运行这些目标变量")
    p.add_argument("--models", nargs="+", help="只运行这些模型")

    p = sub.add_parser("report", help="从结果目录重新生成 report.md")
    p.add_argument("result_dir")

    _add_topic_commands(sub)

    args = parser.parse_args(argv)
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(errors="replace")
    enable_logging()

    if args.command == "build-panel":
        from .panel import build_panel
        build_panel(args.paths, out_dir=args.out)
    elif args.command == "run":
        from .experiment import run_experiment
        from .report import write_report
        result = run_experiment(args.spec, paths=args.paths, out_dir=args.out,
                                targets=args.targets, models=args.models)
        print(f"报告: {write_report(result)}")
    elif args.command == "report":
        from .report import write_report
        print(f"报告: {write_report(args.result_dir)}")
    elif args.command == "topics":
        _run_topic_command(args)


def _add_topic_commands(sub):
    """ceo-rd topics train / infer / assign / training-labels / describe。"""
    topics = sub.add_parser("topics", help="BERTopic topic modeling：训练、推断、topic 描述").add_subparsers(
        dest="topic_command", required=True)

    def add_input_args(p):
        p.add_argument("--paths", default=DEFAULT_PATHS, help="路径配置（默认 %(default)s）")
        p.add_argument("--input", default=None, help="文本文件（默认取路径配置中的 corpus）")
        p.add_argument("--text-col", default="componenttext_masked", help="文本列（默认 %(default)s）")
        p.add_argument("--filter-notna", nargs="+", default=None, help="只处理这些列非缺失的行（如 averageDem）")
        p.add_argument("--rows-from", default=None,
                       help="只处理这些行：.npy 行号数组，或表格文件中的一列（见 --rows-col）。例如 "
                            "data/replication_sample/transcripts_is_ceo.pickle，输出与复现子样本逐行对齐")
        p.add_argument("--rows-col", default="orig_row", help="--rows-from 为表格文件时的行号列（默认 %(default)s）")
        p.add_argument("--overwrite", action="store_true", help="允许覆盖已有的输出文件")
        p.add_argument("--keep-parts", action="store_true", help="完成后保留分块中间结果")

    p = topics.add_parser("train", help="训练 BERTopic 模型（需要 .[topics]）")
    p.add_argument("spec", help="训练配置 YAML，例如 topic_models/bertopic_ideo_13-23_relaxed.yaml")
    p.add_argument("--paths", default=DEFAULT_PATHS, help="路径配置（默认 %(default)s）")
    p.add_argument("--corpus", default=None, help="文本文件（默认取路径配置中的 corpus）")
    p.add_argument("--out", default=None, help="模型输出目录（默认 models_dir/<name>）")
    p.add_argument("--embeddings", default=None, help="已有 embedding（.npy / .npz / 分块目录），不给则重新计算")
    p.add_argument("--embedding-cache", default=None, help="新计算 embedding 的缓存目录（默认 <out>.embeddings）")
    p.add_argument("--embedding-model", default=None, help="覆盖配置中的 embedding 模型（如本地路径）")
    p.add_argument("--overwrite", action="store_true", help="允许覆盖已有的非空输出目录")

    p = topics.add_parser("infer", help="每条文本的 topic 分布（approximate_distribution，需要 .[topics]），输出 npz")
    p.add_argument("model_dir", help="模型目录，例如 models/bertopic_ideo_13-23_relaxed_354Topics")
    p.add_argument("--out", required=True, help="输出 npz 路径（数组名 topic_distr）")
    add_input_args(p)
    p.add_argument("--chunk-size", type=int, default=100_000, help="每块文本数，逐块落盘、可断点续跑（默认 %(default)s）")
    p.add_argument("--batch-size", type=int, default=1000)
    p.add_argument("--window", type=int, default=4)
    p.add_argument("--stride", type=int, default=1)
    p.add_argument("--min-similarity", type=float, default=0.1)
    p.add_argument("--use-embedding-model", action="store_true", help="用 embedding 计算相似度（慢，需要 embedding 模型）")
    p.add_argument("--embedding-model", default=None, help="embedding 模型名称或本地路径（仅 --use-embedding-model 时需要）")

    p = topics.add_parser("assign", help="每条文本的主 topic（BERTopic transform，需要 .[topics] 与 embedding 模型），输出 parquet")
    p.add_argument("model_dir", help="模型目录，例如 models/bertopic_ideo_13-23_relaxed_354Topics")
    p.add_argument("--out", required=True, help="输出 parquet 路径（列：row, topic, topic_prob）")
    add_input_args(p)
    p.add_argument("--chunk-size", type=int, default=50_000, help="每块文本数，逐块落盘、可断点续跑（默认 %(default)s）")
    p.add_argument("--embedding-model", default=None,
                   help="embedding 模型名称或本地路径（默认：模型中保存的名称；现有模型须指定或使用 all-mpnet-base-v2）")

    p = topics.add_parser("training-labels", help="导出训练文本在训练时的主 topic（只读模型文件，不需要 BERTopic）")
    p.add_argument("model_dir")
    p.add_argument("--out", required=True, help="输出 parquet 路径（列：row, topic）")
    p.add_argument("--paths", default=DEFAULT_PATHS, help="路径配置（默认 %(default)s）")
    p.add_argument("--input", default=None, help="训练用的文本文件（默认取路径配置中的 corpus）；模型目录有 train_row_index.npy 时不需要")
    p.add_argument("--filter-notna", nargs="+", default=["averageDem"], help="训练集筛选规则（默认 averageDem）")
    p.add_argument("--overwrite", action="store_true")

    p = topics.add_parser("describe", help="导出 topic 描述 Excel（只读模型文件，不需要 BERTopic）")
    p.add_argument("model_dir")
    p.add_argument("--out", default=None, help="输出 xlsx 路径（默认 <模型目录>/topic_descriptions.xlsx）")
    p.add_argument("--top-n", type=int, default=25)


def _run_topic_command(args):
    from pathlib import Path

    import numpy as np

    from .config import load_paths
    from . import topics as T

    def read_input():
        source = args.input or load_paths(args.paths).require("corpus")
        rows = T.read_row_numbers(args.rows_from, args.rows_col) if args.rows_from else None
        texts, row_index = T.load_corpus(source, args.text_col, args.filter_notna, rows=rows)
        meta = {"model_dir": str(args.model_dir), "input": str(source), "text_column": args.text_col,
                "filter_notna": args.filter_notna, "rows_from": args.rows_from}
        subset = args.filter_notna or args.rows_from
        return texts, (row_index if subset else None), meta

    if args.topic_command == "train":
        paths = load_paths(args.paths)
        spec = T.TopicModelSpec.from_yaml(args.spec)
        out = Path(args.out) if args.out else paths.models_dir / spec.name
        T.train_topic_model(spec, args.corpus or paths.require("corpus"), out, embeddings=args.embeddings,
                            embedding_cache=args.embedding_cache, embedding_model=args.embedding_model,
                            overwrite=args.overwrite)
    elif args.topic_command == "infer":
        texts, rows, meta = read_input()
        model = T.load_topic_model(args.model_dir, embedding_model=args.embedding_model)
        T.infer_topic_distribution(
            model, texts, args.out, row_index=rows, chunk_size=args.chunk_size, overwrite=args.overwrite,
            keep_parts=args.keep_parts, meta=meta, window=args.window, stride=args.stride,
            min_similarity=args.min_similarity, batch_size=args.batch_size, use_embedding_model=args.use_embedding_model,
        )
    elif args.topic_command == "assign":
        texts, rows, meta = read_input()
        emb = args.embedding_model or T.saved_embedding_model(args.model_dir)
        if emb is None:  # 现有模型保存时没有记录 embedding 模型；训练时用的是 all-mpnet-base-v2
            emb = T.DEFAULT_EMBEDDING_MODEL
            logging.getLogger("ceo_rd").info("模型未记录 embedding 模型，使用 %s", emb)
        meta["embedding_model"] = emb
        model = T.load_topic_model(args.model_dir, embedding_model=emb)
        T.assign_topics(model, texts, args.out, row_index=rows, chunk_size=args.chunk_size,
                        overwrite=args.overwrite, keep_parts=args.keep_parts, meta=meta)
    elif args.topic_command == "training-labels":
        row_file = Path(args.model_dir) / "train_row_index.npy"
        if row_file.exists():
            rows = np.load(row_file)
        else:
            source = args.input or load_paths(args.paths).require("corpus")
            _, rows = T.load_corpus(source, notna=args.filter_notna)
        T.export_training_topics(args.model_dir, rows, args.out, overwrite=args.overwrite)
    elif args.topic_command == "describe":
        T.export_topic_excel(args.model_dir, args.out, top_n=args.top_n)


if __name__ == "__main__":
    main()
