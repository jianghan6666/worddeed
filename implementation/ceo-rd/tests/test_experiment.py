import pytest

from ceo_rd.cli import main
from ceo_rd.experiment import ExperimentResult, ExperimentSpec, run_experiment
from ceo_rd.report import write_report

SPEC = {
    "name": "test",
    "targets": ["rd_at_fill0", "rd_sale_fill0"],
    "require": ["y_lag"],
    "control_sets": {"none": [], "base": ["log_at", "sic2", "year"], "lag": ["log_at", "y_lag", "sic2", "year"]},
    "text_sets": {"none": [], "topics": ["topics"]},
    "models": ["ridge"],
    "comparisons": [{"label": "topics | controls", "text": ["none", "topics"]},
                    {"label": "lag", "control": ["base", "lag"]}],
    "n_boot": 50,
}


def test_run_experiment_ridge(panel, tmp_path):
    res = run_experiment(SPEC, panel=panel, out_dir=tmp_path / "out")
    # 每个目标变量 5 个组合（none + none 跳过）
    assert len(res.metrics) == 2 * 5
    d = res.deltas
    topics = d[(d["comparison"] == "topics | controls") & (d["target"] == "rd_at_fill0")]
    assert set(topics["controls_from"]) == {"base", "lag"}  # none 下没有 controls-only 基准
    assert (topics["delta_r2"] > 0).all() and (topics["ci_lo"] > 0).all()
    lag = d[d["comparison"] == "lag"]
    assert set(zip(lag["controls_from"], lag["controls_to"])) == {("base", "lag")}
    assert set(lag["text_from"]) == {"none", "topics"}
    # 训练集不含 fold 0，y_lag 非缺失（每家公司第一年被剔除）
    assert res.metrics["n_test"].iat[0] == (panel["fold"] == 0).sum() * 4 // 5

    loaded = ExperimentResult.load(tmp_path / "out")
    assert loaded.spec == res.spec
    assert len(loaded.predictions) == len(res.predictions)
    text = write_report(loaded).read_text(encoding="utf-8")
    assert "### ΔR²: topics | controls" in text and "**+" in text


def test_model_overrides_and_filters(panel, tmp_path):
    spec = dict(SPEC, models={"ridge": {"grid": {"alpha": [10]}},
                              "xgboost": {"params": {"n_estimators": 20}, "grid": {"max_depth": [2]}}})
    res = run_experiment(spec, panel=panel, out_dir=tmp_path / "out", targets=["rd_at_fill0"], models=["xgboost"])
    assert set(res.metrics["model"]) == {"xgboost"} and set(res.metrics["target"]) == {"rd_at_fill0"}
    assert res.metrics["best_params"].iat[0] == {"max_depth": 2}


@pytest.mark.parametrize("change, message", [
    ({"targets": ["roa"]}, "未知目标变量"),
    ({"text_sets": {"none": [], "topics": ["topicz"]}}, "未知变量"),
    ({"comparisons": [{"label": "x", "text": ["none", "missing"]}]}, "不存在"),
    ({"models": ["svm"]}, "未知模型"),
    ({"model": ["ridge"]}, "未知字段"),
])
def test_spec_validation(change, message):
    with pytest.raises(ValueError, match=message):
        ExperimentSpec.from_dict({**SPEC, **change})


def test_cli_run_and_report(panel, tmp_path):
    panel_dir = tmp_path / "panel"
    panel_dir.mkdir()
    panel.to_parquet(panel_dir / "ceo_firm_year_panel.parquet", index=False)
    paths = tmp_path / "paths.yaml"
    paths.write_text(f"transcripts: x\ntopics: x\ncompustat: x\npanel_dir: {panel_dir.as_posix()}\n"
                     f"results_dir: {(tmp_path / 'results').as_posix()}\n", encoding="utf-8")
    spec = tmp_path / "spec.yaml"
    spec.write_text("name: cli\ntargets: [rd_at_fill0]\ncontrol_sets: {base: [log_at, sic2, year]}\n"
                    "text_sets: {none: [], topics: [topics]}\nmodels: [ridge]\nn_boot: 20\n"
                    "comparisons:\n  - {label: topics, text: [none, topics]}\n", encoding="utf-8")
    main(["run", str(spec), "--paths", str(paths)])
    out = tmp_path / "results" / "cli"
    assert (out / "report.md").exists() and (out / "log.txt").read_text(encoding="utf-8")
    main(["report", str(out)])
