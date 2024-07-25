# type: ignore
from __future__ import annotations

from environs import Env

env = Env()
env.read_env()

GAUGE_API_URL: str = env.str("GAUGE_API_URL", "http://localhost:8000/v0.1")
CLIENT_SECRET: str = env.str("GAUGE_CLIENT_SECRET", "")
