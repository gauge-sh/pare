from __future__ import annotations

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, func

from src.db import Base


class Deployment(Base):
    __tablename__ = "deployments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    git_hash = Column(String, index=True)
    created_at = Column(DateTime, server_default=func.now())


class Service(Base):
    __tablename__ = "services"

    id = Column(Integer, primary_key=True, index=True)
    deployment_id = Column(Integer, ForeignKey("deployments.id"))
    name = Column(String, index=True)
    created_at = Column(DateTime, server_default=func.now())
