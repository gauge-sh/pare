from __future__ import annotations

from fastapi import FastAPI

from src.deploy.routes import router as deploy_router

app = FastAPI()


@app.get("/healthcheck")
def healthcheck():
    return {"ok": True}


app.include_router(deploy_router)
