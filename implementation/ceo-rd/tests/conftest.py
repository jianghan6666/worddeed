"""合成数据：测试不依赖授权的原始数据。"""

import numpy as np
import pandas as pd
import pytest

from ceo_rd.features import add_model_columns
from ceo_rd.splits import assign_folds

SICS = [2834, 2836, 3571, 3674, 7372, 6021, 4911, 5411]


def make_panel(n_firms=80, n_years=5, n_topics=8, seed=0):
    """firm-year 面板：R&D 强度由行业与 topic_000 决定，topic 有公司层面的持续性。"""
    rng = np.random.default_rng(seed)
    rows = []
    for g in range(n_firms):
        sich = SICS[g % len(SICS)]
        alpha = rng.uniform(0.5, 3, n_topics)
        level = max(0.0, 0.15 * (sich < 4000) + rng.normal(0, 0.03))
        for t in range(n_years):
            topics = rng.dirichlet(alpha)
            rd = max(0.0, level + 0.4 * (topics[0] - 1 / n_topics) + rng.normal(0, 0.01))
            rows.append({"gvkey": 1000 + g, "ceo_id": f"bx_{g}", "year": 2013 + t, "sich": float(sich),
                         "rd_at_fill0": rd, "log_at": rng.normal(7, 2),
                         "ceo_gender": rng.choice(["M", "F"], p=[0.9, 0.1]), "ceo_age": rng.normal(56, 7),
                         "ceo_educ": rng.choice(["college", "masters", "doctorate"]),
                         "sent_transformer": rng.normal(0.14, 0.07),
                         **{f"topic_{i:03d}": topics[i] for i in range(n_topics)}})
    p = pd.DataFrame(rows)
    p.loc[p["gvkey"] == 1001, "ceo_id"] = "bx_0"  # 1000 与 1001 共享 CEO，须分到同一 fold
    p["has_rd"] = (p["rd_at_fill0"] > 0).astype(int)
    p["rd_at"] = p["rd_at_fill0"].where(p["has_rd"] == 1)
    p["rd_sale_fill0"] = 2 * p["rd_at_fill0"]
    p["rd_sale"] = p["rd_sale_fill0"].where(p["has_rd"] == 1)
    for col, lag in [("rd_at_fill0", "rd_at_lag"), ("rd_sale_fill0", "rd_sale_lag")]:
        p[lag] = p.groupby("gvkey")[col].shift(1)
    p["panel_id"] = np.arange(len(p))
    return add_model_columns(assign_folds(p, n_folds=5, seed=42))


@pytest.fixture
def panel():
    return make_panel()


@pytest.fixture
def raw_data(tmp_path):
    """最小的原始数据：transcript pickle、topic npz、Compustat CSV 与对应的 paths.yaml。"""
    rng = np.random.default_rng(1)
    n_topics = 5
    rows = []
    for g in range(15):
        for year in (2014, 2015):
            def add(is_ceo, person, director, words, gender="M"):
                rows.append({
                    "is_ceo": is_ceo, "companyid": 500 + g, "transcriptid": year * 100 + g,
                    "transcriptpersonid": person, "directorid": director,
                    "transcriptpersonname": f"P{person}", "symbolvalue": f"T{g}", "year": year,
                    "retained_word_count": words, "transcriptcomponenttypename": "Answer",
                    "ggroup": 4510.0, "gender": gender, "age": 50.0 + g, "educ_level": "masters",
                    "sentiment_transformer": rng.uniform(-0.2, 0.5),
                })
            add(True, g, 9000 + g, 200)   # 主 CEO
            add(True, g, 9000 + g, 100)   # 主 CEO
            add(True, 700 + g, None, 30)  # 词数少的"CEO"（如 Division CEO），应被丢弃
            add(False, 800 + g, None, 300)
    df = pd.DataFrame(rows)
    topics = rng.dirichlet(np.ones(n_topics), size=len(df))
    topics[1] = 0.0  # 第一家公司 2014 年第二条主 CEO 发言没有 topic，应排除在 pooling 之外
    np.savez_compressed(tmp_path / "topics.npz", topic_distr=topics)
    df.to_pickle(tmp_path / "transcripts.pkl")

    firm = []
    for g in range(15):
        for fyear in (2013, 2014, 2015):
            firm.append({"tic": f"T{g}", "gvkey": 100 + g, "fyear": fyear, "datadate": f"{fyear}-12-31",
                         "at": 100.0 + g, "sale": 50.0 + g, "xrd": (5.0 + g) if g % 3 else np.nan,
                         "sich": float(SICS[g % len(SICS)])})
    pd.DataFrame(firm).to_csv(tmp_path / "compustat.csv", index=False)

    paths = tmp_path / "paths.yaml"
    paths.write_text(
        f"transcripts: {(tmp_path / 'transcripts.pkl').as_posix()}\n"
        f"topics: {(tmp_path / 'topics.npz').as_posix()}\n"
        f"compustat: {(tmp_path / 'compustat.csv').as_posix()}\n"
        f"panel_dir: {(tmp_path / 'panel').as_posix()}\n"
        f"results_dir: {(tmp_path / 'results').as_posix()}\n",
        encoding="utf-8",
    )
    return {"paths": paths, "df": df, "topics": topics}
