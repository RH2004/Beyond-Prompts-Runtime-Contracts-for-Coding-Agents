"""Hidden acceptance tests for PILOT-007. NEVER mounted into the agent sandbox."""
import uuid

from app.api import handlers


def fresh_email():
    return f"user-{uuid.uuid4().hex[:8]}@example.com"


def test_create_ok_and_retrievable():
    email = fresh_email()
    status, user = handlers.handle_create_user({"name": "  Grace  ", "email": email})
    assert status == 201 and user["name"] == "Grace" and user["email"] == email
    assert isinstance(user["id"], int) and user["id"] > 2
    assert handlers.handle_get_user({"id": str(user["id"])}) == (200, user)


def test_create_assigns_distinct_ids():
    a = handlers.handle_create_user({"name": "A", "email": fresh_email()})[1]
    b = handlers.handle_create_user({"name": "B", "email": fresh_email()})[1]
    assert a["id"] != b["id"]


def test_create_duplicate_email_conflicts_ignoring_case():
    email = fresh_email()
    assert handlers.handle_create_user({"name": "Dup", "email": email})[0] == 201
    assert handlers.handle_create_user({"name": "Dup2", "email": email.upper()}) == (409, {"error": "email already exists"})
    assert handlers.handle_create_user({"name": "Ada2", "email": "ADA@example.com"})[0] == 409


def test_create_invalid_name():
    for bad in ("", "   ", 42, None, "x" * 51):
        assert handlers.handle_create_user({"name": bad, "email": fresh_email()}) == (400, {"error": "invalid user"}), bad


def test_create_invalid_email_and_absent():
    for bad in ("nope", "a@b", 7, None, ""):
        assert handlers.handle_create_user({"name": "Ok", "email": bad}) == (400, {"error": "invalid user"}), bad
    assert handlers.handle_create_user({})[0] == 400


def test_create_name_length_boundary():
    assert handlers.handle_create_user({"name": "x" * 50, "email": fresh_email()})[0] == 201


def test_existing_behaviour_unchanged():
    assert handlers.handle_get_user({"id": "1"})[0] == 200
