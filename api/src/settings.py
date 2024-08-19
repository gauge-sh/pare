# type: ignore
from __future__ import annotations

from pathlib import Path
from typing import Any

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
AWS_ACCOUNT_ID: str = env.str("AWS_ACCOUNT_ID")
AWS_LAMBDA_UPDATE_INITIAL_BACKOFF: int = env.int("AWS_LAMBDA_UPDATE_INITIAL_BACKOFF", 1)
AWS_LAMBDA_UPDATE_MAX_RETRIES: int = env.int("AWS_LAMBDA_UPDATE_MAX_RETRIES", 8)

ECR_REPO_POLICY: dict[str, Any] = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "LambdaECRImageRetrievalPolicy",
            "Effect": "Allow",
            "Principal": {"Service": "lambda.amazonaws.com"},
            "Action": ["ecr:BatchGetImage", "ecr:GetDownloadUrlForLayer"],
            "Condition": {
                "StringLike": {
                    "aws:sourceArn": f"arn:aws:lambda:{AWS_DEFAULT_REGION}:{AWS_ACCOUNT_ID}:function:*"
                }
            },
        }
    ],
}

PARE_ATOMIC_DEPLOYMENT_HEADER: str = env.str(
    "PARE_ATOMIC_DEPLOYMENT_HEADER", "X-Pare-Atomic-Deployment"
)
PARE_API_KEY_HEADER: str = env.str("PARE_API_KEY_HEADER", "X-Pare-API-Key")
