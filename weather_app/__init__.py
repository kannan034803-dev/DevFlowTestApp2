"""Weather Report - demo application two for DevFlow.

A dashboard with a drawer of saved cities and real weather from Open-Meteo (free, no API key): current conditions, the next
24 hours as a chart and a 7-day forecast. Saved cities are kept in SQLite.
Run:  python -m flask --app weather_app run --port 5070
"""

from pathlib import Path

from flask import Flask

from . import db
from .routes import api, pages


def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(DATABASE=str(Path(app.instance_path) / "weather.sqlite"), CACHE_SECONDS=600)
    if test_config:
        app.config.update(test_config)
    Path(app.config["DATABASE"]).parent.mkdir(parents=True, exist_ok=True)

    db.init_app(app)
    app.register_blueprint(pages)
    app.register_blueprint(api)

    @app.get("/health")
    def health() -> dict:
        return {"ok": True}

    return app
