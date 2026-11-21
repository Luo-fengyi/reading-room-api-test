import pytest

from conftest import BASE_URL


def _assert_rejected(r, expected_statuses):
    assert r.status_code in expected_statuses, f"HTTP {r.status_code} {r.text}"
    if "application/json" in r.headers.get("Content-Type", ""):
        body = r.json()
        assert body.get("code", 0) != 0, body
        assert body.get("data") is None, body


# ---------- 错误密码登录 ----------
def test_login_wrong_password(api):
    r = api.post(f"{BASE_URL}/api/login", json={"username": "student", "password": "wrong-pass"}, timeout=5)
    body = r.json()
    assert body["code"] != 0, body
    assert body["message"] == "用户名或密码错误", body
    assert body["data"] is None


# ---------- 1. 假 token ----------
FAKE_TOKEN_HEADERS = [
    pytest.param({"Authorization": "Bearer faketoken123"}, id="faketoken123"),
    pytest.param({"Authorization": "Bearer " + "0" * 32}, id="zeros-32"),
]


@pytest.mark.parametrize("headers", FAKE_TOKEN_HEADERS)
def test_fake_token_rejected(api, headers):
    r = api.get(f"{BASE_URL}/api/borrows", headers=headers, timeout=5)
    _assert_rejected(r, (401,))


# ---------- 2. 无 token ----------
PROTECTED_ENDPOINTS = [
    pytest.param("GET", "/api/borrows", None, id="get-borrows"),
    pytest.param("POST", "/api/books/999999/borrow", {"quantity": 1}, id="borrow-nonexistent"),
    pytest.param("DELETE", "/api/books/999999", None, id="delete-nonexistent"),
    pytest.param("POST", "/api/books", {"title": "x", "stock": 1}, id="create-book"),
]


@pytest.mark.parametrize("method, path, payload", PROTECTED_ENDPOINTS)
def test_missing_token_rejected(api, method, path, payload):
    kwargs = {"timeout": 5}
    if payload is not None:
        kwargs["json"] = payload
    r = api.request(method, f"{BASE_URL}{path}", **kwargs)
    _assert_rejected(r, (401,))


# ---------- 3. 错误 HTTP 方法 ----------
WRONG_METHODS = [
    pytest.param("PUT", "/api/books/1/borrow", id="put-borrow"),
    pytest.param("DELETE", "/api/books/1/borrow", id="delete-borrow"),
    pytest.param("POST", "/api/books/1", id="post-detail"),
    pytest.param("GET", "/api/login", id="get-login"),
]


@pytest.mark.parametrize("method, path", WRONG_METHODS)
def test_wrong_method_rejected(api, headers, method, path):
    r = api.request(method, f"{BASE_URL}{path}", headers=headers, timeout=5)
    _assert_rejected(r, (405,))


# ---------- 4. 非法 id ----------
INVALID_IDS = [
    pytest.param("GET", "/api/books/abc", None, id="get-abc"),
    pytest.param("POST", "/api/books/abc/borrow", {"quantity": 1}, id="borrow-abc"),
    pytest.param("GET", "/api/books/-1", None, id="get-negative"),
]


@pytest.mark.parametrize("method, path, payload", INVALID_IDS)
def test_invalid_book_id_rejected(api, headers, method, path, payload):
    kwargs = {"headers": headers, "timeout": 5}
    if payload is not None:
        kwargs["json"] = payload
    r = api.request(method, f"{BASE_URL}{path}", **kwargs)

    assert r.status_code < 500, f"HTTP {r.status_code} {r.text}"

    if r.status_code in (400, 404, 422):
        return
    assert "application/json" in r.headers.get("Content-Type", ""), r.text
    body = r.json()
    assert body.get("code", 0) != 0, body
    assert body.get("data") is None, body
