from __future__ import annotations

import os

from pare.sdk.main import endpoint


@endpoint(name="name1")
def hello_world():
    if "PARE_TEST_ONE" in os.environ:
        return f"[{os.environ["PARE_TEST_ONE"]}] Hello World!"
    print("Hello World!")


@endpoint(name="name2", dependencies=["pydantic==2.8.2"])
def test(echo: str):
    if "PARE_TEST_TWO" in os.environ:
        return f"[{os.environ["PARE_TEST_TWO"]}] {echo}"
    return echo
