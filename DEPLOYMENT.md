# JalSense Production Docker Deployment & Registry Guide 🐳

This guide outlines the production container deployment procedure for **JalSense — Village-Level Water Demand Prediction, Shortage Forecasting & Intelligent Water Management System**, including local orchestration and publishing images to **Docker Hub**.

---

## 1. System Architecture & Container Topology

```
                       [ Public Traffic ]
                                |
               +----------------+----------------+
               |                                 |
       (Port 3000 / 80)                  (Port 8000)
               v                                 v
   +-----------------------+         +-----------------------+
   |   jalsense-frontend   |         |    jalsense-backend   |
   | (React + Vite + Nginx)| ===/api/==> |   (Python FastAPI)    |
   +-----------------------+         +-----------------------+
                                                 |
                                     +-----------+-----------+
                                     |                       |
                                     v                       v
                              [shared-data]          [shared-artifacts]
                              (Weather Cache)         (Trained Models)
```

- **Frontend Container (`jalsense-frontend`):** Built with Node.js 20, served via lightweight Nginx Alpine. Automatically reverse-proxies `/api/*` to the FastAPI backend service over the internal Docker network.
- **Backend Container (`jalsense-backend`):** Built on Python 3.11 Slim, serves the FastAPI application with in-memory preloaded model artifacts on `0.0.0.0:8000`.
- **Auxiliary Container (`jalsense-dashboard`):** Preserved Streamlit prototype interface on port `8501`.

---

## 2. Image Naming & Tagging Conventions

| Component | Repository Name | Recommended Tag | Full Image Identifier |
| :--- | :--- | :--- | :--- |
| **Backend REST API** | `jalsense-backend` | `1.0.0`, `latest` | `DOCKERHUB_USERNAME/jalsense-backend:1.0.0` |
| **React Web App** | `jalsense-frontend` | `1.0.0`, `latest` | `DOCKERHUB_USERNAME/jalsense-frontend:1.0.0` |
| **Streamlit Prototype** | `jalsense-dashboard` | `1.0.0`, `latest` | `DOCKERHUB_USERNAME/jalsense-dashboard:1.0.0` |

> *Replace `DOCKERHUB_USERNAME` with your actual Docker Hub account handle.*

---

## 3. Prerequisites

Before deploying or publishing:
1. **Docker Engine & Docker Compose:** Install Docker Desktop (Windows/macOS) or Docker CE + Compose plugin (Linux). Verify via:
   ```bash
   docker --version
   docker compose version
   ```
2. **Docker Hub Account:** Create a free account at [hub.docker.com](https://hub.docker.com) if you do not have one.
3. **Environment Template:** Copy the safe environment templates before building:
   ```bash
   cp .env.example .env
   cp frontend/.env.example frontend/.env
   ```

---

## 4. Local Build & Orchestration (Docker Compose)

### Step 4.1: Build All Images Locally
```bash
docker compose build
```

To build individual services:
```bash
# Build backend image only
docker build -t DOCKERHUB_USERNAME/jalsense-backend:1.0.0 -f Dockerfile .

# Build frontend image only
docker build -t DOCKERHUB_USERNAME/jalsense-frontend:1.0.0 -f frontend/Dockerfile ./frontend
```

### Step 4.2: Start Services via Docker Compose
```bash
docker compose up -d
```

### Step 4.3: Verify Running Containers & Health Status
```bash
docker compose ps
```

Expected output:
```
NAME                    IMAGE                               COMMAND                  SERVICE      STATUS
jalsense-backend        DOCKERHUB_USERNAME/jalsense-backend:1.0.0    "uvicorn api.main:ap…"   api          running (healthy)
jalsense-frontend       DOCKERHUB_USERNAME/jalsense-frontend:1.0.0   "/docker-entrypoint.…"   frontend     running (healthy)
jalsense-dashboard      DOCKERHUB_USERNAME/jalsense-dashboard:1.0.0  "streamlit run app/s…"   dashboard    running (healthy)
```

### Step 4.4: Service Health Verification
```bash
# 1. Test Backend Health Probe
curl -f http://localhost:8000/health

# 2. Test Real Next-Day Demand Prediction
curl -X POST http://localhost:8000/predict-demand \
  -H "Content-Type: application/json" \
  -d '{"village_id": "VILL001", "use_live_weather": true}'

# 3. Test Frontend Web Server
curl -I http://localhost:3000
```

---

## 5. Publishing Images to Docker Hub

### Step 5.1: Authenticate with Docker Hub
Run the authentication command in your terminal and enter your username and Personal Access Token (or password):
```bash
docker login
```

### Step 5.2: Tag Images for Your Repository
```bash
# Tag Backend Image
docker tag jalsense/jalsense-backend:1.0.0 DOCKERHUB_USERNAME/jalsense-backend:1.0.0
docker tag jalsense/jalsense-backend:1.0.0 DOCKERHUB_USERNAME/jalsense-backend:latest

# Tag Frontend Image
docker tag jalsense/jalsense-frontend:1.0.0 DOCKERHUB_USERNAME/jalsense-frontend:1.0.0
docker tag jalsense/jalsense-frontend:1.0.0 DOCKERHUB_USERNAME/jalsense-frontend:latest
```

### Step 5.3: Push Images to Docker Hub
```bash
# Push Backend Image
docker push DOCKERHUB_USERNAME/jalsense-backend:1.0.0
docker push DOCKERHUB_USERNAME/jalsense-backend:latest

# Push Frontend Image
docker push DOCKERHUB_USERNAME/jalsense-frontend:1.0.0
docker push DOCKERHUB_USERNAME/jalsense-frontend:latest
```

---

## 6. Running Published Images on Any Host

On any deployment server (e.g. AWS EC2, DigitalOcean, Azure VM, local workstation):

### Option A: Using Pre-Built Images with Docker Compose
Create a `docker-compose.prod.yml` referencing your published images:

```yaml
version: "3.8"

networks:
  jalsense-network:
    driver: bridge

services:
  api:
    image: DOCKERHUB_USERNAME/jalsense-backend:1.0.0
    container_name: jalsense-backend
    restart: unless-stopped
    ports:
      - "8000:8000"
    environment:
      - API_PORT=8000
      - API_HOST=0.0.0.0
      - PYTHONUNBUFFERED=1
    networks:
      - jalsense-network

  frontend:
    image: DOCKERHUB_USERNAME/jalsense-frontend:1.0.0
    container_name: jalsense-frontend
    restart: unless-stopped
    ports:
      - "3000:80"
    depends_on:
      - api
    networks:
      - jalsense-network
```

Run:
```bash
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d
```

### Option B: Running Individual Containers with Docker CLI
```bash
# 1. Create a shared bridge network
docker network create jalsense-network

# 2. Run the backend service
docker run -d \
  --name jalsense-backend \
  --network jalsense-network \
  -p 8000:8000 \
  DOCKERHUB_USERNAME/jalsense-backend:1.0.0

# 3. Run the frontend web application
docker run -d \
  --name jalsense-frontend \
  --network jalsense-network \
  -p 3000:80 \
  DOCKERHUB_USERNAME/jalsense-frontend:1.0.0
```

- Access **React Dashboard:** `http://<HOST_IP>:3000`
- Access **FastAPI OpenAPI Swagger:** `http://<HOST_IP>:8000/docs`

---

## 7. Environment Variables Reference

| Variable | Service | Default Value | Description |
| :--- | :--- | :--- | :--- |
| `API_PORT` | Backend | `8000` | Port for FastAPI service |
| `API_HOST` | Backend | `0.0.0.0` | Host binding interface |
| `FRONTEND_PORT` | Frontend | `3000` | Host port mapped to Nginx port 80 |
| `STREAMLIT_PORT` | Dashboard | `8501` | Host port for Streamlit |
| `CORS_ORIGINS` | Backend | `http://localhost:5173,http://localhost:3000` | Explicit allowed browser origins |
| `OPEN_METEO_BASE_URL` | Backend | `https://api.open-meteo.com/v1/forecast` | Open-Meteo weather endpoint |
| `JJM_BENCHMARK_LPCD` | Backend | `55.0` | National Jal Jeevan Mission standard |
| `LLM_PROVIDER` | Backend | `groq` | Cloud LLM provider (or fallback) |
| `LLM_API_KEY` | Backend | `None` (Optional) | API key for assistant grounding |
| `LLM_MODEL` | Backend | `openai/gpt-oss-120b` | Target language model |

---

## 8. MLOps, Model Artifacts & Reproducibility

### Trained Artifact Locations (Baked into Backend Image)
All model artifacts reside in `artifacts/models/` and are verified on startup:
- `artifacts/models/water_demand_model.joblib` — XGBoost Regressor (`v2.0.0-champion-xgboost`, Test MAE: 6,589.57 L, $R^2$: 0.9884)
- `artifacts/models/water_demand_ann.keras` — TensorFlow/Keras Deep ANN (Input $\rightarrow$ Dense 128 $\rightarrow$ Dense 64 $\rightarrow$ Dense 32 $\rightarrow$ Dense 1)
- `artifacts/models/feature_scaler.joblib` & `target_scaler.joblib` — StandardScaler preprocessing objects
- `artifacts/models/model_metrics.json` — Holdout evaluation metrics
- `artifacts/models/model_comparison_table.csv` — 4-model evaluation benchmark table
- `artifacts/mlops_metadata.json` — Training timestamps and split statistics

### Dataset Provenance
- **Empirical Baseline:** 263,811 minutely smart water meter readings from `LukaLike/water-consumption-data` on GitHub (CC BY-SA 4.0).
- **Meteorological Fusion:** Open-Meteo Historical Archive and Forecast APIs (ODbL).
- **Reproducible Pipeline:** `python run_pipeline.py` executes data cleaning, 3-way chronological split (70/15/15), and model training.

---

## 9. Troubleshooting & Diagnostics

1. **Backend fails healthcheck:**
   - Inspect container logs: `docker logs jalsense-backend`
   - Verify that model artifacts exist in `artifacts/models/`.
2. **Frontend cannot reach backend (`502 Bad Gateway`):**
   - Check that both containers share `jalsense-network`:
     `docker network inspect jalsense-network`
   - Verify that the backend service container is reachable from frontend:
     `docker exec -it jalsense-frontend wget -qO- http://api:8000/health`
3. **Stopping & Cleaning Up:**
   ```bash
   # Stop all services
   docker compose down

   # Stop and purge persistent volumes
   docker compose down -v
   ```
