from __future__ import annotations

from dataclasses import dataclass

import aiohttp


@dataclass
class GithubAccountInfo:
    username: str
    email: str


GITHUB_USER_API = "https://api.github.com/user"


async def get_github_account_info(token: str) -> GithubAccountInfo:
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(GITHUB_USER_API, headers=headers) as response:
            response = await response.json()
            return GithubAccountInfo(
                username=response["login"], email=response["email"]
            )
