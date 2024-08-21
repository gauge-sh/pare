from __future__ import annotations

import asyncio
import json
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from sqlalchemy import select
from typing_extensions import Annotated

from src import settings
from src.build import build_and_publish_image_to_ecr, unzip_file, write_to_zipfile
from src.constants import API_VERSION
from src.core.models import DeployConfig, ServiceConfig
from src.db import get_db
from src.deploy import create_ecr_repository, deploy_python_lambda_function_from_ecr
from src.middleware import get_total_deploys_for_user, get_user
from src.models import Deployment, Service, User

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix=f"/{API_VERSION}")


UPLOADED_BUNDLE_FILENAME = "uploaded_bundle.zip"
UNZIPPED_BUNDLE_DIR = "unzipped_bundle"


def build_ecr_repo_name(user: User, service_name: str) -> str:
    return f"{user.username}_{service_name}"


def build_lambda_function_name(repo_name: str, tag: str) -> str:
    return f"{repo_name}_{tag}"


# AUTH SENSITIVE!
# This pattern is used in the ECR policy to allow Lambda to pull images
def build_lambda_function_name_pattern(repo_name: str) -> str:
    return f"{repo_name}_*"


async def deploy_image(
    bundle_dir: Path,
    service_config: ServiceConfig,
    deploy_config: DeployConfig,
    user: User,
) -> bool:
    repo_name = build_ecr_repo_name(user, service_config.name)
    tag = deploy_config.git_hash
    function_name = build_lambda_function_name(repo_name, tag)
    function_name_pattern = build_lambda_function_name_pattern(repo_name)

    repo_created = create_ecr_repository(repo_name, function_name=function_name_pattern)
    if not repo_created:
        print(f"Failed to create ECR repository for {repo_name}")
        return False
    build_result = await build_and_publish_image_to_ecr(
        bundle=bundle_dir,
        repo_name=repo_name,
        tag=tag,
        service_config=service_config,
        deploy_config=deploy_config,
    )
    if build_result.exit_code != 0:
        print(f"Failed to build and publish image for {repo_name}:{tag}")
        return False

    return await deploy_python_lambda_function_from_ecr(
        function_name=function_name,
        image_name=build_result.image_name,
        environment_variables=deploy_config.environment_variables,
    )


@router.post("/deploy/")
async def deploy(
    file: Annotated[UploadFile, File()],
    json_data: Annotated[str, Form()],
    user: User = Depends(get_user),
    deploy_count: int = Depends(get_total_deploys_for_user),
    db: AsyncSession = Depends(get_db),
):
    if deploy_count >= settings.MAX_DEPLOYS_PER_USER:
        raise HTTPException(
            status_code=403,
            detail=f"User has reached the maximum number of deploys ({settings.MAX_DEPLOYS_PER_USER}).",
        )

    try:
        deploy_config = DeployConfig(**json.loads(json_data))
        # TODO: more careful handling here
        deploy_config.git_hash = deploy_config.git_hash[:7]
    except Exception:
        raise HTTPException(status_code=422, detail="Couldn't process deployment data.")

    async with db as session:
        deployment = (
            await session.execute(
                select(Deployment).filter(
                    Deployment.user_id == user.id,
                    Deployment.git_hash == deploy_config.git_hash,
                )
            )
        ).scalar()

        if not deployment:
            deployment = Deployment(user_id=user.id, git_hash=deploy_config.git_hash)
            session.add(deployment)
            await session.commit()

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_dir = Path(tmp_dir)
        zipfile_path = tmp_dir / UPLOADED_BUNDLE_FILENAME
        unzipped_bundle_path = tmp_dir / UNZIPPED_BUNDLE_DIR
        try:
            write_to_zipfile(await file.read(), output_path=zipfile_path)  # type: ignore
            unzip_file(zipfile_path, unzipped_bundle_path)
        except ValueError as err:
            return JSONResponse(status_code=400, content={"error": str(err)})

        deploy_results = await asyncio.gather(
            *[
                deploy_image(
                    bundle_dir=unzipped_bundle_path,
                    service_config=service,
                    deploy_config=deploy_config,
                    user=user,
                )
                for service in deploy_config.services
            ]
        )

        # Assuming that 'gather' has preserved the order
        succeeded: list[str] = []
        failed: list[str] = []
        # TODO: make batch query up-front for existence check
        for i, deploy_succeeded in enumerate(deploy_results):
            if deploy_succeeded:
                async with db as session:
                    service = (
                        await session.execute(
                            select(Service).filter(
                                Service.deployment_id == deployment.id,
                                Service.name == deploy_config.services[i].name,
                            )
                        )
                    ).scalar()

                    if not service:
                        service = Service(
                            deployment_id=deployment.id,
                            name=deploy_config.services[i].name,
                        )
                        session.add(service)
                        await session.commit()
                succeeded.append(deploy_config.services[i].name)
            else:
                failed.append(deploy_config.services[i].name)

        if failed:
            return JSONResponse(
                status_code=500,
                content={
                    "succeeded": succeeded,
                    "failed": failed,
                    "message": "Some services failed to deploy",
                },
            )

        return {"succeeded": succeeded, "failed": failed}
