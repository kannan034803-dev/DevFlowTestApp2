"""The drawer's saved cities."""

PARIS = {"name": "Paris", "country": "France", "latitude": 48.85341, "longitude": 2.3488}


def test_starts_with_a_few_cities(client):
    names = [c["name"] for c in client.get("/api/cities").get_json()]
    assert names == ["Chennai", "London", "New York", "Tokyo"]


def test_add_city(client):
    res = client.post("/api/cities", json=PARIS)
    assert res.status_code == 201
    city = res.get_json()
    assert (city["name"], city["country"], city["latitude"], city["longitude"]) == ("Paris", "France", 48.8534, 2.3488)
    assert client.get("/api/cities").get_json()[-1]["name"] == "Paris"


def test_same_city_twice_is_refused(client):
    client.post("/api/cities", json=PARIS)
    res = client.post("/api/cities", json=PARIS)
    assert res.status_code == 409
    assert "already" in res.get_json()["error"]


def test_city_validation(client):
    assert client.post("/api/cities", json={**PARIS, "name": " "}).status_code == 400
    assert client.post("/api/cities", json={**PARIS, "latitude": 91}).status_code == 400
    assert client.post("/api/cities", json={**PARIS, "longitude": "east"}).status_code == 400
    assert client.post("/api/cities", json={**PARIS, "latitude": True}).status_code == 400
    assert client.post("/api/cities", data="not json").status_code == 400


def test_delete_city(client):
    first = client.get("/api/cities").get_json()[0]
    assert client.delete(f"/api/cities/{first['id']}").status_code == 204
    assert first["id"] not in [c["id"] for c in client.get("/api/cities").get_json()]
    assert client.delete(f"/api/cities/{first['id']}").status_code == 404


def test_no_starter_cities_when_switched_off(tmp_path, fake_weather):
    from weather_app import create_app
    app = create_app({"TESTING": True, "DATABASE": str(tmp_path / "empty.sqlite"), "NO_STARTER_CITIES": True})
    assert app.test_client().get("/api/cities").get_json() == []


def test_dashboard_page(client):
    html = client.get("/").get_data(as_text=True)
    assert 'id="drawer"' in html
    assert 'id="city-list"' in html
    assert 'id="chart"' in html
    assert "app.js" in html
    assert "<b>Weather Report</b>" in html
    assert "real data" not in html
    assert client.get("/static/app.js").status_code == 200


def test_dashboard_is_green(client):
    response = client.get("/static/style.css")
    assert response.status_code == 200
    css = response.get_data(as_text=True)
    # header (hero card)
    assert "--accent: #16a34a" in css
    assert "--accent-deep: #166534" in css
    assert "linear-gradient(135deg, var(--accent), var(--accent-deep))" in css
    # drawer
    assert "--drawer: #15803d" in css
    assert "--drawer-muted: #c8f0d6" in css
    assert "background: var(--drawer);" in css
    assert ".city.active { background: var(--drawer-active)" in css
    assert "border: 1px solid var(--drawer-line); background: var(--drawer-field)" in css
    assert ".search input::placeholder" in css
    # buttons
    assert ".unit.on { background: var(--card)" in css
    assert "color: var(--accent-deep)" in css
    assert "--accent-tint: #dcfce7" in css
    # chart (colour lives in CSS, not in app.js)
    assert ".chart .rain-bar { fill: rgba(21, 128, 61, .30)" in css
    assert "--rain: #15803d" in css
    js = client.get("/static/app.js").get_data(as_text=True)
    assert "#" not in js
    assert "rgb" not in js
    # no blue left
    for blue in ("#3b82f6", "#1e40af", "#1d4ed8", "#c7dbff", "#e2ecff", "#2f80d1", "47, 128, 209",
                 "#0d1b3d", "#2a4c8f", "#eef4fd", "#d4e1f5", "#f5f9ff", "#14213a", "#56688a"):
        assert blue not in css
    # no pink left
    for pink in ("#ff69b4", "#d63384", "#e0287d", "#e0479e", "#ffe4f1", "#fff5fa", "#ffd6ea",
                 "#fdf0f6", "#f3d3e3", "#2b1524", "#7a5468", "#3a0f2a", "#7a2a5c", "224, 71, 158"):
        assert pink not in css
    # 390px: drawer closed with a menu button, and it still slides in under 900px
    assert "@media (max-width: 900px)" in css
    assert ".menu { display: block; }" in css
    assert ".dashboard { grid-template-columns: 1fr; }" in css
    assert "@media (max-width: 480px)" in css
    assert "transform: translateX(-100%)" in css
    assert ".drawer.open { transform: translateX(0); }" in css
    for old in ("#2f6fed", "#6ea8ff", "#101a2e", "#dbe4f3", "#8fa0bd", "#2a3a5a", "#18243d",
                "#22345a", "#edf2fd", "#3b9be8", "#1b2747", "#3f4f86", "#eef2f7", "#172033",
                "#f6f8fc", "59, 155, 232"):
        assert old not in css
