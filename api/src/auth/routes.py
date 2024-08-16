from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from src.db import get_db
from src.models import User

from .api_key import generate_api_key
from .github import get_github_account_info

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


class GithubLoginPayload(BaseModel):
    token: str


@router.post("/login-with-github/")
async def login_with_github(
    payload: GithubLoginPayload, db: AsyncSession = Depends(get_db)
):
    try:
        github_account_info = await get_github_account_info(payload.token)
    except Exception:
        return JSONResponse(
            {"error": "Failed to retrieve github account info with token."},
            status_code=400,
        )

    async with db as session:
        user = await session.execute(
            select(User).filter(
                (User.email == github_account_info.email)
                | (User.username == github_account_info.username)
            )
        )
        user = user.scalar()

        if not user:
            api_key = generate_api_key()
            user = User(
                username=github_account_info.username,
                email=github_account_info.email,
                api_key=api_key,
            )
            session.add(user)
            try:
                await session.commit()
            except IntegrityError:
                user.api_key = generate_api_key()  # type: ignore
                await session.commit()

        if user.is_blocked:  # type: ignore
            return JSONResponse(
                {"error": "User is blocked."},
                status_code=403,
            )

        return JSONResponse({"user": user.username, "api_key": user.api_key})
