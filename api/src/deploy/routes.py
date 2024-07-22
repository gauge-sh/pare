from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from src.build.python_lambda import install_deps_to_dir
from src.build.zip import write_extended_zipfile, write_to_zipfile
from src.constants import API_VERSION
from src.deploy.lambda_deploy import deploy_python_lambda_function
from src.transform import build_lambda_handler

router = APIRouter(prefix=f"/{API_VERSION}")


class DeploymentConfig(BaseModel):
    name: str
    path: str
    python_version: str
    requirements: list[str] = Field(default_factory=list)


UPLOADED_BUNDLE_FILENAME = "uploaded_bundle.zip"


@router.post("/deploy/")
async def deploy_zip(
    file: Annotated[UploadFile, File()], json_data: Annotated[str, Form()]
):
    try:
        deployment_data = json.loads(json_data)
        deployments: list[DeploymentConfig] = [
            DeploymentConfig(**deployment) for deployment in deployment_data
        ]
    except Exception:
        raise HTTPException(
            status_code=422, detail="Couldn't process deployments data."
        )

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_dir = Path(tmp_dir)
        zipfile_path = tmp_dir / UPLOADED_BUNDLE_FILENAME
        try:
            write_to_zipfile(await file.read(), output_path=zipfile_path)
        except ValueError as err:
            return JSONResponse(status_code=400, content={"error": str(err)})
        for deployment in deployments:
            # TODO: validate deployment name
            build_path = tmp_dir / deployment.name
            build_lambda_handler(
                symbol_path=deployment.path,
                output_path=build_path / "lambda_function.py",
            )
            install_deps_to_dir(
                dependencies=deployment.requirements,
                python_version=deployment.python_version,
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
                python_version=deployment.python_version,
            )
            # TODO: after each deployment is done, update record in RDS
        return {"status": "OK"}
