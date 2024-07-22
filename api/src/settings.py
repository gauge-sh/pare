# type: ignore
from __future__ import annotations

from typing import Final

from environs import Env

env: Env = Env()
env.read_env()

DB_USER: Final[str] = env.str("DB_USER", "postgres")
DB_PASSWORD: Final[str] = env.str("DB_PASSWORD")
DB_HOST: Final[str] = env.str("DB_HOST", "localhost")
DB_PORT: Final[int] = env.int("DB_PORT", 5432)
DB_NAME: Final[str] = env.str("DB_NAME", "postgres")

LAMBDA_ROLE_ARN: Final[str] = env.str("LAMBDA_ROLE_ARN")
