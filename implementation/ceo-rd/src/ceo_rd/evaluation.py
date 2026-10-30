"""评估指标与按组 cluster bootstrap 的 R² 增量置信区间。"""

import numpy as np
from scipy.stats import spearmanr
from sklearn.metrics import mean_squared_error, r2_score


def metrics(y, yhat):
    return {
        "r2": r2_score(y, yhat),
        "rmse": float(np.sqrt(mean_squared_error(y, yhat))),
        "spearman": spearmanr(y, yhat).correlation,
    }


def cluster_bootstrap_r2(y, preds, groups, rng, n_boot=1000):
    """按组（split_group）有放回重抽样，返回 {name: R² 的 bootstrap 样本}。各模型共用同一组重抽样。"""
    uniq, inv = np.unique(groups, return_inverse=True)
    idx_by_g = np.split(np.argsort(inv), np.cumsum(np.bincount(inv))[:-1])
    out = {k: np.empty(n_boot) for k in preds}
    for b in range(n_boot):
        idx = np.concatenate([idx_by_g[g] for g in rng.integers(0, len(uniq), len(uniq))])
        for k, p in preds.items():
            out[k][b] = r2_score(y[idx], p[idx])
    return out


def compare(y, pred_from, pred_to, groups, rng, n_boot=1000):
    """pred_to 相对 pred_from 的测试集 R² 增量，附 95% 置信区间与 RMSE。"""
    boot = cluster_bootstrap_r2(y, {"a": pred_from, "b": pred_to}, groups, rng, n_boot)
    dr = boot["b"] - boot["a"]
    m_from, m_to = metrics(y, pred_from), metrics(y, pred_to)
    return {
        "r2_from": m_from["r2"], "r2_to": m_to["r2"], "delta_r2": m_to["r2"] - m_from["r2"],
        "ci_lo": np.percentile(dr, 2.5), "ci_hi": np.percentile(dr, 97.5), "p_delta_le_0": (dr <= 0).mean(),
        "rmse_from": m_from["rmse"], "rmse_to": m_to["rmse"],
    }
