"""Hidden acceptance tests for PILOT-001. NEVER mounted into the agent sandbox."""
from app.api import handlers


def test_by_email_ok():
    assert handlers.handle_get_user_by_email({"email": "linus@example.com"}) == (
        200, {"id": 2, "name": "Linus", "email": "linus@example.com"})


def test_by_email_missing():
    assert handlers.handle_get_user_by_email({"email": "nobody@example.com"})[0] == 404


def test_by_email_invalid_type():
    assert handlers.handle_get_user_by_email({"email": 42})[0] == 400


def test_by_email_invalid_format():
    assert handlers.handle_get_user_by_email({"email": "not-an-email"})[0] == 400


def test_by_email_absent():
    assert handlers.handle_get_user_by_email({})[0] == 400


def test_existing_behaviour_unchanged():
    assert handlers.handle_get_user({"id": "1"})[0] == 200
