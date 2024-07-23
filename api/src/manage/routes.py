from __future__ import annotations

import json
from typing import Any

import boto3
from botocore.exceptions import ClientError
from fastapi import APIRouter, Body, HTTPException, Response
from fastapi.responses import JSONResponse

from src import settings
from src.constants import API_VERSION

router = APIRouter(prefix=f"/{API_VERSION}")


@router.get("/status/")
def status(client_id: str): ...


@router.delete("/delete/{function_name}/")
def delete_lambda(function_name: str) -> Response:
    lambda_client = boto3.client("lambda", region_name=settings.AWS_DEFAULT_REGION)  # type: ignore

    try:
        # Delete the Lambda function
        response = lambda_client.delete_function(FunctionName=function_name)  # type: ignore

        # Check if the deletion was successful
        if response["ResponseMetadata"]["HTTPStatusCode"] == 204:
            return JSONResponse(
                content={
                    "message": f"Lambda function '{function_name}' deleted successfully"
                },
                status_code=200,
            )
        else:
            raise HTTPException(
                status_code=500, detail="Failed to delete Lambda function"
            )

    except ClientError as e:
        error_code = e.response["Error"]["Code"]  # type: ignore
        if error_code == "ResourceNotFoundException":
            raise HTTPException(
                status_code=404, detail=f"Lambda function '{function_name}' not found"
            )
        elif error_code == "ResourceConflictException":
            raise HTTPException(
                status_code=409,
                detail=f"Lambda function '{function_name}' is in use or being updated",
            )
        else:
            raise HTTPException(status_code=500, detail=str(e))

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/invoke/{function_name}/")
def invoke_lambda(function_name: str, request_body: Any = Body()) -> Response:
    lambda_client = boto3.client("lambda", region_name=settings.AWS_DEFAULT_REGION)  # type: ignore

    try:
        response = lambda_client.invoke(  # type: ignore
            FunctionName=function_name,
            InvocationType="RequestResponse",
            Payload=request_body,
        )

        payload = json.loads(response["Payload"].read().decode("utf-8"))  # type: ignore

        # Check if the function execution was successful
        if response["StatusCode"] == 200:
            return JSONResponse(content=payload)
        else:
            raise HTTPException(status_code=response["StatusCode"], detail=payload)  # type: ignore

    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceNotFoundException":  # type: ignore
            raise HTTPException(
                status_code=404, detail=f"Lambda function '{function_name}' not found"
            )
        else:
            raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
