"""数据路径配置（configs/paths.yaml）。"""

from dataclasses import dataclass, fields
from pathlib import Path

import yaml

DEFAULT_PATHS = "configs/paths.yaml"


@dataclass
class Paths:
    # 面板构建用（topic modeling 的机器上可以不配置）
    transcripts: Path | None = None
    topics: Path | None = None
    compustat: Path | None = None
    topics_key: str = "topic_distr"
    # topic modeling 用
    corpus: Path | None = None
    models_dir: Path = Path("models")
    # 输出
    panel_dir: Path = Path("data/panel")
    results_dir: Path = Path("results")

    def __post_init__(self):
        for f in fields(self):
            value = getattr(self, f.name)
            if f.name != "topics_key" and value is not None:
                setattr(self, f.name, Path(value))

    def require(self, name):
        """返回某个路径；未配置时给出明确的错误。"""
        value = getattr(self, name)
        if value is None:
            raise ValueError(f"路径配置中缺少 {name}，请在 configs/paths.yaml 中填写")
        return value


def load_paths(path=DEFAULT_PATHS):
    """读取路径配置；已是 Paths 时原样返回。相对路径以当前工作目录为基准。"""
    if isinstance(path, Paths):
        return path
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(
            f"找不到路径配置 {path}。请复制 configs/paths.example.yaml 为 configs/paths.yaml 并填写数据路径。"
        )
    with open(path, encoding="utf-8") as fh:
        d = yaml.safe_load(fh) or {}
    allowed = {f.name for f in fields(Paths)}
    unknown = set(d) - allowed
    if unknown:
        raise ValueError(f"{path} 中有未知字段: {sorted(unknown)}；可用字段: {sorted(allowed)}")
    return Paths(**d)
