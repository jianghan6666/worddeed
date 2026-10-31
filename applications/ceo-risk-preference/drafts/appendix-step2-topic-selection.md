# Draft: Section 2 "Topic Selection" for the technical appendix

*Drafted 31 October 2026 for review by the seat that executed Step 2. This is a handoff copy, not a scientific record. Delete or move it once the appendix absorbs or replaces it.*

The appendix (`Technical_Appendix_Steps_1_3_4_Oct29_v2.docx`) has sections 1, 3 and 4 written and a placeholder for section 2. The text below fills that placeholder in the appendix's own voice (first person plural, author–year citations, no table). Every number is taken from the delivered Step 2 record in this repository:

- [results/step2/MEMO.md](../results/step2/MEMO.md): task, procedure, executed design, principal findings, completeness.
- [summary/screening-counts.csv](../summary/screening-counts.csv): per-trial selected, excluded and unresolved counts.
- [results/step2/TRIAL_INDEX.csv](../results/step2/TRIAL_INDEX.csv): primary and supplementary counts per trial.
- [README.md](../README.md), section 2: the trial that fed Step 3 (`b1-gpt-6-astra-P0-xhigh`, repetition 1, 321 selected / 33 excluded / 0 unresolved).

## Added to the overview paragraph

After "Stage 1 extracts topics from conference-call text." insert:

> Stage 2 screens those topics for relevance to managerial risk preference using independent language-model readers.

The current overview skips from Stage 1 to Stage 3.

## 2 Topic Selection

Stage 2 screens the 354 topics for relevance to managerial risk preference before they enter the supervised mapping in Stage 3. For this purpose, risk preference is defined as a willingness to accept or avoid uncertainty and possible downside in organizational choices. A topic is relevant when its descriptors or source passages contain direct discussion of risk taking, caution, or avoidance, or a supported risk-related decision scenario such as investment and R&D, acquisitions, new ventures, financing and leverage, or deliberate risk management. Topics that mainly describe an industry, product, geography, routine reporting, or general business conditions are irrelevant when the evidence does not support such a state or decision; a risk common to every business activity is not sufficient. The screening task is binary relevance. It does not assign a risk direction, score sentiment, or infer any individual CEO’s preference.

Each screening trial uses three independent readers, each a separate large-language-model session with the same assigned model and reasoning-effort setting, and a coordinator that releases materials and assembles outputs but casts no vote. Screening proceeds in two stages within each reader’s own session. In Stage A, each reader classifies all 354 topics from the topic name and 15 ranked keywords alone, recording a label, a topic-specific rationale, one to five cited keywords, and an ordinal confidence level. All three Stage A responses are sealed, or recorded as missing, before any source text is released. In Stage B, the same reader reviews every topic, including those initially labeled irrelevant, against three saved representative earnings-call passages per topic (1,062 topic–passage entries), presented in a fixed order across 18 pages. The reader records whether the passages support the interpretation of the topic, retains or revises its label with cited keyword and passage evidence, and reports a fresh confidence level. Readers never see one another’s judgments, earlier pilot labels, behavioral outcomes, or model performance.

A topic’s final label in a trial is determined by an unweighted two-of-three majority of the readers’ Stage B labels. Confidence does not weight votes, Stage A labels do not supply fallback votes, and a topic without two matching resolved Stage B labels is recorded as unresolved. Each trial exports the final labels with all three reader votes, the selected, excluded, and unresolved topic identifiers, and the separate Stage A labels for comparison. Literal rationales, cited evidence, confidence reports, and minority positions are preserved for every reader rather than discarded in aggregation (Mostafazadeh Davani, Díaz, and Prabhakaran, 2022). Original submissions form the primary analysis; indexed recoveries of failed or malformed page saves form a supplementary analysis.

The completed screening comprises 12 trials, or 36 readers: two requested model families (GPT-6.1 Sol and GPT-6 Astra), three reasoning-effort settings (medium, high, and extra-high), and two repetitions with fresh reader sessions per configuration. All 12 trials used the same catalogue, codebook, prompt, source passages, page order, and voting rule; the requested model and effort were the only varied factors. A larger design crossing seven prompt strategies was planned, but admission was held after the first 12 direct-prompt trials because of cost, and the 12-trial scope was ratified after collection. Prompt-strategy effects therefore remain untested. All 36 readers completed both stages. Stage A selected 66–87 of the 354 topics (18.6–24.6%) across trials; Stage B selected 313–321 (88.4–90.7%). Among 4,247 jointly resolved majority comparisons, 2,964 (69.8%) changed between stages, 2,928 from irrelevant to relevant and 36 from relevant to irrelevant. Across the 12 primary final selections, 306 topics were always selected, 31 were always excluded, and 17 varied. Within each model–effort cell, the two repetitions agreed on 98.1–98.9% of final labels. Primary Stage B records contain 12,624 of the 12,744 intended judgments; 120 are missing after six failed or malformed page saves across five readers, and one majority in one trial is unresolved. Supplementary recovery completes all 12,744 judgments and resolves the remaining topic without changing any other trial’s selection count.

Stage 3 uses the primary selection from the first GPT-6 Astra extra-high trial, which selected 321 topics and excluded 33, with no unresolved topic. This fixes the 321 topic features described in Section 3.3. The trial was adopted as the operational selection; the screening study did not establish that this configuration was superior to the alternatives, and the 17 topics that vary across trials indicate the sensitivity of the selection to the reading procedure. The broadening from Stage A to Stage B is the dominant pattern. It can reflect information in passages that keywords omit, or inclusion on the basis of incidental decisions within long, mixed-content passages; the data do not separate these explanations or establish that the reviewed labels are more accurate. High repeat agreement measures the repeatability of the procedure, not accuracy against an independent reference (Gilardi, Alizadeh, and Kubli, 2023), and no human-reference validation of the selected topics has been completed.

## References to add

Gilardi, F., Alizadeh, M., and Kubli, M. (2023). ChatGPT outperforms crowd workers for text-annotation tasks. Proceedings of the National Academy of Sciences, 120(30), e2305016120. https://doi.org/10.1073/pnas.2305016120

Mostafazadeh Davani, A., Díaz, M., and Prabhakaran, V. (2022). Dealing with disagreements: Looking beyond the majority vote in subjective annotations. Transactions of the Association for Computational Linguistics, 10, 92–110. https://doi.org/10.1162/tacl_a_00449

## Notes for the reviewer

- No Step 2 table is proposed, because the appendix numbers its tables A1–A13 in order of mention and a table here would renumber all of them. If a table is wanted, the natural content is the 12-row selection-count table from the memo (Stage A and Stage B selected counts by model, effort and repetition).
- "Extra-high" renders the `xhigh` effort setting; change if the paper uses another spelling.
- Model names follow the memo ("GPT-6.1 Sol", "GPT-6 Astra"). Requested settings do not attest backend versions, as the memo notes.
- Percentages were computed from the counts: 66/354 = 18.6%, 87/354 = 24.6%, 313/354 = 88.4%, 321/354 = 90.7%, 2,964/4,247 = 69.8%.
- A filled copy of the appendix exists outside the repository as `Technical_Appendix_Steps_1_2_3_4_Oct31_v3.docx`; the paragraphs above are identical to it.
