"""Build the analytical baseline (n = 873,334) from the raw Berlin Marathon CSV.

Input : data/Dataset_Berlin_Marathon_1999-2025_original.csv  (Zenodo 10.5281/zenodo.19342683)
Output: data/wall_baseline_873k.parquet  (input to the r1_*/r2_* analyses via _r1_common.py)

Transformation (mirrors CLEANING.ipynb, retaining the 5 km-split checkpoints):
  - normalize column names (sex->gender, nation->country, age_category->age_group, final->net_time)
  - parse net finish time to seconds
  - apply the physiological + cutoff filter: 1:59:00 <= net <= 6:15:00 with a valid net time
Run: python notebooks/build_wall_baseline.py
"""
from pathlib import Path

import numpy as np
import pandas as pd

DATA = Path(__file__).resolve().parent.parent / "data"
RAW = DATA / "Dataset_Berlin_Marathon_1999-2025_original.csv"
OUT = DATA / "wall_baseline_873k.parquet"

CHECKPOINTS = ["5km", "10km", "15km", "20km", "half", "25km", "30km", "35km", "40km"]
COL_ORDER = ["year", "gender", "name", "country", "starting_num", "age_group",
             *CHECKPOINTS, "net_time", "time_seconds"]
LO_SECONDS = 119 * 60      # 1:59:00
HI_SECONDS = 375 * 60      # 6:15:00

# Gender harmonization (raw archive uses M / W; harmonize to M / F)
GENDER_MAP = {
    "m": "M", "män": "M", "men": "M", "h": "M",
    "w": "F", "f": "F", "fra": "F", "women": "F", "d": "F",
}


def parse_time_to_seconds(value) -> float:
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return np.nan
    s = str(value).strip()
    if s in ("", "-", "–", "DNF", "DNS"):
        return np.nan
    parts = s.split(":")
    try:
        if len(parts) == 3:
            h, m, sec = parts
        elif len(parts) == 2:
            h, m, sec = "0", parts[0], parts[1]
        else:
            return np.nan
        return int(h) * 3600 + int(m) * 60 + float(sec)
    except ValueError:
        return np.nan


def main() -> None:
    df = pd.read_csv(RAW, sep=";", encoding="utf-8", low_memory=False)
    df = df.rename(columns={"sex": "gender", "nation": "country",
                            "age_category": "age_group", "final": "net_time"})
    df["gender"] = df["gender"].astype(str).str.lower().str[:3].map(GENDER_MAP).fillna("Unknown")
    df["time_seconds"] = df["net_time"].map(parse_time_to_seconds)
    df = df[df["time_seconds"].notna()
            & df["time_seconds"].between(LO_SECONDS, HI_SECONDS)].copy()
    for col in ("starting_num", "age_group"):
        df[col] = df[col].astype("string")
    df = df[COL_ORDER].reset_index(drop=True)
    df.to_parquet(OUT, engine="pyarrow")
    print(f"Wrote {OUT.name}: {len(df):,} rows x {df.shape[1]} cols")


if __name__ == "__main__":
    main()
