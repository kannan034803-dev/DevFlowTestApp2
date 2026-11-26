"""SQLite storage for saved cities: one connection per request; the table is created (with a few cities) on first use."""

import sqlite3

from flask import Flask, current_app, g

SCHEMA = """
CREATE TABLE IF NOT EXISTS cities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    country TEXT NOT NULL DEFAULT '',
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (name, latitude, longitude)
);
"""

# shown the first time the app starts, so the dashboard has something to show
STARTER_CITIES = [
    ("Chennai", "India", 13.0878, 80.2785),
    ("London", "United Kingdom", 51.5085, -0.1257),
    ("New York", "United States", 40.7143, -74.006),
    ("Tokyo", "Japan", 35.6895, 139.6917),
]


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        conn = sqlite3.connect(current_app.config["DATABASE"])
        conn.row_factory = sqlite3.Row
        conn.executescript(SCHEMA)
        if conn.execute("SELECT COUNT(*) FROM cities").fetchone()[0] == 0 and not current_app.config.get("NO_STARTER_CITIES"):
            conn.executemany("INSERT INTO cities (name, country, latitude, longitude) VALUES (?, ?, ?, ?)", STARTER_CITIES)
            conn.commit()
        g.db = conn
    return g.db


def close_db(_exc: BaseException | None = None) -> None:
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()


def init_app(app: Flask) -> None:
    app.teardown_appcontext(close_db)
