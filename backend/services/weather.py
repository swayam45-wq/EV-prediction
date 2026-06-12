"""
Weather-Aware Optimization Service.

Provides weather-based adjustments to the charging strategy.
Phase 1 uses the user-supplied temperature and weather condition.
Phase 2 will integrate with OpenWeatherMap / WeatherAPI for
real-time and forecast data.
"""


def get_weather_adjustments(
    temperature_celsius: float,
    weather_condition: str = "clear",
) -> dict:
    """
    Analyze weather conditions and return charging adjustments.

    Args:
        temperature_celsius: Ambient temperature (°C)
        weather_condition: Weather descriptor (clear, sunny, rain, snow, etc.)

    Returns:
        Dictionary with:
            - efficiency_modifier: multiplier for charging efficiency
            - warnings: list of weather-related warnings
            - solar_opportunity: whether solar charging is favorable
            - recommendations: weather-specific charging advice
    """
    warnings = []
    recommendations = []
    efficiency_modifier = 1.0
    solar_opportunity = False

    # --- Temperature Analysis ---
    if temperature_celsius > 40:
        efficiency_modifier = 0.85
        warnings.append(
            f"Extreme heat ({temperature_celsius}°C) — charging efficiency "
            "reduced by ~15%. Battery thermal management under heavy load."
        )
        recommendations.append(
            "Delay charging to nighttime when temperatures drop below 35°C."
        )

    elif temperature_celsius > 35:
        efficiency_modifier = 0.92
        warnings.append(
            f"High temperature ({temperature_celsius}°C) — slight efficiency "
            "reduction. Consider nighttime charging."
        )
        recommendations.append(
            "Prefer charging between 10 PM and 6 AM to avoid thermal stress."
        )

    elif temperature_celsius < -10:
        efficiency_modifier = 0.75
        warnings.append(
            f"Extreme cold ({temperature_celsius}°C) — significant efficiency "
            "loss. Battery may require extended pre-conditioning."
        )
        recommendations.append(
            "Pre-condition the battery for 15-20 minutes before charging. "
            "Expect slower charge rates."
        )

    elif temperature_celsius < 0:
        efficiency_modifier = 0.82
        warnings.append(
            f"Freezing temperature ({temperature_celsius}°C) — reduced "
            "charging efficiency and lithium plating risk."
        )
        recommendations.append(
            "Use the vehicle's pre-conditioning feature before plugging in."
        )

    elif temperature_celsius < 5:
        efficiency_modifier = 0.90
        warnings.append(
            f"Cold temperature ({temperature_celsius}°C) — slightly reduced "
            "efficiency."
        )

    # --- Weather Condition Analysis ---
    condition_lower = weather_condition.lower()

    if condition_lower in ("sunny", "clear"):
        solar_opportunity = True
        recommendations.append(
            "☀️ Clear skies — excellent conditions for solar-assisted charging "
            "between 10 AM and 3 PM if solar panels are available."
        )

    elif condition_lower in ("rain", "rainy", "drizzle"):
        solar_opportunity = False
        recommendations.append(
            "🌧️ Rain detected — ensure charging connector is protected. "
            "Solar generation will be reduced."
        )

    elif condition_lower in ("snow", "blizzard", "ice"):
        solar_opportunity = False
        recommendations.append(
            "🌨️ Snow/ice conditions — check charging port for ice buildup. "
            "Pre-conditioning strongly recommended."
        )

    elif condition_lower in ("cloudy", "overcast"):
        solar_opportunity = False
        recommendations.append(
            "☁️ Cloudy conditions — solar generation limited. "
            "Grid charging recommended."
        )

    # Default recommendation
    if not recommendations:
        recommendations.append(
            "✅ Weather conditions are favorable for charging."
        )

    return {
        "temperature_celsius": temperature_celsius,
        "weather_condition": weather_condition,
        "efficiency_modifier": round(efficiency_modifier, 2),
        "solar_opportunity": solar_opportunity,
        "warnings": warnings,
        "recommendations": recommendations,
    }
