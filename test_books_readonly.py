import pytest

from conftest import BASE_URL


# ---------- GET /api/books：page / size 的边界与非法值 ----------
BOOKS_PAGE_CASES = [
    pytest.param({}, 200, 0, "ok", id="default-page-size"),
    pytest.param({"page": 1, "size": 1}, 200, 0, "ok", id="page=1,size=1"),
    pytest.param({"page": 1, "size": 5}, 200, 0, "ok", id="page=1,size=5"),
    pytest.param({"page": 2, "size": 5}, 200, 0, "ok", id="page=2,size=5"),
    pytest.param({"page": 1, "size": 100}, 200, 0, "ok", id="size>total"),
    pytest.param({"page": 9999, "size": 5}, 200, 0, "empty", id="page-out-of-range"),
    pytest.param({"page": 0, "size": 5}, 200, None, "none", id="page=0"),
    pytest.param({"page": -1, "size": 5}, 200, None, "none", id="page=-1"),
    pytest.param({"page": "abc", "size": 5}, 200, None, "none", id="page=abc"),
    pytest.param({"page": "1.5", "size": 5}, 200, None, "none", id="page=1.5"),
    pytest.param({"page": 1, "size": 0}, 200, None, "none", id="size=0"),
    pytest.param({"page": 1, "size": -5}, 200, None, "none", id="size=-5"),
    pytest.param({"page": 1, "size": "abc"}, 200, None, "none", id="size=abc"),
    pytest.param({"page": 1, "size": "1.5"}, 200, None, "none", id="size=1.5"),
]


@pytest.mark.parametrize("params, exp_status, exp_code, data_kind", BOOKS_PAGE_CASES)
def test_books_list_page_and_size(api, params, exp_status, exp_code, data_kind):
    r = api.get(f"{BASE_URL}/api/books", params=params, timeout=5)
    body = r.json()

    assert r.status_code == exp_status, r.text
    if exp_code is None:
        assert body["code"] != 0, body
        assert isinstance(body["message"], str) and body["message"], body
    else:
        assert body["code"] == exp_code, body

    if data_kind == "ok":
        data = body["data"]
        assert isinstance(data["items"], list), data
        assert data["page"] == int(params.get("page", 1)), data
        assert data["size"] == int(params.get("size", 5)), data
        assert len(data["items"]) <= data["size"], data
    elif data_kind == "empty":
        assert body["data"]["items"] == [], body
    else:
        assert body["data"] is None, body


# ---------- GET /api/books/<id>：不存在的 id ----------
@pytest.mark.parametrize(
    "book_id",
    [
        pytest.param(999, id="id=999"),
        pytest.param(10000, id="id=10000"),
        pytest.param(0, id="id=0"),
    ],
)
def test_book_detail_not_found(api, book_id):
    r = api.get(f"{BASE_URL}/api/books/{book_id}", timeout=5)
    body = r.json()

    assert r.status_code == 200, r.text
    assert body["code"] == 1, body
    assert body["message"] == "图书不存在", body
    assert body["data"] is None, body
