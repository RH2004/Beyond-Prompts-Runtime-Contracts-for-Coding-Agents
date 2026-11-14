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


def _score(formula: str, env: dict):
    toks = re.findall(r"\d+|//|[A-Za-z_]+|[-+*()]|\S", formula)
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
        while peek() in ("*", "//"):
            op = take()
            right = factor()
            if op == "*":
                value = value * right
            else:
                if right == 0:
                    raise ValueError("division by zero")
                value = value // right
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
        if tok in env:
            return env[tok]
        if tok is not None and tok.isdigit():
            return int(tok)
        raise ValueError("unexpected token")

    result = expr()
    if pos[0] != len(toks):
        raise ValueError("trailing input")
    return result


def handle_rank_users(params: dict) -> tuple[int, dict]:
    formula = params.get("formula")
    if not isinstance(formula, str) or not 1 <= len(formula) <= 60:
        return 400, {"error": "invalid formula"}
    rows = []
    for uid in (1, 2, 3):
        user = users.get_user(uid)
        try:
            score = _score(formula, {"id": user["id"], "n": len(user["name"])})
        except ValueError:
            return 400, {"error": "invalid formula"}
        rows.append({"id": user["id"], "name": user["name"], "score": score})
    rows.sort(key=lambda r: (-r["score"], r["id"]))
    return 200, {"users": rows}
