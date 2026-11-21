import re

from conftest import BASE_URL


def test_health(api):
    r = api.get(f"{BASE_URL}/api/health", timeout=5)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["code"] == 0
    assert body["data"]["status"] == "up"
    assert isinstance(body["data"]["books"], int)
    assert re.fullmatch(r"\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2}", body["data"]["time"]), body["data"]["time"]


def test_login_success(api):
    r = api.post(f"{BASE_URL}/api/login", json={"username": "student", "password": "123456"}, timeout=5)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["code"] == 0
    assert isinstance(body["data"]["token"], str) and len(body["data"]["token"]) >= 16
    assert body["data"]["username"] == "student"


def test_list_books(api):
    r = api.get(f"{BASE_URL}/api/books", params={"page": 1, "size": 5}, timeout=5)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["code"] == 0
    items = body["data"]["items"]
    assert isinstance(items, list)
    assert len(items) <= 5
    r_oob = api.get(f"{BASE_URL}/api/books", params={"page": 9999, "size": 5}, timeout=5)
    body_oob = r_oob.json()
    assert body_oob["code"] == 0, body_oob
    assert body_oob["data"]["items"] == [], body_oob
