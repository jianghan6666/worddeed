"""第 4 步：校验交付内容。

默认检查（约 1 分钟，不训练模型）：
  A. MANIFEST.json 中全部文件的大小与 SHA-256；
  B. 用 models/ 中的 5 个 fold 模型重新给各自的 fold 打分，与 results/risk_scores.parquet 的交叉拟合分数比较；
     用全样本模型重新打分，与 _full 分数比较；
  C. 可移植 JSON 格式的预测与 joblib 模型一致；
  D. 4 个版本（_clip0 / _pct / _z）可由原始分数重算。
若存在 rerun/ 中的重跑结果（第 1–3 步的默认输出），另外比较：
  E. rerun/firm_year_inputs.parquet 与 data/firm_year_inputs.parquet 逐值一致；
  F. rerun/results/risk_scores.parquet 与 results/risk_scores.parquet；
  G. rerun/results/seed_robustness_metrics.csv 与 results/seed_robustness_metrics.csv。

用法（包根目录）：python code/04_verify.py
"""

import hashlib
import json
import sys

import joblib
import numpy as np
import pandas as pd

import step3_lib as L

TOL = 1e-9  # 分数比较的最大绝对误差
results = []


def check(name, ok, detail=""):
    results.append((name, bool(ok)))
    print(f"[{'通过' if ok else '失败'}] {name}{('：' + detail) if detail else ''}")


def max_diff(a, b):
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    if a.shape != b.shape or not np.array_equal(np.isnan(a), np.isnan(b)):
        return np.inf
    m = ~np.isnan(a)
    return float(np.max(np.abs(a[m] - b[m]))) if m.any() else 0.0


def main():
    root = L.ROOT
    man = json.loads((root / "MANIFEST.json").read_text(encoding="utf-8"))
    bad = [f["path"] for f in man["files"]
           if not (root / f["path"]).exists() or (root / f["path"]).stat().st_size != f["bytes"]
           or hashlib.sha256((root / f["path"]).read_bytes()).hexdigest() != f["sha256"]]
    check("A. MANIFEST 文件大小与 SHA-256", not bad, f"{len(man['files'])} 个文件" + (f"，不一致：{bad[:5]}" if bad else ""))

    panel = pd.read_parquet(root / "data" / "firm_year_inputs.parquet")
    scores = pd.read_parquet(root / "results" / "risk_scores.parquet")
    if not np.array_equal(panel["panel_id"].values, scores["panel_id"].values):
        check("分数与输入表行顺序一致", False)
        sys.exit(1)
    for name in L.MODELS:
        oof = np.full(len(panel), np.nan)
        port = np.full(len(panel), np.nan)
        for k in range(5):
            b = joblib.load(root / "models" / name / f"fold_{k}.joblib")
            held = (panel["fold"] == k).values
            oof[held] = b["pipeline"].predict(panel[held])
            port[held] = L.predict_portable(root / "models" / name / f"fold_{k}.json", panel[held])
        d = max_diff(oof, scores[f"risk_score_{name}"])
        check(f"B. {name}：5 个 fold 模型重现交叉拟合分数", d <= TOL, f"最大差 {d:.2e}")
        full = joblib.load(root / "models" / name / "full.joblib")["pipeline"].predict(panel)
        d = max_diff(full, scores[f"risk_score_{name}_full"])
        check(f"B. {name}：全样本模型重现 _full 分数", d <= TOL, f"最大差 {d:.2e}")
        tol_port = 1e-9 if name == "ridge" else 1e-5  # XGBoost booster 以 float32 计算
        d = max_diff(port, oof)
        check(f"C. {name}：可移植 JSON 与 joblib 一致（fold 模型）", d <= tol_port, f"最大差 {d:.2e}")
        d = max_diff(L.predict_portable(root / "models" / name / "full.json", panel), full)
        check(f"C. {name}：可移植 JSON 与 joblib 一致（全样本模型）", d <= tol_port, f"最大差 {d:.2e}")
        for f in ("", "_full"):
            c = f"risk_score_{name}{f}"
            t = L.add_versions(scores[[c]].copy(), c)
            d = max(max_diff(t[c + v], scores[c + v]) for v in ("_clip0", "_pct", "_z"))
            check(f"D. {c} 的 3 个转换版本可重算", d <= 1e-12, f"最大差 {d:.2e}")

    rerun = root / "rerun"
    if (rerun / "firm_year_inputs.parquet").exists():
        a = pd.read_parquet(rerun / "firm_year_inputs.parquet")
        ok = list(a.columns) == list(panel.columns) and all(
            a[c].equals(panel[c]) or max_diff(a[c], panel[c]) == 0 for c in panel.columns
            if pd.api.types.is_numeric_dtype(panel[c])) and all(
            a[c].equals(panel[c]) for c in panel.columns if not pd.api.types.is_numeric_dtype(panel[c]))
        check("E. 重建的 firm-year 输入表与交付版逐值一致", ok)
    if (rerun / "results" / "risk_scores.parquet").exists():
        a = pd.read_parquet(rerun / "results" / "risk_scores.parquet")
        cols = [c for c in scores.columns if c.startswith("risk_score_") and c in a.columns]
        d = max(max_diff(a[c], scores[c]) for c in cols)
        check("F. 重跑的分数与交付版一致", d <= TOL and len(cols) > 0, f"{len(cols)} 列，最大差 {d:.2e}")
    if (rerun / "results" / "seed_robustness_metrics.csv").exists():
        a = pd.read_csv(rerun / "results" / "seed_robustness_metrics.csv")
        b = pd.read_csv(root / "results" / "seed_robustness_metrics.csv")
        num = [c for c in b.columns if pd.api.types.is_float_dtype(b[c])]
        d = max(max_diff(a[c], b[c]) for c in num)
        check("G. 重跑的稳健性指标与交付版一致", d <= 1e-9, f"最大差 {d:.2e}")

    n_fail = sum(not ok for _, ok in results)
    print(f"\n共 {len(results)} 项检查，失败 {n_fail} 项")
    sys.exit(1 if n_fail else 0)


if __name__ == "__main__":
    main()
