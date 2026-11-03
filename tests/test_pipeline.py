"""
Unit & Pipeline Tests for JalSense Core Modules
"""

import pytest
import pandas as pd
import numpy as np

from src.ingestion import fetch_live_weather, generate_benchmark_dataset
from src.preprocessing import clean_raw_data, chronological_train_test_split
from src.features import extract_features, FEATURE_COLUMNS, compute_heat_index
from src.shortage import assess_water_shortage
from src.prediction import predict_next_day_demand


def test_heat_index_calculation():
    hi = compute_heat_index(30.0, 50.0)
    assert isinstance(hi, float)
    assert hi > 20.0


def test_shortage_assessment_critical():
    # Demand 100,000, Supply 50,000 -> 50% coverage -> CRITICAL
    res = assess_water_shortage(
        predicted_demand_litres=100000.0,
        estimated_supply_litres=50000.0,
        population=1800
    )
    assert res["shortage_risk"] == "CRITICAL"
    assert res["deficit_litres"] == 50000.0
    assert res["tankers_needed"] >= 5
    assert len(res["recommendations"]) > 0


def test_shortage_assessment_low_surplus():
    # Demand 100,000, Supply 120,000 -> 120% coverage -> LOW risk
    res = assess_water_shortage(
        predicted_demand_litres=100000.0,
        estimated_supply_litres=120000.0,
        population=1800
    )
    assert res["shortage_risk"] == "LOW"
    assert res["deficit_litres"] == 0.0
    assert res["surplus_litres"] == 20000.0
    assert res["tankers_needed"] == 0


def test_generate_benchmark_dataset():
    df = generate_benchmark_dataset(start_date="2024-01-01", end_date="2024-01-10")
    assert isinstance(df, pd.DataFrame)
    assert len(df) > 0
    assert "water_demand_litres" in df.columns
    assert "is_synthetic_benchmark" in df.columns
    assert df["is_synthetic_benchmark"].all() == True


def test_extract_features():
    df = generate_benchmark_dataset(start_date="2024-01-01", end_date="2024-01-20")
    feat_df = extract_features(df)
    for col in FEATURE_COLUMNS:
        assert col in feat_df.columns, f"Missing feature: {col}"
    assert not feat_df[FEATURE_COLUMNS].isnull().any().any()


def test_ann_model_architecture():
    from src.models import build_ann_model
    ann = build_ann_model(input_dim=15)
    layer_names = [layer.__class__.__name__ for layer in ann.layers]
    assert "Dense" in layer_names
    assert "BatchNormalization" in layer_names
    assert "Dropout" in layer_names
    # Total dense layers = 4 (128, 64, 32, 1)
    dense_count = sum(1 for name in layer_names if name == "Dense")
    assert dense_count == 4


def test_model_comparison_table_saved():
    from src.config import COMPARISON_TABLE_PATH, METRICS_FILE_PATH
    assert COMPARISON_TABLE_PATH.exists()
    assert METRICS_FILE_PATH.exists()
    df_comp = pd.read_csv(COMPARISON_TABLE_PATH)
    assert len(df_comp) == 4
    assert "XGBoost Regressor" in df_comp["Model"].values
    assert "Random Forest Regressor" in df_comp["Model"].values
    assert "TensorFlow/Keras Deep ANN" in df_comp["Model"].values
    assert "Linear Regression Baseline" in df_comp["Model"].values

