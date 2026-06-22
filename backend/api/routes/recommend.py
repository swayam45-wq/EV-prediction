"""
POST /api/recommend — Core charging recommendation endpoint.

Orchestrates the full recommendation pipeline:
    1. Parse & validate user inputs
    2. Run LP optimizer to find cheapest schedule
    3. Calculate battery wear score
    4. Compare costs (naive vs. optimized)
    5. Generate human-readable explanations
    6. Return unified ChargingRecommendation response
"""

from fastapi import APIRouter, HTTPException, Depends
import json

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
from services.recommendation_engine import generate_explanations
from services.weather import get_weather_adjustments
from ml.predict import predict_wear_score
from sqlalchemy.ext.asyncio import AsyncSession


router = APIRouter(tags=["Charging Recommendation"])


@router.post(
    "/api/recommend",
    response_model=ChargingRecommendation,
    summary="Get optimal EV charging recommendation",
    description=(
        "Accepts vehicle state, schedule, electricity prices, and weather data. "
        "Returns an LP-optimized charging schedule with cost savings analysis, "
        "battery health advice (XGBoost ML model), and human-readable explanations."
    ),
)
async def recommend_charging(
    request: ChargingRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Main recommendation endpoint.

    Takes the user's complete charging context and returns an
    optimized charging plan that minimizes cost while protecting
    battery health.
    """

    # ----------------------------------------------------------
    # 1. VALIDATE INPUTS
    # ----------------------------------------------------------
    if request.target_soc <= request.current_soc:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Target SoC ({request.target_soc}%) must be greater than "
                f"current SoC ({request.current_soc}%). No charging needed."
            ),
        )

    # Extract hour labels and prices from the structured input
    hours = [ep.hour for ep in request.electricity_prices]
    prices = [ep.price for ep in request.electricity_prices]

    # Filter slots to only those before departure time
    departure_hour = _parse_hour(request.departure_time)
    eligible_hours = []
    eligible_prices = []

    for h, p in zip(hours, prices):
        slot_hour = _parse_hour(h)
        if slot_hour < departure_hour:
            eligible_hours.append(h)
            eligible_prices.append(p)

    if not eligible_hours:
        raise HTTPException(
            status_code=422,
            detail=(
                "No electricity price slots available before the departure time "
                f"({request.departure_time}). Provide prices for earlier hours."
            ),
        )

    # ----------------------------------------------------------
    # 2. WEATHER ADJUSTMENTS
    # ----------------------------------------------------------
    weather = get_weather_adjustments(
        temperature_celsius=request.temperature_celsius or 25.0,
        weather_condition=request.weather_condition or "clear",
    )

    # Adjust charging efficiency based on weather
    effective_efficiency = (
        (request.charging_efficiency or 0.90) * weather["efficiency_modifier"]
    )

    # ----------------------------------------------------------
    # 3. RUN LP OPTIMIZER
    # ----------------------------------------------------------
    result = optimize_charging_schedule(
        hours=eligible_hours,
        prices=eligible_prices,
        max_charge_rate_kw=request.max_charge_rate_kw,
        battery_capacity_kwh=request.battery_capacity_kwh,
        current_soc_pct=request.current_soc,
        target_soc_pct=request.target_soc,
        battery_health_soh=request.battery_health_soh,
        charging_efficiency=effective_efficiency,
        temperature_celsius=request.temperature_celsius or 25.0,
    )

    if result["status"] == "infeasible":
        raise HTTPException(
            status_code=422,
            detail=(
                "No feasible charging schedule found. "
                + result.get("message", "Check your constraints.")
            ),
        )

    # ----------------------------------------------------------
    # 4. BUILD SCHEDULE RESPONSE
    # ----------------------------------------------------------
    schedule_slots = [
        HourlyChargingSlot(
            hour=slot["hour"],
            price=slot["price"],
            energy_kwh=slot["energy_kwh"],
            is_charging=slot["is_charging"],
            cumulative_soc=slot["cumulative_soc"],
        )
        for slot in result["schedule"]
    ]

    # ----------------------------------------------------------
    # 5. COST ANALYSIS
    # ----------------------------------------------------------
    usable_capacity = (
        request.battery_capacity_kwh * (request.battery_health_soh / 100.0)
    )
    energy_needed = (
        (request.target_soc - request.current_soc) / 100.0 * usable_capacity
    )

    optimized_energy = [slot["energy_kwh"] for slot in result["schedule"]]

    cost_data = analyze_costs(
        hours=eligible_hours,
        prices=eligible_prices,
        optimized_energy=optimized_energy,
        energy_needed_kwh=energy_needed,
        max_charge_rate_kw=request.max_charge_rate_kw,
        charging_efficiency=effective_efficiency,
    )

    cost_comparison = CostComparison(
        normal_cost=cost_data["normal_cost"],
        optimized_cost=cost_data["optimized_cost"],
        savings_dollar=cost_data["savings_dollar"],
        savings_percent=cost_data["savings_percent"],
    )

    # ----------------------------------------------------------
    # 6. BATTERY WEAR ESTIMATION (ML Model)
    # ----------------------------------------------------------
    active_slots = [s for s in result["schedule"] if s["energy_kwh"] > 0.01]
    total_energy = sum(s["energy_kwh"] for s in active_slots)
    num_active = len(active_slots) if active_slots else 1
    avg_rate = total_energy / num_active

    # Use ML model (falls back to heuristic if model not found)
    temp_c = request.temperature_celsius or 25.0
    wear_data = predict_wear_score(
        battery_soc_pct=request.current_soc,
        target_soc_pct=request.target_soc,
        ambient_temp_c=temp_c,
        battery_temp_c=temp_c + 5.0,          # battery slightly warmer than ambient
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

    # Collect battery health advice
    battery_advice = wear_data.get("recommendations", [])

    # Add weather warnings to advice
    if weather["warnings"]:
        battery_advice.extend(weather["warnings"])

    # ----------------------------------------------------------
    # 7. AI EXPLANATIONS
    # ----------------------------------------------------------
    explanations = generate_explanations(
        schedule=result["schedule"],
        prices=eligible_prices,
        temperature_celsius=temp_c,
        target_soc_pct=request.target_soc,
        current_soc_pct=request.current_soc,
        cost_analysis=cost_data,
    )

    if weather["solar_opportunity"]:
        explanations.append(
            "Solar energy opportunity detected — consider shifting some charging "
            "to midday hours if solar panels are available."
        )

    # ----------------------------------------------------------
    # 8. ASSEMBLE RESPONSE
    # ----------------------------------------------------------
    response = ChargingRecommendation(
        status=result["status"],
        start_charging=result["start_time"],
        stop_charging=result["stop_time"],
        schedule=schedule_slots,
        total_energy_kwh=result["total_energy_kwh"],
        target_soc_reached=True,
        cost_analysis=cost_comparison,
        wear_estimate=wear_estimate,
        battery_health_advice=battery_advice,
        explanations=explanations,
    )

    # ----------------------------------------------------------
    # 9. PERSIST SESSION TO DATABASE
    # ----------------------------------------------------------
    try:
        session = ChargingSession(
            current_soc=request.current_soc,
            target_soc=request.target_soc,
            battery_capacity_kwh=request.battery_capacity_kwh,
            max_charge_rate_kw=request.max_charge_rate_kw,
            battery_health_soh=request.battery_health_soh,
            temperature_celsius=temp_c,
            weather_condition=request.weather_condition or "clear",
            departure_time=request.departure_time,
            charging_efficiency=request.charging_efficiency or 0.90,
            status=result["status"],
            start_charging=result["start_time"],
            stop_charging=result["stop_time"],
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
        await db.flush()   # get the ID without full commit (get_db commits on exit)
    except Exception:
        pass   # DB errors must never break the API response

    return response


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def _parse_hour(time_str: str) -> int:
    """
    Parse a time string like '08:00' or '14:30' into an integer hour.

    Returns the hour component (0-23). For comparison purposes,
    minutes are ignored (slots are hourly).
    """
    try:
        parts = time_str.strip().split(":")
        return int(parts[0])
    except (ValueError, IndexError):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid time format: '{time_str}'. Use HH:MM (e.g., '08:00').",
        )
