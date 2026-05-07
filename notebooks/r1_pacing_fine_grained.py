"""Q2: Fine-grained pacing metrics from 5 km splits.

Computes 5 metrics per runner (subset with all valid 5 km splits):
1. CV of pace across segments [variability]
2. Inflection point [transition]
3. Late-race deceleration [late instability]
4. Oscillation count [erratic]
5. Km30 gradient [wall onset]

Outputs:
- notebooks/results/r1/fine_grained_table.csv (.md) — Table 3 / S5
- figures/Figure_D_Pacing_Variability.tiff (300 DPI) + .png (150 DPI)
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from _r1_common import load_data, save_results, COLOR_MEN, COLOR_WOMEN

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats


SPLIT_KMS = [0, 5, 10, 15, 20, 25, 30, 35, 40, 42.195]
# Cumulative times at each split (col names in df after load_data())
CUM_COLS = [None, "5km_sec", "10km_sec", "15km_sec", "20km_sec", "25km_sec",
            "30km_sec", "35km_sec", "40km_sec", "net_time_sec"]


def compute_segment_paces(df: pd.DataFrame) -> pd.DataFrame:
    """Add columns pace_<a>_<b> (sec/km) for each segment."""
    out = df.copy()
    for i in range(len(SPLIT_KMS) - 1):
        a, b = SPLIT_KMS[i], SPLIT_KMS[i + 1]
        seg_dist = b - a
        if i == 0:
            seg_time = out[CUM_COLS[i + 1]]  # 0 -> 5km cumulative
        else:
            seg_time = out[CUM_COLS[i + 1]] - out[CUM_COLS[i]]
        out[f"pace_{a}_{b}"] = seg_time / seg_dist
    return out


def compute_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Compute 5 fine-grained pacing metrics. Returns df with new columns."""
    out = df.copy()
    pace_cols = [f"pace_{SPLIT_KMS[i]}_{SPLIT_KMS[i+1]}" for i in range(len(SPLIT_KMS) - 1)]

    # Metric 1: CV of pace
    paces = out[pace_cols]
    out["cv_pace"] = paces.std(axis=1) / paces.mean(axis=1)

    # Metric 2: Inflection point — first 5km segment for which pace exceeded the
    # pre-half-marathon mean by >5% AND remained slower thereafter (i.e., for ALL
    # subsequent segments through the finish). This matches the strict criterion
    # described in Methods. Updated 2026-05-07 (audit-F-005) from the prior
    # 2-consecutive-segments relaxation to fully match the manuscript wording.
    pre_half_cols = pace_cols[:4]  # 0-5, 5-10, 10-15, 15-20 (pre-half)
    pre_half_mean = out[pre_half_cols].mean(axis=1).values
    threshold = pre_half_mean * 1.05

    paces_arr_inf = out[pace_cols].values  # (n, 9)
    exceed = paces_arr_inf > threshold[:, None]  # (n, 9) bool
    n_runners = paces_arr_inf.shape[0]
    inflection_arr = np.full(n_runners, np.nan)
    # Strict criterion: from candidate i in {4,5,6,7,8} (segments 20-25..40-end),
    # the runner has inflection at SPLIT_KMS[i+1] iff exceed[:, i:].all(axis=1).
    # Iterate i from earliest to latest; first match wins (NaN guard).
    for i in range(4, len(pace_cols)):
        sustained = exceed[:, i:].all(axis=1)
        mask = sustained & np.isnan(inflection_arr)
        # Inflection km is the start-of-segment for the i-th segment, which is
        # SPLIT_KMS[i] (e.g., i=5 → segment 25-30 km → inflection start = 25 km).
        inflection_arr[mask] = SPLIT_KMS[i]
    out["inflection_km"] = inflection_arr

    # Metric 3: Late-race deceleration (% diff pace 35-40 vs pace 5-10)
    out["late_decel_pct"] = 100 * (out["pace_35_40"] / out["pace_5_10"] - 1)

    # Metric 4: Oscillation count (sign changes in pace gradient)
    # Vectorized: forward-fill last non-zero sign, then count diffs != 0
    paces_arr = out[pace_cols].values
    diffs = np.diff(paces_arr, axis=1)
    signs = np.sign(diffs).astype(np.int8)  # (n, 8) values in {-1, 0, +1}

    # For each row, replace 0s with the previous non-zero sign (forward fill).
    # Implementation: walk left-to-right with vectorized "if 0, copy from left".
    n_rows, n_cols = signs.shape
    filled = signs.copy()
    for j in range(1, n_cols):
        zero_mask = filled[:, j] == 0
        filled[zero_mask, j] = filled[zero_mask, j - 1]
    # Now leading-zero columns may still be 0 (no prior info); those rows have
    # all-zero diffs (impossible in practice — paces are never identical across all
    # 8 transitions), but for safety we just count transitions where both sides
    # are non-zero AND differ.
    nonzero_pair = (filled[:, :-1] != 0) & (filled[:, 1:] != 0)
    sign_change = (filled[:, :-1] != filled[:, 1:]) & nonzero_pair
    out["oscillations"] = sign_change.sum(axis=1).astype(int)

    # Metric 5: Km30 gradient (pace 30-35 minus pace 25-30)
    out["km30_gradient"] = out["pace_30_35"] - out["pace_25_30"]

    return out


if __name__ == "__main__":
    df = load_data()

    # Subset with all splits valid + > 0
    cum_cols_to_check = [c for c in CUM_COLS if c is not None]
    valid_mask = df[cum_cols_to_check].notna().all(axis=1) & (df[cum_cols_to_check] > 0).all(axis=1)
    subset = df[valid_mask & df["gender_label"].notna()].copy()
    print(f"Total: {len(df):,} | Valid splits: {len(subset):,} ({100*len(subset)/len(df):.1f}%)")

    subset = compute_segment_paces(subset)
    subset = compute_metrics(subset)

    # Inflection point distribution diagnostics
    n_inf_nan_M = subset[subset["gender_label"] == "Male"]["inflection_km"].isna().sum()
    n_inf_nan_F = subset[subset["gender_label"] == "Female"]["inflection_km"].isna().sum()
    n_M_total = (subset["gender_label"] == "Male").sum()
    n_F_total = (subset["gender_label"] == "Female").sum()
    print(f"\nInflection NaN (no inflection found):")
    print(f"  Men: {n_inf_nan_M:,}/{n_M_total:,} ({100*n_inf_nan_M/n_M_total:.1f}%)")
    print(f"  Women: {n_inf_nan_F:,}/{n_F_total:,} ({100*n_inf_nan_F/n_F_total:.1f}%)")

    inf_M_v = subset[subset["gender_label"] == "Male"]["inflection_km"].dropna()
    inf_F_v = subset[subset["gender_label"] == "Female"]["inflection_km"].dropna()
    print(f"  Men inflection: median={inf_M_v.median():.1f}, IQR=[{inf_M_v.quantile(0.25):.1f}, {inf_M_v.quantile(0.75):.1f}]")
    print(f"  Women inflection: median={inf_F_v.median():.1f}, IQR=[{inf_F_v.quantile(0.25):.1f}, {inf_F_v.quantile(0.75):.1f}]")

    # Persist inflection distribution to CSV (audit-F-009: every manuscript number traceable to results/*.csv)
    inflection_dist = pd.DataFrame([
        {
            "gender": "Male",
            "n_total": int(n_M_total),
            "n_with_inflection": int(len(inf_M_v)),
            "pct_with_inflection": 100 * len(inf_M_v) / n_M_total,
            "n_no_inflection": int(n_inf_nan_M),
            "pct_no_inflection": 100 * n_inf_nan_M / n_M_total,
            "median_km": inf_M_v.median(),
            "q25_km": inf_M_v.quantile(0.25),
            "q75_km": inf_M_v.quantile(0.75),
            "mean_km": inf_M_v.mean(),
            "sd_km": inf_M_v.std(),
        },
        {
            "gender": "Female",
            "n_total": int(n_F_total),
            "n_with_inflection": int(len(inf_F_v)),
            "pct_with_inflection": 100 * len(inf_F_v) / n_F_total,
            "n_no_inflection": int(n_inf_nan_F),
            "pct_no_inflection": 100 * n_inf_nan_F / n_F_total,
            "median_km": inf_F_v.median(),
            "q25_km": inf_F_v.quantile(0.25),
            "q75_km": inf_F_v.quantile(0.75),
            "mean_km": inf_F_v.mean(),
            "sd_km": inf_F_v.std(),
        },
    ])
    save_results(inflection_dist, "inflection_distribution")

    metrics = ["cv_pace", "inflection_km", "late_decel_pct", "oscillations", "km30_gradient"]
    rows = []
    for m in metrics:
        men = subset[subset["gender_label"] == "Male"][m].dropna()
        women = subset[subset["gender_label"] == "Female"][m].dropna()
        if len(men) < 2 or len(women) < 2:
            continue
        welch = stats.ttest_ind(men, women, equal_var=False)
        mwu = stats.mannwhitneyu(men, women, alternative="two-sided")
        d = (men.mean() - women.mean()) / np.sqrt((men.var() + women.var()) / 2)
        rows.append({
            "metric": m,
            "n_M": int(len(men)), "n_F": int(len(women)),
            "mean_M": men.mean(), "mean_F": women.mean(),
            "sd_M": men.std(), "sd_F": women.std(),
            "cohens_d": d,
            "welch_p": welch.pvalue,
            "mwu_p": mwu.pvalue,
        })

    table = pd.DataFrame(rows)
    print("\nFINE-GRAINED PACING METRICS by gender:")
    print(table.to_string(index=False))
    save_results(table, "fine_grained_table")

    # Figure D
    fig, axes = plt.subplots(1, 2, figsize=(12, 5), dpi=300)

    # (a) Violin of CV
    ax = axes[0]
    cv_M = subset[subset["gender_label"] == "Male"]["cv_pace"].dropna()
    cv_F = subset[subset["gender_label"] == "Female"]["cv_pace"].dropna()
    parts = ax.violinplot([cv_M, cv_F], positions=[1, 2], widths=0.7, showmedians=True)
    for pc, color in zip(parts["bodies"], [COLOR_MEN, COLOR_WOMEN]):
        pc.set_facecolor(color)
        pc.set_alpha(0.7)
    ax.set_xticks([1, 2])
    ax.set_xticklabels([f"Men\n(n={len(cv_M):,})", f"Women\n(n={len(cv_F):,})"])
    ax.set_ylabel("Coefficient of variation (CV) of pace across 5 km segments")
    ax.text(0.05, 0.95, "a", transform=ax.transAxes, fontsize=14, fontweight="bold", va="top")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    # (b) Boxplot of inflection km
    ax = axes[1]
    inf_M = subset[subset["gender_label"] == "Male"]["inflection_km"].dropna()
    inf_F = subset[subset["gender_label"] == "Female"]["inflection_km"].dropna()
    bp = ax.boxplot([inf_M, inf_F], positions=[1, 2], widths=0.5, patch_artist=True,
                    medianprops=dict(color="black", linewidth=2))
    for patch, color in zip(bp["boxes"], [COLOR_MEN, COLOR_WOMEN]):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
    ax.set_xticks([1, 2])
    ax.set_xticklabels([f"Men\n(n={len(inf_M):,})", f"Women\n(n={len(inf_F):,})"])
    ax.set_ylabel("Inflection point (km)")
    ax.text(0.05, 0.95, "b", transform=ax.transAxes, fontsize=14, fontweight="bold", va="top")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    plt.tight_layout()
    figures_dir = Path(__file__).parent.parent / "figures"
    out_tiff = figures_dir / "Figure_D_Pacing_Variability.tiff"
    out_png = figures_dir / "Figure_D_Pacing_Variability.png"
    plt.savefig(out_tiff, dpi=300, bbox_inches="tight")
    plt.savefig(out_png, dpi=150, bbox_inches="tight")
    print(f"\nSaved: {out_tiff}, {out_png}")
