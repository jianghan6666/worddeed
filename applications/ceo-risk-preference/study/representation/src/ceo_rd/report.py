"""从实验结果生成 markdown 汇总表（测试集 R²、各比较的 ΔR² 与 RMSE）。"""

from pathlib import Path

TARGET_LABELS = {
    "rd_at_fill0": "R&D / total assets (missing R&D = 0)",
    "rd_at": "R&D / total assets (non-missing R&D only)",
    "rd_sale_fill0": "R&D / sales (missing R&D = 0)",
    "rd_sale": "R&D / sales (non-missing R&D only)",
}


def _table(header, rows):
    out = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    out += ["| " + " | ".join(str(x) for x in row) + " |" for row in rows]
    return out


def _fmt_delta(r):
    s = f"{r.delta_r2:+.3f} [{r.ci_lo:.3f}, {r.ci_hi:.3f}]"
    return f"**{s}**" if r.ci_lo > 0 or r.ci_hi < 0 else s


def make_report(result):
    """result 为 ExperimentResult；返回 markdown 字符串。"""
    spec, m, d = result.spec, result.metrics, result.deltas
    lines = [f"# Experiment: {spec.name}", ""]
    sample = "target non-missing" + (f", and non-missing {', '.join(spec.require)}" if spec.require else "")
    lines += [
        f"- Sample: {sample}. Test set = fold {spec.test_fold}; tuning by grouped CV on the other folds.",
        f"- Outcome winsorized at the training-set {spec.winsorize[0]:.0%} / {spec.winsorize[1]:.0%} quantiles.",
        f"- ΔR² in **bold**: the 95% cluster-bootstrap CI ({spec.n_boot:,} resamples by firm group) excludes 0.",
        "- RMSE is in units of the winsorized ratio.",
        "",
        "## Feature sets",
        "",
    ]
    lines += _table(["type", "name", "variables"],
                    [["controls", k, ", ".join(v) or "–"] for k, v in spec.control_sets.items()]
                    + [["text", k, ", ".join(v) or "–"] for k, v in spec.text_sets.items()])
    lines.append("")

    for target in spec.targets:
        mt = m[m["target"] == target]
        if mt.empty:
            continue
        lines += [f"## {TARGET_LABELS.get(target, target)}", "",
                  f"Train {mt['n_train'].iat[0]:,} / test {mt['n_test'].iat[0]:,} firm-years.", "",
                  "### Test R²", ""]
        texts = [t for t in spec.text_sets if t in set(mt["text"])]
        rows = []
        for cs in spec.control_sets:
            for model in spec.models:
                sub = mt[(mt["controls"] == cs) & (mt["model"] == model)].set_index("text")["test_r2"]
                if not sub.empty:
                    rows.append([cs, model] + [f"{sub[t]:.3f}" if t in sub else "–" for t in texts])
        lines += _table(["controls", "model"] + [f"text: {t}" for t in texts], rows)
        lines.append("")

        for comp in spec.comparisons:
            dt = d[(d["target"] == target) & (d["comparison"] == comp["label"])]
            if dt.empty:
                continue
            lines += [f"### ΔR²: {comp['label']}", ""]
            rows = []
            for r in dt.itertuples():
                if comp["dim"] == "text":
                    cs, ts = r.controls_from, f"{r.text_from} → {r.text_to}"
                else:
                    cs, ts = f"{r.controls_from} → {r.controls_to}", r.text_from
                rows.append([cs, ts, r.model, f"{r.r2_from:.3f}", f"{r.r2_to:.3f}", _fmt_delta(r),
                             f"{r.rmse_from:.4f}", f"{r.rmse_to:.4f}"])
            lines += _table(["controls", "text", "model", "R² from", "R² to", "ΔR² [95% CI]",
                             "RMSE from", "RMSE to"], rows)
            lines.append("")
    return "\n".join(lines)


def write_report(result, path=None):
    """result 为 ExperimentResult 或结果目录；默认写入 <结果目录>/report.md，返回文件路径。"""
    if isinstance(result, (str, Path)):
        from .experiment import ExperimentResult
        result = ExperimentResult.load(result)
    path = Path(path) if path else Path(result.out_dir) / "report.md"
    path.write_text(make_report(result), encoding="utf-8")
    return path
