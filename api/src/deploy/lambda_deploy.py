from __future__ import annotations

import json
from typing import TYPE_CHECKING

import boto3
from botocore.exceptions import ClientError

from src import settings

if TYPE_CHECKING:
    from pathlib import Path

LAMBDA_RUNTIMES = ["python3.12", "python3.11", "python3.10", "python3.9", "python3.8"]


def translate_python_version_to_lambda_runtime(python_version: str) -> str:
    runtime_version = f"python{python_version}"
    if runtime_version not in LAMBDA_RUNTIMES:
        raise ValueError(
            f"Python version: {python_version} does not match a Lambda runtime."
        )
    return runtime_version


def deploy_python_lambda_function(
    function_name: str,
    zip_file: Path,
    python_version: str,
    handler: str = "lambda_function.lambda_handler",
):
    # Initialize the Lambda client
    lambda_client = boto3.client("lambda", region_name=settings.AWS_DEFAULT_REGION)  # type: ignore
    lambda_runtime = translate_python_version_to_lambda_runtime(python_version)

    try:
        # Read the ZIP file
        with open(zip_file, "rb") as file_data:
            bytes_content = file_data.read()

        try:
            # Try to get the function configuration
            lambda_client.get_function(FunctionName=function_name)  # type: ignore

            # If we reach here, the function exists, so we update it
            response = lambda_client.update_function_code(  # type: ignore
                FunctionName=function_name, ZipFile=bytes_content
            )
            print(f"Updated existing Lambda function: {function_name}")

        except ClientError as e:
            if e.response["Error"]["Code"] == "ResourceNotFoundException":  # type: ignore
                # The function doesn't exist, so we create it
                response = lambda_client.create_function(  # type: ignore
                    FunctionName=function_name,
                    Runtime=lambda_runtime,
                    Role=settings.LAMBDA_ROLE_ARN,  # type: ignore
                    Handler=handler,
                    Code=dict(ZipFile=bytes_content),
                )
                print(f"Created new Lambda function: {function_name}")
            else:
                # Unexpected error
                raise

        # Print the response
        print(json.dumps(response, indent=2, default=str))

        return True
    except Exception as e:
        print(f"Error deploying Lambda function: {str(e)}")
        return False
