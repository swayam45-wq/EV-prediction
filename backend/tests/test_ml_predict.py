"""
Tests for the ML battery wear score prediction module.

Covers:
    - ML model inference (when model is available)
    - Heuristic fallback (when model is missing)
    - Score bounds and rating logic
    - Feature edge cases
"""

import pytest
import os
import sys

# Make ml/ importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from ml.predict import (
    predict_wear_score,
    get_model_info,
    _score_to_rating,
    _build_recommendations,
)


# ============================================================
# SCORE BOUNDS & RATING
# ============================================================

class TestScoreLogic:
    """Test score rating bucketing."""

    def test_low_rating_threshold(self):
        assert _score_to_rating(0.0)  == "Low"
        assert _score_to_rating(10.0) == "Low"
        assert _score_to_rating(19.9) == "Low"

    def test_medium_rating_threshold(self):
        assert _score_to_rating(20.0) == "Medium"
        assert _score_to_rating(30.0) == "Medium"
        assert _score_to_rating(44.9) == "Medium"

    def test_high_rating_threshold(self):
        assert _score_to_rating(45.0) == "High"
        assert _score_to_rating(80.0) == "High"
        assert _score_to_rating(100.0) == "High"


# ============================================================
# RECOMMENDATION MESSAGES
# ============================================================

class TestRecommendations:
    """Test recommendation generation."""

    def test_hot_temp_recommendation(self):
        recs = _build_recommendations(temp_c=42, target_soc_pct=70, c_rate=0.2)
        combined = " ".join(recs).lower()
        assert "temperature" in combined or "nighttime" in combined

    def test_cold_temp_recommendation(self):
        recs = _build_recommendations(temp_c=-5, target_soc_pct=70, c_rate=0.2)
        combined = " ".join(recs).lower()
        assert "cold" in combined or "pre-condition" in combined

    def test_high_soc_recommendation(self):
        recs = _build_recommendations(temp_c=20, target_soc_pct=95, c_rate=0.2)
        combined = " ".join(recs).lower()
        assert "90%" in combined or "aging" in combined or "80%" in combined

    def test_high_crate_recommendation(self):
        recs = _build_recommendations(temp_c=20, target_soc_pct=70, c_rate=2.5)
        combined = " ".join(recs).lower()
        assert "c-rate" in combined or "level 2" in combined

    def test_optimal_conditions_generic_advice(self):
        recs = _build_recommendations(temp_c=20, target_soc_pct=75, c_rate=0.2)
        combined = " ".join(recs).lower()
        assert "optimal" in combined


# ============================================================
# PREDICT FUNCTION (end-to-end)
# ============================================================

class TestPredictWearScore:
    """Test the predict_wear_score function end-to-end."""

    def _call(self, **kwargs):
        defaults = dict(
            battery_soc_pct=35.0,
            target_soc_pct=80.0,
            ambient_temp_c=22.0,
            battery_temp_c=27.0,
            charge_rate_kw=11.0,
            battery_capacity_kwh=75.0,
            cycle_count=100,
            battery_health_soh=95.0,
        )
        defaults.update(kwargs)
        return predict_wear_score(**defaults)

    def test_returns_required_keys(self):
        result = self._call()
        assert "total_score" in result
        assert "rating" in result
        assert "recommendations" in result
        assert "source" in result

    def test_score_in_valid_range(self):
        result = self._call()
        assert 0 <= result["total_score"] <= 100

    def test_rating_is_valid(self):
        result = self._call()
        assert result["rating"] in ("Low", "Medium", "High")

    def test_hot_temp_higher_score(self):
        """40C should produce higher wear than 20C."""
        cool = self._call(ambient_temp_c=20, battery_temp_c=25)
        hot  = self._call(ambient_temp_c=40, battery_temp_c=45)
        assert hot["total_score"] > cool["total_score"]

    def test_high_soc_higher_score(self):
        """Charging to 100% should be worse than to 70%."""
        low_soc  = self._call(target_soc_pct=70)
        high_soc = self._call(target_soc_pct=100)
        assert high_soc["total_score"] > low_soc["total_score"]

    def test_fast_charging_higher_score(self):
        """150kW DCFC should produce higher wear than 7kW L2."""
        slow = self._call(charge_rate_kw=7.0,   battery_capacity_kwh=75)
        fast = self._call(charge_rate_kw=150.0,  battery_capacity_kwh=75)
        assert fast["total_score"] > slow["total_score"]

    def test_recommendations_is_list(self):
        result = self._call()
        assert isinstance(result["recommendations"], list)
        assert len(result["recommendations"]) > 0

    def test_source_field_present(self):
        """Source should be either ml_model or heuristic."""
        result = self._call()
        assert result["source"] in ("ml_model", "heuristic")


# ============================================================
# MODEL INFO
# ============================================================

class TestModelInfo:
    """Test get_model_info returns useful metadata."""

    def test_returns_dict(self):
        info = get_model_info()
        assert isinstance(info, dict)
        assert "status" in info
        assert "model_type" in info

    def test_status_is_valid(self):
        info = get_model_info()
        assert info["status"] in ("ml_model_active", "heuristic_fallback")
