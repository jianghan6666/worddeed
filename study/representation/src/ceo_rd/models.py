"""模型注册表。实验配置可以覆盖默认参数（params）与调参网格（grid）。"""

from dataclasses import dataclass
from typing import Callable

from sklearn.compose import TransformedTargetRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler


@dataclass(frozen=True)
class ModelDef:
    factory: Callable  # (params, seed, n_jobs) -> estimator
    params: dict
    grid: dict
    grid_prefix: str = ""  # grid 参数在 estimator 内的前缀
    parallel_cv: bool = True  # 树模型内部已多线程，交叉验证串行


def _ridge(params, seed, n_jobs):
    return Ridge(**params)


def _xgboost(params, seed, n_jobs):
    # Loading the optional native backend must not block Ridge/feature-only runs.
    from xgboost import XGBRegressor
    return XGBRegressor(tree_method="hist", n_jobs=n_jobs, random_state=seed, **params)


def _mlp(params, seed, n_jobs):
    # y 标准化后再训练，避免小尺度目标下 MLP 难以收敛
    return TransformedTargetRegressor(
        regressor=MLPRegressor(random_state=seed, **params), transformer=StandardScaler()
    )


def _random_forest(params, seed, n_jobs):
    return RandomForestRegressor(n_jobs=n_jobs, random_state=seed, **params)


MODELS = {
    "ridge": ModelDef(_ridge, {}, {"alpha": [1, 10, 100, 1000, 10000]}),
    "xgboost": ModelDef(
        _xgboost,
        {"n_estimators": 600, "learning_rate": 0.03, "subsample": 0.8, "colsample_bytree": 0.5},
        {"max_depth": [3, 6], "min_child_weight": [1, 10]},
        parallel_cv=False,
    ),
    "mlp": ModelDef(
        _mlp,
        {"early_stopping": True, "validation_fraction": 0.1, "max_iter": 300,
         "batch_size": 256, "learning_rate_init": 1e-3},
        {"hidden_layer_sizes": [(256,), (256, 64)], "alpha": [1e-3, 1e-1]},
        grid_prefix="regressor__",
    ),
    "random_forest": ModelDef(
        _random_forest, {"n_estimators": 300, "max_features": 0.3}, {"min_samples_leaf": [5, 20]},
        parallel_cv=False,
    ),
}


def validate_model(name, overrides):
    if name not in MODELS:
        raise ValueError(f"未知模型 {name}；可用模型: {sorted(MODELS)}")
    unknown = set(overrides) - {"params", "grid"}
    if unknown:
        raise ValueError(f"模型 {name} 的配置只能包含 params / grid，实际有 {sorted(unknown)}")


def build_model(name, overrides=None, seed=42, n_jobs=8):
    """返回 (estimator, 带 'model__' 前缀的 grid, GridSearchCV 的 n_jobs)。"""
    overrides = overrides or {}
    validate_model(name, overrides)
    d = MODELS[name]
    grid = overrides.get("grid", d.grid)
    params = {**d.params, **overrides.get("params", {})}
    params = {k: v for k, v in params.items() if k not in grid}  # 同时出现时以 grid 为准
    est = d.factory(params, seed, n_jobs)
    grid = {f"model__{d.grid_prefix}{k}": v for k, v in grid.items()}
    return est, grid, (min(n_jobs, 8) if d.parallel_cv else 1)
