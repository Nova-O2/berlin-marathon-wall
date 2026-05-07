"""Q6: Strict dedup sensitivity for repeated runners.

Composite key = (name_norm, age_group). Keeps first appearance per key as
deduplicated subset (conservative: typos -> false uniques, but clean from
false collisions). Re-runs main analyses on subset.

Output:
- data/dedup_subset.parquet (gitignored) -- used by Tasks 4 + 5
- notebooks/results/r1/dedup_sensitivity_table.csv (.md) -- Table S3
"""
import sys
import unicodedata
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from _r1_common import load_data, save_results, DEDUP_SUBSET_PATH

import pandas as pd
import numpy as np
from scipy import stats


def normalize_name(name):
    if pd.isna(name):
        return ""
    s = str(name).strip().lower()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = " ".join(s.split())
    return s


def main_analyses(d, label):
    """Run Welch + Mann-Whitney + Chi2 + crude OR on subset d."""
    d = d.dropna(subset=["hit_wall", "percentage_slowdown"])
    men = d[d["gender_label"] == "Male"]
    women = d[d["gender_label"] == "Female"]

    welch = stats.ttest_ind(men["percentage_slowdown"], women["percentage_slowdown"], equal_var=False)
    mwu = stats.mannwhitneyu(men["percentage_slowdown"], women["percentage_slowdown"], alternative="two-sided")

    a, b = int(men["hit_wall"].sum()), int(len(men) - men["hit_wall"].sum())
    c, d_ = int(women["hit_wall"].sum()), int(len(women) - women["hit_wall"].sum())
    or_val = (a * d_) / (b * c)
    log_or = np.log(or_val)
    se = np.sqrt(1/a + 1/b + 1/c + 1/d_)
    ci_lo = np.exp(log_or - 1.96 * se)
    ci_hi = np.exp(log_or + 1.96 * se)
    chi2, p_chi, _, _ = stats.chi2_contingency([[a, b], [c, d_]])

    return {
        "subset": label,
        "n_total": len(d),
        "n_men": len(men),
        "n_women": len(women),
        "mean_slow_M_pct": men["percentage_slowdown"].mean(),
        "mean_slow_F_pct": women["percentage_slowdown"].mean(),
        "welch_t": welch.statistic,
        "welch_p": welch.pvalue,
        "mwu_p": mwu.pvalue,
        "wall_pct_M": 100 * men["hit_wall"].mean(),
        "wall_pct_F": 100 * women["hit_wall"].mean(),
        "OR_crude": or_val,
        "OR_CI_lo": ci_lo,
        "OR_CI_hi": ci_hi,
        "chi2_p": p_chi,
    }


if __name__ == "__main__":
    df = load_data()
    print(f"Original entries: {len(df):,}")

    df["name_norm"] = df["name"].apply(normalize_name)
    df["composite_key"] = df["name_norm"] + "|" + df["age_str"].astype(str)

    df_sorted = df.sort_values("year", ascending=True)
    dedup = df_sorted.drop_duplicates(subset="composite_key", keep="first").reset_index(drop=True)

    dedup_rate = 100 * (1 - len(dedup) / len(df))
    print(f"Dedup subset: {len(dedup):,} ({100 * len(dedup) / len(df):.1f}% of original)")
    print(f"Dedup reduction: {dedup_rate:.1f}%")

    # Empty / blank name keys note
    blank_keys = (df["name_norm"] == "").sum()
    print(f"Empty normalized names (likely typo / null): {blank_keys}")

    # Save subset
    out_subset = DEDUP_SUBSET_PATH
    dedup.to_parquet(out_subset, engine="pyarrow")
    print(f"Saved dedup subset: {out_subset}")

    # Sensitivity comparison
    results = pd.DataFrame([main_analyses(df, "Full"), main_analyses(dedup, "Dedup")])
    print("\nSENSITIVITY COMPARISON:")
    print(results.T.to_string())
    save_results(results, "dedup_sensitivity_table")
