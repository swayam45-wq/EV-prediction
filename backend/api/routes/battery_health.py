"""
GET /api/battery-health  — Battery health dashboard endpoint (Phase 2).

Returns current battery State of Health, wear trends, cycle count,
and ML model-powered Remaining Useful Life estimate.
"""

from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from models.database import get_db, ChargingSession, BatteryProfile
from ml.predict import get_model_info

router = APIRouter(tags=["Battery Health"])


@router.get(
    "/api/battery-health",
    summary="Battery health overview",
    description="Returns current battery health metrics, ML model info, and session statistics.",
)
async def get_battery_health(db: AsyncSession = Depends(get_db)):
    """
    Aggregate battery health data from stored charging sessions
    and return a dashboard-ready response.
    """

    # --- Session stats from DB ---
    result = await db.execute(
        select(
            func.count(ChargingSession.id).label("total_sessions"),
            func.avg(ChargingSession.wear_score).label("avg_wear_score"),
            func.avg(ChargingSession.savings_percent).label("avg_savings_pct"),
            func.sum(ChargingSession.total_energy_kwh).label("total_energy_kwh"),
        )
    )
    stats = result.one()

    total_sessions  = stats.total_sessions or 0
    avg_wear_score  = round(stats.avg_wear_score or 0, 1)
    avg_savings_pct = round(stats.avg_savings_pct or 0, 1)
    total_energy    = round(stats.total_energy_kwh or 0, 1)

    # --- Recent sessions (last 10) ---
    recent_result = await db.execute(
        select(ChargingSession)
        .order_by(ChargingSession.created_at.desc())
        .limit(10)
    )
    recent_sessions = recent_result.scalars().all()

    wear_history = [
        {
            "session_id":   s.id,
            "wear_score":   s.wear_score,
            "wear_rating":  s.wear_rating,
            "target_soc":   s.target_soc,
            "temperature":  s.temperature_celsius,
            "created_at":   s.created_at.isoformat() if s.created_at else None,
        }
        for s in recent_sessions
    ]

    # --- ML model info ---
    model_info = get_model_info()

    # --- Derive a simplified SoH estimate ---
    # Based on avg wear score from sessions
    # (Phase 4: will use per-vehicle cycle count + ML RUL model)
    inferred_soh = round(max(70.0, 100.0 - (avg_wear_score * 0.15)), 1)

    return {
        "status": "ok",
        "summary": {
            "total_charging_sessions": total_sessions,
            "avg_wear_score":          avg_wear_score,
            "avg_savings_percent":     avg_savings_pct,
            "total_energy_charged_kwh": total_energy,
            "inferred_soh_percent":    inferred_soh,
        },
        "wear_history":  wear_history,
        "ml_model_info": model_info,
        "tips": [
            "Keep daily charge target at 80% to maximise battery longevity.",
            "Avoid charging in temperatures above 35 C or below 0 C.",
            "Prefer overnight Level 2 AC charging over DC fast charging.",
        ],
    }
