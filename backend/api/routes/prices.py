"""
GET /api/prices  — Dynamic electricity pricing.

Query params:
    region : Region code — US_CA, US_TX, UK, DE, IN, DEFAULT (default: US_CA)
    source : 'auto' | 'live' | 'tou' (default: auto)
"""

from fastapi import APIRouter
from typing import Optional

from services.pricing import get_electricity_prices, SUPPORTED_REGIONS

router = APIRouter()


@router.get("/prices")
async def get_prices(
    region: Optional[str] = "US_CA",
    source: Optional[str] = "auto",
):
    """
    Return a 24-hour electricity price schedule for the given region.

    Tries EIA live data first (auto mode), falls back to regional
    Time-of-Use profiles modelled from real utility tariffs.
    """
    result = await get_electricity_prices(region=region, source=source)
    result["supported_regions"] = SUPPORTED_REGIONS
    return result
