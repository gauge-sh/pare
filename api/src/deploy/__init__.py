from __future__ import annotations

from .lambda_deploy import (
    deploy_python_lambda_function_from_ecr,
    deploy_python_lambda_function_from_zip,
)

__all__ = [
    "deploy_python_lambda_function_from_zip",
    "deploy_python_lambda_function_from_ecr",
]
