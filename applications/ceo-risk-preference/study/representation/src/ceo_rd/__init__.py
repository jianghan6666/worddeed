"""用 CEO 讲话 topic 预测公司 R&D 强度：面板构建、实验框架与结果报告。"""

from .cli import enable_logging
from .config import Paths, load_paths
from .experiment import ExperimentResult, ExperimentSpec, run_experiment
from .panel import build_panel, load_panel
from .report import make_report, write_report

__version__ = "0.1.0"

__all__ = [
    "ExperimentResult", "ExperimentSpec", "Paths", "build_panel", "enable_logging", "load_panel",
    "load_paths", "make_report", "run_experiment", "write_report",
]
