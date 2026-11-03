"""
API Integration Tests for FastAPI Endpoints
Tests:
- GET  /health
- GET  /weather
- POST /predict-demand
- POST /shortage-risk
- POST /simulate
- GET  /forecast
- Error handling (404 Not Found, 422 Unprocessable Entity)
"""

import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["model_loaded"] is True
    assert "villages" in data
    assert len(data["villages"]) >= 5


def test_get_weather_endpoint():
    response = client.get("/weather?village_id=VILL001&days=5")
    assert response.status_code == 200
    data = response.json()
    assert data["village_id"] == "VILL001"
    assert "Open-Meteo" in data["source"]
    assert len(data["forecast"]) == 5
    first_day = data["forecast"][0]
    assert "temp_mean" in first_day
    assert "rainfall_mm" in first_day


def test_get_weather_invalid_village():
    response = client.get("/weather?village_id=INVALID_999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_predict_demand_endpoint():
    payload = {
        "village_id": "VILL001",
        "custom_temp": 33.0,
        "custom_rainfall": 0.0,
        "custom_humidity": 45.0,
        "use_live_weather": False
    }
    response = client.post("/predict-demand", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["village_id"] == "VILL001"
    assert data["predicted_demand_litres"] > 0
    assert data["predicted_lpcd"] > 0
    assert "water_balance" in data
    assert "weather" in data


def test_predict_demand_invalid_village():
    payload = {"village_id": "VILL_NONEXISTENT"}
    response = client.post("/predict-demand", json=payload)
    assert response.status_code == 404


def test_shortage_risk_endpoint():
    payload = {
        "predicted_demand_litres": 150000.0,
        "estimated_supply_litres": 120000.0,
        "population": 2500,
        "storage_capacity_litres": 170000.0,
        "current_storage_litres": 80000.0
    }
    response = client.post("/shortage-risk", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["deficit_litres"] == 30000.0
    assert data["surplus_litres"] == 0.0
    assert 0.0 <= data["shortage_probability"] <= 1.0
    assert data["risk_category"] in ["HIGH", "CRITICAL", "MODERATE"]
    assert data["tankers_needed"] == 3
    assert "Predicted demand is 150,000 litres and estimated supply is 120,000 litres" in data["primary_recommendation"]
    assert "NOT an official or statutory water-management instruction" in data["disclaimer"]


def test_shortage_risk_validation_error():
    # Demand must be > 0
    payload = {
        "predicted_demand_litres": -500.0,
        "estimated_supply_litres": 100000.0
    }
    response = client.post("/shortage-risk", json=payload)
    assert response.status_code == 422  # Pydantic validation error


def test_simulate_endpoint():
    payload = {
        "village_id": "VILL001",
        "population": 3200,
        "rainfall_mm": 0.0,
        "temp_celsius": 39.0,
        "water_supply_litres": 110000.0,
        "storage_capacity_litres": 170000.0,
        "current_storage_litres": 40000.0,
        "humidity_pct": 35.0
    }
    response = client.post("/simulate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "scenario_inputs" in data
    assert "recalculated_demand_litres" in data
    assert data["recalculated_demand_litres"] > 0
    assert "shortage_assessment" in data
    assert data["shortage_assessment"]["risk_category"] in ["CRITICAL", "HIGH", "MODERATE", "LOW"]


def test_forecast_7_day_endpoint():
    response = client.get("/forecast?village_id=VILL001")
    assert response.status_code == 200
    data = response.json()
    assert data["village_id"] == "VILL001"
    assert data["forecast_days_count"] == 7
    assert len(data["forecasts"]) == 7
    first_forecast = data["forecasts"][0]
    assert "predicted_demand_litres" in first_forecast
    assert "risk_category" in first_forecast
    assert "tankers_needed" in first_forecast


def test_backward_compatibility_endpoints():
    # Test that legacy /villages and /predict and /shortage/assess work seamlessly
    r1 = client.get("/villages")
    assert r1.status_code == 200

    r2 = client.post("/predict", json={"village_id": "VILL001", "use_live_weather": False})
    assert r2.status_code == 200

    r3 = client.get("/models/metrics")
    assert r3.status_code == 200


def test_assistant_query_endpoint():
    payload = {
        "question": "What is the predicted water demand?",
        "village_id": "VILL001",
        "mode": "fallback"
    }
    response = client.post("/assistant/query", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["village_id"] == "VILL001"
    assert "demand" in data["answer"].lower()
    assert data["is_fallback"] is True
    assert "Deterministic" in data["source_label"]


def test_assistant_query_invalid_village():
    payload = {
        "question": "Will there be a shortage?",
        "village_id": "VILL_INVALID"
    }
    response = client.post("/assistant/query", json=payload)
    assert response.status_code == 404
