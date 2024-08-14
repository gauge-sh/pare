# type: ignore
from __future__ import annotations

from environs import Env

env = Env()
env.read_env()

PARE_API_URL: str = env.str("PARE_API_URL", "http://localhost:8000/v0.1")
PARE_API_DEPLOY_URL_PATH: str = env.str("PARE_API_DEPLOY_URL_PATH", "/deploy/")
PARE_API_SERVICES_URL_PATH: str = env.str("PARE_API_SERVICES_URL_PATH", "/services/")
PARE_API_INVOKE_URL_PATH: str = env.str("PARE_API_INVOKE_URL_PATH", "/services/invoke/")
PARE_API_DELETE_URL_PATH: str = env.str("PARE_API_DELETE_URL_PATH", "/services/delete/")
PARE_API_KEY: str = env.str("PARE_API_KEY", "")
PARE_API_KEY_HEADER: str = env.str("PARE_API_KEY_HEADER", "X-Pare-API-Key")
