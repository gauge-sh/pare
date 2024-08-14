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


DEBUG = env.bool("DEBUG", False)
DEBUG_USER_ID = env.int("DEBUG_USER_ID", 1)

DB_USER = env.str("DB_USER", "postgres")
DB_PASSWORD = env.str("DB_PASSWORD")
DB_HOST = env.str("DB_HOST", "localhost")
DB_PORT = env.int("DB_PORT", 5432)
DB_NAME = env.str("DB_NAME", "postgres")

DATABASE_URL = (
    f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

LAMBDA_ROLE_ARN = env.str("LAMBDA_ROLE_ARN")
AWS_DEFAULT_REGION = env.str("AWS_DEFAULT_REGION", "us-east-1")

CLIENT_SECRET = env.str("CLIENT_SECRET")
