"""
GET /api/prices  — Dynamic electricity pricing.

Query params:
    region : Region code — US_CA, US_TX, UK, DE, IN, DEFAULT (default: US_CA)
    source : 'auto' | 'live' | 'tou' (default: auto)
"""

from fastapi import APIRouter, Query
from typing import Optional

from services.pricing import get_electricity_prices, SUPPORTED_REGIONS, zip_to_region

router = APIRouter()


@router.get("/prices/region-from-zip")
async def region_from_zip(
    postal_code: str = Query(..., description="ZIP / postal code to look up"),
):
    """
    Map a ZIP / postal code to a pricing region code.

    Returns the detected region along with country, confidence, and a human-readable note.
    Supported formats:
      - US 5-digit ZIP (e.g. 90210, 75001)
      - UK postcode (e.g. SW1A 1AA)
      - German PLZ (e.g. 10115)
      - Indian PIN code (e.g. 400001)
    """
    result = zip_to_region(postal_code)
    return {
        "postal_code": postal_code.strip(),
        **result,
        "supported_regions": SUPPORTED_REGIONS,
    }


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
