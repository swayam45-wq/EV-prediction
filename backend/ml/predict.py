"""
ML Model Inference — Battery Wear Score Predictor.

Loads the trained XGBoost model and provides a predict() function
that the API layer calls as a drop-in replacement for the old
heuristic calculate_wear_score().

Falls back to the heuristic model if the ML model is not found
(e.g., first run before training).
"""

import os
import json
import logging
from typing import Optional
import numpy as np

logger = logging.getLogger(__name__)

# ── Paths ────────────────────────────────────────────────────
_BASE_DIR    = os.path.dirname(__file__)
_MODEL_PATH  = os.path.join(_BASE_DIR, "models", "wear_score_model.joblib")
_SCALER_PATH = os.path.join(_BASE_DIR, "models", "wear_score_scaler.joblib")
_META_PATH   = os.path.join(_BASE_DIR, "models", "model_metadata.json")

# ── Lazy-loaded singletons ───────────────────────────────────
_model  = None
_scaler = None
_meta   = None
_ml_available = False


def _load_artifacts() -> bool:
    """Load model artifacts once on first call. Returns True if successful."""
    global _model, _scaler, _meta, _ml_available

    if _ml_available:
        return True

    if not os.path.exists(_MODEL_PATH) or not os.path.exists(_SCALER_PATH):
        logger.warning(
            "ML model not found at %s — falling back to heuristic model. "
            "Run 'python backend/ml/train.py' to train the ML model.",
            _MODEL_PATH,
        )
        return False

    try:
        import joblib
        _model  = joblib.load(_MODEL_PATH)
        _scaler = joblib.load(_SCALER_PATH)

        if os.path.exists(_META_PATH):
            with open(_META_PATH) as f:
                _meta = json.load(f)

        _ml_available = True
        logger.info(
            "ML model loaded: %s (RMSE=%.3f, R²=%.4f)",
            _meta.get("model_type", "unknown") if _meta else "unknown",
            _meta["metrics"]["test"]["rmse"] if _meta else 0,
            _meta["metrics"]["test"]["r2"]   if _meta else 0,
        )
        return True

    except Exception as e:
        logger.error("Failed to load ML model: %s", e)
        return False


def predict_wear_score(
    battery_soc_pct: float,
    target_soc_pct: float,
    ambient_temp_c: float,
    battery_temp_c: float,
    charge_rate_kw: float,
    battery_capacity_kwh: float,
    cycle_count: int = 0,
    battery_health_soh: float = 100.0,
) -> dict:
    """
    Predict battery wear score using ML model (or heuristic fallback).

    Args:
        battery_soc_pct        : Current SoC (%)
        target_soc_pct         : Target SoC after charging (%)
        ambient_temp_c         : Ambient temperature (°C)
        battery_temp_c         : Battery temperature (°C); defaults to ambient+5
        charge_rate_kw         : Charging rate (kW)
        battery_capacity_kwh   : Total battery capacity (kWh)
        cycle_count            : Total charge cycles so far
        battery_health_soh     : State of Health (%)

    Returns:
        dict with keys: total_score, rating, source, recommendations
    """
    ml_ready = _load_artifacts()

    if ml_ready:
        return _predict_ml(
            battery_soc_pct, target_soc_pct,
            ambient_temp_c, battery_temp_c,
            charge_rate_kw, battery_capacity_kwh,
            cycle_count, battery_health_soh,
        )
    else:
        return _predict_heuristic(
            ambient_temp_c, target_soc_pct,
            charge_rate_kw, battery_capacity_kwh,
        )


def _predict_ml(
    battery_soc_pct, target_soc_pct,
    ambient_temp_c, battery_temp_c,
    charge_rate_kw, battery_capacity_kwh,
    cycle_count, battery_health_soh,
) -> dict:
    """Run inference through the trained XGBoost model."""
    c_rate    = charge_rate_kw / battery_capacity_kwh if battery_capacity_kwh > 0 else 0
    soc_delta = target_soc_pct - battery_soc_pct

    features = np.array([[
        battery_soc_pct,
        target_soc_pct,
        ambient_temp_c,
        battery_temp_c,
        charge_rate_kw,
        battery_capacity_kwh,
        cycle_count,
        battery_health_soh,
        c_rate,
        soc_delta,
    ]])

    features_scaled = _scaler.transform(features)
    raw_score = float(_model.predict(features_scaled)[0])
    total_score = round(float(np.clip(raw_score, 0, 100)), 1)

    rating = _score_to_rating(total_score)
    recommendations = _build_recommendations(
        ambient_temp_c, target_soc_pct, c_rate
    )

    return {
        "total_score":           total_score,
        "rating":                rating,
        "source":                "ml_model",
        "model_type":            _meta.get("model_type") if _meta else "XGBoost",
        "recommendations":       recommendations,
        # ML model doesn't split into sub-components, but we approximate them
        "temperature_impact":    round(float(np.clip(raw_score * 0.40, 0, 40)), 1),
        "high_soc_stress":       round(float(np.clip(raw_score * 0.35, 0, 35)), 1),
        "fast_charging_penalty": round(float(np.clip(raw_score * 0.25, 0, 25)), 1),
    }


def _predict_heuristic(
    ambient_temp_c, target_soc_pct,
    charge_rate_kw, battery_capacity_kwh,
) -> dict:
    """
    Fallback to the rule-based heuristic from battery_degradation.py.
    Preserves backward compatibility when model isn't trained yet.
    """
    from services.battery_degradation import calculate_wear_score
    result = calculate_wear_score(
        temperature_celsius=ambient_temp_c,
        target_soc_pct=target_soc_pct,
        avg_charging_rate_kw=charge_rate_kw,
        battery_capacity_kwh=battery_capacity_kwh,
    )
    result["source"] = "heuristic"
    result["model_type"] = "rule_based"
    return result


def get_model_info() -> dict:
    """Return metadata about the currently loaded model."""
    _load_artifacts()
    if _ml_available and _meta:
        return {
            "status":      "ml_model_active",
            "model_type":  _meta.get("model_type"),
            "metrics":     _meta.get("metrics"),
            "n_features":  len(_meta.get("feature_columns", [])),
            "features":    _meta.get("feature_columns"),
        }
    return {
        "status":     "heuristic_fallback",
        "model_type": "rule_based",
        "message":    "Run 'python backend/ml/train.py' to activate the ML model.",
    }


# ── Helpers ──────────────────────────────────────────────────

def _score_to_rating(score: float) -> str:
    if score < 20:
        return "Low"
    elif score < 45:
        return "Medium"
    return "High"


def _build_recommendations(
    temp_c: float,
    target_soc_pct: float,
    c_rate: float,
) -> list[str]:
    recs = []
    if temp_c > 35:
        recs.append(
            f"🌡️ Temperature ({temp_c:.0f}°C) may accelerate degradation. "
            "Prefer nighttime charging."
        )
    elif temp_c < 5:
        recs.append(
            f"❄️ Cold temperature ({temp_c:.0f}°C) — pre-condition battery before charging."
        )
    if target_soc_pct > 90:
        recs.append(
            "⚠️ Charging above 90% significantly accelerates aging. "
            "Use 80% for daily driving."
        )
    elif target_soc_pct > 80:
        recs.append("📊 Limit daily charging to 80% to extend battery lifespan.")
    if c_rate > 1.0:
        recs.append(
            f"⚡ High C-rate ({c_rate:.2f}C). Use Level 2 AC charging when possible."
        )
    if not recs:
        recs.append("✅ Charging conditions are optimal for battery longevity.")
    recs.append("💡 Overnight slow charging is best for long-term battery health.")
    return recs
