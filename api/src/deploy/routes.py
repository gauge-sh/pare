from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing_extensions import Annotated

from src.build import install_deps_to_dir, write_extended_zipfile, write_to_zipfile
from src.constants import API_VERSION
from src.db import get_db
from src.deploy import (
    deploy_python_lambda_function,
)
from src.middleware import get_user_id
from src.models import Deployment, Service
from src.transform import build_lambda_handler

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix=f"/{API_VERSION}")


class ServiceConfig(BaseModel):
    name: str
    path: str
    requirements: list[str] = Field(default_factory=list)


class DeployConfig(BaseModel):
    git_hash: str
    python_version: str
    services: list[ServiceConfig] = Field(default_factory=list)


UPLOADED_BUNDLE_FILENAME = "uploaded_bundle.zip"


@router.post("/deploy/")
async def deploy_zip(
    file: Annotated[UploadFile, File()],
    json_data: Annotated[str, Form()],
    user_id: int = Depends(get_user_id),
    db: AsyncSession = Depends(get_db),
):
    try:
        deploy_config = DeployConfig(**json.loads(json_data))
    except Exception:
        raise HTTPException(status_code=422, detail="Couldn't process deployment data.")

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_dir = Path(tmp_dir)
        zipfile_path = tmp_dir / UPLOADED_BUNDLE_FILENAME
        try:
            write_to_zipfile(await file.read(), output_path=zipfile_path)  # type: ignore
        except ValueError as err:
            return JSONResponse(status_code=400, content={"error": str(err)})
        for service in deploy_config.services:
            # TODO: validate deployment name
            build_path = tmp_dir / service.name
            build_path.mkdir(parents=True, exist_ok=True)
            build_lambda_handler(
                symbol_path=service.path,
                output_path=build_path / "lambda_function.py",
            )
            install_deps_to_dir(
                dependencies=service.requirements,
                python_version=deploy_config.python_version,
                output_dir=build_path,
            )
            deployment_package_path = tmp_dir / f"{service.name}.zip"
            write_extended_zipfile(
                existing_zipfile=zipfile_path,
                additional_paths=[build_path],
                output_path=deployment_package_path,
            )

            deploy_python_lambda_function(
                function_name=service.name,
                zip_file=deployment_package_path,
                python_version=deploy_config.python_version,
            )

    async with db as session:
        deployment = Deployment(user_id=user_id, git_hash=deploy_config.git_hash)
        session.add(deployment)
        await session.commit()

    async with db as session:
        for service in deploy_config.services:
            service = Service(deployment_id=deployment.id, name=service.name)
            session.add(service)
        await session.commit()

    # TODO: return deployment and services
    return {"status": "OK"}
