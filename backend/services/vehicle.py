"""
Vehicle Data Service — Phase 4b.

Fetches real-time battery and charge state from the vehicle
using one of two providers:

  1. Smartcar API  — universal, works for 30+ brands
                     (Tesla, Ford, BMW, VW, Rivian, GM...)
                     Requires SMARTCAR_CLIENT_ID + SMARTCAR_CLIENT_SECRET
                     OAuth flow: /api/vehicle/connect → callback → token stored

  2. Tesla Fleet API — direct Tesla integration
                       Requires TESLA_CLIENT_ID + TESLA_CLIENT_SECRET

  3. Demo mode       — simulates a 75kWh EV, no credentials needed

The frontend calls GET /api/vehicle/status which returns a
VehicleStatus object that the Optimizer form auto-fills.
"""

import httpx
import logging
from typing import Optional
from datetime import datetime, timezone

from config import settings

logger = logging.getLogger(__name__)

# ── Smartcar API constants ────────────────────────────────────
SMARTCAR_BASE     = "https://api.smartcar.com/v2.0"
SMARTCAR_AUTH_URL = "https://connect.smartcar.com/oauth/authorize"
SMARTCAR_TOKEN_URL= "https://auth.smartcar.com/oauth/token"

# ── Tesla Fleet API constants ─────────────────────────────────
TESLA_BASE        = "https://fleet-api.prd.na.vn.cloud.tesla.com/api/1"
TESLA_AUTH_URL    = "https://auth.tesla.com/oauth2/v3/authorize"
TESLA_TOKEN_URL   = "https://auth.tesla.com/oauth2/v3/token"


# ════════════════════════════════════════════════════════════
# DATA MODEL — returned by all providers
# ════════════════════════════════════════════════════════════

def _vehicle_status(
    *,
    source: str,
    connected: bool,
    vehicle_id: Optional[str] = None,
    make: Optional[str] = None,
    model: Optional[str] = None,
    year: Optional[int] = None,
    # Battery
    battery_level_pct: Optional[float] = None,
    battery_range_km: Optional[float] = None,
    battery_capacity_kwh: Optional[float] = None,
    # Charge state
    is_plugged_in: Optional[bool] = None,
    charge_state: Optional[str] = None,   # CHARGING | FULLY_CHARGED | NOT_CHARGING
    charge_rate_kw: Optional[float] = None,
    minutes_to_full: Optional[int] = None,
    # Health
    battery_health_soh: Optional[float] = None,
    # Misc
    error: Optional[str] = None,
    fetched_at: Optional[str] = None,
) -> dict:
    return {
        "source":               source,
        "connected":            connected,
        "vehicle_id":           vehicle_id,
        "make":                 make,
        "model":                model,
        "year":                 year,
        "battery_level_pct":    battery_level_pct,
        "battery_range_km":     battery_range_km,
        "battery_capacity_kwh": battery_capacity_kwh,
        "is_plugged_in":        is_plugged_in,
        "charge_state":         charge_state,
        "charge_rate_kw":       charge_rate_kw,
        "minutes_to_full":      minutes_to_full,
        "battery_health_soh":   battery_health_soh,
        "error":                error,
        "fetched_at":           fetched_at or datetime.now(timezone.utc).isoformat(),
    }


# ════════════════════════════════════════════════════════════
# DEMO MODE — no credentials required
# ════════════════════════════════════════════════════════════

def get_demo_vehicle_status() -> dict:
    """
    Return a simulated EV status for development and demo purposes.
    Values vary slightly based on time-of-day to feel realistic.
    """
    from datetime import datetime, timezone
    import math

    now   = datetime.now(timezone.utc)
    hour  = now.hour
    # Simulate SoC dropping through the day (full at midnight, 60% by 6 PM)
    soc   = round(85 - 25 * math.sin(hour / 24 * math.pi), 1)
    soc   = max(15.0, min(92.0, soc))
    cap   = 75.0
    range_km = round(soc / 100 * cap * 6.2, 0)   # ~6.2 km/kWh efficiency

    return _vehicle_status(
        source="demo",
        connected=True,
        vehicle_id="DEMO-001",
        make="ChargeMind",
        model="EV Demo · 75 kWh",
        year=2024,
        battery_level_pct=soc,
        battery_range_km=range_km,
        battery_capacity_kwh=cap,
        is_plugged_in=True,
        charge_state="NOT_CHARGING",
        charge_rate_kw=0.0,
        minutes_to_full=None,
        battery_health_soh=94.0,
    )


# ════════════════════════════════════════════════════════════
# SMARTCAR PROVIDER
# ════════════════════════════════════════════════════════════

def get_smartcar_auth_url(redirect_uri: str, state: str = "") -> str:
    """
    Build the OAuth 2.0 authorization URL for Smartcar Connect.

    The user visits this URL, selects their car brand, logs in,
    and grants permission. Smartcar redirects back to redirect_uri
    with a ?code= parameter which you exchange for an access token.
    """
    from urllib.parse import urlencode
    params = {
        "response_type": "code",
        "client_id":     settings.smartcar_client_id or "",
        "redirect_uri":  redirect_uri,
        "scope":         "read_battery read_charge read_vehicle_info read_odometer",
        "mode":          "test",   # Change to "live" for real vehicles
        "state":         state,
    }
    return f"{SMARTCAR_AUTH_URL}?{urlencode(params)}"


async def exchange_smartcar_code(code: str, redirect_uri: str) -> Optional[dict]:
    """Exchange authorization code for access + refresh tokens."""
    client_id     = settings.smartcar_client_id
    client_secret = settings.smartcar_client_secret
    if not client_id or not client_secret:
        logger.warning("Smartcar credentials not configured")
        return None
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                SMARTCAR_TOKEN_URL,
                data={
                    "grant_type":   "authorization_code",
                    "code":         code,
                    "redirect_uri": redirect_uri,
                },
                auth=(client_id, client_secret),
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as e:
        logger.error(f"Smartcar token exchange failed: {e}")
        return None


async def get_smartcar_vehicle_status(access_token: str) -> dict:
    """
    Fetch real vehicle data from Smartcar using an access token.

    Calls 3 endpoints in parallel:
      - /vehicles  → list vehicles → pick first
      - /battery   → SoC + range
      - /charge    → plug state + charge rate
    """
    headers = {"Authorization": f"Bearer {access_token}"}

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # 1. Get vehicle list
            vresp = await client.get(f"{SMARTCAR_BASE}/vehicles", headers=headers)
            vresp.raise_for_status()
            vehicles = vresp.json().get("vehicles", [])
            if not vehicles:
                return _vehicle_status(source="smartcar", connected=False,
                                       error="No vehicles linked to this account")

            vid = vehicles[0]  # Use first vehicle

            # 2. Vehicle info
            info_resp, bat_resp, chg_resp, cap_resp = await _parallel_get(
                client, headers, vid,
                ["", "/battery", "/charge", "/battery/capacity"]
            )

        info  = info_resp.json()   if info_resp  else {}
        bat   = bat_resp.json()    if bat_resp   else {}
        chg   = chg_resp.json()    if chg_resp   else {}
        cap   = cap_resp.json()    if cap_resp   else {}

        soc_pct   = round((bat.get("percentRemaining") or 0) * 100, 1)
        range_km  = _extract_value(bat, "range", unit="km")
        cap_kwh   = _extract_value(cap, "capacity", unit="kWh")
        plug      = chg.get("isPluggedIn", False)
        state     = chg.get("state", "UNKNOWN")
        rate_kw   = _extract_value(chg, "chargeRate", unit="kW")

        return _vehicle_status(
            source="smartcar",
            connected=True,
            vehicle_id=vid,
            make=info.get("make"),
            model=info.get("model"),
            year=info.get("year"),
            battery_level_pct=soc_pct,
            battery_range_km=range_km,
            battery_capacity_kwh=cap_kwh,
            is_plugged_in=plug,
            charge_state=state,
            charge_rate_kw=rate_kw,
            battery_health_soh=None,  # Smartcar doesn't expose SoH directly
        )

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            return _vehicle_status(source="smartcar", connected=False,
                                   error="Access token expired — please reconnect")
        return _vehicle_status(source="smartcar", connected=False,
                               error=f"HTTP {e.response.status_code}")
    except Exception as e:
        logger.error(f"Smartcar fetch error: {e}")
        return _vehicle_status(source="smartcar", connected=False, error=str(e))


async def _parallel_get(client, headers, vid, paths):
    """Fire multiple GET requests to Smartcar vehicle endpoints."""
    import asyncio
    async def _get(path):
        try:
            r = await client.get(f"{SMARTCAR_BASE}/vehicles/{vid}{path}", headers=headers)
            r.raise_for_status()
            return r
        except Exception:
            return None
    return await asyncio.gather(*[_get(p) for p in paths])


def _extract_value(data: dict, key: str, unit: str = "") -> Optional[float]:
    """Safely extract a nested value object from Smartcar response."""
    val = data.get(key, {})
    if isinstance(val, dict):
        return val.get("value")
    return val if isinstance(val, (int, float)) else None


# ════════════════════════════════════════════════════════════
# TESLA FLEET API PROVIDER
# ════════════════════════════════════════════════════════════

async def get_tesla_vehicle_status(access_token: str, vehicle_id: str) -> dict:
    """
    Fetch real vehicle data from Tesla Fleet API.

    Requires a valid Tesla access token obtained via Tesla's
    OAuth 2.0 flow (TESLA_CLIENT_ID + TESLA_CLIENT_SECRET).
    """
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type":  "application/json",
    }
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            # Wake up the vehicle first (Tesla sleeps when idle)
            await client.post(
                f"{TESLA_BASE}/vehicles/{vehicle_id}/wake_up",
                headers=headers,
            )
            # Fetch charge state
            resp = await client.get(
                f"{TESLA_BASE}/vehicles/{vehicle_id}/vehicle_data"
                "?endpoints=charge_state%7Cvehicle_state",
                headers=headers,
            )
            resp.raise_for_status()
            data = resp.json().get("response", {})

        charge = data.get("charge_state", {})
        vstate = data.get("vehicle_state", {})

        soc       = charge.get("battery_level")
        range_mi  = charge.get("est_battery_range") or charge.get("battery_range")
        range_km  = round(range_mi * 1.609, 1) if range_mi else None
        plugged   = charge.get("charging_state") not in ("Disconnected", None)
        state_raw = charge.get("charging_state", "Disconnected")
        state_map = {
            "Charging":     "CHARGING",
            "Complete":     "FULLY_CHARGED",
            "Disconnected": "NOT_CHARGING",
            "Stopped":      "NOT_CHARGING",
        }
        state     = state_map.get(state_raw, state_raw.upper())
        rate_kw   = charge.get("charger_power")            # kW
        mins_full = charge.get("time_to_full_charge")      # hours → convert
        if mins_full:
            mins_full = int(mins_full * 60)

        return _vehicle_status(
            source="tesla",
            connected=True,
            vehicle_id=str(vehicle_id),
            make="Tesla",
            model=vstate.get("vehicle_name", "Tesla"),
            year=None,
            battery_level_pct=float(soc) if soc is not None else None,
            battery_range_km=range_km,
            battery_capacity_kwh=None,  # Not exposed in Fleet API directly
            is_plugged_in=plugged,
            charge_state=state,
            charge_rate_kw=float(rate_kw) if rate_kw else None,
            minutes_to_full=mins_full,
            battery_health_soh=None,
        )

    except httpx.HTTPStatusError as e:
        code = e.response.status_code
        if code == 408:
            return _vehicle_status(source="tesla", connected=False,
                                   error="Vehicle asleep and not responding. Try again in 30s.")
        return _vehicle_status(source="tesla", connected=False,
                               error=f"Tesla API error {code}")
    except Exception as e:
        logger.error(f"Tesla fetch error: {e}")
        return _vehicle_status(source="tesla", connected=False, error=str(e))
