"""
Stub routes for battery health dashboard (Phase 2).
"""

from fastapi import APIRouter

router = APIRouter(tags=["Battery Health"])


@router.get(
    "/api/battery-health",
    summary="Get battery health analysis",
    description="Returns current SOH, predicted degradation, cycle count, and RUL. (Phase 2)",
)
async def get_battery_health():
    """Placeholder — will integrate with ML degradation model in Phase 2."""
    return {
        "status": "placeholder",
        "message": "Battery health endpoint coming in Phase 2.",
        "sample_data": {
            "soh_percent": 92.0,
            "cycle_count": 342,
            "estimated_rul_years": 6.5,
            "degradation_trend": "stable",
        },
    }
