from __future__ import annotations

import json

import boto3
from botocore.exceptions import ClientError

from src import settings


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
    environment_variables: dict[str, str],
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

        # Update environment variables
        lambda_client.update_function_configuration(  # type: ignore
            FunctionName=function_name, Environment={"Variables": environment_variables}
        )
        print(f"Updated environment variables for Lambda function: {function_name}")
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
                Environment={"Variables": environment_variables},
            )
            print(f"Created new Lambda function: {function_name}")
        else:
            # Unexpected error
            print(f"Error deploying Lambda function: {str(e)}")
            return False

    # Print the response
    print(json.dumps(response, indent=2, default=str))
    return True
