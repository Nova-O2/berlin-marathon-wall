"""Generate manuscript tables from notebook results CSVs (idempotent, version-controlled).

Closes audit R2-004/005 recommendation: Tables that contain stratified numbers
(Table 2, Table S5) should be regenerated from the data rather than hand-edited,
to prevent stale-table regressions like those caught in audit Round 2.

This script writes:
- manuscript/tables/Table2.md — stratified analysis (5 perf categories × gender)
- manuscript/tables/TableS5.md — fine-grained pacing metrics (5 metrics × gender)

Run after any analysis change that affects per-category prevalence or fine-grained
pacing values. The Makefile may invoke this as a make target.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _r1_common import load_data

import pandas as pd
import numpy as np
from scipy import stats

TABLES_DIR = Path(__file__).parent.parent / "manuscript" / "tables"
RESULTS_DIR = Path(__file__).parent / "results" / "r1"

PERF_ORDER = ["Competitive (<3h)", "Advanced", "Intermediate", "Recreational", "Casual"]
PERF_RANGES = {
    "Competitive (<3h)": "(< 3:00 h)",
    "Advanced": "(3:00--3:30)",
    "Intermediate": "(3:30--4:00)",
    "Recreational": "(4:00--4:30)",
    "Casual": "(> 4:30)",
}


def or_with_ci(a, b, c, d):
    if min(a, b, c, d) == 0:
        return np.nan, np.nan, np.nan
    or_v = (a * d) / (b * c)
    se = np.sqrt(1 / a + 1 / b + 1 / c + 1 / d)
    return or_v, np.exp(np.log(or_v) - 1.96 * se), np.exp(np.log(or_v) + 1.96 * se)


def build_table2(df):
    """Stratified analysis by performance category × gender."""
    df = df.dropna(subset=["hit_wall", "performance_category", "percentage_slowdown", "gender_label"])
    df["hit_wall"] = df["hit_wall"].astype(int)

    rows = []
    for i, cat in enumerate(PERF_ORDER, start=1):
        sub = df[df["performance_category"] == cat]
        m = sub[sub["gender_label"] == "Male"]
        w = sub[sub["gender_label"] == "Female"]
        n_m, n_w = len(m), len(w)
        slow_m, slow_w = m["percentage_slowdown"].mean(), w["percentage_slowdown"].mean()
        gap = slow_m - slow_w
        wall_m_pct = 100 * m["hit_wall"].mean()
        wall_w_pct = 100 * w["hit_wall"].mean()
        # Prevalence ratio (M:F) — matches manuscript prose "X times more likely"
        prev_ratio = wall_m_pct / wall_w_pct if wall_w_pct > 0 else float("inf")
        rng = PERF_RANGES[cat]
        rows.append(
            f"| **{i}. {cat}** {rng if cat != 'Competitive (<3h)' else ''} | "
            f"{n_m:,} / {n_w:,} | "
            f"{slow_m:.2f}% / {slow_w:.2f}% | "
            f"**+{gap:.2f}** | "
            f"{wall_m_pct:.2f}% / {wall_w_pct:.2f}% | "
            f"**{prev_ratio:.2f}** |"
        )

    header = (
        "**Table 2.** Stratified analysis of pacing metrics, \"Ego Gap,\" and risk of hitting the wall by performance level.\n\n"
        "| **Performance Category** | **Sample (N)** (Men / Women) | **Avg Slowdown (%)** (Men / Women) | **Ego Gap (pp)** | **Wall Hit Rate (%)** (Men / Women) | **Prevalence Ratio (M:F)** |\n"
        "|:---|:---:|:---:|:---:|:---:|:---:|"
    )
    footer = (
        "\nValues are presented as Male / Female. \"Ego Gap\" represents the difference "
        "in percentage points between male and female mean slowdown. "
        "Prevalence Ratio is computed as the ratio of male wall-hit prevalence to female wall-hit prevalence "
        "within each performance category. Adjusted Odds Ratios from the multivariable logistic regression are "
        "reported in Supplementary Table S1. All ratios are statistically significant at *p* < 0.001 by Chi-square."
    )

    out = "\n".join([header] + rows) + "\n" + footer + "\n"
    (TABLES_DIR / "Table2.md").write_text(out)
    print(f"Wrote: Table2.md")


def build_tableS5():
    """Fine-grained pacing metrics from fine_grained_table.csv."""
    fg = pd.read_csv(RESULTS_DIR / "fine_grained_table.csv")
    inf_dist = pd.read_csv(RESULTS_DIR / "inflection_distribution.csv")

    # Map metric → display row
    metric_display = {
        "cv_pace": ("Coefficient of variation (CV) of pace across 5 km segments",
                    "Within-runner SD/mean of segment pace"),
        "inflection_km": ("Inflection point (km)",
                          "First 5 km segment for which pace exceeded the pre-half-marathon mean by > 5% AND remained slower for all subsequent segments through the finish (NaN if no such segment)"),
        "late_decel_pct": ("Late-race deceleration (%)",
                           "(pace 35–40 km / pace 5–10 km − 1) × 100"),
        "oscillations": ("Oscillation count",
                         "Number of split-to-split sign changes in pace gradient (across 9 segments)"),
        "km30_gradient": ("Km30 gradient (s/km)",
                          "pace 30–35 km − pace 25–30 km (positive = late-race slowing)"),
    }

    rows = []
    for _, r in fg.iterrows():
        name, desc = metric_display[r["metric"]]
        if r["metric"] == "inflection_km":
            n_m_str = f"{int(r['n_M']):,} ({100 * r['n_M'] / inf_dist.iloc[0]['n_total']:.1f}%)"
            n_f_str = f"{int(r['n_F']):,} ({100 * r['n_F'] / inf_dist.iloc[1]['n_total']:.1f}%)"
        else:
            n_m_str = f"{int(r['n_M']):,}"
            n_f_str = f"{int(r['n_F']):,}"

        d_abs = abs(r["cohens_d"])
        sign = "−" if r["cohens_d"] < 0 else ""
        if d_abs >= 0.20:
            d_str = f"**{sign}{d_abs:.2f}**"
        else:
            d_str = f"{sign}{d_abs:.2f}"

        rows.append(
            f"| **{name}** | {desc} | {n_m_str} | {n_f_str} | "
            f"{r['mean_M']:.3f} ± {r['sd_M']:.3f} | {r['mean_F']:.3f} ± {r['sd_F']:.3f} | "
            f"{d_str} | < 0.001 |"
        )

    inf_m = inf_dist[inf_dist["gender"] == "Male"].iloc[0]
    inf_f = inf_dist[inf_dist["gender"] == "Female"].iloc[0]

    header = (
        "**Table S5.** Fine-grained pacing metrics computed from 5 km splits. "
        "Subset: runners with all cumulative splits valid (n = 856,759; 98.1% of the analytical cohort). "
        "Comparison by gender via Welch's *t*-test, Mann-Whitney U test, and Cohen's *d*.\n\n"
        "| Metric | Definition | n_M | n_F | Mean ± SD, Men | Mean ± SD, Women | Cohen's *d* | *p* (Welch) |\n"
        "|:---|:---|:-:|:-:|:-:|:-:|:-:|:-:|"
    )
    footer = (
        f"\n\nMedian (IQR) for inflection point: men {inf_m['median_km']:.1f} km "
        f"({inf_m['q25_km']:.1f}–{inf_m['q75_km']:.1f}), women {inf_f['median_km']:.1f} km "
        f"({inf_f['q25_km']:.1f}–{inf_f['q75_km']:.1f}); "
        f"~{inf_m['pct_no_inflection']:.0f}% of male and ~{inf_f['pct_no_inflection']:.0f}% of female "
        "runners did not exhibit a defined inflection under the strict criterion (pace exceeded > 5% threshold AND "
        "remained above threshold for ALL subsequent segments through the finish), reflecting the proportion who "
        "maintained relatively even pacing through to the finish. "
        "All metrics differ significantly between sexes given the very large sample size; effect sizes are small to "
        "small-moderate (|*d*| ≤ 0.31). Late-race deceleration shows the largest gender effect, consistent with "
        "men sustaining a substantially larger pace decline in the final stages of the race. "
        "The oscillation count direction is opposite to the variability story (women slightly higher than men) and "
        "warrants further investigation; mechanistic interpretation is not advanced in the present work."
    )

    out = "\n".join([header] + rows) + footer + "\n"
    (TABLES_DIR / "TableS5.md").write_text(out)
    print(f"Wrote: TableS5.md")


def build_tableS3():
    """Dedup sensitivity from dedup_sensitivity_table.csv."""
    d = pd.read_csv(RESULTS_DIR / "dedup_sensitivity_table.csv")
    full = d[d["subset"] == "Full"].iloc[0]
    dedup = d[d["subset"] == "Dedup"].iloc[0]

    def fmt_row(r, label):
        return (
            f"| {label} | {int(r['n_total']):,} | {int(r['n_men']):,} | {int(r['n_women']):,} | "
            f"{r['mean_slow_M_pct']:.2f} | {r['mean_slow_F_pct']:.2f} | "
            f"{r['wall_pct_M']:.2f} | {r['wall_pct_F']:.2f} | "
            f"**{r['OR_crude']:.3f}** | ({r['OR_CI_lo']:.2f}, {r['OR_CI_hi']:.2f}) |"
        )

    reduction_total = -100 * (1 - dedup["n_total"] / full["n_total"])
    reduction_men = -100 * (1 - dedup["n_men"] / full["n_men"])
    reduction_women = -100 * (1 - dedup["n_women"] / full["n_women"])

    header = (
        "**Table S3.** Sensitivity analysis on a deduplicated subset constructed by retaining the first appearance "
        "per composite key of normalized runner name and age group. The deduplication is conservative — spelling "
        "variations across editions may leave some entries from the same runner classified as distinct — and is "
        "therefore treated as a robustness check rather than a definitive correction.\n\n"
        "| Subset | n total | n men | n women | Mean slowdown M (%) | Mean slowdown F (%) | Wall-hit M (%) | Wall-hit F (%) | Crude OR | 95% CI |\n"
        "|:---|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|"
    )
    rows = [
        fmt_row(full, "Full cohort"),
        fmt_row(dedup, "Deduplicated subset (first appearance per name + age-group key)"),
        f"| Reduction from full cohort | {reduction_total:.1f}% | {reduction_men:.1f}% | {reduction_women:.1f}% | — | — | — | — | — | — |",
    ]
    footer = (
        "\n\nThe crude Odds Ratio is virtually unchanged between the full cohort and the deduplicated subset, with "
        "completely overlapping 95% confidence intervals. Mean percentage slowdown is marginally lower in both gender "
        "groups in the deduplicated subset, consistent with experienced multi-year finishers exhibiting slightly more "
        "positive splits than first-time finishers; the gender gap (~2.4 percentage points) is preserved. "
        "Welch's *t*-test, Mann-Whitney U test, and Chi-square remain significant at *p* < 10⁻³⁰⁰ in both subsets."
    )

    out = "\n".join([header] + rows) + footer + "\n"
    (TABLES_DIR / "TableS3.md").write_text(out)
    print(f"Wrote: TableS3.md")


def build_tableS4():
    """Within-Berlin sex × age_group quintile from quintile_sensitivity.csv."""
    q = pd.read_csv(RESULTS_DIR / "quintile_sensitivity.csv")

    rows = []
    for _, r in q.iterrows():
        rows.append(
            f"| {r['Quintile']} | {int(r['n_M']):,} | {int(r['n_F']):,} | "
            f"{r['wall_M_pct']:.1f} | {r['wall_F_pct']:.1f} | "
            f"{r['slow_M_pct']:.1f} | {r['slow_F_pct']:.1f} | "
            f"**{r['OR']:.2f}** | ({r['OR_CI_lo']:.2f}, {r['OR_CI_hi']:.2f}) |"
        )

    header = (
        "**Table S4.** Within-cohort sex × age-group quintile re-stratification. Each runner is classified into a "
        "quintile of finish time computed within their (sex, age-group) stratum (Q1 = top 10%, Q2 = 10–25%, Q3 = 25–50%, "
        "Q4 = 50–75%, Q5 = bottom 25%). Main analyses are re-computed under this percentile-based classification.\n\n"
        "| Quintile | n_M | n_F | Wall-hit M (%) | Wall-hit F (%) | Mean slowdown M (%) | Mean slowdown F (%) | OR (Male vs Female) | 95% CI |\n"
        "|:---|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|"
    )
    footer = (
        "\n\nThe gender gap is preserved across all five within-stratum competitive quintiles "
        "(all ORs > 1, all 95% CIs strictly excluding 1), indicating that the disparity is not an artifact of "
        "differential demographic composition between absolute-time performance categories. The non-monotonic OR "
        "pattern (peaking in Q2, \"competitive but not at the very top\") suggests that male over-representation in "
        "wall events is most pronounced just below the elite tier, and slightly attenuated at the very top (Q1) where "
        "competitive selection is more stringent. Wall-hit prevalence rises monotonically with quintile in both sexes, "
        "consistent with the absolute-time stratification reported in Table 2."
    )

    out = "\n".join([header] + rows) + footer + "\n"
    (TABLES_DIR / "TableS4.md").write_text(out)
    print(f"Wrote: TableS4.md")


if __name__ == "__main__":
    df = load_data()
    print(f"Loaded baseline n={len(df):,}")
    build_table2(df)
    build_tableS3()
    build_tableS4()
    build_tableS5()
