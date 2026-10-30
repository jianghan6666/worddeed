"""实验中可用的变量、目标变量与预处理。

实验配置（YAML）里用下面注册的变量名指定特征；每个变量的预处理方式由类型决定：
    numeric      -> 中位数填补 + 标准化
    categorical  -> one-hot（缺失作为单独类别，测试集未见类别忽略）
    topics       -> CLR（成分数据的 centered log-ratio）+ 标准化
"""

import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import FunctionTransformer, OneHotEncoder, StandardScaler

TOPIC_PREFIX = "topic_"
TOPICS = "topics"

# 变量名 -> 面板中的列
NUMERIC = {
    "log_at": "log_at",
    "y_lag": "y_lag",  # 上一年 R&D ratio，按目标变量构造，并用目标变量的 winsorize 阈值截尾
    "ceo_age": "ceo_age",
    "sentiment": "sent_transformer",
    "N_raw": "N_raw",  # Stage 2 scalar; join only complete scores before preprocessing.
}
CATEGORICAL = {
    "sic2": "sic2_cat",
    "sic3": "sic3_cat",
    "sic4": "sic4_cat",
    "year": "year_cat",
    "ceo_gender": "ceo_gender",
    "ceo_educ": "ceo_educ",
}

# 目标变量 -> 对应的上一年 ratio 列
TARGETS = {
    "rd_at_fill0": "rd_at_lag",  # xrd / at，xrd 缺失视为 0
    "rd_at": "rd_at_lag",  # xrd / at，仅 xrd 非缺失
    "rd_sale_fill0": "rd_sale_lag",
    "rd_sale": "rd_sale_lag",
}


def clr(X, eps=1e-6):
    L = np.log(np.asarray(X, dtype=np.float64) + eps)
    return L - L.mean(axis=1, keepdims=True)


def complete_narrative(X):
    """N is already signed: never CLR-transform or impute unresolved scores."""
    values = np.asarray(X, dtype=np.float64)
    if not np.isfinite(values).all():
        raise ValueError("N_raw requires complete finite Stage 2 scores; apply the checked eligibility join first")
    return values


def topic_columns(panel):
    return [c for c in panel.columns if c.startswith(TOPIC_PREFIX)]


def add_model_columns(panel):
    """添加建模用的类别列（SIC 各级行业、年份），缺失 SIC 记为 "<NA>" 类别。"""
    sich = panel["sich"].astype("Int64")
    panel["sic2_cat"] = (sich // 100).astype(str)
    panel["sic3_cat"] = (sich // 10).astype(str)
    panel["sic4_cat"] = sich.astype(str)
    panel["year_cat"] = panel["year"].astype(str)
    return panel


def split_variables(variables):
    """按类型拆分变量名，保持各自的书写顺序。返回 (numeric 列, categorical 列, 是否含 topics)。"""
    unknown = [v for v in variables if v not in NUMERIC and v not in CATEGORICAL and v != TOPICS]
    if unknown:
        valid = sorted(NUMERIC) + sorted(CATEGORICAL) + [TOPICS]
        raise ValueError(f"未知变量 {unknown}；可用变量: {valid}")
    num = [NUMERIC[v] for v in variables if v in NUMERIC]
    cat = [CATEGORICAL[v] for v in variables if v in CATEGORICAL]
    return num, cat, TOPICS in variables


def column_of(variable, target):
    """变量在面板中对应的原始列（y_lag 取目标变量对应的上一年 ratio，截尾前）。"""
    if variable == "y_lag":
        return TARGETS[target]
    if variable in NUMERIC:
        return NUMERIC[variable]
    if variable in CATEGORICAL:
        return CATEGORICAL[variable]
    raise ValueError(f"未知变量 {variable}")


def make_preprocessor(variables, topic_cols):
    num, cat, with_topics = split_variables(variables)
    parts = []
    if "N_raw" in num:
        num = [column for column in num if column != "N_raw"]
        parts.append(("narrative", make_pipeline(FunctionTransformer(complete_narrative), StandardScaler()), ["N_raw"]))
    if num:
        parts.append(("num", make_pipeline(SimpleImputer(strategy="median"), StandardScaler()), num))
    if cat:
        parts.append(("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), cat))
    if with_topics:
        parts.append(("topic", make_pipeline(FunctionTransformer(clr), StandardScaler()), topic_cols))
    if not parts:
        raise ValueError("特征为空")
    return ColumnTransformer(parts)
