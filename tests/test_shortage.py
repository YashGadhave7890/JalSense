"""
Unit & Integration Tests for Intelligent Shortage Analysis & Decision Support
"""

import pytest
from src.shortage import (
    assess_water_shortage,
    calculate_shortage_probability,
    simulate_shortage_scenario
)


def test_shortage_deficit_and_surplus_logic():
    # Deficit Case: Demand 120,000, Supply 100,000 -> Deficit 20,000, Surplus 0
    res_def = assess_water_shortage(
        predicted_demand_litres=120000.0,
        estimated_supply_litres=100000.0,
        population=2000
    )
    assert res_def["deficit_litres"] == 20000.0
    assert res_def["surplus_litres"] == 0.0
    assert res_def["supply_coverage_ratio"] == round(100000.0 / 120000.0, 3)

    # Surplus Case: Demand 80,000, Supply 100,000 -> Deficit 0, Surplus 20,000
    res_sur = assess_water_shortage(
        predicted_demand_litres=80000.0,
        estimated_supply_litres=100000.0,
        population=2000
    )
    assert res_sur["deficit_litres"] == 0.0
    assert res_sur["surplus_litres"] == 20000.0
    assert res_sur["risk_category"] == "LOW"


def test_shortage_probability_estimation():
    # Severe deficit scenario: Supply far below demand -> Probability near 1.0
    p_high = calculate_shortage_probability(
        predicted_demand=150000.0,
        estimated_supply=80000.0,
        storage_buffer_litres=10000.0
    )
    assert 0.80 <= p_high <= 1.0

    # Ample surplus scenario: Supply far exceeds demand -> Probability near 0.0
    p_low = calculate_shortage_probability(
        predicted_demand=90000.0,
        estimated_supply=160000.0,
        storage_buffer_litres=50000.0
    )
    assert 0.0 <= p_low <= 0.10


def test_risk_categories_tiers():
    # 1. CRITICAL
    crit = assess_water_shortage(predicted_demand_litres=200000.0, estimated_supply_litres=120000.0)
    assert crit["risk_category"] == "CRITICAL"
    assert crit["shortage_probability"] >= 0.75

    # 2. HIGH
    high = assess_water_shortage(predicted_demand_litres=150000.0, estimated_supply_litres=130000.0)
    assert high["risk_category"] in ["HIGH", "CRITICAL"]

    # 3. LOW
    low = assess_water_shortage(predicted_demand_litres=100000.0, estimated_supply_litres=130000.0)
    assert low["risk_category"] == "LOW"


def test_recommendation_format_and_disclaimer():
    demand = 125000.0
    supply = 95000.0
    res = assess_water_shortage(predicted_demand_litres=demand, estimated_supply_litres=supply)

    rec = res["primary_recommendation"]
    # Check exact format requirements
    assert "Predicted demand is 125,000 litres and estimated supply is 95,000 litres" in rec
    assert "producing a deficit of 30,000 litres" in rec
    assert "Recommended action: increase available supply/reserve capacity by approximately 30,000 litres." in rec

    # Check non-official disclaimer
    disclaimer = res["disclaimer"]
    assert "NOT an official or statutory water-management instruction" in disclaimer


def test_scenario_simulator_recalculation():
    # Simulation should re-run model inference and re-compute shortage risk
    sim = simulate_shortage_scenario(
        village_id="VILL001",
        population=3000,
        rainfall_mm=0.0,
        temp_celsius=38.0,
        water_supply_litres=110000.0,
        storage_capacity_litres=150000.0,
        current_storage_litres=40000.0
    )
    assert "scenario_inputs" in sim
    assert "recalculated_demand_litres" in sim
    assert sim["recalculated_demand_litres"] > 0
    assert "shortage_assessment" in sim
    assert sim["shortage_assessment"]["risk_category"] in ["LOW", "MODERATE", "HIGH", "CRITICAL"]
