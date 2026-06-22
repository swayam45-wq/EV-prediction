"""
Tests for the /api/recommend endpoint.

Uses httpx + FastAPI TestClient for integration testing of the
full recommendation pipeline. The `client` fixture is provided
by conftest.py and uses an in-memory SQLite test DB.
"""

import pytest


# ============================================================
# SAMPLE PAYLOADS
# ============================================================

VALID_PAYLOAD = {
    "current_soc": 35,
    "target_soc": 80,
    "battery_capacity_kwh": 75,
    "max_charge_rate_kw": 11,
    "battery_health_soh": 92,
    "departure_time": "08:00",
    "temperature_celsius": 28,
    "weather_condition": "clear",
    "electricity_prices": [
        {"hour": "00:00", "price": 0.12},
        {"hour": "01:00", "price": 0.10},
        {"hour": "02:00", "price": 0.08},
        {"hour": "03:00", "price": 0.07},
        {"hour": "04:00", "price": 0.08},
        {"hour": "05:00", "price": 0.10},
        {"hour": "06:00", "price": 0.15},
        {"hour": "07:00", "price": 0.22},
    ],
}


# ============================================================
# POST /api/recommend
# ============================================================

class TestRecommendEndpoint:
    """Integration tests for POST /api/recommend."""

    def test_successful_recommendation(self, client):
        """Valid input should return 200 with full recommendation."""
        response = client.post("/api/recommend", json=VALID_PAYLOAD)

        assert response.status_code == 200
        data = response.json()

        # Check top-level fields
        assert data["status"] == "optimal"
        assert data["start_charging"] is not None
        assert data["stop_charging"] is not None
        assert data["target_soc_reached"] is True
        assert data["total_energy_kwh"] > 0

        # Check schedule
        assert len(data["schedule"]) > 0
        for slot in data["schedule"]:
            assert "hour" in slot
            assert "price" in slot
            assert "energy_kwh" in slot
            assert "is_charging" in slot
            assert "cumulative_soc" in slot

        # Check cost analysis
        assert data["cost_analysis"] is not None
        cost = data["cost_analysis"]
        assert cost["optimized_cost"] > 0
        assert cost["normal_cost"] > 0
        assert cost["savings_percent"] >= 0

        # Check wear estimate
        assert data["wear_estimate"] is not None
        wear = data["wear_estimate"]
        assert 0 <= wear["total_score"] <= 100
        assert wear["rating"] in ("Low", "Medium", "High")

        # Check explanations
        assert len(data["explanations"]) > 0

        # Check battery health advice
        assert len(data["battery_health_advice"]) > 0

    def test_target_below_current(self, client):
        """Should return 400 if target SoC <= current SoC."""
        payload = {**VALID_PAYLOAD, "target_soc": 30}
        response = client.post("/api/recommend", json=payload)
        assert response.status_code == 400

    def test_invalid_soc_range(self, client):
        """Should return 422 for SoC values outside 0-100."""
        payload = {**VALID_PAYLOAD, "current_soc": 150}
        response = client.post("/api/recommend", json=payload)
        assert response.status_code == 422

    def test_missing_required_fields(self, client):
        """Should return 422 if required fields are missing."""
        response = client.post("/api/recommend", json={})
        assert response.status_code == 422

    def test_empty_prices(self, client):
        """Should return 422 for empty electricity prices."""
        payload = {**VALID_PAYLOAD, "electricity_prices": []}
        response = client.post("/api/recommend", json=payload)
        assert response.status_code == 422

    def test_high_temperature_warning(self, client):
        """High temperature should trigger degradation warnings."""
        payload = {**VALID_PAYLOAD, "temperature_celsius": 42}
        response = client.post("/api/recommend", json=payload)

        assert response.status_code == 200
        data = response.json()

        # Should have temperature-related advice
        all_text = " ".join(data["battery_health_advice"] + data["explanations"])
        assert "temperature" in all_text.lower() or "heat" in all_text.lower()

    def test_high_target_soc_warning(self, client):
        """Charging above 90% should trigger battery health warnings."""
        payload = {**VALID_PAYLOAD, "target_soc": 95}
        response = client.post("/api/recommend", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["wear_estimate"]["high_soc_stress"] > 0

    def test_savings_are_non_negative(self, client):
        """Optimized cost should not exceed naive cost."""
        response = client.post("/api/recommend", json=VALID_PAYLOAD)
        data = response.json()
        assert data["cost_analysis"]["savings_dollar"] >= 0


# ============================================================
# UTILITY ENDPOINTS
# ============================================================

class TestHealthEndpoints:
    """Test utility endpoints."""

    def test_root(self, client):
        """Root endpoint should return API info."""
        response = client.get("/")
        assert response.status_code == 200
        assert "endpoints" in response.json()

    def test_health(self, client):
        """Health check should return healthy status."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_battery_health_placeholder(self, client):
        """Battery health endpoint should return 200."""
        response = client.get("/api/battery-health")
        assert response.status_code == 200

    def test_analytics_placeholder(self, client):
        """Analytics endpoint should return 200."""
        response = client.get("/api/analytics")
        assert response.status_code == 200
