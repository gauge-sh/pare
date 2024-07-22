from __future__ import annotations

from typing import Any, Callable


def endpoint(
    name: str, python_version: str = "3.12", dependencies: list[str] = []
) -> Callable[..., Any]:
    def endpoint_decorator(
        function: Callable[..., Any],
    ) -> Callable[..., Any]:
        def _gauge_register() -> tuple[str, dict[str, str | list[str]]]:
            return name, {
                "function": function.__name__,
                "python_version": python_version,
                "dependencies": dependencies,
            }

        function._gauge_register = _gauge_register  # pyright: ignore[reportFunctionMemberAccess]
        return function

    return endpoint_decorator
