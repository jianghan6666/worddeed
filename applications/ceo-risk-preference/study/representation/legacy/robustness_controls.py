"""
稳健性检验: 更严格的 controls 下 topics 是否仍有增量

control 组合:
    base        log_at + SIC2 + year           （与 train_models.py 相同）
    sic3        log_at + SIC3 + year
    sic4        log_at + SIC4 + year
    lag         log_at + SIC2 + year + 上一年 R&D ratio
    lag+sic4    log_at + SIC4 + year + 上一年 R&D ratio（最严格）
每个组合比较 controls vs controls+topics，模型 Ridge / XGBoost（缩小网格），目标为 fill0 口径的 xrd/at 与 xrd/sale。
样本限定为滞后 ratio 非缺失的 firm-year，各组合在同一样本上比较。

输出: results/robustness_metrics.csv, results/robustness_delta_r2.csv
"""

import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.metrics import r2_score
from sklearn.model_selection import GridSearchCV, PredefinedSplit
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.preprocessing import FunctionTransformer, OneHotEncoder, StandardScaler
from xgboost import XGBRegressor

from train_models import N_JOBS, SEED, clr, cluster_bootstrap, metrics

PANEL = Path("./data/panel/ceo_firm_year_panel.parquet")
OUT_DIR = Path("./results")

TARGETS = [("rd_at", "rd_at_fill0", "rd_at_lag"), ("rd_sale", "rd_sale_fill0", "rd_sale_lag")]
CONTROL_SETS = {
    "base": (["log_at"], ["sic2_cat", "year_cat"]),
    "sic3": (["log_at"], ["sic3_cat", "year_cat"]),
    "sic4": (["log_at"], ["sic4_cat", "year_cat"]),
    "lag": (["log_at", "y_lag"], ["sic2_cat", "year_cat"]),
    "lag+sic4": (["log_at", "y_lag"], ["sic4_cat", "year_cat"]),
}
MODELS = {
    "Ridge": (Ridge(), {"alpha": [1, 10, 100, 1000, 10000]}),
    "XGBoost": (
        XGBRegressor(
            n_estimators=600, learning_rate=0.03, subsample=0.8, colsample_bytree=0.5,
            min_child_weight=10, tree_method="hist", n_jobs=N_JOBS, random_state=SEED,
        ),
        {"max_depth": [3, 6]},
    ),
}


def make_preprocessor(num_cols, cat_cols, topic_cols):
    parts = [
        ("num", make_pipeline(SimpleImputer(strategy="median"), StandardScaler()), num_cols),
        ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), cat_cols),
    ]
    if topic_cols:
        parts.append(("topic", make_pipeline(FunctionTransformer(clr), StandardScaler()), topic_cols))
    return ColumnTransformer(parts)


def main():
    panel = pd.read_parquet(PANEL)
    topic_cols = [c for c in panel.columns if c.startswith("topic_")]
    sich = panel["sich"].astype("Int64")
    for k, div in [("sic2", 100), ("sic3", 10), ("sic4", 1)]:
        panel[f"{k}_cat"] = (sich // div).astype(str)  # 缺失 -> "<NA>" 作为单独类别
    panel["year_cat"] = panel["year"].astype(str)

    rng = np.random.default_rng(SEED)
    rows, deltas = [], []
    for ratio, ycol, lagcol in TARGETS:
        d = panel[panel[ycol].notna() & panel[lagcol].notna()].copy()
        tr, te = d[d["fold"] != 0], d[d["fold"] == 0]
        lo, hi = tr[ycol].quantile([0.01, 0.99])
        # 滞后 ratio 用与目标相同的 winsorize 阈值
        d["y_lag"] = d[lagcol].clip(lo, hi)
        tr, te = d[d["fold"] != 0], d[d["fold"] == 0]
        y_tr, y_te = tr[ycol].clip(lo, hi).values, te[ycol].clip(lo, hi).values
        cv = PredefinedSplit(tr["fold"].values - 1)
        print(f"\n=== {ratio} (fill0): train {len(tr):,}, test {len(te):,}, "
              f"corr(y, y_lag) = {np.corrcoef(y_tr, tr['y_lag'])[0, 1]:.3f} ===")

        for cs, (num_cols, cat_cols) in CONTROL_SETS.items():
            for mname, (est, grid) in MODELS.items():
                preds = {}
                for with_topics in (False, True):
                    fs = "controls+topics" if with_topics else "controls"
                    prep = make_preprocessor(num_cols, cat_cols, topic_cols if with_topics else [])
                    pipe = Pipeline([("prep", prep), ("model", est)])
                    n_jobs = 1 if mname == "XGBoost" else 8
                    t0 = time.time()
                    gs = GridSearchCV(pipe, {f"model__{k}": v for k, v in grid.items()},
                                      cv=cv, scoring="r2", n_jobs=n_jobs, refit=True)
                    gs.fit(tr, y_tr)
                    preds[fs] = gs.predict(te)
                    m = metrics(y_te, preds[fs])
                    rows.append({
                        "ratio": ratio, "controls": cs, "features": fs, "model": mname,
                        "n_train": len(tr), "n_test": len(te), "cv_r2": gs.best_score_,
                        **{f"test_{k}": v for k, v in m.items()},
                        "best_params": {k.replace("model__", ""): v for k, v in gs.best_params_.items()},
                        "secs": round(time.time() - t0, 1),
                    })
                    print(f"  {cs:<9} {fs:<16} {mname:<8} cv_r2={gs.best_score_:.3f}  "
                          f"test_r2={m['r2']:.3f}  rho={m['spearman']:.3f}  ({rows[-1]['secs']}s)")

                boot = cluster_bootstrap(y_te, {"c": preds["controls"], "b": preds["controls+topics"]},
                                         te["split_group"].values, rng)
                dr = boot["b"] - boot["c"]
                deltas.append({
                    "ratio": ratio, "controls": cs, "model": mname,
                    "r2_controls": r2_score(y_te, preds["controls"]),
                    "r2_controls_topics": r2_score(y_te, preds["controls+topics"]),
                    "delta_r2": r2_score(y_te, preds["controls+topics"]) - r2_score(y_te, preds["controls"]),
                    "delta_ci_lo": np.percentile(dr, 2.5), "delta_ci_hi": np.percentile(dr, 97.5),
                    "p_delta_le_0": (dr <= 0).mean(),
                })
                pd.DataFrame(rows).to_csv(OUT_DIR / "robustness_metrics.csv", index=False)
                pd.DataFrame(deltas).to_csv(OUT_DIR / "robustness_delta_r2.csv", index=False)

    print("\n=== Delta R2 (controls+topics - controls) ===")
    print(pd.DataFrame(deltas).round(3).to_string(index=False))


if __name__ == "__main__":
    main()
