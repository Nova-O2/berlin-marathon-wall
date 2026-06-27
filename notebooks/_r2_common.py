"""Shared utilities for R2 revision analyses.

Extends _r1_common with diagnostics helpers used by r2_logistic_diagnostics.py:
VIF, McFadden pseudo-R², decile calibration, natural cubic spline basis,
Pregibon dbeta summary.

Imports _r1_common so the analytical cohort and feature engineering remain
identical to R1; R2 layers diagnostic instruments on top without changing
the underlying model or data.
"""
from pathlib import Path
import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor

# _r1_common imports removed (2026-05-27, audit Round 3 F-028): _r2_common does not
# use any constants from _r1_common; downstream `r2_logistic_diagnostics.py` imports
# DATA_PATH directly from `_r1_common`.

R2_RESULTS_DIR = Path(__file__).parent / "results" / "r2"
R2_RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def compute_vif(design_df):
    """Return DataFrame [predictor, vif] for each column of a numeric design matrix."""
    return pd.DataFrame(
        {
            "predictor": design_df.columns,
            "vif": [
                variance_inflation_factor(design_df.values, i)
                for i in range(design_df.shape[1])
            ],
        }
    )


def mcfadden_r2(model_result):
    """Return McFadden's pseudo-R² = 1 - (loglik_full / loglik_null)."""
    return 1.0 - (model_result.llf / model_result.llnull)


def decile_calibration(y_true, y_pred_prob, n_bins=10):
    """Return DataFrame with decile bins, mean predicted prob, observed rate, n.

    NOTE: When reported side-by-side, ensure `decile_calibration(...)` and
    `hosmer_lemeshow(..., n_bins=10)` are called with the same `n_bins` to keep
    the decile table and the HL chi² statistic computed on identical bins.
    """
    df = pd.DataFrame({"y": y_true, "p": y_pred_prob})
    df["decile"] = pd.qcut(df["p"], q=n_bins, labels=False, duplicates="drop")
    grouped = df.groupby("decile").agg(
        mean_pred=("p", "mean"),
        observed_rate=("y", "mean"),
        n=("y", "size"),
    )
    grouped["abs_diff"] = (grouped["mean_pred"] - grouped["observed_rate"]).abs()
    assert len(grouped) == n_bins, (
        f"qcut produced {len(grouped)} bins; expected exactly {n_bins} "
        f"(if tied predicted probabilities cause dedup, investigate before reporting)"
    )
    return grouped.reset_index()


def hosmer_lemeshow(y_true, y_pred_prob, n_bins=10):
    """Return (HL chi-square, df, p-value). HL is unreliable at n>10⁴ — report with caveat.

    NOTE: When reported side-by-side, ensure `decile_calibration(...)` and
    `hosmer_lemeshow(..., n_bins=10)` are called with the same `n_bins` to keep
    the decile table and the HL chi² statistic computed on identical bins.
    """
    from scipy.stats import chi2

    df = pd.DataFrame({"y": y_true, "p": y_pred_prob})
    df["bin"] = pd.qcut(df["p"], q=n_bins, labels=False, duplicates="drop")
    grouped = df.groupby("bin").agg(
        observed=("y", "sum"),
        expected=("p", "sum"),
        n=("y", "size"),
    )
    chi2_stat = (
        ((grouped["observed"] - grouped["expected"]) ** 2)
        / (grouped["expected"] * (1 - grouped["expected"] / grouped["n"]))
    ).sum()
    dof = max(n_bins - 2, 1)
    p_value = 1 - chi2.cdf(chi2_stat, dof)
    return float(chi2_stat), int(dof), float(p_value)


def spline_basis_age(age_mid_series, n_knots=3):
    """Natural cubic spline basis at quantile knots, with sum-to-zero constraint
    so the basis does NOT span the constant (avoids collinearity with intercept).
    """
    from patsy import dmatrix

    knots = np.quantile(age_mid_series.dropna(), np.linspace(0.1, 0.9, n_knots))
    formula = f"cr(x, knots={list(knots)}, constraints='center') - 1"
    basis = dmatrix(formula, {"x": age_mid_series}, return_type="dataframe")
    basis.columns = [f"age_spline_{i}" for i in range(basis.shape[1])]
    basis.index = age_mid_series.index   # F-008 fix: preserve input index
    return basis


def calibration_in_the_large_and_slope_cv(y_true, design_matrix, n_splits=10, random_state=42):
    """K-fold cross-validated calibration intercept, slope, and mean OOF probability.

    Refits the logistic model on n_splits-1 folds, predicts the held-out fold,
    then fits a logistic recalibration model y ~ logit(p_cv) on the concatenated
    out-of-fold predictions. Returns (intercept, slope, mean_p_cv) — all three
    genuine (no in-sample tautology).

    Inputs:
        y_true: (n,) array-like of 0/1 outcomes
        design_matrix: (n, p) pandas DataFrame matching the predictor set of
                       the main model (including constant column)
        n_splits: K for K-fold (default 10)
        random_state: seed for fold assignment

    Returns:
        Tuple of three floats:
            - intercept: recalibration logistic intercept (target = 0)
            - slope: recalibration logistic slope (target = 1)
            - mean_p_cv: mean out-of-fold predicted probability (sanity check
              against observed event rate)
    """
    from sklearn.model_selection import KFold
    from numpy import log, asarray, mean

    X = asarray(design_matrix)
    y = asarray(y_true).astype(int)
    p_cv = np.zeros(len(y))

    kf = KFold(n_splits=n_splits, shuffle=True, random_state=random_state)
    for fold_idx, (train_idx, test_idx) in enumerate(kf.split(X)):
        m = sm.Logit(y[train_idx], X[train_idx]).fit(disp=False, maxiter=100)
        p_cv[test_idx] = m.predict(X[test_idx])

    # Clip to avoid logit(0) / logit(1)
    eps = 1e-9
    p_cv_clipped = np.clip(p_cv, eps, 1 - eps)
    logit_p = log(p_cv_clipped / (1 - p_cv_clipped))
    X_recal = sm.add_constant(logit_p)
    recal_model = sm.Logit(y, X_recal).fit(disp=False)
    params = asarray(recal_model.params)
    return float(params[0]), float(params[1]), float(mean(p_cv))
