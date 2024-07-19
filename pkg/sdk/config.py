from __future__ import annotations

from pydantic import BaseModel


class AWSLambdaConfig(BaseModel):
    python_version: str = "3.12.4"
    dependencies: list[str] = ["fastapi==0.111.1"]
