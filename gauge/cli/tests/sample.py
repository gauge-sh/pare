from __future__ import annotations

from gauge.sdk.main import endpoint


@endpoint(name="name1")
def hello_world():
    print("Hello World!")


@endpoint(name="name2", python_version="3.11")
def test():
    pass