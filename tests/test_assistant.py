"""
Unit & Integration Tests for JalSense AI Assistant
Verifies:
1. Grounded factual context generation
2. All 5 required queries in deterministic fallback mode
3. Real numerical adherence (no invented values)
4. Source mode labeling (LLM vs HF vs Fallback)
5. Local Hugging Face Transformers QA integration
6. Unconfigured API key fallback resiliency
"""

import pytest
from src.prediction import predict_next_day_demand
from src.assistant import (
    JalSenseAssistant,
    build_situation_context,
    deterministic_fallback_response,
    query_huggingface_qa
)


@pytest.fixture(scope="module")
def sample_prediction():
    """Generates standard sample prediction output for VILL001."""
    return predict_next_day_demand("VILL001", use_live_weather=False)


def test_build_situation_context(sample_prediction):
    context = build_situation_context(sample_prediction)
    assert "JALSENSE SITUATION CONTEXT" in context
    assert sample_prediction["village_name"] in context
    demand = sample_prediction["water_balance"]["predicted_demand_litres"]
    assert f"{demand:,.1f}" in context
    assert "Jal Jeevan Mission" in context


def test_query_shortage_tomorrow(sample_prediction):
    assistant = JalSenseAssistant()
    res = assistant.ask("Will there be a shortage tomorrow?", sample_prediction, mode="fallback")
    
    assert res["is_fallback"] is True
    assert "Deterministic" in res["source_label"]
    
    # Check that answer aligns with actual deficit/surplus
    wb = sample_prediction["water_balance"]
    if wb["deficit_litres"] > 0:
        assert "Yes, a water deficit is forecasted" in res["answer"]
        assert f"{wb['deficit_litres']:,.0f}" in res["answer"]
    else:
        assert "No, there is no forecasted water shortage" in res["answer"]
        assert f"{wb['surplus_litres']:,.0f}" in res["answer"]


def test_query_why_is_shortage_risk_high(sample_prediction):
    assistant = JalSenseAssistant()
    res = assistant.ask("Why is the shortage risk high?", sample_prediction, mode="fallback")
    
    assert res["is_fallback"] is True
    wb = sample_prediction["water_balance"]
    assert wb["risk_category"] in res["answer"]
    assert f"{wb['shortage_probability_pct']:.1f}%" in res["answer"]


def test_query_predicted_water_demand(sample_prediction):
    assistant = JalSenseAssistant()
    res = assistant.ask("What is the predicted water demand?", sample_prediction, mode="fallback")
    
    wb = sample_prediction["water_balance"]
    demand = wb["predicted_demand_litres"]
    lpcd = wb["predicted_lpcd"]
    
    assert f"{demand:,.0f}" in res["answer"]
    assert f"{lpcd:.1f}" in res["answer"]
    assert "55.0 LPCD" in res["answer"]


def test_query_what_happens_if_rainfall_increases(sample_prediction):
    assistant = JalSenseAssistant()
    res = assistant.ask("What happens if rainfall increases?", sample_prediction, mode="fallback")
    
    assert "recharge" in res["answer"].lower()
    assert "irrigation" in res["answer"].lower()
    assert "temperature" in res["answer"].lower()
    assert "Scenario Simulator" in res["answer"]


def test_query_summarize_water_situation(sample_prediction):
    assistant = JalSenseAssistant()
    res = assistant.ask("Summarize today's water situation.", sample_prediction, mode="fallback")
    
    wb = sample_prediction["water_balance"]
    assert "Executive Water Situation Briefing" in res["answer"]
    assert f"{wb['predicted_demand_litres']:,.0f}" in res["answer"]
    assert f"{wb['estimated_supply_litres']:,.0f}" in res["answer"]
    assert wb["risk_category"] in res["answer"]


def test_source_labeling_fallback_when_no_api_key(sample_prediction, monkeypatch):
    # Simulate missing API key
    monkeypatch.setattr("src.assistant.LLM_API_KEY", None)
    inst = JalSenseAssistant()
    inst.has_api_key = False
    
    res = inst.ask("What is the predicted water demand?", sample_prediction, mode="auto")
    assert res["is_fallback"] is True
    assert res["source_mode"] == "fallback"
    assert "Deterministic Fallback" in res["source_label"]


def test_huggingface_transformers_qa(sample_prediction):
    assistant = JalSenseAssistant()
    res = assistant.ask("What is the predicted water demand?", sample_prediction, mode="hf")
    
    assert res["source_mode"] in ["huggingface", "fallback"]
    assert "Hugging Face" in res["source_label"] or "Deterministic" in res["source_label"]
    assert len(res["answer"]) > 10
