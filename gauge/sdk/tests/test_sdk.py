from __future__ import annotations

from gauge.sdk.main import endpoint


def test_default_endpoint_decorator():
    @endpoint(name="name")
    def test_function():
        return "testy"

    assert test_function() == "testy"
    assert hasattr(test_function, "_gauge_register")
    assert test_function._gauge_register() == (
        "name",
        {
            "dependencies": [],
            "python_version": "3.12",
            "function": "test_function",
        },
    )


def test_custom_endpoint_decorator():
    @endpoint(name="name2", dependencies=["fastapi"], python_version="3.13")
    def test_function():
        return "test2"

    assert test_function() == "test2"
    assert hasattr(test_function, "_gauge_register")
    assert test_function._gauge_register() == (
        "name2",
        {
            "dependencies": ["fastapi"],
            "python_version": "3.13",
            "function": "test_function",
        },
    )
