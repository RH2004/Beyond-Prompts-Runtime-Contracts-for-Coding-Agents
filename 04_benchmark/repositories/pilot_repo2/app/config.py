"""Application settings."""

import os


def get_setting(name: str) -> str | None:
    """Return the value of a setting, or None when it is not configured."""
    return os.environ.get(name)
