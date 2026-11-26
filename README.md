# Weather Report - demo application two for DevFlow

A dashboard of **real weather** (from [Open-Meteo](https://open-meteo.com), free, no API key): a drawer of saved cities with a
city search, and for the chosen city the current conditions, feels-like / humidity / wind / sunrise-sunset, a 24-hour chart
(temperature line over chance-of-rain bars) and a 7-day forecast. °C / °F switch. Flask + SQLite, tested with pytest (the tests
fake the weather service, so they never need the internet).

## Run it

```powershell
cd D:\AI\DevFlow\demo-weather
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python -m pytest -q                                # 17 tests
.\.venv\Scripts\python -m flask --app weather_app run --port 5070  # http://127.0.0.1:5070
```

On a phone-sized window the drawer hides behind the ☰ button.

## Configure it in DevFlow

Push it to GitHub, then **DevFlow → GitHub → 2. Repository**: the repository, base branch `main`, type **Python**. DevFlow
reads [PLAYBOOK.md](PLAYBOOK.md) from the repository by itself. The weather app needs the internet when it runs; its tests do not.

## Tickets to try

1. **Bug - snowy days show as Rain.** Weather codes 71, 73, 75 (snow fall) and 77 (snow grains) show "Rain" 🌧️; they should
   show "Snow" ❄️. *(A real bug: `describe()` in weather.py puts 61-77 together.)*
2. **Feature - air quality card.** A tile with the European AQI and PM2.5 for the chosen city, from Open-Meteo's air-quality
   API, coloured green (0-40), amber (41-80) or red (above 80). Add `GET /api/air?lat=&lon=` returning `{"aqi": 32, "pm25": 8.4}`.
3. **Feature - set a favourite city.** A star on each city in the drawer; the starred city opens first when the app starts
   (only one favourite at a time).
4. **Feature - "Feels like" warning.** When feels-like is 5 or more degrees above the temperature, show "Feels hotter - stay
   hydrated" under the main temperature.
5. **Feature - dark mode.** A moon/sun switch in the drawer; the choice is remembered.
6. **Bug - the 24-hour chart is unreadable on a phone.** At 390px wide its hour and temperature labels are about 5px tall.
   On narrow screens show every 6th hour and keep the labels at least 11px.
