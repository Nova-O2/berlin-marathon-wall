"""Shared utilities for R1 revision analyses.

Loads the wall paper baseline dataset (n=873,334, locked across revision
rounds) and computes wall-paper-specific features: percentage_slowdown,
hit_wall, performance_category, age_mid.

The baseline parquet is paper-individualized — each revision round operates
on the same immutable cohort as the R0 submission, allowing direct
comparison of any new analysis to the original headline numbers.
"""
from pathlib import Path
import pandas as pd
import numpy as np

DATA_PATH = Path(__file__).parent.parent / "data" / "wall_baseline_873k.parquet"
DEDUP_SUBSET_PATH = Path(__file__).parent.parent / "data" / "dedup_subset.parquet"
RESULTS_DIR = Path(__file__).parent / "results" / "r1"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# Color palette (Nova O2 research convention)
COLOR_MEN = "#7F7F7F"     # grey
COLOR_WOMEN = "#D62728"   # red
COLOR_OVERALL = "#2C3E50" # dark slate

# Performance category cutoffs (in seconds; finish time)
PERF_CUTOFFS = [
    (0, 3 * 3600, "Competitive (<3h)"),
    (3 * 3600, 3.5 * 3600, "Advanced"),
    (3.5 * 3600, 4 * 3600, "Intermediate"),
    (4 * 3600, 4.5 * 3600, "Recreational"),
    (4.5 * 3600, float("inf"), "Casual"),
]

# Standard age groups (5-year bins, 20-80) — filter noise out
VALID_AGE_GROUPS = ["20", "25", "30", "35", "40", "45", "50", "55", "60", "65", "70", "75", "80"]

# Age midpoints (for logistic regression continuous age proxy)
AGE_MIDPOINT = {
    "20": 22, "25": 27, "30": 32, "35": 37, "40": 42, "45": 47,
    "50": 52, "55": 57, "60": 62, "65": 67, "70": 72, "75": 77, "80": 82,
}

SPLIT_COLS_RAW = ["5km", "10km", "15km", "20km", "half", "25km", "30km", "35km", "40km"]


def parse_time_string(s):
    """Parse HH:MM:SS or MM:SS string to seconds. Returns NaN on failure."""
    s = str(s).strip()
    if pd.isna(s) or s in ("-", "", "nan"):
        return np.nan
    try:
        parts = s.split(":")
        if len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
        elif len(parts) == 2:
            return int(parts[0]) * 60 + float(parts[1])
        return np.nan
    except (ValueError, IndexError):
        return np.nan


def assign_perf_cat(net_time_sec):
    if pd.isna(net_time_sec):
        return None
    for lo, hi, label in PERF_CUTOFFS:
        if lo <= net_time_sec < hi:
            return label
    return None


def load_data(filter_age: bool = False) -> pd.DataFrame:
    """Load wall paper baseline (873,334 finishers) with R1 features computed.

    Returns DataFrame with added columns:
    - <col>_sec: numeric seconds for each split column (5km_sec, 10km_sec, etc.)
    - half_sec, net_time_sec: aliases
    - percentage_slowdown: 100 * (second_half / first_half - 1) where halves
      are time-from-start to half-marathon and from half-marathon to finish
    - hit_wall: int (percentage_slowdown >= 20)
    - performance_category: 5-level category from finish time
    - age_mid: continuous age (midpoint of age_group bin); NaN if non-standard
    - gender_label: "Male" or "Female" mapped from "M" / "F"

    If filter_age=True, restricts to standard 5-year bins (20-80).
    Default False — preserves the 873,334 baseline as-is for headline analyses;
    age-conditioned analyses (Q2 logistic) drop NaN age_mid internally.
    """
    df = pd.read_parquet(DATA_PATH)

    # Parse all split columns to seconds
    for col in SPLIT_COLS_RAW:
        if col in df.columns:
            df[f"{col}_sec"] = df[col].apply(parse_time_string)
    df["net_time_sec"] = df["time_seconds"]
    # half_sec was already created by the parse loop above; no further work needed

    # Pacing metrics — first/second half split
    # Mask invalid half_sec (NaN or 0 — DNS/DNF transponder issues)
    valid_half = df["half_sec"].notna() & (df["half_sec"] > 0)
    first_half = df["half_sec"].where(valid_half)
    second_half = (df["net_time_sec"] - df["half_sec"]).where(valid_half)
    df["percentage_slowdown"] = 100.0 * (second_half / first_half - 1.0)
    # hit_wall as int (NaN preserved for runners without valid pacing)
    df["hit_wall"] = (df["percentage_slowdown"] >= 20).astype(float)
    df.loc[df["percentage_slowdown"].isna(), "hit_wall"] = np.nan

    # Performance category
    df["performance_category"] = df["net_time_sec"].apply(assign_perf_cat)

    # Age cleanup
    df["age_str"] = df["age_group"].astype(str)
    if filter_age:
        df = df[df["age_str"].isin(VALID_AGE_GROUPS)].copy()
    df["age_mid"] = df["age_str"].map(AGE_MIDPOINT)

    # Gender label
    df["gender_label"] = df["gender"].map({"M": "Male", "F": "Female"})

    return df


def save_results(df: pd.DataFrame, name: str):
    """Save results table as CSV + markdown. Returns (csv_path, md_path)."""
    csv_path = RESULTS_DIR / f"{name}.csv"
    md_path = RESULTS_DIR / f"{name}.md"
    df.to_csv(csv_path, index=False)
    df.to_markdown(md_path, index=False, floatfmt=".4f")
    print(f"Saved: {csv_path.name}, {md_path.name}")
    return csv_path, md_path
