"""Q1 light: Within-Berlin sex × age_group quintile re-stratification.

Re-classifies runners by quintile of finish time WITHIN their (sex, age_group)
stratum. Re-computes wall-hit prevalence + ORs by quintile.

Output: notebooks/results/r1/quintile_sensitivity.csv (.md) — Table S4
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from _r1_common import load_data, save_results

import pandas as pd
import numpy as np

QUINTILE_LABELS = ["Q1 (top 10%)", "Q2 (10-25%)", "Q3 (25-50%)", "Q4 (50-75%)", "Q5 (bottom 25%)"]
QUINTILE_BINS = [-0.001, 0.10, 0.25, 0.50, 0.75, 1.001]


def to_quintile(p):
    if pd.isna(p):
        return None
    for i, label in enumerate(QUINTILE_LABELS):
        if QUINTILE_BINS[i] < p <= QUINTILE_BINS[i + 1]:
            return label
    return None


if __name__ == "__main__":
    df = load_data(filter_age=True)
    df = df.dropna(subset=["hit_wall", "net_time_sec", "age_str", "gender_label"])
    print(f"Filtered (valid hit_wall, time, age, gender): {len(df):,}")

    # Within-stratum percentile rank (lower percentile = faster)
    df["finish_pct"] = df.groupby(["gender_label", "age_str"])["net_time_sec"].rank(
        pct=True, method="average"
    )
    df["quintile"] = df["finish_pct"].apply(to_quintile)

    # Aggregate
    agg = (
        df.groupby(["quintile", "gender_label"])
        .agg(
            n=("hit_wall", "size"),
            n_wall=("hit_wall", "sum"),
            mean_slowdown=("percentage_slowdown", "mean"),
            sd_slowdown=("percentage_slowdown", "std"),
        )
        .assign(wall_pct=lambda x: 100 * x["n_wall"] / x["n"])
        .reset_index()
    )

    # OR per quintile
    rows = []
    for q in QUINTILE_LABELS:
        m_row = agg[(agg["quintile"] == q) & (agg["gender_label"] == "Male")]
        f_row = agg[(agg["quintile"] == q) & (agg["gender_label"] == "Female")]
        if m_row.empty or f_row.empty:
            continue
        m, f = m_row.iloc[0], f_row.iloc[0]
        a, b = m["n_wall"], m["n"] - m["n_wall"]
        c, d = f["n_wall"], f["n"] - f["n_wall"]
        if a > 0 and b > 0 and c > 0 and d > 0:
            or_val = (a * d) / (b * c)
            log_or = np.log(or_val)
            se = np.sqrt(1 / a + 1 / b + 1 / c + 1 / d)
            ci_lo = np.exp(log_or - 1.96 * se)
            ci_hi = np.exp(log_or + 1.96 * se)
        else:
            or_val = ci_lo = ci_hi = np.nan
        rows.append(
            {
                "Quintile": q,
                "n_M": int(m["n"]),
                "n_F": int(f["n"]),
                "wall_M_pct": m["wall_pct"],
                "wall_F_pct": f["wall_pct"],
                "slow_M_pct": m["mean_slowdown"],
                "slow_F_pct": f["mean_slowdown"],
                "OR": or_val,
                "OR_CI_lo": ci_lo,
                "OR_CI_hi": ci_hi,
            }
        )

    table = pd.DataFrame(rows)
    print("\nQUINTILE SENSITIVITY:")
    print(table.to_string(index=False))
    save_results(table, "quintile_sensitivity")
