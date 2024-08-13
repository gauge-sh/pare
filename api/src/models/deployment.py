from __future__ import annotations

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, func

from src.db import Base


class Deployment(Base):
    __tablename__ = "deployments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    git_hash = Column(String, index=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)


class Service(Base):
    __tablename__ = "services"

    id = Column(Integer, primary_key=True, index=True)
    deployment_id = Column(Integer, ForeignKey("deployments.id"), nullable=False)
    name = Column(String, index=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
