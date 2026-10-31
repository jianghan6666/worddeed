"""
稳健性检验: controls 中加入 CEO 特征（gender / age / educ_level）

样本: 在 robustness_controls.py 的样本（滞后 ratio 非缺失）基础上，再限定 CEO 三项特征均非缺失
control 组合: base / sic4 / lag+sic4，各自 不加 / 加 CEO 特征
每个组合比较 controls vs controls+topics；另报告 CEO 特征本身的增量

输出:
    data/panel/ceo_chars.parquet              firm-year 级 CEO 特征（首次运行时从原始 df 生成）
    results/ceo_demo_metrics.csv
    results/ceo_demo_delta_r2.csv              topics 的增量（给定 controls）
    results/ceo_demo_delta_demo.csv            CEO 特征的增量（给定是否含 topics）
"""

import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import r2_score
from sklearn.model_selection import GridSearchCV, PredefinedSplit
from sklearn.pipeline import Pipeline

from robustness_controls import MODELS, TARGETS, make_preprocessor
from train_models import SEED, cluster_bootstrap, metrics

PANEL = Path("./data/panel/ceo_firm_year_panel.parquet")
COMP_MAP = Path("./data/panel/component_map.parquet")
CEO_CHARS = Path("./data/panel/ceo_chars.parquet")
TEXT_PKL = Path("./data/t_combined_nodup_13-23_compNameOK_retainedNoEmpty_namesANDcomps_removed_w_scores_5years_ticker_sentiment_title_demos_NoText.pickle")
OUT_DIR = Path("./results")

BASE_SETS = {
    "base": (["log_at"], ["sic2_cat", "year_cat"]),
    "sic4": (["log_at"], ["sic4_cat", "year_cat"]),
    "lag+sic4": (["log_at", "y_lag"], ["sic4_cat", "year_cat"]),
}
DEMO_NUM, DEMO_CAT = ["ceo_age"], ["ceo_gender", "ceo_educ"]


def build_ceo_chars():
    """firm-year 内主 CEO 的特征；同一 firm-year 内各 component 取值一致，取第一个非缺失值。"""
    m = pd.read_parquet(COMP_MAP)
    df = pd.read_pickle(TEXT_PKL)
    c = df.loc[m["orig_idx"].values, ["gender", "age", "educ_level"]].reset_index(drop=True)
    del df
    c["panel_id"] = m["panel_id"].values
    chars = c.groupby("panel_id").first().rename(
        columns={"gender": "ceo_gender", "age": "ceo_age", "educ_level": "ceo_educ"}
    ).reset_index()
    chars.to_parquet(CEO_CHARS, index=False)
    return chars


def main():
    chars = pd.read_parquet(CEO_CHARS) if CEO_CHARS.exists() else build_ceo_chars()
    panel = pd.read_parquet(PANEL).merge(chars, on="panel_id", how="left", validate="1:1")
    topic_cols = [c for c in panel.columns if c.startswith("topic_")]
    sich = panel["sich"].astype("Int64")
    panel["sic2_cat"] = (sich // 100).astype(str)
    panel["sic4_cat"] = sich.astype(str)
    panel["year_cat"] = panel["year"].astype(str)

    rng = np.random.default_rng(SEED)
    rows, d_topics, d_demo = [], [], []
    for ratio, ycol, lagcol in TARGETS:
        d = panel[panel[ycol].notna() & panel[lagcol].notna()
                  & panel[["ceo_gender", "ceo_age", "ceo_educ"]].notna().all(axis=1)].copy()
        tr = d[d["fold"] != 0]
        lo, hi = tr[ycol].quantile([0.01, 0.99])
        d["y_lag"] = d[lagcol].clip(lo, hi)
        tr, te = d[d["fold"] != 0], d[d["fold"] == 0]
        y_tr, y_te = tr[ycol].clip(lo, hi).values, te[ycol].clip(lo, hi).values
        cv = PredefinedSplit(tr["fold"].values - 1)
        print(f"\n=== {ratio} (fill0, CEO 特征完整样本): train {len(tr):,}, test {len(te):,} ===")

        preds = {}
        for bs, (num_cols, cat_cols) in BASE_SETS.items():
            for with_demo in (False, True):
                cs = f"{bs}+ceo" if with_demo else bs
                nc = num_cols + DEMO_NUM if with_demo else num_cols
                cc = cat_cols + DEMO_CAT if with_demo else cat_cols
                for mname, (est, grid) in MODELS.items():
                    for with_topics in (False, True):
                        fs = "controls+topics" if with_topics else "controls"
                        prep = make_preprocessor(nc, cc, topic_cols if with_topics else [])
                        pipe = Pipeline([("prep", prep), ("model", est)])
                        t0 = time.time()
                        gs = GridSearchCV(pipe, {f"model__{k}": v for k, v in grid.items()}, cv=cv,
                                          scoring="r2", n_jobs=1 if mname == "XGBoost" else 8, refit=True)
                        gs.fit(tr, y_tr)
                        preds[(cs, mname, fs)] = gs.predict(te)
                        m = metrics(y_te, preds[(cs, mname, fs)])
                        rows.append({
                            "ratio": ratio, "controls": cs, "features": fs, "model": mname,
                            "n_train": len(tr), "n_test": len(te), "cv_r2": gs.best_score_,
                            **{f"test_{k}": v for k, v in m.items()},
                            "best_params": {k.replace("model__", ""): v for k, v in gs.best_params_.items()},
                            "secs": round(time.time() - t0, 1),
                        })
                        print(f"  {cs:<13} {fs:<16} {mname:<8} cv_r2={gs.best_score_:.3f}  "
                              f"test_r2={m['r2']:.3f}  rho={m['spearman']:.3f}  ({rows[-1]['secs']}s)")

        groups = te["split_group"].values

        def delta(a, b):
            boot = cluster_bootstrap(y_te, {"a": preds[a], "b": preds[b]}, groups, rng)
            dr = boot["b"] - boot["a"]
            return {
                "r2_from": r2_score(y_te, preds[a]), "r2_to": r2_score(y_te, preds[b]),
                "delta_r2": r2_score(y_te, preds[b]) - r2_score(y_te, preds[a]),
                "delta_ci_lo": np.percentile(dr, 2.5), "delta_ci_hi": np.percentile(dr, 97.5),
                "p_delta_le_0": (dr <= 0).mean(),
            }

        for bs in BASE_SETS:
            for mname in MODELS:
                # topics 的增量（给定 controls，含或不含 CEO 特征）
                for cs in (bs, f"{bs}+ceo"):
                    d_topics.append({"ratio": ratio, "controls": cs, "model": mname,
                                     **delta((cs, mname, "controls"), (cs, mname, "controls+topics"))})
                # CEO 特征的增量（给定是否含 topics）
                for fs in ("controls", "controls+topics"):
                    d_demo.append({"ratio": ratio, "controls": bs, "features": fs, "model": mname,
                                   **delta((bs, mname, fs), (f"{bs}+ceo", mname, fs))})

        pd.DataFrame(rows).to_csv(OUT_DIR / "ceo_demo_metrics.csv", index=False)
        pd.DataFrame(d_topics).to_csv(OUT_DIR / "ceo_demo_delta_r2.csv", index=False)
        pd.DataFrame(d_demo).to_csv(OUT_DIR / "ceo_demo_delta_demo.csv", index=False)

    print("\n=== topics 增量 ===")
    print(pd.DataFrame(d_topics).round(3).to_string(index=False))
    print("\n=== CEO 特征增量 ===")
    print(pd.DataFrame(d_demo).round(3).to_string(index=False))


if __name__ == "__main__":
    main()
