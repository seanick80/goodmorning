"""Open-Meteo API client for weather data."""

from __future__ import annotations

import logging
from datetime import datetime

from ._http import fetch_with_retry

logger = logging.getLogger(__name__)

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

# WMO Weather interpretation codes
WMO_CODES = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    71: "Slight snow",
    73: "Moderate snow",
    75: "Heavy snow",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


def fetch_weather_data(latitude: float, longitude: float, units: str = "fahrenheit") -> dict:
    """Fetch current weather and hourly forecast from Open-Meteo.

    Returns a dict suitable for WeatherCache.objects.update_or_create(defaults=...).
    """
    temp_unit = "fahrenheit" if units == "fahrenheit" else "celsius"
    wind_unit = "mph" if units == "fahrenheit" else "kmh"

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": (
            "temperature_2m,relative_humidity_2m,apparent_temperature,"
            "weather_code,wind_speed_10m,wind_direction_10m,precipitation"
        ),
        "hourly": "temperature_2m,weather_code,precipitation_probability",
        "daily": "temperature_2m_max,temperature_2m_min,sunrise,sunset",
        "temperature_unit": temp_unit,
        "wind_speed_unit": wind_unit,
        "forecast_days": 1,
        "timezone": "auto",
    }
    response = fetch_with_retry(OPEN_METEO_URL, params=params)
    data = response.json()

    current = data["current"]
    daily = data["daily"]

    # Build hourly forecast list
    hourly = data.get("hourly", {})
    hourly_forecast = []
    for i, time_str in enumerate(hourly.get("time", [])):
        hourly_forecast.append({
            "time": time_str,
            "temp": hourly["temperature_2m"][i],
            "weather_code": hourly["weather_code"][i],
            "precip_prob": hourly.get("precipitation_probability", [None])[i],
        })

    sunrise_str = daily["sunrise"][0] if daily.get("sunrise") else None
    sunset_str = daily["sunset"][0] if daily.get("sunset") else None

    return {
        "temperature": current["temperature_2m"],
        "temperature_unit": units,
        "feels_like": current.get("apparent_temperature"),
        "humidity": current.get("relative_humidity_2m"),
        "wind_speed": current.get("wind_speed_10m"),
        "wind_direction": current.get("wind_direction_10m"),
        "weather_code": current["weather_code"],
        "precipitation_probability": None,
        "sunrise": datetime.fromisoformat(sunrise_str).time() if sunrise_str else None,
        "sunset": datetime.fromisoformat(sunset_str).time() if sunset_str else None,
        "daily_high": daily["temperature_2m_max"][0] if daily.get("temperature_2m_max") else None,
        "daily_low": daily["temperature_2m_min"][0] if daily.get("temperature_2m_min") else None,
        "hourly_forecast": hourly_forecast,
    }
