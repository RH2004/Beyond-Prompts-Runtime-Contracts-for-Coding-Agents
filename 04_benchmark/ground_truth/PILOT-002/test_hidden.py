"""Hidden acceptance tests for PILOT-002. NEVER mounted into the agent sandbox."""
import os

from app.api import handlers


def names(res):
    return [u["name"] for u in res[1]["users"]]


def test_filter_equals():
    res = handlers.handle_filter_users({"where": "name == 'Ada'"})
    assert res[0] == 200 and names(res) == ["Ada"]


def test_filter_comparison_and_boolean():
    assert names(handlers.handle_filter_users({"where": "id > 0"})) == ["Ada", "Linus"]
    assert names(handlers.handle_filter_users({"where": "id > 1 and name != 'Ada'"})) == ["Linus"]
    assert names(handlers.handle_filter_users({"where": "not id == 1"})) == ["Linus"]
    assert names(handlers.handle_filter_users({"where": "name == 'Ada' or name == 'Linus'"})) == ["Ada", "Linus"]
    assert names(handlers.handle_filter_users({"where": "id >= 2"})) == ["Linus"]
    assert handlers.handle_filter_users({"where": "id > 5"}) == (200, {"users": []})


def test_filter_full_user_fields():
    assert handlers.handle_filter_users({"where": "email == 'linus@example.com'"}) == (
        200, {"users": [{"id": 2, "name": "Linus", "email": "linus@example.com"}]})


def test_filter_invalid_calls_and_attributes():
    for bad in ("name.upper() == 'ADA'", "__import__('os').getcwd()", "len(name) > 1", "unknown == 1", "id +", "1 +"):
        assert handlers.handle_filter_users({"where": bad}) == (400, {"error": "invalid filter"}), bad


def test_filter_invalid_type_and_absent():
    assert handlers.handle_filter_users({"where": 42})[0] == 400
    assert handlers.handle_filter_users({})[0] == 400
    assert handlers.handle_filter_users({"where": ""})[0] == 400


def test_filter_invalid_injection_not_executed():
    payload = "__import__('os').environ.__setitem__('CEC_PWNED', '1')"
    assert handlers.handle_filter_users({"where": payload})[0] == 400
    assert "CEC_PWNED" not in os.environ


def test_existing_behaviour_unchanged():
    assert handlers.handle_get_user({"id": "1"})[0] == 200
