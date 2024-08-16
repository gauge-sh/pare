from __future__ import annotations

import asyncio
import json
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from typing_extensions import Annotated

from src.build import build_and_publish_image_to_ecr, unzip_file, write_to_zipfile
from src.constants import API_VERSION
from src.core.models import DeployConfig, ServiceConfig
from src.db import get_db
from src.deploy import deploy_python_lambda_function_from_ecr
from src.middleware import get_user
from src.models import Deployment, Service, User

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix=f"/{API_VERSION}")


UPLOADED_BUNDLE_FILENAME = "uploaded_bundle.zip"
UNZIPPED_BUNDLE_DIR = "unzipped_bundle"


async def deploy_image(
    bundle_dir: Path,
    service_config: ServiceConfig,
    deploy_config: DeployConfig,
    user: User,
) -> bool:
    build_result = await build_and_publish_image_to_ecr(
        user=user,
        bundle=bundle_dir,
        service_config=service_config,
        deploy_config=deploy_config,
    )
    if build_result.exit_code != 0:
        return False

    return await deploy_python_lambda_function_from_ecr(
        function_name=service_config.name,
        image_name=build_result.image_name,
        python_version=deploy_config.python_version,
    )


@router.post("/deploy/")
async def deploy(
    file: Annotated[UploadFile, File()],
    json_data: Annotated[str, Form()],
    user: User = Depends(get_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        deploy_config = DeployConfig(**json.loads(json_data))
    except Exception:
        raise HTTPException(status_code=422, detail="Couldn't process deployment data.")

    async with db as session:
        # TODO: handle existing deployment
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
            deploy_image(
                bundle_dir=unzipped_bundle_path,
                service_config=service,
                deploy_config=deploy_config,
                user=user,
            )
            for service in deploy_config.services
        )

        # Assuming that 'gather' has preserved the order
        succeeded: list[str] = []
        failed: list[str] = []
        for i, deploy_succeeded in enumerate(deploy_results):
            if deploy_succeeded:
                async with db as session:
                    service = Service(
                        deployment_id=deployment.id, name=deploy_config.services[i].name
                    )
                    session.add(service)
                    await session.commit()
                succeeded.append(deploy_config.services[i].name)
            else:
                failed.append(deploy_config.services[i].name)

        return {"succeeded": succeeded, "failed": failed}
