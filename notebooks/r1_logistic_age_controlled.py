"""Q2: Multivariable logistic regression for hit_wall ~ sex + age + perf_cat,
with sex x age interaction. Run on FULL + DEDUP subset.

Outputs:
- notebooks/results/r1/logistic_full.csv (.md)
- notebooks/results/r1/logistic_dedup.csv (.md)
- Together they form Supplementary Table S1.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from _r1_common import load_data, save_results, RESULTS_DIR

import pandas as pd
import numpy as np
import statsmodels.formula.api as smf


def fit_logistic(df: pd.DataFrame, label: str) -> pd.DataFrame:
    """Fit main + interaction logistic models. Return stacked DataFrame."""
    d = df.dropna(subset=["hit_wall", "gender_label", "age_mid", "performance_category"]).copy()
    d["hit_wall"] = d["hit_wall"].astype(int)

    # Order categories with reference first (statsmodels uses Treatment with first as ref by default)
    d["gender_label"] = pd.Categorical(d["gender_label"], categories=["Female", "Male"])
    d["performance_category"] = pd.Categorical(
        d["performance_category"],
        categories=["Casual", "Recreational", "Intermediate", "Advanced", "Competitive (<3h)"],
    )

    print(f"[{label}] n = {len(d):,} after dropping NA")

    model_main = smf.logit(
        "hit_wall ~ C(gender_label) + age_mid + C(performance_category)",
        data=d,
    ).fit(disp=False)

    model_int = smf.logit(
        "hit_wall ~ C(gender_label) * age_mid + C(performance_category)",
        data=d,
    ).fit(disp=False)

    def extract(model, model_name):
        params = model.params
        ci = model.conf_int()
        out = pd.DataFrame({
            "term": params.index.tolist(),
            "coef": params.values,
            "OR": np.exp(params.values),
            "OR_CI_lo": np.exp(ci[0].values),
            "OR_CI_hi": np.exp(ci[1].values),
            "p": model.pvalues.values,
        })
        out["model"] = model_name
        out["n"] = int(model.nobs)
        out["AIC"] = model.aic
        out["subset"] = label
        return out

    return pd.concat([extract(model_main, "main"), extract(model_int, "interaction")], ignore_index=True)


if __name__ == "__main__":
    # Full dataset
    df_full = load_data()
    res_full = fit_logistic(df_full, "Full")
    print("\n=== FULL DATASET ===")
    print(res_full.to_string(index=False))
    save_results(res_full, "logistic_full")

    # Dedup subset (from Task 3)
    dedup_path = RESULTS_DIR / "dedup_subset.parquet"
    if dedup_path.exists():
        df_dedup = pd.read_parquet(dedup_path)
        res_dedup = fit_logistic(df_dedup, "Dedup")
        print("\n=== DEDUP SUBSET ===")
        print(res_dedup.to_string(index=False))
        save_results(res_dedup, "logistic_dedup")
    else:
        print(f"WARN: {dedup_path} not found - run Task 3 (r1_dedup_sensitivity.py) first")
