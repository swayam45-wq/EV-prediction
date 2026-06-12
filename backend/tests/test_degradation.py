"""
Tests for the Battery Degradation Scoring Model.
"""

import pytest
from services.battery_degradation import calculate_wear_score, compare_wear_scenarios


class TestWearScore:
    """Test individual wear score calculations."""

    def test_optimal_conditions_low_score(self):
        """Optimal temp + 80% SoC + slow charge → low wear score."""
        result = calculate_wear_score(
            temperature_celsius=22.0,
            target_soc_pct=80.0,
            avg_charging_rate_kw=7.0,
            battery_capacity_kwh=75.0,
        )
        assert result["total_score"] < 20
        assert result["rating"] == "Low"

    def test_high_temperature_increases_score(self):
        """Extreme heat should significantly increase wear score."""
        cool = calculate_wear_score(22.0, 80.0, 7.0, 75.0)
        hot = calculate_wear_score(42.0, 80.0, 7.0, 75.0)
        assert hot["temperature_impact"] > cool["temperature_impact"]
        assert hot["total_score"] > cool["total_score"]

    def test_high_soc_increases_score(self):
        """Charging to 100% should score higher than 80%."""
        soc_80 = calculate_wear_score(22.0, 80.0, 7.0, 75.0)
        soc_100 = calculate_wear_score(22.0, 100.0, 7.0, 75.0)
        assert soc_100["high_soc_stress"] > soc_80["high_soc_stress"]
        assert soc_100["total_score"] > soc_80["total_score"]

    def test_fast_charging_increases_score(self):
        """High C-rate charging should increase wear score."""
        slow = calculate_wear_score(22.0, 80.0, 7.0, 75.0)    # ~0.09C
        fast = calculate_wear_score(22.0, 80.0, 150.0, 75.0)   # 2.0C
        assert fast["fast_charging_penalty"] > slow["fast_charging_penalty"]

    def test_score_capped_at_100(self):
        """Total score should never exceed 100."""
        result = calculate_wear_score(
            temperature_celsius=50.0,
            target_soc_pct=100.0,
            avg_charging_rate_kw=200.0,
            battery_capacity_kwh=50.0,
        )
        assert result["total_score"] <= 100.0

    def test_cold_temperature_penalty(self):
        """Sub-zero temps should trigger cold weather penalty."""
        result = calculate_wear_score(-10.0, 80.0, 7.0, 75.0)
        assert result["temperature_impact"] > 0

    def test_recommendations_generated(self):
        """Should always return at least one recommendation."""
        result = calculate_wear_score(22.0, 80.0, 7.0, 75.0)
        assert len(result["recommendations"]) > 0


class TestWearComparison:
    """Test 80% vs 100% comparison utility."""

    def test_80_vs_100_comparison(self):
        """Charging to 100% should always score worse than 80%."""
        comparison = compare_wear_scenarios(
            temperature_celsius=25.0,
            avg_charging_rate_kw=7.0,
            battery_capacity_kwh=75.0,
        )
        assert comparison["charge_to_100"]["wear_score"] > comparison["charge_to_80"]["wear_score"]
        assert comparison["score_difference"] > 0
        assert "80%" in comparison["recommendation"]
