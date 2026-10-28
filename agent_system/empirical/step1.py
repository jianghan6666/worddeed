"""Use saved densities, or call the existing BERTopic inference implementation."""

import json
import hashlib
import zipfile
from pathlib import Path

def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_hash(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                     separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def check_model_identity(model_dir, expected):
    names = ("topics.json", "config.json", "ctfidf_config.json",
             "ctfidf.safetensors", "topic_embeddings.safetensors")
    hashes = {name: sha256_file(model_dir / name) for name in names}
    identity = f"{model_dir.name}:sha256:{stable_hash(hashes)}"
    if identity != expected:
        raise ValueError("Saved model files differ from the catalogue model identity")


def run(config, out):
    import numpy as np
    import pyarrow.parquet as pq

    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    catalogue = Path(config["catalogue"])
    data = json.loads(catalogue.read_text())
    ids = [int(row["topic_id"]) for row in data["topics"]]
    if ids != list(range(354)):
        raise ValueError("This study requires the ordered 354-topic catalogue")
    components = Path(config["step3"]["components"])
    settings = config.get("step1", {})
    mode = settings.get("mode", "saved")
    topics = Path(config["step3"]["topics"])
    if mode == "infer":
        try:
            from ceo_rd.topics.corpus import load_corpus, read_row_numbers
            from ceo_rd.topics.infer import infer_topic_distribution, load_topic_model
        except ImportError as exc:
            raise RuntimeError(
                "step1.mode=infer requires the compatible ceo_rd topic package and "
                "its dependencies installed in the configured Python environment; "
                "use step1.mode=saved for existing density inputs"
            ) from exc
        model_dir = Path(settings["model_dir"])
        check_model_identity(model_dir, data["topic_model_id"])
        # Topic identity must match the catalogue before computing new densities.
        model_info = json.loads((model_dir / "topics.json").read_text())
        actual = {int(i) for i in model_info["topic_representations"] if int(i) >= 0}
        if actual != set(ids):
            raise ValueError("Model topic IDs differ from the fixed catalogue")
        rows = read_row_numbers(settings["rows"]) if settings.get("rows") else None
        texts, row_index = load_corpus(settings["corpus"],
                                      text_column=settings.get("text_column", "componenttext_masked"), rows=rows)
        if len(texts) != pq.ParquetFile(components).metadata.num_rows:
            raise ValueError("Corpus selection and component rows differ")
        component_rows = pq.read_table(components, columns=["orig_row"]).column(0).to_numpy()
        if not np.array_equal(component_rows, row_index):
            raise ValueError("Corpus row order does not match component orig_row")
        topics = out / "topic_distr.npz"
        if not topics.exists():
            infer_topic_distribution(load_topic_model(model_dir), texts, topics, row_index=row_index,
                                     chunk_size=settings.get("chunk_size", 100000), keep_parts=True)
    elif mode != "saved":
        raise ValueError("step1.mode must be saved or infer")
    # Read only the NPZ header; Step 3 streams the 5GB matrix using the supplied loader.
    with zipfile.ZipFile(topics) as archive, archive.open("topic_distr.npy") as stream:
        version = np.lib.format.read_magic(stream)
        reader = np.lib.format.read_array_header_1_0 if version == (1, 0) else np.lib.format.read_array_header_2_0
        shape, fortran, dtype = reader(stream)
    if shape != (pq.ParquetFile(components).metadata.num_rows, 354) or fortran:
        raise ValueError(f"Densities must align with component rows and 354 columns: {shape}")
    if not np.issubdtype(dtype, np.floating):
        raise ValueError("Topic densities must be floating point")
    return {"topics": str(topics.resolve()), "components": str(components.resolve()),
            "catalogue": str(catalogue.resolve()), "topic_model_id": data["topic_model_id"],
            "rows": shape[0], "n_topics": shape[1], "mode": mode,
            "alignment": "delivery-declared historical ordering" if mode == "saved" else "checked orig_row ordering"}
