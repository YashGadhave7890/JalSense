"""
JalSense: Data Preprocessing Module
Handles time-series cleaning, outlier mitigation, chronological splitting, and validation.
"""

import logging
from typing import Tuple, Dict, Any
import numpy as np
import pandas as pd
from src.config import PROCESSED_DATA_DIR

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def clean_raw_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans raw village water consumption dataset:
    - Parses dates
    - Validates columns
    - Sorts chronologically per village
    - Handles missing values via forward/backward fill and medians
    - Clips physically impossible values (negative demand, negative rainfall)
    """
    df = df.copy()

    # Convert date to datetime
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values(by=["village_id", "date"]).reset_index(drop=True)

    # Impute missing weather/consumption values if any
    num_cols = ["temp_mean", "rainfall_mm", "humidity_pct", "population", "daily_supply_litres", "water_demand_litres"]
    for col in num_cols:
        if col in df.columns:
            # Per-village forward fill then median fill
            df[col] = df.groupby("village_id")[col].transform(lambda x: x.ffill().bfill())
            if df[col].isnull().any():
                df[col] = df[col].fillna(df[col].median())

    # Sanity bounds
    if "rainfall_mm" in df.columns:
        df["rainfall_mm"] = df["rainfall_mm"].clip(lower=0.0)
    if "humidity_pct" in df.columns:
        df["humidity_pct"] = df["humidity_pct"].clip(lower=5.0, upper=100.0)
    if "water_demand_litres" in df.columns:
        df["water_demand_litres"] = df["water_demand_litres"].clip(lower=100.0)
    if "daily_supply_litres" in df.columns:
        df["daily_supply_litres"] = df["daily_supply_litres"].clip(lower=0.0)

    # Calculate actual LPCD
    if "population" in df.columns and "water_demand_litres" in df.columns:
        df["lpcd_actual"] = (df["water_demand_litres"] / df["population"]).round(2)

    logger.info(f"Cleaned dataset: {len(df)} records across {df['village_id'].nunique()} villages.")
    return df


def chronological_train_test_split(
    df: pd.DataFrame,
    test_days: int = 60
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Performs strict chronological time-based split to avoid lookahead data leakage.
    The last `test_days` per village are held out for model evaluation.
    """
    df = df.sort_values(by=["village_id", "date"]).reset_index(drop=True)
    train_dfs = []
    test_dfs = []

    for _, group in df.groupby("village_id"):
        if len(group) <= test_days:
            split_idx = int(len(group) * 0.8)
        else:
            split_idx = len(group) - test_days
        train_dfs.append(group.iloc[:split_idx])
        test_dfs.append(group.iloc[split_idx:])

    train_df = pd.concat(train_dfs, ignore_index=True)
    test_df = pd.concat(test_dfs, ignore_index=True)

    logger.info(f"Chronological split complete: Train={len(train_df)} rows, Test={len(test_df)} rows.")
    return train_df, test_df


def chronological_train_val_test_split(
    df: pd.DataFrame,
    group_col: str = "village_id",
    val_ratio: float = 0.15,
    test_ratio: float = 0.15
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Strict 3-way chronological time-series train / validation / test split.
    Guarantees:
    - Zero random shuffling
    - Time-ordered splits: Train -> Validation -> Test
    - No future data leakage
    """
    df = df.copy()
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])
    
    sort_cols = [group_col, "date"] if group_col in df.columns else ["date"]
    df = df.sort_values(by=sort_cols).reset_index(drop=True)

    train_chunks = []
    val_chunks = []
    test_chunks = []

    if group_col in df.columns:
        groups = [g for _, g in df.groupby(group_col)]
    else:
        groups = [df]

    for grp in groups:
        n = len(grp)
        n_test = max(1, int(n * test_ratio))
        n_val = max(1, int(n * val_ratio))
        n_train = n - n_val - n_test

        train_chunks.append(grp.iloc[:n_train])
        val_chunks.append(grp.iloc[n_train:n_train + n_val])
        test_chunks.append(grp.iloc[n_train + n_val:])

    train_df = pd.concat(train_chunks, ignore_index=True)
    val_df = pd.concat(val_chunks, ignore_index=True)
    test_df = pd.concat(test_chunks, ignore_index=True)

    logger.info(
        f"Chronological 3-way Split: Train={len(train_df)}, "
        f"Val={len(val_df)}, Test={len(test_df)} (No shuffling)."
    )
    return train_df, val_df, test_df



def save_processed_data(df: pd.DataFrame, filename: str = "village_water_demand_clean.csv") -> str:
    """Saves cleaned DataFrame to data/processed directory."""
    out_path = PROCESSED_DATA_DIR / filename
    df.to_csv(out_path, index=False)
    logger.info(f"Saved processed data to {out_path}")
    return str(out_path)
