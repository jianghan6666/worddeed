"""第 3 步（可选）：小训练集稳健性。3 个随机种子 × (Ridge / XGBoost)，每次 20% 训练 / 20% 验证 / 60% 测试。

每个 seed：
  1. 在有 R&D 的 firm-year 上，用 StratifiedGroupKFold(5, shuffle, random_state=seed) 按公司–CEO 连通分量分组、
     按 has_rd 分层，切成 5 份：第 1 份训练（20%），第 2 份验证（20%），其余 3 份测试（60%）。
  2. 目标按训练集 1% / 99% winsorize（验证 / 测试用同一阈值）。
  3. 超参数网格中每个取值只在训练集上拟合，按验证集 R² 选最优，在测试集上评估。XGBoost 的 random_state = seed。
  4. 对照：第 2 步的交叉拟合分数（每个模型约 80% 训练）在同一测试集、同一 y 口径下的表现。

用法（包根目录）：python code/03_seed_robustness.py [--scores results/risk_scores.parquet] [--out rerun]
输出 <out>/results/seed_robustness_metrics.csv。耗时约 6 分钟。
"""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.model_selection import ParameterGrid

import step3_lib as L

SEEDS = [1, 2, 3]


def evaluate(y, yhat):
    return {"r2": r2_score(y, yhat), "mse": mean_squared_error(y, yhat), "corr": float(np.corrcoef(y, yhat)[0, 1])}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--inputs", default=str(L.DATA / "firm_year_inputs.parquet"))
    ap.add_argument("--scores", default=str(L.ROOT / "results" / "risk_scores.parquet"))
    ap.add_argument("--out", default=str(L.ROOT / "rerun"))
    args = ap.parse_args()
    out = Path(args.out) / "results"
    out.mkdir(parents=True, exist_ok=True)
    panel = pd.read_parquet(args.inputs)
    ref = pd.read_parquet(args.scores)[["panel_id", "risk_score_ridge", "risk_score_xgboost"]]
    data = panel[panel[L.TARGET].notna()].merge(ref, on="panel_id", validate="1:1")
    topic_cols = L.load_topic_selection(L.DATA / "topic_selection" / "b1-gpt-6-astra-P0-xhigh.json")

    rows = []
    for seed in SEEDS:
        d = L.assign_folds(data.drop(columns=["fold"]).copy(), n_folds=5, seed=seed)
        tr, va, te = d[d["fold"] == 0], d[d["fold"] == 1], d[d["fold"] >= 2]
        lo, hi = L.winsor_bounds(tr[L.TARGET])
        y = {k: s[L.TARGET].clip(lo, hi).values for k, s in (("train", tr), ("val", va), ("test", te))}
        for name in L.MODELS:
            best = None
            for params in ParameterGrid(L.grid_for(name)):
                pipe = L.make_pipe(name, topic_cols, seed=seed).set_params(**params).fit(tr, y["train"])
                v = r2_score(y["val"], pipe.predict(va))
                if best is None or v > best[0]:
                    best = (v, params, pipe)
            val_r2, params, pipe = best
            m = evaluate(y["test"], pipe.predict(te))
            r = evaluate(y["test"], te[f"risk_score_{name}"].values)
            rows.append({"seed": seed, "model": name, "n_train": len(tr), "n_val": len(va), "n_test": len(te),
                         "best_params": {k.split("__")[-1]: v for k, v in params.items()}, "val_r2": val_r2,
                         "train_r2": r2_score(y["train"], pipe.predict(tr)),
                         **{f"test_{k}": v for k, v in m.items()},
                         **{f"crossfit_same_test_{k}": v for k, v in r.items()}})
            print(f"seed {seed} {name}: {rows[-1]['best_params']} 验证 R² {val_r2:.3f} 测试 R² {m['r2']:.3f}"
                  f"（交叉拟合分数在同一测试集 {r['r2']:.3f}）")
    pd.DataFrame(rows).to_csv(out / "seed_robustness_metrics.csv", index=False)
    print(f"已写入 {out / 'seed_robustness_metrics.csv'}")


if __name__ == "__main__":
    main()
