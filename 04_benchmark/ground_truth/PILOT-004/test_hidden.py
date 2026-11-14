"""Hidden acceptance tests for PILOT-004. NEVER mounted into the agent sandbox."""
from app.api import handlers


def test_exists_true():
    assert handlers.handle_user_exists({"id": "1"}) == (200, {"exists": True})
    assert handlers.handle_user_exists({"id": "2"}) == (200, {"exists": True})


def test_exists_false():
    assert handlers.handle_user_exists({"id": "99"}) == (200, {"exists": False})


def test_exists_invalid_id():
    for bad in ("abc", "-1", "1.5", ""):
        assert handlers.handle_user_exists({"id": bad}) == (400, {"error": "invalid id"}), bad


def test_exists_invalid_type_and_absent():
    assert handlers.handle_user_exists({"id": 1})[0] == 400
    assert handlers.handle_user_exists({})[0] == 400


def test_existing_behaviour_unchanged():
    assert handlers.handle_get_user({"id": "1"})[0] == 200
