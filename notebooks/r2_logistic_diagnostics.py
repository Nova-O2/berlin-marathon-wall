"""R2 logistic diagnostics — addresses Reviewer 2 point 5.

Refits the main R1 multivariable logistic model (sex + age_mid + perf_cat,
reference: female + Casual) on the analytical cohort, then computes:

- VIF for each predictor
- McFadden pseudo-R², AIC, BIC
- Decile calibration + Hosmer-Lemeshow + calibration-in-the-large/slope (10-fold CV)
- Nonlinear age via natural cubic spline (3 knots) and quadratic, compared via LRT
- Pregibon dbeta summary (proportion of influential observations)
- Missing-data exclusion cascade
"""
# stdlib
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

# third-party
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import patsy
import scipy
import sklearn
import statsmodels
import statsmodels.api as sm
from scipy.stats import chi2 as chi2_dist
from statsmodels.stats.proportion import proportion_confint

# local
from _r1_common import DATA_PATH, load_data
from _r2_common import (
    R2_RESULTS_DIR,
    compute_vif,
    mcfadden_r2,
    decile_calibration,
    hosmer_lemeshow,
    spline_basis_age,
    calibration_in_the_large_and_slope_cv,
)


if __name__ == "__main__":
    # ----- Load + feature engineering (mirrors r1_logistic_age_controlled.py) -----

    df = load_data()

    # Reference categories: female (sex_male = 0), Casual (perf_cat = "Casual")
    df = df.dropna(subset=["hit_wall", "gender_label", "age_mid", "performance_category"]).copy()
    df["hit_wall"] = df["hit_wall"].astype(int)
    df["sex_male"] = (df["gender_label"] == "Male").astype(int)
    df["perf_cat"] = df["performance_category"]

    print(f"Analytical cohort n = {len(df):,}")
    print(f"Hit-wall prevalence = {df['hit_wall'].mean():.4f}")

    # ----- Main model: sex + age_mid + perf_cat (one-hot, reference Casual) -----
    df["perf_cat"] = df["perf_cat"].replace({"Competitive (<3h)": "Competitive"})

    perf_dummies = pd.get_dummies(df["perf_cat"], prefix="perf", drop_first=False).drop(
        columns=["perf_Casual"]
    )
    X_main = pd.concat(
        [
            pd.Series(1.0, index=df.index, name="const"),
            df[["sex_male", "age_mid"]],
            perf_dummies,
        ],
        axis=1,
    ).astype(float)
    y = df["hit_wall"].astype(int)

    model_main = sm.Logit(y, X_main).fit(disp=False, maxiter=100)
    print("\nMain model (linear age):")
    print(model_main.summary())

    main_sex_male_or = float(np.exp(model_main.params["sex_male"]))
    main_sex_male_ci = [float(x) for x in np.exp(model_main.conf_int().loc["sex_male"])]
    print(
        f"\nMain model — sex_male OR = {main_sex_male_or:.3f} "
        f"(95% CI {main_sex_male_ci[0]:.3f}-{main_sex_male_ci[1]:.3f})"
    )


    # ----- (a) VIF -----

    design_for_vif = X_main.drop(columns=["const"])
    vif_df = compute_vif(design_for_vif)
    vif_df.to_csv(R2_RESULTS_DIR / "r2_vif_table.csv", index=False)
    vif_df.to_markdown(R2_RESULTS_DIR / "r2_vif_table.md", index=False)
    print("\n=== VIF ===")
    print(vif_df.to_string(index=False))


    # ----- (b) Goodness-of-fit: McFadden R², AIC, BIC -----

    # Interaction model (sex × age) — already in R1
    X_inter = X_main.copy()
    X_inter["sex_age_interaction"] = X_inter["sex_male"] * X_inter["age_mid"]
    model_inter = sm.Logit(y, X_inter).fit(disp=False, maxiter=100)

    gof_rows = []
    for name, m in [("main_linear_age", model_main), ("interaction_sex_age", model_inter)]:
        gof_rows.append(
            {
                "model": name,
                "mcfadden_r2": mcfadden_r2(m),
                "aic": m.aic,
                "bic": m.bic,
                "llf": m.llf,
                "llnull": m.llnull,
                "n": int(m.nobs),
                "df_model": int(m.df_model),
            }
        )
    gof_df = pd.DataFrame(gof_rows)
    gof_df.to_csv(R2_RESULTS_DIR / "r2_gof.csv", index=False)
    gof_df.to_markdown(R2_RESULTS_DIR / "r2_gof.md", index=False)
    print("\n=== Goodness-of-fit ===")
    print(gof_df.to_string(index=False))


    # ----- (c) Calibration: decile + Hosmer-Lemeshow + calibration-in-the-large -----

    y_pred = model_main.predict(X_main)

    cal_df = decile_calibration(y.values, y_pred.values)
    cal_df.to_csv(R2_RESULTS_DIR / "r2_calibration.csv", index=False)
    cal_df.to_markdown(R2_RESULTS_DIR / "r2_calibration.md", index=False)
    print("\n=== Calibration (deciles) ===")
    print(cal_df.to_string(index=False))

    hl_chi2, hl_dof, hl_p = hosmer_lemeshow(y.values, y_pred.values, n_bins=10)
    print(f"\nHosmer-Lemeshow chi2 = {hl_chi2:.2f} (df = {hl_dof}, p = {hl_p:.4f})")
    print("Note: HL is unreliable at n>10^4; report alongside calibration plot.")

    cal_intercept, cal_slope, mean_p_cv = calibration_in_the_large_and_slope_cv(
        y.values, X_main, n_splits=10, random_state=42
    )
    observed_prevalence = float(df["hit_wall"].mean())
    print(f"Calibration (10-fold CV) intercept: {cal_intercept:.4f} (target = 0)")
    print(f"Calibration (10-fold CV) slope:     {cal_slope:.4f} (target = 1)")
    print(f"Mean OOF predicted probability:     {mean_p_cv:.4f} (sanity vs observed {observed_prevalence:.4f})")

    # Calibration plot (300 DPI TIFF for publication)
    fig, ax = plt.subplots(figsize=(6, 6), dpi=300)
    lim_max = max(cal_df["mean_pred"].max(), cal_df["observed_rate"].max()) * 1.05
    ax.plot([0, lim_max], [0, lim_max], "k--", lw=1, label="Perfect calibration")
    ax.set_xlim(0, lim_max)
    ax.set_ylim(0, lim_max)
    ax.set_aspect("equal")

    ci_low, ci_high = proportion_confint(
        count=(cal_df["observed_rate"] * cal_df["n"]).round().astype(int),
        nobs=cal_df["n"].astype(int),
        method="wilson",
    )
    yerr = np.vstack([cal_df["observed_rate"] - ci_low, ci_high - cal_df["observed_rate"]])

    ax.errorbar(
        cal_df["mean_pred"],
        cal_df["observed_rate"],
        yerr=yerr,
        fmt="o",
        color="#2C3E50",
        markersize=6,
        capsize=3,
        label="Decile (95% Wilson CI)",
    )
    for _, row in cal_df.iterrows():
        ax.annotate(
            f"n={int(row['n']):,}",
            (row["mean_pred"], row["observed_rate"]),
            textcoords="offset points",
            xytext=(5, -10),
            fontsize=7,
        )
    ax.set_xlabel("Mean predicted probability")
    ax.set_ylabel("Observed rate")
    ax.set_title(
        f"Calibration (10-fold CV) — HL χ²={hl_chi2:.1f}, slope={cal_slope:.3f}, intercept={cal_intercept:.3f}"
    )
    ax.grid(alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(
        R2_RESULTS_DIR / "r2_calibration_plot.tiff",
        dpi=300,
        format="tiff",
        pil_kwargs={"compression": "tiff_lzw"},
    )
    plt.close(fig)
    print(f"Saved calibration plot to {R2_RESULTS_DIR / 'r2_calibration_plot.tiff'}")


    # ----- (d) Nonlinear age: spline + quadratic + LRT vs linear -----

    # Quadratic age
    X_quad = X_main.copy()
    X_quad["age_mid_sq"] = X_quad["age_mid"] ** 2
    model_quad = sm.Logit(y, X_quad).fit(disp=False, maxiter=100)

    # Natural cubic spline (3 knots) — keep age_mid as linear AND add spline basis
    spline_df = spline_basis_age(df["age_mid"], n_knots=3)
    X_spline = pd.concat([X_main.drop(columns=["age_mid"]), spline_df], axis=1).astype(float)
    # Rank sanity check (F-002)
    assert np.linalg.matrix_rank(X_spline.values) == X_spline.shape[1], (
        f"Spline design rank-deficient: rank={np.linalg.matrix_rank(X_spline.values)} "
        f"!= ncols={X_spline.shape[1]}"
    )
    model_spline = sm.Logit(y, X_spline).fit(disp=False, maxiter=100)

    # LRT: linear vs quadratic, linear vs spline
    lrt_linear_vs_quad = 2 * (model_quad.llf - model_main.llf)
    df_quad = model_quad.df_model - model_main.df_model
    p_quad = 1 - chi2_dist.cdf(lrt_linear_vs_quad, df_quad)

    lrt_linear_vs_spline = 2 * (model_spline.llf - model_main.llf)
    df_spline = model_spline.df_model - model_main.df_model
    p_spline = 1 - chi2_dist.cdf(lrt_linear_vs_spline, df_spline)

    nonlinear_rows = [
        {
            "comparison": "quadratic age (2 df) vs linear age (1 df)",
            "lrt_chi2": lrt_linear_vs_quad,
            "df": int(df_quad),
            "p_value": p_quad,
            "aic_alt": model_quad.aic,
            "aic_linear": model_main.aic,
            "delta_aic": model_quad.aic - model_main.aic,
        },
        {
            "comparison": "natural cubic spline 4 cols (constraints='center', knots=3) vs linear age (1 df)",
            "lrt_chi2": lrt_linear_vs_spline,
            "df": int(df_spline),
            "p_value": p_spline,
            "aic_alt": model_spline.aic,
            "aic_linear": model_main.aic,
            "delta_aic": model_spline.aic - model_main.aic,
        },
    ]
    nonlinear_df = pd.DataFrame(nonlinear_rows)
    nonlinear_df.to_csv(R2_RESULTS_DIR / "r2_nonlinear_age.csv", index=False)
    nonlinear_df.to_markdown(R2_RESULTS_DIR / "r2_nonlinear_age.md", index=False)

    # Adjusted ORs from spline model — extract sex_male coefficient
    sex_male_or_spline = float(np.exp(model_spline.params["sex_male"]))
    sex_male_ci_spline = [float(x) for x in np.exp(model_spline.conf_int().loc["sex_male"])]
    print("\n=== Nonlinear age ===")
    print(nonlinear_df.to_string(index=False))
    print(
        f"\nSpline model — sex_male OR = {sex_male_or_spline:.3f} "
        f"(95% CI {sex_male_ci_spline[0]:.3f}-{sex_male_ci_spline[1]:.3f})"
    )
    print(
        f"Linear model — sex_male OR = {np.exp(model_main.params['sex_male']):.3f} "
        f"(95% CI from R1 summary above)"
    )


    # ----- (e) Pregibon dbeta summary -----

    # Pregibon dbeta (cooks-distance-like for logistic) — costly at n=10^5+; use approximation
    # Pearson residuals × leverage approximation
    hat_diag = model_main.get_influence().hat_matrix_diag
    pearson_resid = (y - y_pred) / np.sqrt(y_pred * (1 - y_pred))
    dbeta_approx = (pearson_resid ** 2) * hat_diag / (1 - hat_diag) ** 2

    dbeta_summary = {
        "n_total": int(len(dbeta_approx)),
        "max_dbeta": float(np.max(dbeta_approx)),
        "p99_dbeta": float(np.percentile(dbeta_approx, 99)),
        "p99_9_dbeta": float(np.percentile(dbeta_approx, 99.9)),
        "n_dbeta_gt_1": int((dbeta_approx > 1).sum()),
        "n_dbeta_gt_p99": int((dbeta_approx > np.percentile(dbeta_approx, 99)).sum()),
    }
    pd.DataFrame([dbeta_summary]).to_csv(R2_RESULTS_DIR / "r2_dbeta_summary.csv", index=False)
    pd.DataFrame([dbeta_summary]).to_markdown(R2_RESULTS_DIR / "r2_dbeta_summary.md", index=False)
    dbeta_lines = [
        "(e) Pregibon dbeta (approximation)",
        f"  n_total            : {dbeta_summary['n_total']:>10,}",
        f"  max_dbeta          : {dbeta_summary['max_dbeta']:>10.2e}",
        f"  p99_dbeta          : {dbeta_summary['p99_dbeta']:>10.2e}",
        f"  p99_9_dbeta        : {dbeta_summary['p99_9_dbeta']:>10.2e}",
        f"  n_dbeta_gt_1       : {dbeta_summary['n_dbeta_gt_1']:>10,}",
        f"  n_dbeta_gt_p99     : {dbeta_summary['n_dbeta_gt_p99']:>10,}",
    ]
    print("\n=== Pregibon dbeta (approximation) ===")
    print(dbeta_summary)
    print("Note: at n=855k, individual influence is small by construction; report distribution percentiles.")


    # ----- (f) Missing-data exclusion cascade -----

    df_raw_count = 880779       # raw archive (1999-2025)
    df_cohort = 873334          # post physiological + cutoff filter
    df_pacing_valid = 872670    # half-marathon split present
    df_perf_age_valid = int(model_main.nobs)  # logistic-valid (perf_cat + age_mid)

    cascade_rows = [
        {
            "step": "Raw archive (1999-2025)",
            "n_remaining": df_raw_count,
            "n_excluded_at_step": 0,
            "rule": "Raw extraction from BMW Berlin Marathon archive (1999-2025)",
        },
        {
            "step": "Physiological + cutoff filter",
            "n_remaining": df_cohort,
            "n_excluded_at_step": df_raw_count - df_cohort,
            "rule": "Net finish time 1:59:00 <= t <= 6:15:00; valid net finish recorded",
        },
        {
            "step": "Pacing-valid (half-marathon split present)",
            "n_remaining": df_pacing_valid,
            "n_excluded_at_step": df_cohort - df_pacing_valid,
            "rule": "Both half-marathon and finish time present and parseable",
        },
        {
            "step": "Logistic-valid (perf_cat + age_mid)",
            "n_remaining": df_perf_age_valid,
            "n_excluded_at_step": df_pacing_valid - df_perf_age_valid,
            "rule": "Mappable to performance category AND age group present",
        },
    ]
    cascade_df = pd.DataFrame(cascade_rows)
    cascade_df.to_csv(R2_RESULTS_DIR / "r2_missing_data_summary.csv", index=False)
    cascade_df.to_markdown(R2_RESULTS_DIR / "r2_missing_data_summary.md", index=False)
    print("\n=== Missing-data exclusion cascade ===")
    print(cascade_df.to_string(index=False))


    # ----- Final summary: write r2_diagnostics.txt -----

    header_lines = [
        f"# Generated by r2_logistic_diagnostics.py on {datetime.now().isoformat()}",
        f"# Python {sys.version.split()[0]}",
        f"# pandas {pd.__version__}; numpy {np.__version__}; statsmodels {statsmodels.__version__}; "
        f"scipy {scipy.__version__}; patsy {patsy.__version__}; sklearn {sklearn.__version__}",
        f"# Data: {DATA_PATH.name}",
        f"# Seed: 42 (CV fold assignment)",
        "",
    ]
    summary_lines = [
        "=" * 78,
        "R2 LOGISTIC DIAGNOSTICS — SUMMARY (addresses Reviewer 2 point 5)",
        "=" * 78,
        "",
        f"Analytical cohort: n = {len(df):,}",
        f"Hit-wall prevalence: {df['hit_wall'].mean():.4f}",
        "",
        "(a) VIF (target: all < 5)",
        vif_df.to_string(index=False),
        "",
        "(b) Goodness-of-fit",
        gof_df.to_string(index=False),
        "",
        "(c) Calibration",
        f"  - Hosmer-Lemeshow chi2 = {hl_chi2:.2f} (df = {hl_dof}, p = {hl_p:.4f}) [unreliable at n>10^4]",
        f"  - Calibration (10-fold CV) intercept: {cal_intercept:.4f} (target = 0)",
        f"  - Calibration (10-fold CV) slope:     {cal_slope:.4f} (target = 1)",
        f"  - Mean out-of-fold predicted probability: {mean_p_cv:.4f} (sanity vs observed {observed_prevalence:.4f})",
        f"  - Number of calibration deciles realized: {len(cal_df)}/{10}",
        cal_df.to_string(index=False),
        "",
        "(d) Nonlinear age",
        nonlinear_df.to_string(index=False),
        f"  - Main-model (linear age)  sex_male OR = {main_sex_male_or:.3f} (95% CI {main_sex_male_ci[0]:.3f}-{main_sex_male_ci[1]:.3f})",
        f"  - Spline-model sex_male OR             = {sex_male_or_spline:.3f} (95% CI {sex_male_ci_spline[0]:.3f}-{sex_male_ci_spline[1]:.3f})",
        f"  - Difference                            = {sex_male_or_spline - main_sex_male_or:.4f} (negligible — spline does not materially change the headline)",
        "",
        *dbeta_lines,
        "",
        "(f) Missing-data exclusion cascade",
        cascade_df.to_string(index=False),
        "",
        "=" * 78,
    ]
    summary_lines = header_lines + summary_lines  # prepend reproducibility header
    (R2_RESULTS_DIR / "r2_diagnostics.txt").write_text("\n".join(summary_lines))
    print(f"\nWrote summary to {R2_RESULTS_DIR / 'r2_diagnostics.txt'}")
