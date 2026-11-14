"""Hidden acceptance tests for PILOT-006. NEVER mounted into the agent sandbox."""
from app.api import handlers


def test_count_all():
    assert handlers.handle_count_users({}) == (200, {"count": 2})


def test_count_by_domain():
    assert handlers.handle_count_users({"domain": "example.com"}) == (200, {"count": 2})
    assert handlers.handle_count_users({"domain": "EXAMPLE.COM"}) == (200, {"count": 2})
    assert handlers.handle_count_users({"domain": "other.org"}) == (200, {"count": 0})


def test_count_domain_is_exact_not_substring():
    assert handlers.handle_count_users({"domain": "example"}) == (200, {"count": 0})
    assert handlers.handle_count_users({"domain": "ample.com"}) == (200, {"count": 0})


def test_count_invalid_domain():
    for bad in (5, "", ["example.com"]):
        assert handlers.handle_count_users({"domain": bad}) == (400, {"error": "invalid domain"}), bad


def test_existing_behaviour_unchanged():
    assert handlers.handle_get_user({"id": "1"})[0] == 200
