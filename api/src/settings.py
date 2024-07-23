# type: ignore
from __future__ import annotations

from environs import Env

env = Env()
env.read_env()


DB_USER = env.str("DB_USER", "postgres")
DB_PASSWORD = env.str("DB_PASSWORD")
DB_HOST = env.str("DB_HOST", "localhost")
DB_PORT = env.int("DB_PORT", 5432)
DB_NAME = env.str("DB_NAME", "postgres")


LAMBDA_ROLE_ARN = env.str("LAMBDA_ROLE_ARN")
AWS_DEFAULT_REGION = env.str("AWS_DEFAULT_REGION", "us-east-1")
