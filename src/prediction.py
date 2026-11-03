"""
JalSense: Inference & Demand Prediction Pipeline
Coordinates feature assembly, live weather injection, model inference, and shortage assessment.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import pandas as pd
import numpy as np

from src.config import VILLAGES_CONFIG, DEFAULT_VILLAGE_ID, RAW_DATA_DIR
from src.features import FEATURE_COLUMNS, compute_heat_index, SEASON_MAPPING
from src.models import load_model_and_artifacts
from src.ingestion import fetch_live_weather
from src.shortage import assess_water_shortage

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def predict_from_features(features_dict: Dict[str, Any]) -> float:
    """
    Direct model inference on a raw dictionary of feature values using the champion model adapter.
    """
    adapter, _, _ = load_model_and_artifacts()
    
    # Ensure all required features are present
    row = {col: [features_dict.get(col, 0.0)] for col in FEATURE_COLUMNS}
    df_feat = pd.DataFrame(row)
    
    pred = float(adapter.predict(df_feat)[0])
    return max(100.0, round(pred, 1))



def predict_next_day_demand(
    village_id: str = DEFAULT_VILLAGE_ID,
    forecast_date: Optional[str] = None,
    custom_temp: Optional[float] = None,
    custom_rainfall: Optional[float] = None,
    custom_humidity: Optional[float] = None,
    custom_population: Optional[int] = None,
    custom_supply: Optional[float] = None,
    use_live_weather: bool = True
) -> Dict[str, Any]:
    """
    End-to-end next-day demand prediction and shortage assessment for a village.
    
    1. Looks up village metadata (lat, lon, population, supply baseline).
    2. Fetches live Open-Meteo weather for tomorrow or applies user overrides.
    3. Retrieves recent consumption history from stored data to compute lags & rolling statistics.
    4. Runs ML model to predict next-day water demand in litres.
    5. Evaluates shortage risk, deficit, and emergency management actions.
    """
    village_id = village_id.upper()
    if village_id not in VILLAGES_CONFIG:
        raise ValueError(f"Unknown village ID '{village_id}'. Configured IDs: {list(VILLAGES_CONFIG.keys())}")
    
    vmeta = VILLAGES_CONFIG[village_id]
    population = int(custom_population if custom_population is not None else vmeta["base_population"])
    supply = float(custom_supply if custom_supply is not None else vmeta["avg_daily_supply_litres"])
    storage_capacity = vmeta["storage_capacity_litres"]

    # Target forecast date: tomorrow by default
    tomorrow = datetime.now() + timedelta(days=1)
    target_dt_str = forecast_date if forecast_date else tomorrow.strftime("%Y-%m-%d")
    target_dt = pd.to_datetime(target_dt_str)

    # 1. Weather gathering
    weather_source = "User Override"
    temp_mean = custom_temp
    rainfall_mm = custom_rainfall
    humidity_pct = custom_humidity

    if (temp_mean is None or rainfall_mm is None or humidity_pct is None) and use_live_weather:
        live_weather = fetch_live_weather(vmeta["latitude"], vmeta["longitude"], days=2)
        weather_source = live_weather.get("source", "Open-Meteo API")
        forecasts = live_weather.get("forecast", [])
        if len(forecasts) > 1:
            day_forecast = forecasts[1]  # Tomorrow's forecast
        elif len(forecasts) > 0:
            day_forecast = forecasts[0]
        else:
            day_forecast = {"temp_mean": 28.0, "rainfall_mm": 0.0, "humidity_pct": 55.0}

        if temp_mean is None:
            temp_mean = float(day_forecast["temp_mean"])
        if rainfall_mm is None:
            rainfall_mm = float(day_forecast["rainfall_mm"])
        if humidity_pct is None:
            humidity_pct = float(day_forecast["humidity_pct"])
    else:
        temp_mean = float(temp_mean) if temp_mean is not None else 28.5
        rainfall_mm = float(rainfall_mm) if rainfall_mm is not None else 0.0
        humidity_pct = float(humidity_pct) if humidity_pct is not None else 50.0

    # 2. Historical Lag & Rolling Stats from latest available data
    raw_path = RAW_DATA_DIR / "village_water_demand_raw.csv"
    lag_1 = population * 55.0
    lag_2 = population * 55.0
    lag_7 = population * 55.0
    rolling_mean_7d = population * 55.0
    rolling_std_7d = 2000.0
    rolling_max_7d = population * 60.0

    if raw_path.exists():
        try:
            df_hist = pd.read_csv(raw_path)
            v_hist = df_hist[df_hist["village_id"] == village_id].sort_values("date")
            if len(v_hist) >= 7:
                last_demands = v_hist["water_demand_litres"].values
                lag_1 = float(last_demands[-1])
                lag_2 = float(last_demands[-2])
                lag_7 = float(last_demands[-7])
                rolling_mean_7d = float(np.mean(last_demands[-7:]))
                rolling_std_7d = float(np.std(last_demands[-7:]))
                rolling_max_7d = float(np.max(last_demands[-7:]))
        except Exception as e:
            logger.warning(f"Could not read historical data for lags: {e}")

    # 3. Calendar & Season features
    day_of_week = target_dt.dayofweek
    is_weekend = 1 if day_of_week in [5, 6] else 0
    month = target_dt.month

    if month in [4, 5, 6]:
        season = "Summer"
    elif month in [7, 8, 9]:
        season = "Monsoon"
    elif month in [10, 11]:
        season = "Post-Monsoon"
    else:
        season = "Winter"

    season_encoded = SEASON_MAPPING.get(season, 0)
    heat_index = compute_heat_index(temp_mean, humidity_pct)

    features_dict = {
        "population": population,
        "temp_mean": temp_mean,
        "rainfall_mm": rainfall_mm,
        "humidity_pct": humidity_pct,
        "heat_index": heat_index,
        "day_of_week": day_of_week,
        "is_weekend": is_weekend,
        "month": month,
        "season_encoded": season_encoded,
        "demand_lag_1": lag_1,
        "demand_lag_2": lag_2,
        "demand_lag_7": lag_7,
        "rolling_mean_7d": rolling_mean_7d,
        "rolling_std_7d": rolling_std_7d,
        "rolling_max_7d": rolling_max_7d
    }

    # 4. Predict next-day demand
    predicted_demand = predict_from_features(features_dict)

    # 5. Assess Shortage
    shortage_eval = assess_water_shortage(
        predicted_demand_litres=predicted_demand,
        estimated_supply_litres=supply,
        population=population,
        storage_capacity_litres=storage_capacity
    )

    result = {
        "village_id": village_id,
        "village_name": vmeta["name"],
        "state": vmeta["state"],
        "forecast_date": target_dt_str,
        "weather": {
            "source": weather_source,
            "temp_mean_celsius": temp_mean,
            "rainfall_mm": rainfall_mm,
            "humidity_pct": humidity_pct,
            "heat_index_celsius": heat_index,
            "season": season
        },
        "demographics": {
            "population": population,
            "day_of_week": target_dt.strftime("%A"),
            "is_weekend": bool(is_weekend)
        },
        "water_balance": shortage_eval,
        "features_used": features_dict
    }

    return result


def predict_7_day_forecast(village_id: str = DEFAULT_VILLAGE_ID) -> Dict[str, Any]:
    """
    Generates a 7-day forward-looking autoregressive water demand and shortage forecast.
    Integrates 7-day meteorological forecast from Open-Meteo with dynamic lag propagation.
    """
    vid = village_id.upper()
    if vid not in VILLAGES_CONFIG:
        raise ValueError(f"Unknown village ID '{village_id}'")
    
    vmeta = VILLAGES_CONFIG[vid]
    population = vmeta["base_population"]
    supply = float(vmeta["avg_daily_supply_litres"])
    storage_cap = float(vmeta["storage_capacity_litres"])

    # 1. Fetch 7-day live weather
    weather_res = fetch_live_weather(vmeta["latitude"], vmeta["longitude"], days=7)
    forecast_days = weather_res.get("forecast", [])

    # 2. Seed historical demand sequence
    raw_path = RAW_DATA_DIR / "village_water_demand_raw.csv"
    history_demands = []
    if raw_path.exists():
        try:
            df_hist = pd.read_csv(raw_path)
            v_hist = df_hist[df_hist["village_id"] == vid].sort_values("date")
            history_demands = list(v_hist["water_demand_litres"].values[-14:])
        except Exception:
            pass
    
    if len(history_demands) < 7:
        history_demands = [population * 55.0] * 14

    daily_forecasts = []

    for i, w in enumerate(forecast_days):
        dt = pd.to_datetime(w["date"])
        t_mean = float(w["temp_mean"])
        precip = float(w["rainfall_mm"])
        humid = float(w["humidity_pct"])
        hi = compute_heat_index(t_mean, humid)

        month = dt.month
        if month in [4, 5, 6]:
            season = "Summer"
        elif month in [7, 8, 9]:
            season = "Monsoon"
        elif month in [10, 11]:
            season = "Post-Monsoon"
        else:
            season = "Winter"
        
        season_encoded = SEASON_MAPPING.get(season, 0)
        day_of_week = dt.dayofweek
        is_weekend = 1 if day_of_week in [5, 6] else 0

        # Autoregressive lags from dynamic sequence
        lag_1 = float(history_demands[-1])
        lag_2 = float(history_demands[-2])
        lag_7 = float(history_demands[-7])
        rolling_7 = history_demands[-7:]
        roll_mean = float(np.mean(rolling_7))
        roll_std = float(np.std(rolling_7))
        roll_max = float(np.max(rolling_7))

        feat_row = {
            "population": population,
            "temp_mean": t_mean,
            "rainfall_mm": precip,
            "humidity_pct": humid,
            "heat_index": hi,
            "day_of_week": day_of_week,
            "is_weekend": is_weekend,
            "month": month,
            "season_encoded": season_encoded,
            "demand_lag_1": lag_1,
            "demand_lag_2": lag_2,
            "demand_lag_7": lag_7,
            "rolling_mean_7d": roll_mean,
            "rolling_std_7d": roll_std,
            "rolling_max_7d": roll_max
        }

        day_pred_demand = predict_from_features(feat_row)
        history_demands.append(day_pred_demand)

        shortage_res = assess_water_shortage(
            predicted_demand_litres=day_pred_demand,
            estimated_supply_litres=supply,
            population=population,
            storage_capacity_litres=storage_cap
        )

        daily_forecasts.append({
            "day_offset": i + 1,
            "date": w["date"],
            "day_name": dt.strftime("%A"),
            "temp_mean": t_mean,
            "rainfall_mm": precip,
            "humidity_pct": humid,
            "predicted_demand_litres": day_pred_demand,
            "estimated_supply_litres": supply,
            "deficit_litres": shortage_res["deficit_litres"],
            "surplus_litres": shortage_res["surplus_litres"],
            "shortage_probability_pct": shortage_res["shortage_probability_pct"],
            "risk_category": shortage_res["risk_category"],
            "risk_color": shortage_res["risk_color"],
            "tankers_needed": shortage_res["tankers_needed"]
        })

    return {
        "village_id": vid,
        "village_name": vmeta["name"],
        "state": vmeta["state"],
        "weather_source": weather_res.get("source", "Open-Meteo Live API"),
        "forecast_days_count": len(daily_forecasts),
        "forecasts": daily_forecasts
    }

