from __future__ import annotations

from typing import TYPE_CHECKING, Any

from src import settings

if TYPE_CHECKING:
    from fastapi import FastAPI, Request


from fastapi import HTTPException, Request


async def get_user_id(request: Request) -> int:
    try:
        return request.state.user_id
    except AttributeError:
        raise HTTPException(status_code=401, detail="Unauthenticated")


async def get_deploy_version(request: Request) -> str:
    try:
        return request.state.deploy_version
    except AttributeError:
        raise HTTPException(
            status_code=400,
            detail=f"Must provide '{settings.PARE_ATOMIC_DEPLOYMENT_HEADER}' header.",
        )


def apply_middleware(app: FastAPI) -> None:
    @app.middleware("http")
    async def user_id_middleware(request: Request, call_next: Any):  # pyright: ignore[reportUnusedFunction]
        # TODO: actual user ID extraction from API Key in headers, raise 401 if not found
        request.state.user_id = 1
        return await call_next(request)

    @app.middleware("http")
    async def atomic_deployment_middleware(request: Request, call_next: Any):  # pyright: ignore[reportUnusedFunction]
        if settings.PARE_ATOMIC_DEPLOYMENT_HEADER in request.headers:
            # This is either a git hash or 'latest'
            request.state.deploy_version = request.headers[
                settings.PARE_ATOMIC_DEPLOYMENT_HEADER
            ]

        return await call_next(request)
