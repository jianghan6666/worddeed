"""由 YAML 配置驱动的实验运行器。

一个实验 = 目标变量 x control set x text set x 模型 的全部组合；每个组合在训练集（fold != test_fold）上
用分组交叉验证调参，在测试集上评估，再按 comparisons 计算 R² 增量与 cluster bootstrap 置信区间。
配置格式见 experiments/*.yaml 与 README。
"""

import logging
import os
import time
import zlib
from dataclasses import asdict, dataclass, field, fields, replace
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from sklearn.model_selection import GridSearchCV, PredefinedSplit
from sklearn.pipeline import Pipeline

from .config import DEFAULT_PATHS, load_paths
from .evaluation import compare, metrics
from .features import CATEGORICAL, NUMERIC, TARGETS, column_of, make_preprocessor, split_variables, topic_columns
from .models import build_model, validate_model
from .panel import load_panel

log = logging.getLogger(__name__)


@dataclass
class ExperimentSpec:
    name: str
    targets: list
    control_sets: dict  # 名称 -> 变量列表（可以为空）
    text_sets: dict  # 名称 -> 变量列表（可以为空）；每个组合的特征 = control 变量 + text 变量
    models: dict  # 模型名 -> {params, grid}（可选覆盖默认值）
    comparisons: list = field(default_factory=list)  # [{label, dim: "text"|"control", pairs: [[from, to], ...]}]
    require: list = field(default_factory=list)  # 样本限定：这些变量非缺失
    test_fold: int = 0
    winsorize: list = field(default_factory=lambda: [0.01, 0.99])
    n_boot: int = 1000
    seed: int = 42
    n_jobs: int | None = None

    @classmethod
    def from_yaml(cls, path):
        with open(path, encoding="utf-8") as fh:
            return cls.from_dict(yaml.safe_load(fh))

    @classmethod
    def from_dict(cls, d):
        allowed = {f.name for f in fields(cls)}
        unknown = set(d) - allowed
        if unknown:
            raise ValueError(f"实验配置中有未知字段 {sorted(unknown)}；可用字段: {sorted(allowed)}")
        d = dict(d)
        models = d.get("models") or {}
        d["models"] = {m: {} for m in models} if isinstance(models, list) else {k: v or {} for k, v in models.items()}
        d["control_sets"] = {k: list(v or []) for k, v in (d.get("control_sets") or {}).items()}
        d["text_sets"] = {k: list(v or []) for k, v in (d.get("text_sets") or {}).items()}
        d["comparisons"] = [_normalize_comparison(c) for c in d.get("comparisons") or []]
        spec = cls(**d)
        spec.validate()
        return spec

    def to_dict(self):
        d = asdict(self)
        d["comparisons"] = [{"label": c["label"], c["dim"]: c["pairs"]} for c in self.comparisons]
        return d

    def validate(self):
        bad = [t for t in self.targets if t not in TARGETS]
        if bad:
            raise ValueError(f"未知目标变量 {bad}；可用: {sorted(TARGETS)}")
        if not self.control_sets or not self.text_sets:
            raise ValueError("control_sets 与 text_sets 都至少需要一项（可以是空列表）")
        for variables in [*self.control_sets.values(), *self.text_sets.values()]:
            split_variables(variables)
        bad = [v for v in self.require if v not in NUMERIC and v not in CATEGORICAL]
        if bad:
            raise ValueError(f"require 中有未知变量 {bad}")
        if not self.models:
            raise ValueError("至少需要一个模型")
        for name, overrides in self.models.items():
            validate_model(name, overrides)
        for c in self.comparisons:
            sets = self.text_sets if c["dim"] == "text" else self.control_sets
            for pair in c["pairs"]:
                missing = [s for s in pair if s not in sets]
                if missing:
                    raise ValueError(f"comparison '{c['label']}' 引用了不存在的 {c['dim']} set: {missing}")


def _normalize_comparison(c):
    dims = [k for k in ("text", "control") if k in c]
    if "label" not in c or len(dims) != 1 or set(c) - {"label", "text", "control"}:
        raise ValueError(f"comparison 须包含 label 以及 text / control 之一: {c}")
    pairs = c[dims[0]]
    if pairs and isinstance(pairs[0], str):
        pairs = [pairs]
    if any(len(p) != 2 for p in pairs):
        raise ValueError(f"comparison '{c['label']}' 的每一项须为 [from, to]")
    return {"label": c["label"], "dim": dims[0], "pairs": [list(p) for p in pairs]}


@dataclass
class ExperimentResult:
    spec: ExperimentSpec
    metrics: pd.DataFrame  # 每个 target x controls x text x model 的 CV / 测试集指标
    deltas: pd.DataFrame  # comparisons 的 R² 增量与置信区间
    predictions: pd.DataFrame  # 测试集预测值
    out_dir: Path | None = None

    def save(self, out_dir=None):
        out_dir = Path(out_dir or self.out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        with open(out_dir / "spec.yaml", "w", encoding="utf-8") as fh:
            yaml.safe_dump(self.spec.to_dict(), fh, allow_unicode=True, sort_keys=False)
        self.metrics.to_csv(out_dir / "metrics.csv", index=False)
        self.deltas.to_csv(out_dir / "deltas.csv", index=False)
        self.predictions.to_parquet(out_dir / "predictions.parquet", index=False)
        self.out_dir = out_dir
        return out_dir

    @classmethod
    def load(cls, out_dir):
        out_dir = Path(out_dir)
        pred_file = out_dir / "predictions.parquet"
        return cls(
            spec=ExperimentSpec.from_yaml(out_dir / "spec.yaml"),
            metrics=pd.read_csv(out_dir / "metrics.csv"),
            deltas=pd.read_csv(out_dir / "deltas.csv"),
            predictions=pd.read_parquet(pred_file) if pred_file.exists() else pd.DataFrame(),
            out_dir=out_dir,
        )

    def report(self):
        from .report import make_report
        return make_report(self)


def _target_sample(panel, spec, target):
    """目标变量与 require 变量均非缺失的样本；y 与 y_lag 按训练集分位数截尾。"""
    mask = panel[target].notna()
    for v in spec.require:
        mask &= panel[column_of(v, target)].notna()
    d = panel[mask].copy()
    is_test = d["fold"] == spec.test_fold
    lo, hi = d.loc[~is_test, target].quantile(spec.winsorize)
    d["y_lag"] = d[TARGETS[target]].clip(lo, hi)
    d["y"] = d[target].clip(lo, hi)
    return d[~is_test], d[is_test], (lo, hi)


def _comparison_runs(spec, comp):
    """展开一个 comparison：在另一维度的每个取值、每个模型上，产出 (from 键, to 键)。"""
    for a, b in comp["pairs"]:
        others = spec.control_sets if comp["dim"] == "text" else spec.text_sets
        for other in others:
            for model in spec.models:
                if comp["dim"] == "text":
                    yield (other, a, model), (other, b, model)
                else:
                    yield (a, other, model), (b, other, model)


def run_experiment(spec, paths=DEFAULT_PATHS, panel=None, out_dir=None, targets=None, models=None):
    """运行实验并保存结果。

    spec:    YAML 路径、dict 或 ExperimentSpec
    paths:   路径配置（用于读取面板与默认输出目录 results_dir/<name>）
    panel:   直接传入面板 DataFrame 时不再从磁盘读取
    targets, models: 只运行其中一部分（快速测试用；建议同时指定 out_dir，避免覆盖完整结果）
    """
    if isinstance(spec, (str, Path)):
        spec = ExperimentSpec.from_yaml(spec)
    elif isinstance(spec, dict):
        spec = ExperimentSpec.from_dict(spec)
    if targets:
        spec = replace(spec, targets=[t for t in spec.targets if t in targets])
    if models:
        spec = replace(spec, models={m: v for m, v in spec.models.items() if m in models})
    spec.validate()

    if panel is None:
        panel = load_panel(paths)
    if out_dir is None:
        out_dir = load_paths(paths).results_dir / spec.name
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    n_jobs = spec.n_jobs or min(16, os.cpu_count() or 1)
    topic_cols = topic_columns(panel)

    handler = logging.FileHandler(out_dir / "log.txt", mode="w", encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(message)s", "%H:%M:%S"))
    pkg_logger = logging.getLogger("ceo_rd")
    pkg_logger.addHandler(handler)
    prev_level = pkg_logger.level
    if pkg_logger.getEffectiveLevel() > logging.INFO:  # 调用方未配置日志时，日志文件仍记录进度
        pkg_logger.setLevel(logging.INFO)
    result = ExperimentResult(spec, pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), out_dir)
    rows, deltas, pred_frames = [], [], []
    try:
        log.info("实验 %s → %s", spec.name, out_dir)
        for target in spec.targets:
            tr, te, (lo, hi) = _target_sample(panel, spec, target)
            cv = PredefinedSplit(tr["fold"].values)
            log.info("=== %s: train %s, test %s, winsor [%.4f, %.4f] ===", target, f"{len(tr):,}", f"{len(te):,}", lo, hi)

            preds = {}
            for cs, c_vars in spec.control_sets.items():
                for ts, t_vars in spec.text_sets.items():
                    variables = c_vars + t_vars
                    if not variables:
                        continue
                    for mname, overrides in spec.models.items():
                        est, grid, cv_jobs = build_model(mname, overrides, spec.seed, n_jobs)
                        pipe = Pipeline([("prep", make_preprocessor(variables, topic_cols)), ("model", est)])
                        t0 = time.time()
                        gs = GridSearchCV(pipe, grid, cv=cv, scoring="r2", n_jobs=cv_jobs, refit=True)
                        gs.fit(tr, tr["y"].values)
                        yhat = gs.predict(te)
                        preds[(cs, ts, mname)] = yhat
                        m = metrics(te["y"].values, yhat)
                        rows.append({
                            "target": target, "controls": cs, "text": ts, "model": mname,
                            "n_train": len(tr), "n_test": len(te), "cv_r2": gs.best_score_,
                            **{f"test_{k}": v for k, v in m.items()},
                            "best_params": {k.split("__")[-1]: v for k, v in gs.best_params_.items()},
                            "secs": round(time.time() - t0, 1),
                        })
                        log.info("  %-14s %-18s %-13s cv_r2=%.3f  test_r2=%.3f  rho=%.3f  (%ss)",
                                 cs, ts, mname, gs.best_score_, m["r2"], m["spearman"], rows[-1]["secs"])
                        pred_frames.append(pd.DataFrame({
                            "panel_id": te["panel_id"].values, "target": target, "controls": cs,
                            "text": ts, "model": mname, "y": te["y"].values, "yhat": yhat,
                        }))

            groups = te["split_group"].values
            for comp in spec.comparisons:
                for ka, kb in _comparison_runs(spec, comp):
                    if ka not in preds or kb not in preds:
                        continue
                    # 每个比较用独立、确定的随机种子，结果不依赖运行顺序
                    key = f"{target}|{comp['label']}|{ka}|{kb}"
                    rng = np.random.default_rng([spec.seed, zlib.crc32(key.encode())])
                    deltas.append({
                        "target": target, "comparison": comp["label"], "model": ka[2],
                        "controls_from": ka[0], "controls_to": kb[0], "text_from": ka[1], "text_to": kb[1],
                        "n_test": len(te),
                        **compare(te["y"].values, preds[ka], preds[kb], groups, rng, spec.n_boot),
                    })

            # 每个目标变量跑完就落盘，中断时不丢结果
            result = ExperimentResult(spec, pd.DataFrame(rows), pd.DataFrame(deltas),
                                      pd.concat(pred_frames, ignore_index=True), out_dir)
            result.save()
        log.info("完成：%s", out_dir)
    finally:
        pkg_logger.removeHandler(handler)
        pkg_logger.setLevel(prev_level)
        handler.close()
    return result
