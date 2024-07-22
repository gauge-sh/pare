from __future__ import annotations

from sdk.config import AWSLambdaConfig
from sdk.main import endpoint


@endpoint()
def hello_world():
    print("Hello World!")


class Hello:
    @endpoint(config=AWSLambdaConfig(image="python:3.12"))
    def world(self):
        print("Hello World!")
