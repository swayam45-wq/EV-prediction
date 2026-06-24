"""
POST /api/recommend — Core charging recommendation endpoint (Phase 4).

Pipeline:
    1. Validate inputs
    2. Weather adjustments (live or manual)
    3. LP optimizer (with optional V2G)
    4. XGBoost wear prediction
    5. Cost analysis
    6. Enhanced AI explanation engine
    7. Persist to DB
    8. Return unified response
"""

from fastapi import APIRouter, HTTPException, Depends

from models.schemas import (
    ChargingRequest,
    ChargingRecommendation,
    HourlyChargingSlot,
    CostComparison,
    BatteryWearEstimate,
)
from models.database import get_db, ChargingSession
from services.optimizer import optimize_charging_schedule
from services.cost_analyzer import analyze_costs
from services.explainer import generate_explanations, generate_health_advice
from services.weather import get_weather_adjustments
from ml.predict import predict_wear_score
from sqlalchemy.ext.asyncio import AsyncSession


router = APIRouter(tags=["Charging Recommendation"])


@router.post(
    "/api/recommend",
    response_model=ChargingRecommendation,
    summary="Get optimal EV charging recommendation",
    description=(
        "Accepts vehicle state, schedule, electricity prices, and optional weather data. "
        "Returns an LP-optimized charging schedule with cost savings, "
        "XGBoost battery wear prediction, V2G revenue (if enabled), "
        "and AI-generated explanations."
    ),
)
async def recommend_charging(
    request: ChargingRequest,
    db: AsyncSession = Depends(get_db),
):
    # ── 1. Validate ────────────────────────────────────────────
    if request.target_soc <= request.current_soc:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Target SoC ({request.target_soc}%) must be greater than "
                f"current SoC ({request.current_soc}%)."
            ),
        )

    hours  = [ep.hour  for ep in request.electricity_prices]
    prices = [ep.price for ep in request.electricity_prices]

    departure_hour  = _parse_hour(request.departure_time)
    eligible_hours  = []
    eligible_prices = []

    for h, p in zip(hours, prices):
        if _parse_hour(h) < departure_hour:
            eligible_hours.append(h)
            eligible_prices.append(p)

    if not eligible_hours:
        raise HTTPException(
            status_code=422,
            detail=(
                f"No price slots before departure ({request.departure_time}). "
                "Provide prices for earlier hours."
            ),
        )

    # ── 2. Weather ─────────────────────────────────────────────
    temp_c   = request.temperature_celsius or 25.0
    cond     = request.weather_condition or "clear"
    weather  = get_weather_adjustments(
        temperature_celsius=temp_c,
        weather_condition=cond,
    )
    eff = (request.charging_efficiency or 0.90) * weather["efficiency_modifier"]

    # ── 3. LP Optimizer (+ V2G) ────────────────────────────────
    v2g_enabled = getattr(request, "v2g_enabled", False)
    result = optimize_charging_schedule(
        hours=eligible_hours,
        prices=eligible_prices,
        max_charge_rate_kw=request.max_charge_rate_kw,
        battery_capacity_kwh=request.battery_capacity_kwh,
        current_soc_pct=request.current_soc,
        target_soc_pct=request.target_soc,
        battery_health_soh=request.battery_health_soh,
        charging_efficiency=eff,
        temperature_celsius=temp_c,
        v2g_enabled=v2g_enabled,
    )

    if result["status"] == "infeasible":
        raise HTTPException(
            status_code=422,
            detail="No feasible charging schedule found. Check constraints.",
        )

    # ── 4. Schedule response ───────────────────────────────────
    schedule_slots = [
        HourlyChargingSlot(
            hour=s["hour"],
            price=s["price"],
            energy_kwh=s["energy_kwh"],
            is_charging=s["is_charging"],
            cumulative_soc=s["cumulative_soc"],
        )
        for s in result["schedule"]
    ]

    # Derive start / stop times
    active = [s for s in result["schedule"] if s["is_charging"]]
    start_charging = active[0]["hour"]  if active else None
    stop_charging  = active[-1]["hour"] if active else None

    # ── 5. Cost analysis ───────────────────────────────────────
    usable_cap    = request.battery_capacity_kwh * (request.battery_health_soh / 100.0)
    energy_needed = (request.target_soc - request.current_soc) / 100.0 * usable_cap
    cost_data = analyze_costs(
        hours=eligible_hours,
        prices=eligible_prices,
        optimized_energy=[s["energy_kwh"] for s in result["schedule"]],
        energy_needed_kwh=energy_needed,
        max_charge_rate_kw=request.max_charge_rate_kw,
        charging_efficiency=eff,
    )
    cost_comparison = CostComparison(
        normal_cost=cost_data["normal_cost"],
        optimized_cost=cost_data["optimized_cost"],
        savings_dollar=cost_data["savings_dollar"],
        savings_percent=cost_data["savings_percent"],
    )

    # ── 6. ML Wear Prediction ──────────────────────────────────
    active_slots = [s for s in result["schedule"] if s["energy_kwh"] > 0.01]
    total_energy = sum(s["energy_kwh"] for s in active_slots)
    avg_rate     = total_energy / len(active_slots) if active_slots else 0.0

    wear_data = predict_wear_score(
        battery_soc_pct=request.current_soc,
        target_soc_pct=request.target_soc,
        ambient_temp_c=temp_c,
        battery_temp_c=temp_c + 5.0,
        charge_rate_kw=avg_rate,
        battery_capacity_kwh=request.battery_capacity_kwh,
        battery_health_soh=request.battery_health_soh,
    )
    wear_estimate = BatteryWearEstimate(
        total_score=wear_data["total_score"],
        rating=wear_data["rating"],
        temperature_impact=wear_data.get("temperature_impact", 0.0),
        high_soc_stress=wear_data.get("high_soc_stress", 0.0),
        fast_charging_penalty=wear_data.get("fast_charging_penalty", 0.0),
    )

    # ── 7. Enhanced AI explanations ────────────────────────────
    price_vals    = eligible_prices
    peak_price    = max(price_vals) if price_vals else None
    off_peak_price= min(price_vals) if price_vals else None
    off_peak_hour = eligible_hours[price_vals.index(off_peak_price)] if price_vals else None

    explanations = generate_explanations(
        current_soc=request.current_soc,
        target_soc=request.target_soc,
        battery_capacity_kwh=request.battery_capacity_kwh,
        battery_health_soh=request.battery_health_soh,
        max_charge_rate_kw=request.max_charge_rate_kw,
        departure_time=request.departure_time,
        temperature_celsius=temp_c,
        weather_condition=cond,
        start_charging=start_charging,
        stop_charging=stop_charging,
        total_energy_kwh=result.get("total_energy_kwh"),
        normal_cost=cost_data["normal_cost"],
        optimized_cost=cost_data["optimized_cost"],
        savings_dollar=cost_data["savings_dollar"],
        savings_percent=cost_data["savings_percent"],
        peak_price=peak_price,
        off_peak_price=off_peak_price,
        off_peak_hour=off_peak_hour,
        wear_score=wear_data["total_score"],
        wear_rating=wear_data["rating"],
        schedule_slots=result["schedule"],
        v2g_enabled=v2g_enabled,
        v2g_revenue=result.get("v2g_revenue", 0.0),
    )

    battery_advice = generate_health_advice(
        target_soc=request.target_soc,
        temperature_celsius=temp_c,
        max_charge_rate_kw=request.max_charge_rate_kw,
        battery_capacity_kwh=request.battery_capacity_kwh,
        battery_health_soh=request.battery_health_soh,
        wear_rating=wear_data["rating"],
        weather_condition=cond,
    )

    if weather["warnings"]:
        battery_advice = weather["warnings"] + battery_advice

    # ── 8. Response ────────────────────────────────────────────
    response = ChargingRecommendation(
        status=result["status"],
        start_charging=start_charging,
        stop_charging=stop_charging,
        schedule=schedule_slots,
        total_energy_kwh=result["total_energy_kwh"],
        target_soc_reached=True,
        cost_analysis=cost_comparison,
        wear_estimate=wear_estimate,
        battery_health_advice=battery_advice,
        explanations=explanations,
    )

    # ── 9. Persist to DB ───────────────────────────────────────
    try:
        session = ChargingSession(
            current_soc=request.current_soc,
            target_soc=request.target_soc,
            battery_capacity_kwh=request.battery_capacity_kwh,
            max_charge_rate_kw=request.max_charge_rate_kw,
            battery_health_soh=request.battery_health_soh,
            temperature_celsius=temp_c,
            weather_condition=cond,
            departure_time=request.departure_time,
            charging_efficiency=request.charging_efficiency or 0.90,
            status=result["status"],
            start_charging=start_charging,
            stop_charging=stop_charging,
            total_energy_kwh=result["total_energy_kwh"],
            optimized_cost=cost_data["optimized_cost"],
            normal_cost=cost_data["normal_cost"],
            savings_percent=cost_data["savings_percent"],
            wear_score=wear_data["total_score"],
            wear_rating=wear_data["rating"],
            wear_source=wear_data.get("source", "unknown"),
            schedule_json=[s.model_dump() for s in schedule_slots],
            explanations_json=explanations,
        )
        db.add(session)
        await db.flush()
    except Exception:
        pass  # DB errors must never break the API response

    return response


# ── Helper ─────────────────────────────────────────────────────

def _parse_hour(time_str: str) -> int:
    try:
        return int(time_str.strip().split(":")[0])
    except (ValueError, IndexError):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid time format '{time_str}'. Use HH:MM.",
        )
