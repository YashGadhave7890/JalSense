"""
JalSense: Feature Engineering Module
Builds temporal, meteorological, demographic, lag, and rolling features for water demand forecasting.
"""

import logging
from typing import List, Tuple
import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

SEASON_MAPPING = {
    "Winter": 0,
    "Summer": 1,
    "Monsoon": 2,
    "Post-Monsoon": 3
}

FEATURE_COLUMNS = [
    "population",
    "temp_mean",
    "rainfall_mm",
    "humidity_pct",
    "heat_index",
    "day_of_week",
    "is_weekend",
    "month",
    "season_encoded",
    "demand_lag_1",
    "demand_lag_2",
    "demand_lag_7",
    "rolling_mean_7d",
    "rolling_std_7d",
    "rolling_max_7d"
]

TARGET_COLUMN = "water_demand_litres"


def compute_heat_index(temp_c: float, humidity: float) -> float:
    """
    Simplified Steadman heat index approximation in Celsius.
    """
    # Simple Rothfusz formula approximation
    hi = temp_c + 0.33 * (humidity / 100.0 * 6.105 * np.exp((17.27 * temp_c) / (237.7 + temp_c))) - 4.0
    return float(np.round(hi, 2))


def extract_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Transforms raw/cleaned time series DataFrame into model-ready feature matrix.
    Generates:
    - Calendar features: day_of_week, is_weekend, month, day_of_year
    - Seasonal encoding
    - Meteorological indices: heat_index
    - Grouped lag features: demand_lag_1, demand_lag_2, demand_lag_7
    - Grouped rolling window statistics: rolling_mean_7d, rolling_std_7d, rolling_max_7d
    """
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values(by=["village_id", "date"]).reset_index(drop=True)

    # 1. Calendar features
    df["day_of_week"] = df["date"].dt.dayofweek
    df["is_weekend"] = df["day_of_week"].isin([5, 6]).astype(int)
    df["month"] = df["date"].dt.month
    df["day_of_year"] = df["date"].dt.dayofyear

    # 2. Season mapping
    if "season" not in df.columns or df["season"].isnull().any():
        def assign_season(m):
            if m in [4, 5, 6]:
                return "Summer"
            elif m in [7, 8, 9]:
                return "Monsoon"
            elif m in [10, 11]:
                return "Post-Monsoon"
            return "Winter"
        df["season"] = df["month"].apply(assign_season)

    df["season_encoded"] = df["season"].map(SEASON_MAPPING).fillna(0).astype(int)

    # 3. Meteorological Interaction
    df["heat_index"] = df.apply(
        lambda r: compute_heat_index(r["temp_mean"], r["humidity_pct"]),
        axis=1
    )

    # 4. Grouped Lag & Rolling Features (per village)
    # Using shift(1) ensures strictly past data is used, eliminating lookahead bias
    grouped = df.groupby("village_id")["water_demand_litres"]

    df["demand_lag_1"] = grouped.shift(1)
    df["demand_lag_2"] = grouped.shift(2)
    df["demand_lag_7"] = grouped.shift(7)

    # Rolling statistics over previous 7 days (shift(1) so today's target is not included)
    shifted = grouped.shift(1)
    df["rolling_mean_7d"] = shifted.groupby(df["village_id"]).transform(
        lambda s: s.rolling(window=7, min_periods=1).mean()
    )
    df["rolling_std_7d"] = shifted.groupby(df["village_id"]).transform(
        lambda s: s.rolling(window=7, min_periods=1).std()
    ).fillna(0.0)
    df["rolling_max_7d"] = shifted.groupby(df["village_id"]).transform(
        lambda s: s.rolling(window=7, min_periods=1).max()
    )

    # Fill any initial missing lag periods with base estimation (population * 55 LPCD)
    base_demand = df["population"] * 55.0
    df["demand_lag_1"] = df["demand_lag_1"].fillna(base_demand)
    df["demand_lag_2"] = df["demand_lag_2"].fillna(base_demand)
    df["demand_lag_7"] = df["demand_lag_7"].fillna(base_demand)
    df["rolling_mean_7d"] = df["rolling_mean_7d"].fillna(base_demand)
    df["rolling_max_7d"] = df["rolling_max_7d"].fillna(base_demand)
    df["rolling_std_7d"] = df["rolling_std_7d"].fillna(0.0)

    logger.info(f"Feature extraction complete. Feature columns: {FEATURE_COLUMNS}")
    return df


def prepare_train_test_matrices(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame
) -> Tuple[pd.DataFrame, pd.Series, pd.DataFrame, pd.Series]:
    """
    Extracts features and separates feature matrices (X_train, X_test)
    and target series (y_train, y_test).
    """
    train_feat = extract_features(train_df)
    test_feat = extract_features(test_df)

    X_train = train_feat[FEATURE_COLUMNS]
    y_train = train_feat[TARGET_COLUMN]

    X_test = test_feat[FEATURE_COLUMNS]
    y_test = test_feat[TARGET_COLUMN]

    return X_train, y_train, X_test, y_test


def prepare_train_val_test_matrices(
    train_df: pd.DataFrame,
    val_df: pd.DataFrame,
    test_df: pd.DataFrame
) -> Tuple[pd.DataFrame, pd.Series, pd.DataFrame, pd.Series, pd.DataFrame, pd.Series]:
    """
    Extracts feature matrices and targets for train, validation, and test splits.
    """
    train_feat = extract_features(train_df)
    val_feat = extract_features(val_df)
    test_feat = extract_features(test_df)

    X_train = train_feat[FEATURE_COLUMNS]
    y_train = train_feat[TARGET_COLUMN]

    X_val = val_feat[FEATURE_COLUMNS]
    y_val = val_feat[TARGET_COLUMN]

    X_test = test_feat[FEATURE_COLUMNS]
    y_test = test_feat[TARGET_COLUMN]

    return X_train, y_train, X_val, y_val, X_test, y_test

