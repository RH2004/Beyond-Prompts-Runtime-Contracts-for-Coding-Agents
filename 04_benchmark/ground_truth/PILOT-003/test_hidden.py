"""Hidden acceptance tests for PILOT-003. NEVER mounted into the agent sandbox."""
from app.api import handlers


def test_validate_ok():
    assert handlers.handle_validate_email({"email": "ada@example.com"}) == (200, {"valid": True, "email": "ada@example.com"})


def test_validate_normalises_domain_only():
    assert handlers.handle_validate_email({"email": "Ada.B+tag@SUB.Example.ORG"}) == (
        200, {"valid": True, "email": "Ada.B+tag@sub.example.org"})


def test_validate_invalid_formats():
    for bad in ("not-an-email", "a@b", "ada@@example.com", "a b@example.com", "@example.com", "ada@", ""):
        assert handlers.handle_validate_email({"email": bad}) == (400, {"valid": False, "error": "invalid email"}), bad


def test_validate_invalid_type_and_absent():
    assert handlers.handle_validate_email({"email": 42})[0] == 400
    assert handlers.handle_validate_email({"email": None})[0] == 400
    assert handlers.handle_validate_email({})[0] == 400


def test_existing_behaviour_unchanged():
    assert handlers.handle_get_user({"id": "1"})[0] == 200
