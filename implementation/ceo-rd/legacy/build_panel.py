"""
Step 1: 构建 CEO-firm-year 面板

- 只保留 is_ceo 的 transcript component，按 ticker + 通话年份匹配 Compustat
- 每个 firm-year (gvkey, year) 只保留发言词数最多的 CEO（is_ceo 混入了 Division CEO / CFO 等）
- topic density 按 retained_word_count 加权平均（从 npz 分块流式读取，避免 16GB 全量载入）
- 切分：按 firm–CEO 连通分量分组的 StratifiedGroupKFold，fold 0 = holdout test

输出:
    data/panel/ceo_firm_year_panel.parquet   每行一个 firm-year，含 topic_000..topic_353、目标变量、控制变量、fold
    data/panel/component_map.parquet         component 级映射 (orig_idx -> panel_id)，用于回溯
"""

import gc
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import sparse
from scipy.sparse.csgraph import connected_components
from sklearn.model_selection import StratifiedGroupKFold

DATA = Path("./data")
TEXT_PKL = DATA / "t_combined_nodup_13-23_compNameOK_retainedNoEmpty_namesANDcomps_removed_w_scores_5years_ticker_sentiment_title_demos_NoText.pickle"
TOPIC_NPZ = DATA / "topic_density/13-23_354Tpoics/topic_distr_Full_wNoIdeoLabel.npz"
FIRM_CSV = DATA / "ceo_and_firm/compustat_fundamentals_annual_2010-2025.csv"
OUT_DIR = DATA / "panel"

N_FOLDS = 5
SEED = 42
CHUNK_ROWS = 200_000


def load_ceo_components():
    keep = [
        "companyid", "transcriptid", "transcriptpersonid", "directorid", "transcriptpersonname",
        "symbolvalue", "year", "retained_word_count", "transcriptcomponenttypename", "ggroup",
    ]
    df = pd.read_pickle(TEXT_PKL)
    n_total = len(df)
    assert df.index.equals(pd.RangeIndex(n_total))  # index 与 topic_distr 行对齐
    c = df.loc[df["is_ceo"], keep].copy()
    del df
    gc.collect()
    c["orig_idx"] = c.index
    # CEO 身份：优先 BoardEx directorid（同一人可能有多个 transcriptpersonid）
    c["ceo_id"] = np.where(
        c["directorid"].notna(),
        "bx_" + c["directorid"].astype("Int64").astype(str),
        "tp_" + c["transcriptpersonid"].astype("Int64").astype(str),
    )
    return c.reset_index(drop=True), n_total


def load_firm():
    f = pd.read_csv(FIRM_CSV)
    cols = ["tic", "gvkey", "fyear", "datadate", "at", "sale", "xrd", "sich"]
    f = f[cols].sort_values(["gvkey", "fyear", "datadate"])
    # (tic, fyear) 仅 LIMX/VSXY 有重复，财务值为空，保留最新 datadate
    f = f.drop_duplicates(["tic", "fyear"], keep="last").drop_duplicates(["gvkey", "fyear"], keep="last")
    lag = f[["gvkey", "fyear", "at", "sale", "xrd"]].copy()
    lag["fyear"] += 1
    f = f.merge(lag, on=["gvkey", "fyear"], how="left", suffixes=("", "_lag"))
    return f


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
    # 上一财年的 ratio，供后续 baseline / 变化量模型使用
    p["rd_at_lag"] = np.where(p["at_lag"] > 0, p["xrd_lag"].fillna(0.0) / p["at_lag"], np.nan)
    p["rd_sale_lag"] = np.where(p["sale_lag"] > 0, p["xrd_lag"].fillna(0.0) / p["sale_lag"], np.nan)
    p["log_at"] = np.log(p["at"].where(at_ok))
    p["sic2"] = (p["sich"] // 100).astype("Int64")
    # winsorize 留到训练阶段，只用 train 的分位数，避免泄露
    return p


def assign_folds(p):
    # firm–CEO 二部图的连通分量：同一 CEO 跨公司时，相关公司必须在同一侧
    firms = pd.factorize(p["gvkey"])[0]
    ceos = pd.factorize(p["ceo_id"])[0] + firms.max() + 1
    n = ceos.max() + 1
    adj = sparse.coo_matrix((np.ones(len(p)), (firms, ceos)), shape=(n, n))
    _, labels = connected_components(adj, directed=False)
    p["split_group"] = labels[firms]
    p["fold"] = -1
    sgkf = StratifiedGroupKFold(n_splits=N_FOLDS, shuffle=True, random_state=SEED)
    for k, (_, idx) in enumerate(sgkf.split(p, p["has_rd"], groups=p["split_group"])):
        p.iloc[idx, p.columns.get_loc("fold")] = k
    return p


def pool_topics(comp, n_groups, n_total):
    """按 panel_id 对 topic density 做 retained_word_count 加权平均，分块读取 npz。"""
    order = np.argsort(comp["orig_idx"].values)
    rows = comp["orig_idx"].values[order]
    gids = comp["panel_id"].values[order]
    w = comp["retained_word_count"].values[order].astype(np.float64)

    with zipfile.ZipFile(TOPIC_NPZ) as zf, zf.open("topic_distr.npy") as fh:
        version = np.lib.format.read_magic(fh)
        shape, fortran, dtype = np.lib.format._read_array_header(fh, version)
        assert shape[0] == n_total and not fortran
        n_topics = shape[1]
        sums = np.zeros((n_groups, n_topics))
        tot_w = np.zeros(n_groups)
        n_zero = 0
        for start in range(0, shape[0], CHUNK_ROWS):
            stop = min(start + CHUNK_ROWS, shape[0])
            buf = fh.read((stop - start) * n_topics * dtype.itemsize)
            X = np.frombuffer(buf, dtype=dtype).reshape(stop - start, n_topics)
            lo, hi = np.searchsorted(rows, [start, stop])
            if hi == lo:
                continue
            local = rows[lo:hi] - start
            # 行和为 0 的 component（短发言，未分配 topic）不参与平均
            wk = np.where(X[local].sum(axis=1) > 1e-9, w[lo:hi], 0.0)
            n_zero += int((wk == 0).sum())
            agg = sparse.csr_matrix((wk, (gids[lo:hi], local)), shape=(n_groups, stop - start))
            sums += agg @ X
            tot_w += np.bincount(gids[lo:hi], weights=wk, minlength=n_groups)
    print(f"  排除 topic 全 0 的 components: {n_zero:,}；无有效 topic 的 firm-year: {(tot_w == 0).sum()}")
    with np.errstate(invalid="ignore"):
        return (sums / tot_w[:, None]).astype(np.float32), n_topics


def main():
    OUT_DIR.mkdir(exist_ok=True)

    print("1/5 读取 CEO components")
    comp, n_total = load_ceo_components()
    print(f"  is_ceo components: {len(comp):,}")

    print("2/5 匹配 Compustat")
    firm = load_firm()
    comp = comp.merge(
        firm.rename(columns={"tic": "symbolvalue"}),
        left_on=["symbolvalue", "year"], right_on=["symbolvalue", "fyear"],
        how="inner", validate="m:1",
    )
    print(f"  匹配上 Compustat: {len(comp):,}")

    print("3/5 每个 firm-year 保留主 CEO")
    words = comp.groupby(["gvkey", "year", "ceo_id"])["retained_word_count"].sum()
    share = words / words.groupby(level=[0, 1]).transform("sum")
    main_ceo = words.groupby(level=[0, 1]).idxmax().apply(lambda t: t[2]).rename("main_ceo")
    comp = comp.merge(main_ceo, left_on=["gvkey", "year"], right_index=True)
    n_before = len(comp)
    comp = comp[comp["ceo_id"] == comp["main_ceo"]].drop(columns="main_ceo")
    print(f"  丢弃非主 CEO components: {n_before - len(comp):,}；保留 {len(comp):,}")
    print(f"  主 CEO 词数占比中位数: {share.groupby(level=[0, 1]).max().median():.3f}")

    # 面板元数据
    comp["is_pres"] = (comp["transcriptcomponenttypename"] == "Presenter Speech").astype(int)
    comp["w_pres"] = comp["retained_word_count"] * comp["is_pres"]
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
    panel = panel.merge(
        firm.drop(columns="tic").rename(columns={"fyear": "year"}),
        on=["gvkey", "year"], how="left", validate="1:1",
    )
    panel["panel_id"] = np.arange(len(panel))
    comp = comp.merge(panel[["gvkey", "year", "panel_id"]], on=["gvkey", "year"])

    print("4/5 加权 pooling topic density")
    topics, n_topics = pool_topics(comp, len(panel), n_total)
    topic_cols = [f"topic_{i:03d}" for i in range(n_topics)]
    panel = pd.concat([panel, pd.DataFrame(topics, columns=topic_cols)], axis=1)

    print("5/5 目标变量与切分")
    panel = add_targets(panel)
    panel = assign_folds(panel)

    panel.to_parquet(OUT_DIR / "ceo_firm_year_panel.parquet", index=False)
    comp[["orig_idx", "panel_id", "transcriptid", "retained_word_count"]].to_parquet(
        OUT_DIR / "component_map.parquet", index=False
    )

    # 汇总
    print(f"\n面板: {panel.shape}, firm {panel.gvkey.nunique():,}, CEO {panel.ceo_id.nunique():,}, "
          f"split_group {panel.split_group.nunique():,} (最大 {panel.split_group.value_counts().max()} firm-years)")
    print(panel.groupby("year").size().to_string())
    summ = panel[["rd_at", "rd_sale", "rd_at_fill0", "rd_sale_fill0", "has_rd", "rd_missing", "log_at", "sic2"]]
    print(summ.describe(percentiles=[0.01, 0.5, 0.99]).T.to_string())
    print(panel.groupby("fold").agg(n=("panel_id", "size"), firms=("gvkey", "nunique"),
                                    has_rd=("has_rd", "mean"), rd_at=("rd_at_fill0", "mean")).to_string())


if __name__ == "__main__":
    main()
