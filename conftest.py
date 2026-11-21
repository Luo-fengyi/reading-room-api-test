import pytest
import requests

BASE_URL = "http://127.0.0.1:5000"

STUDENT = {"username": "student", "password": "123456"}
TEACHER = {"username": "teacher", "password": "abc123"}


@pytest.fixture(scope="session")
def api():
    with requests.Session() as s:
        s.headers.update({"Content-Type": "application/json"})
        yield s


def _login(api: requests.Session, account: dict) -> str:
    r = api.post(f"{BASE_URL}/api/login", json=account, timeout=5)
    assert r.status_code == 200, f"登录失败：HTTP {r.status_code} {r.text}"
    body = r.json()
    assert body.get("code") == 0, f"登录业务失败：{body}"
    return body["data"]["token"]


@pytest.fixture(scope="session")
def token(api):
    return _login(api, STUDENT)


@pytest.fixture(scope="session")
def headers(token):
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="session")
def teacher_headers(api):
    return {"Authorization": f"Bearer {_login(api, TEACHER)}"}
