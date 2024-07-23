from __future__ import annotations
from dataclasses import dataclass, field, asdict
import json

import requests

from typing import Any, Callable

from gauge import settings, errors


@dataclass
class RemoteInvocationArguments:
    args: list[Any] = field(default_factory=list)
    kwargs: dict[Any, Any] = field(default_factory=dict)


def invoke_endpoint(function_name: str, arguments: RemoteInvocationArguments) -> Any:
    try:
        response = requests.post(
            f"{settings.GAUGE_API_URL}/invoke/{function_name}/",
            headers={"X-Client-Secret": settings.CLIENT_SECRET},
            json=json.dumps(asdict(arguments))
        )
        response.raise_for_status()
        return response.json()
    except requests.HTTPError as e:
        raise errors.GaugeInvokeError(f"Function invocation for '{function_name}' failed with status: {e.response.status_code}")
    except Exception as e:
        raise errors.GaugeInvokeError(f"Could not invoke function: '{function_name}' due to error:\n{e}")



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

        def _as_lambda_handler() -> Callable[[Any, Any], Any]:
            def _lambda_handler(event: Any, context: Any) -> Any:
                if not isinstance(event, dict):
                    return {
                        "status": 400,
                        "detail": "Could not parse incoming data. The request body must be JSON.",
                    }
                try:
                    return {"status": 200, "result": function(*event["args"], **event["kwargs"])}
                except Exception as e:
                    return {"status": 500, "detail": str(e)}

            return _lambda_handler

        function.as_lambda_function_url_handler = _as_lambda_handler  # pyright: ignore[reportFunctionMemberAccess]

        def _invoke_fn(*args, **kwargs) -> Callable[..., Any]:  # type: ignore
            return invoke_endpoint(name, RemoteInvocationArguments(args=args, kwargs=kwargs))  # type: ignore

        function.invoke = _invoke_fn    # pyright: ignore[reportFunctionMemberAccess]

        return function

    return endpoint_decorator
