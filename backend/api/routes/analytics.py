"""
GET /api/analytics  — Charging analytics dashboard endpoint (Phase 2).

Returns aggregated charging history data for charts:
    - Wear score trend over time
    - Cost savings trend
    - Charging pattern (hour distribution)
    - SoC distribution
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from models.database import get_db, ChargingSession

router = APIRouter(tags=["Analytics"])


@router.get(
    "/api/analytics",
    summary="Charging analytics",
    description="Aggregated analytics data for dashboard charts — wear trends, savings, patterns.",
)
async def get_analytics(
    limit: int = Query(default=30, ge=1, le=100, description="Number of recent sessions"),
    db: AsyncSession = Depends(get_db),
):
    """
    Return analytics data for the frontend dashboard.
    """

    # --- All sessions (limited) ---
    result = await db.execute(
        select(ChargingSession)
        .order_by(ChargingSession.created_at.desc())
        .limit(limit)
    )
    sessions = result.scalars().all()

    # --- Wear score trend (chronological) ---
    wear_trend = [
        {
            "date":       s.created_at.isoformat() if s.created_at else None,
            "wear_score": s.wear_score,
            "rating":     s.wear_rating,
        }
        for s in reversed(sessions)
        if s.wear_score is not None
    ]

    # --- Cost savings trend ---
    savings_trend = [
        {
            "date":             s.created_at.isoformat() if s.created_at else None,
            "savings_percent":  s.savings_percent,
            "optimized_cost":   s.optimized_cost,
            "normal_cost":      s.normal_cost,
        }
        for s in reversed(sessions)
        if s.savings_percent is not None
    ]

    # --- Charging start-hour distribution ---
    hour_counts: dict[str, int] = {}
    for s in sessions:
        if s.start_charging:
            h = s.start_charging
            hour_counts[h] = hour_counts.get(h, 0) + 1

    charging_pattern = [
        {"hour": h, "count": c}
        for h, c in sorted(hour_counts.items())
    ]

    # --- SoC distribution buckets ---
    soc_buckets = {"0-20": 0, "20-40": 0, "40-60": 0, "60-80": 0, "80-100": 0}
    for s in sessions:
        soc = s.target_soc or 0
        if soc <= 20:   soc_buckets["0-20"]   += 1
        elif soc <= 40: soc_buckets["20-40"]  += 1
        elif soc <= 60: soc_buckets["40-60"]  += 1
        elif soc <= 80: soc_buckets["60-80"]  += 1
        else:           soc_buckets["80-100"] += 1

    # --- Aggregate totals ---
    total_saved = sum(
        (s.normal_cost or 0) - (s.optimized_cost or 0)
        for s in sessions
        if s.normal_cost and s.optimized_cost
    )

    return {
        "status":          "ok",
        "session_count":   len(sessions),
        "total_saved_usd": round(total_saved, 2),
        "wear_trend":      wear_trend,
        "savings_trend":   savings_trend,
        "charging_pattern": charging_pattern,
        "soc_distribution": [
            {"range": k, "count": v} for k, v in soc_buckets.items()
        ],
    }
