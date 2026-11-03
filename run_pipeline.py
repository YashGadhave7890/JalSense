"""
JalSense: End-to-End Pipeline Runner
Executes data ingestion, preprocessing, feature extraction, model training,
and artifact persistence in one streamlined execution.
"""

import sys
import logging
import json
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.ingestion import ingest_data
from src.preprocessing import clean_raw_data, chronological_train_val_test_split, save_processed_data
from src.features import prepare_train_val_test_matrices
from src.models import train_and_compare_all_models
from src.prediction import predict_next_day_demand


logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("JalSensePipeline")


from src.data_pipeline import execute_data_layer_pipeline


def run_full_pipeline():
    logger.info("==================================================")
    logger.info("         JalSense Data Science Pipeline           ")
    logger.info("==================================================")

    # Step 0: Public Water Data Layer & Open-Meteo Weather Caching
    logger.info("Step 0/6: Executing Public Water Data Layer Pipeline...")
    data_layer_res = execute_data_layer_pipeline(force_download=False)
    logger.info(
        f"Public Dataset Processed: {data_layer_res['records_count']} days, "
        f"Unified Features saved to {data_layer_res['unified_features_file']}"
    )

    # Step 1: Village Ingestion
    logger.info("Step 1/6: Ingesting Village Baseline...")
    raw_df = ingest_data(force_generate=False)
    logger.info(f"Loaded raw records: {len(raw_df)} rows")


    # Step 2: Preprocessing
    logger.info("Step 2/6: Preprocessing and cleaning...")
    clean_df = clean_raw_data(raw_df)
    save_processed_data(clean_df)

    # Step 3: Chronological 3-Way Splitting (Train / Val / Test)
    logger.info("Step 3/6: Chronological 3-way Split (Train / Val / Test - No Shuffling)...")
    train_df, val_df, test_df = chronological_train_val_test_split(clean_df, val_ratio=0.15, test_ratio=0.15)

    # Step 4: Feature Engineering
    logger.info("Step 4/6: Feature extraction & matrix construction...")
    X_train, y_train, X_val, y_val, X_test, y_test = prepare_train_val_test_matrices(train_df, val_df, test_df)
    logger.info(f"Features: {list(X_train.columns)}")
    logger.info(f"Train Shape: {X_train.shape}, Val Shape: {X_val.shape}, Test Shape: {X_test.shape}")

    # Step 5: Model Training, Benchmarking & Comparison
    logger.info("Step 5/6: Training & Benchmarking 4 Models (Linear Regression, Random Forest, XGBoost, Keras Deep ANN)...")
    champion_adapter, scaler, metrics = train_and_compare_all_models(X_train, y_train, X_val, y_val, X_test, y_test)


    logger.info("==================================================")
    logger.info("             Pipeline Execution Summary           ")
    logger.info("==================================================")
    logger.info(f"Best Model Selected : {metrics['selected_model']}")
    logger.info(f"Mean Absolute Error : {metrics['best_model_metrics']['mae_litres']} Litres")
    logger.info(f"RMSE                : {metrics['best_model_metrics']['rmse_litres']} Litres")
    logger.info(f"R² Score            : {metrics['best_model_metrics']['r2_score']}")
    logger.info(f"WAPE (%)            : {metrics['best_model_metrics']['wape_pct']}%")
    logger.info("Top Feature Importances:")
    sorted_feats = sorted(metrics["feature_importances"].items(), key=lambda x: x[1], reverse=True)[:5]
    for feat, imp in sorted_feats:
        logger.info(f"  - {feat:20s}: {imp:.4f}")

    # Sanity inference test
    logger.info("\n--- Running Sanity Inference for Default Village (Ralegan Siddhi) ---")
    test_result = predict_next_day_demand("VILL001")
    wb = test_result["water_balance"]
    logger.info(f"Village          : {test_result['village_name']}")
    logger.info(f"Forecast Date    : {test_result['forecast_date']}")
    logger.info(f"Weather Temp/Rain: {test_result['weather']['temp_mean_celsius']}°C, {test_result['weather']['rainfall_mm']}mm")
    logger.info(f"Predicted Demand : {wb['predicted_demand_litres']:,} Litres ({wb['predicted_lpcd']} LPCD)")
    logger.info(f"Estimated Supply : {wb['estimated_supply_litres']:,} Litres")
    logger.info(f"Deficit          : {wb['deficit_litres']:,} Litres")
    logger.info(f"Shortage Risk    : {wb['shortage_risk']} ({wb['coverage_percentage']}%)")
    logger.info(f"Tankers Needed   : {wb['tankers_needed']}")
    logger.info("Pipeline executed successfully!")


if __name__ == "__main__":
    run_full_pipeline()
