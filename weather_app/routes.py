"""The dashboard page and the JSON API it uses."""

from flask import Blueprint, jsonify, render_template, request

from . import cities, weather

pages = Blueprint("pages", __name__)
api = Blueprint("api", __name__, url_prefix="/api")


def error(message: str, status: int):
    return jsonify({"error": message}), status


@pages.get("/")
def index():
    return render_template("index.html")


@api.get("/cities")
def list_cities():
    return jsonify(cities.list_cities())


@api.post("/cities")
def add_city():
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return error("Send the city as JSON", 400)
    try:
        return jsonify(cities.add_city(body)), 201
    except cities.DuplicateError as exc:
        return error(str(exc), 409)
    except cities.ValidationError as exc:
        return error(str(exc), 400)


@api.delete("/cities/<int:city_id>")
def delete_city(city_id: int):
    if not cities.delete_city(city_id):
        return error("City not found", 404)
    return "", 204


@api.get("/search")
def search():
    q = (request.args.get("q") or "").strip()
    if len(q) < 2:
        return error("Type at least 2 letters", 400)
    try:
        return jsonify(weather.search(q[:80]))
    except weather.WeatherServiceError:
        return error("The weather service is not answering - try again in a moment", 502)


@api.get("/weather")
def get_weather():
    units = request.args.get("units", "metric")
    if units not in weather.UNITS:
        return error("units must be metric or imperial", 400)
    try:
        lat = cities.coordinate(request.args.get("lat"), -90, 90, "lat")
        lon = cities.coordinate(request.args.get("lon"), -180, 180, "lon")
    except cities.ValidationError as exc:
        return error(str(exc), 400)
    try:
        return jsonify(weather.forecast(lat, lon, units))
    except weather.WeatherServiceError:
        return error("The weather service is not answering - try again in a moment", 502)
