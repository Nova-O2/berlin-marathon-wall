"""Threshold sensitivity (15/20/25%) + graded severity classification.

Closes audit Finding-010: extracts the previously inline-only computations
into a committed, idempotent script so Tables S2 are reproducible from a
versioned source.

Outputs:
- notebooks/results/r1/threshold_sensitivity.csv (.md) — Panel A of Table S2
- notebooks/results/r1/graded_severity.csv (.md) — Panel B of Table S2
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _r1_common import load_data, save_results

import numpy as np
import pandas as pd
from scipy import stats


def or_at_threshold(d, th):
    """Compute crude OR (men vs women) for hit_wall = (slowdown >= th)."""
    d2 = d.assign(hit=(d["percentage_slowdown"] >= th).astype(int))
    m = d2[d2["gender_label"] == "Male"]
    w = d2[d2["gender_label"] == "Female"]
    a, b = int(m["hit"].sum()), int(len(m) - m["hit"].sum())
    c, d_ = int(w["hit"].sum()), int(len(w) - w["hit"].sum())
    or_v = (a * d_) / (b * c)
    se = np.sqrt(1 / a + 1 / b + 1 / c + 1 / d_)
    lo = np.exp(np.log(or_v) - 1.96 * se)
    hi = np.exp(np.log(or_v) + 1.96 * se)
    chi2, p, _, _ = stats.chi2_contingency([[a, b], [c, d_]])
    return {
        "threshold_pct": f"≥{th}%",
        "n_M": len(m), "n_F": len(w),
        "wall_M_pct": 100 * a / len(m),
        "wall_F_pct": 100 * c / len(w),
        "OR": or_v, "OR_CI_lo": lo, "OR_CI_hi": hi,
        "chi2_p": p,
    }


if __name__ == "__main__":
    df = load_data().dropna(subset=["percentage_slowdown", "gender_label"])
    print(f"Valid rows: {len(df):,}")

    # === Panel A — threshold sensitivity ===
    sens = pd.DataFrame([or_at_threshold(df, t) for t in [15, 20, 25]])
    print("\n=== THRESHOLD SENSITIVITY ===")
    print(sens.to_string(index=False))
    save_results(sens, "threshold_sensitivity")

    # === Panel B — graded severity ===
    bins = [(10, 15, "Mild (10–15%)"),
            (15, 20, "Moderate (15–20%)"),
            (20, 25, "Severe (20–25%)"),
            (25, float("inf"), "Catastrophic (>25%)")]

    total_m = (df["gender_label"] == "Male").sum()
    total_f = (df["gender_label"] == "Female").sum()
    graded_rows = []
    for lo, hi, label in bins:
        sub = df[(df["percentage_slowdown"] >= lo) & (df["percentage_slowdown"] < hi)]
        n_m = (sub["gender_label"] == "Male").sum()
        n_f = (sub["gender_label"] == "Female").sum()
        graded_rows.append({
            "Severity": label,
            "n_M": int(n_m), "n_F": int(n_f),
            "pct_M": 100 * n_m / total_m,
            "pct_F": 100 * n_f / total_f,
            "ratio_M_to_F": (n_m / total_m) / (n_f / total_f) if n_f > 0 else None,
        })

    graded = pd.DataFrame(graded_rows)
    print("\n=== GRADED SEVERITY ===")
    print(graded.to_string(index=False))
    save_results(graded, "graded_severity")
