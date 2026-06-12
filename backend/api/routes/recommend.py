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

from fastapi import APIRouter, HTTPException

from models.schemas import (
    ChargingRequest,
    ChargingRecommendation,
    HourlyChargingSlot,
    CostComparison,
    BatteryWearEstimate,
)
from services.optimizer import optimize_charging_schedule
from services.battery_degradation import calculate_wear_score, compare_wear_scenarios
from services.cost_analyzer import analyze_costs
from services.recommendation_engine import generate_explanations
from services.weather import get_weather_adjustments


router = APIRouter(tags=["Charging Recommendation"])


@router.post(
    "/api/recommend",
    response_model=ChargingRecommendation,
    summary="Get optimal EV charging recommendation",
    description=(
        "Accepts vehicle state, schedule, electricity prices, and weather data. "
        "Returns an LP-optimized charging schedule with cost savings analysis, "
        "battery health advice, and human-readable explanations."
    ),
)
async def recommend_charging(request: ChargingRequest):
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
    # 6. BATTERY WEAR ESTIMATION
    # ----------------------------------------------------------
    active_slots = [s for s in result["schedule"] if s["energy_kwh"] > 0.01]
    total_energy = sum(s["energy_kwh"] for s in active_slots)
    num_active = len(active_slots) if active_slots else 1
    avg_rate = total_energy / num_active

    wear_data = calculate_wear_score(
        temperature_celsius=request.temperature_celsius or 25.0,
        target_soc_pct=request.target_soc,
        avg_charging_rate_kw=avg_rate,
        battery_capacity_kwh=request.battery_capacity_kwh,
    )

    wear_estimate = BatteryWearEstimate(
        total_score=wear_data["total_score"],
        rating=wear_data["rating"],
        temperature_impact=wear_data["temperature_impact"],
        high_soc_stress=wear_data["high_soc_stress"],
        fast_charging_penalty=wear_data["fast_charging_penalty"],
    )

    # Collect battery health advice
    battery_advice = wear_data["recommendations"]

    # Add weather warnings to advice
    if weather["warnings"]:
        battery_advice.extend(weather["warnings"])

    # ----------------------------------------------------------
    # 7. AI EXPLANATIONS
    # ----------------------------------------------------------
    explanations = generate_explanations(
        schedule=result["schedule"],
        prices=eligible_prices,
        temperature_celsius=request.temperature_celsius or 25.0,
        target_soc_pct=request.target_soc,
        current_soc_pct=request.current_soc,
        cost_analysis=cost_data,
    )

    # Add weather recommendations to explanations
    if weather["solar_opportunity"]:
        explanations.append(
            "☀️ Solar energy opportunity detected — if you have solar panels, "
            "consider shifting some charging to midday hours."
        )

    # ----------------------------------------------------------
    # 8. ASSEMBLE RESPONSE
    # ----------------------------------------------------------
    return ChargingRecommendation(
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
