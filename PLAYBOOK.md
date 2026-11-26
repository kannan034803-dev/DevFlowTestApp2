PROJECT: Weather Report - a Flask web app (Python 3.12): a dashboard of REAL weather from Open-Meteo (free, no API key) with
a drawer of saved cities. Demo application two for DevFlow.
- Where things are: weather_app/__init__.py (create_app), weather_app/weather.py (ALL Open-Meteo calls: fetch_json, the
  10-minute cache, describe(code) for WMO weather codes, search(), forecast() which shapes the answer), weather_app/cities.py
  (saved cities: validation + SQL), weather_app/routes.py (page + JSON API under /api, kept thin), weather_app/db.py (SQLite,
  starter cities), templates/index.html (the dashboard: drawer + main area), static/app.js (plain JavaScript: drawer, search,
  rendering, the inline-SVG 24-hour chart), static/style.css (CSS variables in :root; the drawer slides in under 900px).
- API: GET /api/cities, POST /api/cities, DELETE /api/cities/<id>, GET /api/search?q=, GET /api/weather?lat=&lon=&units=metric|imperial.
  Errors are JSON {"error": "..."}: 400 bad input, 404 missing, 409 duplicate, 502 when Open-Meteo does not answer.
  JSON keys are camelCase (feelsLike, precipChance, windSpeed).
- New weather data: add the Open-Meteo variable to the request in weather.forecast() and the field to its result; other
  Open-Meteo APIs (air quality: https://air-quality-api.open-meteo.com/v1/air-quality) go through fetch_json and _cached too.
- Code rules: keep the existing style; type hints on new functions; no new dependencies (urllib, no requests); the page stays
  plain HTML/CSS/JS - no frameworks, no chart libraries; build DOM with textContent / createElement (never innerHTML with data);
  colours via the CSS variables; the layout must still work at 390px wide (drawer closed, menu button).
- Tests: pytest in tests/. NEVER call the real internet in tests: the fake_weather fixture (conftest.py) replaces
  weather.fetch_json and records every call (fake_weather.calls - host and query params); change forecast_payload() /
  GEOCODE there when a test needs other data. For every acceptance criterion add or update a test; a test must fail without
  the change. Run: python -m pytest -q
- Never touch: requirements.txt pins unless the plan says so, the instance/ folder, .venv.
