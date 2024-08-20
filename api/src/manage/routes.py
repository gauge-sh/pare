from __future__ import annotations

import json
from datetime import datetime
from typing import TYPE_CHECKING, Any, List

import boto3
from botocore.exceptions import ClientError
from fastapi import APIRouter, Body, Depends, HTTPException, Path, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, field_serializer
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from src import settings
from src.constants import API_VERSION
from src.db import get_db
from src.middleware import get_deploy_version, get_user
from src.models import Deployment, Service, User

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


router = APIRouter(prefix=f"/{API_VERSION}/services")


async def services_for_user_by_name(
    user: User = Depends(get_user),
    service_name: str = Path(..., title="Service Name"),
    db: AsyncSession = Depends(get_db),
) -> list[Service]:
    async with db as session:
        result = await session.execute(
            select(Service)
            .join(Service.deployment)
            .join(Deployment.user)
            .where(User.id == user.id, Service.name == service_name)
        )
        services = result.scalars().all()

        if not services:
            raise HTTPException(status_code=404, detail="No services found")

        return list(services)


# Used when invoking a service
async def service_for_user_by_version_or_latest(
    deploy_version: str | None = Depends(get_deploy_version),
    services: list[Service] = Depends(services_for_user_by_name),
) -> Service:
    if deploy_version is None:
        # If no deploy version is provided, return the latest service
        return services[0]

    matching_service: Service | None = None
    for service in services:
        if service.deployment.git_hash == deploy_version:
            if matching_service:
                raise HTTPException(status_code=500, detail="Multiple services found")
            matching_service = service

    if not matching_service:
        raise HTTPException(
            status_code=404, detail="Service not found for deploy version"
        )

    return matching_service


# Used when deleting a service or getting details about a service
async def service_for_user_by_version_or_unique_name(
    deploy_version: str | None = Depends(get_deploy_version),
    services: list[Service] = Depends(services_for_user_by_name),
) -> Service:
    if len(services) == 1:
        return services[0]

    if deploy_version is None:
        raise HTTPException(
            status_code=400,
            detail="Deploy version is required when more than one service exists for a name.",
        )

    matching_service: Service | None = None
    for service in services:
        if service.deployment.git_hash == deploy_version:
            if matching_service:
                raise HTTPException(status_code=500, detail="Multiple services found")
            matching_service = service

    if not matching_service:
        raise HTTPException(
            status_code=404, detail="Service not found for deploy version"
        )

    return matching_service


def get_lambda_function_name(service: Service) -> str:
    return f"{service.deployment.user.username}_{service.name}_{service.deployment.git_hash}"


class DeploymentSchema(BaseModel):
    git_hash: str
    created_at: datetime

    @field_serializer("created_at")
    def serialize_created_at(self, value: datetime) -> str:
        return value.isoformat()

    class Config:
        from_attributes = True


class ServiceSchema(BaseModel):
    name: str
    deployment: DeploymentSchema
    created_at: datetime

    @field_serializer("created_at")
    def serialize_created_at(self, value: datetime) -> str:
        return value.isoformat()

    class Config:
        from_attributes = True


@router.get("/{service_name}/", response_model=ServiceSchema)
def get_lambda_info(
    service: Service = Depends(service_for_user_by_version_or_unique_name),
):
    return service


@router.get("/", response_model=List[ServiceSchema])
async def list_lambda_info(
    user: User = Depends(get_user), db: AsyncSession = Depends(get_db)
):
    async with db as session:
        query = (
            select(Service)
            .join(Service.deployment)
            .join(Deployment.user)
            .options(joinedload(Service.deployment).joinedload(Deployment.user))
            .where(User.id == user.id)
        )

        result = await session.execute(query)
        services = result.scalars().all()

    return services


@router.delete("/delete/{service_name}/")
async def delete_lambda(
    service: Service = Depends(service_for_user_by_version_or_unique_name),
    db: AsyncSession = Depends(get_db),
) -> Response:
    lambda_client = boto3.client("lambda", region_name=settings.AWS_DEFAULT_REGION)  # type: ignore

    try:
        # Delete the Lambda function
        response = lambda_client.delete_function(  # type: ignore
            FunctionName=get_lambda_function_name(service)
        )

        # Check if the deletion was successful
        if response["ResponseMetadata"]["HTTPStatusCode"] == 204:
            async with db as session:
                await session.delete(service)
                await session.commit()
            return JSONResponse(
                content={
                    "message": f"Lambda function '{service.name}' deleted successfully"
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
                status_code=404, detail=f"Lambda function '{service.name}' not found"
            )
        elif error_code == "ResourceConflictException":
            raise HTTPException(
                status_code=409,
                detail=f"Lambda function '{service.name}' is in use or being updated",
            )
        else:
            raise HTTPException(status_code=500, detail=str(e))

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/invoke/{service_name}/")
def invoke_lambda(
    request_body: Any = Body(),
    service: Service = Depends(service_for_user_by_version_or_latest),
) -> Response:
    lambda_client = boto3.client("lambda", region_name=settings.AWS_DEFAULT_REGION)  # type: ignore

    try:
        response = lambda_client.invoke(  # type: ignore
            FunctionName=get_lambda_function_name(service),
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
                status_code=404, detail=f"Lambda function '{service.name}' not found"
            )
        else:
            raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
