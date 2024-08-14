from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request

from src.auth import is_auth_exempt
from src.deploy.routes import router as deploy_router
from src.manage.routes import router as manage_router

app = FastAPI()


@app.middleware("http")
async def user_id_middleware(request: Request, call_next: Any):
    if is_auth_exempt(request):
        return await call_next(request)

    # TODO: actual user ID extraction, raise 401 if not found
    request.state.user_id = 1
    return await call_next(request)


@app.get("/healthcheck")
def healthcheck():
    return {"ok": True}


app.include_router(deploy_router)
app.include_router(manage_router)
