from __future__ import annotations

from typing import TYPE_CHECKING  # type: ignore

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from src.auth import get_user_id
from src.constants import API_VERSION
from src.db import get_db
from src.models import Deployment, Service

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix=f"/{API_VERSION}")


class ServiceConfig(BaseModel):
    name: str
    path: str
    requirements: list[str] = Field(default_factory=list)


UPLOADED_BUNDLE_FILENAME = "uploaded_bundle.zip"


@router.post("/deploy/")
async def deploy_zip(
    # file: Annotated[UploadFile, File()],  # type: ignore
    # json_data: Annotated[str, Form()],  # type: ignore
    user_id: int = Depends(get_user_id),
    db: AsyncSession = Depends(get_db),
):
    try:
        # deployment_data = json.loads(json_data)  # type: ignore
        deployment_data = {
            "git_hash": "1234567890",
            "python_version": "3.12",
            "services": {
                "service1": {
                    "path": "service1.py",
                    "requirements": ["requests", "pydantic"],
                },
                "service2": {
                    "path": "service2.py",
                    "requirements": ["requests", "pydantic"],
                },
            },
        }
        git_hash: str = deployment_data["git_hash"]
        python_version: str = deployment_data.get("python_version", "3.12")
        services: list[ServiceConfig] = [
            ServiceConfig(
                name=name,
                path=service["path"],
                requirements=service["requirements"],
            )
            for name, service in deployment_data["services"].items()
        ]
    except Exception:
        raise HTTPException(status_code=422, detail="Couldn't process deployment data.")

    ...
    # TODO: restore this
    # with tempfile.TemporaryDirectory() as tmp_dir:
    #     tmp_dir = Path(tmp_dir)
    #     zipfile_path = tmp_dir / UPLOADED_BUNDLE_FILENAME
    #     try:
    #         write_to_zipfile(await file.read(), output_path=zipfile_path)  # type: ignore
    #     except ValueError as err:
    #         return JSONResponse(status_code=400, content={"error": str(err)})
    #     for service in services:
    #         # TODO: validate deployment name
    #         build_path = tmp_dir / service.name
    #         build_path.mkdir(parents=True, exist_ok=True)
    #         build_lambda_handler(
    #             symbol_path=service.path,
    #             output_path=build_path / "lambda_function.py",
    #         )
    #         install_deps_to_dir(
    #             dependencies=service.requirements,
    #             python_version=python_version,
    #             output_dir=build_path,
    #         )
    #         deployment_package_path = tmp_dir / f"{service.name}.zip"
    #         write_extended_zipfile(
    #             existing_zipfile=zipfile_path,
    #             additional_paths=[build_path],
    #             output_path=deployment_package_path,
    #         )

    #         deploy_python_lambda_function(
    #             function_name=service.name,
    #             zip_file=deployment_package_path,
    #             python_version=python_version,
    #         )
    ...

    async with db as session:
        deployment = Deployment(user_id=user_id, git_hash=git_hash)
        session.add(deployment)
        await session.commit()

    async with db as session:
        for service in services:
            service = Service(deployment_id=deployment.id, name=service.name)
            session.add(service)
        await session.commit()

    return {"status": "OK"}
