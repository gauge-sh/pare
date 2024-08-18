from __future__ import annotations

from pydantic import BaseModel, Field


class ServiceRegistration(BaseModel):
    name: str
    function: str
    dependencies: list[str] = Field(default_factory=list)


class ServiceConfig(BaseModel):
    name: str
    path: str
    requirements: list[str] = Field(default_factory=list)


class DeployConfig(BaseModel):
    git_hash: str
    python_version: str
    environment_variables: dict[str, str] = Field(default_factory=dict)
    services: list[ServiceConfig] = Field(default_factory=list)
