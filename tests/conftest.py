"""Test fixtures. The weather service is faked: fetch_json is replaced, so no test touches the internet."""

from datetime import datetime, timedelta
from urllib.parse import parse_qs, urlparse

import pytest

from weather_app import create_app, weather


def forecast_payload(current_time: str = "2026-11-26T14:15", code: int = 2) -> dict:
    """An Open-Meteo forecast answer: 7 days of hourly data from midnight, the current conditions and 7 daily rows."""
    start = datetime(2026, 11, 26)
    hours = [(start + timedelta(hours=i)).strftime("%Y-%m-%dT%H:%M") for i in range(7 * 24)]
    days = [(start + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]
    return {
        "timezone": "Asia/Kolkata",
        "current": {"time": current_time, "temperature_2m": 29.4, "relative_humidity_2m": 74, "apparent_temperature": 33.1,
                    "weather_code": code, "wind_speed_10m": 14.2, "wind_direction_10m": 90, "is_day": 1},
        "hourly": {"time": hours, "temperature_2m": [20 + (i % 24) / 2 for i in range(len(hours))],
                   "precipitation_probability": [(i * 7) % 100 for i in range(len(hours))]},
        "daily": {"time": days, "weather_code": [0, 1, 3, 61, 95, 45, 80], "temperature_2m_max": [31, 30, 29, 28, 27, 30, 31],
                  "temperature_2m_min": [24, 23, 23, 22, 22, 23, 24], "precipitation_sum": [0, 0, 0.4, 12.5, 30.1, 0, 2.2],
                  "sunrise": [f"{d}T06:12" for d in days], "sunset": [f"{d}T17:44" for d in days]},
    }


GEOCODE = {"results": [
    {"name": "Paris", "country": "France", "admin1": "Île-de-France", "latitude": 48.85341, "longitude": 2.3488},
    {"name": "Paris", "country": "United States", "admin1": "Texas", "latitude": 33.66094, "longitude": -95.55551},
]}


class FakeOpenMeteo:
    """Answers like Open-Meteo and remembers every URL asked for."""

    def __init__(self) -> None:
        self.calls: list[dict] = []
        self.forecast = forecast_payload()
        self.fail = False

    def __call__(self, url: str, timeout: float = 10.0) -> dict:
        parsed = urlparse(url)
        self.calls.append({"host": parsed.netloc, "params": {k: v[0] for k, v in parse_qs(parsed.query).items()}})
        if self.fail:
            raise weather.WeatherServiceError("connection refused")
        if parsed.netloc.startswith("geocoding"):
            return GEOCODE
        return self.forecast


@pytest.fixture()
def fake_weather(monkeypatch):
    fake = FakeOpenMeteo()
    monkeypatch.setattr(weather, "fetch_json", fake)
    weather.clear_cache()
    yield fake
    weather.clear_cache()


@pytest.fixture()
def app(tmp_path, fake_weather):
    return create_app({"TESTING": True, "DATABASE": str(tmp_path / "test.sqlite")})


@pytest.fixture()
def client(app):
    return app.test_client()
