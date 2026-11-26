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
    assert client.get("/static/app.js").status_code == 200
