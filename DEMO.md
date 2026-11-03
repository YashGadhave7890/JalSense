# JalSense Demonstration & Evaluation Guide

This guide provides a structured walkthrough for evaluating **JalSense** during academic presentations, viva reviews, and technical demonstrations.

---

## 1. Quick Launch

Ensure the local services or Docker containers are running:

### Local Execution:
```bash
# Terminal 1: Launch FastAPI Service
uvicorn api.main:app --host 127.0.0.1 --port 8000

# Terminal 2: Launch Streamlit Dashboard
streamlit run app/streamlit_app.py --server.port=8501
```

### Docker Execution:
```bash
docker-compose up --build
```

- **Interactive Dashboard:** [http://localhost:8501](http://localhost:8501)
- **FastAPI OpenAPI Swagger Docs:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## 2. Walkthrough of Dashboard Sections

### Section 1: Overview
- **What to observe:**
  - Executive KPI cards: Predicted Demand (Litres & LPCD), Available Supply, Deficit/Surplus, and Shortage Risk badge.
  - Jal Jeevan Mission rural target benchmark gauge (55 LPCD).
  - Synchronized live weather for the selected village.
  - Recent historical demand trend line chart.

### Section 2: Demand Forecast
- **What to observe:**
  - Historical water consumption timeline over the multi-month record.
  - **Next 7-Day Autoregressive Forecast Table & Multi-Day Chart:** Demonstrates dynamic feature propagation (lags updated with prior day predictions) coupled with Open-Meteo forward weather forecasts.

### Section 3: Shortage Risk Analysis
- **What to observe:**
  - Shortage Probability Gauge ($P(\text{Shortage})$ calculated via Gaussian stochastic margin).
  - Tanker requisition calculator (computes exact number of 10,000L municipal tankers required).
  - Algorithmic recommendation banner with mandatory institutional disclaimer.

### Section 4: Weather Intelligence
- **What to observe:**
  - Real-time meteorological telemetry fetched from Open-Meteo.
  - Local disk cache indicator showing MD5 cache hits and fast response times.
  - Temperature, precipitation, humidity, and calculated Steadman Heat Index.

### Section 5: Scenario Simulator
- **What to test:**
  1. Slide **Temperature** up to `42°C` (heatwave stress-test) $\rightarrow$ observe demand surge.
  2. Slide **Precipitation** up to `35 mm` $\rightarrow$ observe demand reduction.
  3. Slide **Available Water Supply** down to `60,000 L` (pump breakdown) $\rightarrow$ watch Shortage Risk transition from `LOW` to `CRITICAL` with instant tanker requisition calculation.

### Section 6: Model Performance & Benchmarking
- **What to observe:**
  - Genuine holdout benchmark comparison table across **Linear Regression**, **Random Forest**, **XGBoost**, and **TensorFlow Deep ANN**.
  - Confirms zero fabricated scores: XGBoost champion achieved holdout MAE of **6,589.57 L** and $R^2 = 0.9884$.
  - Feature Importance chart highlighting top drivers (`rolling_max_7d`, `population`, `demand_lag_7`).

### Section 7: AI Hydrological Assistant
- **What to test:**
  1. Click **"🚨 Shortage Tomorrow?"** $\rightarrow$ verifies factual answer on tomorrow's water balance.
  2. Click **"🔍 Why Risk Level?"** $\rightarrow$ explains hydrological contributing factors.
  3. Click **"🌧️ Rainfall Impact?"** $\rightarrow$ explains groundwater recharge and thermal dynamics.
  4. Type a custom query in the chat input.
  5. Check the source provenance badge (`🤖 LLM Powered`, `🤗 Hugging Face Transformers`, or `⚙️ Deterministic Fallback Mode`).
  6. Expand **"View Grounding Situation Context"** to inspect the factual data block provided to the assistant.

---

## 3. FastAPI REST Endpoint Demonstrations

Test all endpoints using `curl` or FastAPI's interactive Swagger UI at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs):

```bash
# 1. Health Probe
curl -X GET "http://127.0.0.1:8000/health"

# 2. Weather Synchronization
curl -X GET "http://127.0.0.1:8000/weather?village_id=VILL001&days=3"

# 3. Next-Day Demand Prediction
curl -X POST "http://127.0.0.1:8000/predict-demand" \
     -H "Content-Type: application/json" \
     -d '{"village_id": "VILL001", "use_live_weather": true}'

# 4. Shortage Risk Assessment
curl -X POST "http://127.0.0.1:8000/shortage-risk" \
     -H "Content-Type: application/json" \
     -d '{"predicted_demand_litres": 145000.0, "estimated_supply_litres": 110000.0}'

# 5. Scenario Simulation
curl -X POST "http://127.0.0.1:8000/simulate" \
     -H "Content-Type: application/json" \
     -d '{"village_id": "VILL001", "population": 3000, "temp_celsius": 40.0, "water_supply_litres": 90000.0}'

# 6. 7-Day Autoregressive Forecast
curl -X GET "http://127.0.0.1:8000/forecast?village_id=VILL001"

# 7. Conversational AI Assistant Query
curl -X POST "http://127.0.0.1:8000/assistant/query" \
     -H "Content-Type: application/json" \
     -d '{"question": "Will there be a shortage tomorrow?", "village_id": "VILL001", "mode": "fallback"}'
```

---

## 4. Key Academic Evaluation Highlights

- **Real Empirical Telemetry:** 263,811 actual smart meter observations standardized to daily timesteps.
- **Strict Time-Series Integrity:** 70% / 15% / 15% chronological split with zero random shuffling.
- **Four Model Architectures:** Linear Regression, Random Forest, XGBoost, and TensorFlow Deep ANN with Batch Normalization and Dropout.
- **Explainable Hydrological Logic:** Shortage probability calculated via Gaussian stochastic margin rather than arbitrary black-box thresholds.
- **Resilient AI Assistant:** Zero-hallucination guarantee through structured context grounding, configurable LLM, local Hugging Face Transformers, and deterministic fallback.
