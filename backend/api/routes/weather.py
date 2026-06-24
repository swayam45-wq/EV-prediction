"""
GET /api/weather  — Live weather fetch + adjustment advice.

Query params:
    city  : City name (e.g. "Mumbai", "London")
    lat   : Latitude  (use with lon)
    lon   : Longitude (use with lat)
    temp  : Fallback temperature in °C (used when city/lat not supplied)
    condition: Fallback weather string (used when city/lat not supplied)
"""

from fastapi import APIRouter
from typing import Optional

from services.weather import fetch_live_weather, get_weather_adjustments

router = APIRouter()


@router.get("/weather")
async def get_weather(
    city: Optional[str] = None,
    lat:  Optional[float] = None,
    lon:  Optional[float] = None,
    temp: Optional[float] = 22.0,
    condition: Optional[str] = "clear",
):
    """
    Fetch live weather data and compute charging adjustments.

    If OPENWEATHER_API_KEY is set and a location is provided,
    returns real-time data. Otherwise falls back to the supplied
    temp/condition values.
    """
    # Try live fetch first
    live = await fetch_live_weather(city=city, lat=lat, lon=lon)

    if live["source"] == "openweathermap":
        temp_c = live["temperature_celsius"]
        cond   = live["weather_condition"]
        humidity = live["humidity_pct"]
    else:
        # Fallback to user-supplied values
        temp_c   = temp
        cond     = condition
        humidity = None

    adjustments = get_weather_adjustments(
        temperature_celsius=temp_c,
        weather_condition=cond,
        humidity_pct=humidity,
    )

    return {
        "status": "ok",
        "live_data": live,
        "adjustments": adjustments,
    }
