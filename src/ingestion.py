"""
JalSense: Data Ingestion Module
Handles Open-Meteo live weather retrieval, external dataset downloads,
and generates clearly labelled realistic baseline benchmark datasets.
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import requests
import numpy as np
import pandas as pd

from src.config import (
    RAW_DATA_DIR,
    SAMPLE_DATA_DIR,
    PROCESSED_DATA_DIR,
    VILLAGES_CONFIG,
    OPEN_METEO_BASE_URL,
    OPEN_METEO_ARCHIVE_URL,
    JJM_BENCHMARK_LPCD
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


from src.weather_client import weather_client


def fetch_live_weather(latitude: float, longitude: float, days: int = 7) -> Dict[str, Any]:
    """
    Fetch live real-time weather forecast from Open-Meteo API using WeatherClient with disk caching.
    Prevents duplicate calls and rate-limiting.
    """
    return weather_client.fetch_current_and_forecast(latitude=latitude, longitude=longitude, days=days)


def generate_benchmark_dataset(
    start_date: str = "2023-01-01",
    end_date: str = "2024-12-31",
    seed: int = 42
) -> pd.DataFrame:
    """
    Generates a realistic, hydrology-grounded village-level time-series benchmark dataset.
    
    IMPORTANT NOTE:
    This dataset is explicitly designated as a DEMO / BENCHMARK SYNTHETIC DATASET.
    It models real rural consumption patterns compliant with India's Jal Jeevan Mission
    guidelines (55 LPCD baseline) and regional climatic elasticity, allowing full
    reproducibility and testing until local field SCADA meter data is plugged in.
    """
    np.random.seed(seed)
    date_range = pd.date_range(start=start_date, end=end_date, freq="D")
    all_rows = []

    for village_id, vmeta in VILLAGES_CONFIG.items():
        base_pop = vmeta["base_population"]
        base_supply = vmeta["avg_daily_supply_litres"]
        storage_cap = vmeta["storage_capacity_litres"]

        for dt in date_range:
            day_of_year = dt.dayofyear
            month = dt.month
            day_of_week = dt.dayofweek  # 0=Monday, 6=Sunday

            # Seasonal weather simulation for Indian agro-climatic zones
            # Hot summer (April-June), Monsoon (July-Sept), Post-monsoon/Winter (Oct-March)
            if month in [4, 5, 6]:
                # Summer
                temp_max = np.random.normal(38.0, 2.5)
                temp_min = np.random.normal(25.0, 2.0)
                rainfall = np.random.choice([0.0, 5.0, 12.0], p=[0.90, 0.08, 0.02])
                humidity = np.random.normal(40.0, 8.0)
                season = "Summer"
            elif month in [7, 8, 9]:
                # Monsoon
                temp_max = np.random.normal(30.0, 2.0)
                temp_min = np.random.normal(22.0, 1.5)
                rainfall = np.random.exponential(14.0) if np.random.rand() < 0.65 else 0.0
                humidity = np.random.normal(82.0, 7.0)
                season = "Monsoon"
            elif month in [10, 11]:
                # Post-Monsoon
                temp_max = np.random.normal(31.0, 2.0)
                temp_min = np.random.normal(18.0, 2.0)
                rainfall = np.random.choice([0.0, 4.0], p=[0.92, 0.08])
                humidity = np.random.normal(55.0, 6.0)
                season = "Post-Monsoon"
            else:
                # Winter (Dec-March)
                temp_max = np.random.normal(27.0, 2.5)
                temp_min = np.random.normal(12.0, 2.0)
                rainfall = np.random.choice([0.0, 2.0], p=[0.95, 0.05])
                humidity = np.random.normal(45.0, 6.0)
                season = "Winter"

            temp_mean = (temp_max + temp_min) / 2.0
            humidity = float(np.clip(humidity, 15.0, 98.0))
            rainfall = float(np.clip(rainfall, 0.0, 150.0))

            # Demographic dynamic (gradual annual population growth + festival/harvest spikes)
            pop_growth = 1.0 + (dt.year - 2023) * 0.012
            # Major festival seasons (Diwali around Oct/Nov, Holi in March)
            festival_factor = 1.0
            if (month == 11 and dt.day in [10, 11, 12, 13, 14]) or (month == 3 and dt.day in [24, 25]):
                festival_factor = 1.18  # Relatives visit village
            
            current_pop = int(base_pop * pop_growth * festival_factor)

            # Hydrological demand formula (litres per capita per day)
            # Base JJM norm = 55 LPCD
            # Temp elasticity: +1.6% demand per degree above 25°C
            temp_effect = max(0.0, (temp_mean - 25.0)) * 0.016
            
            # Rainfall effect: on rain days, rainwater harvesting & lower cattle wash/dust suppression drops demand
            rain_effect = -0.15 if rainfall > 5.0 else (-0.05 if rainfall > 0.0 else 0.0)

            # Weekend effect: laundry and livestock cleaning higher on Sunday
            weekend_effect = 0.08 if day_of_week == 6 else (0.04 if day_of_week == 5 else 0.0)

            # Random lifestyle variance (Gaussian noise ~ 4%)
            noise = np.random.normal(0.0, 0.04)

            lpcd = JJM_BENCHMARK_LPCD * (1.0 + temp_effect + rain_effect + weekend_effect + noise)
            lpcd = float(np.clip(lpcd, 38.0, 85.0))

            water_demand_litres = round(current_pop * lpcd, 1)

            # Realistic daily water supply generation
            # In monsoon/post-monsoon, borewell replenishment yields higher supply
            # In peak summer (May/June), groundwater levels drop, reducing borehole yield
            supply_seasonal_mult = 1.0
            if season == "Summer":
                supply_seasonal_mult = 0.82  # Depleted groundwater table
            elif season == "Monsoon":
                supply_seasonal_mult = 1.15  # Recharged reservoirs & wells
            elif season == "Post-Monsoon":
                supply_seasonal_mult = 1.05

            # Pumping outage/maintenance risk (3% probability of pump breakdown)
            pump_failure = 0.5 if np.random.rand() < 0.03 else 1.0

            daily_supply_litres = round(base_supply * supply_seasonal_mult * pump_failure * np.random.uniform(0.95, 1.05), 1)

            all_rows.append({
                "date": dt.strftime("%Y-%m-%d"),
                "village_id": village_id,
                "village_name": vmeta["name"],
                "state": vmeta["state"],
                "latitude": vmeta["latitude"],
                "longitude": vmeta["longitude"],
                "population": current_pop,
                "temp_max": round(temp_max, 1),
                "temp_min": round(temp_min, 1),
                "temp_mean": round(temp_mean, 1),
                "rainfall_mm": round(rainfall, 1),
                "humidity_pct": round(humidity, 1),
                "season": season,
                "storage_capacity_litres": storage_cap,
                "daily_supply_litres": daily_supply_litres,
                "water_demand_litres": water_demand_litres,
                "lpcd_actual": round(lpcd, 2),
                "is_synthetic_benchmark": True
            })

    df = pd.DataFrame(all_rows)
    return df


def ingest_data(force_generate: bool = False) -> pd.DataFrame:
    """
    Top-level data ingestion routine.
    Loads raw CSV if present, otherwise generates benchmark dataset,
    saving to both data/sample/ and data/raw/.
    """
    raw_path = RAW_DATA_DIR / "village_water_demand_raw.csv"
    sample_path = SAMPLE_DATA_DIR / "village_water_demand_benchmark.csv"

    if raw_path.exists() and not force_generate:
        logger.info(f"Loading existing raw dataset from {raw_path}")
        df = pd.read_csv(raw_path)
    else:
        logger.info("Generating hydrology-grounded village water benchmark dataset...")
        df = generate_benchmark_dataset()

        # Save to sample and raw
        df.to_csv(sample_path, index=False)
        df.to_csv(raw_path, index=False)

        # Write sample metadata note
        metadata_path = SAMPLE_DATA_DIR / "README.md"
        with open(metadata_path, "w", encoding="utf-8") as f:
            f.write(
                "# JalSense Sample Benchmark Dataset\n\n"
                "**Dataset Type:** Grounded Synthetic Benchmark (`is_synthetic_benchmark = True`)\n\n"
                "**Compliance:** Jal Jeevan Mission (JJM) rural standard of 55 LPCD baseline.\n\n"
                "**Purpose:** Provides a consistent, reproducible baseline for time-series feature engineering, "
                "machine learning model training, and shortage evaluation in village water management.\n\n"
                "**Replacing with Real Data:**\n"
                "Place your real meter/SCADA logs CSV into `data/raw/village_water_demand_raw.csv` with the columns:\n"
                "`[date, village_id, population, temp_mean, rainfall_mm, humidity_pct, daily_supply_litres, water_demand_litres]`.\n"
            )
        logger.info(f"Saved benchmark dataset to {sample_path} and {raw_path} ({len(df)} rows).")

    return df
