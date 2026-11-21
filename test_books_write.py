import uuid

import pytest

from conftest import BASE_URL


# ---------- 辅助 ----------

def get_stock(api, book_id):
    r = api.get(f"{BASE_URL}/api/books/{book_id}", timeout=5)
    body = r.json()
    assert r.status_code == 200, r.text
    assert body["code"] == 0, body
    return body["data"]["stock"]


@pytest.fixture
def make_book(api, teacher_headers):
    created = []

    def _make(**overrides):
        payload = {
            "title": f"测试书-{uuid.uuid4().hex[:8]}",
            "author": "测试作者",
            "isbn": "",
            "price": 12.34,
            "stock": 3,
        }
        payload.update(overrides)
        r = api.post(f"{BASE_URL}/api/books", json=payload, headers=teacher_headers, timeout=5)
        body = r.json()
        assert r.status_code == 200 and body["code"] == 0, body
        created.append(body["data"])
        return body["data"]

    yield _make

    for b in created:
        api.delete(f"{BASE_URL}/api/books/{b['id']}", headers=teacher_headers, timeout=5)


@pytest.fixture
def new_book(make_book):
    return make_book()


# ---------- POST /api/books 新增 ----------

def test_create_book_ok(api, teacher_headers):
    payload = {
        "title": f"新书-{uuid.uuid4().hex[:8]}",
        "author": "作者甲",
        "isbn": "9780000000001",
        "price": 59.00,
        "stock": 2,
    }
    r = api.post(f"{BASE_URL}/api/books", json=payload, headers=teacher_headers, timeout=5)
    body = r.json()
    try:
        assert r.status_code == 200, r.text
        assert body["code"] == 0, body
        data = body["data"]
        assert isinstance(data["id"], int)
        assert data["title"] == payload["title"]
        assert data["price"] == 59.0
        assert data["stock"] == 2
        assert data["total"] == 2
    finally:
        if body.get("code") == 0:
            api.delete(f"{BASE_URL}/api/books/{body['data']['id']}", headers=teacher_headers)


@pytest.mark.parametrize(
    "title",
    ["", "   ", "测" * 101],
    ids=["empty", "blank", "len-101"],
)
def test_create_book_invalid_title(api, teacher_headers, title):
    payload = {"title": title, "author": "x", "isbn": "", "price": 1.00, "stock": 1}
    r = api.post(f"{BASE_URL}/api/books", json=payload, headers=teacher_headers, timeout=5)
    body = r.json()
    try:
        assert r.status_code == 200, r.text
        assert body["code"] != 0, body
        assert isinstance(body["message"], str) and body["message"], body
        assert body["data"] is None, body
    finally:
        if body.get("code") == 0 and isinstance(body.get("data"), dict):
            api.delete(f"{BASE_URL}/api/books/{body['data']['id']}", headers=teacher_headers)


# ---------- PUT /api/books/<id> 修改 ----------

def test_update_book_ok(api, teacher_headers, new_book):
    book_id = new_book["id"]
    r = api.put(
        f"{BASE_URL}/api/books/{book_id}",
        json={"price": 49.90, "stock": 5},
        headers=teacher_headers,
        timeout=5,
    )
    body = r.json()
    assert r.status_code == 200, r.text
    assert body["code"] == 0, body
    data = body["data"]
    assert data["id"] == book_id
    assert data["price"] == 49.9
    assert data["stock"] == 5
    g = api.get(f"{BASE_URL}/api/books/{book_id}", timeout=5).json()
    assert g["code"] == 0, g
    assert g["data"]["price"] == 49.9
    assert g["data"]["stock"] == 5


def test_update_book_not_found(api, teacher_headers):
    r = api.put(
        f"{BASE_URL}/api/books/999999",
        json={"price": 1.00},
        headers=teacher_headers,
        timeout=5,
    )
    body = r.json()
    assert r.status_code == 200, r.text
    assert body["code"] != 0, body
    assert body["data"] is None, body


# ---------- DELETE /api/books/<id> 删除 ----------

def test_delete_own_book_ok(api, teacher_headers, new_book):
    book_id = new_book["id"]
    r = api.delete(f"{BASE_URL}/api/books/{book_id}", headers=teacher_headers, timeout=5)
    body = r.json()
    assert r.status_code == 200, r.text
    assert body["code"] == 0, body
    assert body["data"] is None, body
    g = api.get(f"{BASE_URL}/api/books/{book_id}", timeout=5).json()
    assert g["code"] != 0, g
    assert g["data"] is None, g


def test_delete_book_not_found(api, teacher_headers):
    r = api.delete(f"{BASE_URL}/api/books/999999", headers=teacher_headers, timeout=5)
    body = r.json()
    assert r.status_code == 200, r.text
    assert body["code"] != 0, body
    assert body["data"] is None, body


# ---------- POST /api/books/<id>/borrow 借 ----------

def test_borrow_out_of_stock(api, teacher_headers, make_book):
    book = make_book(stock=0)
    book_id = book["id"]
    assert get_stock(api, book_id) == 0

    r = api.post(
        f"{BASE_URL}/api/books/{book_id}/borrow",
        json={"quantity": 1},
        headers=teacher_headers,
        timeout=5,
    )
    body = r.json()
    assert r.status_code == 200, r.text
    assert body["code"] != 0, body
    assert body["data"] is None, body
    assert get_stock(api, book_id) == 0


# ---------- POST /api/books/<id>/return 还 ----------

def test_return_after_borrow_restores_stock(api, teacher_headers, new_book):
    book_id = new_book["id"]
    before = get_stock(api, book_id)

    rb = api.post(
        f"{BASE_URL}/api/books/{book_id}/borrow",
        json={"quantity": 1},
        headers=teacher_headers,
        timeout=5,
    )
    bb = rb.json()
    assert rb.status_code == 200, rb.text
    assert bb["code"] == 0, bb
    assert bb["data"]["quantity"] == 1
    assert get_stock(api, book_id) == before - 1

    rr = api.post(
        f"{BASE_URL}/api/books/{book_id}/return",
        json={"quantity": 1},
        headers=teacher_headers,
        timeout=5,
    )
    rb_body = rr.json()
    assert rr.status_code == 200, rr.text
    assert rb_body["code"] == 0, rb_body
    assert rb_body["data"]["quantity"] == 1
    assert get_stock(api, book_id) == before


def test_return_exceed_borrowed_quantity(api, teacher_headers, new_book):
    book_id = new_book["id"]
    before = get_stock(api, book_id)

    rb = api.post(
        f"{BASE_URL}/api/books/{book_id}/borrow",
        json={"quantity": 1},
        headers=teacher_headers,
        timeout=5,
    )
    assert rb.json()["code"] == 0, rb.text
    assert get_stock(api, book_id) == before - 1

    rr = api.post(
        f"{BASE_URL}/api/books/{book_id}/return",
        json={"quantity": 2},
        headers=teacher_headers,
        timeout=5,
    )
    body = rr.json()
    assert rr.status_code == 200, rr.text
    assert body["code"] != 0, body
    assert body["data"] is None, body
    assert get_stock(api, book_id) == before - 1

    api.post(
        f"{BASE_URL}/api/books/{book_id}/return",
        json={"quantity": 1},
        headers=teacher_headers,
        timeout=5,
    )
    assert get_stock(api, book_id) == before
