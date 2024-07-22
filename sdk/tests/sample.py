from __future__ import annotations

from sdk.main import endpoint


@endpoint(name="hello_world")
def hello_world():
    print("Hello World!")


@endpoint(name="test", python_version="3.11")
def test():
    pass
