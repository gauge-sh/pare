from __future__ import annotations

from fastapi import FastAPI

from src import middleware
from src.deploy.routes import router as deploy_router
from src.manage.routes import router as manage_router

app = FastAPI()

middleware.apply_middleware(app)


@app.get("/healthcheck")
def healthcheck():
    return {"ok": True}


app.include_router(deploy_router)
app.include_router(manage_router)
