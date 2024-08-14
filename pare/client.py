from __future__ import annotations

import subprocess
from functools import lru_cache

from pare import settings

FALLBACK_LATEST_SENTINEL = "latest"

# TODO: build a Client singleton to handle all requests


@lru_cache(maxsize=1)
def get_current_git_hash() -> str:
    if settings.PARE_GIT_HASH:
        return settings.PARE_GIT_HASH

    # if the git hash is not provided, we will try to get it from the current git state
    try:
        # verify we are in a clean git state
        subprocess.check_call(["git", "diff", "--quiet"])

        return subprocess.check_output(["git", "rev-parse", "HEAD"]).decode().strip()
    except subprocess.CalledProcessError:
        return FALLBACK_LATEST_SENTINEL
