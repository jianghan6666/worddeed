"""构建 CEO-firm-year 面板。

1. 只保留 is_ceo 的 transcript component，按 ticker + 讲话年份匹配 Compustat fyear
2. 每个 firm-year (gvkey, year) 只保留发言词数最多的 CEO（is_ceo 混入了 Division CEO / CFO 等）
3. topic density 按 retained_word_count 加权平均（topic 全为 0 的极短发言不参与）
4. 主 CEO 的性别 / 年龄 / 学历，以及按词数加权的讲话情绪 sentiment_transformer
5. 目标变量、控制变量与 fold 划分

输出（panel_dir 下）:
    ceo_firm_year_panel.parquet   每行一个 firm-year
    component_map.parquet         component 级映射 (orig_idx -> panel_id)，用于回溯原始数据
"""

import logging
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import sparse

from .config import DEFAULT_PATHS, load_paths
from .data import iter_topic_chunks, load_ceo_components, load_compustat, topic_shape
from .features import TOPIC_PREFIX, add_model_columns
from .splits import assign_folds

log = logging.getLogger(__name__)

PANEL_FILE = "ceo_firm_year_panel.parquet"
COMPONENT_MAP_FILE = "component_map.parquet"
REQUIRED_COLUMNS = ["gvkey", "year", "ceo_id", "sich", "fold", "split_group", "panel_id",
                    "ceo_gender", "ceo_age", "ceo_educ", "sent_transformer"]


def keep_main_ceo(comp):
    words = comp.groupby(["gvkey", "year", "ceo_id"])["retained_word_count"].sum()
    share = words / words.groupby(level=[0, 1]).transform("sum")
    main_ceo = words.groupby(level=[0, 1]).idxmax().apply(lambda t: t[2]).rename("main_ceo")
    comp = comp.merge(main_ceo, left_on=["gvkey", "year"], right_index=True)
    n_before = len(comp)
    comp = comp[comp["ceo_id"] == comp["main_ceo"]].drop(columns="main_ceo")
    log.info("  丢弃非主 CEO components: %s；保留 %s", f"{n_before - len(comp):,}", f"{len(comp):,}")
    log.info("  主 CEO 词数占比中位数: %.3f", share.groupby(level=[0, 1]).max().median())
    return comp


def aggregate_meta(comp):
    comp = comp.assign(w_pres=comp["retained_word_count"]
                       * (comp["transcriptcomponenttypename"] == "Presenter Speech").astype(int))
    panel = (
        comp.groupby(["gvkey", "year"])
        .agg(
            ceo_id=("ceo_id", "first"),
            ceo_name=("transcriptpersonname", lambda s: s.mode().iat[0]),
            companyid=("companyid", lambda s: s.mode().iat[0]),
            tic=("symbolvalue", "first"),
            ggroup=("ggroup", lambda s: s.mode().iat[0] if s.notna().any() else np.nan),
            n_components=("orig_idx", "size"),
            n_transcripts=("transcriptid", "nunique"),
            total_words=("retained_word_count", "sum"),
            w_pres=("w_pres", "sum"),
        )
        .reset_index()
    )
    panel["pres_word_share"] = panel.pop("w_pres") / panel["total_words"]
    return panel


def pool_topics(comp, n_groups, topics_path, topics_key="topic_distr", chunk_rows=200_000):
    """按 panel_id 对 topic density 做 retained_word_count 加权平均。"""
    order = np.argsort(comp["orig_idx"].values)
    rows = comp["orig_idx"].values[order]
    gids = comp["panel_id"].values[order]
    w = comp["retained_word_count"].values[order].astype(np.float64)

    sums, tot_w, n_zero = None, np.zeros(n_groups), 0
    for start, X in iter_topic_chunks(topics_path, topics_key, chunk_rows):
        if sums is None:
            sums = np.zeros((n_groups, X.shape[1]))
        lo, hi = np.searchsorted(rows, [start, start + len(X)])
        if hi == lo:
            continue
        local = rows[lo:hi] - start
        # 行和为 0 的 component（短发言，未分配 topic）不参与平均
        wk = np.where(X[local].sum(axis=1) > 1e-9, w[lo:hi], 0.0)
        n_zero += int((wk == 0).sum())
        agg = sparse.csr_matrix((wk, (gids[lo:hi], local)), shape=(n_groups, len(X)))
        sums += agg @ X
        tot_w += np.bincount(gids[lo:hi], weights=wk, minlength=n_groups)
    log.info("  排除 topic 全 0 的 components: %s；无有效 topic 的 firm-year: %d", f"{n_zero:,}", (tot_w == 0).sum())
    with np.errstate(invalid="ignore"):
        pooled = (sums / tot_w[:, None]).astype(np.float32)
    cols = [f"{TOPIC_PREFIX}{i:03d}" for i in range(pooled.shape[1])]
    return pd.DataFrame(pooled, columns=cols)


def ceo_text_features(comp):
    """主 CEO 的性别 / 年龄 / 学历（同一 firm-year 内取值一致）与按词数加权的讲话情绪。"""
    chars = comp.groupby("panel_id")[["gender", "age", "educ_level"]].first().rename(
        columns={"gender": "ceo_gender", "age": "ceo_age", "educ_level": "ceo_educ"}
    )
    w = comp["retained_word_count"].where(comp["sentiment_transformer"].notna())
    sent = (comp["sentiment_transformer"] * w).groupby(comp["panel_id"]).sum() / w.groupby(comp["panel_id"]).sum()
    return chars.join(sent.rename("sent_transformer")).reset_index()


def add_targets(p):
    p["rd_missing"] = p["xrd"].isna().astype(int)
    xrd0 = p["xrd"].fillna(0.0)
    p["has_rd"] = (xrd0 > 0).astype(int)
    at_ok = p["at"] > 0
    sale_ok = p["sale"] > 0
    # 两种缺失处理：原值（缺失保留 NaN）/ 缺失视为 0
    p["rd_at"] = np.where(at_ok, p["xrd"] / p["at"], np.nan)
    p["rd_sale"] = np.where(sale_ok, p["xrd"] / p["sale"], np.nan)
    p["rd_at_fill0"] = np.where(at_ok, xrd0 / p["at"], np.nan)
    p["rd_sale_fill0"] = np.where(sale_ok, xrd0 / p["sale"], np.nan)
    # 上一财年的 ratio（缺失 xrd 视为 0）
    p["rd_at_lag"] = np.where(p["at_lag"] > 0, p["xrd_lag"].fillna(0.0) / p["at_lag"], np.nan)
    p["rd_sale_lag"] = np.where(p["sale_lag"] > 0, p["xrd_lag"].fillna(0.0) / p["sale_lag"], np.nan)
    p["log_at"] = np.log(p["at"].where(at_ok))
    p["sic2"] = (p["sich"] // 100).astype("Int64")
    # winsorize 在实验阶段做，只用训练集的分位数，避免泄露
    return p


def build_panel(paths=DEFAULT_PATHS, out_dir=None, n_folds=5, seed=42, chunk_rows=200_000):
    """从原始数据构建面板并写入 out_dir（默认 paths.panel_dir）。返回面板 DataFrame。"""
    paths = load_paths(paths)
    out_dir = Path(out_dir) if out_dir else paths.panel_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    log.info("1/6 读取 CEO components")
    comp, n_total = load_ceo_components(paths.require("transcripts"))
    log.info("  is_ceo components: %s / %s", f"{len(comp):,}", f"{n_total:,}")

    log.info("2/6 按 ticker + 讲话年份匹配 Compustat")
    firm = load_compustat(paths.require("compustat"))
    comp = comp.merge(
        firm.rename(columns={"tic": "symbolvalue"}),
        left_on=["symbolvalue", "year"], right_on=["symbolvalue", "fyear"],
        how="inner", validate="m:1",
    )
    log.info("  匹配上 Compustat: %s", f"{len(comp):,}")

    log.info("3/6 每个 firm-year 保留主 CEO")
    comp = keep_main_ceo(comp)
    panel = aggregate_meta(comp)
    panel = panel.merge(
        firm.drop(columns="tic").rename(columns={"fyear": "year"}),
        on=["gvkey", "year"], how="left", validate="1:1",
    )
    panel["panel_id"] = np.arange(len(panel))
    comp = comp.merge(panel[["gvkey", "year", "panel_id"]], on=["gvkey", "year"])

    log.info("4/6 加权 pooling topic density")
    n_topic_rows = topic_shape(paths.require("topics"), paths.topics_key)[0]
    if n_topic_rows != n_total:
        raise ValueError(f"topic 矩阵行数 {n_topic_rows:,} 与 transcript 行数 {n_total:,} 不一致")
    panel = pd.concat([panel, pool_topics(comp, len(panel), paths.topics, paths.topics_key, chunk_rows)], axis=1)

    log.info("5/6 CEO 特征与讲话情绪")
    panel = panel.merge(ceo_text_features(comp), on="panel_id", how="left", validate="1:1")

    log.info("6/6 目标变量与切分")
    panel = add_targets(panel)
    panel = assign_folds(panel, n_folds=n_folds, seed=seed)

    panel.to_parquet(out_dir / PANEL_FILE, index=False)
    comp[["orig_idx", "panel_id", "transcriptid", "retained_word_count"]].to_parquet(
        out_dir / COMPONENT_MAP_FILE, index=False
    )
    log.info("面板 %s：firm %s，CEO %s，split_group %s；已写入 %s",
             panel.shape, f"{panel.gvkey.nunique():,}", f"{panel.ceo_id.nunique():,}",
             f"{panel.split_group.nunique():,}", out_dir)
    return panel


def load_panel(source=DEFAULT_PATHS):
    """读取面板并添加建模用的类别列。source 可以是 paths 配置、Paths 对象或 parquet 文件路径。"""
    if isinstance(source, (str, Path)) and str(source).endswith(".parquet"):
        file = Path(source)
    else:
        file = load_paths(source).panel_dir / PANEL_FILE
    if not file.exists():
        raise FileNotFoundError(f"找不到面板 {file}，请先运行 ceo-rd build-panel")
    panel = pd.read_parquet(file)
    missing = [c for c in REQUIRED_COLUMNS if c not in panel.columns]
    if missing:
        raise ValueError(f"面板缺少列 {missing}（可能是旧版本生成的），请重新运行 ceo-rd build-panel")
    return add_model_columns(panel)
