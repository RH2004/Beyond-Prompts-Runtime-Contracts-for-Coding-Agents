from app.api.handlers import handle_get_user


def test_get_user_ok():
    assert handle_get_user({"id": "1"}) == (200, {"id": 1, "name": "Ada Lovelace", "email": "ada@example.com"})


def test_get_user_invalid():
    assert handle_get_user({"id": "abc"})[0] == 400


def test_get_user_missing():
    assert handle_get_user({"id": "99"})[0] == 404
