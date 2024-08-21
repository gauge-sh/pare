# type: ignore
from __future__ import annotations

from pathlib import Path

from environs import Env

env = Env()

PARE_API_URL: str = env.str("PARE_API_URL", "https://api.pare.gauge.sh")
PARE_API_VERSION: str = env.str("PARE_API_VERSION", "v0.1")
PARE_API_DEPLOY_URL_PATH: str = env.str("PARE_API_DEPLOY_URL_PATH", "/deploy/")
PARE_API_SERVICES_URL_PATH: str = env.str("PARE_API_SERVICES_URL_PATH", "/services/")
PARE_API_INVOKE_URL_PATH: str = env.str("PARE_API_INVOKE_URL_PATH", "/services/invoke/")
PARE_API_DELETE_URL_PATH: str = env.str("PARE_API_DELETE_URL_PATH", "/services/delete/")

PARE_API_KEY: str = env.str("PARE_API_KEY", "")
PARE_API_KEY_FILE: str = env.str("PARE_API_KEY_FILE", ".pare/api_key.priv")

if not PARE_API_KEY and PARE_API_KEY_FILE:
    pare_api_key_path = Path(PARE_API_KEY_FILE)
    if pare_api_key_path.exists():
        PARE_API_KEY = pare_api_key_path.read_text()

PARE_API_KEY_HEADER: str = env.str("PARE_API_KEY_HEADER", "X-Pare-API-Key")


PARE_ATOMIC_DEPLOYMENT_ENABLED: bool = env.bool("PARE_ATOMIC_DEPLOYMENT_ENABLED", False)
PARE_ATOMIC_DEPLOYMENT_HEADER: str = env.str(
    "PARE_ATOMIC_DEPLOYMENT_HEADER", "X-Pare-Atomic-Deployment"
)
PARE_GIT_HASH: str = env.str("PARE_GIT_HASH", "")

_KNOWN_GIT_HASH_ENV_VARS = [
    "GITHUB_SHA",  # GitHub Actions
    "CI_COMMIT_SHA",  # GitLab CI
    "GIT_COMMIT",  # Jenkins
    "CIRCLE_SHA1",  # CircleCI
    "TRAVIS_COMMIT",  # Travis CI
    "BUILD_SOURCEVERSION",  # Azure Pipelines
    "BITBUCKET_COMMIT",  # Bitbucket Pipelines
    "BUILD_VCS_NUMBER",  # TeamCity
    "DRONE_COMMIT_SHA",  # Drone CI
    "CODEBUILD_RESOLVED_SOURCE_VERSION",  # AWS CodeBuild
]

if not PARE_GIT_HASH:
    # try to get the git hash from the environment
    for env_var in _KNOWN_GIT_HASH_ENV_VARS:
        PARE_GIT_HASH = env.str(env_var, "")
        if PARE_GIT_HASH:
            break
