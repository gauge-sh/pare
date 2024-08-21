from __future__ import annotations

from typing import TYPE_CHECKING, Any

from fastapi import Depends
from fastapi.responses import JSONResponse
from sqlalchemy import func, select
from sqlalchemy.exc import MultipleResultsFound, NoResultFound

from src import settings
from src.db import get_db
from src.models import Deployment, Service, User

if TYPE_CHECKING:
    from fastapi import FastAPI, Request
    from sqlalchemy.ext.asyncio import AsyncSession


from fastapi import HTTPException, Request


async def get_user(request: Request, db: AsyncSession = Depends(get_db)) -> User:
    try:
        api_key = request.state.api_key
        async with db as session:
            user = await session.execute(select(User).where(User.api_key == api_key))
            user = user.scalar_one()
    except (AttributeError, MultipleResultsFound, NoResultFound):
        raise HTTPException(status_code=401, detail="Unauthenticated")

    if user.is_blocked:  # type: ignore
        raise HTTPException(status_code=403, detail="User is blocked")
    return user


async def get_total_services_deployed_for_user(
    user: User, db: AsyncSession = Depends(get_db)
) -> int:
    async with db as session:
        query = (
            func.count(Service.id)
            .select_from(Service)
            .join(Service.deployment)
            .join(Deployment.user)
            .where(User.id == user.id)
        )

        result = await session.execute(query)
        return result.scalar_one()


async def get_deploy_version(request: Request) -> str | None:
    try:
        return request.state.deploy_version
    except AttributeError:
        return None


AUTH_EXEMPT = {"/healthcheck/", "/login-with-github/"}


def apply_middleware(app: FastAPI) -> None:
    @app.middleware("http")
    async def api_key_middleware(request: Request, call_next: Any):  # pyright: ignore[reportUnusedFunction]
        if settings.PARE_API_KEY_HEADER in request.headers:
            request.state.api_key = request.headers[settings.PARE_API_KEY_HEADER]
        elif request.url.path not in AUTH_EXEMPT:
            print(request.url.path)
            return JSONResponse(status_code=401, content={"detail": "Unauthenticated"})
        return await call_next(request)

    @app.middleware("http")
    async def atomic_deployment_middleware(request: Request, call_next: Any):  # pyright: ignore[reportUnusedFunction]
        if settings.PARE_ATOMIC_DEPLOYMENT_HEADER in request.headers:
            request.state.deploy_version = request.headers[
                settings.PARE_ATOMIC_DEPLOYMENT_HEADER
            ]

        return await call_next(request)
