import pytest

from conftest import BASE_URL


def get_stock(api, book_id: int) -> int:
    r = api.get(f"{BASE_URL}/api/books/{book_id}", timeout=5)
    assert r.status_code == 200, r.text
    return r.json()["data"]["stock"]


@pytest.fixture
def new_book(api, teacher_headers):
    payload = {
        "title": "pytest 测试用书",
        "author": "tester",
        "isbn": "9780000000001",
        "price": 10.00,
        "stock": 3,
    }
    r = api.post(f"{BASE_URL}/api/books", json=payload, headers=teacher_headers, timeout=5)
    assert r.status_code == 200 and r.json()["code"] == 0, r.text
    book = r.json()["data"]
    yield book
    api.delete(f"{BASE_URL}/api/books/{book['id']}", headers=teacher_headers, timeout=5)


def test_borrow_decrease_stock(api, headers, new_book):
    before = get_stock(api, new_book["id"])
    r = api.post(f"{BASE_URL}/api/books/{new_book['id']}/borrow", json={"quantity": 1}, headers=headers, timeout=5)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["code"] == 0
    assert body["data"]["stock"] == before - 1
    assert get_stock(api, new_book["id"]) == before - 1


@pytest.mark.parametrize("quantity", [0, 4, -1, "abc"])
def test_borrow_invalid_quantity(api, headers, new_book, quantity):
    r = api.post(f"{BASE_URL}/api/books/{new_book['id']}/borrow", json={"quantity": quantity}, headers=headers, timeout=5)
    assert r.status_code == 400, f"quantity={quantity!r} 未被拒绝：HTTP {r.status_code} {r.text}"
    assert r.json()["code"] != 0


def test_borrow_without_token(api, new_book):
    before = get_stock(api, new_book["id"])
    r = api.post(f"{BASE_URL}/api/books/{new_book['id']}/borrow", json={"quantity": 1}, timeout=5)
    assert r.status_code == 401, f"HTTP {r.status_code} {r.text}"
    assert get_stock(api, new_book["id"]) == before
