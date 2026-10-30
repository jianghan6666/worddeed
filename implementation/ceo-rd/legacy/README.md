# 重构前的独立脚本与 notebook（仅供参考）

这些脚本已由 `ceo_rd` 包与 `experiments/*.yaml` 取代，结果已验证一致：

| 旧脚本 | 现在 |
|---|---|
| `build_panel.py` | `ceo-rd build-panel` |
| `train_models.py` | `ceo-rd run experiments/main.yaml` |
| `robustness_controls.py` | `ceo-rd run experiments/strict_controls.yaml` |
| `robustness_ceo_demo.py` | `ceo-rd run experiments/ceo_demo.yaml` |
| `robustness_sentiment.py` | `ceo-rd run experiments/sentiment.yaml` |

注意：新面板已直接包含 CEO 特征与情绪列，`robustness_ceo_demo.py` 和 `robustness_sentiment.py` 在新面板上会因重复列而无法运行。

## notebooks/

| notebook | 内容 |
|---|---|
| `bertopic_new_text_modelling_ideoOnly_13-23_version-Updated2026Jul3-FinallyUsed (1).ipynb` | 训练现有 BERTopic 模型 `bertopic_ideo_13-23_relaxed_354Topics`，并推断全部文本的 topic 分布（2026-07-03，bertopic 0.16.4）。已由 `ceo-rd topics train / infer / describe` 和 `topic_models/bertopic_ideo_13-23_relaxed.yaml` 取代 |
| `topic_modeling_revised.ipynb` | 读取含文本的 pickle 并查看列 |

notebook 里的相对路径（`./bertopic_ideo_13-23_relaxed_354Topics`、`./all-mpnet-base-v2`、原 CSV）是原机器上的位置，在这里不能直接运行。
