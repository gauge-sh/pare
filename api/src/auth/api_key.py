from __future__ import annotations

import uuid


def generate_api_key() -> str:
    return str(uuid.uuid4())
