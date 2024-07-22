from __future__ import annotations

from typing import Any, Callable

from sdk.config import AWSLambdaConfig


def endpoint(config: AWSLambdaConfig = AWSLambdaConfig()) -> Callable[..., Any]:
    def endpoint_decorator(
        function: Callable[..., Any],
    ) -> Callable[..., Any]:
        def _gauge_register() -> tuple[str, AWSLambdaConfig]:
            return function.__name__, config

        function._gauge_register = _gauge_register  # pyright: ignore[reportFunctionMemberAccess]
        return lambda *args, **kwargs: function(*args, **kwargs)

    return endpoint_decorator
