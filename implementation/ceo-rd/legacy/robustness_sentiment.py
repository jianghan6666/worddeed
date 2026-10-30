"""
稳健性检验: 加入 CEO 讲话情绪 sentiment_transformer

情绪特征: 主 CEO 各 component 的 sentiment_transformer 按 retained_word_count 加权平均（firm-year 级）
样本: 与 robustness_controls.py 相同（滞后 ratio 非缺失）
control 组合: none / base / sic4 / lag+sic4
特征: [controls] + {无, sentiment, topics, topics+sentiment}
增量: sentiment 相对 topics（topics -> topics+sentiment）；sentiment 相对 controls（controls -> controls+sentiment）

输出:
    data/panel/ceo_sentiment.parquet           firm-year 级情绪（首次运行时从原始 df 生成）
    results/sentiment_metrics.csv
    results/sentiment_delta_r2.csv
"""

import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.metrics import r2_score
from sklearn.model_selection import GridSearchCV, PredefinedSplit
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.preprocessing import FunctionTransformer, OneHotEncoder, StandardScaler

from robustness_controls import MODELS, TARGETS
from train_models import SEED, clr, cluster_bootstrap, metrics

PANEL = Path("./data/panel/ceo_firm_year_panel.parquet")
COMP_MAP = Path("./data/panel/component_map.parquet")
SENTIMENT = Path("./data/panel/ceo_sentiment.parquet")
TEXT_PKL = Path("./data/t_combined_nodup_13-23_compNameOK_retainedNoEmpty_namesANDcomps_removed_w_scores_5years_ticker_sentiment_title_demos_NoText.pickle")
OUT_DIR = Path("./results")

CONTROL_SETS = {
    "none": ([], []),
    "base": (["log_at"], ["sic2_cat", "year_cat"]),
    "sic4": (["log_at"], ["sic4_cat", "year_cat"]),
    "lag+sic4": (["log_at", "y_lag"], ["sic4_cat", "year_cat"]),
}
TEXT_SETS = {  # (含 sentiment, 含 topics)
    "controls": (False, False),
    "+sentiment": (True, False),
    "+topics": (False, True),
    "+topics+sentiment": (True, True),
}


def build_sentiment():
    m = pd.read_parquet(COMP_MAP)
    df = pd.read_pickle(TEXT_PKL)
    m["sent"] = df.loc[m["orig_idx"].values, "sentiment_transformer"].values
    del df
    w = m["retained_word_count"].where(m["sent"].notna())
    s = (m["sent"] * w).groupby(m["panel_id"]).sum() / w.groupby(m["panel_id"]).sum()
    out = s.rename("sent_transformer").reset_index()
    out.to_parquet(SENTIMENT, index=False)
    return out


def make_preprocessor(num_cols, cat_cols, topic_cols):
    parts = []
    if num_cols:
        parts.append(("num", make_pipeline(SimpleImputer(strategy="median"), StandardScaler()), num_cols))
    if cat_cols:
        parts.append(("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), cat_cols))
    if topic_cols:
        parts.append(("topic", make_pipeline(FunctionTransformer(clr), StandardScaler()), topic_cols))
    return ColumnTransformer(parts)


def main():
    sent = pd.read_parquet(SENTIMENT) if SENTIMENT.exists() else build_sentiment()
    panel = pd.read_parquet(PANEL).merge(sent, on="panel_id", how="left", validate="1:1")
    topic_cols = [c for c in panel.columns if c.startswith("topic_")]
    sich = panel["sich"].astype("Int64")
    panel["sic2_cat"] = (sich // 100).astype(str)
    panel["sic4_cat"] = sich.astype(str)
    panel["year_cat"] = panel["year"].astype(str)

    rng = np.random.default_rng(SEED)
    rows, deltas = [], []
    for ratio, ycol, lagcol in TARGETS:
        d = panel[panel[ycol].notna() & panel[lagcol].notna()].copy()
        tr = d[d["fold"] != 0]
        lo, hi = tr[ycol].quantile([0.01, 0.99])
        d["y_lag"] = d[lagcol].clip(lo, hi)
        tr, te = d[d["fold"] != 0], d[d["fold"] == 0]
        y_tr, y_te = tr[ycol].clip(lo, hi).values, te[ycol].clip(lo, hi).values
        cv = PredefinedSplit(tr["fold"].values - 1)
        print(f"\n=== {ratio} (fill0): train {len(tr):,}, test {len(te):,}, "
              f"corr(y, sentiment) = {np.corrcoef(y_tr, tr['sent_transformer'])[0, 1]:.3f} ===")

        preds = {}
        for cs, (num_cols, cat_cols) in CONTROL_SETS.items():
            for ts, (with_sent, with_topics) in TEXT_SETS.items():
                nc = num_cols + (["sent_transformer"] if with_sent else [])
                if not (nc or cat_cols or with_topics):
                    continue  # none + controls: 无特征
                for mname, (est, grid) in MODELS.items():
                    prep = make_preprocessor(nc, cat_cols, topic_cols if with_topics else [])
                    pipe = Pipeline([("prep", prep), ("model", est)])
                    t0 = time.time()
                    gs = GridSearchCV(pipe, {f"model__{k}": v for k, v in grid.items()}, cv=cv,
                                      scoring="r2", n_jobs=1 if mname == "XGBoost" else 8, refit=True)
                    gs.fit(tr, y_tr)
                    preds[(cs, ts, mname)] = gs.predict(te)
                    m = metrics(y_te, preds[(cs, ts, mname)])
                    rows.append({
                        "ratio": ratio, "controls": cs, "features": ts, "model": mname,
                        "n_train": len(tr), "n_test": len(te), "cv_r2": gs.best_score_,
                        **{f"test_{k}": v for k, v in m.items()},
                        "best_params": {k.replace("model__", ""): v for k, v in gs.best_params_.items()},
                        "secs": round(time.time() - t0, 1),
                    })
                    print(f"  {cs:<9} {ts:<18} {mname:<8} cv_r2={gs.best_score_:.3f}  "
                          f"test_r2={m['r2']:.3f}  rho={m['spearman']:.3f}  ({rows[-1]['secs']}s)")

        groups = te["split_group"].values
        comparisons = [("+topics", "+topics+sentiment", "sentiment | topics")]
        for cs in CONTROL_SETS:
            for mname in MODELS:
                comps = list(comparisons)
                if cs != "none":
                    comps += [("controls", "+sentiment", "sentiment | controls"),
                              ("controls", "+topics", "topics | controls")]
                for a, b, label in comps:
                    pa, pb = preds[(cs, a, mname)], preds[(cs, b, mname)]
                    boot = cluster_bootstrap(y_te, {"a": pa, "b": pb}, groups, rng)
                    dr = boot["b"] - boot["a"]
                    deltas.append({
                        "ratio": ratio, "controls": cs, "model": mname, "increment": label,
                        "r2_from": r2_score(y_te, pa), "r2_to": r2_score(y_te, pb),
                        "delta_r2": r2_score(y_te, pb) - r2_score(y_te, pa),
                        "delta_ci_lo": np.percentile(dr, 2.5), "delta_ci_hi": np.percentile(dr, 97.5),
                        "p_delta_le_0": (dr <= 0).mean(),
                    })

        pd.DataFrame(rows).to_csv(OUT_DIR / "sentiment_metrics.csv", index=False)
        pd.DataFrame(deltas).to_csv(OUT_DIR / "sentiment_delta_r2.csv", index=False)

    print("\n=== 增量 ===")
    print(pd.DataFrame(deltas).round(3).to_string(index=False))


if __name__ == "__main__":
    main()
