from fastapi import APIRouter
from src.constants import API_VERSION


router = APIRouter(prefix=f"/{API_VERSION}")

@router.get("/status/")
def status(client_id: str):
    ...
