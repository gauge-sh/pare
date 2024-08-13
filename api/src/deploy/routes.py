from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, Annotated  # type: ignore

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from src.build.python_lambda import install_deps_to_dir
from src.build.zip import write_extended_zipfile, write_to_zipfile
from src.constants import API_VERSION
from src.db import get_db
from src.deploy.lambda_deploy import deploy_python_lambda_function
from src.transform import build_lambda_handler

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix=f"/{API_VERSION}")


class DeploymentConfig(BaseModel):
    name: str
    path: str
    requirements: list[str] = Field(default_factory=list)


UPLOADED_BUNDLE_FILENAME = "uploaded_bundle.zip"


# TODO: middleware to pull user for the request from api key


@router.post("/deploy/")
async def deploy_zip(
    file: Annotated[UploadFile, File()],  # type: ignore
    json_data: Annotated[str, Form()],  # type: ignore
    db: AsyncSession = Depends(get_db),
):
    try:
        deployment_data = json.loads(json_data)  # type: ignore
        git_hash: str = deployment_data["git_hash"]
        python_version: str = deployment_data.get("python_version", "3.12")
        deployments: list[DeploymentConfig] = [
            DeploymentConfig(
                name=name,
                path=deployment["path"],
                requirements=deployment["requirements"],
            )
            for name, deployment in deployment_data["deployments"].items()
        ]
    except Exception:
        raise HTTPException(
            status_code=422, detail="Couldn't process deployments data."
        )

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_dir = Path(tmp_dir)
        zipfile_path = tmp_dir / UPLOADED_BUNDLE_FILENAME
        try:
            write_to_zipfile(await file.read(), output_path=zipfile_path)  # type: ignore
        except ValueError as err:
            return JSONResponse(status_code=400, content={"error": str(err)})
        for deployment in deployments:
            # TODO: validate deployment name
            build_path = tmp_dir / deployment.name
            build_path.mkdir(parents=True, exist_ok=True)
            build_lambda_handler(
                symbol_path=deployment.path,
                output_path=build_path / "lambda_function.py",
            )
            install_deps_to_dir(
                dependencies=deployment.requirements,
                python_version=python_version,
                output_dir=build_path,
            )
            deployment_package_path = tmp_dir / f"{deployment.name}.zip"
            write_extended_zipfile(
                existing_zipfile=zipfile_path,
                additional_paths=[build_path],
                output_path=deployment_package_path,
            )

            deploy_python_lambda_function(
                function_name=deployment.name,
                zip_file=deployment_package_path,
                python_version=python_version,
            )

        # TODO: save deployment to db
        # TODO: save services to db

        return {"status": "OK"}
