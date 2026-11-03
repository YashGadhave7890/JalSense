"""
JalSense: Production FastAPI Backend Service
Exposes REST endpoints for:
- GET  /health          : Service health, model status, and metadata
- GET  /weather         : Live/Forecast Open-Meteo weather with disk caching
- POST /predict-demand  : Next-day water demand prediction
- POST /shortage-risk   : Deficit, shortage probability, and recommendation engine
- POST /simulate        : Scenario simulator recalculating demand & shortage
- GET  /forecast        : 7-day autoregressive demand and weather forecast

Includes comprehensive Pydantic models, detailed OpenAPI docs, and robust error handling.
"""

import os
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional, List, Dict, Any
import pandas as pd
from fastapi import FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.config import (
    VILLAGES_CONFIG,
    MODEL_FILE_PATH,
    DEFAULT_VILLAGE_ID,
    PROCESSED_DATA_DIR,
    RAW_DATA_DIR,
    COMPARISON_TABLE_PATH
)
from src.ingestion import fetch_live_weather
from src.models import load_model_and_artifacts
from src.prediction import predict_next_day_demand, predict_7_day_forecast
from src.shortage import assess_water_shortage, simulate_shortage_scenario
from src.assistant import assistant


# =============================================================================
# In-Memory Model & Artifact Cache (Avoids Disk I/O & Retraining on Every Hit)
# =============================================================================
_CACHED_ADAPTER = None
_CACHED_SCALER = None
_CACHED_METRICS = None


def get_cached_artifacts():
    global _CACHED_ADAPTER, _CACHED_SCALER, _CACHED_METRICS
    if _CACHED_ADAPTER is None:
        try:
            _CACHED_ADAPTER, _CACHED_SCALER, _CACHED_METRICS = load_model_and_artifacts()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Trained model artifacts could not be loaded: {e}. Run 'python run_pipeline.py' first."
            )
    return _CACHED_ADAPTER, _CACHED_SCALER, _CACHED_METRICS


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Pre-load model artifacts into memory on application startup."""
    try:
        get_cached_artifacts()
    except Exception:
        pass
    yield


# =============================================================================
# FastAPI Application & OpenAPI Metadata
# =============================================================================
app = FastAPI(
    title="JalSense API",
    description=(
        "**JalSense — Village Water Intelligence System**\n\n"
        "REST API service powering next-day rural water demand forecasting, "
        "Open-Meteo meteorological synchronization, probabilistic shortage risk "
        "analysis, and scenario stress-testing.\n\n"
        "Aligned with India's **Jal Jeevan Mission (55 LPCD benchmark)**."
    ),
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
    openapi_tags=[
        {"name": "System", "description": "Health check and configuration inspection."},
        {"name": "Weather", "description": "Meteorological data from Open-Meteo with caching."},
        {"name": "Forecasting", "description": "Next-day and 7-day water demand forecasting."},
        {"name": "Shortage Analysis", "description": "Deficit evaluation, shortage probability, and recommendations."},
        {"name": "Simulation", "description": "What-if scenario stress-testing."},
        {"name": "AI Assistant", "description": "Conversational natural-language explanations and decision support."}
    ]
)

# Enable explicit CORS for frontend clients (React Vite on 5173, Streamlit on 8501, local dev)
ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000,http://localhost:8501,http://127.0.0.1:8501"
    ).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# Pydantic Schemas: Request & Response Models
# =============================================================================
class HealthResponse(BaseModel):
    status: str = Field(..., examples=["healthy"])
    model_loaded: bool = Field(..., examples=[True])
    champion_model: Optional[str] = Field(None, examples=["XGBoostRegressor"])
    configured_villages_count: int = Field(..., examples=[5])
    villages: List[str] = Field(..., examples=[["VILL001", "VILL002", "VILL003", "VILL004", "VILL005"]])
    timestamp: str = Field(..., examples=["2026-10-07T21:00:00Z"])


class DailyWeatherRecord(BaseModel):
    date: str = Field(..., examples=["2026-10-08"])
    temp_max: Optional[float] = Field(None, examples=[33.5])
    temp_min: Optional[float] = Field(None, examples=[21.0])
    temp_mean: float = Field(..., examples=[27.25])
    rainfall_mm: float = Field(..., examples=[0.0])
    humidity_pct: float = Field(..., examples=[52.0])


class WeatherForecastResponse(BaseModel):
    village_id: str = Field(..., examples=["VILL001"])
    village_name: str = Field(..., examples=["Ralegan Siddhi (Ahmednagar, MH)"])
    source: str = Field(..., examples=["Open-Meteo Live API"])
    cache_hit: bool = Field(..., examples=[True])
    forecast: List[DailyWeatherRecord]


class PredictDemandRequest(BaseModel):
    village_id: str = Field(default="VILL001", description="Village identifier (VILL001 to VILL005)")
    forecast_date: Optional[str] = Field(default=None, description="Target forecast date (YYYY-MM-DD)")
    custom_temp: Optional[float] = Field(default=None, description="Override mean temperature in Celsius")
    custom_rainfall: Optional[float] = Field(default=None, description="Override rainfall in mm")
    custom_humidity: Optional[float] = Field(default=None, description="Override relative humidity percentage")
    custom_population: Optional[int] = Field(default=None, description="Override village population")
    custom_supply: Optional[float] = Field(default=None, description="Override daily available supply in litres")
    use_live_weather: bool = Field(default=True, description="Fetch real-time weather from Open-Meteo API")


class PredictDemandResponse(BaseModel):
    village_id: str = Field(..., examples=["VILL001"])
    village_name: str = Field(..., examples=["Ralegan Siddhi (Ahmednagar, MH)"])
    state: str = Field(..., examples=["Maharashtra"])
    forecast_date: str = Field(..., examples=["2026-10-08"])
    predicted_demand_litres: float = Field(..., examples=[132550.1])
    predicted_lpcd: float = Field(..., examples=[54.1])
    estimated_supply_litres: float = Field(..., examples=[150000.0])
    deficit_litres: float = Field(..., examples=[0.0])
    surplus_litres: float = Field(..., examples=[17449.9])
    shortage_risk: str = Field(..., examples=["LOW"])
    weather: Dict[str, Any]
    features_used: Dict[str, Any]
    water_balance: Dict[str, Any]


class ShortageRiskRequest(BaseModel):
    predicted_demand_litres: Optional[float] = Field(default=None, gt=0, description="Predicted water demand in litres (if omitted, calculated from village_id)")
    estimated_supply_litres: Optional[float] = Field(default=None, ge=0, description="Available incoming supply in litres (if omitted, loaded from village_id config)")
    village_id: Optional[str] = Field(default=None, description="Village ID (e.g. VILL001) for auto-populating baseline demand and supply")
    population: Optional[int] = Field(default=None, gt=0, description="Village population override")
    storage_capacity_litres: Optional[float] = Field(default=None, gt=0, description="Overhead reservoir capacity in litres")
    current_storage_litres: Optional[float] = Field(default=None, ge=0, description="Current overhead tank level in litres")


class ShortageRiskResponse(BaseModel):
    predicted_demand_litres: float = Field(..., examples=[150000.0])
    estimated_supply_litres: float = Field(..., examples=[120000.0])
    deficit_litres: float = Field(..., examples=[30000.0])
    surplus_litres: float = Field(..., examples=[0.0])
    supply_coverage_ratio: float = Field(..., examples=[0.8])
    coverage_percentage: float = Field(..., examples=[80.0])
    shortage_probability: float = Field(..., examples=[0.842])
    shortage_probability_pct: float = Field(..., examples=[84.2])
    risk_category: str = Field(..., examples=["CRITICAL"])
    risk_color: str = Field(..., examples=["#DC2626"])
    risk_description: str = Field(..., examples=["Critical water deficit exceeding 20% of requirements."])
    tankers_needed: int = Field(..., examples=[3])
    tanker_capacity_litres: float = Field(..., examples=[10000.0])
    primary_recommendation: str
    disclaimer: str
    operational_directives: List[str]
    predicted_lpcd: float = Field(..., examples=[60.0])
    supply_lpcd: float = Field(..., examples=[48.0])
    jjm_benchmark_lpcd: float = Field(..., examples=[55.0])
    shortage_risk: str = Field(..., examples=["CRITICAL"])



class ScenarioSimulationRequest(BaseModel):
    village_id: str = Field(default="VILL001", description="Village identifier")
    population: int = Field(default=2500, gt=0, description="Village population")
    rainfall_mm: float = Field(default=0.0, ge=0, description="Rainfall in mm")
    temp_celsius: float = Field(default=32.0, description="Mean temperature in Celsius")
    water_supply_litres: float = Field(default=150000.0, ge=0, description="Available water supply in litres")
    storage_capacity_litres: float = Field(default=170000.0, gt=0, description="Storage reservoir capacity in litres")
    current_storage_litres: float = Field(default=85000.0, ge=0, description="Current stored water in litres")
    humidity_pct: float = Field(default=50.0, ge=0, le=100, description="Relative humidity percentage")


class ScenarioSimulationResponse(BaseModel):
    scenario_inputs: Dict[str, Any]
    recalculated_demand_litres: float
    shortage_assessment: ShortageRiskResponse


class ForecastDayItem(BaseModel):
    day_offset: int
    date: str
    day_name: str
    temp_mean: float
    rainfall_mm: float
    humidity_pct: float
    predicted_demand_litres: float
    estimated_supply_litres: float
    deficit_litres: float
    surplus_litres: float
    shortage_probability_pct: float
    risk_category: str
    risk_color: str
    tankers_needed: int


class MultiDayForecastResponse(BaseModel):
    village_id: str
    village_name: str
    state: str
    weather_source: str
    forecast_days_count: int
    forecasts: List[ForecastDayItem]


class AssistantQueryRequest(BaseModel):
    question: str = Field(..., examples=["Will there be a shortage tomorrow?"])
    village_id: str = Field(default="VILL001", examples=["VILL001"])
    mode: str = Field(default="auto", examples=["auto"], description="auto, hf, or fallback")


class AssistantQueryResponse(BaseModel):
    question: str
    village_id: str
    answer: str
    source_mode: str
    source_label: str
    is_fallback: bool


# =============================================================================
# API Endpoints
# =============================================================================
@app.get("/", tags=["System"])
def root():
    return {
        "system": "JalSense Intelligent Water Management System",
        "status": "online",
        "documentation": "/docs",
        "version": "2.0.0"
    }


@app.get("/health", response_model=HealthResponse, tags=["System"])
def health_check():
    """
    System Health Probe.
    Returns model loading status, champion architecture, and monitored villages.
    """
    model_ready = MODEL_FILE_PATH.exists()
    champ_name = None
    if model_ready:
        try:
            _, _, metrics = get_cached_artifacts()
            champ_name = metrics.get("selected_model")
        except Exception:
            pass

    return HealthResponse(
        status="healthy",
        model_loaded=model_ready,
        champion_model=champ_name,
        configured_villages_count=len(VILLAGES_CONFIG),
        villages=list(VILLAGES_CONFIG.keys()),
        timestamp=datetime.utcnow().isoformat()
    )


@app.get("/weather", response_model=WeatherForecastResponse, tags=["Weather"])
def get_weather(
    village_id: str = Query(default=DEFAULT_VILLAGE_ID, description="Village ID"),
    days: int = Query(default=7, ge=1, le=14, description="Forecast days")
):
    """
    Fetches real-time and multi-day meteorological forecast from Open-Meteo.
    Utilizes disk caching with 1-hour TTL.
    """
    vid = village_id.upper()
    if vid not in VILLAGES_CONFIG:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Village '{village_id}' not found. Available IDs: {list(VILLAGES_CONFIG.keys())}"
        )
    
    vmeta = VILLAGES_CONFIG[vid]
    weather_data = fetch_live_weather(vmeta["latitude"], vmeta["longitude"], days=days)

    return WeatherForecastResponse(
        village_id=vid,
        village_name=vmeta["name"],
        source=weather_data.get("source", "Open-Meteo Live API"),
        cache_hit=bool(weather_data.get("cache_hit", False)),
        forecast=weather_data.get("forecast", [])
    )


@app.post("/predict-demand", response_model=PredictDemandResponse, tags=["Forecasting"])
def predict_demand_endpoint(req: PredictDemandRequest):
    """
    Predicts next-day village water demand in litres.
    Uses preloaded champion model (XGBoost / Random Forest / ANN) without retraining.
    """
    vid = req.village_id.upper()
    if vid not in VILLAGES_CONFIG:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Village '{req.village_id}' not found. Available IDs: {list(VILLAGES_CONFIG.keys())}"
        )

    # Ensure preloaded artifacts are ready
    get_cached_artifacts()

    try:
        raw_res = predict_next_day_demand(
            village_id=vid,
            forecast_date=req.forecast_date,
            custom_temp=req.custom_temp,
            custom_rainfall=req.custom_rainfall,
            custom_humidity=req.custom_humidity,
            custom_population=req.custom_population,
            custom_supply=req.custom_supply,
            use_live_weather=req.use_live_weather
        )
        wb = raw_res["water_balance"]
        
        return PredictDemandResponse(
            village_id=raw_res["village_id"],
            village_name=raw_res["village_name"],
            state=raw_res["state"],
            forecast_date=raw_res["forecast_date"],
            predicted_demand_litres=wb["predicted_demand_litres"],
            predicted_lpcd=wb["predicted_lpcd"],
            estimated_supply_litres=wb["estimated_supply_litres"],
            deficit_litres=wb["deficit_litres"],
            surplus_litres=wb["surplus_litres"],
            shortage_risk=wb["risk_category"],
            weather=raw_res["weather"],
            features_used=raw_res["features_used"],
            water_balance=wb
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.post("/shortage-risk", response_model=ShortageRiskResponse, tags=["Shortage Analysis"])
def shortage_risk_endpoint(req: ShortageRiskRequest):
    """
    Computes transparent hydrological water balance, shortage probability (Gaussian margin),
    and generates standardized recommendation guidance.
    
    Accepts either direct demand/supply parameters or a village_id for automatic forecasting.
    """
    try:
        if req.predicted_demand_litres is None or req.estimated_supply_litres is None:
            if not req.village_id:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Either provide both 'predicted_demand_litres' and 'estimated_supply_litres', or provide 'village_id'."
                )
            vid = req.village_id.upper()
            if vid not in VILLAGES_CONFIG:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Village '{req.village_id}' not found. Available IDs: {list(VILLAGES_CONFIG.keys())}"
                )
            v_cfg = VILLAGES_CONFIG[vid]
            pred_res = predict_next_day_demand(village_id=vid, custom_population=req.population)
            demand = req.predicted_demand_litres or pred_res["water_balance"]["predicted_demand_litres"]
            supply = req.estimated_supply_litres if req.estimated_supply_litres is not None else float(v_cfg.get("avg_daily_supply_litres", 150000.0))
            pop = req.population or int(v_cfg.get("base_population", 2000))
            cap = req.storage_capacity_litres or float(v_cfg.get("storage_capacity_litres", 150000.0))
            curr_stor = req.current_storage_litres if req.current_storage_litres is not None else (cap * 0.5)
        else:
            demand = req.predicted_demand_litres
            supply = req.estimated_supply_litres
            pop = req.population or 2000
            cap = req.storage_capacity_litres or 150000.0
            curr_stor = req.current_storage_litres if req.current_storage_litres is not None else 75000.0

        assessment = assess_water_shortage(
            predicted_demand_litres=demand,
            estimated_supply_litres=supply,
            population=pop,
            storage_capacity_litres=cap,
            current_storage_litres=curr_stor
        )
        return ShortageRiskResponse(**assessment)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.post("/simulate", response_model=ScenarioSimulationResponse, tags=["Simulation"])
def simulate_endpoint(req: ScenarioSimulationRequest):
    """
    Interactive Scenario Simulator:
    Recalculates next-day water demand and shortage risk under user-defined
    stress-test conditions (population, temperature, rainfall, supply, storage).
    """
    vid = req.village_id.upper()
    if vid not in VILLAGES_CONFIG:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Village '{req.village_id}' not found. Available IDs: {list(VILLAGES_CONFIG.keys())}"
        )

    try:
        sim_res = simulate_shortage_scenario(
            village_id=vid,
            population=req.population,
            rainfall_mm=req.rainfall_mm,
            temp_celsius=req.temp_celsius,
            water_supply_litres=req.water_supply_litres,
            storage_capacity_litres=req.storage_capacity_litres,
            current_storage_litres=req.current_storage_litres,
            humidity_pct=req.humidity_pct
        )
        return ScenarioSimulationResponse(
            scenario_inputs=sim_res["scenario_inputs"],
            recalculated_demand_litres=sim_res["recalculated_demand_litres"],
            shortage_assessment=ShortageRiskResponse(**sim_res["shortage_assessment"])
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.get("/forecast", response_model=MultiDayForecastResponse, tags=["Forecasting"])
def get_multi_day_forecast(
    village_id: str = Query(default=DEFAULT_VILLAGE_ID, description="Village ID")
):
    """
    7-Day Autoregressive Demand & Shortage Forecast.
    Propagates dynamic lags and future Open-Meteo daily weather.
    """
    vid = village_id.upper()
    if vid not in VILLAGES_CONFIG:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Village '{village_id}' not found. Available IDs: {list(VILLAGES_CONFIG.keys())}"
        )

    try:
        forecast_data = predict_7_day_forecast(vid)
        return MultiDayForecastResponse(**forecast_data)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.post("/assistant/query", response_model=AssistantQueryResponse, tags=["AI Assistant"])
def query_assistant_endpoint(req: AssistantQueryRequest):
    """
    JalSense AI Conversational Assistant.
    Provides grounded natural-language answers regarding next-day water demand,
    shortage risks, weather impacts, and operational directives.
    """
    vid = req.village_id.upper()
    if vid not in VILLAGES_CONFIG:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Village '{req.village_id}' not found. Available IDs: {list(VILLAGES_CONFIG.keys())}"
        )
    try:
        pred_res = predict_next_day_demand(village_id=vid)
        res = assistant.ask(
            question=req.question,
            prediction_dict=pred_res,
            mode=req.mode
        )
        return AssistantQueryResponse(
            question=req.question,
            village_id=vid,
            answer=res["answer"],
            source_mode=res["source_mode"],
            source_label=res["source_label"],
            is_fallback=res["is_fallback"]
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# =============================================================================
# Backward Compatibility Aliases (Preserves Existing Dashboard & Tools)
# =============================================================================
@app.get("/villages", tags=["System"], include_in_schema=False)
def get_villages_alias():
    return {"count": len(VILLAGES_CONFIG), "villages": list(VILLAGES_CONFIG.values())}


@app.get("/weather/live/{village_id}", tags=["Weather"], include_in_schema=False)
def get_live_weather_alias(village_id: str, days: int = Query(default=7, ge=1, le=14)):
    return get_weather(village_id=village_id, days=days)


@app.post("/predict", tags=["Forecasting"], include_in_schema=False)
def predict_alias(req: PredictDemandRequest):
    return predict_demand_endpoint(req)


@app.post("/shortage/assess", tags=["Shortage Analysis"], include_in_schema=False)
def shortage_assess_alias(req: ShortageRiskRequest):
    return shortage_risk_endpoint(req)


@app.post("/shortage/simulate", tags=["Simulation"], include_in_schema=False)
def shortage_simulate_alias(req: ScenarioSimulationRequest):
    return simulate_endpoint(req)


@app.get("/models/metrics", tags=["System"])
def get_model_metrics():
    """Returns genuine holdout evaluation metrics from the saved model artifact."""
    try:
        _, _, metrics = get_cached_artifacts()
        return metrics
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))


@app.get("/models/comparison", tags=["System"])
def get_model_comparison():
    """Returns the genuine 4-model evaluation benchmark comparison table."""
    if not COMPARISON_TABLE_PATH.exists():
        raise HTTPException(status_code=404, detail="Model comparison table artifact not found.")
    try:
        df_comp = pd.read_csv(COMPARISON_TABLE_PATH)
        rows = []
        for _, r in df_comp.iterrows():
            rows.append({
                "model": str(r["Model"]),
                "val_mae": float(r["Val MAE (L)"]),
                "val_rmse": float(r["Val RMSE (L)"]),
                "val_r2": float(r["Val R2"]),
                "test_mae": float(r["Test MAE (L)"]),
                "test_rmse": float(r["Test RMSE (L)"]),
                "test_r2": float(r["Test R2"])
            })
        return {"count": len(rows), "comparison": rows}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/historical", tags=["Forecasting"])
def get_historical_demand(
    village_id: str = Query(default=DEFAULT_VILLAGE_ID, description="Village ID"),
    days: int = Query(default=45, ge=7, le=180, description="Historical observations count")
):
    """
    Returns recent historical water consumption observations for the selected village.
    Sources from clean processed empirical series or raw telemetry.
    """
    vid = village_id.upper()
    if vid not in VILLAGES_CONFIG:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Village '{village_id}' not found. Available IDs: {list(VILLAGES_CONFIG.keys())}"
        )

    proc_path = PROCESSED_DATA_DIR / "village_water_demand_clean.csv"
    raw_path = RAW_DATA_DIR / "village_water_demand_raw.csv"
    df = None
    if proc_path.exists():
        df = pd.read_csv(proc_path)
    elif raw_path.exists():
        df = pd.read_csv(raw_path)

    if df is None:
        return {
            "village_id": vid,
            "records_count": 0,
            "records": [],
            "stats": {"avg_demand_litres": 0, "min_demand_litres": 0, "max_demand_litres": 0}
        }

    v_df = df[df["village_id"] == vid].copy()
    v_df["date"] = pd.to_datetime(v_df["date"]).dt.strftime("%Y-%m-%d")
    v_df = v_df.sort_values("date").tail(days)

    records = []
    for _, row in v_df.iterrows():
        records.append({
            "date": str(row["date"]),
            "water_demand_litres": round(float(row["water_demand_litres"]), 1),
            "daily_supply_litres": round(float(row.get("daily_supply_litres", 150000.0)), 1),
            "temp_mean": round(float(row.get("temp_mean", 28.0)), 1),
            "rainfall_mm": round(float(row.get("rainfall_mm", 0.0)), 1),
            "humidity_pct": round(float(row.get("humidity_pct", 50.0)), 1)
        })

    demands = [r["water_demand_litres"] for r in records]
    stats = {
        "avg_demand_litres": round(float(sum(demands) / len(demands)), 1) if demands else 0,
        "min_demand_litres": round(float(min(demands)), 1) if demands else 0,
        "max_demand_litres": round(float(max(demands)), 1) if demands else 0
    }

    return {
        "village_id": vid,
        "records_count": len(records),
        "records": records,
        "stats": stats
    }

