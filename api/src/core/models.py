from __future__ import annotations

from pydantic import BaseModel, Field


class ServiceConfig(BaseModel):
    name: str
    path: str
    requirements: list[str] = Field(default_factory=list)


class DeployConfig(BaseModel):
    git_hash: str
    python_version: str
    services: list[ServiceConfig] = Field(default_factory=list)
