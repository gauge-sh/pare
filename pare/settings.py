# type: ignore
from __future__ import annotations

from environs import Env

env = Env()
env.read_env()

PARE_API_URL: str = env.str("PARE_API_URL", "http://localhost:8000/v0.1")
PARE_API_DEPLOY_URL_PATH: str = env.str("PARE_API_DEPLOY_URL_PATH", "/deploy/")
PARE_API_SERVICES_URL_PATH: str = env.str("PARE_API_SERVICES_URL_PATH", "/services/")
PARE_API_INVOKE_URL_PATH: str = env.str("PARE_API_INVOKE_URL_PATH", "/services/invoke/")
PARE_API_DELETE_URL_PATH: str = env.str("PARE_API_DELETE_URL_PATH", "/services/delete/")
PARE_API_KEY: str = env.str("PARE_API_KEY", "")
PARE_API_KEY_HEADER: str = env.str("PARE_API_KEY_HEADER", "X-Pare-API-Key")
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
