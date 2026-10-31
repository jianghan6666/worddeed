import numpy as np
import pandas as pd
import pytest

from ceo_rd.data import iter_topic_chunks, load_compustat, topic_shape
from ceo_rd.features import clr, make_preprocessor, split_variables, topic_columns


def test_clr_rows_center_to_zero():
    X = np.random.default_rng(0).dirichlet(np.ones(6), size=10)
    np.testing.assert_allclose(clr(X).sum(axis=1), 0, atol=1e-9)


def test_split_variables_keeps_order_by_type():
    num, cat, with_topics = split_variables(["log_at", "sic4", "y_lag", "year", "topics", "sentiment"])
    assert num == ["log_at", "y_lag", "sent_transformer"]
    assert cat == ["sic4_cat", "year_cat"]
    assert with_topics


def test_split_variables_rejects_unknown():
    with pytest.raises(ValueError, match="未知变量"):
        split_variables(["log_at", "leverage"])


def test_signed_narrative_is_numeric_and_missing_n_is_never_imputed():
    panel = pd.DataFrame({"N_raw": [-0.6, 0.0, 0.6], "log_at": [1.0, np.nan, 3.0]})
    assert split_variables(["N_raw", "log_at"]) == (["N_raw", "log_at"], [], False)
    processor = make_preprocessor(["N_raw", "log_at"], [])
    values = processor.fit_transform(panel)
    assert values.shape == (3, 2)
    np.testing.assert_allclose(values[:, 0], [-np.sqrt(1.5), 0, np.sqrt(1.5)])
    for invalid in (np.nan, np.inf):
        incomplete = panel.copy()
        incomplete.loc[0, "N_raw"] = invalid
        with pytest.raises(ValueError, match="complete finite Stage 2"):
            processor.transform(incomplete)


def test_make_preprocessor_width(panel):
    tc = topic_columns(panel)
    X = make_preprocessor(["log_at", "year", "topics"], tc).fit_transform(panel)
    assert X.shape == (len(panel), 1 + panel["year_cat"].nunique() + len(tc))


def test_folds_keep_firms_and_shared_ceos_together(panel):
    assert set(panel["fold"]) == {0, 1, 2, 3, 4}
    assert (panel.groupby("gvkey")["fold"].nunique() == 1).all()
    assert (panel.groupby("split_group")["fold"].nunique() == 1).all()
    folds = panel.loc[panel["gvkey"].isin([1000, 1001]), "fold"]
    assert folds.nunique() == 1  # 共享 CEO 的两家公司


def test_iter_topic_chunks_reassembles(tmp_path):
    X = np.random.default_rng(0).random((1003, 7))
    np.savez_compressed(tmp_path / "t.npz", topic_distr=X)
    assert topic_shape(tmp_path / "t.npz") == (1003, 7)
    chunks = list(iter_topic_chunks(tmp_path / "t.npz", chunk_rows=100))
    assert [s for s, _ in chunks] == list(range(0, 1003, 100))
    np.testing.assert_array_equal(np.vstack([c for _, c in chunks]), X)


def test_load_compustat_dedup_and_lag(tmp_path):
    pd.DataFrame({
        "tic": ["A", "A", "A", "B"], "gvkey": [1, 1, 1, 2], "fyear": [2014, 2015, 2015, 2015],
        "datadate": ["2014-12-31", "2015-06-30", "2015-12-31", "2015-12-31"],
        "at": [10.0, 11.0, 12.0, 5.0], "sale": [1.0, 2.0, 3.0, 4.0], "xrd": [0.5, np.nan, 0.7, np.nan],
        "sich": [2834.0] * 3 + [6021.0],
    }).to_csv(tmp_path / "c.csv", index=False)
    f = load_compustat(tmp_path / "c.csv").set_index(["gvkey", "fyear"])
    assert len(f) == 3
    assert f.loc[(1, 2015), "at"] == 12.0  # 保留最新 datadate
    assert f.loc[(1, 2015), "at_lag"] == 10.0
    assert np.isnan(f.loc[(2, 2015), "at_lag"])
