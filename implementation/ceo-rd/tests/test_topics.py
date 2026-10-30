"""topic modeling 测试：用假的模型 / 编码器与手工生成的模型文件代替 BERTopic，不导入、不运行 BERTopic。"""

import json
import sys
import types
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from ceo_rd.cli import main
from ceo_rd.data import write_npz_chunks
from ceo_rd.topics import (INFERENCE_DEFAULTS, TopicModelSpec, assign_topics, export_topic_excel,
                           export_training_topics, infer_topic_distribution, load_corpus, top_words, topic_table,
                           train_topic_model)
from ceo_rd.topics import train as train_mod
from ceo_rd.topics.modelfiles import load_ctfidf, read_safetensors, training_topics

VOCAB = ["alpha", "beta", "gamma", "delta", "alpha beta"]
CTFIDF = np.array([[0.1, 0.0, 0.3, 0.2, 0.0],   # topic -1
                   [0.9, 0.5, 0.0, 0.0, 0.5],   # topic 0（beta 与 "alpha beta" 分数相同）
                   [0.0, 0.2, 0.4, 0.8, 0.0]])  # topic 1
TRAIN_TOPICS = [-1, 0, 1, 0, -1, 1]


def write_safetensors(path, tensors):
    codes = {np.dtype("float64"): "F64", np.dtype("int64"): "I64", np.dtype("int32"): "I32"}
    header, blobs, offset = {}, [], 0
    for name, arr in tensors.items():
        b = np.ascontiguousarray(arr).tobytes()
        header[name] = {"dtype": codes[arr.dtype], "shape": list(arr.shape), "data_offsets": [offset, offset + len(b)]}
        blobs.append(b)
        offset += len(b)
    h = json.dumps(header).encode()
    Path(path).write_bytes(len(h).to_bytes(8, "little") + h + b"".join(blobs))


def write_model_files(model_dir):
    """按 BERTopic safetensors 格式写一个最小的模型目录。"""
    model_dir = Path(model_dir)
    model_dir.mkdir(parents=True, exist_ok=True)
    from scipy import sparse
    m = sparse.csr_matrix(CTFIDF)
    write_safetensors(model_dir / "ctfidf.safetensors", {
        "shape": np.array(m.shape, dtype=np.int64), "data": m.data.astype(np.float64),
        "indices": m.indices.astype(np.int32), "indptr": m.indptr.astype(np.int32)})
    (model_dir / "ctfidf_config.json").write_text(json.dumps(
        {"vectorizer_model": {"params": {}, "vocab": {w: i for i, w in enumerate(VOCAB)}}}), encoding="utf-8")
    reps = {str(t): [[VOCAB[j], float(CTFIDF[r, j])] for j in np.argsort(-CTFIDF[r])[:3]]
            for r, t in enumerate([-1, 0, 1])}
    (model_dir / "topics.json").write_text(json.dumps({
        "topic_representations": reps, "topics": TRAIN_TOPICS,
        "topic_sizes": {"-1": 2, "0": 2, "1": 2},
        "topic_labels": {"-1": "-1_gamma_delta", "0": "0_alpha_beta", "1": "1_delta_gamma"},
        "custom_labels": None, "_outliers": 1,
        "topic_aspects": {"KeyBERT": {"-1": [["x", 0.1]], "0": [["alpha", 0.9]], "1": [["delta", 0.8]]}},
    }), encoding="utf-8")
    pd.DataFrame({"Topic": [-1, 0, 1], "Count": [2, 2, 2],
                  "Representative_Docs": [str(["doc a\x01", "doc b"]), str(["doc c"]), str(["doc d"])]}
                 ).to_csv(model_dir / "topic_info.csv", index=False)
    (model_dir / "config.json").write_text("{}", encoding="utf-8")
    return model_dir


def fake_distribution(docs):
    """确定性的假 topic 分布：按文本长度落在 3 个 topic 之一。"""
    out = np.zeros((len(docs), 3))
    out[np.arange(len(docs)), [len(d) % 3 for d in docs]] = 1.0
    return out


class FakeInferenceModel:
    def __init__(self, fail_on_call=None):
        self.calls, self.fail_on_call = [], fail_on_call

    def approximate_distribution(self, docs, **params):
        self.calls.append((len(docs), params))
        if self.fail_on_call is not None and len(self.calls) == self.fail_on_call:
            raise RuntimeError("模拟中断")
        return fake_distribution(docs), None

    def transform(self, docs):
        self.calls.append((len(docs), {}))
        return [len(d) % 3 - 1 for d in docs], np.array([len(d) / 100 for d in docs])


class FakeTrainedModel:
    def fit_transform(self, docs, embeddings):
        self.fitted = (len(docs), embeddings.shape)
        return TRAIN_TOPICS, None

    def get_topic_info(self):
        return pd.DataFrame({"Topic": [-1, 0, 1], "Count": [2, 2, 2],
                             "Representative_Docs": [str(["a"]), str(["b"]), str(["c"])]})

    def save(self, path, **kwargs):
        self.save_kwargs = kwargs
        write_model_files(path)


@pytest.fixture
def corpus(tmp_path):
    df = pd.DataFrame({"componenttext_masked": [f"doc {'x' * i}" for i in range(25)],
                       "averageDem": [0.4 if i % 2 else np.nan for i in range(25)],
                       "other": range(25)})
    df.to_pickle(tmp_path / "corpus.pickle")
    return df


def test_importing_topics_does_not_import_bertopic():
    assert "bertopic" not in sys.modules
    assert "sentence_transformers" not in sys.modules


def test_spec_file_parses():
    spec = TopicModelSpec.from_yaml("topic_models/bertopic_ideo_13-23_relaxed.yaml")
    assert spec.notna_columns == ["averageDem"]
    assert spec.hdbscan["min_cluster_size"] == 120 and spec.umap["random_state"] == 42
    assert spec.representation["MMR"] == {"type": "mmr", "diversity": 0.3}


@pytest.mark.parametrize("change, message", [
    ({"representation": {"X": {"type": "gpt"}}}, "type"),
    ({"bertopic": {"umap_model": None}}, "不能包含"),
    ({"train_filter": {"isin": ["a"]}}, "notna"),
    ({"umap_params": {}}, "未知字段"),
])
def test_spec_validation(change, message):
    with pytest.raises(ValueError, match=message):
        TopicModelSpec.from_dict({"name": "t", **change})


@pytest.mark.parametrize("fmt", ["pickle", "parquet", "csv"])
def test_load_corpus_formats_and_filter(corpus, tmp_path, fmt):
    path = tmp_path / f"c.{fmt}"
    {"pickle": corpus.to_pickle, "parquet": lambda p: corpus.to_parquet(p, index=False),
     "csv": lambda p: corpus.to_csv(p, index=False)}[fmt](path)
    texts, idx = load_corpus(path, notna=["averageDem"])
    assert list(idx) == list(range(1, 25, 2))
    assert texts == corpus["componenttext_masked"].iloc[idx].tolist()
    all_texts, all_idx = load_corpus(path)
    assert len(all_texts) == 25 and list(all_idx) == list(range(25))


def test_write_npz_chunks_roundtrip(tmp_path):
    X = np.random.default_rng(0).random((23, 5))
    write_npz_chunks(tmp_path / "a.npz", "topic_distr", [X[:10], X[10:20], X[20:]], extra={"row_index": np.arange(23)})
    z = np.load(tmp_path / "a.npz")
    np.testing.assert_array_equal(z["topic_distr"], X)
    np.testing.assert_array_equal(z["row_index"], np.arange(23))


def test_model_files_reader(tmp_path):
    d = write_model_files(tmp_path / "m")
    assert set(read_safetensors(d / "ctfidf.safetensors")) == {"shape", "data", "indices", "indptr"}
    matrix, vocab = load_ctfidf(d)
    np.testing.assert_allclose(matrix.toarray(), CTFIDF)
    assert list(vocab) == VOCAB
    assert list(training_topics(d)) == TRAIN_TOPICS


def test_top_words_and_topic_table(tmp_path):
    d = write_model_files(tmp_path / "m")
    long, wide = top_words(d, top_n=3)
    # 分数相同（beta 与 "alpha beta"）时按字母顺序
    assert wide.set_index("Topic").loc[0].tolist() == ["alpha", "alpha beta", "beta"]
    assert wide.set_index("Topic").loc[1].tolist() == ["delta", "gamma", "beta"]
    table = topic_table(d)
    assert list(table["Name"]) == ["-1_gamma_delta", "0_alpha_beta", "1_delta_gamma"]
    assert (table["Label"] == "").all() and table["Share"].sum() == pytest.approx(1)
    assert table.loc[1, "KeyBERT"] == "alpha"


def test_export_topic_excel(tmp_path):
    d = write_model_files(tmp_path / "m")
    out = export_topic_excel(d, tmp_path / "desc.xlsx", top_n=3)
    sheets = pd.read_excel(out, sheet_name=None)
    assert list(sheets) == ["说明", "Topics", "Top3_Words", "Top3_With_Scores", "Representative_Docs"]
    assert sheets["Topics"].shape[0] == 3
    assert sheets["Representative_Docs"]["Document"].tolist()[0] == "doc a"  # 去掉了 Excel 不允许的控制字符


def test_infer_chunks_match_direct_computation(corpus, tmp_path):
    texts = corpus["componenttext_masked"].tolist()
    model = FakeInferenceModel()
    out = infer_topic_distribution(model, texts, tmp_path / "td.npz", chunk_size=10, meta={"note": "x"})
    np.testing.assert_array_equal(np.load(out)["topic_distr"], fake_distribution(texts))
    assert [n for n, _ in model.calls] == [10, 10, 5]
    assert model.calls[0][1] == INFERENCE_DEFAULTS  # 推断参数显式固定为原 notebook 的取值
    assert not (tmp_path / "td.npz.parts").exists()
    assert '"note": "x"' in (tmp_path / "td.npz.meta.json").read_text(encoding="utf-8")
    with pytest.raises(FileExistsError):
        infer_topic_distribution(model, texts, out, chunk_size=10)


def test_infer_resumes_after_interruption(corpus, tmp_path):
    texts = corpus["componenttext_masked"].tolist()
    with pytest.raises(RuntimeError, match="模拟中断"):
        infer_topic_distribution(FakeInferenceModel(fail_on_call=2), texts, tmp_path / "td.npz", chunk_size=10)
    assert (tmp_path / "td.npz.parts" / "part_00000.npy").exists()
    assert not (tmp_path / "td.npz").exists()
    with pytest.raises(ValueError, match="不同设置"):
        infer_topic_distribution(FakeInferenceModel(), texts, tmp_path / "td.npz", chunk_size=5)
    model = FakeInferenceModel()
    out = infer_topic_distribution(model, texts, tmp_path / "td.npz", chunk_size=10)
    assert [n for n, _ in model.calls] == [10, 5]  # 第 0 块已完成，被跳过
    np.testing.assert_array_equal(np.load(out)["topic_distr"], fake_distribution(texts))


def test_infer_rejects_unknown_params(tmp_path):
    with pytest.raises(ValueError, match="未知的推断参数"):
        infer_topic_distribution(FakeInferenceModel(), ["a"], tmp_path / "x.npz", nr_topics=5)


def test_assign_topics(corpus, tmp_path):
    texts = corpus["componenttext_masked"].tolist()
    model = FakeInferenceModel()
    out = pd.read_parquet(assign_topics(model, texts, tmp_path / "a.parquet", row_index=np.arange(100, 125),
                                        chunk_size=7))
    assert [n for n, _ in model.calls] == [7, 7, 7, 4]
    assert out["row"].tolist() == list(range(100, 125))
    assert out["topic"].tolist() == [len(t) % 3 - 1 for t in texts]
    np.testing.assert_allclose(out["topic_prob"], [len(t) / 100 for t in texts], rtol=1e-6)


def test_export_training_topics(tmp_path):
    d = write_model_files(tmp_path / "m")
    out = pd.read_parquet(export_training_topics(d, [3, 5, 8, 9, 11, 20], tmp_path / "t.parquet"))
    assert out.to_dict("list") == {"row": [3, 5, 8, 9, 11, 20], "topic": TRAIN_TOPICS}
    with pytest.raises(ValueError, match="训练行号"):
        export_training_topics(d, [1, 2], tmp_path / "t2.parquet")


def test_train_pipeline_with_fakes(corpus, tmp_path, monkeypatch):
    encoded = []

    class FakeSentenceTransformer:
        def __init__(self, name):
            self.name = name

        def encode(self, docs, batch_size, show_progress_bar):
            encoded.append(len(docs))
            return np.ones((len(docs), 4), dtype=np.float32)

    monkeypatch.setitem(sys.modules, "sentence_transformers",
                        types.SimpleNamespace(SentenceTransformer=FakeSentenceTransformer))
    fake = FakeTrainedModel()
    monkeypatch.setattr(train_mod, "build_topic_model", lambda spec, embedding_model: fake)

    spec = TopicModelSpec.from_yaml("topic_models/bertopic_ideo_13-23_relaxed.yaml")
    out = tmp_path / "models" / "m"
    train_topic_model(spec, tmp_path / "corpus.pickle", out)
    assert fake.fitted == (12, (12, 4))  # 只用 averageDem 非缺失的 12 条
    assert fake.save_kwargs == {"serialization": "safetensors", "save_ctfidf": True,
                                "save_embedding_model": "sentence-transformers/all-mpnet-base-v2"}
    assert list(np.load(out / "train_row_index.npy")) == list(range(1, 25, 2))
    for f in ["train_meta.json", "train_spec.yaml", "topic_info.csv", "topic_descriptions.xlsx"]:
        assert (out / f).exists(), f
    assert (tmp_path / "models" / "m.embeddings" / "part_00000.npy").exists()  # embedding 缓存在模型目录之外

    with pytest.raises(FileExistsError):
        train_topic_model(spec, tmp_path / "corpus.pickle", out)
    n_encoded = len(encoded)  # 复用缓存的 embedding：不再调用编码器
    train_topic_model(spec, tmp_path / "corpus.pickle", out, embeddings=tmp_path / "models" / "m.embeddings",
                      overwrite=True)
    assert len(encoded) == n_encoded


def test_cli_topic_commands(corpus, tmp_path, monkeypatch):
    import ceo_rd.topics as topics_pkg

    loaded = {}

    def fake_load(model_dir, embedding_model=None):
        loaded["embedding_model"] = embedding_model
        return FakeInferenceModel()

    monkeypatch.setattr(topics_pkg, "load_topic_model", fake_load)
    src = str(tmp_path / "corpus.pickle")
    main(["topics", "infer", "models/x", "--input", src, "--out", str(tmp_path / "td.npz"),
          "--filter-notna", "averageDem", "--chunk-size", "4", "--min-similarity", "0.2"])
    z = np.load(tmp_path / "td.npz")
    np.testing.assert_array_equal(z["row_index"], np.arange(1, 25, 2))
    np.testing.assert_array_equal(z["topic_distr"], fake_distribution(corpus["componenttext_masked"].iloc[1::2].tolist()))

    d = write_model_files(tmp_path / "m")  # config.json 中没有 embedding_model → 使用默认的 all-mpnet-base-v2
    main(["topics", "assign", str(d), "--input", src, "--out", str(tmp_path / "a.parquet")])
    assert loaded["embedding_model"] == "sentence-transformers/all-mpnet-base-v2"
    assert len(pd.read_parquet(tmp_path / "a.parquet")) == 25

    rows = tmp_path / "rows.pickle"
    pd.DataFrame({"componenttext_masked": list("abcdefgh"), "averageDem": [1, None, 1, 1, None, 1, 1, 1]}).to_pickle(rows)
    main(["topics", "training-labels", str(d), "--input", str(rows), "--out", str(tmp_path / "t.parquet")])
    assert pd.read_parquet(tmp_path / "t.parquet")["row"].tolist() == [0, 2, 3, 5, 6, 7]

    main(["topics", "describe", str(d), "--out", str(tmp_path / "desc.xlsx")])
    assert (tmp_path / "desc.xlsx").exists()
    assert "bertopic" not in sys.modules


def test_load_corpus_selected_rows(corpus, tmp_path):
    rows = [20, 3, 7, 4]  # 按给定顺序取行（如复现子样本的 orig_row）
    texts, idx = load_corpus(tmp_path / "corpus.pickle", rows=rows)
    assert list(idx) == rows and texts == corpus["componenttext_masked"].iloc[rows].tolist()
    texts, idx = load_corpus(tmp_path / "corpus.pickle", rows=rows, notna=["averageDem"])
    assert list(idx) == [3, 7]  # 先取行，再按 averageDem 筛选
    with pytest.raises(ValueError, match="超出范围"):
        load_corpus(tmp_path / "corpus.pickle", rows=[0, 25])


def test_read_row_numbers(tmp_path):
    from ceo_rd.topics import read_row_numbers
    np.save(tmp_path / "r.npy", np.array([5, 1]))
    pd.DataFrame({"orig_row": [9, 2], "x": [0, 0]}).to_pickle(tmp_path / "s.pickle")
    assert list(read_row_numbers(tmp_path / "r.npy")) == [5, 1]
    assert list(read_row_numbers(tmp_path / "s.pickle")) == [9, 2]


def test_cli_infer_rows_from_sample(corpus, tmp_path, monkeypatch):
    """--rows-from 复现子样本：输出与子样本逐行对齐，可直接作为 paths.yaml 的 topics 用于 build-panel。"""
    import ceo_rd.topics as topics_pkg

    monkeypatch.setattr(topics_pkg, "load_topic_model", lambda model_dir, embedding_model=None: FakeInferenceModel())
    sample = pd.DataFrame({"is_ceo": True, "orig_row": [2, 11, 5, 24]})
    sample.to_pickle(tmp_path / "transcripts_is_ceo.pickle")
    main(["topics", "infer", "models/x", "--input", str(tmp_path / "corpus.pickle"), "--out", str(tmp_path / "td.npz"),
          "--rows-from", str(tmp_path / "transcripts_is_ceo.pickle")])
    z = np.load(tmp_path / "td.npz")
    assert list(z["row_index"]) == [2, 11, 5, 24]
    np.testing.assert_array_equal(z["topic_distr"],
                                  fake_distribution(corpus["componenttext_masked"].iloc[[2, 11, 5, 24]].tolist()))
