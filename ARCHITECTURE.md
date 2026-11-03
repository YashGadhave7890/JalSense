# JalSense System Architecture

## 1. High-Level Architectural Diagram

```mermaid
flowchart TB
    subgraph DataLayer ["Data & Telemetry Ingestion Layer"]
        A1["Public Smart Meter CSV\n(263k Minutely Logs, CC-BY-SA)"] --> B1["Data Pipeline\n(Standardize YYYY-MM-DD)"]
        A2["Open-Meteo Weather API\n(Archive & Real-time Forecast)"] --> B2["Deterministic Disk Cache\n(MD5 Hashed TTL)"]
        B1 & B2 --> C["Unified Feature Matrix\n(data/processed/unified_features.csv)"]
    end

    subgraph FeatureML ["Feature Engineering & Model Pipeline"]
        C --> D["Feature Extractor\n(Lags 1,2,7 | 7d Rolling Stats | Heat Index)"]
        D --> E["Strict Chronological Split\n(70% Train | 15% Val | 15% Test)"]
        E --> F1["Linear Regression Baseline"]
        E --> F2["Random Forest Regressor"]
        E --> F3["XGBoost Regressor (Champion)"]
        E --> F4["TensorFlow/Keras Deep ANN\n(Dense 128 -> BN -> Dropout 0.3...)"]
        F3 --> G["Serialized Champion Artifacts\n(artifacts/models/water_demand_model.joblib)"]
    end

    subgraph Hydrology ["Hydrological Decision Engine"]
        G --> H["Prediction Engine\n(Next-Day & 7-Day Autoregressive)"]
        H --> I["Water Balance Calculator\n(Deficit / Surplus / JJM 55 LPCD)"]
        I --> J["Stochastic Shortage Analyzer\n(Gaussian Margin: P(Shortage) = Φ(-μ/σ))"]
        J --> K["Recommendation Engine\n(Tanker Requisition & Directives)"]
    end

    subgraph ServiceLayer ["Serving & Application Layer"]
        H & J & K --> L["FastAPI REST Service\n(Port 8000 | In-Memory Preloaded Models)"]
        H & J & K --> M["AI Assistant Module\n(Hugging Face QA + LLM + Fallback)"]
        L & M --> N["Streamlit Multi-Tab Dashboard\n(Port 8501 | Interactive Decision UI)"]
    end
```

---

## 2. Layer-by-Layer Architecture

### 1. Data Ingestion & Caching Layer (`src/weather_client.py`, `src/data_pipeline.py`)
- Downloads and normalizes public smart water meter telemetry from `LukaLike/water-consumption-data` into clean daily totals.
- Queries Open-Meteo weather coordinates with local disk caching (`data/cache/weather/`) using MD5 request hashes.

### 2. Preprocessing & Feature Engineering Layer (`src/preprocessing.py`, `src/features.py`)
- Standardizes timestamps to ISO-8601 (`YYYY-MM-DD`).
- Generates 15 domain-informed features:
  - Demographic scale: Census population
  - Meteorology: Temperature, precipitation, relative humidity, Steadman heat index
  - Calendar factors: Day of week, weekend indicator, month, encoded agro-climatic season
  - Autoregressive memory: Lag 1, Lag 2, Lag 7 daily demands
  - Rolling windows: 7-day rolling mean, rolling standard deviation, rolling maximum

### 3. Model Training & Evaluation Engine (`src/models.py`, `run_pipeline.py`)
- Enforces strict chronological train/validation/test splitting (70% / 15% / 15%) without shuffling to eliminate temporal data leakage.
- Trains and benchmarks 4 architectures: Linear Regression, Random Forest, XGBoost, and TensorFlow Deep ANN with Batch Normalization and Dropout.
- Automatically selects and serializes the champion model based on holdout Mean Absolute Error (MAE).

### 4. Hydrological Water Balance & Shortage Engine (`src/shortage.py`)
- Computes transparent volumetric water balances: Demand, Available Supply, Storage Buffer, and Deficit/Surplus.
- Calculates shortage probability using a stochastic Gaussian margin ($M = [S + \alpha B] - D$).
- Categorizes risk into 4 tiers: `LOW`, `MODERATE`, `HIGH`, `CRITICAL`.
- Generates templated administrative advisories with required disclaimers.

### 5. Conversational AI Assistant Layer (`src/assistant.py`)
- Synthesizes structured prediction telemetry into an unambiguous situation briefing.
- Routes queries through configurable LLM APIs (`.env`), local Hugging Face Transformers (`distilbert-base-cased-distilled-squad`), or a deterministic zero-hallucination fallback engine.
- Explicitly labels every answer with its source attribution mode.

### 6. Serving Layer (`api/main.py`, `app/streamlit_app.py`)
- **FastAPI Backend (Port 8000):** Async REST API exposing health checks, weather endpoints, next-day demand prediction, shortage risk evaluation, scenario simulation, and multi-day forecasts. Pre-loads models into memory on boot to eliminate disk I/O on inference hits.
- **Streamlit Dashboard (Port 8501):** 7 interactive sections featuring Plotly visualizations, gauge charts, parameter sliders, holdout benchmark tables, and interactive conversational assistant.

---

## 3. Container Orchestration Architecture

```mermaid
flowchart LR
    Host["Docker Host"] --> Compose["docker-compose.yml"]
    
    subgraph Network ["Bridge Network"]
        Compose --> APIService["jalsense-fastapi\n(Port 8000)"]
        Compose --> DashboardService["jalsense-streamlit\n(Port 8501)"]
    end
    
    subgraph Volumes ["Named Shared Volumes"]
        shared_data["shared-data\n(/app/data)"]
        shared_artifacts["shared-artifacts\n(/app/artifacts)"]
    end
    
    APIService -.-> shared_data
    APIService -.-> shared_artifacts
    DashboardService -.-> shared_data
    DashboardService -.-> shared_artifacts
    DashboardService -->|"Depends on healthy API"| APIService
```
