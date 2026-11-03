"""
JalSense: Public Water Data Ingestion & Unified Feature Pipeline
Handles downloading, cleaning, date standardization, Open-Meteo weather matching with caching,
and building unified feature datasets for machine learning.
"""

import logging
from pathlib import Path
from typing import Tuple, Dict, Any, Optional
import requests
import numpy as np
import pandas as pd

from src.config import (
    PUBLIC_WATER_DATA_URL,
    PUBLIC_RAW_DATA_PATH,
    PUBLIC_PROCESSED_DATA_PATH,
    UNIFIED_FEATURES_PATH,
    STUDY_AREA_LATITUDE,
    STUDY_AREA_LONGITUDE,
    STUDY_AREA_ID,
    RAW_DATA_DIR,
    PROCESSED_DATA_DIR,
    SAMPLE_DATA_DIR
)
from src.weather_client import weather_client
from src.features import compute_heat_index, SEASON_MAPPING

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def download_public_water_data(
    url: str = PUBLIC_WATER_DATA_URL,
    target_path: Path = PUBLIC_RAW_DATA_PATH,
    force_download: bool = False
) -> Path:
    """
    Step 1 & 5: Downloads the public water consumption dataset if not already present.
    Documents origin: LukaLike/water-consumption-data (CC-BY-SA).
    """
    target_path.parent.mkdir(parents=True, exist_ok=True)

    if target_path.exists() and not force_download:
        logger.info(f"Public water consumption dataset already exists at {target_path}")
        return target_path

    logger.info(f"Downloading public water consumption dataset from {url}...")
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        with open(target_path, "wb") as f:
            f.write(response.content)
        logger.info(f"Successfully saved {len(response.content)} bytes to {target_path}")
        return target_path
    except Exception as e:
        logger.error(f"Failed to download public dataset from {url}: {e}")
        raise


def load_and_clean_water_data(
    raw_csv_path: Path = PUBLIC_RAW_DATA_PATH
) -> pd.DataFrame:
    """
    Steps 2, 3 & 4:
    - Loads raw high-frequency meter data
    - Standardizes date column (YYYY-MM-DD)
    - Aggregates by day
    - Clearly identifies the target variable: 'water_consumption_litres'
    - Filters out days with negligible sensor sampling (e.g. edge days)
    """
    logger.info(f"Loading raw water consumption data from {raw_csv_path}...")
    raw_df = pd.read_csv(raw_csv_path)

    # 1. Parse timestamps
    # Raw file columns: 'created_at' (epoch seconds), 'sensor_value' (volume pulse)
    if "created_at" in raw_df.columns:
        raw_df["timestamp"] = pd.to_datetime(raw_df["created_at"], unit="s", utc=True)
    elif "timestamp" in raw_df.columns:
        raw_df["timestamp"] = pd.to_datetime(raw_df["timestamp"], utc=True)
    elif "date" in raw_df.columns:
        raw_df["timestamp"] = pd.to_datetime(raw_df["date"], utc=True)
    else:
        raise ValueError(f"Unable to find timestamp column in {raw_df.columns.tolist()}")

    # 2. Extract standard date (YYYY-MM-DD)
    raw_df["date"] = raw_df["timestamp"].dt.strftime("%Y-%m-%d")

    # 3. Target column identification
    value_col = "sensor_value" if "sensor_value" in raw_df.columns else "water_demand_litres"
    if value_col not in raw_df.columns:
        # Fallback to last numeric column
        num_cols = raw_df.select_dtypes(include=[np.number]).columns
        value_col = num_cols[-1]

    logger.info(f"Identified water consumption target column: '{value_col}'")

    # 4. Daily aggregation
    daily_summary = raw_df.groupby("date").agg(
        water_consumption_litres=(value_col, "sum"),
        reading_count=(value_col, "count"),
        peak_reading=(value_col, "max"),
        avg_minute_reading=(value_col, "mean")
    ).reset_index()

    # Filter out partial first/last days with fewer than 500 minutes of records
    daily_clean = daily_summary[daily_summary["reading_count"] >= 500].copy()
    daily_clean["date"] = pd.to_datetime(daily_clean["date"])
    daily_clean = daily_clean.sort_values("date").reset_index(drop=True)
    daily_clean["date_str"] = daily_clean["date"].dt.strftime("%Y-%m-%d")

    # Add study area metadata
    daily_clean["study_area_id"] = STUDY_AREA_ID
    daily_clean["study_area_type"] = "micro_catchment_study_area"
    daily_clean["data_source"] = "LukaLike/water-consumption-data (CC-BY-SA)"

    logger.info(
        f"Cleaned daily series: {len(daily_clean)} days "
        f"({daily_clean['date_str'].min()} to {daily_clean['date_str'].max()}). "
        f"Daily mean consumption: {daily_clean['water_consumption_litres'].mean():.2f} L"
    )

    # Step 6: Save clean processed dataset
    PUBLIC_PROCESSED_DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    daily_clean.to_csv(PUBLIC_PROCESSED_DATA_PATH, index=False)
    logger.info(f"Saved clean processed dataset to {PUBLIC_PROCESSED_DATA_PATH}")

    return daily_clean


def fetch_weather_for_study_period(
    daily_clean: pd.DataFrame,
    latitude: float = STUDY_AREA_LATITUDE,
    longitude: float = STUDY_AREA_LONGITUDE
) -> pd.DataFrame:
    """
    Steps 7, 8 & 9:
    Uses WeatherClient with disk caching to retrieve matching historical Open-Meteo weather
    for the exact dates of the study dataset.
    """
    start_date = daily_clean["date_str"].min()
    end_date = daily_clean["date_str"].max()

    logger.info(f"Fetching Open-Meteo historical weather for period {start_date} to {end_date}...")
    weather_df = weather_client.fetch_historical_weather(
        latitude=latitude,
        longitude=longitude,
        start_date=start_date,
        end_date=end_date
    )
    logger.info(f"Retrieved {len(weather_df)} weather records (cached on disk)")
    return weather_df


def build_unified_feature_dataset(
    water_df: pd.DataFrame,
    weather_df: pd.DataFrame,
    output_path: Path = UNIFIED_FEATURES_PATH
) -> pd.DataFrame:
    """
    Step 10:
    Merges standardized water consumption with Open-Meteo meteorological factors,
    temporal features, time-series lags, and rolling averages into a unified ML-ready feature matrix.
    """
    logger.info("Constructing unified feature dataset...")
    df = water_df.copy()
    df["date"] = pd.to_datetime(df["date_str"])

    # Merge weather on date
    weather_df = weather_df.copy()
    weather_df["date"] = pd.to_datetime(weather_df["date"])

    merged = pd.merge(df, weather_df, on="date", how="left")

    # Impute missing weather if any with forward/median fill
    weather_cols = ["temp_mean", "temp_max", "temp_min", "rainfall_mm", "humidity_pct"]
    for wc in weather_cols:
        if wc in merged.columns:
            merged[wc] = merged[wc].ffill().bfill().fillna(merged[wc].median())

    # 1. Calendar Features
    merged["day_of_week"] = merged["date"].dt.dayofweek
    merged["is_weekend"] = merged["day_of_week"].isin([5, 6]).astype(int)
    merged["month"] = merged["date"].dt.month
    merged["day_of_year"] = merged["date"].dt.dayofyear

    # 2. Season Determination
    def get_season(m):
        if m in [6, 7, 8]:
            return "Summer"
        elif m in [9, 10, 11]:
            return "Autumn"
        elif m in [12, 1, 2]:
            return "Winter"
        return "Spring"

    merged["season"] = merged["month"].apply(get_season)
    season_code_map = {"Winter": 0, "Spring": 1, "Summer": 2, "Autumn": 3}
    merged["season_encoded"] = merged["season"].map(season_code_map).fillna(0).astype(int)

    # 3. Meteorological Interaction (Heat Index)
    merged["heat_index"] = merged.apply(
        lambda r: compute_heat_index(r["temp_mean"], r["humidity_pct"]),
        axis=1
    )

    # 4. Target Variable: water_consumption_litres
    target_series = merged["water_consumption_litres"]

    # 5. Lags with backward shift (shift(1)) to prevent leakage
    merged["consumption_lag_1"] = target_series.shift(1)
    merged["consumption_lag_2"] = target_series.shift(2)
    merged["consumption_lag_7"] = target_series.shift(7)

    # 6. Rolling statistics over past 7 days (shift(1) so today's consumption is excluded)
    shifted_target = target_series.shift(1)
    merged["rolling_mean_7d"] = shifted_target.rolling(window=7, min_periods=1).mean()
    merged["rolling_std_7d"] = shifted_target.rolling(window=7, min_periods=1).std().fillna(0.0)
    merged["rolling_max_7d"] = shifted_target.rolling(window=7, min_periods=1).max()

    # Backfill earliest days with series median
    median_consumption = float(target_series.median())
    merged["consumption_lag_1"] = merged["consumption_lag_1"].fillna(median_consumption)
    merged["consumption_lag_2"] = merged["consumption_lag_2"].fillna(median_consumption)
    merged["consumption_lag_7"] = merged["consumption_lag_7"].fillna(median_consumption)
    merged["rolling_mean_7d"] = merged["rolling_mean_7d"].fillna(median_consumption)
    merged["rolling_max_7d"] = merged["rolling_max_7d"].fillna(median_consumption)

    # Final ordering and selection
    cols_to_save = [
        "date",
        "study_area_id",
        "study_area_type",
        "water_consumption_litres",     # TARGET
        "temp_mean",
        "temp_max",
        "temp_min",
        "rainfall_mm",
        "humidity_pct",
        "heat_index",
        "day_of_week",
        "is_weekend",
        "month",
        "season",
        "season_encoded",
        "consumption_lag_1",
        "consumption_lag_2",
        "consumption_lag_7",
        "rolling_mean_7d",
        "rolling_std_7d",
        "rolling_max_7d",
        "reading_count",
        "data_source"
    ]

    output_df = merged[cols_to_save].copy()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_df.to_csv(output_path, index=False)
    logger.info(f"Saved unified feature dataset to {output_path} ({len(output_df)} rows, {len(cols_to_save)} columns)")

    return output_df


def execute_data_layer_pipeline(force_download: bool = False) -> Dict[str, Any]:
    """
    Executes the full 10-step data layer sequence.
    """
    logger.info("==================================================")
    logger.info("   JalSense: Executing Data Layer Pipeline        ")
    logger.info("==================================================")

    # Step 1: Download/Load
    raw_path = download_public_water_data(force_download=force_download)

    # Step 2, 3, 4, 6: Clean, standardize date, identify target, save processed
    daily_clean = load_and_clean_water_data(raw_path)

    # Step 7, 8, 9: Open-Meteo weather client with caching
    weather_df = fetch_weather_for_study_period(daily_clean)

    # Step 10: Create unified feature dataset
    unified_df = build_unified_feature_dataset(daily_clean, weather_df)

    summary = {
        "status": "success",
        "raw_file": str(raw_path),
        "processed_file": str(PUBLIC_PROCESSED_DATA_PATH),
        "unified_features_file": str(UNIFIED_FEATURES_PATH),
        "records_count": len(unified_df),
        "date_min": str(unified_df["date"].min())[:10],
        "date_max": str(unified_df["date"].max())[:10],
        "mean_water_consumption_litres": round(float(unified_df["water_consumption_litres"].mean()), 2),
        "target_column": "water_consumption_litres",
        "features_list": [
            "temp_mean", "rainfall_mm", "humidity_pct", "heat_index",
            "day_of_week", "is_weekend", "month", "season_encoded",
            "consumption_lag_1", "consumption_lag_2", "consumption_lag_7",
            "rolling_mean_7d", "rolling_std_7d", "rolling_max_7d"
        ],
        "weather_cache_dir": str(weather_client.cache_dir)
    }

    logger.info(f"Data layer completed: {summary['records_count']} rows generated.")
    return summary


if __name__ == "__main__":
    execute_data_layer_pipeline()
