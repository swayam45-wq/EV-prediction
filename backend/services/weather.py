"""
Live Weather Service — Phase 4.

Fetches real-time weather data from OpenWeatherMap API.
Falls back gracefully to user-supplied values when:
  - API key is not configured
  - Location is not provided
  - Network request fails

Usage:
    from services.weather import get_weather_adjustments, fetch_live_weather

    # Live fetch (requires OPENWEATHER_API_KEY in .env)
    live = await fetch_live_weather(city="Mumbai")

    # Apply adjustments (works with both live and manual data)
    adjustments = get_weather_adjustments(temp_c=live["temperature_celsius"],
                                          condition=live["weather_condition"])
"""

import httpx
import logging
from typing import Optional

from config import settings

logger = logging.getLogger(__name__)

# ── OpenWeatherMap constants ──────────────────────────────────
OWM_BASE = "https://api.openweathermap.org/data/2.5/weather"

# Map OWM condition group IDs → our internal condition strings
_OWM_CONDITION_MAP: dict[str, str] = {
    "Clear":       "clear",
    "Clouds":      "cloudy",
    "Rain":        "rain",
    "Drizzle":     "rain",
    "Thunderstorm":"rain",
    "Snow":        "snow",
    "Mist":        "cloudy",
    "Fog":         "cloudy",
    "Haze":        "cloudy",
    "Dust":        "cloudy",
    "Sand":        "cloudy",
    "Ash":         "cloudy",
    "Squall":      "rain",
    "Tornado":     "rain",
    "Extreme":     "rain",
}


async def fetch_live_weather(
    city: Optional[str] = None,
    lat: Optional[float] = None,
    lon: Optional[float] = None,
) -> dict:
    """
    Fetch real-time weather from OpenWeatherMap.

    Priority: (lat, lon) > city name.
    Returns a dict with temperature_celsius, weather_condition,
    humidity_pct, wind_speed_ms, description, and source.

    If API key is missing or the request fails, returns a
    `source: "unavailable"` dict with None values.
    """
    api_key = settings.openweather_api_key
    if not api_key:
        logger.info("OPENWEATHER_API_KEY not set — live weather unavailable")
        return _unavailable("API key not configured")

    if not city and (lat is None or lon is None):
        return _unavailable("No location provided (city or lat/lon required)")

    # Build query params
    params: dict = {"appid": api_key, "units": "metric"}
    if lat is not None and lon is not None:
        params["lat"] = lat
        params["lon"] = lon
    else:
        params["q"] = city

    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(OWM_BASE, params=params)
            resp.raise_for_status()
            data = resp.json()

        main_group = data["weather"][0]["main"]          # e.g. "Clouds"
        description = data["weather"][0]["description"]  # e.g. "scattered clouds"
        temp_c      = data["main"]["temp"]
        humidity    = data["main"].get("humidity", 0)
        wind_ms     = data["wind"].get("speed", 0)
        city_name   = data.get("name", city or f"{lat},{lon}")

        condition = _OWM_CONDITION_MAP.get(main_group, "clear")

        logger.info(f"Live weather fetched: {city_name} — {temp_c}°C, {description}")

        return {
            "source":              "openweathermap",
            "city":                city_name,
            "temperature_celsius": round(temp_c, 1),
            "weather_condition":   condition,
            "description":         description,
            "humidity_pct":        humidity,
            "wind_speed_ms":       round(wind_ms, 1),
        }

    except httpx.HTTPStatusError as e:
        logger.warning(f"OWM HTTP error {e.response.status_code}: {e}")
        return _unavailable(f"HTTP {e.response.status_code}")
    except httpx.RequestError as e:
        logger.warning(f"OWM network error: {e}")
        return _unavailable("Network error")
    except Exception as e:
        logger.error(f"Unexpected weather fetch error: {e}")
        return _unavailable(str(e))


def _unavailable(reason: str) -> dict:
    return {
        "source":              "unavailable",
        "city":                None,
        "temperature_celsius": None,
        "weather_condition":   None,
        "description":         None,
        "humidity_pct":        None,
        "wind_speed_ms":       None,
        "reason":              reason,
    }


# ── Adjustment logic (works with any data source) ────────────

def get_weather_adjustments(
    temperature_celsius: float,
    weather_condition: str = "clear",
    humidity_pct: Optional[float] = None,
) -> dict:
    """
    Compute charging adjustments based on weather conditions.

    Args:
        temperature_celsius: Ambient temperature in °C
        weather_condition: One of clear/cloudy/rain/snow/hot
        humidity_pct: Optional relative humidity (0-100)

    Returns:
        dict with efficiency_modifier, solar_opportunity,
        warnings, recommendations
    """
    warnings: list[str] = []
    recommendations: list[str] = []
    efficiency_modifier = 1.0
    solar_opportunity   = False

    # ── Temperature ─────────────────────────────────────────
    if temperature_celsius >= 40:
        efficiency_modifier = 0.85
        warnings.append(
            f"Extreme heat ({temperature_celsius}°C) — charging efficiency "
            "reduced ~15%. Battery thermal management is active."
        )
        recommendations.append(
            "Delay charging to after 10 PM when temperatures drop below 35°C."
        )
    elif temperature_celsius >= 35:
        efficiency_modifier = 0.92
        warnings.append(
            f"High temperature ({temperature_celsius}°C) — slight efficiency reduction."
        )
        recommendations.append(
            "Prefer charging between 10 PM and 6 AM to reduce thermal stress."
        )
    elif temperature_celsius < -15:
        efficiency_modifier = 0.70
        warnings.append(
            f"Extreme cold ({temperature_celsius}°C) — significant efficiency loss."
        )
        recommendations.append(
            "Pre-condition battery for 20–30 min before charging to warm cells."
        )
    elif temperature_celsius < 0:
        efficiency_modifier = 0.82
        warnings.append(
            f"Freezing ({temperature_celsius}°C) — lithium plating risk. "
            "Keep charging rate below 0.5C."
        )
        recommendations.append(
            "Use the vehicle pre-conditioning feature before plugging in."
        )
    elif temperature_celsius < 5:
        efficiency_modifier = 0.90
        warnings.append(
            f"Cold temperature ({temperature_celsius}°C) — slightly reduced efficiency."
        )

    # ── Humidity modifier ─────────────────────────────────────
    if humidity_pct is not None and humidity_pct > 85:
        warnings.append(
            f"High humidity ({humidity_pct:.0f}%) — inspect charge port seals."
        )

    # ── Weather condition ─────────────────────────────────────
    cond = weather_condition.lower()
    if cond in ("clear", "sunny"):
        solar_opportunity = True
        recommendations.append(
            "Clear skies — ideal for solar-assisted charging between 10 AM–3 PM."
        )
    elif cond in ("rain", "drizzle"):
        recommendations.append(
            "Rain detected — verify charging connector is properly seated and sealed."
        )
    elif cond in ("snow", "blizzard"):
        recommendations.append(
            "Snow conditions — check charging port for ice. "
            "Pre-conditioning strongly recommended."
        )
    elif cond in ("cloudy", "overcast"):
        recommendations.append(
            "Overcast — grid charging preferred over solar."
        )
    elif cond == "hot":
        if temperature_celsius < 35:
            efficiency_modifier = 0.88
        recommendations.append(
            "Hot conditions — limit charging to 80% SoC to reduce heat buildup."
        )

    if not recommendations:
        recommendations.append(
            "Weather conditions are favorable for charging. No adjustments needed."
        )

    return {
        "temperature_celsius":  temperature_celsius,
        "weather_condition":    weather_condition,
        "efficiency_modifier":  round(efficiency_modifier, 3),
        "solar_opportunity":    solar_opportunity,
        "warnings":             warnings,
        "recommendations":      recommendations,
    }
