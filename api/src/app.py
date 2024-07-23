from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request, Response

from src import settings
from src.deploy.routes import router as deploy_router

app = FastAPI()


AUTH_EXEMPT = ["/healthcheck"]


@app.middleware("http")
async def auth_check(request: Request, call_next: Any):
    print(settings.CLIENT_SECRET, request.headers.get("X-Client-Secret"))
    if (
        request.url.path not in AUTH_EXEMPT
        and settings.CLIENT_SECRET != request.headers.get("X-Client-Secret")
    ):
        return Response(status_code=403)

    return await call_next(request)


@app.get("/healthcheck")
def healthcheck():
    return {"ok": True}


app.include_router(deploy_router)
