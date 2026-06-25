"""
Vehicle API routes — Phase 4b.

Endpoints:
    GET  /api/vehicle/status          → Current vehicle battery status
                                        (demo | smartcar | tesla)
    GET  /api/vehicle/connect         → Returns Smartcar OAuth URL
    GET  /api/vehicle/callback        → Handles OAuth code exchange
    DELETE /api/vehicle/disconnect    → Clears stored token
    GET  /api/vehicle/providers       → Lists supported providers

Token storage: in-memory for now (single-user dev mode).
Production: use Redis or a user-linked DB table.
"""

from fastapi import APIRouter, Query, HTTPException
from typing import Optional

from services.vehicle import (
    get_demo_vehicle_status,
    get_smartcar_vehicle_status,
    get_tesla_vehicle_status,
    get_smartcar_auth_url,
    exchange_smartcar_code,
)
from config import settings

router = APIRouter(prefix="/api/vehicle", tags=["Vehicle"])

# ── In-memory token store (single-user dev) ───────────────────
_token_store: dict = {
    "provider":      None,   # "smartcar" | "tesla" | "demo"
    "access_token":  None,
    "vehicle_id":    None,
}


# ═══════════════════════════════════════════════════════════════
# GET /api/vehicle/status
# ═══════════════════════════════════════════════════════════════

@router.get("/status")
async def vehicle_status(
    provider: Optional[str] = Query(
        default=None,
        description="Force provider: 'demo' | 'smartcar' | 'tesla'. "
                    "Defaults to the connected provider or 'demo'.",
    )
):
    """
    Return current vehicle battery and charge state.

    If a vehicle has been connected via OAuth, uses live data.
    Otherwise returns demo data so the frontend always has something
    to auto-fill.

    Response fields map directly to the Optimizer form inputs:
      - battery_level_pct   → current_soc
      - battery_capacity_kwh → battery_capacity_kwh
      - battery_health_soh  → battery_health_soh
    """
    effective_provider = provider or _token_store.get("provider") or "demo"

    if effective_provider == "demo":
        return get_demo_vehicle_status()

    if effective_provider == "smartcar":
        token = _token_store.get("access_token")
        if not token:
            raise HTTPException(
                status_code=401,
                detail="No Smartcar token found. Visit /api/vehicle/connect first.",
            )
        return await get_smartcar_vehicle_status(token)

    if effective_provider == "tesla":
        token    = _token_store.get("access_token")
        vid      = _token_store.get("vehicle_id")
        if not token or not vid:
            raise HTTPException(
                status_code=401,
                detail="No Tesla token found. Configure TESLA_CLIENT_ID and connect.",
            )
        return await get_tesla_vehicle_status(token, vid)

    raise HTTPException(status_code=400, detail=f"Unknown provider: {effective_provider}")


# ═══════════════════════════════════════════════════════════════
# GET /api/vehicle/connect  — Start Smartcar OAuth
# ═══════════════════════════════════════════════════════════════

@router.get("/connect")
async def connect_vehicle():
    """
    Start the Smartcar OAuth 2.0 flow.

    Returns an authorization_url the user should open in their browser.
    After they grant permission, Smartcar redirects to /api/vehicle/callback
    which exchanges the code for an access token automatically.

    Requires SMARTCAR_CLIENT_ID and SMARTCAR_CLIENT_SECRET in .env
    """
    if not settings.smartcar_client_id:
        return {
            "status":   "not_configured",
            "message":  "Smartcar credentials not set. Add SMARTCAR_CLIENT_ID and "
                        "SMARTCAR_CLIENT_SECRET to your .env file.",
            "docs_url": "https://developer.smartcar.com",
            "demo_url": "/api/vehicle/status?provider=demo",
        }

    auth_url = get_smartcar_auth_url(
        redirect_uri=settings.smartcar_redirect_uri,
        state="ev-optimizer",
    )
    return {
        "status":            "ready",
        "authorization_url": auth_url,
        "instructions":      "Open the authorization_url in your browser to connect your car.",
        "redirect_uri":      settings.smartcar_redirect_uri,
    }


# ═══════════════════════════════════════════════════════════════
# GET /api/vehicle/callback  — OAuth callback
# ═══════════════════════════════════════════════════════════════

@router.get("/callback")
async def vehicle_oauth_callback(
    code:  Optional[str]  = Query(default=None),
    error: Optional[str]  = Query(default=None),
    state: Optional[str]  = Query(default=None),
):
    """
    OAuth callback endpoint — Smartcar redirects here after user grants permission.
    Exchanges the authorization code for tokens and stores them in memory.
    """
    if error:
        raise HTTPException(status_code=400, detail=f"OAuth error: {error}")

    if not code:
        raise HTTPException(status_code=400, detail="Missing authorization code")

    tokens = await exchange_smartcar_code(
        code=code,
        redirect_uri=settings.smartcar_redirect_uri,
    )

    if not tokens:
        raise HTTPException(
            status_code=502,
            detail="Failed to exchange code for token. Check Smartcar credentials.",
        )

    _token_store["provider"]     = "smartcar"
    _token_store["access_token"] = tokens.get("access_token")

    # Fetch and return vehicle status to confirm connection
    status = await get_smartcar_vehicle_status(_token_store["access_token"])

    return {
        "status":          "connected",
        "provider":        "smartcar",
        "vehicle_summary": {
            "make":               status.get("make"),
            "model":              status.get("model"),
            "battery_level_pct":  status.get("battery_level_pct"),
        },
        "message": "Vehicle connected! The Optimizer will now auto-fill your battery data.",
    }


# ═══════════════════════════════════════════════════════════════
# DELETE /api/vehicle/disconnect
# ═══════════════════════════════════════════════════════════════

@router.delete("/disconnect")
async def disconnect_vehicle():
    """Clear stored OAuth token and revert to demo mode."""
    _token_store["provider"]     = None
    _token_store["access_token"] = None
    _token_store["vehicle_id"]   = None
    return {"status": "disconnected", "message": "Vehicle disconnected. Demo mode active."}


# ═══════════════════════════════════════════════════════════════
# GET /api/vehicle/providers
# ═══════════════════════════════════════════════════════════════

@router.get("/providers")
async def list_providers():
    """List supported vehicle data providers and their configuration status."""
    return {
        "providers": [
            {
                "id":           "demo",
                "name":         "Demo Mode",
                "description":  "Simulated 75 kWh EV — no credentials required",
                "configured":   True,
                "brands":       ["ChargeMind Demo EV"],
                "docs":         None,
            },
            {
                "id":           "smartcar",
                "name":         "Smartcar",
                "description":  "Universal API — works with 30+ EV brands",
                "configured":   bool(settings.smartcar_client_id),
                "brands":       [
                    "Tesla", "Ford", "BMW", "Chevrolet", "Volkswagen",
                    "Rivian", "Hyundai", "Kia", "Volvo", "Audi", "Mercedes",
                    "Jeep", "Lincoln", "Cadillac", "+ 20 more",
                ],
                "docs":         "https://developer.smartcar.com",
                "connect_url":  "/api/vehicle/connect",
            },
            {
                "id":           "tesla",
                "name":         "Tesla Fleet API",
                "description":  "Direct Tesla integration via Fleet API",
                "configured":   bool(settings.tesla_client_id),
                "brands":       ["Tesla Model S", "Model 3", "Model X", "Model Y", "Cybertruck"],
                "docs":         "https://developer.tesla.com",
            },
        ],
        "active_provider": _token_store.get("provider") or "demo",
    }
