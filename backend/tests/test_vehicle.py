"""
Tests for the vehicle integration API endpoints (/api/vehicle/*).

Verifies response schemas, provider listing, connection start, 
mock callback token exchange, status query, and disconnect behavior.
"""

import pytest
from unittest.mock import AsyncMock, patch

# ============================================================
# API TESTS
# ============================================================

class TestVehicleEndpoints:
    """Integration tests for vehicle API router."""

    def test_get_providers(self, client):
        """Should return a list of providers and show 'demo' as active by default."""
        response = client.get("/api/vehicle/providers")
        assert response.status_code == 200
        data = response.json()
        assert "providers" in data
        assert len(data["providers"]) == 3
        
        provider_ids = [p["id"] for p in data["providers"]]
        assert "demo" in provider_ids
        assert "smartcar" in provider_ids
        assert "tesla" in provider_ids
        assert data["active_provider"] == "demo"

    def test_get_status_demo_default(self, client):
        """Should return simulated demo data by default."""
        response = client.get("/api/vehicle/status")
        assert response.status_code == 200
        data = response.json()
        
        assert data["source"] == "demo"
        assert data["connected"] is True
        assert data["vehicle_id"] == "DEMO-001"
        assert data["make"] == "VoltWise"
        assert data["battery_level_pct"] > 0
        assert data["battery_capacity_kwh"] == 75.0
        assert data["error"] is None

    def test_get_status_force_provider_demo(self, client):
        """Should return demo data when provider=demo is passed."""
        response = client.get("/api/vehicle/status?provider=demo")
        assert response.status_code == 200
        assert response.json()["source"] == "demo"

    def test_connect_smartcar_not_configured(self, client):
        """When SMARTCAR_CLIENT_ID is not configured, should return not_configured status."""
        from config import settings
        with patch.object(settings, "smartcar_client_id", None):
            response = client.get("/api/vehicle/connect")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "not_configured"
            assert "message" in data

    def test_connect_smartcar_ready(self, client):
        """When SMARTCAR_CLIENT_ID is configured, should return authorization URL."""
        from config import settings
        with patch.object(settings, "smartcar_client_id", "test-client-id"), \
             patch.object(settings, "smartcar_client_secret", "test-client-secret"), \
             patch.object(settings, "smartcar_redirect_uri", "http://localhost:5173/callback"):
            
            response = client.get("/api/vehicle/connect")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ready"
            assert "authorization_url" in data
            assert "test-client-id" in data["authorization_url"]

    @pytest.mark.anyio
    async def test_oauth_callback_success(self, client):
        """Should successfully exchange code, set token store, and return connected state."""
        from config import settings
        mock_tokens = {"access_token": "mock-access-token", "refresh_token": "mock-refresh-token"}
        mock_status = {
            "source": "smartcar",
            "connected": True,
            "make": "Tesla",
            "model": "Model Y",
            "battery_level_pct": 68.5,
        }

        # Mock the service methods called in callback
        with patch("api.routes.vehicle.exchange_smartcar_code", new_callable=AsyncMock) as mock_exchange, \
             patch("api.routes.vehicle.get_smartcar_vehicle_status", new_callable=AsyncMock) as mock_status_fetch, \
             patch.object(settings, "smartcar_redirect_uri", "http://localhost:5173/callback"):
            mock_exchange.return_value = mock_tokens
            mock_status_fetch.return_value = mock_status

            response = client.get("/api/vehicle/callback?code=test-code")
            assert response.status_code == 200
            data = response.json()
            
            assert data["status"] == "connected"
            assert data["provider"] == "smartcar"
            assert data["vehicle_summary"]["make"] == "Tesla"
            assert data["vehicle_summary"]["battery_level_pct"] == 68.5
            
            # Now querying status should return the smartcar provider since it's connected
            # Mock get_smartcar_vehicle_status for subsequent status call
            with patch("api.routes.vehicle.get_smartcar_vehicle_status", new_callable=AsyncMock) as mock_status_fetch2:
                mock_status_fetch2.return_value = {
                    "source": "smartcar",
                    "connected": True,
                    "make": "Tesla",
                    "model": "Model Y",
                    "battery_level_pct": 68.5,
                    "battery_capacity_kwh": 75.0,
                    "battery_health_soh": 98.0,
                    "is_plugged_in": True,
                }
                status_resp = client.get("/api/vehicle/status")
                assert status_resp.status_code == 200
                status_data = status_resp.json()
                assert status_data["source"] == "smartcar"
                assert status_data["make"] == "Tesla"
                assert status_data["battery_level_pct"] == 68.5

    def test_disconnect_vehicle(self, client):
        """Disconnect should reset the active provider back to demo."""
        # Disconnect vehicle
        response = client.delete("/api/vehicle/disconnect")
        assert response.status_code == 200
        assert response.json()["status"] == "disconnected"

        # Active provider should be demo again
        providers_resp = client.get("/api/vehicle/providers")
        assert providers_resp.status_code == 200
        assert providers_resp.json()["active_provider"] == "demo"
