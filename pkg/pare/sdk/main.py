from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any, Callable, Generic, TypeVar

import aiohttp
import requests
from typing_extensions import ParamSpec

from pare import errors, settings
from pare.client import get_client_headers
from pare.models import ServiceRegistration


@dataclass
class RemoteInvocationArguments:
    args: list[Any] = field(default_factory=list)
    kwargs: dict[Any, Any] = field(default_factory=dict)


def invoke_endpoint(function_name: str, arguments: RemoteInvocationArguments) -> Any:
    try:
        response = requests.post(
            f"{settings.PARE_API_URL}/{settings.PARE_API_VERSION}{settings.PARE_API_INVOKE_URL_PATH}{function_name}/",
            headers=get_client_headers(),
            json=json.dumps(asdict(arguments)),
        )
        response.raise_for_status()
        json_response = response.json()
        return json_response.get("result")
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
                f"{settings.PARE_API_URL}/{settings.PARE_API_VERSION}/invoke/{function_name}/",
                headers=get_client_headers(),
                json=json.dumps(asdict(arguments)),
            ) as response:
                response.raise_for_status()
                json_response = await response.json()
                return json_response.get("result")
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


class PareEndpoint(Generic[P, R]):
    def __init__(
        self, func: Callable[P, R], name: str, dependencies: list[str] = []
    ) -> None:
        self.func = func
        self.name = name
        self.dependencies = dependencies

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R:
        return self.func(*args, **kwargs)

    def _pare_register(self) -> ServiceRegistration:
        return ServiceRegistration(
            name=self.name, function=self.func.__name__, dependencies=self.dependencies
        )

    def as_lambda_function_url_handler(self) -> Callable[[Any, Any], Any]:
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
                    "result": self.func(
                        *event.get("args", []),  # type: ignore
                        **event.get("kwargs", {}),  # type: ignore
                    ),
                }
            except Exception as e:
                return {"status": 500, "detail": str(e)}

        return _lambda_handler

    def invoke(self, *args: P.args, **kwargs: P.kwargs) -> Callable[P, R]:
        return invoke_endpoint(
            self.name,
            RemoteInvocationArguments(args=args, kwargs=kwargs),  # type: ignore
        )

    async def invoke_async(self, *args: P.args, **kwargs: P.kwargs) -> Callable[P, R]:
        return await async_invoke_endpoint(
            self.name,
            RemoteInvocationArguments(args=args, kwargs=kwargs),  # type: ignore
        )


def endpoint(
    name: str, dependencies: list[str] = []
) -> Callable[[Callable[P, R]], PareEndpoint[P, R]]:
    def decorator(func: Callable[P, R]) -> PareEndpoint[P, R]:
        return PareEndpoint(func, name, dependencies)

    return decorator
