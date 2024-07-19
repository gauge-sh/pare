from __future__ import annotations

from typing import Callable


def endpoint(function: Callable) -> Callable:
    return lambda *args, **kwargs: function(*args, **kwargs)
