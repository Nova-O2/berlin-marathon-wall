# The Gender Pacing Gap: Analysis of 873,000 Berlin Marathon Runners Reveals Men are Twice as Likely to "Hit the Wall"

> Cluster-scale analysis of 873,334 finishers of the Berlin Marathon (1999–2025), examining sex differences in pacing stability and the prevalence of catastrophic deceleration.

## Status

- **Status:** 🔥
- **Próximo passo:** Phase 11.3 (plan execution) + Phase 11.4 kickoff (analysis) — seg 11/05 09-13h
- **Trigger:** Calendar event Phase 11.3+11.4 kil3opopssd6i404bi5u8r7fa0
- **Updated:** 2026-05-07
- **OKR:** 3.2

### Pesquisa
- **Phase:** 11.3 (R1 plan; 11.2 triage ✅ 2026-05-07: 13 ✅ apply + 1 💬 modify)
- **Submission ID:** abcd56f1-e286-4e03-9844-d3734e705384
- **Journal:** Scientific Reports
- **Round:** R1

## Authors

- **Aldo Seffrin**¹ — netoseffrin@gmail.com — ORCID: 0000-0001-8229-8565
- **Elias Villiger**² — ORCID: 0000-0001-8371-1390
- **Marília Santos Andrade**³ — ORCID: 0000-0002-7004-4565
- **Thomas Rosemann**² — ORCID: 0000-0002-6436-6306
- **Katja Weiss**² — ORCID: 0000-0003-1247-6754
- **Beat Knechtle**²\* — beat.knechtle@hispeed.ch — ORCID: 0000-0002-2412-9103

1 — Nova O2 Sports Science, São José dos Campos, Brazil
2 — Institute of Primary Care, University of Zurich, Zurich, Switzerland
3 — Department of Physiology, Federal University of São Paulo, Brazil

\*Corresponding author

## Key Finding

Among 873,334 finishers of the Berlin Marathon (1999–2025), male runners exhibited a twofold higher risk of "hitting the wall" — operationally defined as a ≥20% slowdown in the second half of the race relative to the first — compared with female runners (17.61% vs 9.66%; OR = 2.00, 95% CI 1.97–2.03). The disparity widened markedly among the fastest runners: in the sub-3h cohort, men were 6.06 times more likely to experience catastrophic deceleration than women (1.42% vs 0.23%). Mean percentage slowdown was significantly greater in men across all five performance categories (Cohen's *d* = 0.22 globally; *p* < 0.001 by Welch's t-test and Mann-Whitney U).

## Sample

- **n = 873,334** finishers (men: 659,294, 75.5% — women: 214,040, 24.5%)
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

| Notebook | Content |
|----------|---------|
| `notebooks/OTIMIZATION.ipynb` | **Step 1:** memory optimization — convert raw CSV to Parquet (~60% size reduction) |
| `notebooks/CLEANING.ipynb` | **Step 2:** standardize gender encoding, parse HH:MM:SS times to seconds, apply physiological filters |
| `notebooks/MAIN_ANALYSIS.ipynb` | **Step 3:** feature engineering (pacing metrics, "wall" definition), statistical tests (Welch, Mann-Whitney U, Chi², Odds Ratios), figure generation |

Run notebooks in the order above. Outputs feed each other.

## Figures

1. **Figure 1 — Density** (`figures/Figure_1_Density.tiff`) — kernel density estimation of percentage slowdown by gender; visualizes the heavier right tail of male pacing failures
2. **Figure 2 — Risk** (`figures/Figure_3_Risk_Plot.tiff`) — bar plot of "hitting the wall" prevalence by gender; OR = 2.00 (95% CI 1.97–2.03)
3. **Figure 3 — Stratified** (`figures/Figure_2_Boxplot.tiff`) — mean percentage slowdown by performance category × gender; gender disparity persists across all five tiers

## Suggested Reviewers

To be provided at submission.

## Pending

- [ ] Phase 11.3: convert R1 triage decisions into actionable execution plan
- [ ] Phase 11.4: implement new analyses (multivariable logistic with age + sex × age interaction; dedup sensitivity; fine-grained pacing metrics; within-Berlin sex × age_group quintile re-stratification; 27-year temporal trend)
- [ ] Phase 11.5: apply manuscript edits (behavioural framing hedging across 14 trechos; threshold sensitivity; Conclusions rewrite)
- [ ] Phase 11.6: draft response-to-reviewers
- [ ] Phase 11.7: pre-resubmission audit
- [ ] Phase 11.8–11.10: cover letter + Beat handoff + resubmit

## Structure

```
.
├── README.md                # This file
├── LICENSE                  # MIT — copyright Nova O2
├── requirements.txt         # Python dependencies
├── notebooks/               # Reproducible analysis pipeline
│   ├── OTIMIZATION.ipynb
│   ├── CLEANING.ipynb
│   └── MAIN_ANALYSIS.ipynb
├── figures/                 # Manuscript figures (TIFF, 300 DPI)
└── .gitignore               # Pattern 2 (standalone submission repo)
```

`data/`, `manuscript/`, `scripts/`, `Makefile`, and the governance subfolders (`_planning/`, `_reviews/`, `_comms/`) are gitignored — they live in the workspace monorepo for the authoring team and are not part of the public submission repo. See `_reviews/README.md` (workspace-only) for round-by-round revision artefacts.

## Tech

- **Python:** 3.10+
- **Dataset encoding:** UTF-8
- **Separator:** comma
- **Decimal:** period
- **Key packages:** Pandas, NumPy, SciPy, statsmodels, Matplotlib, Seaborn
- **Build:** Pandoc (manuscript → DOCX), GNU Make
- **Repo:** `git@github.com:Nova-O2/berlin-marathon-wall.git`

## License

MIT — Copyright (c) 2026 Nova O2 Sports Science.

---

## Notes — repo state

**Padrão 2 .gitignore ativo desde 2026-04-18** (commit `5a23b6f`). Manuscript/, Makefile, scripts/ permanecem gitignored; SSOT files restored to disk after recovery 2026-05-05 mas off-repo.

**Estado público (GitHub):** notebooks/, figures/, LICENSE, README.md, requirements.txt, .gitignore. SSOT não exposto.

**Open decision (deferred per Aldo, 2026-05-05):** ao chegar na ressubmissão R1, escolher:
- **Stay Padrão 2:** SSOT continua workspace-only; redline R1 gerado de `_reviews/r1/source/2026-02-21_submitted_canonical.docx` vs novo Pandoc-rendered .docx. Audit via tags `archive/lost-2026-05/*` + branch `recovery/ssot-restored-2026-05-05` + incident report `05-strategy/incidents/2026-05-05_wall_ssot_recovery.md`.
- **Switch to Padrão 1:** rebase main on `recovery/ssot-restored-2026-05-05` (or cherry-pick), update .gitignore Padrão 1, push. SSOT vira parte da public history. Tag `v1.0-submitted-original` torna-se meaningful.

R1 work prossegue on disk-only SSOT regardless. Decisão será feita quando manuscript revisado estiver pronto pra ressubmissão.

Padrão 2 migration plan original (escrito 2026-04-08): `_planning/2026-04-08_padrao2_migration_plan.md` (workspace-only, gitignored). Partially obsoleto — Padrão 2 .gitignore já ativo; só "tag v1.0-submitted-original" + Zenodo confirmation steps remain.
