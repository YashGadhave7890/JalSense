"""
JalSense: Configuration & Constants
Central repository settings, directory paths, and default village parameters.
"""

from pathlib import Path
import os

# Project root directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Data directories
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
SAMPLE_DATA_DIR = DATA_DIR / "sample"

# Model artifacts directory
MODEL_DIR = BASE_DIR / "artifacts" / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
SAMPLE_DATA_DIR.mkdir(parents=True, exist_ok=True)

# Model Artifact Filenames
MODEL_FILE_PATH = MODEL_DIR / "water_demand_model.joblib"
ANN_MODEL_FILE_PATH = MODEL_DIR / "water_demand_ann.keras"
SCALER_FILE_PATH = MODEL_DIR / "feature_scaler.joblib"
TARGET_SCALER_FILE_PATH = MODEL_DIR / "target_scaler.joblib"
METRICS_FILE_PATH = MODEL_DIR / "model_metrics.json"
COMPARISON_TABLE_PATH = MODEL_DIR / "model_comparison_table.csv"


# Public Real Water Dataset Configuration
PUBLIC_WATER_DATA_URL = "https://raw.githubusercontent.com/LukaLike/water-consumption-data/main/minutely-water-consumption-data.csv"
PUBLIC_RAW_DATA_PATH = RAW_DATA_DIR / "public_water_consumption_raw.csv"
PUBLIC_PROCESSED_DATA_PATH = PROCESSED_DATA_DIR / "public_water_consumption_daily_clean.csv"
UNIFIED_FEATURES_PATH = PROCESSED_DATA_DIR / "unified_features.csv"

# Study Area Coordinates for Weather Matching (Zagreb / Central European reference for LukaLike dataset)
STUDY_AREA_LATITUDE = 45.8150
STUDY_AREA_LONGITUDE = 15.9819
STUDY_AREA_ID = "STUDY_RES_01"

# Jal Jeevan Mission (JJM) Rural Benchmark: 55 Litres Per Capita per Day (LPCD)
JJM_BENCHMARK_LPCD = 55.0

# Open-Meteo API config
OPEN_METEO_BASE_URL = os.getenv("OPEN_METEO_BASE_URL", "https://api.open-meteo.com/v1/forecast")
OPEN_METEO_ARCHIVE_URL = os.getenv("OPEN_METEO_ARCHIVE_URL", "https://archive-api.open-meteo.com/v1/archive")

# Predefined representative Indian rural villages (diverse geography, climate & ground water profiles)
VILLAGES_CONFIG = {
    "VILL001": {
        "id": "VILL001",
        "name": "Ralegan Siddhi (Ahmednagar, MH)",
        "state": "Maharashtra",
        "latitude": 18.91,
        "longitude": 74.40,
        "base_population": 2450,
        "storage_capacity_litres": 170000,   # Overhead tank + check dam yield
        "avg_daily_supply_litres": 150000,
        "water_source": "Borewell & Watershed Storage"
    },
    "VILL002": {
        "id": "VILL002",
        "name": "Hiware Bazar (Ahmednagar, MH)",
        "state": "Maharashtra",
        "latitude": 19.04,
        "longitude": 74.52,
        "base_population": 1350,
        "storage_capacity_litres": 110000,
        "avg_daily_supply_litres": 95000,
        "water_source": "Watershed Recharged Wells"
    },
    "VILL003": {
        "id": "VILL003",
        "name": "Punsari (Sabarkantha, GJ)",
        "state": "Gujarat",
        "latitude": 23.48,
        "longitude": 73.07,
        "base_population": 5800,
        "storage_capacity_litres": 380000,
        "avg_daily_supply_litres": 330000,
        "water_source": "Piped RO Water Scheme + Wells"
    },
    "VILL004": {
        "id": "VILL004",
        "name": "Kothapally (Ranga Reddy, TS)",
        "state": "Telangana",
        "latitude": 17.37,
        "longitude": 78.12,
        "base_population": 3100,
        "storage_capacity_litres": 210000,
        "avg_daily_supply_litres": 180000,
        "water_source": "Community Borewells & Tanks"
    },
    "VILL005": {
        "id": "VILL005",
        "name": "Piplantri (Rajsamand, RJ)",
        "state": "Rajasthan",
        "latitude": 25.08,
        "longitude": 73.88,
        "base_population": 4200,
        "storage_capacity_litres": 250000,
        "avg_daily_supply_litres": 215000,
        "water_source": "Deep Aquifer Tubewells"
    }
}

DEFAULT_VILLAGE_ID = "VILL001"
