from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any, Callable, TypeVar

import aiohttp
import requests
from typing_extensions import ParamSpec

from pare import errors, settings
from pare.client import get_current_git_hash
from pare.models import ServiceRegistration


@dataclass
class RemoteInvocationArguments:
    args: list[Any] = field(default_factory=list)
    kwargs: dict[Any, Any] = field(default_factory=dict)


def invoke_endpoint(function_name: str, arguments: RemoteInvocationArguments) -> Any:
    try:
        response = requests.post(
            f"{settings.PARE_API_URL}{settings.PARE_API_INVOKE_URL_PATH}{function_name}/",
            headers={
                settings.PARE_API_KEY_HEADER: settings.PARE_API_KEY,
                settings.PARE_ATOMIC_DEPLOYMENT_HEADER: get_current_git_hash(),
            },
            json=json.dumps(asdict(arguments)),
        )
        response.raise_for_status()
        return response.json()
    except requests.HTTPError as e:
        raise errors.PareInvokeError(
            f"Function invocation for '{function_name}' failed with status: {e.response.status_code}"
        )
    except Exception as e:
        raise errors.PareInvokeError(
            f"Could not invoke function: '{function_name}' due to error:\n{e}"
        )


async def async_invoke_endpoint(
    function_name: str, arguments: RemoteInvocationArguments
) -> Any:
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                f"{settings.PARE_API_URL}/invoke/{function_name}/",
                headers={
                    settings.PARE_API_KEY_HEADER: settings.PARE_API_KEY,
                    settings.PARE_ATOMIC_DEPLOYMENT_HEADER: get_current_git_hash(),
                },
                json=json.dumps(asdict(arguments)),
            ) as response:
                response.raise_for_status()
                return await response.json()
        except aiohttp.ClientResponseError as e:
            raise errors.PareInvokeError(
                f"Function invocation for '{function_name}' failed with status: {e.status}"
            )
        except Exception as e:
            raise errors.PareInvokeError(
                f"Could not invoke function: '{function_name}' due to error:\n{e}"
            )


P = ParamSpec("P")
R = TypeVar("R")


def endpoint(name: str, dependencies: list[str] = []) -> Callable[..., Any]:
    def endpoint_decorator(
        function: Callable[P, R],
    ) -> Callable[P, R]:
        def _pare_register() -> ServiceRegistration:
            return ServiceRegistration(
                name=name, function=function.__name__, dependencies=dependencies
            )

        function._pare_register = _pare_register  # pyright: ignore[reportFunctionMemberAccess]

        def _as_lambda_handler() -> Callable[[Any, Any], Any]:
            def _lambda_handler(event: Any, context: Any) -> Any:
                if not isinstance(event, dict):
                    return {
                        "status": 400,
                        "detail": "Could not parse incoming data. The request body must be JSON.",
                    }
                if "args" not in event and "kwargs" not in event:
                    return {
                        "status": 400,
                        "detail": "Incoming JSON should contain 'args' or 'kwargs' to invoke the function.",
                    }
                try:
                    return {
                        "status": 200,
                        "result": function(
                            *event.get("args", []),  # type: ignore
                            **event.get("kwargs", {}),  # type: ignore
                        ),
                    }
                except Exception as e:
                    return {"status": 500, "detail": str(e)}

            return _lambda_handler

        function.as_lambda_function_url_handler = _as_lambda_handler  # pyright: ignore[reportFunctionMemberAccess]

        def _invoke_fn(*args: P.args, **kwargs: P.kwargs) -> Callable[P, R]:
            return invoke_endpoint(
                name,
                RemoteInvocationArguments(args=args, kwargs=kwargs),  # type: ignore
            )

        function.invoke = _invoke_fn  # pyright: ignore[reportFunctionMemberAccess]

        async def _async_invoke_fn(*args: P.args, **kwargs: P.kwargs) -> Callable[P, R]:
            return await async_invoke_endpoint(
                name,
                RemoteInvocationArguments(args=args, kwargs=kwargs),  # type: ignore
            )

        function.invoke_async = _async_invoke_fn  # pyright: ignore[reportFunctionMemberAccess]

        return function

    return endpoint_decorator
