# Step 2 mini-experiment: descriptive comparison

All 12 planned conditions and 354 topics were retained. Each condition contains three fresh initial reader records and a two-of-three majority. Prompt, ordered catalogue, assignments, observed model settings, original votes, manifests and exported majorities were checked before comparison.

One ensemble was observed per condition. Its three readers are within-condition repetitions, not three independent ensemble replications. The comparisons describe this fixed catalogue; they do not identify an accuracy winner, a causal model/effort effect or construct validity. There are no human-reference labels, and higher inclusion or agreement is not evidence of better measurement.

Condition 01 already completed before this expansion was requested; remaining 11 conditions planned before their launch. This is not a prospective registration of condition 01.

## Condition results

| Condition | Relevant | Irrelevant | Unresolved | Unanimous 3/3 | Split 2/3 | Reader selections A/B/C |
|---|---:|---:|---:|---:|---:|---|
| 01-mixed-high | 71 | 283 | 0 | 303 | 51 | 77/44/85 |
| 02-mixed-xhigh | 79 | 275 | 0 | 315 | 39 | 86/88/74 |
| 03-mixed-medium | 77 | 277 | 0 | 292 | 62 | 87/98/62 |
| 04-sol61-medium | 78 | 276 | 0 | 319 | 35 | 71/90/80 |
| 05-sol61-high | 66 | 288 | 0 | 332 | 22 | 78/62/66 |
| 06-sol61-xhigh | 84 | 270 | 0 | 328 | 26 | 74/86/86 |
| 07-sol6-medium | 54 | 300 | 0 | 295 | 59 | 97/46/52 |
| 08-sol6-high | 75 | 279 | 0 | 319 | 35 | 77/73/68 |
| 09-sol6-xhigh | 73 | 281 | 0 | 322 | 32 | 76/69/68 |
| 10-astra-medium | 74 | 280 | 0 | 333 | 21 | 66/76/75 |
| 11-astra-high | 79 | 275 | 0 | 341 | 13 | 78/77/81 |
| 12-astra-xhigh | 95 | 259 | 0 | 329 | 25 | 87/96/93 |

A split means all three votes are resolved and divide 2–1. Two matching votes plus a missing third can still decide a topic, but are counted separately in `condition_summary.csv`. Failed and abstained votes are never treated as irrelevant.

## Stability across twelve conditions

Always selected: **42**. Always excluded: **241**. Variable with all twelve labels resolved: **71**. At least one unresolved label: **0**.

These four groups partition the full roster. A topic with missing labels remains in the unresolved group even when its observed labels differ; `observed_label_variation` preserves that distinction. The complete 12-label matrix is `topic_comparison.csv`.

## Pairwise comparisons

`pairwise_comparisons.csv` contains all 66 pairs. Mismatch rates divide mismatches by jointly resolved topics. Jaccard is the relevant-set intersection divided by its union within that same jointly resolved universe. An empty relevant union has undefined Jaccard, recorded as JSON null / an empty CSV cell; it is not automatically perfect agreement. No jointly resolved topics also yields undefined rates. Missingness counts and denominators accompany every pair.

Observed pairwise mismatch rates range from 2.54% to 16.10%; all ties and denominators remain in the CSV.

## Topics with greatest observed variation

Ranked by the number of differently labeled condition pairs among topics resolved in all twelve conditions. The list shows the first twenty topics including all ties at the cutoff, or all variable topics if fewer. This is a descriptive review queue, not evidence that either label is correct. Full reasons and minority votes remain in each linked original.

| Topic ID | Name | Selected / 12 | Differing pairs / 66 | Keywords |
|---|---|---:|---:|---|
| 101 | 101_gene_gene therapy_pompe_therapy | 6 | 36 | gene, gene therapy, pompe, therapy, disease, enzyme, patients, rare, diseases, study, medicine, programs, editing, therapies, genetic |
| 162 | 162_oil_drilling_production_basin | 6 | 36 | oil, drilling, production, basin, wells, delaware, eagle ford, eagle, ford, acreage, plays, production growth, returns, permian, resource |
| 350 | 350_alarm_recurring revenue_recurring_security | 6 | 36 | alarm, recurring revenue, recurring, security, access control, school, dealers, locking, starlink, intrusion, schools, connected home, access, locks, control |
| 44 | 44_copper_gold_mining_mines | 7 | 35 | copper, gold, mining, mines, silver, production, ounces, ore, coal, underground, grade, exploration, pit, cash, project |
| 73 | 73_depression_sage_ppd_217 | 7 | 35 | depression, sage, ppd, 217, patients, drug, treatment, study, depressive, schizophrenia, brain, disorders, symptoms, studies, data |
| 99 | 99_biosimilars_biosimilar_humira_patents | 5 | 35 | biosimilars, biosimilar, humira, patents, patent, payers, market, oncology, generics, launch, ip, competition, generic, erosion, products |
| 103 | 103_rate case_case_rate_commission | 7 | 35 | rate case, case, rate, commission, rate cases, filing, file, cases, test year, settlement, file rate, regulatory, lag, filed, regulatory lag |
| 115 | 115_supply chain_chain_supply_suppliers | 7 | 35 | supply chain, chain, supply, suppliers, lead times, issues, shortages, constraints, lead, challenges, chain issues, times, inventory, components, supplier |
| 182 | 182_hurricane_storm_hurricanes_damage | 7 | 35 | hurricane, storm, hurricanes, damage, florida, storms, impact, houston, harvey, flooding, flood, sandy, impacted, affected, irma |
| 184 | 184_advertising_spend_marketing_marketing spend | 7 | 35 | advertising, spend, marketing, marketing spend, ad, spending, media, advertising spend, ad spend, brand, dollars, tv, roi, percentage, campaign |
| 210 | 210_enzymes_enzyme_protein_merck | 7 | 35 | enzymes, enzyme, protein, merck, pharmaceutical, protein engineering, dna, manufacturing, novel, gsk, biotherapeutics, engineering, drug, food, molecular |
| 216 | 216_carbon_climate_emissions_climate change | 7 | 35 | carbon, climate, emissions, climate change, net zero, zero, greenhouse, energy, greenhouse gas, scope, reduce, change, paris, gas emissions, net |
| 236 | 236_cardiomyopathy_onpattro_patients_study | 5 | 35 | cardiomyopathy, onpattro, patients, study, apollo, disease, hereditary, wild type, neuropathy, wild, stabilizer, cardiac, label, treatment, drug |
| 272 | 272_natural gas_natural_gas_gas liquids | 5 | 35 | natural gas, natural, gas, gas liquids, liquids, ngl, partners, fee based, gathering processing, processing, gathering, partnership, williston, gathered, growth projects |
| 297 | 297_lupus_patients_disease_autoimmune | 5 | 35 | lupus, patients, disease, autoimmune, type diabetes, study, diabetes, jak, steroid, therapy, mf, stage, potential, inhibitor, dose |
| 347 | 347_kinder_kinder morgan_kmi_morgan | 5 | 35 | kinder, kinder morgan, kmi, morgan, trans, mountain, natural gas, gas, natural, terminals, project, co2, assets, segment, expansion |
| 26 | 26_loan_deposit_loan growth_banking | 4 | 32 | loan, deposit, loan growth, banking, loans, bank, income, credit, mortgage, net, deposits, quarter, net income, lending, growth |
| 30 | 30_security_cloud_firewall_wan | 8 | 32 | security, cloud, firewall, wan, sd wan, sd, network, network security, threat, cybersecurity, vulnerability, solution, endpoint, secure, platform |
| 48 | 48_loan_mortgage_loan growth_loans | 4 | 32 | loan, mortgage, loan growth, loans, lenders, growth, quarter, lending, mortgage business, little, bit, little bit, pipeline, purchase, seeing |
| 52 | 52_biotech_pharma_discovery_biopharma | 8 | 32 | biotech, pharma, discovery, biopharma, science, research, clients, life, growth, life science, companies, strong, drug, business, pharma biotech |
| 165 | 165_identity_okta_customer identity_cloud | 4 | 32 | identity, okta, customer identity, cloud, security, auth0, access, workforce, customer, access management, governance, platform, saas, authentication, customers |
| 191 | 191_hemophilia_factor_factor viii_viii | 4 | 32 | hemophilia, factor, factor viii, viii, bleeding, patients, gene, therapy, gene therapy, ix, recombinant, knockdown, phase, data, disorders |
| 274 | 274_rfid_rain_premises_loss prevention | 8 | 32 | rfid, rain, premises, loss prevention, checkout, items, retailers, item, readers, ic, reader, retail, visibility, prevention, federal |
| 284 | 284_royalty_royalties_licensing_license | 4 | 32 | royalty, royalties, licensing, license, ip, royalty rate, royalty stream, licenses, deals, licensee, royalty rates, agreement, royalties think, patent, think |
| 332 | 332_niagen_tru_science_research | 8 | 32 | niagen, tru, science, research, aging, studies, ingredient, dietary, published, precursors, health, scientific, dietary supplement, cellular, preclinical |

## Original records

Use each topic ID to locate its entry in the decisions and initial reader JSON files. `input_index.json` contains all original file references and manifest hashes; `highest_variability_topics.json` provides the explicit topic-to-original references.

- [01-mixed-high original decisions](../../results/2026-10-19-three-models/details/decisions.json)
- [02-mixed-xhigh original decisions](../runs/02-mixed-xhigh/details/decisions.json)
- [03-mixed-medium original decisions](../runs/03-mixed-medium/details/decisions.json)
- [04-sol61-medium original decisions](../runs/04-sol61-medium/details/decisions.json)
- [05-sol61-high original decisions](../runs/05-sol61-high/details/decisions.json)
- [06-sol61-xhigh original decisions](../runs/06-sol61-xhigh/details/decisions.json)
- [07-sol6-medium original decisions](../runs/07-sol6-medium/details/decisions.json)
- [08-sol6-high original decisions](../runs/08-sol6-high/details/decisions.json)
- [09-sol6-xhigh original decisions](../runs/09-sol6-xhigh/details/decisions.json)
- [10-astra-medium original decisions](../runs/10-astra-medium/details/decisions.json)
- [11-astra-high original decisions](../runs/11-astra-high/details/decisions.json)
- [12-astra-xhigh original decisions](../runs/12-astra-xhigh/details/decisions.json)

No prompt was retuned from these results, no preferred condition is selected automatically, and no density × sentiment score is calculated here. Condition choice and any later human-reference validation remain separate decisions.
