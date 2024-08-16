from __future__ import annotations

import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from src import settings
from src.utils import run_async_subprocess

if TYPE_CHECKING:
    from src.core.models import DeployConfig, ServiceConfig
    from src.models import User

LAMBDA_DOCKERFILE_PATH = Path(__file__).parent / "Dockerfile.py_lambda"


def build_ecr_image_name(repo_name: str, tag: str) -> str:
    return f"{settings.AWS_ACCOUNT_ID}.dkr.ecr.{settings.AWS_DEFAULT_REGION}.amazonaws.com/{repo_name}:{tag}"


@dataclass
class ECRBuildResult:
    exit_code: int
    image_name: str


async def build_and_publish_image_to_ecr(
    user: User, bundle: Path, service_config: ServiceConfig, deploy_config: DeployConfig
) -> ECRBuildResult:
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_dir = Path(tmp_dir)

        # copy dockerfile from sibling file
        dockerfile_path = tmp_dir / "Dockerfile"
        dockerfile_path.write_text(LAMBDA_DOCKERFILE_PATH.read_text())

        # copy bundle contents to build root (expected by Dockerfile)
        build_path = tmp_dir / "build-root"
        build_path.mkdir()
        bundle_files = list(bundle.glob("*"))
        for file in bundle_files:
            file.rename(build_path / file.name)

        # write requirements.txt
        requirements = tmp_dir / "requirements.txt"
        requirements.write_text("\n".join(service_config.requirements))

        # build and push image
        repo_name = f"{service_config.name}-{user.id}"
        tag = f"{deploy_config.git_hash}-{deploy_config.python_version}"
        ecr_image_name = build_ecr_image_name(repo_name, tag)
        # --push here assumes that we have already authenticated with ECR
        depot_bin_absolute_path = Path.home() / ".depot" / "bin" / "depot"
        result = await run_async_subprocess(
            f"{depot_bin_absolute_path} build --push -t {ecr_image_name} ."
        )
        print(result.stdout)
        print(result.stderr)
        return ECRBuildResult(exit_code=result.exit_code, image_name=ecr_image_name)
