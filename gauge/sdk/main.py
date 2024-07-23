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

        def as_lambda_function_url_handler() -> Callable[[Any, Any], Any]:
            def _lambda_handler(event: Any, context: Any) -> Any:
                if not isinstance(event, dict):
                    return {"status": 400, "detail": "Could not parse incoming data. The request body must be JSON."}
                try:
                    return {
                        "status": 200,
                        "result": function(**event)
                    }
                except Exception as e:
                    return {
                        "status": 500,
                        "detail": str(e)
                    }

            return _lambda_handler
        
        function.as_lambda_function_url_handler = as_lambda_function_url_handler  # pyright: ignore[reportFunctionMemberAccess]
        return function

    return endpoint_decorator
