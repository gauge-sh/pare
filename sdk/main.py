from __future__ import annotations

from typing import Any, Callable

from sdk.config import AWSLambdaConfig


def endpoint(
    function: Callable[..., Any], config: AWSLambdaConfig = AWSLambdaConfig()
) -> Callable[..., Any]:
    return function
