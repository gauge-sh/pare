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


def create_ecr_repository(repository_name: str) -> bool:
    ecr_client = boto3.client("ecr", region_name=settings.AWS_DEFAULT_REGION)  # type: ignore

    try:
        ecr_client.create_repository(  # type: ignore
            repositoryName=repository_name,
            imageScanningConfiguration={"scanOnPush": True},
            encryptionConfiguration={"encryptionType": "AES256"},
        )
        print(f"Repository '{repository_name}' created successfully.")
    except ClientError as e:
        if e.response["Error"]["Code"] == "RepositoryAlreadyExistsException":  # type: ignore
            print(f"Repository '{repository_name}' already exists.")
        else:
            print(f"An error occurred: {e}")
            return False

    ecr_client.set_repository_policy(  # type: ignore
        repositoryName=repository_name,
        policyText=json.dumps(settings.ECR_REPO_POLICY),
    )
    print(f"Repository policy set for '{repository_name}'")
    return True


async def deploy_python_lambda_function_from_ecr(
    function_name: str,
    image_name: str,
):
    # Initialize the Lambda client
    lambda_client = boto3.client("lambda", region_name=settings.AWS_DEFAULT_REGION)  # type: ignore

    try:
        lambda_client.get_function(FunctionName=function_name)  # type: ignore

        # If we reach here, the function exists, so we update it
        response = lambda_client.update_function_code(  # type: ignore
            FunctionName=function_name, ImageUri=image_name
        )
        print(f"Updated existing Lambda function: {function_name}")

    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceNotFoundException":  # type: ignore
            # The function doesn't exist, so we create it
            response = lambda_client.create_function(  # type: ignore
                FunctionName=function_name,
                PackageType="Image",
                Code={
                    "ImageUri": image_name,
                },
                Role=settings.LAMBDA_ROLE_ARN,
            )
            print(f"Created new Lambda function: {function_name}")
        else:
            # Unexpected error
            print(f"Error deploying Lambda function: {str(e)}")
            return False

    # Print the response
    print(json.dumps(response, indent=2, default=str))

    return True


def deploy_python_lambda_function_from_zip(
    function_name: str,
    zip_file: Path,
    python_version: str,
    handler: str = "lambda_function.lambda_handler",
):
    # Initialize the Lambda client
    lambda_client = boto3.client("lambda", region_name=settings.AWS_DEFAULT_REGION)  # type: ignore
    lambda_runtime = translate_python_version_to_lambda_runtime(python_version)

    try:
        bytes_content = zip_file.read_bytes()
    except FileNotFoundError:
        print(f"Error reading ZIP file: {zip_file}")
        return False

    try:
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
                Role=settings.LAMBDA_ROLE_ARN,
                Handler=handler,
                Code=dict(ZipFile=bytes_content),
            )
            print(f"Created new Lambda function: {function_name}")
        else:
            # Unexpected error
            print(f"Error deploying Lambda function: {str(e)}")
            return False

    # Print the response
    print(json.dumps(response, indent=2, default=str))

    return True
