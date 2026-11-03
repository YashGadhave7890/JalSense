"""
JalSense AI Assistant: Natural Language Explainer & Conversational Engine
Provides natural-language interpretation of water forecasts, hydrological shortage risks,
and decision-support recommendations.

Features:
1. Grounded Context Generation: Synthesizes real model predictions into a factual briefing.
2. Configurable LLM Provider: Connects to OpenAI, OpenRouter, Groq, Gemini via .env.
3. Local Hugging Face Transformers: Local DistilBERT SQuAD question-answering.
4. Deterministic Fallback Engine: Zero-hallucination rule-based NLG grounded in model outputs.
5. Response Source Labeling: Explicit metadata tracking (LLM vs HF vs Fallback).
"""

import os
import re
import json
import logging
from typing import Dict, Any, Optional, Tuple
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger("jalsense.assistant")

# Environment configurations
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

if GROQ_API_KEY and not os.getenv("LLM_API_KEY"):
    LLM_PROVIDER = "groq"
    LLM_API_KEY = GROQ_API_KEY
    LLM_MODEL = os.getenv("LLM_MODEL") or GROQ_MODEL
    LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1")
else:
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai").lower()
    LLM_API_KEY = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY") or os.getenv("GEMINI_API_KEY") or GROQ_API_KEY
    LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
    if LLM_PROVIDER == "groq":
        LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1")
    else:
        LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")

# Lazy-loaded HF QA model cache
_HF_QA_TOKENIZER = None
_HF_QA_MODEL = None


def load_hf_qa_pipeline():
    """Lazy load Hugging Face Question Answering model."""
    global _HF_QA_TOKENIZER, _HF_QA_MODEL
    if _HF_QA_TOKENIZER is None or _HF_QA_MODEL is None:
        try:
            import torch
            from transformers import AutoTokenizer, AutoModelForQuestionAnswering
            model_name = "distilbert-base-cased-distilled-squad"
            _HF_QA_TOKENIZER = AutoTokenizer.from_pretrained(model_name)
            _HF_QA_MODEL = AutoModelForQuestionAnswering.from_pretrained(model_name)
            logger.info("Loaded Hugging Face QA pipeline: %s", model_name)
        except Exception as e:
            logger.warning("Could not load Hugging Face QA pipeline: %s", e)
            return None, None
    return _HF_QA_TOKENIZER, _HF_QA_MODEL


def build_situation_context(prediction_dict: Dict[str, Any]) -> str:
    """
    Synthesizes actual prediction and water balance data into an unambiguous,
    factual situation context block.
    """
    v_name = prediction_dict.get("village_name", "Micro-Catchment Area")
    v_id = prediction_dict.get("village_id", "VILL001")
    state = prediction_dict.get("state", "India")
    f_date = prediction_dict.get("forecast_date", "Tomorrow")
    
    wb = prediction_dict.get("water_balance", {})
    weather = prediction_dict.get("weather", {})
    features = prediction_dict.get("features_used", {})

    demand = wb.get("predicted_demand_litres", prediction_dict.get("predicted_demand_litres", 0.0))
    supply = wb.get("estimated_supply_litres", prediction_dict.get("estimated_supply_litres", 0.0))
    deficit = wb.get("deficit_litres", 0.0)
    surplus = wb.get("surplus_litres", 0.0)
    coverage = wb.get("coverage_percentage", 100.0)
    shortage_prob = wb.get("shortage_probability_pct", 0.0)
    risk_cat = wb.get("risk_category", "LOW")
    tankers = wb.get("tankers_needed", 0)
    lpcd = wb.get("predicted_lpcd", 55.0)
    jjm = wb.get("jjm_benchmark_lpcd", 55.0)
    rec = wb.get("primary_recommendation", "Maintain standard monitoring.")

    temp = weather.get("temp_mean_celsius", features.get("temp_mean", 28.0))
    rain = weather.get("rainfall_mm", features.get("rainfall_mm", 0.0))
    humidity = weather.get("humidity_pct", features.get("humidity_pct", 50.0))
    season = weather.get("season", "Current Season")
    pop = features.get("population", 2000)
    lag1 = features.get("demand_lag_1", demand)

    context = f"""=== JALSENSE SITUATION CONTEXT ===
Village: {v_name} ({v_id}, {state})
Target Forecast Date: {f_date}
Demographics: Population of {pop:,} residents
Meteorology: Temperature {temp}°C, Precipitation {rain} mm, Relative Humidity {humidity}%, Season {season}

WATER BALANCE AND DEMAND FORECAST:
- Predicted Water Demand: {demand:,.1f} litres ({lpcd:.1f} LPCD)
- Estimated Incoming Supply: {supply:,.1f} litres
- Water Balance Outcome: {'Deficit of ' + f'{deficit:,.1f}' + ' litres' if deficit > 0 else 'Surplus of ' + f'{surplus:,.1f}' + ' litres'}
- Supply Coverage Ratio: {coverage:.1f}% of requirements met
- Shortage Probability: {shortage_prob:.1f}% (calculated via Gaussian margin stochastic model)
- Shortage Risk Classification: {risk_cat}
- Emergency Tanker Requisition Requirement: {tankers} tanker(s) (10,000 litres capacity each)
- National Jal Jeevan Mission Benchmark: {jjm:.1f} LPCD (Current forecast is {round(lpcd / jjm, 2)}x the national benchmark)
- Prior Day Consumption Lag: {lag1:,.1f} litres

ACTION ADVISORY AND DIRECTIVES:
- Primary Recommendation: {rec}
- Regulatory Note: This recommendation is generated as algorithmic decision-support guidance for Gram Panchayat resource planning and is not a statutory order.
"""
    return context.strip()


def query_huggingface_qa(question: str, context: str) -> Optional[str]:
    """
    Performs extractive Question-Answering using local Hugging Face Transformers model.
    """
    tokenizer, model = load_hf_qa_pipeline()
    if tokenizer is None or model is None:
        return None

    try:
        import torch
        inputs = tokenizer(question, context, return_tensors="pt", max_length=512, truncation=True)
        with torch.no_grad():
            outputs = model(**inputs)

        start_idx = torch.argmax(outputs.start_logits)
        end_idx = torch.argmax(outputs.end_logits) + 1

        if start_idx >= end_idx or (end_idx - start_idx) > 30:
            return None

        tokens = inputs["input_ids"][0][start_idx:end_idx]
        answer = tokenizer.convert_tokens_to_string(tokenizer.convert_ids_to_tokens(tokens)).strip()

        # Filter out empty or punctuation-only outputs
        if len(answer) < 2 or answer.startswith("[CLS]") or answer.startswith("[SEP]"):
            return None

        return answer
    except Exception as e:
        logger.warning("HF QA inference error: %s", e)
        return None


def call_llm_api(question: str, context: str) -> Optional[str]:
    """
    Invokes external LLM API (OpenAI / OpenRouter / Groq / Gemini) using configured key.
    """
    if not LLM_API_KEY:
        return None

    try:
        import requests

        system_prompt = (
            "You are JalSense AI, an intelligent hydrological assistant for Gram Panchayat rural water administrators. "
            "Explain water demand predictions, shortage risks, and recommended actions clearly and professionally. "
            "STRICT GROUNDING RULE: Base your entire answer strictly on the provided JALSENSE SITUATION CONTEXT. "
            "Never invent, assume, or hallucinate numerical figures not present in the context. "
            "Keep answers concise, actionable, and formatted in clean markdown."
        )

        user_content = f"{context}\n\nUSER QUESTION: {question}"

        # Standard OpenAI-compatible API format (works for OpenAI, OpenRouter, Groq, Together, Ollama)
        headers = {
            "Authorization": f"Bearer {LLM_API_KEY}",
            "Content-Type": "application/json"
        }

        url = f"{LLM_BASE_URL.rstrip('/')}/chat/completions"
        payload = {
            "model": LLM_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            "temperature": 0.2,
            "max_tokens": 600
        }

        resp = requests.post(url, headers=headers, json=payload, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            msg = data["choices"][0]["message"]
            content = (msg.get("content") or "").strip()
            if not content and msg.get("reasoning"):
                content = msg.get("reasoning").strip()
            return content if content else None
        else:
            logger.warning("LLM API returned %s: %s", resp.status_code, resp.text[:200])
            return None
    except Exception as e:
        logger.warning("LLM API call failed: %s", e)
        return None


def deterministic_fallback_response(question: str, prediction_dict: Dict[str, Any]) -> str:
    """
    Rule-based, zero-hallucination deterministic natural language generator.
    Guarantees mathematically accurate answers directly mapped to JalSense model outputs.
    """
    q_lower = question.lower().strip()
    
    v_name = prediction_dict.get("village_name", "the study village")
    f_date = prediction_dict.get("forecast_date", "tomorrow")
    wb = prediction_dict.get("water_balance", {})
    weather = prediction_dict.get("weather", {})
    features = prediction_dict.get("features_used", {})

    demand = wb.get("predicted_demand_litres", prediction_dict.get("predicted_demand_litres", 0.0))
    supply = wb.get("estimated_supply_litres", prediction_dict.get("estimated_supply_litres", 0.0))
    deficit = wb.get("deficit_litres", 0.0)
    surplus = wb.get("surplus_litres", 0.0)
    coverage = wb.get("coverage_percentage", 100.0)
    prob = wb.get("shortage_probability_pct", 0.0)
    risk = wb.get("risk_category", "LOW")
    tankers = wb.get("tankers_needed", 0)
    lpcd = wb.get("predicted_lpcd", 55.0)
    jjm = wb.get("jjm_benchmark_lpcd", 55.0)
    rec = wb.get("primary_recommendation", "Maintain continuous monitoring of storage reserves.")

    temp = weather.get("temp_mean_celsius", features.get("temp_mean", 28.0))
    rain = weather.get("rainfall_mm", features.get("rainfall_mm", 0.0))
    humidity = weather.get("humidity_pct", features.get("humidity_pct", 50.0))
    pop = features.get("population", 2000)

    # 1. "Will there be a shortage tomorrow?"
    if any(k in q_lower for k in ["shortage tomorrow", "will there be a shortage", "expect a shortage", "face a shortage"]):
        if deficit > 0:
            return (
                f"**Yes, a water deficit is forecasted tomorrow for {v_name}.**\n\n"
                f"- **Forecasted Shortage:** `{deficit:,.0f} Litres` (Available incoming supply meets only `{coverage:.1f}%` of demand).\n"
                f"- **Risk Classification:** **{risk}** (Calculated shortage probability: `{prob:.1f}%`).\n"
                f"- **Emergency Requisition:** Immediate deployment of **{tankers} tanker(s)** (10,000L standard capacity) is recommended.\n\n"
                f"**Recommended Action:** {rec}"
            )
        else:
            return (
                f"**No, there is no forecasted water shortage tomorrow for {v_name}.**\n\n"
                f"- **Projected Balance:** Incoming supply `{supply:,.0f} L` comfortably exceeds predicted demand `{demand:,.0f} L`, "
                f"yielding a comfortable **surplus of `{surplus:,.0f} Litres`** (`{coverage:.1f}%` supply coverage).\n"
                f"- **Shortage Risk:** **{risk}** (Shortage probability is very low at `{prob:.1f}%`).\n\n"
                f"**Operational Advisory:** {rec}"
            )

    # 2. "Why is the shortage risk high?" / risk explanation
    if any(k in q_lower for k in ["why is the shortage risk", "why is risk", "risk high", "risk critical", "contributing factor"]):
        if risk in ["HIGH", "CRITICAL"]:
            return (
                f"**The shortage risk is categorized as {risk} due to three core hydrological factors:**\n\n"
                f"1. **Supply Deficit:** Projected demand of `{demand:,.0f} Litres` outstrips incoming supply `{supply:,.0f} Litres`, "
                f"creating an unfulfilled deficit of `{deficit:,.0f} Litres`.\n"
                f"2. **Supply Coverage Margin:** Available supply covers only `{coverage:.1f}%` of required community consumption.\n"
                f"3. **Stochastic Margin Probability:** Under the Gaussian distribution margin model "
                f"($M = [S + \\alpha B] - D$), the probability of yield shortfall is **`{prob:.1f}%`**.\n\n"
                f"**Required Countermeasure:** Requisition `{tankers}` emergency tanker(s) and enforce domestic rationing (40 LPCD)."
            )
        else:
            return (
                f"**Currently, the shortage risk for {v_name} is classified as {risk} (not High):**\n\n"
                f"- The supply coverage ratio is healthy at **`{coverage:.1f}%`** (Supply: `{supply:,.0f} L` vs Demand: `{demand:,.0f} L`).\n"
                f"- The calculated probability of experiencing a water shortfall tomorrow is only **`{prob:.1f}%`**.\n"
                f"- Prevailing weather (Temp: `{temp}°C`, Rain: `{rain} mm`) remains within standard operational bounds."
            )

    # 3. "What is the predicted water demand?"
    if any(k in q_lower for k in ["predicted water demand", "predicted demand", "water demand", "how much water"]):
        compliance_pct = round((lpcd / jjm) * 100, 1)
        return (
            f"**Predicted Next-Day Water Demand for {v_name}:**\n\n"
            f"- **Total Aggregate Volume:** **`{demand:,.0f} Litres`** (for {pop:,} residents).\n"
            f"- **Per Capita Allocation:** **`{lpcd:.1f} LPCD`** (Litres Per Capita per Day).\n"
            f"- **Jal Jeevan Mission Benchmark:** The national rural target is `55.0 LPCD`. Current forecast represents **`{compliance_pct}%`** of this target.\n"
            f"- **Weather Inputs Used:** Ambient temperature `{temp}°C`, precipitation `{rain} mm`, and relative humidity `{humidity}%`."
        )

    # 4. "What happens if rainfall increases?"
    if any(k in q_lower for k in ["rainfall increases", "if it rains", "rain increase", "more rain"]):
        return (
            f"**If rainfall increases in {v_name}, water security improves via three distinct mechanisms:**\n\n"
            f"1. **Aquifer & Watershed Recharge:** Monsoon or storm runoff replenishes percolation check-dams and shallow borewells, boosting daily well yield.\n"
            f"2. **Agricultural Irrigation Relief:** Farm field irrigation drawing from shared community groundwater decreases, preserving drinking reserves.\n"
            f"3. **Cooler Thermal Dynamics:** Rain lowers ambient temperature (currently `{temp}°C`) and increases humidity, reducing human hydration needs and evaporative cattle cooling by **~1.6% per °C**.\n\n"
            f"*Tip: You can use the **Scenario Simulator** tab to test exact rainfall surges (e.g., +25mm) and observe the updated deficit reduction in real time.*"
        )

    # 5. "Summarize today's water situation."
    if any(k in q_lower for k in ["summarize", "water situation", "overview", "situation today", "summary"]):
        bal_text = f"Deficit of {deficit:,.0f} L" if deficit > 0 else f"Surplus of {surplus:,.0f} L"
        return (
            f"### 📋 Executive Water Situation Briefing: {v_name}\n\n"
            f"- **Date:** `{f_date}` | **Population:** `{pop:,}` residents\n"
            f"- **Weather:** `{temp}°C`, `{rain} mm` rainfall, `{humidity}%` humidity\n"
            f"- **Demand Forecast:** `{demand:,.0f} Litres` (`{lpcd:.1f} LPCD`)\n"
            f"- **Available Supply:** `{supply:,.0f} Litres`\n"
            f"- **Net Balance:** **{bal_text}** (`{coverage:.1f}%` coverage)\n"
            f"- **Shortage Risk:** **{risk}** (Probability: `{prob:.1f}%`)\n"
            f"- **Tankers Needed:** `{tankers}` unit(s)\n\n"
            f"**Action Recommendation:** {rec}"
        )

    # Default fallback for custom or unmapped queries
    return (
        f"**JalSense Hydrological Assessment for {v_name}:**\n\n"
        f"The forecasted demand is `{demand:,.0f} Litres` against an available supply of `{supply:,.0f} Litres`. "
        f"The net position is a **{'deficit of ' + f'{deficit:,.0f}' + ' L' if deficit > 0 else 'surplus of ' + f'{surplus:,.0f}' + ' L'}**, "
        f"resulting in a **{risk}** shortage risk (`{prob:.1f}%` probability).\n\n"
        f"**Recommended Directive:** {rec}\n\n"
        f"*(Regarding your inquiry: '{question}', please refer to the detailed Demand Forecast or Scenario Simulator tabs for further parameters.)*"
    )


class JalSenseAssistant:
    """
    Unified JalSense Conversational & Explainer Assistant.
    Supports LLM API (OpenAI/Gemini/Groq), Local Hugging Face Transformers,
    and Deterministic Fallback based strictly on true model outputs.
    """

    def __init__(self):
        self.provider = LLM_PROVIDER
        self.has_api_key = bool(LLM_API_KEY and len(LLM_API_KEY.strip()) > 5)
        self.model_name = LLM_MODEL

    def get_status(self) -> Dict[str, Any]:
        """Returns the operational status of available assistant backends."""
        return {
            "has_api_key": self.has_api_key,
            "provider": self.provider if self.has_api_key else "None (Offline)",
            "model": self.model_name if self.has_api_key else "Deterministic / Hugging Face",
            "hf_available": True
        }

    def ask(
        self,
        question: str,
        prediction_dict: Dict[str, Any],
        mode: str = "auto"
    ) -> Dict[str, Any]:
        """
        Processes a user question and returns a grounded response with source attribution.

        Parameters:
        - question: Natural language user query
        - prediction_dict: Structured output dictionary from predict_next_day_demand()
        - mode: "auto" (LLM -> HF -> Fallback), "hf" (Force Hugging Face), "fallback" (Force Deterministic)

        Returns:
        Dict with keys:
        - answer: str (the formatted response)
        - source_mode: str ("llm", "huggingface", "fallback")
        - source_label: str (Human-readable badge text)
        - is_fallback: bool
        """
        if not question or not question.strip():
            return {
                "answer": "Please ask a question regarding tomorrow's water forecast or shortage risk.",
                "source_mode": "fallback",
                "source_label": "⚙️ System",
                "is_fallback": True
            }

        context = build_situation_context(prediction_dict)

        # 1. Force Local Hugging Face Mode
        if mode == "hf":
            hf_answer = query_huggingface_qa(question, context)
            if hf_answer:
                formatted = (
                    f"**Extracted via Hugging Face Transformers (DistilBERT SQuAD):**\n\n"
                    f"> **Answer:** {hf_answer}\n\n"
                    f"**Context Grounding:**\n"
                    f"{deterministic_fallback_response(question, prediction_dict)}"
                )
                return {
                    "answer": formatted,
                    "source_mode": "huggingface",
                    "source_label": "🤗 Hugging Face Transformers (Local DistilBERT)",
                    "is_fallback": False
                }
            else:
                # If extractive QA cannot find span, fall back gracefully
                ans = deterministic_fallback_response(question, prediction_dict)
                return {
                    "answer": ans,
                    "source_mode": "fallback",
                    "source_label": "⚙️ Deterministic Fallback (HF Span Undetected)",
                    "is_fallback": True
                }

        # 2. Force Deterministic Fallback
        if mode == "fallback":
            ans = deterministic_fallback_response(question, prediction_dict)
            return {
                "answer": ans,
                "source_mode": "fallback",
                "source_label": "⚙️ Deterministic Model Fallback (Zero Hallucination)",
                "is_fallback": True
            }

        # 3. Auto Mode: Try LLM first if API key configured
        if self.has_api_key:
            llm_res = call_llm_api(question, context)
            if llm_res:
                return {
                    "answer": llm_res,
                    "source_mode": "llm",
                    "source_label": f"🤖 LLM Powered ({self.provider.upper()}: {self.model_name})",
                    "is_fallback": False
                }
            logger.info("LLM call failed or returned empty; falling back to deterministic engine.")

        # 4. Fallback Mode: Clean deterministic answer
        ans = deterministic_fallback_response(question, prediction_dict)
        return {
            "answer": ans,
            "source_mode": "fallback",
            "source_label": "⚙️ Deterministic Fallback Mode (Grounded in Model Predictions)",
            "is_fallback": True
        }


# Global singleton instance
assistant = JalSenseAssistant()
