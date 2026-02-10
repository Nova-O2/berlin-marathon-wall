# The Gender Pacing Gap: Berlin Marathon Analysis (1999–2025)

This repository contains the dataset and source code for the study: **"The Gender Pacing Gap: Analysis of 873,000 Berlin Marathon Runners Reveals Men are Twice as Likely to ‘Hit the Wall’"**.

**Status:** Submitted for peer review.

## 📂 Repository Content

- **`data/`**: Cleaned dataset used for analysis (`.parquet` format).
- **`notebooks/`**: Jupyter Notebooks containing the full reproducible pipeline:
    - `01_Data_Cleaning.ipynb`: Raw data preprocessing.
    - `02_Feature_Engineering.ipynb`: Calculation of pacing metrics (splits, % slowdown).
    - `03_Main_Analysis.ipynb`: Statistical tests and figure generation.
- **`figures/`**: High-resolution outputs of the figures presented in the manuscript (Figures A, B, and C).

## 🚀 How to Reproduce

1. Clone this repository.
2. Install dependencies: `pandas`, `numpy`, `matplotlib`, `seaborn`, `scipy`.
3. Run the `03_Main_Analysis.ipynb` notebook to generate the statistics and figures.

## 📊 Dataset Info

The analysis is based on **873,334 finishers** of the Berlin Marathon.
- **File:** `Dataset_Berlin_Cleaned_Analysis_Ready.parquet`
- **Key Variables:** `gender`, `age_group`, `net_time`, `pct_slowdown` (% deceleration in 2nd half), `hit_wall` (>20% slowdown).

*Corresponding Author linked in the manuscript.*
