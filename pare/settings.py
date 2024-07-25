# type: ignore
from __future__ import annotations

from environs import Env

env = Env()
env.read_env()

PARE_API_URL: str = env.str("PARE_API_URL", "http://localhost:8000/v0.1")
CLIENT_SECRET: str = env.str("PARE_CLIENT_SECRET", "")
