from __future__ import annotations

import tempfile
from dataclasses import dataclass
from itertools import chain
from pathlib import Path
from shutil import copytree
from typing import TYPE_CHECKING

from src import settings
from src.transform import build_lambda_handler
from src.utils import run_async_subprocess

if TYPE_CHECKING:
    from src.core.models import DeployConfig, ServiceConfig

LAMBDA_DOCKERFILE_PATH = Path(__file__).parent / "Dockerfile.py_lambda"


def build_ecr_image_name(repo_name: str, tag: str) -> str:
    return f"{settings.AWS_ACCOUNT_ID}.dkr.ecr.{settings.AWS_DEFAULT_REGION}.amazonaws.com/{repo_name}:{tag}"


@dataclass
class ECRBuildResult:
    exit_code: int
    image_name: str


async def build_and_publish_image_to_ecr(
    bundle: Path,
    repo_name: str,
    tag: str,
    service_config: ServiceConfig,
    deploy_config: DeployConfig,
) -> ECRBuildResult:
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_dir = Path(tmp_dir)

        # copy dockerfile from sibling file
        dockerfile_path = tmp_dir / "Dockerfile"
        dockerfile_path.write_text(LAMBDA_DOCKERFILE_PATH.read_text())

        # copy bundle contents to build root (expected by Dockerfile)
        build_path = tmp_dir / "build-root"
        copytree(bundle, build_path)

        # write requirements.txt
        requirements = tmp_dir / "requirements.txt"
        requirements.write_text("\n".join(chain(service_config.requirements, ["pare"])))

        # lambda function
        lambda_function = build_path / "lambda_function.py"
        build_lambda_handler(service_config.path, lambda_function)

        # build and push image
        ecr_image_name = build_ecr_image_name(repo_name, tag)
        # --push here assumes that we have already authenticated with ECR
        # TODO fix abs docker path
        result = await run_async_subprocess(
            f'/usr/bin/docker build --push -t {ecr_image_name} --build-arg="PYTHON_VERSION={deploy_config.python_version}" --provenance=false {tmp_dir}'
        )
        print(result.stdout)
        print(result.stderr)
        return ECRBuildResult(exit_code=result.exit_code, image_name=ecr_image_name)
