"""Step 3 共用函数：数据读取、firm-year 输入表构建、特征预处理、模型、分组划分与交叉拟合。

只依赖 numpy / pandas / scipy / scikit-learn / xgboost / joblib。保存的 joblib 模型引用本模块中的 `clr`，
加载模型前须能 import step3_lib（把 code/ 目录加入 sys.path 即可，见 README）。
"""

import json
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import sparse
from scipy.sparse.csgraph import connected_components
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.model_selection import GridSearchCV, PredefinedSplit, StratifiedGroupKFold
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.preprocessing import FunctionTransformer, StandardScaler
from xgboost import XGBRegressor

ROOT = Path(__file__).resolve().parent.parent  # 包根目录
DATA = ROOT / "data"

TARGET = "rd_at_fill0"
SENTIMENT = "sent_transformer"
TOPIC_PREFIX = "topic_"
N_TOPICS = 354
SPLIT_SEED = 42  # 5 个分组 fold 的随机种子
MODEL_SEED = 42  # XGBoost 的 random_state
N_JOBS = 16

# 模型定义：固定参数 + 调参网格（与原项目完全一致）
MODELS = {
    "ridge": {"params": {}, "grid": {"alpha": [1, 10, 100, 1000, 10000]}},
    "xgboost": {"params": {"n_estimators": 600, "learning_rate": 0.03, "subsample": 0.8,
                           "colsample_bytree": 0.5, "min_child_weight": 10},
                "grid": {"max_depth": [3, 6]}},
}


# ---------------------------------------------------------------------------
# 读取数据
# ---------------------------------------------------------------------------

def read_topic_chunks(path, key="topic_distr", chunk_rows=200_000):
    """逐块读取 npz 中的 topic 矩阵（float64，约 1.78M × 354），产出 (起始行号, 块)，避免一次载入约 5GB。"""
    with zipfile.ZipFile(path) as zf:
        fh = zf.open(f"{key}.npy")
        version = np.lib.format.read_magic(fh)
        read_header = np.lib.format.read_array_header_1_0 if version == (1, 0) else np.lib.format.read_array_header_2_0
        (n_rows, n_cols), fortran, dtype = read_header(fh)
        if fortran:
            raise ValueError("topic 矩阵须为 C 顺序")
        with fh:
            for start in range(0, n_rows, chunk_rows):
                stop = min(start + chunk_rows, n_rows)
                buf = fh.read((stop - start) * n_cols * dtype.itemsize)
                yield start, np.frombuffer(buf, dtype=dtype).reshape(stop - start, n_cols)


def load_compustat(path):
    """Compustat：(tic, fyear) 与 (gvkey, fyear) 去重（极少数重复保留最新 datadate），附上一财年 at / sale / xrd。"""
    f = pd.read_csv(path)
    f = f[["tic", "gvkey", "fyear", "datadate", "at", "sale", "xrd", "sich"]].sort_values(["gvkey", "fyear", "datadate"])
    f = f.drop_duplicates(["tic", "fyear"], keep="last").drop_duplicates(["gvkey", "fyear"], keep="last")
    lag = f[["gvkey", "fyear", "at", "sale", "xrd"]].copy()
    lag["fyear"] += 1
    return f.merge(lag, on=["gvkey", "fyear"], how="left", suffixes=("", "_lag"))


def load_topic_selection(path):
    """Step 2 的 selected_topics.json（final.relevant）-> topic 列名列表（按编号排序）。"""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    ids = data["final"]["relevant"] if isinstance(data, dict) else data
    return [f"{TOPIC_PREFIX}{i:03d}" for i in sorted({int(i) for i in ids})]


# ---------------------------------------------------------------------------
# component -> firm-year 输入表
# ---------------------------------------------------------------------------

def assign_folds(panel, n_folds=5, seed=SPLIT_SEED, stratify="has_rd"):
    """按 firm–CEO 二部图连通分量分组（同一公司全部年份、共享 CEO 的公司在同一组），StratifiedGroupKFold 划分。"""
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


def build_inputs(components_path, topics_path, compustat_path, chunk_rows=200_000, log=print):
    """由 component 级数据构建 firm-year 输入表（与原项目 ceo-rd build-panel 的相应列逐值一致）。

    1. 按 ticker（symbolvalue）+ 讲话自然年匹配 Compustat 的 tic + fyear；
    2. 每个 firm-year 只保留发言词数最多的 CEO；
    3. topic：按 retained_word_count 加权平均（topic 全为 0 的发言不参与），float32；
    4. 情绪：sentiment_transformer 按词数加权平均（含 topic 全为 0 的发言）；
    5. 目标 rd_at_fill0 = xrd（缺失视为 0）/ at（at ≤ 0 或缺失时为 NaN）；
    6. 5 个分组 fold。
    """
    comp = pd.read_parquet(components_path)
    n_total = len(comp)
    if not np.array_equal(comp["row"].values, np.arange(n_total)):
        raise ValueError("components 的 row 列须为 0..N-1，与 topic 矩阵逐行对齐")
    comp["ceo_id"] = np.where(comp["directorid"].notna(),
                              "bx_" + comp["directorid"].astype("Int64").astype(str),
                              "tp_" + comp["transcriptpersonid"].astype("Int64").astype(str))
    log(f"1/6 components: {n_total:,}")

    firm = load_compustat(compustat_path)
    comp = comp.merge(firm.rename(columns={"tic": "symbolvalue"}), left_on=["symbolvalue", "year"],
                      right_on=["symbolvalue", "fyear"], how="inner", validate="m:1")
    log(f"2/6 匹配上 Compustat: {len(comp):,}")

    words = comp.groupby(["gvkey", "year", "ceo_id"])["retained_word_count"].sum()
    main_ceo = words.groupby(level=[0, 1]).idxmax().apply(lambda t: t[2]).rename("main_ceo")
    comp = comp.merge(main_ceo, left_on=["gvkey", "year"], right_index=True)
    comp = comp[comp["ceo_id"] == comp["main_ceo"]].drop(columns="main_ceo")
    log(f"3/6 主 CEO 的 components: {len(comp):,}")

    panel = comp.groupby(["gvkey", "year"]).agg(ceo_id=("ceo_id", "first"), tic=("symbolvalue", "first"),
                                                n_components=("row", "size")).reset_index()
    panel = panel.merge(firm.drop(columns="tic").rename(columns={"fyear": "year"})[
        ["gvkey", "year", "at", "sale", "xrd", "sich"]], on=["gvkey", "year"], how="left", validate="1:1")
    panel["panel_id"] = np.arange(len(panel))
    comp = comp.merge(panel[["gvkey", "year", "panel_id"]], on=["gvkey", "year"])

    # topic：Σ w d / Σ w（只含 topic 非全 0 的 component）
    order = np.argsort(comp["row"].values)
    rows, gids = comp["row"].values[order], comp["panel_id"].values[order]
    w = comp["retained_word_count"].values[order].astype(np.float64)
    n_groups = len(panel)
    sums, tot_w, n_zero = None, np.zeros(n_groups), 0
    for start, X in read_topic_chunks(topics_path, chunk_rows=chunk_rows):
        if sums is None:
            if start == 0 and X.shape[1] != N_TOPICS:
                raise ValueError(f"topic 矩阵应有 {N_TOPICS} 列")
            sums = np.zeros((n_groups, X.shape[1]))
        lo, hi = np.searchsorted(rows, [start, start + len(X)])
        if hi == lo:
            continue
        local = rows[lo:hi] - start
        wk = np.where(X[local].sum(axis=1) > 1e-9, w[lo:hi], 0.0)
        n_zero += int((wk == 0).sum())
        sums += sparse.csr_matrix((wk, (gids[lo:hi], local)), shape=(n_groups, len(X))) @ X
        tot_w += np.bincount(gids[lo:hi], weights=wk, minlength=n_groups)
    with np.errstate(invalid="ignore"):
        pooled = (sums / tot_w[:, None]).astype(np.float32)
    topic_cols = [f"{TOPIC_PREFIX}{i:03d}" for i in range(pooled.shape[1])]
    log(f"4/6 topic 加权平均：排除 topic 全 0 的 components {n_zero:,}")

    ws = comp["retained_word_count"].where(comp["sentiment_transformer"].notna())
    sent = (comp["sentiment_transformer"] * ws).groupby(comp["panel_id"]).sum() / ws.groupby(comp["panel_id"]).sum()
    panel[SENTIMENT] = panel["panel_id"].map(sent)
    log("5/6 情绪加权平均")

    xrd0 = panel["xrd"].fillna(0.0)
    panel["has_rd"] = (xrd0 > 0).astype(int)
    panel["rd_missing"] = panel["xrd"].isna().astype(int)
    panel[TARGET] = np.where(panel["at"] > 0, xrd0 / panel["at"], np.nan)
    panel = assign_folds(panel)
    log(f"6/6 目标变量与 5 个分组 fold；firm-year {len(panel):,}，R&D 非缺失 {panel[TARGET].notna().sum():,}")

    cols = ["panel_id", "gvkey", "ceo_id", "year", "tic", "sich", "fold", "split_group", "n_components",
            "at", "sale", "xrd", "has_rd", "rd_missing", TARGET, SENTIMENT]
    return pd.concat([panel[cols], pd.DataFrame(pooled, columns=topic_cols)], axis=1)


# ---------------------------------------------------------------------------
# 特征与模型
# ---------------------------------------------------------------------------

def clr(X, eps=1e-6):
    """centered log-ratio：log(x + eps) 减去该行在所选 topic 上的均值。"""
    L = np.log(np.asarray(X, dtype=np.float64) + eps)
    return L - L.mean(axis=1, keepdims=True)


def make_preprocessor(topic_cols):
    """情绪：中位数填补 + 标准化；所选 topic：CLR（在所选子集内部）+ 标准化。"""
    return ColumnTransformer([
        ("num", make_pipeline(SimpleImputer(strategy="median"), StandardScaler()), [SENTIMENT]),
        ("topics:astra", make_pipeline(FunctionTransformer(clr), StandardScaler()), list(topic_cols)),
    ])


def make_estimator(name, seed=MODEL_SEED, n_jobs=N_JOBS, **extra):
    params = {**MODELS[name]["params"], **extra}
    if name == "ridge":
        return Ridge(**params)
    return XGBRegressor(tree_method="hist", n_jobs=n_jobs, random_state=seed, **params)


def make_pipe(name, topic_cols, seed=MODEL_SEED, n_jobs=N_JOBS):
    return Pipeline([("prep", make_preprocessor(topic_cols)), ("model", make_estimator(name, seed, n_jobs))])


def grid_for(name):
    return {f"model__{k}": v for k, v in MODELS[name]["grid"].items()}


def winsor_bounds(y):
    lo, hi = pd.Series(y).quantile([0.01, 0.99])
    return float(lo), float(hi)


def fit_grouped_cv(name, df, topic_cols, seed=MODEL_SEED, n_jobs=N_JOBS):
    """在 df 上按其 fold 列做分组交叉验证选超参数（R²），再用 df 全部行重新拟合。

    目标按 df 的 1% / 99% 分位 winsorize。返回 (GridSearchCV, (lo, hi))。
    """
    lo, hi = winsor_bounds(df[TARGET])
    y = df[TARGET].clip(lo, hi).values
    gs = GridSearchCV(make_pipe(name, topic_cols, seed, n_jobs), grid_for(name),
                      cv=PredefinedSplit(pd.factorize(df["fold"])[0]), scoring="r2",
                      n_jobs=(min(n_jobs, 8) if name == "ridge" else 1), refit=True)
    gs.fit(df, y)
    return gs, (lo, hi)


def best_params(gs):
    return {k.split("__")[-1]: v for k, v in gs.best_params_.items()}


# ---------------------------------------------------------------------------
# 分数的 4 个版本
# ---------------------------------------------------------------------------

TRANSFORMS = {
    "": "原始值：预测的 R&D / 总资产",
    "_clip0": "max(原始值, 0)",
    "_pct": "百分位排名，(0, 1]，在全部 firm-year 上计算，同值取平均排名",
    "_z": "标准化：(原始值 − 均值) / 标准差，在全部 firm-year 上计算",
}


def add_versions(df, col):
    x = df[col]
    df[f"{col}_clip0"] = x.clip(lower=0)
    df[f"{col}_pct"] = x.rank(pct=True)
    df[f"{col}_z"] = (x - x.mean()) / x.std()
    return df


# ---------------------------------------------------------------------------
# 模型的可移植格式（不依赖 sklearn 版本）
# ---------------------------------------------------------------------------

def export_portable(pipe, path_prefix):
    """把拟合好的 Pipeline 导出为 JSON（预处理参数 + Ridge 系数）；XGBoost 另存原生 booster JSON。

    写出 <prefix>.json（XGBoost 另有 <prefix>.booster.json）；predict_portable 可据此还原预测。
    """
    prep, model = pipe.named_steps["prep"], pipe.named_steps["model"]
    num = prep.named_transformers_["num"]
    top = prep.named_transformers_["topics:astra"]
    topic_cols = list(prep.transformers_[1][2])
    spec = {
        "feature_order": [SENTIMENT] + topic_cols,
        "sentiment": {"impute_median": float(num.named_steps["simpleimputer"].statistics_[0]),
                      "mean": float(num.named_steps["standardscaler"].mean_[0]),
                      "scale": float(num.named_steps["standardscaler"].scale_[0])},
        "topics": {"clr_eps": 1e-6, "columns": topic_cols,
                   "mean": top.named_steps["standardscaler"].mean_.tolist(),
                   "scale": top.named_steps["standardscaler"].scale_.tolist()},
    }
    prefix = Path(path_prefix)
    if isinstance(model, Ridge):
        spec["model"] = {"type": "ridge", "alpha": float(model.alpha), "coef": model.coef_.tolist(),
                         "intercept": float(model.intercept_)}
    else:
        booster_file = prefix.with_name(prefix.name + ".booster.json")
        model.get_booster().save_model(str(booster_file))
        spec["model"] = {"type": "xgboost", "booster_file": booster_file.name,
                         "params": {k: v for k, v in model.get_params().items() if v is not None}}
    prefix.with_name(prefix.name + ".json").write_text(json.dumps(spec, default=str), encoding="utf-8")


def portable_features(spec, df):
    s, t = spec["sentiment"], spec["topics"]
    sent = df[SENTIMENT].fillna(s["impute_median"]).to_numpy(dtype=np.float64)
    Z = clr(df[t["columns"]].to_numpy(), t["clr_eps"])
    return np.column_stack([(sent - s["mean"]) / s["scale"], (Z - np.array(t["mean"])) / np.array(t["scale"])])


def predict_portable(json_path, df):
    """用 export_portable 导出的 JSON 预测（Ridge 只需 numpy / pandas；XGBoost 另需 xgboost）。"""
    json_path = Path(json_path)
    spec = json.loads(json_path.read_text(encoding="utf-8"))
    X = portable_features(spec, df)
    m = spec["model"]
    if m["type"] == "ridge":
        return X @ np.array(m["coef"]) + m["intercept"]
    import xgboost as xgb
    booster = xgb.Booster()
    booster.load_model(str(json_path.with_name(m["booster_file"])))
    return booster.inplace_predict(X)
