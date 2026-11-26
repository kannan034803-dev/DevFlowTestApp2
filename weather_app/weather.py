"""Real weather from Open-Meteo (https://open-meteo.com - free, no API key), turned into the shape the dashboard uses.

All network access goes through fetch_json, so tests replace that one function and never touch the internet.
Answers are cached for CACHE_SECONDS (10 minutes) - the weather does not change faster than that.
"""

import json
import time
import urllib.error
import urllib.parse
import urllib.request

from flask import current_app

FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
UNITS = {
    "metric": {"temperature_unit": "celsius", "wind_speed_unit": "kmh", "temp": "°C", "wind": "km/h"},
    "imperial": {"temperature_unit": "fahrenheit", "wind_speed_unit": "mph", "temp": "°F", "wind": "mph"},
}

_cache: dict[str, tuple[float, object]] = {}


class WeatherServiceError(RuntimeError):
    pass


def fetch_json(url: str, timeout: float = 10.0) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "weather-report-demo/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as res:
            return json.loads(res.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, ValueError) as exc:
        raise WeatherServiceError(str(exc)) from exc


def _cached(url: str) -> dict:
    ttl = current_app.config.get("CACHE_SECONDS", 600)
    hit = _cache.get(url)
    if hit and hit[0] > time.monotonic():
        return hit[1]  # type: ignore[return-value]
    data = fetch_json(url)
    _cache[url] = (time.monotonic() + ttl, data)
    return data


def clear_cache() -> None:
    _cache.clear()


def describe(code: int) -> dict[str, str]:
    """WMO weather code -> text and icon (https://open-meteo.com/en/docs, "WMO Weather interpretation codes")."""
    if code == 0:
        return {"text": "Clear sky", "icon": "☀️"}
    if code in (1, 2):
        return {"text": "Mainly clear" if code == 1 else "Partly cloudy", "icon": "🌤️" if code == 1 else "⛅"}
    if code == 3:
        return {"text": "Overcast", "icon": "☁️"}
    if code in (45, 48):
        return {"text": "Fog", "icon": "🌫️"}
    if 51 <= code <= 57:
        return {"text": "Drizzle", "icon": "🌦️"}
    if 61 <= code <= 77:
        return {"text": "Rain", "icon": "🌧️"}
    if 80 <= code <= 82:
        return {"text": "Rain showers", "icon": "🌦️"}
    if code in (85, 86):
        return {"text": "Snow showers", "icon": "🌨️"}
    if code >= 95:
        return {"text": "Thunderstorm", "icon": "⛈️"}
    return {"text": "Unknown", "icon": "❔"}


def search(query: str, count: int = 6) -> list[dict]:
    """Places matching the name, e.g. 'Paris' -> Paris (France), Paris (United States) ..."""
    url = f"{GEOCODE_URL}?{urllib.parse.urlencode({'name': query, 'count': count, 'language': 'en', 'format': 'json'})}"
    return [
        {"name": r.get("name", ""), "country": r.get("country", ""), "region": r.get("admin1", ""),
         "latitude": r["latitude"], "longitude": r["longitude"]}
        for r in _cached(url).get("results") or []
    ]


def forecast(latitude: float, longitude: float, units: str = "metric") -> dict:
    """Current conditions, the next 24 hours and 7 days for one place."""
    u = UNITS[units]
    params = {
        "latitude": latitude, "longitude": longitude, "timezone": "auto", "forecast_days": 7,
        "temperature_unit": u["temperature_unit"], "wind_speed_unit": u["wind_speed_unit"],
        "current": "temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m,wind_direction_10m,is_day",
        "hourly": "temperature_2m,precipitation_probability",
        "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum,sunrise,sunset",
    }
    data = _cached(f"{FORECAST_URL}?{urllib.parse.urlencode(params)}")
    cur = data["current"]
    hourly, daily = data["hourly"], data["daily"]
    # the next 24 hours, starting at the current hour (times are local to the place, "2026-11-26T14:00")
    start = next((i for i, t in enumerate(hourly["time"]) if t[:13] >= cur["time"][:13]), 0)
    return {
        "timezone": data.get("timezone", ""),
        "units": {"temp": u["temp"], "wind": u["wind"]},
        "current": {
            "time": cur["time"], "temperature": cur["temperature_2m"], "feelsLike": cur["apparent_temperature"],
            "humidity": cur["relative_humidity_2m"], "windSpeed": cur["wind_speed_10m"], "windDirection": cur["wind_direction_10m"],
            "isDay": bool(cur.get("is_day", 1)), "code": cur["weather_code"], **describe(cur["weather_code"]),
        },
        "hourly": [
            {"time": hourly["time"][i], "temperature": hourly["temperature_2m"][i], "precipChance": hourly["precipitation_probability"][i]}
            for i in range(start, min(start + 24, len(hourly["time"])))
        ],
        "daily": [
            {"date": daily["time"][i], "code": daily["weather_code"][i], **describe(daily["weather_code"][i]),
             "max": daily["temperature_2m_max"][i], "min": daily["temperature_2m_min"][i], "precip": daily["precipitation_sum"][i],
             "sunrise": daily["sunrise"][i], "sunset": daily["sunset"][i]}
            for i in range(len(daily["time"]))
        ],
    }
