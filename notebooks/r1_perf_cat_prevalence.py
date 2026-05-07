"""Per-performance-category × gender wall-hit prevalence and Odds Ratios.

Closes audit Finding-004: persists the "six times sub-3h" (and equivalent
ratios for Advanced/Intermediate/Recreational/Casual) to a committed CSV so
all manuscript-cited per-category prevalences and ORs have a traceable source.

Output: notebooks/results/r1/perf_cat_gender_prevalence.csv (.md)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _r1_common import load_data, save_results

import numpy as np
import pandas as pd

PERF_ORDER = ["Competitive (<3h)", "Advanced", "Intermediate", "Recreational", "Casual"]


def or_with_ci(a, b, c, d):
    """Crude OR with 95% CI via log-OR + Woolf SE. a,b: men hit/no-hit; c,d: women hit/no-hit."""
    if min(a, b, c, d) == 0:
        return np.nan, np.nan, np.nan
    or_v = (a * d) / (b * c)
    se = np.sqrt(1 / a + 1 / b + 1 / c + 1 / d)
    return or_v, np.exp(np.log(or_v) - 1.96 * se), np.exp(np.log(or_v) + 1.96 * se)


if __name__ == "__main__":
    df = load_data()
    df = df.dropna(subset=["hit_wall", "performance_category", "gender_label"])
    df["hit_wall"] = df["hit_wall"].astype(int)
    print(f"Valid rows: {len(df):,}")

    rows = []
    for cat in PERF_ORDER:
        sub = df[df["performance_category"] == cat]
        m = sub[sub["gender_label"] == "Male"]
        w = sub[sub["gender_label"] == "Female"]
        n_m, n_w = len(m), len(w)
        hit_m, hit_w = int(m["hit_wall"].sum()), int(w["hit_wall"].sum())
        pct_m = 100 * hit_m / n_m if n_m > 0 else np.nan
        pct_w = 100 * hit_w / n_w if n_w > 0 else np.nan
        ratio = pct_m / pct_w if pct_w and pct_w > 0 else np.nan
        a, b = hit_m, n_m - hit_m
        c, d = hit_w, n_w - hit_w
        or_v, ci_lo, ci_hi = or_with_ci(a, b, c, d)
        rows.append({
            "performance_category": cat,
            "n_M": n_m, "n_F": n_w,
            "hit_M": hit_m, "hit_F": hit_w,
            "wall_pct_M": pct_m, "wall_pct_F": pct_w,
            "prevalence_ratio_M_to_F": ratio,
            "OR": or_v, "OR_CI_lo": ci_lo, "OR_CI_hi": ci_hi,
        })

    table = pd.DataFrame(rows)
    print("\nPER-PERFORMANCE-CATEGORY × GENDER:")
    print(table.to_string(index=False))
    save_results(table, "perf_cat_gender_prevalence")
