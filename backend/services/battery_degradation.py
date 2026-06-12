"""
Battery Degradation Scoring Model.

Provides a heuristic-based battery wear score (0-100) that accounts
for three primary degradation accelerators:

    1. Temperature stress  (0-40 points)
       - Optimal: 15-25°C
       - Heat penalty follows Arrhenius relationship (~2× per 10°C above 25°C)
       - Cold penalty for lithium plating risk below 5°C

    2. High SoC stress  (0-35 points)
       - Keeping the battery above 80% accelerates SEI layer growth
       - Exponential penalty above 90%

    3. Fast charging penalty  (0-25 points)
       - Based on C-rate (charging_rate / battery_capacity)
       - Minimal stress below 0.5C, significant above 1C

The total score drives recommendations for the user.
"""


def calculate_wear_score(
    temperature_celsius: float,
    target_soc_pct: float,
    avg_charging_rate_kw: float,
    battery_capacity_kwh: float,
) -> dict:
    """
    Calculate a battery degradation risk score.

    Args:
        temperature_celsius: Ambient temperature during charging (°C)
        target_soc_pct: Target state of charge (0-100%)
        avg_charging_rate_kw: Average charging power (kW)
        battery_capacity_kwh: Total battery capacity (kWh)

    Returns:
        Dictionary with total_score, rating, component breakdown,
        and actionable recommendations.
    """

    # Convert SoC to fraction for calculations
    target_soc = target_soc_pct / 100.0

    # --- 1. Temperature Impact (0-40 points) ---
    temp_score = _temperature_penalty(temperature_celsius)

    # --- 2. High SoC Stress (0-35 points) ---
    soc_score = _high_soc_penalty(target_soc)

    # --- 3. Fast Charging Penalty (0-25 points) ---
    c_rate = avg_charging_rate_kw / battery_capacity_kwh if battery_capacity_kwh > 0 else 0
    charge_score = _fast_charging_penalty(c_rate)

    # --- Aggregate ---
    total_score = round(min(100.0, temp_score + soc_score + charge_score), 1)

    if total_score < 20:
        rating = "Low"
    elif total_score < 45:
        rating = "Medium"
    else:
        rating = "High"

    # --- Build recommendations ---
    recommendations = _build_recommendations(
        temp_score, soc_score, charge_score,
        temperature_celsius, target_soc_pct, c_rate,
    )

    return {
        "total_score": total_score,
        "rating": rating,
        "temperature_impact": round(temp_score, 1),
        "high_soc_stress": round(soc_score, 1),
        "fast_charging_penalty": round(charge_score, 1),
        "recommendations": recommendations,
    }


def compare_wear_scenarios(
    temperature_celsius: float,
    avg_charging_rate_kw: float,
    battery_capacity_kwh: float,
) -> dict:
    """
    Compare wear scores for charging to 80% vs 100%.

    Returns a side-by-side comparison to show the user the benefit
    of limiting charge to 80%.
    """
    wear_80 = calculate_wear_score(
        temperature_celsius, 80.0, avg_charging_rate_kw, battery_capacity_kwh
    )
    wear_100 = calculate_wear_score(
        temperature_celsius, 100.0, avg_charging_rate_kw, battery_capacity_kwh
    )
    return {
        "charge_to_80": {
            "target_soc": 80,
            "wear_score": wear_80["total_score"],
            "rating": wear_80["rating"],
        },
        "charge_to_100": {
            "target_soc": 100,
            "wear_score": wear_100["total_score"],
            "rating": wear_100["rating"],
        },
        "score_difference": round(
            wear_100["total_score"] - wear_80["total_score"], 1
        ),
        "recommendation": (
            "Limiting charge to 80% reduces battery stress by "
            f"{round(wear_100['total_score'] - wear_80['total_score'], 1)} points."
        ),
    }


# ============================================================
# PRIVATE SCORING FUNCTIONS
# ============================================================

def _temperature_penalty(temp_c: float) -> float:
    """
    Score temperature impact (0-40 points).

    Based on the Arrhenius relationship: degradation rate roughly
    doubles for every 10°C above the optimal range (15-25°C).
    Cold temperatures risk lithium plating.
    """
    if 15 <= temp_c <= 25:
        # Optimal range — minimal stress
        return 0.0
    elif temp_c > 25:
        # Heat penalty — exponential increase
        excess = temp_c - 25
        return min(40.0, (2 ** (excess / 10) - 1) * 10)
    else:
        # Cold penalty — linear increase below 15°C
        deficit = 15 - temp_c
        if temp_c < 0:
            # Severe cold — lithium plating risk
            return min(40.0, 15 + deficit * 1.5)
        return min(25.0, deficit * 1.0)


def _high_soc_penalty(target_soc: float) -> float:
    """
    Score high SoC stress (0-35 points).

    Charging above 80% SoC causes accelerated Solid Electrolyte
    Interphase (SEI) layer growth. The penalty increases sharply
    above 90%.
    """
    if target_soc <= 0.80:
        return 0.0
    elif target_soc <= 0.90:
        # Linear ramp from 0 to 15 between 80-90%
        return ((target_soc - 0.80) / 0.10) * 15
    else:
        # Steeper ramp from 15 to 35 between 90-100%
        return 15 + ((target_soc - 0.90) / 0.10) * 20


def _fast_charging_penalty(c_rate: float) -> float:
    """
    Score fast charging impact (0-25 points).

    C-rate = charging_power (kW) / battery_capacity (kWh).
    Slow charging (≤0.5C) is gentle on the battery.
    Fast charging (>1C) causes mechanical stress and internal heating.
    """
    if c_rate <= 0.5:
        return 0.0
    elif c_rate <= 1.0:
        # Linear ramp from 0 to 10 between 0.5C and 1.0C
        return ((c_rate - 0.5) / 0.5) * 10
    else:
        # Steeper penalty above 1C
        return 10 + min(15.0, (c_rate - 1.0) * 15)


def _build_recommendations(
    temp_score: float,
    soc_score: float,
    charge_score: float,
    temperature: float,
    target_soc_pct: float,
    c_rate: float,
) -> list[str]:
    """Generate actionable battery health recommendations."""
    recs = []

    # Temperature advice
    if temperature > 35:
        recs.append(
            f"🌡️ Current temperature ({temperature}°C) may accelerate battery degradation. "
            "Consider charging during cooler nighttime hours."
        )
    elif temperature < 5:
        recs.append(
            f"❄️ Low temperature ({temperature}°C) reduces charging efficiency "
            "and risks lithium plating. Pre-condition the battery before charging."
        )

    # SoC advice
    if target_soc_pct > 90:
        recs.append(
            "⚠️ Charging above 90% significantly accelerates battery aging. "
            "Limit daily charging to 80% unless you need maximum range."
        )
    elif target_soc_pct > 80:
        recs.append(
            "📊 Charging to 80-90% is acceptable occasionally but keeping daily "
            "charge at 80% extends battery lifespan."
        )

    # Charging rate advice
    if c_rate > 1.0:
        recs.append(
            f"⚡ High C-rate ({c_rate:.2f}C) detected. Use Level 2 (AC) "
            "charging when time permits to reduce battery stress."
        )
    elif c_rate > 0.5:
        recs.append(
            "✅ Moderate charging rate — battery stress is within normal limits."
        )

    # General advice
    if not recs:
        recs.append(
            "✅ Current charging conditions are optimal for battery longevity."
        )

    recs.append("💡 Use slow overnight charging whenever possible for best battery health.")

    return recs
