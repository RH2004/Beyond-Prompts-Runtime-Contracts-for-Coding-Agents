"""Hidden acceptance tests for PILOT-008. NEVER mounted into the agent sandbox."""
from app.api import handlers


def ids(res):
    return [u["id"] for u in res[1]["users"]]


def test_search_by_name_case_insensitive():
    res = handlers.handle_search_users({"q": "aDa"})
    assert res[0] == 200 and ids(res) == [1]


def test_search_by_email_and_trim():
    assert ids(handlers.handle_search_users({"q": "  LINUS@ex  "})) == [2]
    assert ids(handlers.handle_search_users({"q": "example.com"})) == [1, 2]


def test_search_no_match():
    assert handlers.handle_search_users({"q": "zzz"}) == (200, {"users": []})


def test_search_returns_full_users():
    assert handlers.handle_search_users({"q": "ada"}) == (200, {"users": [{"id": 1, "name": "Ada", "email": "ada@example.com"}]})


def test_search_invalid_query():
    for bad in ("", "   ", 5, None):
        assert handlers.handle_search_users({"q": bad}) == (400, {"error": "invalid query"}), bad
    assert handlers.handle_search_users({})[0] == 400


def test_existing_behaviour_unchanged():
    assert handlers.handle_get_user({"id": "1"})[0] == 200
