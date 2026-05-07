# The Gender Pacing Gap: Analysis of 873,334 Berlin Marathon Runners Reveals Men are Twice as Likely to "Hit the Wall"

> Cluster-scale analysis of 873,334 finishers of the Berlin Marathon (1999–2025), examining sex differences in pacing stability and the prevalence of catastrophic deceleration.

## Status

Manuscript under peer review at *Scientific Reports*.

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

Raw and processed datasets are hosted externally due to GitHub size limits.

- **Zenodo deposit:** [10.5281/zenodo.19342683](https://doi.org/10.5281/zenodo.19342683)
- **Mirror (Google Drive):** [Datasets folder](https://drive.google.com/drive/folders/1Y0EkPjKQy6dtfzkIikwKNX3-B-FI6vfq?usp=drive_link)

| File | Format | Stage | Description |
|------|--------|-------|-------------|
| `Dataset_Berlin_Marathon_1999-2025_original` | CSV | Raw | Web-scraped output (1999–2025) |
| `Dataset_Berlin_Marathon_1999-2025` | Parquet | Optimized | CSV converted for memory efficiency (Step 1 output) |
| `Dataset_Berlin_Cleaned_Analysis_Ready` | Parquet | Cleaned | Nulls removed, time strings parsed, outliers filtered (Step 2 output) |
| `Dataset_Berlin_Features_Engineered` | Parquet | Final | Adds pacing metrics (`pct_slowdown`, `hit_wall`); used by figures (Step 3 output) |

Place files in `data/` to reproduce.

## Analyses

### Primary pipeline

| Notebook | Content |
|----------|---------|
| `notebooks/OTIMIZATION.ipynb` | **Step 1:** memory optimization — convert raw CSV to Parquet (~60% size reduction) |
| `notebooks/CLEANING.ipynb` | **Step 2:** standardize gender encoding, parse HH:MM:SS times to seconds, apply physiological filters |
| `notebooks/MAIN_ANALYSIS.ipynb` | **Step 3:** feature engineering (pacing metrics, "wall" definition), statistical tests (Welch, Mann-Whitney U, Chi², Odds Ratios), figure generation |

Run notebooks in the order above. Outputs feed each other.

### Revision analyses

Additional analyses developed during peer review, with outputs written to `notebooks/results/r1/`:

| Notebook | Content |
|----------|---------|
| `notebooks/r1_logistic_age_controlled.py` | Multivariable logistic regression (sex + age + performance category + sex × age interaction) |
| `notebooks/r1_dedup_sensitivity.py` | Sensitivity analysis on deduplicated subset (composite key: normalized name + age group) |
| `notebooks/r1_pacing_fine_grained.py` | Fine-grained pacing metrics from 5 km splits (CV, inflection, late-deceleration, oscillation, km-30 gradient) |
| `notebooks/r1_age_relative_quintile.py` | Within-cohort sex × age-group quintile re-stratification |
| `notebooks/r1_temporal_trend.py` | 27-year temporal trend (Mann-Kendall + linear regression) |
| `notebooks/r1_threshold_severity.py` | Threshold sensitivity (15%/20%/25%) and graded severity |
| `notebooks/r1_perf_cat_prevalence.py` | Per-category × gender prevalence with odds ratios |
| `notebooks/_r1_common.py` | Shared feature engineering, color palette, save_results helper |
| `notebooks/generate_figures.py` | Idempotent regeneration of Figures 1–5 |
| `notebooks/generate_tables.py` | Idempotent regeneration of supplementary tables (CSV → Markdown) |

## Figures

1. **Figure 1 — Density** (`figures/Figure_1_Density.tiff`) — kernel density estimation of percentage slowdown by gender; visualizes the heavier right tail of male pacing failures
2. **Figure 2 — Stratified prevalence** (`figures/Figure_2_Boxplot.tiff`) — mean percentage slowdown by performance category × gender; gender disparity persists across all five tiers
3. **Figure 3 — Risk** (`figures/Figure_3_Risk_Plot.tiff`) — bar plot of "hitting the wall" prevalence by gender with 95% CIs and odds ratio annotation
4. **Figure 4 — Fine-grained pacing variability** (`figures/Figure_4_Pacing_Variability.tiff`) — five 5 km-split-derived metrics (CV, inflection km, late-deceleration %, oscillation, km-30 gradient) by gender
5. **Figure 5 — Temporal trend** (`figures/Figure_5_Temporal_Trend.tiff`) — wall prevalence by gender across 27 editions (1999–2025) with Mann-Kendall and linear-regression annotations

## Structure

```
.
├── README.md                # This file
├── LICENSE                  # MIT — copyright Nova O2
├── requirements.txt         # Python dependencies
├── notebooks/               # Reproducible analysis pipeline
│   ├── OTIMIZATION.ipynb
│   ├── CLEANING.ipynb
│   ├── MAIN_ANALYSIS.ipynb
│   ├── _r1_common.py
│   ├── r1_*.py              # Revision analyses
│   ├── generate_figures.py
│   ├── generate_tables.py
│   └── results/r1/          # Tabular outputs (CSV + Markdown)
└── figures/                 # Manuscript figures (TIFF + PNG, 300 DPI)
```

Build artefacts (`manuscript/`, `Makefile`, `scripts/`) and large datasets (`data/`) are maintained off-repo. Data is available via the Zenodo deposit linked above.

## Tech

- **Python:** 3.10+
- **Dataset encoding:** UTF-8
- **Separator:** comma
- **Decimal:** period
- **Key packages:** Pandas, NumPy, SciPy, statsmodels, pymannkendall, Matplotlib, Seaborn

## Citation

To be added upon acceptance. For now, please cite this repository:

> Seffrin A., Villiger E., Andrade M.S., Rosemann T., Weiss K., Knechtle B. (2026). *The Gender Pacing Gap: Analysis of 873,334 Berlin Marathon Runners Reveals Men are Twice as Likely to "Hit the Wall"* [Code and figures]. GitHub. https://github.com/Nova-O2/berlin-marathon-wall

## License

MIT — Copyright (c) 2026 Nova O2 Sports Science.
