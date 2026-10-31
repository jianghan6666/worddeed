# Full results: the four-step AI Microfoundation Proxy application

The completed results are now available as a separate reviewer deliverable.

- **Read:** [nine-page PDF report](results/report.pdf), or download/open the [HTML report](results/report.html).
- **Inspect judgments:** [searchable topic-by-topic readers](results/step2/explorers/index.html), covering all twelve trials, both stages, primary and supplementary results. Download/open the HTML pages locally; GitHub displays HTML source.
- **Download everything:** [full results release](https://github.com/joyzhzh/ai-microfoundation-proxy/releases/tag/full-results-2026-10-31). The ZIP includes the browsable results plus all literal reader evidence, seals, recoveries and provenance.
- **Navigate the original outputs:** [complete file guide](results/README.md).

| Step | Full results included |
|---|---|
| 1. Narrative representation | 354-topic catalogue; original topic information, descriptions and keywords workbooks; model configuration and saved topic metadata; training/inference method records |
| 2. Relevance screening | All twelve trials; all 24 primary/supplementary handoffs; complete analysis tables; all 95 distinct indexed reader records; searchable reasons, evidence quotations and minority judgments; original literal evidence in the ZIP |
| 3. Behavioral prediction | All 29,506 firm-year scores in CSV and Parquet; both model families and score transformations; complete fold metrics; all six supplied robustness runs; method documentation |
| 4. Downstream assessment | All 25 model specifications; all 1,799 coefficient rows; sample and fit diagnostics; original complete workbook and full tables; the separate 16-score-model workbook; used-sample records and historical checks |

These are the existing completed study results, not a new empirical rerun. The separate replication package supplies inputs, executable reproduction and newly executed verification. The report clearly distinguishes historical topic-density provenance, screening agreement, predictive performance, associations and construct validity.

## Download and verify

With access to this private repository:

```sh
gh release download full-results-2026-10-31 \
  --repo joyzhzh/ai-microfoundation-proxy \
  --pattern 'nbm-full-results-2026-10-31.zip' \
  --pattern 'nbm-full-results-2026-10-31.zip.sha256' \
  --dir results-download
```

The frozen results ZIP keeps its original internal layout. Verify its SHA-256 sidecar, unzip it, and open `results/report.html` or `results/report.pdf` inside the extracted package. The topic browsers work offline. From that extracted package root, run:

```sh
python3 results/verify.py
```

In a current repository clone, run from the repository root instead:

```sh
python3 applications/ceo-risk-preference/results/verify.py
```

Both commands verify the same preserved results. The full ZIP additionally contains and checks every expanded reader-evidence file. No model calls, Stata, or empirical training are needed to inspect the findings.
