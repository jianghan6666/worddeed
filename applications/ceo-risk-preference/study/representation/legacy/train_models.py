"""
Step 2: 用 topic + controls 预测 firm-year R&D ratio（回归）

目标 (4 组): {xrd/at, xrd/sale} x {fill0: xrd 缺失视为 0, nonmissing: 只用 xrd 非缺失样本}
特征 (3 组): controls (log_at + SIC2 + year) / topics / controls + topics
模型 (4 个): Ridge, XGBoost, MLP, RandomForest

- 调参: fold 1-4 做 PredefinedSplit CV（fold 已按 firm–CEO 连通分量分组）
- 测试: fold 0 holdout；R2 / RMSE / Spearman，按 split_group 做 cluster bootstrap 置信区间
- 目标变量按 train 的 1%/99% 分位 winsorize（test 用同一阈值）
- topics 做 CLR 变换后标准化（成分数据）

输出:
    results/metrics.csv        每个 target x sample x features x model 的 CV / test 指标
    results/delta_r2.csv       controls+topics 相对 controls 的 test R2 增量及 bootstrap CI
    results/predictions.parquet  test 集预测值
"""

import argparse
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.compose import ColumnTransformer, TransformedTargetRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.exceptions import ConvergenceWarning
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.model_selection import GridSearchCV, PredefinedSplit
from sklearn.neural_network import MLPRegressor
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.preprocessing import FunctionTransformer, OneHotEncoder, StandardScaler
from xgboost import XGBRegressor

warnings.filterwarnings("ignore", category=ConvergenceWarning)

PANEL = Path("./data/panel/ceo_firm_year_panel.parquet")
OUT_DIR = Path("./results")
SEED = 42
N_BOOT = 1000
N_JOBS = 16

TARGETS = [  # (ratio, sample, column)
    ("rd_at", "fill0", "rd_at_fill0"),
    ("rd_at", "nonmissing", "rd_at"),
    ("rd_sale", "fill0", "rd_sale_fill0"),
    ("rd_sale", "nonmissing", "rd_sale"),
]
NUM_CONTROLS = ["log_at"]
CAT_CONTROLS = ["sic2_cat", "year_cat"]


def clr(X, eps=1e-6):
    L = np.log(np.asarray(X, dtype=np.float64) + eps)
    return L - L.mean(axis=1, keepdims=True)


def make_preprocessor(feature_set, topic_cols):
    parts = []
    if feature_set in ("controls", "controls+topics"):
        parts.append(("num", make_pipeline(SimpleImputer(strategy="median"), StandardScaler()), NUM_CONTROLS))
        parts.append(("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CAT_CONTROLS))
    if feature_set in ("topics", "controls+topics"):
        parts.append(("topic", make_pipeline(FunctionTransformer(clr), StandardScaler()), topic_cols))
    return ColumnTransformer(parts)


def make_models():
    """(estimator, param_grid)；param 名相对于 pipeline 中的 'model' 步骤。"""
    return {
        "Ridge": (
            Ridge(),
            {"alpha": [1, 10, 100, 1000, 10000]},
        ),
        "XGBoost": (
            XGBRegressor(
                n_estimators=600, learning_rate=0.03, subsample=0.8, colsample_bytree=0.5,
                tree_method="hist", n_jobs=N_JOBS, random_state=SEED,
            ),
            {"max_depth": [3, 6], "min_child_weight": [1, 10]},
        ),
        "MLP": (
            # y 标准化后再训练，避免小尺度目标下 MLP 难以收敛
            TransformedTargetRegressor(
                regressor=MLPRegressor(
                    early_stopping=True, validation_fraction=0.1, max_iter=300,
                    batch_size=256, learning_rate_init=1e-3, random_state=SEED,
                ),
                transformer=StandardScaler(),
            ),
            {"regressor__hidden_layer_sizes": [(256,), (256, 64)], "regressor__alpha": [1e-3, 1e-1]},
        ),
        "RandomForest": (
            RandomForestRegressor(n_estimators=300, max_features=0.3, n_jobs=N_JOBS, random_state=SEED),
            {"min_samples_leaf": [5, 20]},
        ),
    }


def metrics(y, yhat):
    return {
        "r2": r2_score(y, yhat),
        "rmse": mean_squared_error(y, yhat, squared=False),
        "spearman": spearmanr(y, yhat).correlation,
    }


def cluster_bootstrap(y, preds, groups, rng):
    """按 split_group 重抽样；返回 {name: R2 样本数组}。"""
    uniq, inv = np.unique(groups, return_inverse=True)
    idx_by_g = np.split(np.argsort(inv), np.cumsum(np.bincount(inv))[:-1])
    out = {k: np.empty(N_BOOT) for k in preds}
    for b in range(N_BOOT):
        idx = np.concatenate([idx_by_g[g] for g in rng.integers(0, len(uniq), len(uniq))])
        for k, p in preds.items():
            out[k][b] = r2_score(y[idx], p[idx])
    return out


def main(models_to_run, targets_to_run):
    OUT_DIR.mkdir(exist_ok=True)
    panel = pd.read_parquet(PANEL)
    topic_cols = [c for c in panel.columns if c.startswith("topic_")]
    panel["sic2_cat"] = panel["sic2"].astype(str)  # 缺失 -> "<NA>" 作为单独类别
    panel["year_cat"] = panel["year"].astype(str)
    X_cols = NUM_CONTROLS + CAT_CONTROLS + topic_cols

    rng = np.random.default_rng(SEED)
    rows, deltas, pred_frames = [], [], []
    all_models = make_models()

    for ratio, sample, ycol in TARGETS:
        if f"{ratio}:{sample}" not in targets_to_run:
            continue
        d = panel[panel[ycol].notna()]
        tr, te = d[d["fold"] != 0], d[d["fold"] == 0]
        lo, hi = tr[ycol].quantile([0.01, 0.99])
        y_tr, y_te = tr[ycol].clip(lo, hi).values, te[ycol].clip(lo, hi).values
        cv = PredefinedSplit(tr["fold"].values - 1)
        print(f"\n=== {ratio} / {sample}: train {len(tr):,}, test {len(te):,}, winsor [{lo:.4f}, {hi:.4f}] ===")

        test_preds = {}
        for fs in ["controls", "topics", "controls+topics"]:
            for mname in models_to_run:
                est, grid = all_models[mname]
                pipe = Pipeline([("prep", make_preprocessor(fs, topic_cols)), ("model", est)])
                grid = {f"model__{k}": v for k, v in grid.items()}
                # 树模型内部已并行，CV 串行；线性/MLP 并行 CV
                n_jobs = 1 if mname in ("XGBoost", "RandomForest") else min(N_JOBS, 8)
                t0 = time.time()
                gs = GridSearchCV(pipe, grid, cv=cv, scoring="r2", n_jobs=n_jobs, refit=True)
                gs.fit(tr[X_cols], y_tr)
                yhat = gs.predict(te[X_cols])
                test_preds[(fs, mname)] = yhat
                m = metrics(y_te, yhat)
                rows.append({
                    "ratio": ratio, "sample": sample, "features": fs, "model": mname,
                    "n_train": len(tr), "n_test": len(te), "cv_r2": gs.best_score_,
                    **{f"test_{k}": v for k, v in m.items()},
                    "best_params": {k.replace("model__", ""): v for k, v in gs.best_params_.items()},
                    "secs": round(time.time() - t0, 1),
                })
                print(f"  {fs:<16} {mname:<13} cv_r2={gs.best_score_:.3f}  test_r2={m['r2']:.3f}  "
                      f"rho={m['spearman']:.3f}  ({rows[-1]['secs']}s)")
                pred_frames.append(pd.DataFrame({
                    "panel_id": te["panel_id"].values, "ratio": ratio, "sample": sample,
                    "features": fs, "model": mname, "y": y_te, "yhat": yhat,
                }))

        # 每个模型：controls+topics 相对 controls 的 R2 增量，cluster bootstrap CI
        for mname in models_to_run:
            pc, pb = test_preds[("controls", mname)], test_preds[("controls+topics", mname)]
            boot = cluster_bootstrap(y_te, {"c": pc, "b": pb}, te["split_group"].values, rng)
            dr = boot["b"] - boot["c"]
            deltas.append({
                "ratio": ratio, "sample": sample, "model": mname,
                "r2_controls": r2_score(y_te, pc), "r2_controls_topics": r2_score(y_te, pb),
                "delta_r2": r2_score(y_te, pb) - r2_score(y_te, pc),
                "delta_ci_lo": np.percentile(dr, 2.5), "delta_ci_hi": np.percentile(dr, 97.5),
                "p_delta_le_0": (dr <= 0).mean(),
            })

        # 每个 target 跑完就落盘，中断时不丢结果
        pd.DataFrame(rows).to_csv(OUT_DIR / "metrics.csv", index=False)
        pd.DataFrame(deltas).to_csv(OUT_DIR / "delta_r2.csv", index=False)
        pd.concat(pred_frames).to_parquet(OUT_DIR / "predictions.parquet", index=False)

    print("\n=== test R2 ===")
    res = pd.DataFrame(rows)
    print(res.pivot_table(index=["ratio", "sample", "model"], columns="features", values="test_r2")
          [["controls", "topics", "controls+topics"]].round(3).to_string())
    print("\n=== Delta R2 (controls+topics - controls) ===")
    print(pd.DataFrame(deltas).round(3).to_string(index=False))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", nargs="+", default=["Ridge", "XGBoost", "MLP", "RandomForest"])
    ap.add_argument("--targets", nargs="+", default=[f"{r}:{s}" for r, s, _ in TARGETS])
    args = ap.parse_args()
    main(args.models, args.targets)
