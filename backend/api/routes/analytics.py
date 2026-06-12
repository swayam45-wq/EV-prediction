"""
Stub routes for analytics dashboard (Phase 2).
"""

from fastapi import APIRouter

router = APIRouter(tags=["Analytics"])


@router.get(
    "/api/analytics",
    summary="Get charging analytics",
    description="Returns battery health trends, cost trends, and charging patterns. (Phase 2)",
)
async def get_analytics():
    """Placeholder — will integrate with PostgreSQL history in Phase 2."""
    return {
        "status": "placeholder",
        "message": "Analytics endpoint coming in Phase 2.",
        "available_charts": [
            "battery_health_trend",
            "electricity_cost_trend",
            "charging_pattern_trend",
        ],
    }
