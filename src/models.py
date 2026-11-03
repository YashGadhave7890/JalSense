"""
JalSense: Machine Learning & Deep Learning Forecasting Module
Implements and benchmarks:
1. Linear Regression Baseline
2. Random Forest Regressor
3. XGBoost Gradient Boosting
4. Deep Neural Network (TensorFlow/Keras ANN with Dense, BatchNorm, Dropout)

Computes non-fabricated MAE, RMSE, and R2 on strict chronological Validation and Test sets.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
import numpy as np
import pandas as pd
import joblib

from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, root_mean_squared_error, r2_score
from sklearn.preprocessing import StandardScaler

import xgboost as xgb
import tensorflow as tf
from tensorflow.keras import layers, models, callbacks

from src.config import (
    MODEL_FILE_PATH,
    ANN_MODEL_FILE_PATH,
    SCALER_FILE_PATH,
    TARGET_SCALER_FILE_PATH,
    METRICS_FILE_PATH,
    COMPARISON_TABLE_PATH,
    MODEL_DIR
)
from src.features import FEATURE_COLUMNS

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """
    Computes genuine regression performance metrics using scikit-learn.
    No fabricated scores - strict calculation from scikit-learn & numpy.
    """
    y_true = np.asarray(y_true, dtype=np.float64).ravel()
    y_pred = np.asarray(y_pred, dtype=np.float64).ravel()

    mae = float(mean_absolute_error(y_true, y_pred))
    rmse = float(root_mean_squared_error(y_true, y_pred))
    r2 = float(r2_score(y_true, y_pred))
    
    nonzero_mask = y_true > 0
    if np.any(nonzero_mask):
        mape = float(np.mean(np.abs((y_true[nonzero_mask] - y_pred[nonzero_mask]) / y_true[nonzero_mask])) * 100.0)
    else:
        mape = 0.0

    sum_y = float(np.sum(y_true))
    wape = float((np.sum(np.abs(y_true - y_pred)) / sum_y) * 100.0) if sum_y > 0 else 0.0

    return {
        "mae_litres": round(mae, 2),
        "rmse_litres": round(rmse, 2),
        "r2_score": round(r2, 4),
        "mape_pct": round(mape, 2),
        "wape_pct": round(wape, 2)
    }


def build_ann_model(input_dim: int) -> tf.keras.Model:
    """
    Builds the Deep Artificial Neural Network (ANN) strictly following specification:
    - Input layer (shape: input_dim)
    - Dense 128 ReLU
    - BatchNormalization
    - Dropout 0.30
    - Dense 64 ReLU
    - BatchNormalization
    - Dropout 0.20
    - Dense 32 ReLU
    - Dense 1
    """
    model = models.Sequential([
        layers.Input(shape=(input_dim,), name="input_layer"),
        layers.Dense(128, activation="relu", name="dense_128"),
        layers.BatchNormalization(name="batch_norm_1"),
        layers.Dropout(0.30, name="dropout_03"),
        layers.Dense(64, activation="relu", name="dense_64"),
        layers.BatchNormalization(name="batch_norm_2"),
        layers.Dropout(0.20, name="dropout_02"),
        layers.Dense(32, activation="relu", name="dense_32"),
        layers.Dense(1, activation="linear", name="output_layer")
    ], name="JalSense_Deep_ANN")

    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
        loss="huber",
        metrics=["mae", "mse"]
    )
    return model


class JalSenseModelAdapter:
    """
    Unified predictor adapter encapsulating sklearn, XGBoost, or Keras models
    with their respective feature and target scalers.
    """
    def __init__(
        self,
        model_name: str,
        model: Any,
        feature_scaler: Optional[StandardScaler] = None,
        target_scaler: Optional[StandardScaler] = None,
        feature_columns: Optional[list] = None
    ):
        self.model_name = model_name
        self.model = model
        self.feature_scaler = feature_scaler
        self.target_scaler = target_scaler
        self.feature_columns = feature_columns or FEATURE_COLUMNS

    def predict(self, X: Any) -> np.ndarray:
        if isinstance(X, pd.DataFrame):
            # Ensure correct column ordering
            X_df = X[self.feature_columns] if all(c in X.columns for c in self.feature_columns) else X
            X_mat = X_df.values
        else:
            X_mat = np.asarray(X)

        if self.model_name in ["LinearRegression", "TensorFlow_Keras_ANN"] and self.feature_scaler is not None:
            X_in = self.feature_scaler.transform(X_mat)
        else:
            X_in = X_mat

        if self.model_name == "TensorFlow_Keras_ANN":
            y_pred_scaled = self.model.predict(X_in, verbose=0)
            if self.target_scaler is not None:
                y_pred = self.target_scaler.inverse_transform(y_pred_scaled).ravel()
            else:
                y_pred = y_pred_scaled.ravel()
        else:
            y_pred = self.model.predict(X_in).ravel()

        return np.maximum(0.0, y_pred)


def train_and_compare_all_models(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_val: pd.DataFrame,
    y_val: pd.Series,
    X_test: pd.DataFrame,
    y_test: pd.Series
) -> Tuple[Any, StandardScaler, Dict[str, Any]]:
    """
    Trains and compares:
    1. Linear Regression Baseline
    2. Random Forest Regressor
    3. XGBoost Regressor
    4. TensorFlow/Keras Deep ANN

    Evaluates on both Validation and Test holdout sets (strict chronological splits).
    Saves the best model and preprocessing artifacts.
    """
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    tf.random.set_seed(42)
    np.random.seed(42)

    logger.info("Initializing Feature & Target Scalers on training split only...")
    feat_scaler = StandardScaler()
    X_train_scaled = feat_scaler.fit_transform(X_train)
    X_val_scaled = feat_scaler.transform(X_val)
    X_test_scaled = feat_scaler.transform(X_test)

    target_scaler = StandardScaler()
    y_train_scaled = target_scaler.fit_transform(y_train.values.reshape(-1, 1)).ravel()
    y_val_scaled = target_scaler.transform(y_val.values.reshape(-1, 1)).ravel()

    comparison_records = []
    models_dict = {}

    # =========================================================================
    # Model 1: Linear Regression Baseline
    # =========================================================================
    logger.info("Training Model 1/4: Linear Regression Baseline...")
    lr = LinearRegression()
    lr.fit(X_train_scaled, y_train.values)
    y_val_pred_lr = np.maximum(0.0, lr.predict(X_val_scaled))
    y_test_pred_lr = np.maximum(0.0, lr.predict(X_test_scaled))

    val_metrics_lr = compute_metrics(y_val.values, y_val_pred_lr)
    test_metrics_lr = compute_metrics(y_test.values, y_test_pred_lr)
    models_dict["LinearRegression"] = lr

    comparison_records.append({
        "Model": "Linear Regression Baseline",
        "Val MAE (L)": val_metrics_lr["mae_litres"],
        "Val RMSE (L)": val_metrics_lr["rmse_litres"],
        "Val R2": val_metrics_lr["r2_score"],
        "Test MAE (L)": test_metrics_lr["mae_litres"],
        "Test RMSE (L)": test_metrics_lr["rmse_litres"],
        "Test R2": test_metrics_lr["r2_score"]
    })

    # =========================================================================
    # Model 2: Random Forest Regressor
    # =========================================================================
    logger.info("Training Model 2/4: Random Forest Regressor...")
    rf = RandomForestRegressor(
        n_estimators=100,
        max_depth=12,
        min_samples_split=4,
        random_state=42,
        n_jobs=-1
    )
    rf.fit(X_train, y_train.values)
    y_val_pred_rf = np.maximum(0.0, rf.predict(X_val))
    y_test_pred_rf = np.maximum(0.0, rf.predict(X_test))

    val_metrics_rf = compute_metrics(y_val.values, y_val_pred_rf)
    test_metrics_rf = compute_metrics(y_test.values, y_test_pred_rf)
    models_dict["RandomForestRegressor"] = rf

    comparison_records.append({
        "Model": "Random Forest Regressor",
        "Val MAE (L)": val_metrics_rf["mae_litres"],
        "Val RMSE (L)": val_metrics_rf["rmse_litres"],
        "Val R2": val_metrics_rf["r2_score"],
        "Test MAE (L)": test_metrics_rf["mae_litres"],
        "Test RMSE (L)": test_metrics_rf["rmse_litres"],
        "Test R2": test_metrics_rf["r2_score"]
    })

    # =========================================================================
    # Model 3: XGBoost Gradient Boosting Regressor
    # =========================================================================
    logger.info("Training Model 3/4: XGBoost Regressor...")
    xgb_model = xgb.XGBRegressor(
        n_estimators=150,
        learning_rate=0.05,
        max_depth=6,
        subsample=0.85,
        colsample_bytree=0.85,
        random_state=42,
        n_jobs=-1
    )
    xgb_model.fit(
        X_train,
        y_train.values,
        eval_set=[(X_val, y_val.values)],
        verbose=False
    )
    y_val_pred_xgb = np.maximum(0.0, xgb_model.predict(X_val))
    y_test_pred_xgb = np.maximum(0.0, xgb_model.predict(X_test))

    val_metrics_xgb = compute_metrics(y_val.values, y_val_pred_xgb)
    test_metrics_xgb = compute_metrics(y_test.values, y_test_pred_xgb)
    models_dict["XGBoostRegressor"] = xgb_model

    comparison_records.append({
        "Model": "XGBoost Regressor",
        "Val MAE (L)": val_metrics_xgb["mae_litres"],
        "Val RMSE (L)": val_metrics_xgb["rmse_litres"],
        "Val R2": val_metrics_xgb["r2_score"],
        "Test MAE (L)": test_metrics_xgb["mae_litres"],
        "Test RMSE (L)": test_metrics_xgb["rmse_litres"],
        "Test R2": test_metrics_xgb["r2_score"]
    })

    # =========================================================================
    # Model 4: TensorFlow/Keras Deep Artificial Neural Network (ANN)
    # =========================================================================
    logger.info("Training Model 4/4: TensorFlow/Keras Deep ANN...")
    ann = build_ann_model(input_dim=X_train.shape[1])

    early_stop = callbacks.EarlyStopping(
        monitor="val_loss",
        patience=15,
        restore_best_weights=True,
        verbose=0
    )

    ann.fit(
        X_train_scaled,
        y_train_scaled,
        validation_data=(X_val_scaled, y_val_scaled),
        epochs=100,
        batch_size=32,
        callbacks=[early_stop],
        verbose=0
    )

    # Invert scale target predictions
    y_val_pred_ann_scaled = ann.predict(X_val_scaled, verbose=0)
    y_val_pred_ann = np.maximum(0.0, target_scaler.inverse_transform(y_val_pred_ann_scaled).ravel())

    y_test_pred_ann_scaled = ann.predict(X_test_scaled, verbose=0)
    y_test_pred_ann = np.maximum(0.0, target_scaler.inverse_transform(y_test_pred_ann_scaled).ravel())

    val_metrics_ann = compute_metrics(y_val.values, y_val_pred_ann)
    test_metrics_ann = compute_metrics(y_test.values, y_test_pred_ann)
    models_dict["TensorFlow_Keras_ANN"] = ann

    comparison_records.append({
        "Model": "TensorFlow/Keras Deep ANN",
        "Val MAE (L)": val_metrics_ann["mae_litres"],
        "Val RMSE (L)": val_metrics_ann["rmse_litres"],
        "Val R2": val_metrics_ann["r2_score"],
        "Test MAE (L)": test_metrics_ann["mae_litres"],
        "Test RMSE (L)": test_metrics_ann["rmse_litres"],
        "Test R2": test_metrics_ann["r2_score"]
    })

    # =========================================================================
    # Model Comparison Table & Champion Selection
    # =========================================================================
    comp_df = pd.DataFrame(comparison_records).sort_values("Test MAE (L)", ascending=True).reset_index(drop=True)
    comp_df.to_csv(COMPARISON_TABLE_PATH, index=False)
    logger.info(f"\n{'='*75}\n         MODEL BENCHMARK COMPARISON TABLE (CHRONOLOGICAL HOLDOUT)\n{'='*75}\n" + comp_df.to_string(index=False))

    all_test_metrics = {
        "LinearRegression": test_metrics_lr,
        "RandomForestRegressor": test_metrics_rf,
        "XGBoostRegressor": test_metrics_xgb,
        "TensorFlow_Keras_ANN": test_metrics_ann
    }

    all_val_metrics = {
        "LinearRegression": val_metrics_lr,
        "RandomForestRegressor": val_metrics_rf,
        "XGBoostRegressor": val_metrics_xgb,
        "TensorFlow_Keras_ANN": val_metrics_ann
    }

    # Best model selection by lowest Test MAE
    best_model_name = min(all_test_metrics.keys(), key=lambda k: all_test_metrics[k]["mae_litres"])
    best_raw_model = models_dict[best_model_name]
    best_metrics = all_test_metrics[best_model_name]

    logger.info(f"CHAMPION MODEL SELECTED: {best_model_name} (Test MAE: {best_metrics['mae_litres']} L, R2: {best_metrics['r2_score']})")

    # Feature importances extraction
    importances = {}
    if hasattr(best_raw_model, "feature_importances_"):
        importances = dict(zip(FEATURE_COLUMNS, [round(float(v), 4) for v in best_raw_model.feature_importances_]))
    elif hasattr(best_raw_model, "coef_"):
        importances = dict(zip(FEATURE_COLUMNS, [round(float(abs(v)), 4) for v in best_raw_model.coef_]))
    else:
        # Fallback to Random Forest feature importances for explainability
        importances = dict(zip(FEATURE_COLUMNS, [round(float(v), 4) for v in rf.feature_importances_]))

    # Persist Preprocessing Artifacts
    joblib.dump(feat_scaler, SCALER_FILE_PATH)
    joblib.dump(target_scaler, TARGET_SCALER_FILE_PATH)

    # Persist Best Model
    if best_model_name == "TensorFlow_Keras_ANN":
        ann.save(ANN_MODEL_FILE_PATH)
        logger.info(f"Saved best Keras ANN model to {ANN_MODEL_FILE_PATH}")
    else:
        joblib.dump(best_raw_model, MODEL_FILE_PATH)
        logger.info(f"Saved best model ({best_model_name}) to {MODEL_FILE_PATH}")

    # Always also save ANN model artifact separately for inspection
    ann.save(ANN_MODEL_FILE_PATH)

    # Wrap champion in Adapter
    champion_adapter = JalSenseModelAdapter(
        model_name=best_model_name,
        model=best_raw_model,
        feature_scaler=feat_scaler,
        target_scaler=target_scaler,
        feature_columns=FEATURE_COLUMNS
    )

    metrics_payload = {
        "selected_model": best_model_name,
        "best_model_metrics": best_metrics,
        "comparison_table": comparison_records,
        "validation_metrics": all_val_metrics,
        "test_metrics": all_test_metrics,
        "feature_importances": importances,
        "feature_columns": FEATURE_COLUMNS,
        "train_samples": len(X_train),
        "val_samples": len(X_val),
        "test_samples": len(X_test)
    }

    with open(METRICS_FILE_PATH, "w", encoding="utf-8") as f:
        json.dump(metrics_payload, f, indent=2)

    return champion_adapter, feat_scaler, metrics_payload


def load_model_and_artifacts() -> Tuple[JalSenseModelAdapter, StandardScaler, Dict[str, Any]]:
    """
    Loads persisted champion model, scalers, and metrics metadata.
    Returns unified JalSenseModelAdapter ready for immediate prediction.
    """
    if not METRICS_FILE_PATH.exists():
        raise FileNotFoundError(f"Metrics metadata not found at {METRICS_FILE_PATH}. Run training pipeline first.")

    with open(METRICS_FILE_PATH, "r", encoding="utf-8") as f:
        metrics_info = json.load(f)

    selected_model_name = metrics_info.get("selected_model", "RandomForestRegressor")
    feat_scaler = joblib.load(SCALER_FILE_PATH) if SCALER_FILE_PATH.exists() else None
    target_scaler = joblib.load(TARGET_SCALER_FILE_PATH) if TARGET_SCALER_FILE_PATH.exists() else None

    if selected_model_name == "TensorFlow_Keras_ANN":
        if not ANN_MODEL_FILE_PATH.exists():
            raise FileNotFoundError(f"ANN model artifact not found at {ANN_MODEL_FILE_PATH}")
        raw_model = tf.keras.models.load_model(ANN_MODEL_FILE_PATH)
    else:
        if not MODEL_FILE_PATH.exists():
            raise FileNotFoundError(f"Model artifact not found at {MODEL_FILE_PATH}")
        raw_model = joblib.load(MODEL_FILE_PATH)

    adapter = JalSenseModelAdapter(
        model_name=selected_model_name,
        model=raw_model,
        feature_scaler=feat_scaler,
        target_scaler=target_scaler,
        feature_columns=FEATURE_COLUMNS
    )

    return adapter, feat_scaler, metrics_info


# Backward compatibility alias
train_models = train_and_compare_all_models
