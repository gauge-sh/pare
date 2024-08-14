from __future__ import annotations

from fastapi import HTTPException, Request

from src import settings

AUTH_EXEMPT = ["/healthcheck"]


def is_auth_exempt(request: Request) -> bool:
    if settings.DEBUG or request.url.path in AUTH_EXEMPT:  # type: ignore
        return True

    return False


async def get_user_id(request: Request) -> int:
    if is_auth_exempt(request):
        return settings.DEBUG_USER_ID  # type: ignore

    try:
        return request.state.user_id
    except AttributeError:
        raise HTTPException(status_code=401, detail="Unauthenticated")
