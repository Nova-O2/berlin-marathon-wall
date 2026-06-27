# Sex Differences in Marathon Pacing: Analysis of 873,000 Berlin Marathon Runners Reveals Men are Twice as Likely to "Hit the Wall"

> Cluster-scale analysis of 873,334 finishers of the Berlin Marathon (1999–2025), examining sex differences in pacing stability and the prevalence of catastrophic deceleration.

## Status

**Published in *Scientific Reports* (2026) 16:19529.** DOI: [10.1038/s41598-026-56334-7](https://doi.org/10.1038/s41598-026-56334-7). Open Access (CC BY 4.0). This repository is the frozen code-and-figures companion to the published article; the version of record is included as [`paper.pdf`](./paper.pdf).

## Authors

- **Aldo Seffrin**¹ — ORCID: 0000-0001-8229-8565
- **Elias Villiger**² — ORCID: 0000-0001-8371-1390
- **Marília Santos Andrade**³ — ORCID: 0000-0002-7004-4565
- **Thomas Rosemann**² — ORCID: 0000-0002-6436-6306
- **Katja Weiss**² — ORCID: 0000-0003-1247-6754
- **Beat Knechtle**²\* — ORCID: 0000-0002-2412-9103

1 — Nova O2 Sports Science, São José dos Campos, Brazil
2 — Institute of Primary Care, University of Zurich, Zurich, Switzerland
3 — Department of Physiology, Federal University of São Paulo, Brazil

\*Corresponding author

## Key Finding

Among 873,334 finishers of the Berlin Marathon (1999–2025), male runners exhibited a twofold higher risk of "hitting the wall" — operationally defined as a ≥20% slowdown in the second half of the race relative to the first — compared with female runners (17.63% vs 9.66%; OR = 2.00, 95% CI 1.97–2.03). After adjustment for age and performance category, the disparity strengthened (adjusted OR = 3.88, 95% CI 3.81–3.94). The gap widened markedly among the fastest runners: in the sub-3h cohort, men were approximately six times more likely to experience catastrophic deceleration than women (1.42% vs 0.23%). Mean percentage slowdown was significantly greater in men across all five performance categories (10.73% ± 11.41% vs 8.34% ± 8.91%; *p* < 0.001).

## Sample

- **n = 873,334** finishers (men: 659,294, 75.5% — women: 214,040, 24.5%)
- **Pacing-valid analytical cohort:** n = 872,670 (excluding 664 finishers without valid half-marathon split data)
- **Deduplicated sensitivity subset:** n = 700,877 (first appearance per composite key of normalized name + age group)
- **Source:** Official BMW Berlin Marathon Results Archive
- **Period:** 27 editions, 1999–2025
- **Inclusion:** chip-timed finishers with valid net finish time and half-marathon split
- **Exclusion:** biologically implausible times (< 1:59:00) or beyond official cutoff (> 6:15:00); records missing critical pacing checkpoints. Total excluded: 7,445 records (0.85% of 880,779 raw entries)
- **Age distribution:** mature cohort; ~50% of the field aged 35–49

## Data

Only the **raw dataset** (the single CSV below) is archived externally due to GitHub size limits. Every processed and derivative file — including the analytical baseline `wall_baseline_873k.parquet` — is **regenerated from that CSV** by the pipeline (see Analyses), so nothing else needs to be downloaded.

- **Zenodo deposit (raw CSV, citable archive):** [10.5281/zenodo.19342683](https://doi.org/10.5281/zenodo.19342683)

### Initial pipeline files (intermediate, regenerated)

| File | Format | Stage | Description |
|------|--------|-------|-------------|
| `Dataset_Berlin_Marathon_1999-2025_original.csv` | CSV | Raw | Web-scraped output (1999–2025); the archived Zenodo file |
| `Dataset_Berlin_Marathon_1999-2025.parquet` | Parquet | Optimized | CSV converted for memory efficiency (Step 1 output) |
| `Dataset_Berlin_Cleaned_Analysis_Ready.parquet` | Parquet | Cleaned | Nulls removed, time strings parsed, outliers filtered (Step 2 output) |
| `Dataset_Berlin_Features_Engineered.parquet` | Parquet | Final | Adds pacing metrics (`pct_slowdown`, `hit_wall`) (Step 3 output) |

### Revision-round derivative files

| File | Format | Description |
|------|--------|-------------|
| `wall_baseline_873k.parquet` | Parquet | Analytical cohort (n = 873,334 finishers; raw checkpoints + age_group + sex + year). **Built from the raw CSV** by `notebooks/build_wall_baseline.py`; input to the R1/R2 analyses |
| `dedup_subset.parquet` | Parquet | Deduplicated subset (n = 700,877; first appearance per composite key of normalized name + age group), produced by `notebooks/r1_dedup_sensitivity.py` and consumed by `r1_logistic_age_controlled.py` |

Both derivative files regenerate from the raw CSV — `wall_baseline_873k.parquet` via `build_wall_baseline.py`, then `dedup_subset.parquet` via `r1_dedup_sensitivity.py`.

To reproduce: download the raw CSV from Zenodo into `data/`, then build the analytical baseline with `python notebooks/build_wall_baseline.py` (see Analyses for the full run order). The `data/` directory is gitignored.

## Analyses

### Reproducing the published results

The published statistics and figures use the **analytical cohort of n = 873,334** (`wall_baseline_873k.parquet`). From the raw Zenodo CSV in `data/`:

```bash
python notebooks/build_wall_baseline.py         # raw CSV -> data/wall_baseline_873k.parquet (n = 873,334)
python notebooks/r1_dedup_sensitivity.py        # -> data/dedup_subset.parquet (run before the logistic script)
python notebooks/r1_logistic_age_controlled.py  # adjusted OR; then run the remaining r1_* and r2_* scripts
python notebooks/generate_figures.py            # Figures 1-5
```

`generate_figures.py` and the `r1_*`/`r2_*` scripts operate on `wall_baseline_873k.parquet` and produce the published numbers (e.g. men 17.63% vs women 9.66% hitting the wall; crude OR 2.00; adjusted OR 3.88).

### Initial pipeline (data preparation & exploratory analysis)

| Notebook | Content |
|----------|---------|
| `notebooks/OTIMIZATION.ipynb` | **Step 1:** memory optimization — convert raw CSV to Parquet (~60% size reduction) |
| `notebooks/CLEANING.ipynb` | **Step 2:** standardise sex encoding, parse HH:MM:SS times to seconds, apply physiological filters |
| `notebooks/MAIN_ANALYSIS.ipynb` | **Step 3:** feature engineering (pacing metrics, "wall" definition), statistical tests (Welch, Mann-Whitney U, Chi², Odds Ratios) |

These notebooks document the initial exploratory analysis; the final published cohort and statistics come from the `wall_baseline` pipeline above.

### Revision analyses

Additional analyses developed during peer review, with outputs written to `notebooks/results/r1/` (R1 round) and `notebooks/results/r2/` (R2 round).

#### R1 round (first-round comments)

| Notebook | Content |
|----------|---------|
| `notebooks/r1_logistic_age_controlled.py` | Multivariable logistic regression (sex + age + performance category + sex × age interaction) |
| `notebooks/r1_dedup_sensitivity.py` | Sensitivity analysis on deduplicated subset (composite key: normalized name + age group) |
| `notebooks/r1_pacing_fine_grained.py` | Fine-grained pacing metrics from 5 km splits (CV, inflection, late-deceleration, oscillation, km-30 gradient) |
| `notebooks/r1_age_relative_quintile.py` | Within-cohort sex × age-group quintile re-stratification |
| `notebooks/r1_temporal_trend.py` | 27-year temporal trend (Mann-Kendall + linear regression) |
| `notebooks/r1_threshold_severity.py` | Threshold sensitivity (15%/20%/25%) and graded severity |
| `notebooks/r1_perf_cat_prevalence.py` | Per-category × sex prevalence with odds ratios |
| `notebooks/_r1_common.py` | Shared feature engineering, colour palette, save_results helper |

#### R2 round (Reviewer 2 second-round diagnostics)

| Notebook | Content |
|----------|---------|
| `notebooks/r2_logistic_diagnostics.py` | Logistic model diagnostics — Variance Inflation Factors, McFadden pseudo-R², AIC/BIC, decile calibration with Hosmer-Lemeshow, 10-fold cross-validated recalibration intercept and slope, comparison of linear / quadratic / natural-cubic-spline parameterisations of age (likelihood-ratio + ΔAIC), Pregibon dbeta influence summary, missing-data exclusion cascade. Verbatim summary reproduced in Appendix A of the R2 response letter. |
| `notebooks/_r2_common.py` | R2 shared helpers — `compute_vif`, `mcfadden_r2`, `decile_calibration`, `hosmer_lemeshow`, `spline_basis_age` (with sum-to-zero constraint avoiding rank-deficiency against the intercept), `calibration_in_the_large_and_slope_cv` (10-fold cross-validated, non-degenerate). |

#### Build helpers

| Notebook | Content |
|----------|---------|
| `notebooks/generate_figures.py` | Idempotent regeneration of Figures 1–5 |
| `notebooks/generate_tables.py` | Idempotent regeneration of Table 2 (with crude OR + 95% CI columns added in R2) and Supplementary Tables S1–S6 (CSV → Markdown) |

## Figures

1. **Figure 1 — Density** (`figures/Figure_1_Density.tiff`) — kernel density estimation of percentage slowdown by sex; visualises the heavier right tail of male pacing failures
2. **Figure 2 — Stratified prevalence** (`figures/Figure_2_Boxplot.tiff`) — mean percentage slowdown by performance category × sex; the sex disparity persists across all five tiers
3. **Figure 3 — Risk** (`figures/Figure_3_Risk_Plot.tiff`) — bar plot of "hitting the wall" prevalence by sex with 95% CIs and odds ratio annotation
4. **Figure 4 — Fine-grained pacing variability** (`figures/Figure_4_Pacing_Variability.tiff`) — five 5 km-split-derived metrics (CV, inflection km, late-deceleration %, oscillation, km-30 gradient) by sex
5. **Figure 5 — Temporal trend** (`figures/Figure_5_Temporal_Trend.tiff`) — wall prevalence by sex across 27 editions (1999–2025) with Mann-Kendall and linear-regression annotations

## Structure

```
.
├── README.md                # This file
├── paper.pdf                # Version of record (Sci Rep 2026; CC BY 4.0)
├── LICENSE                  # MIT — copyright Nova O2 (code/figures only)
├── requirements.txt         # Python dependencies (pinned)
├── notebooks/               # Reproducible analysis pipeline
│   ├── OTIMIZATION.ipynb
│   ├── CLEANING.ipynb
│   ├── MAIN_ANALYSIS.ipynb
│   ├── build_wall_baseline.py       # raw CSV -> wall_baseline_873k.parquet
│   ├── _r1_common.py
│   ├── r1_*.py              # R1 revision analyses
│   ├── _r2_common.py
│   ├── r2_logistic_diagnostics.py   # R2 revision diagnostics
│   ├── generate_figures.py
│   ├── generate_tables.py
│   └── results/
│       ├── r1/              # R1 tabular outputs (CSV + Markdown)
│       └── r2/              # R2 tabular outputs (CSV + Markdown + calibration TIFF)
└── figures/                 # Manuscript figures (TIFF + PNG, 300 DPI)
```

Build artefacts (`manuscript/`, `Makefile`, `scripts/`) and large datasets (`data/`) are maintained off-repo. Data is available via the Zenodo deposit linked above.

## Tech

- **Python:** 3.12 (pinned dependencies in `requirements.txt`)
- **Raw dataset:** UTF-8, semicolon-separated, period decimal
- **Key packages:** pandas, NumPy, SciPy, statsmodels, scikit-learn, pymannkendall, Matplotlib, Seaborn, tabulate

## Citation

> Seffrin, A., Villiger, E., Andrade, M. S., Rosemann, T., Weiss, K., & Knechtle, B. (2026). Sex differences in marathon pacing: analysis of 873,000 Berlin marathon runners reveals men are twice as likely to "hit the wall". *Scientific Reports, 16*, 19529. https://doi.org/10.1038/s41598-026-56334-7

**Dataset:** BMW Berlin Marathon Results 1999–2025. Zenodo. https://doi.org/10.5281/zenodo.19342683

## Published article

The version of record is included in this repository as [`paper.pdf`](./paper.pdf), reproduced under its Creative Commons Attribution 4.0 (CC BY 4.0) license. © The authors.

## License

- **Code, notebooks, and figures:** MIT — Copyright (c) 2026 Nova O2 Sports Science (see [`LICENSE`](./LICENSE)).
- **`paper.pdf` (version of record):** © The authors, licensed [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) as published by *Scientific Reports*. Not covered by the MIT license.
