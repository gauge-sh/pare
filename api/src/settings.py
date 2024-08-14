# type: ignore
from __future__ import annotations

from pathlib import Path

from environs import Env

env = Env()

try:
    local_path = Path(__file__).parent.parent / ".env.local"
    env.read_env(local_path, recurse=False)
except FileNotFoundError:
    raise

env.read_env()


DEBUG: bool = env.bool("DEBUG", False)
DEBUG_USER_ID: int = env.int("DEBUG_USER_ID", 1)

DB_USER: str = env.str("DB_USER", "postgres")
DB_PASSWORD: str = env.str("DB_PASSWORD")
DB_HOST: str = env.str("DB_HOST", "localhost")
DB_PORT: str = env.int("DB_PORT", 5432)
DB_NAME: str = env.str("DB_NAME", "postgres")

DATABASE_URL: str = (
    f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

LAMBDA_ROLE_ARN: str = env.str("LAMBDA_ROLE_ARN")
AWS_DEFAULT_REGION: str = env.str("AWS_DEFAULT_REGION", "us-east-1")

PARE_ATOMIC_DEPLOYMENT_HEADER: str = env.str(
    "PARE_ATOMIC_DEPLOYMENT_HEADER", "X-Pare-Atomic-Deployment"
)
