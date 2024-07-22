import tempfile
from fastapi import APIRouter, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from src.build.zip import write_to_zipfile
from src.constants import API_VERSION

router = APIRouter(prefix=f"/{API_VERSION}")


class DeploymentConfig(BaseModel):
    path: str
    python_version: str
    requirements: list[str] = Field(default_factory=list)


UPLOADED_BUNDLE_FILENAME = "uploaded_bundle.zip"

@router.post("/deploy/")
async def deploy_zip(file: UploadFile, deployments: list[DeploymentConfig]):
    with tempfile.TemporaryDirectory() as tmp_dir:
        zipfile_path = tmp_dir / UPLOADED_BUNDLE_FILENAME
        try:
            write_to_zipfile(await file.read(), output_path=zipfile_path)
        except ValueError as err:
            return JSONResponse(status_code=400, content={"error": str(err)})
        for deployment in deployments:
            # create subfolder
            # install requirements into subfolder
            # build lambda handler from path
            # create new zip from uploaded zip, lambda handler, and requirements
            # use boto3 to upload this zip to a lambda with a derived name (upsert)
            ...
        
        # after all deployments done, update record in RDS
        return {"status": "WIP"}
