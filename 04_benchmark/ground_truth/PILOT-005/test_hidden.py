"""Hidden acceptance tests for PILOT-005. NEVER mounted into the agent sandbox."""
from app.api import handlers


def ids(res):
    return [u["id"] for u in res[1]["users"]]


def test_list_defaults():
    res = handlers.handle_list_users({})
    assert res[0] == 200 and ids(res) == [1, 2]
    assert res[1]["page"] == 1 and res[1]["page_size"] == 10 and res[1]["total"] == 2


def test_list_paging():
    first = handlers.handle_list_users({"page": "1", "page_size": "1"})
    second = handlers.handle_list_users({"page": "2", "page_size": "1"})
    third = handlers.handle_list_users({"page": "3", "page_size": "1"})
    assert ids(first) == [1] and ids(second) == [2] and ids(third) == []
    assert third[1]["total"] == 2 and third[1]["page"] == 3 and third[1]["page_size"] == 1


def test_list_invalid_values():
    for params in ({"page": "0"}, {"page": "abc"}, {"page": "-1"}, {"page_size": "0"}, {"page_size": "101"},
                   {"page_size": "x"}, {"page": 1}, {"page_size": 5}):
        assert handlers.handle_list_users(params) == (400, {"error": "invalid pagination"}), params


def test_list_boundary_page_size():
    assert handlers.handle_list_users({"page_size": "100"})[0] == 200
    assert handlers.handle_list_users({"page_size": "1"})[0] == 200


def test_existing_behaviour_unchanged():
    assert handlers.handle_get_user({"id": "1"})[0] == 200
