"""Saved cities (the drawer's list): validation and queries."""

import sqlite3

from .db import get_db


class ValidationError(ValueError):
    pass


class DuplicateError(ValueError):
    pass


def to_dict(row) -> dict:
    return {"id": row["id"], "name": row["name"], "country": row["country"], "latitude": row["latitude"], "longitude": row["longitude"]}


def list_cities() -> list[dict]:
    return [to_dict(r) for r in get_db().execute("SELECT * FROM cities ORDER BY id").fetchall()]


def get_city(city_id: int) -> dict | None:
    row = get_db().execute("SELECT * FROM cities WHERE id = ?", (city_id,)).fetchone()
    return to_dict(row) if row else None


def coordinate(value: object, low: float, high: float, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        raise ValidationError(f"{name} must be a number")
    try:
        number = float(value)
    except ValueError as exc:
        raise ValidationError(f"{name} must be a number") from exc
    if not low <= number <= high:
        raise ValidationError(f"{name} must be between {low:g} and {high:g}")
    return number


def add_city(body: dict) -> dict:
    name = body.get("name")
    if not isinstance(name, str) or not name.strip() or len(name.strip()) > 100:
        raise ValidationError("name is required (at most 100 characters)")
    country = body.get("country") or ""
    if not isinstance(country, str) or len(country) > 100:
        raise ValidationError("country must be text (at most 100 characters)")
    lat = coordinate(body.get("latitude"), -90, 90, "latitude")
    lon = coordinate(body.get("longitude"), -180, 180, "longitude")
    db = get_db()
    try:
        cur = db.execute("INSERT INTO cities (name, country, latitude, longitude) VALUES (?, ?, ?, ?)",
                         (name.strip(), country.strip(), round(lat, 4), round(lon, 4)))
    except sqlite3.IntegrityError as exc:
        raise DuplicateError(f"{name.strip()} is already in your list") from exc
    db.commit()
    return get_city(cur.lastrowid)


def delete_city(city_id: int) -> bool:
    db = get_db()
    cur = db.execute("DELETE FROM cities WHERE id = ?", (city_id,))
    db.commit()
    return cur.rowcount > 0
