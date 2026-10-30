import numpy as np
import pandas as pd

from ceo_rd.panel import COMPONENT_MAP_FILE, PANEL_FILE, build_panel, load_panel


def test_build_panel_end_to_end(raw_data, tmp_path):
    panel = build_panel(raw_data["paths"])
    df, topics = raw_data["df"], raw_data["topics"]

    assert len(panel) == 30  # 15 家公司 x 2 年，每个 firm-year 一行
    assert (panel.groupby(["gvkey", "year"]).size() == 1).all()
    tc = [c for c in panel.columns if c.startswith("topic_")]
    np.testing.assert_allclose(panel[tc].sum(axis=1), 1, atol=1e-5)

    # 只保留主 CEO：非主 CEO（30 词）与非 CEO 行都不在 component map 中
    cmap = pd.read_parquet(tmp_path / "panel" / COMPONENT_MAP_FILE)
    assert set(df.loc[cmap["orig_idx"], "retained_word_count"]) == {100, 200}
    assert panel["ceo_id"].str.startswith("bx_").all()

    # 第一家公司 2014 年：第二条发言 topic 全 0，pooled topic 等于第一条发言
    first = panel[(panel["tic"] == "T0") & (panel["year"] == 2014)].iloc[0]
    np.testing.assert_allclose(first[tc].values.astype(float), topics[0], atol=1e-6)

    # 情绪按词数加权（包括 topic 全 0 的发言）
    s = df.loc[[0, 1], "sentiment_transformer"].values
    assert np.isclose(first["sent_transformer"], (200 * s[0] + 100 * s[1]) / 300)

    # 目标变量与滞后项：xrd 缺失 -> rd_at 为 NaN，rd_at_fill0 为 0
    t0 = panel[panel["tic"] == "T0"]  # g=0 的 xrd 缺失
    assert t0["rd_at"].isna().all() and (t0["rd_at_fill0"] == 0).all()
    t1 = panel[(panel["tic"] == "T1") & (panel["year"] == 2015)].iloc[0]
    assert np.isclose(t1["rd_at_lag"], 6.0 / 101.0)

    assert set(panel["fold"]) <= {0, 1, 2, 3, 4} and (panel["fold"] >= 0).all()
    loaded = load_panel(raw_data["paths"])
    assert {"sic2_cat", "sic4_cat", "year_cat"} <= set(loaded.columns)
    assert (tmp_path / "panel" / PANEL_FILE).exists()
