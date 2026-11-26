"""The weather API: real Open-Meteo answers (faked here) turned into the dashboard's shape."""

from weather_app import weather

CHENNAI = "/api/weather?lat=13.0878&lon=80.2785"


def test_current_conditions(client):
    w = client.get(CHENNAI).get_json()
    assert w["timezone"] == "Asia/Kolkata"
    assert w["units"] == {"temp": "°C", "wind": "km/h"}
    now = w["current"]
    assert (now["temperature"], now["feelsLike"], now["humidity"], now["windSpeed"], now["windDirection"]) == (29.4, 33.1, 74, 14.2, 90)
    assert (now["text"], now["icon"], now["isDay"]) == ("Partly cloudy", "⛅", True)


def test_next_24_hours_start_at_the_current_hour(client):
    hourly = client.get(CHENNAI).get_json()["hourly"]
    assert len(hourly) == 24
    assert hourly[0]["time"] == "2026-11-26T14:00"
    assert hourly[-1]["time"] == "2026-11-27T13:00"
    assert set(hourly[0]) == {"time", "temperature", "precipChance"}


def test_seven_days(client):
    daily = client.get(CHENNAI).get_json()["daily"]
    assert len(daily) == 7
    assert daily[3] == {"date": "2026-11-29", "code": 61, "text": "Rain", "icon": "🌧️", "max": 28, "min": 22, "precip": 12.5,
                        "sunrise": "2026-11-29T06:12", "sunset": "2026-11-29T17:44"}
    assert [d["text"] for d in daily] == ["Clear sky", "Mainly clear", "Overcast", "Rain", "Thunderstorm", "Fog", "Rain showers"]


def test_asks_open_meteo_for_the_right_place_and_units(client, fake_weather):
    client.get(CHENNAI)
    p = fake_weather.calls[-1]["params"]
    assert fake_weather.calls[-1]["host"] == "api.open-meteo.com"
    assert (p["latitude"], p["longitude"], p["temperature_unit"], p["wind_speed_unit"], p["timezone"]) == ("13.0878", "80.2785", "celsius", "kmh", "auto")


def test_imperial_units(client, fake_weather):
    w = client.get(CHENNAI + "&units=imperial").get_json()
    assert w["units"] == {"temp": "°F", "wind": "mph"}
    p = fake_weather.calls[-1]["params"]
    assert (p["temperature_unit"], p["wind_speed_unit"]) == ("fahrenheit", "mph")


def test_answers_are_cached(client, fake_weather):
    client.get(CHENNAI)
    client.get(CHENNAI)
    assert len(fake_weather.calls) == 1
    client.get(CHENNAI + "&units=imperial")  # another question: asked again
    assert len(fake_weather.calls) == 2


def test_bad_requests(client):
    assert client.get("/api/weather?lat=95&lon=10").status_code == 400
    assert client.get("/api/weather?lat=10&lon=-181").status_code == 400
    assert client.get("/api/weather?lat=abc&lon=10").status_code == 400
    assert client.get("/api/weather?lon=10").status_code == 400
    res = client.get(CHENNAI + "&units=kelvin")
    assert res.status_code == 400
    assert "metric or imperial" in res.get_json()["error"]


def test_weather_service_down(client, fake_weather):
    fake_weather.fail = True
    res = client.get(CHENNAI)
    assert res.status_code == 502
    assert "not answering" in res.get_json()["error"]


def test_search(client, fake_weather):
    found = client.get("/api/search?q=Paris").get_json()
    assert found[0] == {"name": "Paris", "country": "France", "region": "Île-de-France", "latitude": 48.85341, "longitude": 2.3488}
    assert len(found) == 2
    assert fake_weather.calls[-1]["host"] == "geocoding-api.open-meteo.com"
    assert fake_weather.calls[-1]["params"]["name"] == "Paris"
    assert client.get("/api/search?q=P").status_code == 400


def test_weather_codes():
    assert weather.describe(0)["text"] == "Clear sky"
    assert weather.describe(3)["text"] == "Overcast"
    assert weather.describe(45)["text"] == "Fog"
    assert weather.describe(53)["text"] == "Drizzle"
    assert weather.describe(63)["text"] == "Rain"
    assert weather.describe(81)["text"] == "Rain showers"
    assert weather.describe(85)["text"] == "Snow showers"
    assert weather.describe(99)["text"] == "Thunderstorm"
    assert weather.describe(42)["text"] == "Unknown"
