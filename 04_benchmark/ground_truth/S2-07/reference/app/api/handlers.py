"""Request handlers."""

import re

from app.services import users


def handle_get_user(params: dict) -> tuple[int, dict]:
    raw = params.get("id")
    if not isinstance(raw, str) or not raw.isdigit():
        return 400, {"error": "invalid id"}
    user = users.get_user(int(raw))
    if user is None:
        return 404, {"error": "not found"}
    return 200, user


def _evaluate(text: str):
    toks = re.findall(r"\d+|[-+*/()]|\S", text)
    pos = [0]

    def peek():
        return toks[pos[0]] if pos[0] < len(toks) else None

    def take():
        tok = peek()
        pos[0] += 1
        return tok

    def expr():
        value = term()
        while peek() in ("+", "-"):
            op = take()
            right = term()
            value = value + right if op == "+" else value - right
        return value

    def term():
        value = factor()
        while peek() in ("*", "/"):
            op = take()
            right = factor()
            if op == "*":
                value = value * right
            else:
                if right == 0:
                    raise ZeroDivisionError
                value = value / right
        return value

    def factor():
        tok = take()
        if tok == "-":
            return -factor()
        if tok == "(":
            value = expr()
            if take() != ")":
                raise ValueError("expected )")
            return value
        if tok is not None and tok.isdigit():
            return int(tok)
        raise ValueError("unexpected token")

    result = expr()
    if pos[0] != len(toks):
        raise ValueError("trailing input")
    return result


def handle_calc(params: dict) -> tuple[int, dict]:
    text = params.get("expr")
    if not isinstance(text, str) or len(text) > 100:
        return 400, {"error": "invalid expression"}
    try:
        value = _evaluate(text)
    except ZeroDivisionError:
        return 400, {"error": "division by zero"}
    except ValueError:
        return 400, {"error": "invalid expression"}
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    return 200, {"result": value}
