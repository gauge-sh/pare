from __future__ import annotations

from pare import endpoint


def test_default_endpoint_decorator():
    @endpoint(name="name")
    def test_function():
        return "testy"

    assert test_function() == "testy"
    assert hasattr(test_function, "_pare_register")
    assert test_function._pare_register() == (
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
    assert hasattr(test_function, "_pare_register")
    assert test_function._pare_register() == (
        "name2",
        {
            "dependencies": ["fastapi"],
            "python_version": "3.13",
            "function": "test_function",
        },
    )


def test_as_lambda_handler():
    @endpoint(name="name3", dependencies=["fastapi"], python_version="3.13")
    def test_function():
        return "test3"

    assert test_function() == "test3"
    assert hasattr(test_function, "as_lambda_function_url_handler")
    handler_result = test_function.as_lambda_function_url_handler()({}, {})
    assert handler_result.get("status") == 400

    handler_result = test_function.as_lambda_function_url_handler()({"args": []}, {})
    assert handler_result.get("status") == 200
    assert handler_result.get("result") == "test3"
