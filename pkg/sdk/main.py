from __future__ import annotations

from typing import Callable

from sdk.config import AWSLambdaConfig


def endpoint(
    function: Callable, config: AWSLambdaConfig = AWSLambdaConfig()
) -> Callable:
    return lambda *args, **kwargs: function(*args, **kwargs)
