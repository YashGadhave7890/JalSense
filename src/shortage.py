"""
JalSense: Intelligent Shortage Analysis & Decision Support Module
Implements probabilistic risk assessment, transparent hydrological deficit/surplus modeling,
scenario stress-testing, and automated recommendation generation.
"""

import math
from typing import Dict, Any, List, Optional
from scipy.stats import norm
from src.config import JJM_BENCHMARK_LPCD

STANDARD_TANKER_CAPACITY_LITRES = 10000.0  # Standard rural municipal water tanker capacity


def calculate_shortage_probability(
    predicted_demand: float,
    estimated_supply: float,
    storage_buffer_litres: float = 0.0,
    demand_std_err: Optional[float] = None,
    supply_std_err: Optional[float] = None
) -> float:
    """
    Transparent & Explainable Shortage Probability Estimation using Gaussian margin modeling.
    
    Margin M = (Supply + Usable Storage Buffer) - Demand
    Where:
        Demand ~ N(mu_D, sigma_D^2)
        Supply ~ N(mu_S, sigma_S^2)
        Margin M ~ N(mu_M, sigma_M^2)
        Shortage occurs when M < 0
        P(Shortage) = Phi(-mu_M / sigma_M)
    
    Usable storage buffer accounts for maximum safe single-day tank depletion (~50% of storage).
    """
    usable_storage = max(0.0, storage_buffer_litres * 0.50)
    effective_supply = estimated_supply + usable_storage

    # Demand uncertainty: default to ~5.5% model RMSE / residual variance if not supplied
    sigma_d = demand_std_err if demand_std_err is not None else max(500.0, predicted_demand * 0.055)
    # Supply uncertainty: pumping/groundwater fluctuation ~4%
    sigma_s = supply_std_err if supply_std_err is not None else max(400.0, estimated_supply * 0.040)

    sigma_margin = math.sqrt(sigma_d**2 + sigma_s**2)
    mu_margin = effective_supply - predicted_demand

    if sigma_margin <= 0:
        return 1.0 if mu_margin < 0 else 0.0

    z_score = -mu_margin / sigma_margin
    prob = float(norm.cdf(z_score))
    return round(float(np_clip(prob, 0.001, 0.999)), 4)


def np_clip(val: float, low: float, high: float) -> float:
    return max(low, min(high, val))


def assess_water_shortage(
    predicted_demand_litres: float,
    estimated_supply_litres: float,
    population: int = 2000,
    storage_capacity_litres: float = 150000.0,
    current_storage_litres: float = 75000.0,
    demand_std_err: Optional[float] = None
) -> Dict[str, Any]:
    """
    Comprehensive, explainable water balance assessment:
    1. Predicted next-day demand
    2. Estimated available supply
    3. Deficit / Surplus calculation
    4. Shortage probability (Gaussian margin modeling)
    5. Risk category: LOW, MODERATE, HIGH, CRITICAL
    6. Recommendation engine matching required template format.
    """
    pred_demand = max(1.0, float(predicted_demand_litres))
    est_supply = max(0.0, float(estimated_supply_litres))
    storage_cap = max(0.0, float(storage_capacity_litres))
    cur_storage = max(0.0, float(current_storage_litres))

    # 1. Deficit / Surplus
    deficit_litres = max(0.0, pred_demand - est_supply)
    surplus_litres = max(0.0, est_supply - pred_demand)
    coverage_ratio = est_supply / pred_demand
    coverage_pct = round(coverage_ratio * 100.0, 1)

    predicted_lpcd = round(pred_demand / max(1, population), 2)
    supply_lpcd = round(est_supply / max(1, population), 2)

    # 2. Shortage Probability
    shortage_prob = calculate_shortage_probability(
        predicted_demand=pred_demand,
        estimated_supply=est_supply,
        storage_buffer_litres=cur_storage,
        demand_std_err=demand_std_err
    )
    shortage_prob_pct = round(shortage_prob * 100.0, 1)

    # 3. Transparent Multi-Criteria Risk Categorization
    # Grounded on coverage ratio and shortage probability
    if coverage_ratio < 0.80 or shortage_prob >= 0.75:
        risk_category = "CRITICAL"
        risk_color = "#DC2626"  # Red
        risk_description = "Critical water deficit exceeding 20% of requirements. Reserves under extreme strain."
    elif coverage_ratio < 0.95 or shortage_prob >= 0.45:
        risk_category = "HIGH"
        risk_color = "#EA580C"  # Orange
        risk_description = "High shortage risk. Daily demand meaningfully exceeds incoming source yield."
    elif coverage_ratio < 1.05 or shortage_prob >= 0.15:
        risk_category = "MODERATE"
        risk_color = "#CA8A04"  # Yellow
        risk_description = "Moderate risk. Supply closely balances demand with minimal safety buffer."
    else:
        risk_category = "LOW"
        risk_color = "#16A34A"  # Green
        risk_description = "Low shortage risk. Available supply and storage yield adequately cover forecasted consumption."

    # 4. Tanker Logistical Requirements
    tankers_needed = 0
    if deficit_litres > 0:
        tankers_needed = math.ceil(deficit_litres / STANDARD_TANKER_CAPACITY_LITRES)


    # 5. Recommendation Engine (Standard Template Format)
    x_val = f"{int(round(pred_demand)):,}"
    y_val = f"{int(round(est_supply)):,}"
    z_val = f"{int(round(deficit_litres)):,}"
    s_val = f"{int(round(surplus_litres)):,}"

    if deficit_litres > 0:
        primary_recommendation = (
            f"Predicted demand is {x_val} litres and estimated supply is {y_val} litres, "
            f"producing a deficit of {z_val} litres. Recommended action: increase available "
            f"supply/reserve capacity by approximately {z_val} litres."
        )
    else:
        primary_recommendation = (
            f"Predicted demand is {x_val} litres and estimated supply is {y_val} litres, "
            f"producing a surplus of {s_val} litres. Recommended action: store surplus volume "
            f"in overhead storage/groundwater recharge tanks to fortify dry-season reserve buffer."
        )

    disclaimer = (
        "Note: This recommendation is generated as algorithmic decision-support guidance for Gram Panchayat "
        "resource planning and is NOT an official or statutory water-management instruction."
    )

    # Operational directives
    operational_directives: List[str] = []
    if risk_category == "CRITICAL":
        operational_directives.append(
            f"🚨 Requisition {tankers_needed} municipal water tanker(s) ({int(tankers_needed * STANDARD_TANKER_CAPACITY_LITRES):,} L) for emergency distribution."
        )
        operational_directives.append(
            "⚠️ Impose essential domestic rationing: Prioritize 40 LPCD drinking and cooking supplies."
        )
        operational_directives.append(
            "🛑 Temporarily suspend non-essential bulk water drawing (construction, civic watering)."
        )
    elif risk_category == "HIGH":
        operational_directives.append(
            f"⚠️ Place {tankers_needed} emergency tanker(s) on standby for vulnerable community wards."
        )
        operational_directives.append(
            "⏳ Shift pumping cycles to early morning off-peak electrical supply hours."
        )
        operational_directives.append(
            "🚰 Enforce rotational dual-batch ward supply (morning 6-8 AM, evening 5-7 PM)."
        )
    elif risk_category == "MODERATE":
        operational_directives.append(
            "ℹ️ Offset temporary deficit by drawing from overhead storage reservoir buffer."
        )
        operational_directives.append(
            "🔍 Inspect pipeline feeder valves for distribution leakage or pressure anomalies."
        )
    else:
        operational_directives.append(
            "✅ Normal Operations: Source yield comfortably meets next-day forecasted demand."
        )
        operational_directives.append(
            f"💧 Channel excess supply ({s_val} L) into community overhead tank to maintain 100% capacity."
        )

    return {
        "predicted_demand_litres": round(pred_demand, 1),
        "estimated_supply_litres": round(est_supply, 1),
        "deficit_litres": round(deficit_litres, 1),
        "surplus_litres": round(surplus_litres, 1),
        "supply_coverage_ratio": round(coverage_ratio, 3),
        "coverage_percentage": coverage_pct,
        "shortage_probability": shortage_prob,
        "shortage_probability_pct": shortage_prob_pct,
        "risk_category": risk_category,
        "risk_color": risk_color,
        "risk_description": risk_description,
        "tankers_needed": tankers_needed,
        "tanker_capacity_litres": STANDARD_TANKER_CAPACITY_LITRES,
        "primary_recommendation": primary_recommendation,
        "disclaimer": disclaimer,
        "operational_directives": operational_directives,
        "predicted_lpcd": predicted_lpcd,
        "supply_lpcd": supply_lpcd,
        "jjm_benchmark_lpcd": JJM_BENCHMARK_LPCD,
        # Backward compatibility aliases
        "shortage_risk": risk_category,
        "recommendations": [primary_recommendation] + operational_directives
    }


def simulate_shortage_scenario(
    village_id: str,
    population: int,
    rainfall_mm: float,
    temp_celsius: float,
    water_supply_litres: float,
    storage_capacity_litres: float,
    current_storage_litres: float,
    humidity_pct: float = 50.0
) -> Dict[str, Any]:
    """
    Simulates a what-if scenario by recalculating demand and shortage risk.
    """
    from src.prediction import predict_next_day_demand

    # Recalculate demand using model inference
    pred_res = predict_next_day_demand(
        village_id=village_id,
        custom_temp=temp_celsius,
        custom_rainfall=rainfall_mm,
        custom_humidity=humidity_pct,
        custom_population=population,
        custom_supply=water_supply_litres,
        use_live_weather=False
    )

    pred_demand = pred_res["water_balance"]["predicted_demand_litres"]

    # Re-evaluate shortage analysis with new tank & supply parameters
    assessment = assess_water_shortage(
        predicted_demand_litres=pred_demand,
        estimated_supply_litres=water_supply_litres,
        population=population,
        storage_capacity_litres=storage_capacity_litres,
        current_storage_litres=current_storage_litres
    )

    return {
        "scenario_inputs": {
            "village_id": village_id,
            "population": population,
            "rainfall_mm": rainfall_mm,
            "temp_celsius": temp_celsius,
            "water_supply_litres": water_supply_litres,
            "storage_capacity_litres": storage_capacity_litres,
            "current_storage_litres": current_storage_litres
        },
        "recalculated_demand_litres": pred_demand,
        "shortage_assessment": assessment
    }
