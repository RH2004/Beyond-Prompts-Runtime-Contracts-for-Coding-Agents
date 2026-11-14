"""User service: business logic between the api and db layers."""

import ast
import operator

from app.db import store

_COMPARE = {ast.Eq: operator.eq, ast.NotEq: operator.ne, ast.Lt: operator.lt, ast.LtE: operator.le,
            ast.Gt: operator.gt, ast.GtE: operator.ge}
_FIELDS = {"id", "name", "email"}


class InvalidFilter(ValueError):
    """The filter expression is outside the supported grammar."""


def get_user(user_id: int) -> dict | None:
    return store.get_by_id(user_id)


def _evaluate(node, user):
    if isinstance(node, ast.Expression):
        return _evaluate(node.body, user)
    if isinstance(node, ast.BoolOp):
        values = [_evaluate(v, user) for v in node.values]
        return all(values) if isinstance(node.op, ast.And) else any(values)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
        return not _evaluate(node.operand, user)
    if isinstance(node, ast.Compare) and len(node.ops) == 1 and type(node.ops[0]) in _COMPARE:
        return _COMPARE[type(node.ops[0])](_evaluate(node.left, user), _evaluate(node.comparators[0], user))
    if isinstance(node, ast.Name) and node.id in _FIELDS:
        return user[node.id]
    if isinstance(node, ast.Constant) and isinstance(node.value, (str, int)) and not isinstance(node.value, bool):
        return node.value
    raise InvalidFilter(ast.dump(node))


def filter_users(expression: str) -> list[dict]:
    try:
        tree = ast.parse(expression.strip(), mode="eval")
        return [u for u in store.list_all() if _evaluate(tree, u)]
    except (SyntaxError, ValueError, TypeError, RecursionError) as exc:
        raise InvalidFilter(str(exc)) from exc
