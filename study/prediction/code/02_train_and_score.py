"""第 2 步：训练 Ridge / XGBoost，交叉拟合打分，并保存模型。

输入：firm-year 输入表（默认 data/firm_year_inputs.parquet）、data/topic_selection/b1-gpt-6-astra-P0-xhigh.json
输出（默认写到 rerun/，不覆盖包内交付的结果；--out . 则写入包根目录的 models/ 与 results/）：
  results/risk_scores.parquet / .csv   每个 firm-year 的分数（交叉拟合 + 全样本，各 4 个版本）
  results/metrics.json                 每个 fold 的超参数与 CV R²、交叉拟合与样本内指标
  models/<模型>/fold_<k>.joblib        5 个交叉拟合模型（模型 k 用 fold ≠ k 训练，只给 fold k 打分）
  models/<模型>/full.joblib            全样本模型（用于对新数据推断）
  models/<模型>/*.json                 可移植格式（预处理参数 + Ridge 系数 / XGBoost booster）

用法（包根目录）：python code/02_train_and_score.py [--models ridge xgboost] [--inputs PATH] [--out rerun]
耗时：Ridge 约 0.5 分钟，XGBoost 约 9 分钟（16 线程）。
"""

import argparse
import json
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import mean_squared_error, r2_score

import step3_lib as L

SELECTION = L.DATA / "topic_selection" / "b1-gpt-6-astra-P0-xhigh.json"
KEYS = ["panel_id", "gvkey", "ceo_id", "year", "fold"]


def train_one(name, panel, labeled, topic_cols, mdir):
    """交叉拟合 + 全样本模型；返回 (交叉拟合分数, 全样本分数, 指标)。"""
    t0 = time.time()
    mdir.mkdir(parents=True, exist_ok=True)
    oof = pd.Series(np.nan, index=panel.index)
    folds = {}
    for k in sorted(panel["fold"].unique()):
        train = panel[(panel["fold"] != k) & labeled]
        gs, (lo, hi) = L.fit_grouped_cv(name, train, topic_cols)
        held = panel["fold"] == k
        oof[held] = gs.predict(panel[held])
        info = {"train_folds": sorted(int(f) for f in train["fold"].unique()), "n_train": len(train),
                "scores_fold": int(k), "n_scored": int(held.sum()), "best_params": L.best_params(gs),
                "inner_cv_r2": float(gs.best_score_), "winsor": [lo, hi]}
        folds[int(k)] = info
        joblib.dump({"pipeline": gs.best_estimator_, "topic_cols": topic_cols, **info}, mdir / f"fold_{k}.joblib")
        L.export_portable(gs.best_estimator_, mdir / f"fold_{k}")
        print(f"{name} fold {k}：train {len(train):,}，{info['best_params']}，cv R² {gs.best_score_:.3f}")
    gs, (lo, hi) = L.fit_grouped_cv(name, panel[labeled], topic_cols)
    joblib.dump({"pipeline": gs.best_estimator_, "topic_cols": topic_cols, "n_train": int(labeled.sum()),
                 "best_params": L.best_params(gs), "inner_cv_r2": float(gs.best_score_), "winsor": [lo, hi]},
                mdir / "full.joblib")
    L.export_portable(gs.best_estimator_, mdir / "full")
    full = pd.Series(gs.predict(panel), index=panel.index)
    y = panel.loc[labeled, L.TARGET].clip(lo, hi)
    m = {"crossfit": {"r2": r2_score(y, oof[labeled]), "mse": mean_squared_error(y, oof[labeled]),
                      "corr": float(np.corrcoef(y, oof[labeled])[0, 1])},
         "full_insample_r2": r2_score(y, full[labeled]), "full_best_params": L.best_params(gs),
         "full_inner_cv_r2": float(gs.best_score_), "full_winsor": [lo, hi], "folds": folds,
         "secs": round(time.time() - t0)}
    print(f"{name}：交叉拟合 R² {m['crossfit']['r2']:.4f}（corr {m['crossfit']['corr']:.4f}）；"
          f"全样本模型样本内 R² {m['full_insample_r2']:.4f}；{m['secs']}s")
    return oof, full, m


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", nargs="+", default=list(L.MODELS), choices=list(L.MODELS))
    ap.add_argument("--inputs", default=str(L.DATA / "firm_year_inputs.parquet"))
    ap.add_argument("--out", default=str(L.ROOT / "rerun"))
    args = ap.parse_args()
    out = Path(args.out)
    (out / "results").mkdir(parents=True, exist_ok=True)

    panel = pd.read_parquet(args.inputs)
    topic_cols = L.load_topic_selection(SELECTION)
    labeled = panel[L.TARGET].notna()
    print(f"firm-year {len(panel):,}；有 R&D {labeled.sum():,}；特征：情绪 + {len(topic_cols)} 个 topic")

    scores = panel[KEYS].copy()
    metrics = {"target": L.TARGET, "n_firm_years": len(panel), "n_labeled": int(labeled.sum()),
               "n_topics": len(topic_cols), "selection": SELECTION.name, "models": {}}
    for name in args.models:
        oof, full, m = train_one(name, panel, labeled, topic_cols, out / "models" / name)
        scores[f"risk_score_{name}"] = oof.values
        scores[f"risk_score_{name}_full"] = full.values
        metrics["models"][name] = m

    for c in [c for c in scores.columns if c.startswith("risk_score_")]:
        L.add_versions(scores, c)
    order = KEYS + [f"risk_score_{m}{f}{v}" for m in args.models for f in ("", "_full") for v in L.TRANSFORMS]
    scores = scores[order]
    scores.to_parquet(out / "results" / "risk_scores.parquet", index=False)
    scores.to_csv(out / "results" / "risk_scores.csv", index=False)
    metrics["versions"] = {f"risk_score_<模型>{v}": d for v, d in L.TRANSFORMS.items()}
    (out / "results" / "metrics.json").write_text(json.dumps(metrics, indent=2, ensure_ascii=False, default=str),
                                                  encoding="utf-8")
    print(f"已写入 {out / 'results'} 与 {out / 'models'}")


if __name__ == "__main__":
    main()
