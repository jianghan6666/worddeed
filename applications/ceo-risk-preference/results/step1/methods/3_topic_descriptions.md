# 3. Topic 描述

354 个 topic 的关键词、名称、规模和代表性发言整理在 Excel 文件中：**[topic_descriptions_354Topics.xlsx](topic_descriptions_354Topics.xlsx)**。

## 3.1 Excel 内容

| 工作表 | 内容 |
|---|---|
| `说明` | 模型概况与各列说明 |
| `Topics` | 每个 topic 一行（共 355 行，含离群类 -1） |
| `Top25_Words` | 每个 topic 按 c-TF-IDF 分数排序的前 25 个词（宽表） |
| `Top25_With_Scores` | 同上，长表，附 c-TF-IDF 分数 |
| `Representative_Docs` | 训练时每个 topic 最有代表性的 3 段发言（人名、公司名已打码） |

`Topics` 表的列：

| 列 | 含义 |
|---|---|
| `Topic` | topic 编号（0–353）。-1 为离群类，即训练时没有被分到任何 topic 的文本，不是一个真正的主题 |
| `Name` | BERTopic 自动生成的名称：编号 + c-TF-IDF 前 4 个词，例如 `0_care_health_health care_medicare` |
| `Label` | **人工命名，目前为空**。模型没有人工起的名称，可以按研究需要填写 |
| `Count` / `Share` | 训练时被分到该 topic 的文本数，以及占全部 887,488 段训练文本的比例 |
| `Top10_cTFIDF` | c-TF-IDF 分数最高的 10 个词（1–2 gram），是 BERTopic 的主要表示 |
| `KeyBERT` | 与 topic embedding 最相似的候选词，语义上更连贯 |
| `MMR` | Maximal Marginal Relevance（diversity=0.3）选出的关键词，在相关性之外兼顾多样性 |

## 3.2 规模最大的 15 个 topic

| Topic | 名称 | 训练文本数 | 占比 | KeyBERT 关键词（前 5 个） |
|---|---|---|---|---|
| 0 | 0_care_health_health care_medicare | 32,216 | 3.6% | managed care, medicare advantage, healthcare, medicare, health systems |
| 1 | 1_aircraft_defense_airline_programs | 17,494 | 2.0% | aerospace, industry, dod, boeing, business |
| 2 | 2_margin_margins_gross_gross margin | 14,994 | 1.7% | gross margin, gross margins, margin improvement, operating margins, operating margin |
| 3 | 3_study_patients_data_trial | 14,943 | 1.7% | chemotherapy, oncology, lung cancer, fda, solid tumors |
| 4 | 4_pricing_price_inflation_price increases | 10,843 | 1.2% | price increases, pricing environment, price increase, cost increases, pricing |
| 5 | 5_clients_funds_fund_equity | 10,434 | 1.2% | investment management, wealth management, investors, investing, liquidity |
| 6 | 6_insurance_underwriting_reinsurance_loss | 8,876 | 1.0% | reinsurance, insurance business, property casualty, insurers, underwriting |
| 7 | 7_energy_solar_transmission_utility | 8,834 | 1.0% | utilities, clean energy, renewables, renewable energy, energy efficiency |
| 8 | 8_guidance_quarter_seasonality_fourth | 8,508 | 1.0% | seasonality, q4, seasonal, quarter year, quarter quarter |
| 9 | 9_expense_expenses_cost_sg | 8,163 | 0.9% | expense growth, operating leverage, operating expenses, expense ratio, expense base |
| 10 | 10_europe_asia_international_countries | 6,896 | 0.8% | emerging markets, asia pacific, economy, europe, emea |
| 11 | 11_restaurant_restaurants_food_brand | 6,143 | 0.7% | new restaurants, franchisees, restaurants, restaurant, franchise |
| 12 | 12_excited_team_pleased_look forward | 5,575 | 0.6% | company, excited future, results quarter, business, looking forward |
| 13 | 13_tenants_lease_leasing_rents | 5,116 | 0.6% | leasing activity, tenants, leases, rent growth, leasing |
| 14 | 14_acquisitions_acquisition_deals_opportunities | 5,075 | 0.6% | acquisitions think, acquisitions, look acquisitions, acquisitions ve, acquisition |

另有离群类 -1：482,860 段，占 54.4%。

topic 大致分三类：
- **行业主题：** 医疗、航空国防、保险、能源、餐饮、房地产租赁等；
- **财务经营主题：** 毛利率、定价、费用、业绩指引、并购等；
- **一般性的表述：** 例如第 12 号"excited / pleased / look forward"。

这也是 R&D 预测中 topics 的预测力有很大一部分来自识别行业的原因，见 [4_rd_prediction.md](4_rd_prediction.md)。

## 3.3 重新生成

```bash
ceo-rd topics describe models/bertopic_ideo_13-23_relaxed_354Topics --out docs/topic_descriptions_354Topics.xlsx
```

- **不需要 BERTopic：** 只读取模型目录中的文件（`topics.json`、c-TF-IDF 矩阵与词表、`topic_info*.csv`）。
- **新训练的模型：** 训练结束时会自动在模型目录里生成同样的 `topic_descriptions.xlsx`。
- **与训练时导出结果的一致性：** 前 25 个词和分数与训练时用 BERTopic 导出的结果一致。只有 2 处分数完全相同的词，先后顺序可能不同。这里分数相同时一律按字母顺序排列。
