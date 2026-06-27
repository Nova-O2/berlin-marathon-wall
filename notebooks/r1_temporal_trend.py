"""Q4: 27-year temporal trend of gender wall-hit gap.

Tests whether gender disparity in wall-hit prevalence widened or narrowed
over 1999-2025. Mann-Kendall trend + linear regression of gap.

Outputs:
- notebooks/results/r1/temporal_trend_table.csv (.md)
- figures/Figure_5_Temporal_Trend.tiff (300 DPI, LZW compressed) + .png (150 DPI)
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from _r1_common import load_data, save_results, COLOR_MEN, COLOR_WOMEN

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
import pymannkendall as mk

if __name__ == "__main__":
    df = load_data()
    valid = df.dropna(subset=["hit_wall"])
    print(f"Total valid pacing rows: {len(valid):,}")

    # Aggregate by year x gender
    annual = (valid.groupby(["year", "gender_label"])
                   .agg(n=("hit_wall", "size"), n_wall=("hit_wall", "sum"))
                   .assign(prevalence_pct=lambda x: 100 * x["n_wall"] / x["n"])
                   .reset_index())

    pivot = annual.pivot(index="year", columns="gender_label", values="prevalence_pct").reset_index()
    pivot["gap_pp"] = pivot["Male"] - pivot["Female"]

    print(f"\nYears covered: {pivot['year'].min()}-{pivot['year'].max()} (n={len(pivot)})")

    # Mann-Kendall on three series
    def mk_test(series):
        result = mk.original_test(series)
        return {"tau": result.Tau, "p": result.p, "trend": result.trend, "slope": result.slope}

    men_mk = mk_test(pivot["Male"].values)
    women_mk = mk_test(pivot["Female"].values)
    gap_mk = mk_test(pivot["gap_pp"].values)

    print(f"\nMen prevalence trend: tau={men_mk['tau']:.3f}, p={men_mk['p']:.4f}, trend={men_mk['trend']}")
    print(f"Women prevalence trend: tau={women_mk['tau']:.3f}, p={women_mk['p']:.4f}, trend={women_mk['trend']}")
    print(f"Gap trend: tau={gap_mk['tau']:.3f}, p={gap_mk['p']:.4f}, trend={gap_mk['trend']}")

    # Linear regression of gap ~ year
    slope, intercept, r, p, se = stats.linregress(pivot["year"], pivot["gap_pp"])
    print(f"\nLinear regression gap ~ year: slope={slope:.4f} pp/year (95% CI +/-{1.96*se:.4f}), R^2={r**2:.4f}, p={p:.4f}")

    # Save table
    out = pivot.copy()
    out["mk_men_tau"] = men_mk["tau"]
    out["mk_men_p"] = men_mk["p"]
    out["mk_women_tau"] = women_mk["tau"]
    out["mk_women_p"] = women_mk["p"]
    out["mk_gap_tau"] = gap_mk["tau"]
    out["mk_gap_p"] = gap_mk["p"]
    out["lr_slope_pp_per_year"] = slope
    out["lr_p"] = p
    out["lr_R2"] = r ** 2
    save_results(out, "temporal_trend_table")

    # Figure 5 (was E): Temporal trend with COVID marker + MK stats
    n_men_avg = annual.query("gender_label == 'Male'")["n"].mean()
    n_women_avg = annual.query("gender_label == 'Female'")["n"].mean()

    fig, ax = plt.subplots(figsize=(9, 5.5), dpi=300, facecolor="white")
    ax.scatter(pivot["year"], pivot["Male"], color=COLOR_MEN,
               label=f"Men (mean n/yr ≈ {n_men_avg:,.0f})", alpha=0.85, s=45,
               edgecolor="white", linewidth=0.5)
    ax.scatter(pivot["year"], pivot["Female"], color=COLOR_WOMEN,
               label=f"Women (mean n/yr ≈ {n_women_avg:,.0f})", alpha=0.85, s=45,
               edgecolor="white", linewidth=0.5)
    ax.plot(pivot["year"], pivot["Male"].rolling(3, center=True).mean(),
            color=COLOR_MEN, lw=2.2, alpha=0.55, label="_nolegend_")
    ax.plot(pivot["year"], pivot["Female"].rolling(3, center=True).mean(),
            color=COLOR_WOMEN, lw=2.2, alpha=0.55, label="_nolegend_")

    # COVID 2020 marker (race cancelled — no data point)
    ax.axvspan(2019.5, 2020.5, color="lightgrey", alpha=0.45, zorder=0)
    ymax = max(pivot["Male"].max(), pivot["Female"].max())
    # Place label near the x-axis to avoid overlap with the legend (top-right)
    ymin = min(pivot["Male"].min(), pivot["Female"].min())
    ax.text(2020, ymin * 0.55, "2020 cancelled\n(COVID-19)",
            ha="center", va="bottom", fontsize=8.5, style="italic", color="dimgrey")

    # Mann-Kendall + LR statistics annotation (top-left)
    stats_text = (
        f"Mann-Kendall trend (gender gap):\n"
        f"  τ = {gap_mk['tau']:.2f},  p = {gap_mk['p']:.2f}\n"
        f"Linear regression (slope of gap):\n"
        f"  +{slope:.2f} pp/year  (95% CI ±{1.96*se:.2f})\n"
        f"  R² = {r**2:.2f},  p = {p:.2f}"
    )
    ax.text(0.02, 0.97, stats_text,
            transform=ax.transAxes, fontsize=8.5, ha="left", va="top",
            family="monospace",
            bbox=dict(boxstyle="round,pad=0.4", facecolor="white", edgecolor="grey", alpha=0.92))

    ax.set_xlabel("Year")
    ax.set_ylabel('Prevalence of "hitting the wall" (%)')
    ax.set_ylim(0, ymax * 1.15)
    ax.legend(frameon=False, loc="upper right")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    plt.tight_layout()

    out_tiff = Path(__file__).parent.parent / "figures" / "Figure_5_Temporal_Trend.tiff"
    out_png = Path(__file__).parent.parent / "figures" / "Figure_5_Temporal_Trend.png"
    plt.savefig(out_tiff, dpi=300, bbox_inches="tight", facecolor="white")
    plt.savefig(out_png, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)

    # LZW compression + RGB conversion (per workspace research-figures rule)
    from PIL import Image
    img = Image.open(out_tiff)
    if img.mode == "RGBA":
        bg = Image.new("RGB", img.size, "white")
        bg.paste(img, mask=img.split()[3])
        img = bg
    elif img.mode != "RGB":
        img = img.convert("RGB")
    img.save(out_tiff, compression="tiff_lzw", dpi=(300, 300))
    print(f"\nSaved: {out_tiff} ({out_tiff.stat().st_size/1024:.1f} KB), {out_png}")
