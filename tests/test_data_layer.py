"""
Tests for JalSense Data Layer & Weather Client
Validates public data loading, date standardization, target identification,
weather client responses, and caching mechanism.
"""

import pytest
import pandas as pd
from pathlib import Path

from src.config import PUBLIC_PROCESSED_DATA_PATH, UNIFIED_FEATURES_PATH
from src.weather_client import WeatherClient
from src.data_pipeline import (
    load_and_clean_water_data,
    build_unified_feature_dataset,
    execute_data_layer_pipeline
)


def test_weather_client_caching(tmp_path):
    """Verifies that weather client correctly caches responses on disk."""
    client = WeatherClient(cache_dir=tmp_path)
    
    # First fetch (network call)
    res1 = client.fetch_current_and_forecast(18.91, 74.40, days=2)
    assert "forecast" in res1
    assert len(res1["forecast"]) == 2
    assert res1.get("cache_hit") is False
    
    # Second fetch (must hit cache)
    res2 = client.fetch_current_and_forecast(18.91, 74.40, days=2)
    assert "forecast" in res2
    assert res2.get("cache_hit") is True


def test_processed_public_water_dataset_exists_and_valid():
    """Validates the processed public water dataset schema and target."""
    assert PUBLIC_PROCESSED_DATA_PATH.exists()
    df = pd.read_csv(PUBLIC_PROCESSED_DATA_PATH)
    
    # Check date column standardization
    assert "date" in df.columns
    # Check ISO format YYYY-MM-DD
    sample_date = str(df["date"].iloc[0])
    assert len(sample_date.split("-")) == 3
    
    # Check water-consumption target
    assert "water_consumption_litres" in df.columns
    assert (df["water_consumption_litres"] >= 0).all()
    assert df["study_area_id"].iloc[0] == "STUDY_RES_01"


def test_unified_features_dataset_exists_and_valid():
    """Validates the unified feature dataset."""
    assert UNIFIED_FEATURES_PATH.exists()
    df = pd.read_csv(UNIFIED_FEATURES_PATH)
    
    required_cols = [
        "date",
        "study_area_id",
        "water_consumption_litres",
        "temp_mean",
        "rainfall_mm",
        "humidity_pct",
        "heat_index",
        "day_of_week",
        "is_weekend",
        "month",
        "season_encoded",
        "consumption_lag_1",
        "consumption_lag_2",
        "consumption_lag_7",
        "rolling_mean_7d",
        "rolling_std_7d",
        "rolling_max_7d"
    ]
    
    for col in required_cols:
        assert col in df.columns, f"Missing required column: {col}"
    
    assert len(df) > 0
    assert not df[required_cols].isnull().any().any()
