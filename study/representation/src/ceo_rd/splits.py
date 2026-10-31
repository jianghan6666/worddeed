"""训练 / 测试划分：按 firm–CEO 连通分量分组的 StratifiedGroupKFold。"""

import numpy as np
import pandas as pd
from scipy import sparse
from scipy.sparse.csgraph import connected_components
from sklearn.model_selection import StratifiedGroupKFold


def assign_folds(panel, n_folds=5, seed=42, stratify="has_rd"):
    """添加 split_group 与 fold 列。

    同一公司的所有年份在同一组；同一 CEO 任职过的多家公司也合并为一组（firm–CEO 二部图的连通分量），
    保证测试集公司与 CEO 都未在训练集出现。
    """
    firms = pd.factorize(panel["gvkey"])[0]
    ceos = pd.factorize(panel["ceo_id"])[0] + firms.max() + 1
    n = ceos.max() + 1
    adj = sparse.coo_matrix((np.ones(len(panel)), (firms, ceos)), shape=(n, n))
    _, labels = connected_components(adj, directed=False)
    panel["split_group"] = labels[firms]
    panel["fold"] = -1
    sgkf = StratifiedGroupKFold(n_splits=n_folds, shuffle=True, random_state=seed)
    for k, (_, idx) in enumerate(sgkf.split(panel, panel[stratify], groups=panel["split_group"])):
        panel.iloc[idx, panel.columns.get_loc("fold")] = k
    return panel
